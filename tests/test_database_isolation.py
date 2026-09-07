"""Die Testumgebung isoliert den Standardpfad und stoppt falsche Verbindungen."""

from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from app.config import get_settings
from app.container import get_daily_history_service

SAVED_CONNECT = sqlite3.connect


def test_konfigurierter_arbeitsdatenpfad_ausserhalb_data_wird_beim_start_erfasst(
    tmp_path,
):
    target = tmp_path / "external.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os, sqlite3; import tests.conftest; sqlite3.connect(os.environ['DATABASE_PATH'])",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "DATABASE_PATH": str(target)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert "Test database access blocked" in result.stderr
    assert not target.exists()


@pytest.mark.parametrize("iteration", range(2))
def test_gecachter_tagesdienst_verwendet_den_aktuellen_testpfad(tmp_path, iteration):
    service = get_daily_history_service()
    assert service._repository._database_path == str(tmp_path / "stockinfo.db")


@pytest.mark.parametrize("iteration", range(2))
def test_jeder_test_erhaelt_eine_leere_standarddatenbank(tmp_path, iteration):
    path = Path(get_settings().database_path)
    assert path.parent == tmp_path
    assert not path.exists()
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE isolated (value INTEGER)")
        connection.execute("INSERT INTO isolated VALUES (?)", (iteration,))


@pytest.mark.parametrize(
    "connect", [sqlite3.connect, SAVED_CONNECT, sqlite3.Connection]
)
@pytest.mark.parametrize(
    "form", ["absolute", "relative", "uri", "relative_uri", "symlink"]
)
def test_geschuetzte_verbindung_scheitert_vor_dateierstellung(
    tmp_path, monkeypatch, connect, form
):
    from tests import conftest

    target = tmp_path / "protected" / "work database.sqlite"
    target.parent.mkdir()
    monkeypatch.setattr(
        conftest, "PROTECTED_DATABASES", (*conftest.PROTECTED_DATABASES, target)
    )
    monkeypatch.chdir(tmp_path)
    alias = tmp_path / "alias.sqlite"
    alias.symlink_to(target)
    inputs = {
        "absolute": target,
        "relative": str(target.relative_to(tmp_path)),
        "uri": target.as_uri() + "?mode=rwc",
        "relative_uri": "file:protected/work%20database.sqlite?mode=rwc",
        "symlink": alias,
    }
    with pytest.raises(RuntimeError, match="Test database access blocked"):
        with closing(connect(inputs[form], uri=True)):
            pass
    assert not target.exists()


def test_auch_neue_dateien_im_geschuetzten_verzeichnis_sind_gesperrt(
    tmp_path, monkeypatch
):
    from tests import conftest

    protected = tmp_path / "protected"
    protected.mkdir()
    monkeypatch.setattr(
        conftest, "PROTECTED_DIRECTORIES", (*conftest.PROTECTED_DIRECTORIES, protected)
    )
    target = protected / "new.sqlite"
    with pytest.raises(RuntimeError, match="Test database access blocked"):
        with closing(sqlite3.connect(target)):
            pass
    assert not target.exists()


@pytest.mark.parametrize("database", [":memory:", "file::memory:?cache=shared"])
def test_speicherdatenbanken_bleiben_erlaubt(database):
    with closing(sqlite3.connect(database, uri=True)) as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)
