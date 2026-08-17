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
from app.models import OVERRIDE_FIELDS, QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService, apply_overrides
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError


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

    # Geprüft wird, dass die geschriebenen Werte beim Lesen wiederkommen —
    # nicht die exakte Feldmenge des Dicts. Die Override-Tabelle wächst
    # (T-15) um fünf weitere Spalten, die `get_overrides` per `SELECT *`
    # mitliefert; die genaue Feldmenge deckt ab Task 3 ein eigener Test ab.
    gespeichert = repo.get_overrides(instrument_id)
    assert gespeichert is not None
    assert gespeichert["instrument_id"] == instrument_id
    assert gespeichert["ter"] == 0.25
    assert gespeichert["volatility"] == 30.0
    assert gespeichert["accumulating"] == 1
    assert gespeichert["updated_at"] == "2026-08-17T10:00:00+00:00"


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
        {"ter": 50},          # ein Vertipper, keine TER — kein Produkt liegt dort
        {"ter": 5.1},         # knapp über der Grenze
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


# ─── Die Antwort des Kurs-Endpoints ──────────────────────────────────────────


class _Quelle:
    """Live-Beschaffung als Attrappe.

    Ohne Antwort im Gepäck ist jeder Zugriff ein Fehler — so fällt auf, wenn ein
    Test versehentlich den Live-Pfad nimmt statt des Caches.
    """

    def __init__(self, antwort: QuoteResponse | None = None, fehler: bool = False) -> None:
        self._antwort = antwort
        self._fehler = fehler

    def _liefern(self, kennung: str) -> QuoteResponse:
        if self._fehler:
            raise QuoteUnavailableError(kennung)
        if self._antwort is None:
            raise AssertionError(f"unerwartet live beschafft: {kennung}")
        return self._antwort.model_copy(deep=True)

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        return self._liefern(isin)

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:
        return self._liefern(symbol)


class _StummerSync:
    """EOD-Sync, der nichts nachzieht — die Volatilität bleibt damit leer."""

    def sync(self, instrument_id: int, symbol: str, start: str) -> None:
        return None


def _dienst(
    repo: QuoteRepository,
    quelle: _Quelle | None = None,
    *,
    ttl_hours: int = 24 * 365,
) -> CachedQuoteService:
    """Cache-Dienst auf einem echten Repository.

    Die Vorgabe-TTL ist absichtlich riesig: Ein gespeicherter Kurs gilt damit
    als frisch, und der Test nimmt den Cache-Pfad. Wer den Live-Pfad prüfen
    will, setzt `ttl_hours=0`.
    """
    return CachedQuoteService(
        quote_service=quelle or _Quelle(),  # type: ignore[arg-type]
        repository=repo,
        ttl_hours=ttl_hours,
        daily_sync=_StummerSync(),  # type: ignore[arg-type]
    )


def test_der_kurs_endpoint_kennt_die_manuellen_werte(repo: QuoteRepository) -> None:
    """Der eigentliche Bug: Die Regel galt nur in der Liste, nicht im Kurs.

    `apply_overrides` lief ausschließlich in `list_instruments`. Wer dieselbe
    Kennzahl über `/quote` abfragte — die Oberfläche im JSON-Fenster, Excel
    über Power Query, jedes Skript — bekam den rohen Wert der Quelle und damit
    ein „nicht gesetzt", obwohl etwas eingetragen war.
    """
    instrument_id = repo.save_quote(_quote(accumulating=None, ter=None))
    repo.set_overrides(instrument_id, 0.12, None, True, "2026-08-17T10:00:00+00:00")

    antwort = _dienst(repo).get_by_isin("DE000EWG0LD1")

    assert antwort.accumulating is True
    assert antwort.ter == 0.12


def test_der_kurs_endpoint_laesst_der_quelle_den_vortritt(repo: QuoteRepository) -> None:
    """Dieselbe Vorrang-Regel wie in der Liste — nicht eine zweite daneben."""
    instrument_id = repo.save_quote(_quote(accumulating=True, ter=0.20))
    repo.set_overrides(instrument_id, 0.99, None, False, "2026-08-17T10:00:00+00:00")

    antwort = _dienst(repo).get_by_isin("DE000EWG0LD1")

    assert antwort.ter == 0.20
    assert antwort.accumulating is True


def test_der_kurs_endpoint_ohne_eintrag_bleibt_unveraendert(repo: QuoteRepository) -> None:
    # Ohne Eintrag darf nichts passieren — auch keine leere Zeile dazuerfinden.
    repo.save_quote(_quote(accumulating=None, ter=None))

    antwort = _dienst(repo).get_by_isin("DE000EWG0LD1")

    assert antwort.accumulating is None
    assert antwort.ter is None


def test_der_kurs_endpoint_kennt_sie_auch_per_symbol(repo: QuoteRepository) -> None:
    """Papiere ohne ISIN gehen über `/quote?symbol=` — derselbe Anspruch."""
    instrument_id = repo.save_quote(_quote(accumulating=None))
    repo.set_overrides(instrument_id, None, None, True, "2026-08-17T10:00:00+00:00")

    assert _dienst(repo).get_by_symbol("GOLD.SG").accumulating is True


def test_ein_frisch_beschaffter_kurs_kennt_sie_ebenfalls(repo: QuoteRepository) -> None:
    """Der Live-Pfad baut die Antwort aus der Quelle, nicht aus der Zeile.

    Ohne die Regel an dieser Stelle hinge es am Zufall der TTL, ob eine
    Abfrage den eingetragenen Wert zeigt oder nicht.
    """
    instrument_id = repo.save_quote(_quote(accumulating=None, ter=None))
    repo.set_overrides(instrument_id, 0.30, None, True, "2026-08-17T10:00:00+00:00")

    # TTL 0 ⇒ der gespeicherte Kurs gilt als alt, die Quelle wird gefragt.
    dienst = _dienst(repo, _Quelle(_quote(accumulating=None, ter=None)), ttl_hours=0)
    antwort = dienst.get_by_isin("DE000EWG0LD1")

    assert antwort.accumulating is True
    assert antwort.ter == 0.30


def test_auch_ein_veralteter_kurs_kennt_sie(repo: QuoteRepository) -> None:
    """Fällt die Quelle aus, kommt der alte Wert — mit den Eingaben darauf."""
    instrument_id = repo.save_quote(_quote(accumulating=None))
    repo.set_overrides(instrument_id, None, None, True, "2026-08-17T10:00:00+00:00")

    dienst = _dienst(repo, _Quelle(fehler=True), ttl_hours=0)
    antwort = dienst.get_by_isin("DE000EWG0LD1")

    assert antwort.stale is True
    assert antwort.accumulating is True


def test_refresh_liefert_sie_mit_zurueck(repo: QuoteRepository) -> None:
    """`POST /refresh/{isin}` gibt die neue Antwort direkt an die Oberfläche."""
    instrument_id = repo.save_quote(_quote(accumulating=None, ter=None))
    repo.set_overrides(instrument_id, 0.30, None, True, "2026-08-17T10:00:00+00:00")

    dienst = _dienst(repo, _Quelle(_quote(accumulating=None, ter=None)))
    antwort = dienst.refresh_one("DE000EWG0LD1")

    assert antwort.accumulating is True
    assert antwort.ter == 0.30


def test_refresh_per_symbol_liefert_sie_ebenfalls(repo: QuoteRepository) -> None:
    instrument_id = repo.save_quote(_quote(accumulating=None))
    repo.set_overrides(instrument_id, None, None, True, "2026-08-17T10:00:00+00:00")

    dienst = _dienst(repo, _Quelle(_quote(accumulating=None)))

    assert dienst.refresh_one_by_symbol("GOLD.SG").accumulating is True


def test_der_refresh_schreibt_den_manuellen_wert_nicht_in_die_zeile(
    repo: QuoteRepository,
) -> None:
    """Die Antwort trägt ihn, die Instrumentenzeile nicht.

    Sonst wäre die Trennung der Tabellen wieder hinfällig: Der nächste Lauf der
    Quelle fände einen Wert vor, den er nicht gesetzt hat, und die Eingabe
    ließe sich nie wieder von der Quelle unterscheiden.
    """
    instrument_id = repo.save_quote(_quote(accumulating=None))
    repo.set_overrides(instrument_id, None, None, True, "2026-08-17T10:00:00+00:00")

    _dienst(repo, _Quelle(_quote(accumulating=None))).refresh_one("DE000EWG0LD1")

    zeile = repo.get_instrument_by_isin("DE000EWG0LD1")
    assert zeile is not None
    assert zeile["accumulating"] is None


def test_jede_kennzahl_tragende_antwort_kennt_die_regel() -> None:
    """Wächter über die Fläche, nicht über einen einzelnen Pfad.

    Der Bug war nicht, dass eine Stelle falsch rechnete — sondern dass es eine
    zweite Stelle überhaupt gab. Wächst ein Modell mit `ter`, `volatility` oder
    `accumulating` dazu, muss jemand entscheiden, wo die Regel dort greift;
    dieser Test zwingt die Entscheidung, statt sie zu vergessen.
    """
    import inspect

    from pydantic import BaseModel

    from app import models

    tragend = {
        name
        for name, obj in vars(models).items()
        if inspect.isclass(obj)
        and issubclass(obj, BaseModel)
        and obj is not BaseModel
        and set(OVERRIDE_FIELDS) & set(obj.model_fields)
    }

    assert tragend == {
        "QuoteResponse",  # /quote, /quote/{isin}, /refresh/… — über _with_overrides
        "InstrumentSummary",  # /instruments — über apply_overrides
        "InstrumentOverrides",  # die Eingaben selbst, absichtlich roh
    }


def test_die_liste_des_dienstes_wendet_die_regel_an(repo: QuoteRepository) -> None:
    """`/instruments` — der eine Pfad, der die Regel schon vorher hatte.

    Geprüft wurden bisher Repository und Regel getrennt; dass der Dienst beide
    verbindet, stand nur im Code. Damit fiele ein entfernter Aufruf niemandem
    auf.
    """
    instrument_id = repo.save_quote(_quote(accumulating=None, ter=None))
    repo.set_overrides(instrument_id, 0.30, None, True, "2026-08-17T10:00:00+00:00")

    zeile = next(z for z in _dienst(repo).list_instruments() if z["id"] == instrument_id)

    assert zeile["accumulating"] is True
    assert zeile["ter"] == 0.30
    assert zeile["manual_fields"] == ["ter", "accumulating"]


def test_die_ter_grenze_laesst_reale_werte_durch(client: TestClient) -> None:
    """5 % ist die Grenze, nicht das Verbot.

    Der Wert fängt Vertipper ab (50 statt 0,50) und lässt jeden handelbaren
    Fall zu: ETFs liegen bei 0,03–1 %, aktive Fonds bis rund 3 %.
    """
    antwort = client.put(
        "/instruments/by-symbol/GOLD.SG/overrides", json={"ter": 5}
    )

    assert antwort.status_code == 200
    assert antwort.json()["ter"] == 5
