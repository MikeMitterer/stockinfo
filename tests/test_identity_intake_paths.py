"""Jeder Aufnahmeweg erzeugt dieselbe Identität (T-21, Teil 2, Runde 3).

Verify `#5` gilt für **das Aufnehmen eines neuen Papiers** — nicht für einen
bestimmten Weg dorthin. StockInfo hat zwei: über die ISIN (dann löst der
Resolver auf) und über das fertige Symbol (dann nicht). Der zweite ging an der
Identitätsbildung vorbei, und keiner der Tests aus Runde 2 hat es gesehen:

* `tests/test_identity_creation.py` übergibt dem Repository die fertige
  Identität von Hand — das prüft die Speicherung, nicht ihre Herkunft.
* `tests/test_quote_service.py` prüft nur den ISIN-Pfad.

Deshalb läuft hier die **echte Kette**: Router → Cache-Dienst → Quote-Service →
Repository, mit echter SQLite-Datei. Ersetzt sind allein die Außengrenzen, an
denen sonst das Netz hinge — Kursquelle, ETF-Anreicherung, EOD-Historie.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.db import init_db
from app.main import app
from app.providers.base import RawQuote
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService
from stockinfo_plugin.types import NotFound
from tests.boundaries import EmptyDailyCloseProvider, EmptyEtfEnricher


class _QuoteSource:
    """Die Außengrenze zur Kursquelle — hier hinge sonst yfinance am Netz."""

    def fetch_quote(self, symbol: str) -> RawQuote:
        return RawQuote(
            symbol=symbol,
            price=123.45,
            quote_time="2026-08-23T17:00:00+00:00",
            currency="EUR",
            type="etf",
        )


class _NoResolver:
    """Auf dem Symbol-Weg wird nicht aufgelöst — es gibt keine ISIN zu fragen.

    Genau das ist der Punkt: Die Identität kann hier **nicht** aus einer
    Auflösung kommen. Sie muss aus dem Symbol selbst entstehen, nach derselben
    Regel, mit der die Migration den Bestand zerlegt hat.
    """

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        return NotFound()


@pytest.fixture
def client_and_repo(tmp_path: Path) -> Iterator[tuple[TestClient, QuoteRepository]]:
    db_path = str(tmp_path / "aufnahme.db")
    init_db(db_path)
    repository = QuoteRepository(db_path)
    service = CachedQuoteService(
        QuoteService(_QuoteSource(), EmptyEtfEnricher(), _NoResolver()),
        repository,
        ttl_hours=0,
        daily_sync=DailyCloseSync(repository, EmptyDailyCloseProvider()),
    )

    app.dependency_overrides[get_cached_quote_service] = lambda: service
    yield TestClient(app), repository
    app.dependency_overrides.clear()


def _row(repository: QuoteRepository, symbol: str) -> dict:
    with repository._connect() as connection:
        row = connection.execute(
            "SELECT ticker, mic, identity_status, listing_id FROM instruments "
            "WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    return dict(row) if row else {}


def test_ein_zerlegbares_symbol_wird_zugeordnet(client_and_repo) -> None:
    """Der Befund aus Runde 3: `VGWL.DE` landete als offener Fall.

    Das Symbol ist eindeutig zerlegbar — dieselbe Rechnung, die die Migration
    auf den ganzen Bestand angewendet hat. Dass hier kein Resolver läuft,
    ändert daran nichts: Die Regel hängt am Symbol, nicht am Weg.
    """
    client, repository = client_and_repo

    response = client.get("/quote", params={"symbol": "VGWL.DE"})

    assert response.status_code == 200
    assert _row(repository, "VGWL.DE") | {"listing_id": None} == {
        "ticker": "VGWL",
        "mic": "XETR",
        "identity_status": "resolved",
        "listing_id": None,
    }


def test_auch_dieser_weg_vergibt_eine_listing_id(client_and_repo) -> None:
    """Die dauerhafte Kennung darf nicht am Aufnahmeweg hängen."""
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "VGWL.DE"})

    assert _row(repository, "VGWL.DE")["listing_id"]


def test_ein_suffixloses_symbol_bleibt_sichtbar_offen(client_and_repo) -> None:
    """`AAPL` nennt keine Börse — und der Weg wird trotzdem nicht verweigert.

    **Hier unterscheidet sich der Symbol-Weg bewusst vom ISIN-Weg.** Dort
    wählt StockInfo aus mehreren Notierungen eine aus; eine halb geratene
    Identität wäre eine Entscheidung, die niemand getroffen hat, also wird
    abgelehnt. Hier nennt der Aufrufer das Listing selbst — ihm die Auskunft zu
    verweigern, weil die Börsentabelle für suffixlose Symbole nur einen
    Sammelcode führt, nähme ihm eine Abfrage weg, die heute funktioniert.

    Die Zeile entsteht deshalb **offen und sichtbar**, mit demselben Status,
    den die Migration vergibt. Teil 3 listet sie zur Zuordnung von Hand auf.
    """
    client, repository = client_and_repo

    response = client.get("/quote", params={"symbol": "AAPL"})

    assert response.status_code == 200
    row = _row(repository, "AAPL")
    assert (row["ticker"], row["mic"]) == (None, None)
    assert row["identity_status"] == "legacy_unresolved"


def test_eine_fremde_schreibweise_wird_auch_hier_nicht_uebernommen(
    client_and_repo,
) -> None:
    """`BRK-B.DE` hat ein bekanntes Suffix — der Ticker bleibt trotzdem Yahoos.

    Ohne diese Zeile könnte der Symbol-Weg eine Schreibweise in das kanonische
    Feld schreiben, die der ISIN-Weg zurückweist.
    """
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "BRK-B.DE"})

    row = _row(repository, "BRK-B.DE")
    assert (row["ticker"], row["mic"]) == (None, None)


def test_ein_bekanntes_papier_wird_beim_naechsten_kurs_nachgetragen(
    client_and_repo,
) -> None:
    """Der dritte Weg — und der, über den der Scheduler läuft.

    Ein Papier, das schon in der Datenbank steht, geht nicht mehr durch die
    Aufnahme, sondern durch `get_quote_for_known`. Auch dort entstand die
    Identität bisher nicht: Eine Zeile, die einmal offen war, blieb es bei
    jedem weiteren Kurs — obwohl ihr Symbol längst zerlegbar ist.

    Genau diese Lücke hatte ich in Runde 2 als „Nachtrag passiert nur auf dem
    ISIN-Weg" ins Ticket geschrieben. Sie gehört nicht in eine Fußnote,
    sondern behoben: Die Rechnung ist dieselbe und kostet nichts.
    """
    client, repository = client_and_repo
    # Der Zustand, den die Migration für ein unzerlegbares Symbol hinterlässt —
    # hier absichtlich für ein zerlegbares gesetzt, wie ihn der Symbol-Weg vor
    # dieser Runde erzeugt hat.
    with repository._connect() as connection:
        connection.execute(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "identity_status) VALUES (?, ?, ?, ?, ?)",
            ("IE00B4L5Y983", "EUNL.DE", "2026-08-01T00:00:00+00:00", "alt-1",
             "legacy_unresolved"),
        )

    client.get("/quote", params={"symbol": "EUNL.DE"})

    row = _row(repository, "EUNL.DE")
    assert (row["ticker"], row["mic"]) == ("EUNL", "XETR")
    assert row["identity_status"] == "resolved"
    assert row["listing_id"] == "alt-1", "die dauerhafte Kennung bleibt"


def test_der_resolver_ist_auf_diesem_weg_wirklich_stumm(client_and_repo) -> None:
    """Die Gegenprobe zum Aufbau dieses Tests.

    Liefe hier doch ein Resolver, käme die Identität aus ihm und der Test
    belegte nicht, was er behauptet. `_NoResolver` antwortet auf jede ISIN mit
    `NotFound` — was `VGWL.DE` zugeordnet hat, kann also nur das Symbol sein.
    """
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "VGWL.DE"})

    assert _row(repository, "VGWL.DE")["ticker"] == "VGWL"
    assert isinstance(_NoResolver().resolve_isin("IE00B3RBWM25"), NotFound)
