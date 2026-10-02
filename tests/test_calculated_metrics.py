"""Die berechnete Volatilität gilt für alle Gattungen, nicht nur für ETFs.

StockInfo berechnet die Volatilität aus den Tageskursen jedes Instruments.
Angezeigt wird ein Detailwert aber nur, wenn eine Deklaration ihn für Gattung
und Identitätsart freigibt. Bisher deklarierte nur justETF `volatility`, und
nur für ETFs und ETCs; bei Aktien und Fonds blieb der Wert unsichtbar.
"""

from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import get_cached_quote_service, get_sources_config
from app.detail_models import DetailDefinition
from app.main import app
from app.persistence import detail_store
from app.persistence.db import init_db
from app.persistence.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService
from app.sources_registry import detail_definitions
from tests.boundaries import empty_daily_sync
from tests.test_quote_cache import FakeQuoteService, _now, _response


@pytest.fixture
def catalog() -> list[DetailDefinition]:
    return detail_definitions(get_sources_config(), get_settings())


@pytest.fixture
def repo(tmp_path: Path, catalog: list[DetailDefinition]) -> QuoteRepository:
    path = str(tmp_path / "volatility.db")
    init_db(path)
    repository = QuoteRepository(path)
    repository.detail_catalog(catalog)
    return repository


def _volatility(catalog: list[DetailDefinition]) -> DetailDefinition:
    return next(definition for definition in catalog if definition.name == "volatility")


@pytest.mark.parametrize("instrument_type", ["stock", "fund", "etf", "etc", "crypto", "bond"])
def test_volatilitaet_ist_fuer_jede_gattung_deklariert(
    catalog: list[DetailDefinition], instrument_type: str
) -> None:
    assert _volatility(catalog).applies(instrument_type, "listed")


def test_justetf_steht_vor_der_berechnung(catalog: list[DetailDefinition]) -> None:
    """Bei ETFs gilt weiter justETFs Wert, die Berechnung füllt die Lücke."""
    assert _volatility(catalog).sources == ["justetf", "calculated"]


def _save(repo: QuoteRepository, instrument_type: str, symbol: str = "VGWL.DE") -> int:
    """Legt ein Instrument der Gattung an und gibt seine interne ID zurück."""
    ticker = symbol.split(".")[0]
    response = _response(_now()).model_copy(update={
        "type": instrument_type,
        "symbol": symbol,
        "identity": _response(_now()).identity.model_copy(update={"ticker": ticker, "isin": None}),
    })
    return repo.save_quote(response).instrument_id


def _service(repo: QuoteRepository) -> CachedQuoteService:
    response = _response(_now())
    return CachedQuoteService(FakeQuoteService(response), repo, 6, empty_daily_sync(repo))


def _put_justetf(repo: QuoteRepository, instrument_id: int, value: float) -> None:
    with repo._connect() as connection:
        detail_store.put_provider(connection, instrument_id, "volatility",
                                  {"value": value, "source": "justetf"})


def test_aktie_zeigt_die_berechnete_volatilitaet(repo: QuoteRepository) -> None:
    instrument_id = _save(repo, "stock")
    repo.set_volatility(instrument_id, 26.11)

    detail = _service(repo).get_instrument_summary(instrument_id)["details"]["volatility"]

    assert detail["value"] == 26.11
    assert detail["source"] == "calculated"


def test_etf_zeigt_justetf_vor_der_berechnung(repo: QuoteRepository) -> None:
    instrument_id = _save(repo, "etf")
    repo.set_volatility(instrument_id, 11.09)
    _put_justetf(repo, instrument_id, 10.67)

    detail = _service(repo).get_instrument_summary(instrument_id)["details"]["volatility"]

    assert detail["value"] == 10.67
    assert detail["source"] == "justetf"


# ─── Stand des berechneten Werts ────────────────────────────────────────────


def _stock_with_closes(repo: QuoteRepository, days: int) -> tuple[CachedQuoteService, str, str]:
    """Aktie mit `days` Tagesschlusskursen; gibt Dienst, ISIN und letztes Datum zurück."""
    response = _response(_now()).model_copy(update={"type": "stock"})
    instrument_id = repo.save_quote(response).instrument_id
    today = date.today()
    rows = [
        {"date": (today - timedelta(days=days - index)).isoformat(),
         "close": 100.0 + (index % 3), "currency": "EUR"}
        for index in range(days)
    ]
    repo.upsert_daily_closes(instrument_id, rows)
    service = CachedQuoteService(FakeQuoteService(response), repo, 6, empty_daily_sync(repo))
    last_date = rows[-1]["date"] if rows else ""
    return service, response.identity.isin, last_date


def _volatility_detail(service: CachedQuoteService, repo: QuoteRepository, isin: str) -> dict:
    instrument_id = repo.get_instrument_by_isin(isin)["id"]
    return service.get_instrument_summary(instrument_id)["details"]["volatility"]


def test_berechnete_volatilitaet_traegt_das_datum_des_letzten_schlusskurses(
    repo: QuoteRepository,
) -> None:
    service, isin, last_date = _stock_with_closes(repo, 30)

    service.refresh_one(isin)

    detail = _volatility_detail(service, repo, isin)
    assert detail["value"] is not None
    assert detail["as_of"] == last_date


def test_wiederhergestellte_volatilitaet_behaelt_ihr_datum(repo: QuoteRepository) -> None:
    """Fehlen Tageskurse, bleibt der alte Wert stehen, und mit ihm sein Stand."""
    service, isin, _ = _stock_with_closes(repo, 0)
    instrument_id = repo.get_instrument_by_isin(isin)["id"]
    repo.set_volatility(instrument_id, 12.5, as_of="2026-09-30")

    service.refresh_one(isin)

    detail = _volatility_detail(service, repo, isin)
    assert detail["value"] == 12.5
    assert detail["as_of"] == "2026-09-30"


# ─── Öffentlicher Weg: GET /fields und GET /instruments ──────────────────────


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Die echte App mit Lifespan auf der temporären Datenbank aus `conftest`."""
    with TestClient(app) as opened:
        yield opened


def test_fields_deklariert_die_berechnete_volatilitaet_fuer_aktien_und_fonds(
    client: TestClient,
) -> None:
    fields = client.get("/fields").json()["details"]
    volatility = next(field for field in fields if field["name"] == "volatility")
    calculated = next(scope for scope in volatility["scopes"] if scope["source"] == "calculated")

    assert volatility["sources"] == ["justetf", "calculated"]
    assert {"stock", "fund"} <= set(calculated["instrument_types"])
    assert calculated["identity_kinds"] == ["listed", "pair"]


def test_instruments_liefert_berechnete_und_justetf_volatilitaet(client: TestClient) -> None:
    repo = QuoteRepository(get_settings().database_path)
    stock_id = _save(repo, "stock", "APC.DE")
    repo.set_volatility(stock_id, 26.11, as_of="2026-10-01")
    etf_id = _save(repo, "etf", "EUNL.DE")
    repo.set_volatility(etf_id, 11.09)
    _put_justetf(repo, etf_id, 10.67)

    by_symbol = {item["symbol"]: item for item in client.get("/instruments").json()}

    assert by_symbol["APC.DE"]["details"]["volatility"]["value"] == 26.11
    assert by_symbol["APC.DE"]["details"]["volatility"]["source"] == "calculated"
    assert by_symbol["APC.DE"]["details"]["volatility"]["as_of"] == "2026-10-01"
    assert by_symbol["EUNL.DE"]["details"]["volatility"]["value"] == 10.67
    assert by_symbol["EUNL.DE"]["details"]["volatility"]["source"] == "justetf"


@pytest.fixture
def refresh_api() -> Iterator[tuple[TestClient, QuoteRepository]]:
    """Echte App, deren Dienst auf der Temp-DB einen netzfreien Kursdienst nutzt."""
    with TestClient(app) as opened:
        repository = QuoteRepository(get_settings().database_path)
        yield opened, repository
    app.dependency_overrides.clear()


def _use_service(service: CachedQuoteService) -> None:
    app.dependency_overrides[get_cached_quote_service] = lambda: service


def _api_volatility(client: TestClient, symbol: str) -> dict:
    by_symbol = {item["symbol"]: item for item in client.get("/instruments").json()}
    return by_symbol[symbol]["details"]["volatility"]


def test_refresh_liefert_den_stand_bis_zur_api(
    refresh_api: tuple[TestClient, QuoteRepository],
) -> None:
    client, repository = refresh_api
    service, isin, last_date = _stock_with_closes(repository, 30)
    _use_service(service)

    assert client.post(f"/refresh/{isin}").status_code == 200

    detail = _api_volatility(client, "VGWL.DE")
    assert detail["source"] == "calculated"
    assert detail["as_of"] == last_date


def test_wiederhergestellter_wert_behaelt_seinen_stand_bis_zur_api(
    refresh_api: tuple[TestClient, QuoteRepository],
) -> None:
    client, repository = refresh_api
    service, isin, _ = _stock_with_closes(repository, 0)
    repository.set_volatility(repository.get_instrument_by_isin(isin)["id"], 12.5,
                              as_of="2026-09-30")
    _use_service(service)

    assert client.post(f"/refresh/{isin}").status_code == 200

    detail = _api_volatility(client, "VGWL.DE")
    assert detail["value"] == 12.5
    assert detail["as_of"] == "2026-09-30"
