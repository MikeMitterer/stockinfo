"""Tests für die ISIN-Auflösung (OpenFIGI-Client gemockt)."""

import pytest
from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable

from app.providers.base import ResolvedInstrument, SourceUnavailableError
from app.providers.openfigi_provider import FigiMatch, OpenFigiClient
from app.resolver import (
    EXCHANGES,
    CompositeResolver,
    OpenFigiResolver,
    YFinanceResolver,
)


class FakeFigiClient:
    """Liefert einen vorgegebenen Ticker und merkt sich den letzten Aufruf."""

    def __init__(self, ticker: str | None) -> None:
        self._ticker = ticker
        self.last_id_value: str | None = None
        self.last_id_type: str | None = None

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        self.last_id_value = id_value
        self.last_id_type = id_type
        return FigiMatch(self._ticker) if self._ticker else None


def test_openfigi_baut_xetra_symbol() -> None:
    client = FakeFigiClient("VGWL")
    resolver = OpenFigiResolver(client, default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert resolved is not None
    assert resolved.symbol == "VGWL.DE"
    assert resolved.isin == "IE00B3RBWM25"
    assert client.last_id_value == "XETR"
    assert client.last_id_type == "micCode"


def test_openfigi_ohne_treffer_meldet_not_found() -> None:
    """Kein Treffer heißt „kenne ich nicht" — nicht „konnte nicht nachsehen"."""
    resolver = OpenFigiResolver(FakeFigiClient(None), default_exchange="XETR")

    assert isinstance(resolver.resolve_isin("DE000A0S9GB0"), NotFound)


def test_openfigi_respektiert_andere_boerse() -> None:
    client = FakeFigiClient("EQQQ")
    resolver = OpenFigiResolver(client, default_exchange="XMIL")

    resolved = resolver.resolve_isin("IE0032077012")

    assert resolved is not None
    assert resolved.symbol == "EQQQ.MI"
    assert client.last_id_value == "XMIL"
    assert client.last_id_type == "micCode"


class _FakeFigi:
    """Zeichnet den letzten map_isin-Aufruf auf und liefert einen festen Ticker."""

    def __init__(self, ticker: str | None) -> None:
        self.ticker = ticker
        self.calls: list[tuple] = []

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        self.calls.append((isin, id_value, id_type))
        return FigiMatch(self.ticker) if self.ticker else None


def test_tsx_bildet_punkt_to_symbol() -> None:
    figi = _FakeFigi("RY")
    resolved = OpenFigiResolver(figi, "XTSE").resolve_isin("CA7800871021")
    assert resolved is not None
    assert resolved.symbol == "RY.TO"
    assert figi.calls == [("CA7800871021", "XTSE", "micCode")]


def test_der_sammelcode_us_wird_gar_nicht_erst_gefragt() -> None:
    """Seit T-21: Ohne echten MIC gibt es keine Identität — und keine Anfrage.

    Früher lieferte dieser Weg `AAPL` ohne Börse. Der Wert taugte für yfinance
    und für sonst nichts: `US` fasst NYSE, NASDAQ, Arca, American und Cboe
    zusammen, und welcher davon gilt, sagt OpenFIGI hier nicht.

    Die Anfrage entfällt deshalb ganz, statt ihr Ergebnis wegzuwerfen — sie
    zählte gegen das Kontingent, ohne je etwas Verwertbares zu liefern. Den
    Fall löst der Yahoo-Fallback, der den Handelsplatz benennt.
    """
    figi = _FakeFigi("AAPL")

    resolved = OpenFigiResolver(figi, "US").resolve_isin("US0378331005")

    assert getattr(resolved, "symbol", None) is None
    assert figi.calls == []


def test_unbekannte_boerse_faellt_auf_xetr_zurueck() -> None:
    figi = _FakeFigi("EUNL")
    resolved = OpenFigiResolver(figi, "NOPE").resolve_isin("IE00B4L5Y983")
    assert resolved is not None
    assert resolved.symbol == "EUNL.DE"
    assert figi.calls == [("IE00B4L5Y983", "XETR", "micCode")]


def test_us_notiert_ohne_suffix() -> None:
    """Was von diesem Test übrig bleibt, nachdem das Anbieterwissen umgezogen ist.

    Der fehlende Alias ist eine Eigenschaft der **Börse**: In den USA ist das
    punktlose Symbol die Notierung. Dass OpenFIGI dort über `exchCode` sucht,
    ist dagegen eine Eigenschaft des Anbieters und steht seit T-21 Teil 2b bei
    ihm — geprüft in `tests/test_openfigi_lookup.py`.

    Seit Teil 3 steht hier ein **echter MIC** statt des Sammelcodes `US`: Die
    Eigenschaft gehört dem Handelsplatz, und `US` ist keiner. Die Abwesenheit
    steht als `None` da, nicht als Leerstring.
    """
    assert EXCHANGES["XNAS"].alias is None


class _FigiFails:
    """Der Dienst ist nicht erreichbar — Netz, Kontingent, Fehlerseite."""

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        raise SourceUnavailableError("openfigi: HTTP 503")


def test_ausfall_ist_nicht_dasselbe_wie_unbekannt() -> None:
    """Der Kern des Tickets: `None` bedeutete drei verschiedene Dinge.

    Ein ausgefallener Dienst und ein unbekanntes Papier kamen beide als
    ``None`` an. Die Kette konnte sie nicht unterscheiden, der Router auch
    nicht — jeder Fehlschlag wurde zu 404, auch wenn niemand nachgesehen hatte.
    """
    failure = OpenFigiResolver(_FigiFails(), "XETR").resolve_isin("IE00B4L5Y983")
    unknown = OpenFigiResolver(_FigiByExchange({}), "XETR").resolve_isin(
        "IE00B4L5Y983"
    )

    assert isinstance(failure, Unavailable)
    assert "openfigi" in failure.error
    assert isinstance(unknown, NotFound)


def test_treffer_bleibt_ein_aufgeloestes_instrument() -> None:
    """Der Erfolgsfall trägt weiterhin das Symbol, das die App braucht."""
    resolved = OpenFigiResolver(_FigiByExchange({"XETR": "EUNL"}), "XETR").resolve_isin(
        "IE00B4L5Y983"
    )

    assert isinstance(resolved, ResolvedInstrument)
    assert resolved.symbol == "EUNL.DE"


class _FigiByExchange:
    """Liefert Ticker je Börse — bildet ab, dass ein Papier nur dort notiert."""

    def __init__(self, hits: dict[str, str]) -> None:
        self._tickers = hits
        self.calls: list[str] = []

    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> FigiMatch | None:
        self.calls.append(id_value)
        treffer = self._tickers.get(id_value)
        return FigiMatch(treffer) if treffer else None


def test_kaskade_weicht_auf_die_heimatboerse_aus() -> None:
    """Der Kanada-Fall, der das Vorhaben ausgelöst hat.

    Gemessen am 2026-08-22: `CA7800871021` (RBC Stammaktie) hat an Xetra kein
    Listing, an Toronto schon. Bisher fiel das Papier durch — die
    Vorgabebörse war die einzige, die gefragt wurde. Das Emissionsland steckt
    im ISIN-Präfix, also muss niemand es konfigurieren.
    """
    figi = _FigiByExchange({"XTSE": "RY"})

    resolved = OpenFigiResolver(figi, "XETR").resolve_isin("CA7800871021")

    assert figi.calls == ["XETR", "XTSE"]  # erst die Vorgabe, dann die Heimat
    assert resolved is not None
    assert resolved.symbol == "RY.TO"
    assert resolved.exchange == "Toronto"


def test_kaskade_meldet_die_abweichung(monkeypatch) -> None:
    """Wer sein Papier plötzlich in CAD sieht, muss den Grund finden können."""
    import structlog

    figi = _FigiByExchange({"XTKS": "7203"})

    with structlog.testing.capture_logs() as logs:
        OpenFigiResolver(figi, "XETR").resolve_isin("JP3633400001")

    fallbacks = [
        entry for entry in logs if entry["event"] == "resolve_home_exchange"
    ]
    assert len(fallbacks) == 1
    assert fallbacks[0]["preferred"] == "XETR"
    assert fallbacks[0]["home"] == "XTKS"


def test_die_bevorzugte_boerse_bleibt_vorrangig() -> None:
    """Ein Papier mit Listing an der Vorgabebörse wandert nicht aus.

    Sonst kippte die Kaskade europäische ETFs auf ihre Heimatbörse — und
    `IE00B4L5Y983` notierte plötzlich in Dublin statt an Xetra.
    """
    figi = _FigiByExchange({"XETR": "EUNL", "XTSE": "IRRELEVANT"})

    resolved = OpenFigiResolver(figi, "XETR").resolve_isin("IE00B4L5Y983")

    assert figi.calls == ["XETR"]  # die Heimat wird gar nicht erst gefragt
    assert resolved is not None
    assert resolved.symbol == "EUNL.DE"


def test_ohne_heimatboerse_bleibt_es_beim_einen_versuch() -> None:
    """Für ein Präfix ohne zugeordnete Börse gibt es nichts auszuweichen.

    Ein irischer Fonds wird europaweit gehandelt; das Präfix nennt die
    ausgebende Stelle, nicht den gewünschten Handelsplatz. Solche Länder
    stehen bewusst nicht in der Tabelle — dort übernimmt der Yahoo-Fallback.
    """
    figi = _FigiByExchange({})

    assert isinstance(OpenFigiResolver(figi, "XETR").resolve_isin("IE00B4L5Y983"), NotFound)
    assert figi.calls == ["XETR"]


def test_strikte_boerse_kennt_keine_kaskade() -> None:
    """`STRICT_EXCHANGE=true` heißt: diese Börse oder gar nicht.

    Wer das einstellt, will keine Überraschung in fremder Währung — die
    Kaskade wäre genau das.
    """
    figi = _FigiByExchange({"XTSE": "RY"})

    resolver = OpenFigiResolver(figi, "XETR", home_fallback=False)

    assert isinstance(resolver.resolve_isin("CA7800871021"), NotFound)
    assert figi.calls == ["XETR"]


class StubResolver:
    """Resolver-Stub für den CompositeResolver-Test.

    `handles` ist getrennt vorgebbar: Eine unzuständige Quelle darf gar nicht
    erst gefragt werden, und genau das prüft einer der Tests.
    """

    def __init__(self, result, handles: bool = True) -> None:
        self._result = result
        self._handles = handles
        self.asked = 0

    def handles(self, isin: str) -> bool:
        return self._handles

    def resolve_isin(self, isin: str):
        self.asked += 1
        return self._result


def test_composite_nimmt_ersten_treffer() -> None:
    primary = StubResolver(NotFound())
    fallback = StubResolver(ResolvedInstrument(symbol="BRK-B", isin="US0846707026"))
    resolver = CompositeResolver(primary, fallback)

    resolved = resolver.resolve_isin("US0846707026")

    assert resolved is not None
    assert resolved.symbol == "BRK-B"


def test_composite_meldet_not_found_wenn_alle_nachgesehen_haben() -> None:
    """Alle haben nachgesehen, keiner kennt es — das rechtfertigt ein 404."""
    resolver = CompositeResolver(StubResolver(NotFound()), StubResolver(NotFound()))

    assert isinstance(resolver.resolve_isin("XX0000000000"), NotFound)


def test_ein_ausfall_schlaegt_ein_kenne_ich_nicht() -> None:
    """Der Kern der Kettenlogik — und der Grund für 502 statt 404.

    Hat eine Quelle gar nicht nachsehen können, ist „gibt es nicht" keine
    belegte Aussage, auch wenn eine andere Quelle das Papier tatsächlich nicht
    kennt. Ein 404 brächte einen Konsumenten dazu, das Papier aufzugeben.
    """
    resolver = CompositeResolver(
        StubResolver(Unavailable(error="openfigi: HTTP 503")),
        StubResolver(NotFound()),
    )

    outcome = resolver.resolve_isin("IE00B4L5Y983")

    assert isinstance(outcome, Unavailable)
    assert "openfigi" in outcome.error


def test_die_kette_nennt_alle_ausgefallenen_quellen() -> None:
    """Der Antwortkörper soll sagen, wer nicht erreichbar war."""
    resolver = CompositeResolver(
        StubResolver(Unavailable(error="openfigi: HTTP 503")),
        StubResolver(Unavailable(error="yahoo: timeout")),
    )

    outcome = resolver.resolve_isin("IE00B4L5Y983")

    assert isinstance(outcome, Unavailable)
    assert "openfigi" in outcome.error
    assert "yahoo" in outcome.error


def test_ein_treffer_schlaegt_einen_vorherigen_ausfall() -> None:
    """Wer liefert, gewinnt — ein Ausfall davor macht das Ergebnis nicht schlechter."""
    resolver = CompositeResolver(
        StubResolver(Unavailable(error="openfigi: HTTP 503")),
        StubResolver(ResolvedInstrument(symbol="EUNL.DE", isin="IE00B4L5Y983")),
    )

    resolved = resolver.resolve_isin("IE00B4L5Y983")

    assert isinstance(resolved, ResolvedInstrument)
    assert resolved.symbol == "EUNL.DE"


def test_unzustaendige_quelle_wird_nicht_gefragt() -> None:
    """Eine Quelle, die nicht zuständig ist, kostet weder Netz noch Kontingent."""
    not_responsible = StubResolver(NotFound(), handles=False)
    responsible = StubResolver(ResolvedInstrument(symbol="EUNL.DE"))
    resolver = CompositeResolver(not_responsible, responsible)

    resolver.resolve_isin("IE00B4L5Y983")

    assert not_responsible.asked == 0
    assert responsible.asked == 1


def test_nur_unzustaendige_quellen_melden_das_auch_so() -> None:
    """Niemand war zuständig — das ist etwas anderes als „nachgesehen und nichts"."""
    resolver = CompositeResolver(
        StubResolver(NotFound(), handles=False),
        StubResolver(NotFound(), handles=False),
    )

    assert isinstance(resolver.resolve_isin("XX0000000000"), NotResponsible)


class _FakeResponse:
    """Antwortobjekt für den gemockten OpenFIGI-Aufruf."""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _RecordingSearch:
    """Ersetzt ``yf.Search`` und merkt sich, wonach gesucht wurde.

    Die Trefferliste ist die **einzige** Stelle, an der hier gemockt wird —
    alles davor und danach ist echter Code. Nur so beantwortet der Test die
    Frage, ob der Yahoo-Resolver wirklich lief, statt sie durch einen Stub zu
    ersetzen, der die Antwort schon kennt.
    """

    hits: list[dict] = []
    queries: list[str] = []

    def __init__(self, isin: str) -> None:
        _RecordingSearch.queries.append(isin)
        self.quotes = list(_RecordingSearch.hits)


def _with_openfigi_response(monkeypatch: pytest.MonkeyPatch, payload: object) -> None:
    """Legt die OpenFIGI-Antwort fest, ohne den Dienst zu fragen."""
    import app.providers.openfigi_provider as openfigi_module

    monkeypatch.setattr(
        openfigi_module.httpx,
        "post",
        lambda *args, **kwargs: _FakeResponse(payload),
    )


def _with_recording_search(
    monkeypatch: pytest.MonkeyPatch, hits: list[dict]
) -> type[_RecordingSearch]:
    """Hängt die aufzeichnende Suche an die Stelle, an der der Resolver sie holt."""
    from app import resolver as resolver_module

    _RecordingSearch.hits = hits
    _RecordingSearch.queries = []
    monkeypatch.setattr(resolver_module.yf, "Search", _RecordingSearch)
    return _RecordingSearch


def _chain_with_real_fallback() -> CompositeResolver:
    """Die echte Kette: OpenFIGI, dann der echte Yahoo-Resolver."""
    return CompositeResolver(
        OpenFigiResolver(OpenFigiClient(), default_exchange="XTSE"),
        YFinanceResolver(default_exchange="XTSE"),
    )


def test_bloomberg_bezeichner_laesst_den_fallback_ans_werk(monkeypatch) -> None:
    """Die ganze Kette, nicht nur der Filter: Läuft der zweite Resolver wirklich?

    Gemessen am 2026-08-21: OpenFIGI liefert zu `CA78012H5675` (Vorzugsaktie
    der Royal Bank) den Bloomberg-Bezeichner `RY V3.65 PERP BB`. Daraus wurde
    das Symbol `RY V3.65 PERP BB.TO`, auf das yfinance mit 404 antwortet — und
    weil der `CompositeResolver` nur auf ``None`` prüft, galt das als Treffer.
    Der Yahoo-Fallback kam nie an die Reihe.

    Echt sind hier beide Resolver samt Antwort-Parser; ersetzt sind allein die
    zwei Außengrenzen — der HTTP-Aufruf zu OpenFIGI und `yf.Search`. Die leere
    Trefferliste bildet die Live-Messung ab: Yahoo kennt diese ISIN ebenfalls
    nicht. Das Papier bleibt also unauflösbar, und genau das prüft der Test —
    die Kette läuft bis zum Ende durch und meldet ``None``, statt bei einem
    Symbol stehenzubleiben, das es nicht gibt.
    """
    _with_openfigi_response(
        monkeypatch,
        [{"data": [{"ticker": "RY V3.65 PERP BB", "exchCode": "TORONTO"}]}],
    )
    search = _with_recording_search(monkeypatch, [])

    resolved = _chain_with_real_fallback().resolve_isin("CA78012H5675")

    assert search.queries == ["CA78012H5675"]  # der Fallback lief wirklich
    assert isinstance(resolved, NotFound)


def test_brauchbarer_ticker_laesst_den_fallback_in_ruhe(monkeypatch) -> None:
    """Die Gegenprobe auf demselben echten Pfad: ein Symbol beendet die Kette."""
    _with_openfigi_response(monkeypatch, [{"data": [{"ticker": "RY"}]}])
    search = _with_recording_search(monkeypatch, [])

    resolved = _chain_with_real_fallback().resolve_isin("CA7800871021")

    assert search.queries == []  # gar nicht erst gefragt
    assert resolved is not None
    assert resolved.symbol == "RY.TO"


def test_der_fallback_darf_nach_einem_unbrauchbaren_ticker_treffen(
    monkeypatch,
) -> None:
    """Und wenn Yahoo das Papier kennt, kommt es auch an.

    Konstruierter Fall, kein Messwert: Für `CA78012H5675` findet Yahoo live
    nichts. Geprüft wird der Mechanismus — ein verworfener OpenFIGI-Treffer
    beendet die Kette nicht, sondern reicht sie weiter, und ein Treffer der
    zweiten Quelle kommt beim Aufrufer an.
    """
    _with_openfigi_response(monkeypatch, [{"data": [{"ticker": "SOME THING BB"}]}])
    search = _with_recording_search(
        monkeypatch,
        [{"symbol": "RY.TO", "exchDisp": "Toronto", "quoteType": "EQUITY"}],
    )

    resolved = _chain_with_real_fallback().resolve_isin("CA7800871021")

    assert search.queries == ["CA7800871021"]
    assert resolved is not None
    assert resolved.symbol == "RY.TO"


class _FakeSearch:
    """Ersetzt ``yf.Search`` — liefert eine je Test gesetzte Trefferliste."""

    hits: list[dict] = []

    def __init__(self, isin: str) -> None:
        self.quotes = list(self.hits)


def _with_search(monkeypatch: pytest.MonkeyPatch, hits: list[dict]) -> None:
    """Hängt die Fake-Suche an die Stelle, an der der Resolver sie holt."""
    from app import resolver as resolver_module

    _FakeSearch.hits = hits
    monkeypatch.setattr(resolver_module.yf, "Search", _FakeSearch)


def _with_foreign_us_listing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lässt Yahoo nur auswärtige Listings ohne Xetra-Alternative finden.

    Die Suche liefert absichtlich mehrere Treffer — NasdaqGS und Mexiko —,
    aber keinen an der bevorzugten Börse. Genau dann muss der Fallback greifen
    und den ersten Treffer nehmen, statt gar nichts zu finden.

    Args:
        monkeypatch: Fixture, über die die Fake-Suche gesetzt wird.
    """
    _with_search(
        monkeypatch,
        [
            {
                "symbol": "AAPL",
                "exchange": "NMS",
                "exchDisp": "NasdaqGS",
                "quoteType": "EQUITY",
            },
            {
                "symbol": "AAPL.MX",
                "exchange": "MEX",
                "exchDisp": "Mexico",
                "quoteType": "EQUITY",
            },
        ],
    )


def test_yahoo_nimmt_das_listing_der_bevorzugten_boerse(monkeypatch) -> None:
    """Nicht der erste Treffer gewinnt, sondern der passende.

    Der Anlass steht in DATA-03: Die Yahoo-Suche liefert für ein iShares-Papier
    zuerst die Londoner Notierung. Wer sie nimmt, bekommt GBP statt EUR — und
    im Depot fällt die Position aus der Währungsrechnung.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"


def test_yahoo_nimmt_den_ersten_treffer_wenn_die_boerse_fehlt(monkeypatch) -> None:
    """Ein US-Papier ohne deutsches Listing muss weiterhin durchgehen.

    Genau dafür gibt es den Fallback — er darf nicht zum Nichts-Finden werden.
    """
    _with_foreign_us_listing(monkeypatch)
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("US0378331005")

    assert resolved is not None
    assert resolved.symbol == "AAPL"


def test_yahoo_protokolliert_das_auswaertige_listing(monkeypatch) -> None:
    """Das strukturierte Event benennt die Abweichung samt Entscheidungsdaten."""
    import structlog

    _with_foreign_us_listing(monkeypatch)
    resolver = YFinanceResolver(default_exchange="XETR")

    with structlog.testing.capture_logs() as logs:
        resolver.resolve_isin("US0378331005")

    records = [
        entry for entry in logs if entry["event"] == "resolve_foreign_exchange"
    ]
    assert records == [
        {
            "event": "resolve_foreign_exchange",
            "isin": "US0378331005",
            "chosen": "AAPL",
            "expected": "XETR",
            "log_level": "info",
        }
    ]


def test_yahoo_folgt_der_konfigurierten_boerse(monkeypatch) -> None:
    _with_search(
        monkeypatch,
        [
            {"symbol": "EQQQ.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
            {"symbol": "EQQQ.MI", "exchDisp": "Milan", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XMIL")

    resolved = resolver.resolve_isin("IE0032077012")

    assert resolved is not None
    assert resolved.symbol == "EQQQ.MI"


def test_yahoo_bevorzugt_bei_boerse_ohne_suffix_das_symbol_ohne_punkt(
    monkeypatch,
) -> None:
    """`US` hat kein Suffix — dort ist das punktlose Symbol die Notierung.

    Erkannt wird es nicht daran, dass der Punkt fehlt, sondern an Yahoos
    Börsencode: `NMS` bildet auf `XNAS` ab, und `XNAS` ist ein Mitglied von
    `US`. Der Xetra-Treffer scheidet über sein Suffix aus.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "AAPL.DE", "exchange": "GER", "exchDisp": "XETRA", "quoteType": "EQUITY"},
            {"symbol": "AAPL", "exchange": "NMS", "exchDisp": "NasdaqGS", "quoteType": "EQUITY"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="US")

    resolved = resolver.resolve_isin("US0378331005")

    assert resolved is not None
    assert resolved.symbol == "AAPL"


def test_yahoo_unterscheidet_eine_us_boerse_vom_sammelcode(monkeypatch) -> None:
    """`DEFAULT_EXCHANGE=XNAS` meint NASDAQ, nicht „irgendwo in den USA".

    Der Befund aus Runde 26: Solange die Auswahl allein am Alias hing, waren
    `XNAS` und der Sammelcode `US` ununterscheidbar — beide führen keinen, und
    die Regel deutete das als „jedes punktlose Symbol gehört dazu". Der
    Arca-Treffer stand vorn und gewann, obwohl der NASDAQ-Treffer zwei Zeilen
    später kam.

    Die Reihenfolge ist deshalb Absicht: Der **falsche** Treffer steht zuerst.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "SPY", "exchange": "PCX", "exchDisp": "NYSEArca", "quoteType": "ETF"},
            {"symbol": "ONEQ", "exchange": "NMS", "exchDisp": "NasdaqGS", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XNAS")

    resolved = resolver.resolve_isin("US0378331005")

    assert isinstance(resolved, ResolvedInstrument)
    assert (resolved.symbol, resolved.mic) == ("ONEQ", "XNAS")


def test_yahoo_laesst_das_suffix_nicht_vom_boersencode_ueberstimmen(
    monkeypatch,
) -> None:
    """Trägt ein Symbol ein bekanntes Suffix, entscheidet **nur** dieses.

    Der Befund aus Runde 27: Auswahl und Identitätsbildung leiteten die Börse
    getrennt ab. Die Auswahl zog Yahoos Code auch bei einem suffigierten
    Symbol heran, und `WRONG.DE` mit dem Code `NMS` galt ihr als
    NASDAQ-Notierung — während `_identity` demselben Treffer gleich darauf
    `XETR` gab. Anzeige, gewählte Präferenz und gespeicherter MIC
    widersprachen einander, und der gültige NASDAQ-Treffer dahinter wurde
    verdrängt.

    Beide Treffer tragen denselben Yahoo-Code; **allein** das Suffix
    unterscheidet sie. Der falsche steht wieder zuerst.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "WRONG.DE", "exchange": "NMS", "exchDisp": "NasdaqGS", "quoteType": "ETF"},
            {"symbol": "RIGHT", "exchange": "NMS", "exchDisp": "NasdaqGS", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XNAS")

    resolved = resolver.resolve_isin("US0378331005")

    assert isinstance(resolved, ResolvedInstrument)
    assert (resolved.symbol, resolved.ticker, resolved.mic) == ("RIGHT", "RIGHT", "XNAS")


def test_yahoo_laesst_einen_unbekannten_punktlosen_treffer_nicht_gewinnen(
    monkeypatch,
) -> None:
    """Ein Treffer, dessen Börse niemand kennt, gehört zu keiner Präferenz.

    Vorher zählte er beim Sammelcode `US` als Treffer der bevorzugten Börse,
    verdrängte das gültige Mitglied dahinter — und die anschließende
    MIC-Abbildung machte daraus `Unavailable`. Der Fehlerfall war damit
    schlimmer als kein Vorzug: Ein auflösbarer Treffer lag vor.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "FUND", "exchange": "ZZZ", "exchDisp": "Nirgendwo", "quoteType": "ETF"},
            {"symbol": "ONEQ", "exchange": "NMS", "exchDisp": "NasdaqGS", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="US")

    resolved = resolver.resolve_isin("US0378331005")

    assert isinstance(resolved, ResolvedInstrument)
    assert (resolved.symbol, resolved.mic) == ("ONEQ", "XNAS")


def test_yahoo_ueberspringt_treffer_ohne_symbol(monkeypatch) -> None:
    _with_search(
        monkeypatch,
        [
            {"exchDisp": "XETRA", "quoteType": "ETF"},
            {"symbol": "VGWL.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00B3RBWM25")

    assert resolved is not None
    assert resolved.symbol == "VGWL.DE"


def test_yahoo_ohne_treffer_meldet_not_found(monkeypatch) -> None:
    """Die Suche war erreichbar und leer — das ist „kenne ich nicht"."""
    _with_search(monkeypatch, [])
    resolver = YFinanceResolver(default_exchange="XETR")

    assert isinstance(resolver.resolve_isin("IE00B3RBWM25"), NotFound)


def test_yahoo_bevorzugt_die_gattung_des_bestplatzierten_treffers(monkeypatch) -> None:
    """Das Börsen-Suffix allein reicht nicht — die Trefferliste mischt Gattungen.

    Yahoos ISIN-Suche ist unscharf: Neben dem gesuchten ETF stehen dort
    Zertifikate, Fonds und Optionsscheine desselben Basiswerts. Wer schlicht
    den ersten Suffix-Treffer nimmt, holt sich einen davon ins Haus, obwohl
    der bestplatzierte Treffer die richtige Gattung nennt.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "XYZ.DE", "exchDisp": "XETRA", "quoteType": "MUTUALFUND"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": "ETF"},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"
    assert resolved.type == "etf"


def test_yahoo_nimmt_die_boerse_auch_bei_abweichender_gattung(monkeypatch) -> None:
    """Die Gattung ist die Feinauswahl, nicht die Bedingung.

    Nennt kein Treffer der bevorzugten Börse dieselbe Gattung wie der
    bestplatzierte, gewinnt weiterhin die Börse — sonst kippte die Regel bei
    jeder unsauberen `quoteType`-Angabe auf die Londoner Notierung zurück.
    """
    _with_search(
        monkeypatch,
        [
            {"symbol": "IS3M.L", "exchDisp": "LSE", "quoteType": "ETF"},
            {"symbol": "IS3M.DE", "exchDisp": "XETRA", "quoteType": ""},
        ],
    )
    resolver = YFinanceResolver(default_exchange="XETR")

    resolved = resolver.resolve_isin("IE00BCRY6557")

    assert resolved is not None
    assert resolved.symbol == "IS3M.DE"


def test_name_und_gattung_ueberleben_die_aufloesung() -> None:
    """**Der Befund aus dem UI-Lauf T-35 — und der teuerste bisher.**

    OpenFIGI schickt Name und Gattung in derselben Antwort wie den Ticker;
    gemessen am 2026-08-28 für `IE00B4L5Y983`:

        {"ticker": "EUNL", "name": "ISHARES CORE MSCI WORLD",
         "securityType": "ETP", "securityType2": "Mutual Fund", …}

    Der Client warf beides weg und lieferte nur den Ticker. Sichtbar wurde das
    an zwei Stellen, und die zweite war die schlimmere:

    1. Die Oberfläche zeigte **keinen Namen** — nur Symbol und ISIN.
    2. Weil `type` leer blieb, hielt das Dashboard jeden ETF für eine Aktie
       (`skipReason === 'notEtf'`) und **fragte justETF gar nicht erst**. TER,
       Anbieter, Domizil, Fondsvolumen und Replikationsart blieben für jedes
       Papier dauerhaft leer — ohne Fehlermeldung, ohne Protokolleintrag.

    Kein Unit-Test hat das gesehen: Jede Schicht war für sich richtig. Erst
    der Weg durch die Oberfläche hat es gezeigt.
    """
    figi = _FakeFigi("EUNL")
    figi.ticker = "EUNL"

    class _WithNameAndType(_FakeFigi):
        def map_isin(self, isin, id_value, id_type="micCode"):
            self.calls.append((isin, id_value, id_type))
            return FigiMatch(
                "EUNL", name="ISHARES CORE MSCI WORLD", instrument_type="etf"
            )

    resolved = OpenFigiResolver(_WithNameAndType("EUNL"), "XETR").resolve_isin(
        "IE00B4L5Y983"
    )

    assert isinstance(resolved, ResolvedInstrument)
    assert resolved.name == "ISHARES CORE MSCI WORLD", "der Name geht verloren"
    assert resolved.type == "etf", (
        "ohne die Gattung wird justETF nie gefragt — die ETF-Kennzahlen "
        "bleiben dann für immer leer"
    )


@pytest.mark.parametrize(
    ("figi_type", "expected"),
    [
        ("ETP", "etf"),
        ("Mutual Fund", "etf"),
        ("Common Stock", "stock"),
        ("Irgendwas Neues", None),
    ],
    ids=["etp", "fonds", "aktie", "unbekannt"],
)
def test_die_gattung_wird_uebersetzt_und_nicht_geraten(
    figi_type: str, expected: str | None
) -> None:
    """Was nicht in der Tabelle steht, bleibt ``None``.

    Ein geratenes ``"stock"`` wäre schlimmer als kein Wert: Es schaltete die
    ETF-Anreicherung stillschweigend ab — genau der Fehler, der diesen Test
    veranlasst hat, nur mit einer falschen Antwort statt gar keiner.
    """
    from app.providers.openfigi_provider import OpenFigiClient

    antwort = [{"data": [{"ticker": "EUNL", "securityType": figi_type}]}]
    match = OpenFigiClient._extract_match(antwort)

    assert match is not None
    assert match.instrument_type == expected
