"""Kanonische Identität beim **Anlegen** neuer Papiere (T-21, Teil 2).

Teil 1 hat den Bestand zerlegt. Hier geht es um den umgekehrten Weg: Ein
Papier, das StockInfo zum ersten Mal sieht, muss `ticker` und `mic` schon aus
der Auflösung mitbringen — sonst entstünde bei jedem Neuzugang genau der
offene Fall, den die Migration mühsam meldet.

Die Regel des Tickets, wörtlich: *normalisieren, wenn eindeutig — sonst
ablehnen und sichtbar machen. Niemals raten.*
"""

import pytest
import structlog

from app.exchanges import is_real_mic, split_symbol
from app.resolver import YAHOO_EXCHANGE_MICS, OpenFigiResolver, YFinanceResolver
from stockinfo_plugin.types import Unavailable


class _Search:
    """Ersetzt ``yf.Search`` durch eine feste Trefferliste."""

    hits: list[dict] = []

    def __init__(self, isin: str) -> None:
        self.isin = isin

    @property
    def quotes(self) -> list[dict]:
        return _Search.hits


def _with_hits(monkeypatch: pytest.MonkeyPatch, *hits: dict) -> None:
    """Hängt die Fake-Suche mit den angegebenen Treffern an den Resolver.

    Args:
        monkeypatch: Fixture, über die die Fake-Suche gesetzt wird.
        hits: Yahoo-Treffer in der Reihenfolge, in der die Suche sie liefert.
    """
    from app import resolver as resolver_module

    _Search.hits = list(hits)
    monkeypatch.setattr(resolver_module.yf, "Search", _Search)


class _FigiClient:
    """Liefert einen vorgegebenen Ticker je Börse."""

    def __init__(self, by_exchange: dict[str, str]) -> None:
        self._by_exchange = by_exchange

    def map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None:
        return self._by_exchange.get(id_value)


# --- Yahoo: der Börsencode schließt die Lücke, die das Suffix offen lässt ---


def test_suffixloses_symbol_bekommt_seinen_mic_aus_dem_boersencode(monkeypatch) -> None:
    """Genau die Lücke aus Teil 1 — und der Grund, warum sie dort offen blieb.

    Die Migration kann `AAPL` nicht zuordnen: Die Börsentabelle führt für
    suffixlose Symbole nur den Sammelcode `US`, und ob NYSE oder NASDAQ gilt,
    steht dort nicht. Die **Auflösung** weiß es — Yahoo nennt den Handelsplatz
    im Feld `exchange`.
    """
    _with_hits(monkeypatch, {"symbol": "AAPL", "exchange": "NMS", "quoteType": "EQUITY"})

    resolved = YFinanceResolver(default_exchange="US").resolve_isin("US0378331005")

    assert resolved.ticker == "AAPL"
    assert resolved.mic == "XNAS"


def test_das_suffix_entscheidet_ohne_yahoos_boersencode(monkeypatch) -> None:
    """Wo die eigene Tabelle greift, wird Yahoos Code gar nicht gebraucht.

    `GER` steht bewusst **nicht** in der Yahoo-Tabelle: Für `.DE` kennt
    StockInfo den MIC aus der eigenen Börsentabelle. Die Yahoo-Zuordnung ist
    die Ausnahme für suffixlose Notierungen, nicht der Regelweg.
    """
    _with_hits(monkeypatch, {"symbol": "EUNL.DE", "exchange": "GER", "quoteType": "ETF"})

    resolved = YFinanceResolver(default_exchange="XETR").resolve_isin("IE00B4L5Y983")

    assert (resolved.ticker, resolved.mic) == ("EUNL", "XETR")
    assert "GER" not in YAHOO_EXCHANGE_MICS


def test_das_yahoo_symbol_bleibt_als_alias_erhalten(monkeypatch) -> None:
    """Punkt 3 der Ticket-Regel: Das Anbieter-Symbol geht nicht verloren.

    Es ist weiterhin das, womit yfinance den Kurs holt — und woran die
    Profil-Links im Dashboard hängen.
    """
    _with_hits(monkeypatch, {"symbol": "EUNL.DE", "exchange": "GER", "quoteType": "ETF"})

    resolved = YFinanceResolver(default_exchange="XETR").resolve_isin("IE00B4L5Y983")

    assert resolved.symbol == "EUNL.DE"


def test_fremde_schreibweise_wird_abgelehnt_statt_umgedeutet(monkeypatch) -> None:
    """`BRK-B` ist der Fall, an dem die Regel hängt.

    Der MIC steht fest (`NYQ` → `XNYS`), der Ticker nicht: Yahoos Bindestrich
    ist anbieterspezifisch, und `BRK.B` daraus zu machen wäre geraten — bei
    anderen Tickern bedeutet dieselbe Zeichensetzung etwas anderes. Ein halb
    geratenes Papier anzulegen ist schlechter, als es sichtbar offen zu lassen.
    """
    _with_hits(monkeypatch, {"symbol": "BRK-B", "exchange": "NYQ", "quoteType": "EQUITY"})

    with structlog.testing.capture_logs() as logs:
        result = YFinanceResolver(default_exchange="US").resolve_isin("US0846707026")

    assert isinstance(result, Unavailable)
    assert "BRK-B" in result.error
    records = [entry for entry in logs if entry["event"] == "resolve_isin_ambiguous"]
    assert len(records) == 1
    assert records[0]["symbol"] == "BRK-B"


def test_unbekannter_handelsplatz_wird_gemeldet_statt_geraten(monkeypatch) -> None:
    """Ein Suffix, das die Tabelle nicht kennt, und kein zugeordneter Code.

    Bis T-21 Teil 3 stand hier `GOLD.SG` (Stuttgart) — der Fall aus Mikes
    echtem Bestand. Mit dem Eintrag `XSTU`/`SG` ist Stuttgart **bekannt**, und
    genau deshalb überlebt das Papier die Migration samt seiner 257
    Tageskurse. Die Regel selbst gilt unverändert; sie braucht nur ein Beispiel,
    das die Tabelle wirklich nicht kennt.
    """
    _with_hits(monkeypatch, {"symbol": "ABC.XY", "exchange": "XYZ", "quoteType": "ETF"})

    with structlog.testing.capture_logs() as logs:
        result = YFinanceResolver(default_exchange="XETR").resolve_isin("DE000A0S9GB0")

    assert isinstance(result, Unavailable)
    records = [entry for entry in logs if entry["event"] == "resolve_isin_ambiguous"]
    assert records and records[0]["exchange_code"] == "XYZ"


def test_stuttgart_wird_seit_teil_3_aufgeloest(monkeypatch) -> None:
    """Die Gegenprobe zum Test darüber — und der Grund für die Reihenfolge.

    Diese Übergabe **muss** vor der Migration ausgeliefert werden. Vorher wäre
    `GOLD.SG` nicht auflösbar und würde nach der Migrationsregel aus Runde 16
    abgelehnt statt migriert; im echten Bestand hängen daran 257 Tageskurse.
    """
    _with_hits(monkeypatch, {"symbol": "GOLD.SG", "exchange": "STU", "quoteType": "ETF"})

    result = YFinanceResolver(default_exchange="XETR").resolve_isin("DE000A0S9GB0")

    assert result.ticker == "GOLD"
    assert result.mic == "XSTU"
    assert result.symbol == "GOLD.SG"


@pytest.mark.parametrize("code", sorted(YAHOO_EXCHANGE_MICS))
def test_jede_zuordnung_zeigt_auf_einen_echten_mic(code: str) -> None:
    """Ein Tippfehler in der Tabelle wäre sonst ein falscher MIC in der Datenbank.

    Die Tabelle ist von Hand gepflegt — `XNA` statt `XNAS` fiele ohne diesen
    Test erst auf, wenn ein Anbieter den Wert zurückweist.
    """
    assert is_real_mic(YAHOO_EXCHANGE_MICS[code]) is True


# --- OpenFIGI: der MIC ist schon bekannt, der Ticker muss kanonisch sein ---


def test_openfigi_traegt_die_befragte_boerse_als_mic_ein() -> None:
    """Hier ist der MIC keine Ableitung, sondern die gestellte Frage.

    Der Resolver hat OpenFIGI ausdrücklich nach `XETR` gefragt; die Antwort
    gehört zu genau dieser Börse.
    """
    resolver = OpenFigiResolver(_FigiClient({"XETR": "VGWL"}), default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert (resolved.ticker, resolved.mic) == ("VGWL", "XETR")


def test_der_sammelcode_us_liefert_keine_identitaet() -> None:
    """`US` ist kein MIC — und ein Treffer darauf darf keinen vortäuschen.

    Die Kaskade fällt für US-Papiere auf den Sammelcode zurück. OpenFIGI
    beantwortet die Frage „welcher Ticker", nicht „welche Börse". Der Treffer
    wird deshalb nicht angelegt; auflösen kann ihn der Yahoo-Fallback, der den
    Handelsplatz nennt.
    """
    resolver = OpenFigiResolver(_FigiClient({"US": "AAPL"}), default_exchange="US")

    with structlog.testing.capture_logs() as logs:
        result = resolver.resolve_isin("US0378331005")

    assert getattr(result, "mic", None) is None
    assert [entry for entry in logs if entry["event"] == "resolve_without_identity"]


def test_openfigi_lehnt_eine_fremde_ticker_schreibweise_ab() -> None:
    """OpenFIGI schreibt Anteilsklassen mit Schrägstrich (`BRK/B`).

    Dieselbe Regel wie bei Yahoo: Die Schreibweise ist anbieterspezifisch,
    also wird sie nicht als kanonischer Ticker übernommen.
    """
    resolver = OpenFigiResolver(_FigiClient({"XNYS": "BRK/B"}), default_exchange="XNYS")

    result = resolver.resolve_isin("US0846707026")

    assert getattr(result, "ticker", None) is None


# --- dieselbe Regel gilt rückwärts, in der Zerlegung ---


def test_die_zerlegung_haelt_sich_an_dieselbe_ticker_regel() -> None:
    """Sonst hätte der Bestand eine Schreibweise, die kein Neuzugang bekäme.

    `RDS-A.L` hat ein bekanntes Suffix — die Börse steht also fest. Der Ticker
    trägt aber Yahoos Bindestrich, und genau den weist die Erzeugung zurück.
    Ohne diese Zeile gälte für gewachsene Zeilen eine andere Regel als für
    neue, und `is_canonical_ticker` hätte zwei Wahrheiten.
    """
    assert split_symbol("RDS-A.L") == (None, None)
