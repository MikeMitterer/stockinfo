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


class _Suche:
    """Ersetzt ``yf.Search`` durch eine feste Trefferliste."""

    hits: list[dict] = []

    def __init__(self, isin: str) -> None:
        self.isin = isin

    @property
    def quotes(self) -> list[dict]:
        return _Suche.hits


def _mit_treffer(monkeypatch, *treffer: dict) -> None:
    from app import resolver as resolver_module

    _Suche.hits = list(treffer)
    monkeypatch.setattr(resolver_module.yf, "Search", _Suche)


class _FigiClient:
    """Liefert einen vorgegebenen Ticker je Börse."""

    def __init__(self, nach_boerse: dict[str, str]) -> None:
        self._nach_boerse = nach_boerse

    def map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None:
        return self._nach_boerse.get(id_value)


# --- Yahoo: der Börsencode schließt die Lücke, die das Suffix offen lässt ---


def test_suffixloses_symbol_bekommt_seinen_mic_aus_dem_boersencode(monkeypatch) -> None:
    """Genau die Lücke aus Teil 1 — und der Grund, warum sie dort offen blieb.

    Die Migration kann `AAPL` nicht zuordnen: Die Börsentabelle führt für
    suffixlose Symbole nur den Sammelcode `US`, und ob NYSE oder NASDAQ gilt,
    steht dort nicht. Die **Auflösung** weiß es — Yahoo nennt den Handelsplatz
    im Feld `exchange`.
    """
    _mit_treffer(monkeypatch, {"symbol": "AAPL", "exchange": "NMS", "quoteType": "EQUITY"})

    aufgeloest = YFinanceResolver(default_exchange="US").resolve_isin("US0378331005")

    assert aufgeloest.ticker == "AAPL"
    assert aufgeloest.mic == "XNAS"


def test_das_suffix_entscheidet_ohne_yahoos_boersencode(monkeypatch) -> None:
    """Wo die eigene Tabelle greift, wird Yahoos Code gar nicht gebraucht.

    `GER` steht bewusst **nicht** in der Yahoo-Tabelle: Für `.DE` kennt
    StockInfo den MIC aus der eigenen Börsentabelle. Die Yahoo-Zuordnung ist
    die Ausnahme für suffixlose Notierungen, nicht der Regelweg.
    """
    _mit_treffer(monkeypatch, {"symbol": "EUNL.DE", "exchange": "GER", "quoteType": "ETF"})

    aufgeloest = YFinanceResolver(default_exchange="XETR").resolve_isin("IE00B4L5Y983")

    assert (aufgeloest.ticker, aufgeloest.mic) == ("EUNL", "XETR")
    assert "GER" not in YAHOO_EXCHANGE_MICS


def test_das_yahoo_symbol_bleibt_als_alias_erhalten(monkeypatch) -> None:
    """Punkt 3 der Ticket-Regel: Das Anbieter-Symbol geht nicht verloren.

    Es ist weiterhin das, womit yfinance den Kurs holt — und woran die
    Profil-Links im Dashboard hängen.
    """
    _mit_treffer(monkeypatch, {"symbol": "EUNL.DE", "exchange": "GER", "quoteType": "ETF"})

    aufgeloest = YFinanceResolver(default_exchange="XETR").resolve_isin("IE00B4L5Y983")

    assert aufgeloest.symbol == "EUNL.DE"


def test_fremde_schreibweise_wird_abgelehnt_statt_umgedeutet(monkeypatch) -> None:
    """`BRK-B` ist der Fall, an dem die Regel hängt.

    Der MIC steht fest (`NYQ` → `XNYS`), der Ticker nicht: Yahoos Bindestrich
    ist anbieterspezifisch, und `BRK.B` daraus zu machen wäre geraten — bei
    anderen Tickern bedeutet dieselbe Zeichensetzung etwas anderes. Ein halb
    geratenes Papier anzulegen ist schlechter, als es sichtbar offen zu lassen.
    """
    _mit_treffer(monkeypatch, {"symbol": "BRK-B", "exchange": "NYQ", "quoteType": "EQUITY"})

    with structlog.testing.capture_logs() as logs:
        antwort = YFinanceResolver(default_exchange="US").resolve_isin("US0846707026")

    assert isinstance(antwort, Unavailable)
    assert "BRK-B" in antwort.error
    meldungen = [e for e in logs if e["event"] == "resolve_isin_uneindeutig"]
    assert len(meldungen) == 1
    assert meldungen[0]["symbol"] == "BRK-B"


def test_unbekannter_handelsplatz_wird_gemeldet_statt_geraten(monkeypatch) -> None:
    """Ein Suffix, das die Tabelle nicht kennt, und kein zugeordneter Code.

    `GOLD.SG` (Stuttgart) ist genau dieser Fall — er steht so auch in Mikes
    echtem Bestand. Ohne Eintrag in der Börsentabelle gibt es keinen MIC, und
    einen zu erfinden hieße, ein falsches Listing festzuschreiben.
    """
    _mit_treffer(monkeypatch, {"symbol": "GOLD.SG", "exchange": "STU", "quoteType": "ETF"})

    with structlog.testing.capture_logs() as logs:
        antwort = YFinanceResolver(default_exchange="XETR").resolve_isin("DE000A0S9GB0")

    assert isinstance(antwort, Unavailable)
    meldungen = [e for e in logs if e["event"] == "resolve_isin_uneindeutig"]
    assert meldungen and meldungen[0]["boersencode"] == "STU"


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

    aufgeloest = resolver.resolve_isin("IE00B3RBWM25")

    assert (aufgeloest.ticker, aufgeloest.mic) == ("VGWL", "XETR")


def test_der_sammelcode_us_liefert_keine_identitaet() -> None:
    """`US` ist kein MIC — und ein Treffer darauf darf keinen vortäuschen.

    Die Kaskade fällt für US-Papiere auf den Sammelcode zurück. OpenFIGI
    beantwortet die Frage „welcher Ticker", nicht „welche Börse". Der Treffer
    wird deshalb nicht angelegt; auflösen kann ihn der Yahoo-Fallback, der den
    Handelsplatz nennt.
    """
    resolver = OpenFigiResolver(_FigiClient({"US": "AAPL"}), default_exchange="US")

    with structlog.testing.capture_logs() as logs:
        antwort = resolver.resolve_isin("US0378331005")

    assert getattr(antwort, "mic", None) is None
    assert [e for e in logs if e["event"] == "resolve_ohne_identitaet"]


def test_openfigi_lehnt_eine_fremde_ticker_schreibweise_ab() -> None:
    """OpenFIGI schreibt Anteilsklassen mit Schrägstrich (`BRK/B`).

    Dieselbe Regel wie bei Yahoo: Die Schreibweise ist anbieterspezifisch,
    also wird sie nicht als kanonischer Ticker übernommen.
    """
    resolver = OpenFigiResolver(_FigiClient({"XNYS": "BRK/B"}), default_exchange="XNYS")

    antwort = resolver.resolve_isin("US0846707026")

    assert getattr(antwort, "ticker", None) is None


# --- dieselbe Regel gilt rückwärts, in der Zerlegung ---


def test_die_zerlegung_haelt_sich_an_dieselbe_ticker_regel() -> None:
    """Sonst hätte der Bestand eine Schreibweise, die kein Neuzugang bekäme.

    `RDS-A.L` hat ein bekanntes Suffix — die Börse steht also fest. Der Ticker
    trägt aber Yahoos Bindestrich, und genau den weist die Erzeugung zurück.
    Ohne diese Zeile gälte für gewachsene Zeilen eine andere Regel als für
    neue, und `is_canonical_ticker` hätte zwei Wahrheiten.
    """
    assert split_symbol("RDS-A.L") == (None, None)
