"""T-25: Datenkompatibilität folgt ausschließlich der Plugin-Deklaration."""

from dataclasses import replace
from pathlib import Path

from app.db import init_db
from app.services.backup import BackupService
from app.sources_config import SourcesConfig
from app.sources_registry import SourceSpec, register_loaded
from stockinfo_plugin import Source
import pytest


@pytest.fixture
def source():
    class Example(Source):
        name = "t25-example"
        data_version = 1

    register_loaded(
        (
            SourceSpec(
                Example.name,
                frozenset({"quotes"}),
                lambda *args: None,
                declaration=Example,
            ),
        )
    )
    yield Example
    register_loaded(())


@pytest.fixture
def config():
    return SourcesConfig(
        chains={"quotes": ("t25-example",)}, packages=("example==1.0.0",)
    )


def test_paketupdate_und_kettenwechsel_bleiben_kompatibel(tmp_path, source, config):
    database = str(tmp_path / "stockinfo.db")
    init_db(database)
    original = BackupService(database, config).create()
    updated = replace(
        config,
        packages=("example==2.0.0",),
        chains={"quotes": ("yfinance", "t25-example")},
    )
    entry = BackupService(database, updated).list()[0]
    assert entry.compatible, entry.reason
    BackupService(database, updated).request_restore(original.name)


def test_nur_data_version_macht_unpassend_auch_ohne_manifest(tmp_path, source, config):
    database = str(tmp_path / "stockinfo.db")
    init_db(database)
    original = BackupService(database, config).create()
    source.data_version = 2
    Path(tmp_path / "backups" / original.name).with_suffix(".json").unlink()
    entry = BackupService(database, config).list()[0]
    assert not entry.compatible
    assert entry.reason.code == "backup_data_version_differ"
    assert entry.reason.differences[0].field == "t25-example"
    assert entry.reason.differences[0].theirs == ["1"]
    assert entry.reason.differences[0].ours == ["2"]


def test_source_hat_kompatiblen_standard():
    assert Source.data_version == 1


def test_neuer_stand_wird_nicht_als_migration_gespeichert(tmp_path, source, config):
    from app.data_versions import stamp_versions, stored_versions

    database = str(tmp_path / "stockinfo.db")
    init_db(database)
    stamp_versions(database, config, fresh=True)
    source.data_version = 2
    stamp_versions(database, config)
    assert stored_versions(database)["t25-example"] == 1
    entry = BackupService(database, config).create()
    assert not entry.compatible


def test_frische_datenbank_traegt_deklaration_auch_beim_erneuten_lesen(
    tmp_path, source, config
):
    from app.data_versions import stamp_versions

    database = str(tmp_path / "stockinfo.db")
    source.data_version = 3
    init_db(database)
    stamp_versions(database, config, fresh=True)
    entry = BackupService(database, config).create()
    assert entry.compatible
    assert BackupService(database, config).list()[0].compatible


@pytest.mark.parametrize("invalid", [True, 0, -1, "2", 1.5, None])
def test_loader_lehnt_ungueltige_deklaration_ab(invalid):
    from app.plugin_loader import _check
    from stockinfo_plugin import QuoteSource, API_VERSION

    class Invalid(QuoteSource):
        name = "invalid-version"
        api_version = API_VERSION
        data_version = invalid

    assert "data_version" in _check(Invalid, "test").reason


def test_altes_backup_ohne_versionsmarker_gilt_als_eins(tmp_path, source, config):
    database = str(tmp_path / "stockinfo.db")
    init_db(database)
    service = BackupService(database, config)
    entry = service.create()
    import sqlite3

    with sqlite3.connect(service.directory / entry.name) as connection:
        connection.execute("DELETE FROM meta WHERE key='plugin_data_versions'")
    assert service.list()[0].compatible
    source.data_version = 2
    assert not service.list()[0].compatible


def test_dateiplugin_wird_vor_restore_neu_geladen(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.config import get_settings
    from app.container import get_sources_config, get_backup_service

    def reset():
        for cached in (get_settings, get_sources_config, get_backup_service):
            cached.cache_clear()

    def plugin(version):
        return f"""from stockinfo_plugin import QuoteSource, NotFound
class Example(QuoteSource):
    name = "t25-example"
    api_version = 2
    data_version = {version}
    supported_types = frozenset({{"stock"}})
    def fetch(self, request):
        return NotFound()
SOURCES = [Example]
# {"updated" * version}
"""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "stockinfo.db"))
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    source_file = plugins / "example.py"
    source_file.write_text(plugin(1))
    (tmp_path / "sources.yaml").write_text(
        "quotes: [t25-example]\nresolvers: []\ndaily: []\nfx: []\netf_meta: []\n"
    )
    reset()
    try:
        with TestClient(app) as client:
            declared = client.get("/sources").json()["sources"]
            assert (
                next(entry for entry in declared if entry["name"] == "t25-example")[
                    "data_version"
                ]
                == 1
            )
            backup = client.post("/backups").json()
            assert client.post(f"/backups/{backup['name']}/restore").status_code == 202
        source_file.write_text(plugin(2))
        reset()
        with TestClient(app) as client:
            listed = client.get("/backups").json()
            assert listed["restore_error"], listed
            assert (
                listed["backups"][0]["reason"]["code"] == "backup_data_version_differ"
            )
            declared = client.get("/sources").json()["sources"]
            assert (
                next(entry for entry in declared if entry["name"] == "t25-example")[
                    "data_version"
                ]
                == 2
            )
    finally:
        reset()
