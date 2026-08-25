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
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteService
from stockinfo_plugin.types import NotFound
from tests.boundaries import EmptyEtfEnricher, empty_daily_sync


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
        daily_sync=empty_daily_sync(repository),
    )

    app.dependency_overrides[get_cached_quote_service] = lambda: service
    yield TestClient(app), repository
    app.dependency_overrides.clear()


def _row(repository: QuoteRepository, symbol: str) -> dict:
    with repository._connect() as connection:
        row = connection.execute(
            "SELECT ticker, mic, listing_id FROM instruments WHERE symbol = ?",
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
        "listing_id": None,
    }


def test_auch_dieser_weg_vergibt_eine_listing_id(client_and_repo) -> None:
    """Die dauerhafte Kennung darf nicht am Aufnahmeweg hängen."""
    client, repository = client_and_repo

    client.get("/quote", params={"symbol": "VGWL.DE"})

    assert _row(repository, "VGWL.DE")["listing_id"]


@pytest.mark.parametrize(
    ("symbol", "warum"),
    [
        ("AAPL", "nennt keine Börse"),
        ("BRK-B.DE", "trägt Yahoos Schreibweise im Ticker"),
    ],
    ids=["suffixlos", "fremde_schreibweise"],
)
def test_ein_unzuordenbares_symbol_wird_abgelehnt(
    client_and_repo, symbol: str, warum: str
) -> None:
    """**Die Umkehr aus T-21 Teil 3** — hier stand das Gegenteil.

    Der Test hieß „bleibt sichtbar offen" und begründete das so: Auf dem
    ISIN-Weg wähle StockInfo aus mehreren Notierungen eine aus, eine halb
    geratene Identität wäre also eine Entscheidung, die niemand getroffen hat.
    Hier nenne der Aufrufer das Listing dagegen selbst; ihm die Auskunft zu
    verweigern, nähme ihm eine Abfrage weg, die funktioniert.

    **Das Argument hielt nicht.** Genau dieser Weg war die Quelle, die
    dauerhaft offene Zeilen nachlieferte — und `get_quote_for_known` schloss
    sie nie, weil es nicht auflöst, sondern Kurse holt. Der Bestand füllte
    sich also schneller mit halben Identitäten, als eine Migration sie
    aufräumen konnte.

    Geraten wird weiterhin nicht. Neu ist nur, dass das Nichtwissen zu einer
    **Ablehnung** führt statt zu einer Zeile, die es konserviert.
    """
    client, repository = client_and_repo

    response = client.get("/quote", params={"symbol": symbol})

    assert response.status_code == 400, warum
    assert _row(repository, symbol) == {}, "eine halbe Zeile ist entstanden"


def test_die_ablehnung_nennt_beide_auswege(client_and_repo) -> None:
    """Ein `400`, das nur „geht nicht" sagt, ist eine Sackgasse.

    Der Benutzer hat zwei Möglichkeiten, und beide gehören in den Text: das
    Provider-Suffix und den echten MIC. Die ISIN wird als zuverlässigster Weg
    genannt, weil sie ohne Kenntnis der Schreibweise auskommt.
    """
    client, _ = client_and_repo

    detail = client.get("/quote", params={"symbol": "AAPL"}).json()["detail"]

    assert "EUNL.DE" in detail
    assert "EUNL.XETR" in detail
    assert "ISIN" in detail


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

    **Der Aufbau musste wechseln.** Vorher stand hier eine Zeile *ohne*
    Identität — der Zustand, den die alte Migration hinterließ. Den gibt es
    seit T-21 Teil 3 nicht mehr; `NOT NULL` lässt ihn nicht entstehen. Geprüft
    wird deshalb der Fall, den es weiterhin gibt: eine **überholte**
    Zuordnung. Der geprüfte Weg ist derselbe, und die Zusage auch — was
    `get_quote_for_known` über die Identität weiß, trägt es nach.
    """
    client, repository = client_and_repo
    # Eine Zuordnung, die nicht mehr zum Symbol passt: `EUNL.DE` liegt an
    # Xetra, nicht in Mailand. So sieht die Zeile aus, nachdem jemand die
    # Vorzugsbörse umgestellt hat und dasselbe Papier neu aufgelöst wurde.
    with repository._connect() as connection:
        connection.execute(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic) VALUES (?, ?, ?, ?, ?, ?)",
            ("IE00B4L5Y983", "EUNL.DE", "2026-08-01T00:00:00+00:00", "alt-1",
             "EUNL", "XMIL"),
        )

    client.get("/quote", params={"symbol": "EUNL.DE"})

    row = _row(repository, "EUNL.DE")
    assert (row["ticker"], row["mic"]) == ("EUNL", "XETR")
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
