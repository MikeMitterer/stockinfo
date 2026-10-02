"""Die berechnete Volatilität gilt für alle Gattungen, nicht nur für ETFs.

StockInfo berechnet die Volatilität aus den Tageskursen jedes Instruments.
Angezeigt wird ein Detailwert aber nur, wenn eine Deklaration ihn für Gattung
und Identitätsart freigibt. Bisher deklarierte nur justETF `volatility`, und
nur für ETFs und ETCs; bei Aktien und Fonds blieb der Wert unsichtbar.
"""

import pytest

from app import detail_store
from app.config import get_settings
from app.container import get_sources_config
from app.db import init_db
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService
from app.sources_registry import detail_definitions
from tests.boundaries import empty_daily_sync
from tests.test_quote_cache import FakeQuoteService, _now, _response


@pytest.fixture
def catalog() -> list:
    return detail_definitions(get_sources_config(), get_settings())


@pytest.fixture
def repo(tmp_path, catalog) -> QuoteRepository:
    path = str(tmp_path / "volatility.db")
    init_db(path)
    repository = QuoteRepository(path)
    repository.detail_catalog(catalog)
    return repository


def _volatility(catalog: list):
    return next(definition for definition in catalog if definition.name == "volatility")


@pytest.mark.parametrize("instrument_type", ["stock", "fund", "etf", "etc", "crypto", "bond"])
def test_volatilitaet_ist_fuer_jede_gattung_deklariert(catalog, instrument_type) -> None:
    assert _volatility(catalog).applies(instrument_type, "listed")


def test_justetf_steht_vor_der_berechnung(catalog) -> None:
    """Bei ETFs gilt weiter justETFs Wert, die Berechnung füllt die Lücke."""
    assert _volatility(catalog).sources == ["justetf", "calculated"]


def _summary(repo: QuoteRepository, instrument_type: str) -> tuple[dict, int]:
    response = _response(_now()).model_copy(update={"type": instrument_type})
    saved = repo.save_quote(response)
    service = CachedQuoteService(FakeQuoteService(response), repo, 6, empty_daily_sync(repo))
    return service, saved.instrument_id


def test_aktie_zeigt_die_berechnete_volatilitaet(repo) -> None:
    service, instrument_id = _summary(repo, "stock")
    repo.set_volatility(instrument_id, 26.11)

    detail = service.get_instrument_summary(instrument_id)["details"]["volatility"]

    assert detail["value"] == 26.11
    assert detail["source"] == "calculated"


def test_etf_zeigt_justetf_vor_der_berechnung(repo) -> None:
    service, instrument_id = _summary(repo, "etf")
    repo.set_volatility(instrument_id, 11.09)
    with repo._connect() as connection:
        detail_store.put_provider(connection, instrument_id, "volatility",
                                  {"value": 10.67, "source": "justetf"})

    detail = service.get_instrument_summary(instrument_id)["details"]["volatility"]

    assert detail["value"] == 10.67
    assert detail["source"] == "justetf"
