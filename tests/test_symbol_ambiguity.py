"""Ein mehrdeutiges Symbol ist ein `409`, kein geratenes Listing (T-24).

`symbol` ist Anzeigename und **nicht** garantiert eindeutig: Seit T-21 `US` in
`XNYS` und `XNAS` zerlegt, tragen `AAPL/XNAS` und `AAPL/XNYS` beide den Alias
`AAPL`. T-24 hat daraus eine Zusage gemacht — Symbol-Endpunkte antworten dann
mit `409` samt Kandidatenliste, statt still das Falsche zu treffen.

Umgesetzt war sie bis Runde 45 nirgends. Der Lookup lautete
`ORDER BY id LIMIT 1`, und `DELETE /instruments/by-symbol/{symbol}` löschte
sogar alle passenden Zeilen auf einmal.

**Beide Sorten Weg stehen hier**, und das ist keine Symmetrie um ihrer selbst
willen: Auf dem lesenden Weg kostet das Raten eine falsche Auskunft, auf dem
verändernden die Daten. Ein Test nur über `/quote` hätte den schlimmeren Fall
nicht berührt.

Geprüft wird über die **echte** Kette mit echter SQLite-Datei; ersetzt sind
allein die Außengrenzen.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.main import app
from app.providers.base import RawQuote, ResolvedInstrument
from app.repository import REASON_SYMBOL_AMBIGUOUS, QuoteRepository
from stockinfo_plugin.types import NotFound
from tests.boundaries import wire_real_chain

# Der Alias, den sich die US-Plätze teilen — sie führen kein Suffix.
_ALIAS = "AAPL"
_SEEN = "2026-08-01T00:00:00+00:00"


class _QuoteSource:
    """Die Außengrenze zur Kursquelle."""

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote:
        # Seit T-23 bekommt eine Kursquelle die **aufgelöste Identität**, nicht
        # nur das Symbol: Der Plugin-Vertrag fragt mit `ticker` und `mic`, und
        # aus einem Symbol ohne Suffix ließe sich die Börse nicht eindeutig
        # zurückgewinnen.
        return RawQuote(
            symbol=instrument.symbol,
            name=f"{instrument.symbol} Testpapier",
            price=101.0,
            quote_time="2026-08-27T17:00:00+00:00",
            currency="USD",
            type="equity",
        )


class _NoResolver:
    """Keine zusätzliche Beschreibung zum genannten Listing."""

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        return NotFound()

    def resolve_symbol(self, symbol: str):
        return NotFound()


@pytest.fixture
def client_and_repo(tmp_path: Path) -> Iterator[tuple[TestClient, QuoteRepository]]:
    service, repository = wire_real_chain(
        str(tmp_path / "mehrdeutig.db"), _QuoteSource(), _NoResolver()
    )
    app.dependency_overrides[get_cached_quote_service] = lambda: service
    yield TestClient(app), repository
    app.dependency_overrides.clear()


def _two_listings(repository: QuoteRepository) -> None:
    """Legt zwei echte Listings desselben Wertpapiers mit demselben Alias an.

    Kein konstruierter Sonderfall: Genau diesen Bestand erzeugt der Aufnahmeweg
    aus `AAPL.XNAS` und `AAPL.XNYS`, und `#2f` im Smoke-Script hält fest, dass
    beide nebeneinander stehen sollen. Mehrdeutig ist nicht der Bestand,
    sondern die **Frage** nach dem Alias.
    """
    with repository._connect() as connection:
        connection.executemany(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic, exchange, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (None, _ALIAS, _SEEN, "nasdaq-1", _ALIAS, "XNAS", "NASDAQ", "USD"),
                (None, _ALIAS, _SEEN, "nyse-1", _ALIAS, "XNYS", "NYSE", "USD"),
            ],
        )


def _row_count(repository: QuoteRepository) -> int:
    with repository._connect() as connection:
        return connection.execute(
            "SELECT COUNT(*) AS total FROM instruments"
        ).fetchone()["total"]


def test_der_lesende_weg_raet_nicht_mehr(client_and_repo) -> None:
    """**Befund 1 aus Runde 44** — `GET /quote?symbol=AAPL` gab still ein Listing.

    Auf `36d54ce` antwortete der Endpunkt mit `200` und `mic: XNAS`, weil der
    Lookup die ältere Zeile nahm. Der Aufrufer sah eine gewöhnliche Antwort und
    hatte keinen Anhaltspunkt, dass eine zweite Notierung existiert.
    """
    client, repository = client_and_repo
    _two_listings(repository)

    response = client.get("/quote", params={"symbol": _ALIAS})

    assert response.status_code == 409, response.text
    assert response.json()["code"] == REASON_SYMBOL_AMBIGUOUS


def test_der_rumpf_nennt_die_kandidaten_samt_listing_id(client_and_repo) -> None:
    """Ohne Kandidaten wäre der `409` eine Sackgasse.

    Der Aufrufer hat nur das mehrdeutige Symbol; erst die `listing_id` je
    Kandidat gibt ihm etwas Eindeutiges in die Hand. Die Form steht seit T-24
    in `contract/fixtures/quote-409-ambiguous-symbol.json` fest — geprüft wird
    deshalb gegen genau diese Feldmenge und nicht gegen das, was gerade
    herauskommt.
    """
    client, repository = client_and_repo
    _two_listings(repository)

    body = client.get("/quote", params={"symbol": _ALIAS}).json()

    assert set(body) == {"detail", "code", "params", "candidates"}
    assert body["params"] == {"symbol": _ALIAS}
    assert [candidate["mic"] for candidate in body["candidates"]] == ["XNAS", "XNYS"]
    assert {candidate["listing_id"] for candidate in body["candidates"]} == {
        "nasdaq-1",
        "nyse-1",
    }
    for candidate in body["candidates"]:
        assert set(candidate) == {"listing_id", "symbol", "mic", "exchange", "isin"}


def test_der_veraendernde_weg_loescht_nicht_mehr_beide(client_and_repo) -> None:
    """**Der schwerere Fall** — `DELETE by-symbol` traf alle passenden Zeilen.

    `DELETE FROM instruments WHERE symbol = ?` hat bei zwei gleichnamigen
    Listings beide entfernt, samt Kurshistorie über den Cascade. Das ist keine
    falsche Auskunft mehr, die man wiederholen kann, sondern Datenverlust auf
    einen Klick.

    Geprüft wird deshalb **beides**: der Status und dass hinterher noch zwei
    Zeilen dastehen. Ein Test nur auf den Status wäre grün geblieben, hätte der
    `409` nach dem Löschen gegriffen.
    """
    client, repository = client_and_repo
    _two_listings(repository)

    response = client.delete(f"/instruments/by-symbol/{_ALIAS}")

    assert response.status_code == 409, response.text
    assert response.json()["code"] == REASON_SYMBOL_AMBIGUOUS
    assert _row_count(repository) == 2, "der Bestand darf den Konflikt überleben"


def test_auch_das_nachtragen_einer_isin_trifft_nicht_die_aeltere(
    client_and_repo,
) -> None:
    """Der dritte verändernde Weg — dieselbe Regel, dieselbe Quelle.

    `PUT .../isin` schrieb die ISIN in die älteste Zeile. Der Benutzer hätte
    damit ein Papier an einem Handelsplatz identifiziert, den er nicht gemeint
    hat, und es nicht gemerkt: Die Antwort war `200`.
    """
    client, repository = client_and_repo
    _two_listings(repository)

    response = client.put(
        f"/instruments/by-symbol/{_ALIAS}/isin", json={"isin": "US0378331005"}
    )

    assert response.status_code == 409, response.text
    assert response.json()["code"] == REASON_SYMBOL_AMBIGUOUS
    with repository._connect() as connection:
        isins = [
            row["isin"]
            for row in connection.execute("SELECT isin FROM instruments ORDER BY id")
        ]
    assert isins == [None, None], "keine Zeile darf die ISIN bekommen haben"


def test_die_fixture_zeigt_was_der_dienst_wirklich_antwortet(client_and_repo) -> None:
    """Die Fixture ist eine Zusage nach außen — und war eine zweite Wahrheit.

    `contract/fixtures/` wird von StockPortfolio gelesen, **ohne** StockInfo zu
    starten. Eine Fixture, die niemand gegen die Laufzeit hält, beschreibt
    darum irgendwann einen Dienst, den es nicht gibt. Genau das war der Fall:
    Sie zeigte zwei Kandidaten mit **derselben** ISIN — einen Zustand, den
    `isin TEXT UNIQUE` verbietet.

    Der Test stellt den Bestand der Fixture nach und vergleicht ihren Rumpf
    Feld für Feld mit dem, was herauskommt.
    """
    client, repository = client_and_repo
    fixture = json.loads(
        (
            Path(__file__).resolve().parent.parent
            / "contract"
            / "fixtures"
            / "quote-409-ambiguous-symbol.json"
        ).read_text(encoding="utf-8")
    )
    expected = fixture["response"]["body"]
    with repository._connect() as connection:
        connection.executemany(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic, exchange) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    candidate["isin"],
                    candidate["symbol"],
                    _SEEN,
                    candidate["listing_id"],
                    candidate["symbol"],
                    candidate["mic"],
                    candidate["exchange"],
                )
                for candidate in expected["candidates"]
            ],
        )

    response = client.get("/quote", params={"symbol": expected["params"]["symbol"]})

    assert response.status_code == fixture["response"]["status"]
    assert response.json() == expected, "Fixture und Laufzeit sagen Verschiedenes zu"


def test_ein_eindeutiges_symbol_bleibt_unberuehrt(client_and_repo) -> None:
    """Das Gegenstück — sonst bestünde auch ein „wirft immer" alle Tests oben.

    Genau ein Listing mit diesem Alias: Der Weg muss durchlaufen, sonst hätte
    die Regel den Normalfall mit erschlagen. `AAPL.XNAS` ist im Bestand die
    Regel, nicht die Ausnahme.
    """
    client, repository = client_and_repo
    with repository._connect() as connection:
        connection.execute(
            "INSERT INTO instruments (isin, symbol, first_seen, listing_id, "
            "ticker, mic, exchange, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (None, _ALIAS, _SEEN, "nasdaq-1", _ALIAS, "XNAS", "NASDAQ", "USD"),
        )

    response = client.get("/quote", params={"symbol": _ALIAS})

    assert response.status_code == 200, response.text
    assert response.json()["identity"]["mic"] == "XNAS"


def test_zwei_listings_duerfen_weiterhin_nebeneinander_entstehen(
    client_and_repo,
) -> None:
    """Die Mehrdeutigkeit gilt der **Frage**, nicht dem Bestand.

    `AAPL/XNAS` neben `AAPL/XNYS` ist seit T-21 der ausdrücklich gewollte
    Zustand (`#2f`). Der Aufnahmeweg nennt die Börse mit und ist damit nie
    mehrdeutig — er darf durch die neue Regel nicht mit abgewiesen werden.
    Ohne diesen Test wäre die schärfere Fassung „jedes doppelte Symbol ist ein
    Fehler" ebenfalls grün gelaufen.
    """
    client, repository = client_and_repo

    first = client.post("/instruments/intake", json={"identifier": "AAPL.XNAS"})
    second = client.post("/instruments/intake", json={"identifier": "AAPL.XNYS"})

    assert (first.status_code, second.status_code) == (201, 201), second.text
    assert _row_count(repository) == 2
