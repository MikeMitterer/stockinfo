"""Plugin-Datenmigration über den echten Start mit isolierten Daten."""

import json
import sqlite3
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app import container
from app.config import get_settings
from app.data_versions import stored_versions
from app.db import init_db
from app.main import app
from app.migration_guard import MigrationGate
from app.routers import migration
from app.scheduler import RefreshScheduler
from app.services.backup import BackupService
from app.sources_registry import close_all


@pytest.fixture
def installation(tmp_path, monkeypatch):
    database = tmp_path / "stockinfo.db"
    monkeypatch.setenv("DATABASE_PATH", str(database))
    (tmp_path / "plugins").mkdir()
    (tmp_path / "sources.yaml").write_text(
        "quotes: [yfinance]\nresolvers: []\ndaily: [yfinance]\nfx: []\netf_meta: [t25-example]\n"
    )
    started = []
    monkeypatch.setattr(RefreshScheduler, "start", lambda self: started.append(True))
    monkeypatch.setattr(RefreshScheduler, "shutdown", lambda self: None)
    yield tmp_path, database, started
    reset()


def reset():
    close_all()
    get_settings.cache_clear()
    for value in vars(container).values():
        if hasattr(value, "cache_clear"):
            value.cache_clear()
    migration._gate = MigrationGate()


@contextmanager
def boot():
    reset()
    with TestClient(app) as client:
        yield client


def seed(database, version=None):
    init_db(str(database))
    with sqlite3.connect(database) as connection:
        connection.executemany("INSERT INTO meta(key,value) VALUES (?,?)", [
            ("example-data", "old"), ("foreign-data", "untouched"),
        ])
        if version is not None:
            connection.execute("INSERT INTO meta(key,value) VALUES (?,?)", (
                "plugin_data_versions", json.dumps({"t25-example": version}),
            ))


def write_plugin(root, version, *, failure="", missing=False):
    method = "" if missing else f"""
    @staticmethod
    def migrate(context, from_version, to_version):
        context.execute("UPDATE meta SET value=? WHERE key='example-data'", (f"{{from_version}}->{{to_version}}",))
        {failure or 'pass'}
"""
    (root / "plugins" / "example.py").write_text(f"""from stockinfo_plugin import MetadataSource
class Example(MetadataSource):
    name = "t25-example"
    api_version = 2
    data_version = {version}
    supported_types = frozenset({{"stock"}})
    def handles(self, request): return False
    def fetch(self, request): return []
{method}
SOURCES = [Example]
""")
    # Der Dateilader soll auch bei gleicher Länge sicher neuen Quelltext lesen.
    for cached in (root / "plugins" / "__pycache__").glob("example.*.pyc"):
        cached.unlink()


def values(database):
    with sqlite3.connect(database) as connection:
        return dict(connection.execute("SELECT key,value FROM meta WHERE key IN ('example-data','foreign-data')"))


@pytest.mark.parametrize("target", [2, 3])
def test_sichert_migriert_und_wiederholt_nicht(installation, target):
    root, database, started = installation
    seed(database)
    write_plugin(root, target)
    with boot() as client:
        assert client.get("/instruments").status_code == 200
        assert values(database) == {"example-data": f"1->{target}", "foreign-data": "untouched"}
        assert stored_versions(database)["t25-example"] == target
        backups = list((root / "backups").glob("*.db"))
        assert len(backups) == 1
        assert values(backups[0])["example-data"] == "old"
        assert stored_versions(backups[0])["t25-example"] == 1
    with boot() as client:
        assert client.get("/ready").status_code == 200
        assert len(list((root / "backups").glob("*.db"))) == 1
    assert len(started) == 2


@pytest.mark.parametrize("failure,missing,stored", [
    ("", True, 1),
    ("raise ValueError('unsupported origin')", False, 1),
    ("", False, 3),
    ("context.execute('COMMIT')", False, 1),
])
def test_fehler_sperrt_betrieb_ohne_falschen_stempel(installation, failure, missing, stored, capsys):
    root, database, started = installation
    seed(database, stored)
    write_plugin(root, 2, failure=failure, missing=missing)
    with boot() as client:
        assert client.get("/instruments").status_code == 503
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200
        assert not started
        assert values(database)["example-data"] == "old"
        assert stored_versions(database)["t25-example"] == stored
    assert f"t25-example: data_version {stored} -> 2" in capsys.readouterr().out
    write_plugin(root, stored)
    with boot() as client:
        assert client.get("/instruments").status_code == 200


def test_ohne_sicherung_keine_autorenfunktion(installation, monkeypatch):
    root, database, started = installation
    seed(database)
    write_plugin(root, 2)
    def fail(self, **kwargs):
        raise OSError("backup failed")
    monkeypatch.setattr(BackupService, "create", fail)
    with boot() as client:
        assert client.get("/instruments").status_code == 503
        assert values(database)["example-data"] == "old"
        assert stored_versions(database)["t25-example"] == 1
        assert not started


@pytest.mark.parametrize("empty_file", [False, True])
def test_frische_db_uebernimmt_ziel_ohne_migration(installation, empty_file):
    root, database, started = installation
    if empty_file:
        database.touch()
    write_plugin(root, 3, failure="raise AssertionError('must not run')")
    with boot() as client:
        assert client.get("/instruments").status_code == 200
        assert stored_versions(database)["t25-example"] == 3
        assert not list((root / "backups").glob("*.db"))
        assert started


def test_unveraenderte_datenversion_braucht_keine_funktion(installation):
    root, database, started = installation
    seed(database, 1)
    write_plugin(root, 1, missing=True)
    with boot() as client:
        assert client.get("/instruments").status_code == 200
        assert values(database)["example-data"] == "old"
        assert not list((root / "backups").glob("*.db"))
        assert started


def test_prozessabbruch_rollt_zurueck_und_neustart_migriert(installation):
    import os
    import subprocess
    import sys

    root, database, _ = installation
    seed(database, 1)
    write_plugin(root, 2, failure="__import__('os')._exit(73)")
    result = subprocess.run(
        [sys.executable, "-c", "from fastapi.testclient import TestClient; from app.main import app\nwith TestClient(app): pass"],
        env={**os.environ, "DATABASE_PATH": str(database)}, capture_output=True, timeout=20,
    )
    assert result.returncode == 73, result.stderr.decode()
    assert values(database)["example-data"] == "old"
    assert stored_versions(database)["t25-example"] == 1
    assert len(list((root / "backups").glob("*.db"))) == 1
    write_plugin(root, 2)
    with boot() as client:
        assert client.get("/instruments").status_code == 200
        assert values(database)["example-data"] == "1->2"


def test_autorenbeispiel_erhaelt_fremde_daten_und_schema(installation):
    root, database, _ = installation
    seed(database, 1)
    write_plugin(root, 2)
    source = root / "plugins" / "example.py"
    source.write_text(source.read_text().replace(
        "class Example(MetadataSource):",
        "from stockinfo_plugin_examples.migration import migrate\nclass Example(MetadataSource):",
    ).replace("SOURCES = [Example]", "Example.migrate = staticmethod(migrate)\nSOURCES = [Example]"))
    with sqlite3.connect(database) as connection:
        schema = list(connection.execute('SELECT name,sql FROM sqlite_master WHERE type="table" ORDER BY name'))
    with boot() as client:
        assert client.get("/instruments").status_code == 200
        assert values(database) == {"example-data": "new", "foreign-data": "untouched"}
        with sqlite3.connect(database) as connection:
            assert list(connection.execute('SELECT name,sql FROM sqlite_master WHERE type="table" ORDER BY name')) == schema


def test_identitaetsbestaetigung_bleibt_vorrangig(installation):
    from tests.legacy_schema import create_legacy_tables

    root, database, started = installation
    with sqlite3.connect(database) as connection:
        create_legacy_tables(connection)
        connection.execute("INSERT INTO instruments(symbol,first_seen) VALUES ('INVALID', '2026-01-01')")
    seed(database, 1)
    write_plugin(root, 2)
    with boot() as client:
        assert client.get("/migration").json()["pending"]
        assert client.get("/instruments").status_code == 503
        assert values(database)["example-data"] == "old"
        assert not started
        assert client.post("/migration/confirm").status_code == 200
        assert values(database)["example-data"] == "1->2"
        assert client.get("/instruments").status_code == 200
        assert started


def test_spaeterer_pluginfehler_behaelt_vorherigen_erfolg(installation):
    root, database, _ = installation
    seed(database, 1)
    write_plugin(root, 2)
    other = (root / "plugins" / "example.py").read_text().replace("t25-example", "zz-other").replace("example-data", "foreign-data").replace("        pass", "        raise ValueError('later plugin failed')")
    (root / "plugins" / "other.py").write_text(other)
    config = root / "sources.yaml"
    config.write_text(config.read_text().replace("[t25-example]", "[t25-example, zz-other]"))
    with boot() as client:
        assert client.get("/instruments").status_code == 503
        assert values(database) == {"example-data": "1->2", "foreign-data": "untouched"}
        assert stored_versions(database)["t25-example"] == 2
        assert stored_versions(database)["zz-other"] == 1


def test_paket_bump_startet_keine_migration(installation, monkeypatch):
    from app import plugin_env

    root, database, _ = installation
    seed(database, 1)
    write_plugin(root, 1, missing=True)
    requested = []
    # Nur die Paketinstallation ersetzen; Laden, Start und Versionen bleiben echt.
    def installed(packages, data_dir):
        requested.append(packages)
        return None
    monkeypatch.setattr(plugin_env, "ensure", installed)
    config = root / "sources.yaml"
    original = config.read_text()
    for version in ("1.0.0", "1.1.0"):
        config.write_text(original + f"plugins:\n  packages: [example=={version}]\n")
        with boot() as client:
            assert client.get("/instruments").status_code == 200
            assert values(database)["example-data"] == "old"
            assert not list((root / "backups").glob("*.db"))
    assert requested == [("example==1.0.0",), ("example==1.1.0",)]
