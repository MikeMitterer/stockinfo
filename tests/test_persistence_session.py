"""Die Engine öffnet genau die Datei aus `DATABASE_PATH` — auch mit Sonderzeichen.

`init_db` schreibt das Schema über `sqlite3`, das Repository liest über
SQLAlchemy. Stand der Pfad im URL-Text (`sqlite:///{pfad}`), las SQLAlchemy
ein `?` als Beginn der Optionen und öffnete eine zweite Datei ohne Schema;
der Start brach mit `no such table: meta` ab (Codex, T-91 Runde 1).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import get_sources_config
from app.main import app
from app.persistence.db import init_db
from app.persistence.repository import QuoteRepository

NAMES = ["quotes?archive.db", "a#b.db", "p%20q.db", "x&mode=ro.db"]


@pytest.mark.parametrize("name", NAMES)
def test_repository_liest_und_schreibt_die_datei_aus_dem_pfad(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    init_db(str(path))
    repository = QuoteRepository(str(path))

    repository.save_fx_rate("EUR", "USD", 1.1, "2026-10-02T10:00:00+00:00", "2026-10-02T10:00:00+00:00")

    assert repository.count_instruments() == 0
    assert repository.get_fx_rate("EUR", "USD")["rate"] == 1.1
    assert {entry.name for entry in tmp_path.iterdir()} <= {name, f"{name}-wal", f"{name}-shm"}


def test_die_app_startet_mit_fragezeichen_im_pfad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "quotes?archive.db"))
    get_settings.cache_clear()
    get_sources_config.cache_clear()

    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200
        assert client.get("/instruments").json() == []

    assert not (tmp_path / "quotes").exists(), "SQLAlchemy hat eine zweite Datei geöffnet"
