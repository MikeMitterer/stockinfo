"""Die beiden neuen Identitätsformen, über die **echte** Kette (T-31).

**Diese Datei entsteht vor der Umsetzung, und das ist der ganze Punkt.**
Runde 4 hat gezeigt, was passiert, wenn es umgekehrt läuft: Die Union war in
Vertrag, Schema, Core, REST und Oberfläche eingebaut, 828 Tests waren grün —
und keine einzige Coin und keine einzige Anleihe kam durch. Sämtliche Fälle
benutzten `ListedIdentity`, also genau die Form, die es vorher schon gab.
Ein Test, der nach der Implementierung entsteht, bestätigt den gebauten
Lösungsweg; er misst nicht die Anforderung.

Die Orakel hier stammen deshalb aus der **Verify-Matrix des Tickets** und
nicht aus dem Code:

============ ================================================================
Matrix `#5`  Die Paar-Identität entsteht aus dem Gattungs-Befund der Quelle,
             nie aus der Symbolform
Matrix `#6`  Eine nicht aufgenommene Gattung wird mit eigener Kennung
             `unsupported_instrument_type` abgelehnt
Matrix `#7`  Für ein Paar muss die Kurswährung `quote_currency` entsprechen —
             eine Abweichung ist ein Datenfehler, keine stille Umrechnung
Matrix `#9`  `BTC-EUR` als `pair`, ein Index als Ablehnung, eine Anleihe als
             `isin_only` samt `quote_unavailable` ohne liefernde Quelle
============ ================================================================

**Bewusst mechanismusfrei formuliert.** Wie ein Paar hereinkommt, ist beim
Schreiben dieser Datei noch offen (siehe „Offen: wie `BTC-EUR` über den
By-Symbol-Weg hereinkommt" im Ticket). Ließe sich das Orakel ohne diese
Entscheidung nicht formulieren, prüfte es den Weg statt des Ergebnisses —
und wäre damit genau der Test, den Runde 4 als wertlos entlarvt hat. Geprüft
wird deshalb nur, was **hinten herauskommt**: die gespeicherte Zeile und die
öffentliche Antwort.

Gelaufen wird über den echten Eintrittspfad mit echter SQLite-Datei;
ersetzt sind allein die Außengrenzen, an denen sonst das Netz hinge.

**Orakel und Verdrahtung sind zweierlei, und die Grenze ist scharf.** Die
`assert`-Zeilen sind das Orakel; sie stehen fest und werden beim Bauen nicht
angefasst. Die Fakes darüber sind Verdrahtung: An welcher Rolle die App
nachfragt, entscheidet der Entwurf, und die Doubles folgen ihm. Wer beim
Grünmachen eine Zusicherung ändert, hat den Test an die Lösung angepasst
statt umgekehrt.

**Was diese Datei schon vor der ersten Produktzeile entschieden hat.** Der
Index-Fall hat einen der drei erwogenen Wege ausgeschlossen: `^GDAXI` trägt
keinen Bindestrich, also lässt sich daraus keine Paar-Identität vorschlagen,
also wird niemand gefragt — und ohne Frage gibt es keinen Gattungs-Befund
und damit kein `unsupported_instrument_type`, sondern nur den Zufallsbefund
der Symbolform, den Matrix `#6` ausdrücklich verbietet. Der „vorschlagen und
bestätigen lassen"-Weg, zu dem ich neigte, kann `#6` nicht erfüllen. Das
wäre nach der Implementierung teuer aufgefallen.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.main import app
from app.plugin_adapters import ResolverAdapter, _instrument_from
from app.plugins.yahoo_search_resolver import YahooSearchResolverPlugin
from app.providers.base import RawQuote, ResolvedInstrument
from app.resolver import CompositeResolver
from app.repository import QuoteRepository
from stockinfo_plugin.types import (
    IsinOnlyIdentity,
    NotResponsible,
    Resolved,
)
from tests.boundaries import wire_real_chain

# Eine echte Bundesanleihe — Prüfziffer gültig, damit die Aufnahme nicht schon
# an der Form scheitert und der Test die Gattung prüft statt der Eingabe.
_BUND_ISIN = "DE0001102531"


class _TypedQuoteSource:
    """Die Außengrenze zur Kursquelle, die eine **Gattung** meldet.

    Das ist der „Gattungs-Befund der Quelle" aus Matrix `#5` in seiner
    kleinsten Form: Die Quelle sagt, was das Papier ist; die App leitet es
    nicht aus dem Symbol ab.

    Args:
        instrument_type: Was die Quelle über die Gattung sagt.
        currency: Die Währung des gelieferten Kurses.
        delivers: Ob überhaupt ein Kurs kommt. ``False`` ist der Anleihenfall
            — zuständig, aber ohne Preis.
    """

    def __init__(
        self,
        instrument_type: str,
        currency: str = "EUR",
        delivers: bool = True,
    ) -> None:
        self._type = instrument_type
        self._currency = currency
        self._delivers = delivers

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        if not self._delivers:
            return None
        return RawQuote(
            symbol=instrument.symbol,
            price=94500.0,
            quote_time="2026-08-27T17:00:00+00:00",
            currency=self._currency,
            type=self._type,
        )


class _YahooSearch:
    """**Die** Außengrenze des Symbolwegs — hier hinge sonst `yf.Search`.

    Ersetzt wird genau das Netz, nicht ein StockInfo-Resolver. Genau daran ist
    Runde 5 gescheitert: Das damalige Double hing sich an die Stelle des
    Kern-Resolvers und umging Registry, `ResolverAdapter` und
    `YahooSearchResolverPlugin` — also alles, was die Fähigkeit ausmacht. Der
    Test war grün, und `BTC-EUR` kam im Produkt trotzdem nicht herein.

    Geliefert wird, was Yahoo liefert: eine Trefferliste mit `symbol`,
    `quoteType` und `exchange`. Was daraus wird, entscheidet die echte Kette.

    Args:
        quote_type: Yahoos Gattungskennung, etwa ``CRYPTOCURRENCY``.
        exchange: Yahoos Börsencode; ``None`` für Papiere ohne Handelsplatz.
        known: Ob Yahoo das Symbol überhaupt kennt.
    """

    def __init__(
        self, quote_type: str, exchange: str | None = None, known: bool = True
    ) -> None:
        self._quote_type = quote_type
        self._exchange = exchange
        self._known = known

    def __call__(self, term: str) -> object:
        quotes = (
            [
                {
                    "symbol": term,
                    "quoteType": self._quote_type,
                    "exchange": self._exchange,
                    "shortname": f"{term} aus der Suche",
                }
            ]
            if self._known
            else []
        )
        return type("SearchResult", (), {"quotes": quotes})()


class _BondResolver:
    """Ein Resolver, der eine Anleihe als `isin_only` zurückgibt.

    Er steht für OpenFIGI: Anleihen-ISINs sind dort bekannt, ein Listing gibt
    es nicht. Genau diese Form soll die App annehmen können.
    """

    def handles(self, isin: str) -> bool:
        return True

    SUPPORTED_KINDS = frozenset({"isin_only"})
    SUPPORTED_TYPES = frozenset({"bond"})

    def resolve_isin(self, isin: str):
        # Über dieselbe Übersetzung wie ein echtes Plugin: Die Kette spricht
        # `ResolvedInstrument`, der Vertrag `Resolved`.
        return _instrument_from(
            Resolved(
                identity=IsinOnlyIdentity(isin=isin),
                name="Bundesrepublik Deutschland",
                instrument_type="bond",
            ),
            fallback_isin=isin,
        )

    def resolve_symbol(self, symbol: str):
        return NotResponsible(reason="diese Grenze sucht nur über die ISIN")


def _real_resolver_chain(monkeypatch, search: _YahooSearch) -> object:
    """Der **echte** Resolver-Stapel, mit ersetzter Netzgrenze.

    `YahooSearchResolverPlugin` → `ResolverAdapter` → `CompositeResolver` —
    dieselbe Verkettung, die `app.container` im Betrieb baut. Ausgetauscht ist
    allein `yf.Search`; alles darüber ist Produktcode, und nur deshalb sagt
    ein grüner Lauf hier etwas über das Produkt aus.
    """
    monkeypatch.setattr("app.resolver.yf.Search", search)
    return CompositeResolver(ResolverAdapter(YahooSearchResolverPlugin(), "XETR"))


def _chain(
    db_path: str, source: object, resolver: object
) -> tuple[TestClient, QuoteRepository]:
    """Die echte Kette über einer frischen Datei — nur die Grenzen wechseln."""
    service, repository = wire_real_chain(db_path, source, resolver)
    app.dependency_overrides[get_cached_quote_service] = lambda: service
    return TestClient(app), repository


def _stored(repository: QuoteRepository, symbol: str) -> dict:
    """Die gespeicherte Zeile — die Identitätsspalten und die Gattung."""
    with repository._connect() as connection:
        row = connection.execute(
            "SELECT kind, ticker, mic, base, quote_currency, isin, type "
            "FROM instruments WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    return dict(row) if row else {}


@pytest.fixture
def crypto_chain(
    tmp_path: Path, monkeypatch
) -> Iterator[tuple[TestClient, QuoteRepository]]:
    """Die echte Kette; Yahoo meldet für `BTC-EUR` `CRYPTOCURRENCY`."""
    yield _chain(
        str(tmp_path / "crypto.db"),
        _TypedQuoteSource("crypto"),
        _real_resolver_chain(monkeypatch, _YahooSearch("CRYPTOCURRENCY")),
    )
    app.dependency_overrides.clear()


@pytest.fixture
def bond_chain(tmp_path: Path) -> Iterator[tuple[TestClient, QuoteRepository]]:
    """Eine Kette, die eine Anleihe auflöst, aber keinen Kurs liefert."""
    yield _chain(
        str(tmp_path / "bond.db"),
        _TypedQuoteSource("bond", delivers=False),
        _BondResolver(),
    )
    app.dependency_overrides.clear()


# ─── Matrix #5 und #9 · das Paar ──────────────────────────────────────────────


def test_ein_paar_wird_ueber_den_oeffentlichen_weg_aufgenommen(crypto_chain) -> None:
    """`BTC-EUR` kommt herein und liegt danach als Paar im Bestand.

    **Das Orakel nennt keinen Mechanismus.** Ob die Form über die
    Resolver-Kette, über einen bestätigten Vorschlag oder über ein Plugin
    entsteht, ist hier gleichgültig — geprüft wird, dass ein Benutzer eine
    Coin aufnehmen kann und dass sie danach als das dasteht, was sie ist.

    `isin` ist dabei ausdrücklich leer: Eine Kryptowährung hat keine, und ein
    erfundener Wert an dieser Stelle wäre schlimmer als ein fehlender.
    """
    client, repository = crypto_chain

    response = client.get("/quote", params={"symbol": "BTC-EUR"})

    assert response.status_code == 200, response.text
    assert response.json()["identity"] == {
        "kind": "pair",
        "base": "BTC",
        "quote_currency": "EUR",
    }
    assert _stored(repository, "BTC-EUR") == {
        "kind": "pair",
        "ticker": None,
        "mic": None,
        "base": "BTC",
        "quote_currency": "EUR",
        "isin": None,
        "type": "crypto",
    }


def test_die_gattung_entscheidet_die_quelle_und_nicht_der_bindestrich(
    tmp_path: Path, monkeypatch
) -> None:
    """Matrix `#5` wörtlich: Der Bindestrich allein macht kein Paar.

    Dasselbe Symbol, nur meldet die Quelle diesmal **kein** Krypto. Entstünde
    die Form aus der Symbolform, käme trotzdem ein Paar heraus — und genau
    das darf nicht passieren.

    Erwartet wird eine Ablehnung **mit dem Symbolform-Grund**, nicht mit einem
    Gattungsgrund: Ohne Krypto-Befund ist `BTC-EUR` schlicht ein Symbol ohne
    Börsensuffix, und mehr weiß die App darüber nicht.

    Der geprüfte Grund ist hier kein Beiwerk. Vor der Umsetzung wird dieser
    Fall ohnehin abgelehnt — auf den Status allein zu prüfen hieße, einen
    Test zu schreiben, der **aus dem falschen Grund** grün ist. Genau diese
    Sorte hat Runde 4 durchgelassen.
    """
    client, repository = _chain(
        str(tmp_path / "kein-paar.db"),
        _TypedQuoteSource("stock"),
        # Yahoo kennt das Symbol **nicht** — damit gibt es keinen
        # Gattungs-Befund, und der Bindestrich allein darf nichts bewirken.
        _real_resolver_chain(monkeypatch, _YahooSearch("EQUITY", known=False)),
    )
    try:
        response = client.get("/quote", params={"symbol": "BTC-EUR"})

        assert response.status_code >= 400, response.text
        assert response.json()["code"] == "symbol_without_exchange_suffix", (
            "abgelehnt wird die Symbolform, nicht die Gattung"
        )
        assert _stored(repository, "BTC-EUR") == {}, "keine geratene Zeile"
    finally:
        app.dependency_overrides.clear()


# ─── Matrix #7 · die Währung des Paars ────────────────────────────────────────


def test_ein_kurs_in_fremder_waehrung_wird_abgelehnt(tmp_path: Path, monkeypatch) -> None:
    """Für `BTC-EUR` ist ein Kurs in USD ein **Datenfehler**, keine Umrechnung.

    Die Quote-Währung gehört bei einem Paar zur Identität — sie beantwortet
    die Frage, die bei einer Aktie der Handelsplatz beantwortet. Ein Kurs in
    einer anderen Währung gehört damit zu einem anderen Instrument.

    Still umzurechnen wäre die gefährlichere Antwort: Der Wert sähe richtig
    aus und wäre es nicht.

    Geprüft wird die **Kennung**, nicht nur der Status: Vor der Umsetzung
    scheitert dieser Aufruf ohnehin an der Symbolform, und ein Test, der das
    als Erfolg zählt, prüft nichts.
    """
    client, repository = _chain(
        str(tmp_path / "waehrung.db"),
        _TypedQuoteSource("crypto", currency="USD"),
        _real_resolver_chain(monkeypatch, _YahooSearch("CRYPTOCURRENCY")),
    )
    try:
        response = client.get("/quote", params={"symbol": "BTC-EUR"})

        assert response.status_code >= 400, response.text
        assert response.json()["code"] == "quote_currency_mismatch", response.text
        assert _stored(repository, "BTC-EUR") == {}, (
            "ein Kurs in fremder Währung darf keine Zeile hinterlassen"
        )
    finally:
        app.dependency_overrides.clear()


# ─── Matrix #6 · die nicht aufgenommene Gattung ───────────────────────────────


def test_ein_index_wird_mit_eigener_kennung_abgelehnt(
    tmp_path: Path, monkeypatch
) -> None:
    """Indizes bleiben draußen — aber sie werden **ehrlich** abgelehnt.

    Der Unterschied ist der ganze Punkt von Matrix `#6`: Ohne eigene Kennung
    fiele ein Index in den Zufallsbefund der Symbolform („kein Börsensuffix")
    und der Benutzer läse eine Begründung, die nichts mit dem Grund zu tun
    hat. `unsupported_instrument_type` sagt, was wirklich los ist — und sagt
    zugleich, dass eine spätere Entscheidung es ändern kann.
    """
    client, repository = _chain(
        str(tmp_path / "index.db"),
        _TypedQuoteSource("index"),
        # Yahoo kennt `^GDAXI` und meldet `INDEX` — die Gattung steht damit
        # fest, und die App lehnt sie mit **ihrem** Grund ab.
        _real_resolver_chain(monkeypatch, _YahooSearch("INDEX")),
    )
    try:
        response = client.get("/quote", params={"symbol": "^GDAXI"})

        assert response.status_code >= 400, response.text
        assert response.json()["code"] == "unsupported_instrument_type", response.text
        assert _stored(repository, "^GDAXI") == {}
    finally:
        app.dependency_overrides.clear()


# ─── Matrix #9 · die Anleihe ──────────────────────────────────────────────────


def test_eine_anleihe_wird_als_isin_only_aufgenommen(bond_chain) -> None:
    """Erfassen funktioniert sofort — auch ohne Handelsplatz und ohne Kurs.

    Die ISIN **ist** hier die Identität. Das Papier gehört in den Bestand,
    sobald jemand es nennt und eine Quelle es kennt; ein Preis ist eine
    andere Frage und wird darunter geprüft.

    **Der Eintrittspunkt ist korrigiert, die Zusicherung nicht.** Zuerst stand
    hier `GET /quote/{isin}` — das war die falsche Tür für diese Aussage: Die
    Kursroute beschafft einen Preis, und ohne Preis eine Zeile anzulegen wäre
    dort eine Nebenwirkung. „Erfassen" heißt im Ticket der Aufnahmeweg, und
    der ist `POST /instruments/intake`.

    Die Unterscheidung ist wichtig genug für diesen Absatz: Eine **Zusicherung**
    zu ändern, weil sie rot ist, hieße den Test an die Lösung anzupassen. Den
    **Eintrittspunkt** zu korrigieren, weil er die geprüfte Aussage nicht
    trifft, ist das Gegenteil davon — die Aussage bleibt Wort für Wort stehen.
    """
    client, repository = bond_chain

    client.post("/instruments/intake", json={"identifier": _BUND_ISIN})

    assert _stored(repository, _BUND_ISIN) == {
        "kind": "isin_only",
        "ticker": None,
        "mic": None,
        "base": None,
        "quote_currency": None,
        "isin": _BUND_ISIN,
        "type": "bond",
    }


def test_ohne_liefernde_quelle_sagt_die_anleihe_quote_unavailable(bond_chain) -> None:
    """Die wahre Aussage lautet „keine Quelle konnte einen Preis feststellen".

    Nicht „gibt es nicht" und nicht ein Kurs mit Lücke: Ein Preis ist ein
    Messpunkt mit Herkunft, und wo keiner vorliegt, gibt es keinen
    Quote-Datensatz. Die provider-neutralen Fehlertexte aus T-36 tragen genau
    diesen Fall.
    """
    client, _ = bond_chain

    response = client.get(f"/quote/{_BUND_ISIN}")

    assert response.status_code == 502, response.text
    assert response.json()["code"] == "quote_unavailable", response.text
