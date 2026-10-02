"""Die berechnete Volatilität gilt für alle Gattungen, nicht nur für ETFs.

StockInfo berechnet die Volatilität aus den Tageskursen jedes Instruments.
Angezeigt wird ein Detailwert aber nur, wenn eine Deklaration ihn für Gattung
und Identitätsart freigibt. Bisher deklarierte nur justETF `volatility`, und
nur für ETFs und ETCs; bei Aktien und Fonds blieb der Wert unsichtbar.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import detail_store
from app.config import get_settings
from app.container import get_sources_config
from app.db import init_db
from app.detail_models import DetailDefinition
from app.main import app
from app.repository import QuoteRepository
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
    repo.set_volatility(stock_id, 26.11)
    etf_id = _save(repo, "etf", "EUNL.DE")
    repo.set_volatility(etf_id, 11.09)
    _put_justetf(repo, etf_id, 10.67)

    by_symbol = {item["symbol"]: item for item in client.get("/instruments").json()}

    assert by_symbol["APC.DE"]["details"]["volatility"]["value"] == 26.11
    assert by_symbol["APC.DE"]["details"]["volatility"]["source"] == "calculated"
    assert by_symbol["EUNL.DE"]["details"]["volatility"]["value"] == 10.67
    assert by_symbol["EUNL.DE"]["details"]["volatility"]["source"] == "justetf"
