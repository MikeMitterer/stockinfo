"""Tests für von Hand nachgetragene Kennzahlen (T-09).

Geprüft wird die **Regel**, nicht eine Beispieldatei: Was die Quelle liefert,
gewinnt; ein manueller Wert füllt nur Lücken — und wo er verdeckt wird, sagt
die Antwort das ausdrücklich. Die Eingaben sind deshalb synthetisch und decken
die Fälle ab, an denen sich die Regel entscheidet, nicht einen Datenbestand.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.db import init_db
from app.main import app
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_cache import apply_overrides
from app.services.quote_service import InstrumentNotFoundError


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    """Repository auf einer frisch initialisierten temporären DB."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _quote(**felder: object) -> QuoteResponse:
    """Ein Kurs mit leeren ETF-Extras — der Fall, für den T-09 gedacht ist."""
    vorgabe: dict = {
        "isin": "DE000EWG0LD1",
        "symbol": "GOLD.SG",
        "exchange": "Stuttgart",
        "name": "EUWAX Gold",
        "type": "etf",
        "currency": "EUR",
        "price": 122.41,
        "quote_time": "2026-08-14T19:55:19+00:00",
        "fetched_at": "2026-08-16T18:33:53+00:00",
    }
    vorgabe.update(felder)
    return QuoteResponse(**vorgabe)


# ─── Die Regel ───────────────────────────────────────────────────────────────


def test_manueller_wert_fuellt_eine_luecke() -> None:
    zeile = apply_overrides({"ter": None, "manual_ter": 0.25})

    assert zeile["ter"] == 0.25
    assert zeile["manual_fields"] == ["ter"]
    assert zeile["shadowed_fields"] == []


def test_quelle_gewinnt_und_der_manuelle_wert_bleibt_sichtbar() -> None:
    # Verdecken ist erlaubt, Verschweigen nicht: Wer 0.25 eingetragen hat und
    # 0.19 sieht, muss erfahren, dass sein Wert noch da ist.
    zeile = apply_overrides({"ter": 0.19, "manual_ter": 0.25})

    assert zeile["ter"] == 0.19
    assert zeile["manual_ter"] == 0.25
    assert zeile["shadowed_fields"] == ["ter"]
    assert zeile["manual_fields"] == []


def test_ohne_manuellen_wert_bleibt_alles_wie_es_war() -> None:
    zeile = apply_overrides({"ter": 0.19, "manual_ter": None})

    assert zeile["ter"] == 0.19
    assert zeile["manual_fields"] == []
    assert zeile["shadowed_fields"] == []


def test_ausschuettend_ist_eine_aussage_keine_luecke() -> None:
    """``False`` bei ``accumulating`` heißt „ausschüttend" — nicht „leer"."""
    zeile = apply_overrides({"accumulating": False, "manual_accumulating": 1})

    assert zeile["accumulating"] is False
    assert zeile["shadowed_fields"] == ["accumulating"]


def test_manuelles_ausschuettend_faellt_nicht_durchs_raster() -> None:
    # Der umgekehrte Fall: Die Quelle weiß nichts, von Hand steht „nein" da.
    # Ein Test auf Wahrheit statt auf `None` würde den Wert hier verschlucken.
    zeile = apply_overrides({"accumulating": None, "manual_accumulating": 0})

    assert zeile["accumulating"] is False
    assert zeile["manual_fields"] == ["accumulating"]


def test_mehrere_kennzahlen_werden_einzeln_entschieden() -> None:
    zeile = apply_overrides(
        {
            "ter": None,
            "manual_ter": 0.25,
            "volatility": 26.6,
            "manual_volatility": 30.0,
            "accumulating": None,
            "manual_accumulating": None,
        }
    )

    assert zeile["ter"] == 0.25
    assert zeile["volatility"] == 26.6
    assert zeile["manual_fields"] == ["ter"]
    assert zeile["shadowed_fields"] == ["volatility"]


# ─── Persistenz ──────────────────────────────────────────────────────────────


def test_werte_ueberleben_das_erneute_lesen(repo: QuoteRepository) -> None:
    instrument_id = repo.save_quote(_quote())

    repo.set_overrides(instrument_id, 0.25, 30.0, True, "2026-08-17T10:00:00+00:00")

    assert repo.get_overrides(instrument_id) == {
        "instrument_id": instrument_id,
        "ter": 0.25,
        "volatility": 30.0,
        "accumulating": 1,
        "updated_at": "2026-08-17T10:00:00+00:00",
    }


def test_ein_kurs_update_ruehrt_die_manuellen_werte_nicht_an(
    repo: QuoteRepository,
) -> None:
    """Der eigentliche Zweck der getrennten Tabelle.

    Der Hintergrund-Refresh schreibt die Instrumentenzeile neu — mit leeren
    ETF-Extras, weil die Quelle für dieses Papier keine liefert. Läge der
    manuelle Wert in derselben Zeile, wäre er danach weg.
    """
    instrument_id = repo.save_quote(_quote())
    repo.set_overrides(instrument_id, 0.25, None, None, "2026-08-17T10:00:00+00:00")

    repo.save_quote(_quote(price=124.00, quote_time="2026-08-17T09:00:00+00:00"))

    gespeichert = repo.get_overrides(instrument_id)
    assert gespeichert is not None
    assert gespeichert["ter"] == 0.25

    zeile = next(z for z in repo.list_instruments_with_latest() if z["id"] == instrument_id)
    assert apply_overrides(zeile)["ter"] == 0.25


def test_alles_leeren_entfernt_die_zeile(repo: QuoteRepository) -> None:
    # Sonst sammeln sich Karteileichen ohne Inhalt.
    instrument_id = repo.save_quote(_quote())
    repo.set_overrides(instrument_id, 0.25, None, None, "2026-08-17T10:00:00+00:00")

    repo.set_overrides(instrument_id, None, None, None, "2026-08-17T11:00:00+00:00")

    assert repo.get_overrides(instrument_id) is None


def test_die_liste_bringt_die_manuellen_werte_mit(repo: QuoteRepository) -> None:
    instrument_id = repo.save_quote(_quote())
    repo.set_overrides(instrument_id, 0.25, None, False, "2026-08-17T10:00:00+00:00")

    zeile = next(z for z in repo.list_instruments_with_latest() if z["id"] == instrument_id)

    assert zeile["manual_ter"] == 0.25
    assert zeile["manual_accumulating"] == 0


def test_das_loeschen_eines_instruments_nimmt_die_overrides_mit(
    repo: QuoteRepository,
) -> None:
    instrument_id = repo.save_quote(_quote())
    repo.set_overrides(instrument_id, 0.25, None, None, "2026-08-17T10:00:00+00:00")

    assert repo.delete_by_symbol("GOLD.SG") is True
    assert repo.get_overrides(instrument_id) is None


# ─── Endpoint ────────────────────────────────────────────────────────────────


class _FakeService:
    """Merkt sich, was geschrieben wurde — der Endpoint soll nur durchreichen."""

    def __init__(self) -> None:
        self.gespeichert: dict = {"ter": None, "volatility": None, "accumulating": None}

    def get_overrides(self, symbol: str) -> dict:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        return dict(self.gespeichert)

    def set_overrides(
        self,
        symbol: str,
        ter: float | None,
        volatility: float | None,
        accumulating: bool | None,
    ) -> dict:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        self.gespeichert = {
            "ter": ter,
            "volatility": volatility,
            "accumulating": accumulating,
        }
        return dict(self.gespeichert)


@pytest.fixture
def client() -> Iterator[TestClient]:
    dienst = _FakeService()
    app.dependency_overrides[get_cached_quote_service] = lambda: dienst
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_endpoint_schreibt_und_liest(client: TestClient) -> None:
    antwort = client.put(
        "/instruments/by-symbol/GOLD.SG/overrides",
        json={"ter": 0.25, "volatility": 30.0, "accumulating": True},
    )

    assert antwort.status_code == 200
    assert antwort.json() == {"ter": 0.25, "volatility": 30.0, "accumulating": True}
    assert client.get("/instruments/by-symbol/GOLD.SG/overrides").json()["ter"] == 0.25


def test_endpoint_leert_weggelassene_felder(client: TestClient) -> None:
    """Der Satz ist vollständig — ein fehlendes Feld heißt „löschen"."""
    client.put(
        "/instruments/by-symbol/GOLD.SG/overrides",
        json={"ter": 0.25, "volatility": 30.0, "accumulating": True},
    )

    antwort = client.put("/instruments/by-symbol/GOLD.SG/overrides", json={"ter": 0.25})

    assert antwort.json() == {"ter": 0.25, "volatility": None, "accumulating": None}


@pytest.mark.parametrize(
    "nutzlast",
    [
        {"ter": -1},          # unter der Grenze
        {"ter": 101},         # über der Grenze
        {"volatility": -0.1},
        {"volatility": 501},
        {"ter": "viel"},      # gar keine Zahl
    ],
)
def test_endpoint_weist_unsinn_ab(client: TestClient, nutzlast: dict) -> None:
    antwort = client.put("/instruments/by-symbol/GOLD.SG/overrides", json=nutzlast)

    assert antwort.status_code == 422


def test_endpoint_meldet_unbekanntes_symbol(client: TestClient) -> None:
    assert client.put("/instruments/by-symbol/XXX/overrides", json={}).status_code == 404
    assert client.get("/instruments/by-symbol/XXX/overrides").status_code == 404
