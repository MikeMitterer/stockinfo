"""Tests für die Orchestrierung im QuoteService (Provider gemockt)."""

import pytest
import structlog
from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable

from app.exchanges import split_symbol
from app.providers.base import EtfDetails, RawQuote, ResolvedInstrument
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
)


class FakeQuoteProvider:
    """Liefert einen vorgegebenen RawQuote (oder None)."""

    #: **Wie jede echte Kettenquelle nennt auch das Double seinen Namen.**
    #:
    #: Seit T-37 stempelt `QuoteService` die Herkunft nicht mehr als Konstante
    #: `"yfinance"`, sondern fragt die Quelle. Ein Double ohne Namen hätte
    #: danach `"unbekannt"` geliefert — und drei Tests, die vorher die
    #: Konstante festschrieben, hätten das als Fehler gemeldet, obwohl der
    #: Dienst richtig gearbeitet hat. In der Kette trägt jede Quelle einen
    #: Namen (`app.plugin_adapters` reicht ihn durch); das Double bildet das
    #: nach, statt die Prüfung zu lockern.
    name = "yfinance"

    def __init__(self, raw: RawQuote | None) -> None:
        self._raw = raw

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        # Seit T-23 die aufgelöste Identität statt des Symbols — siehe
        # `app.plugin_adapters.QuoteAdapter`.
        return self._raw


class FakeEtfProvider:
    """Liefert vorgegebene ETF-Details (oder None).

    ``responsible`` bildet den zweiten, unabhängigen Zustand ab: Ob die Quelle
    für dieses Papier überhaupt zuständig ist, ist eine andere Frage als ob sie
    geantwortet hat.
    """

    def __init__(self, details: EtfDetails | None, responsible: bool = True) -> None:
        self._details = details
        self._responsible = responsible
        self.seen_responsibility: list[tuple] = []

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        self.seen_responsibility.append((isin, exchange, currency))
        return self._responsible

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None:
        return self._details


def _resolved(symbol: str, **fields) -> ResolvedInstrument:
    """Eine Auflösung, wie der echte Resolver sie liefert — **mit** Identität.

    Bis T-21 Übergabe 3 bauten die Vorrichtungen hier `ResolvedInstrument`
    ohne `ticker` und `mic`. Das war eine Auflösung, die es nicht gibt: Der
    Resolver setzt beide seit Teil 1 über `_identity`, und seit `ticker`/`mic`
    zugesagte Pflichtfelder sind, antwortet der Core auf eine Auflösung ohne
    Identität mit `502` statt eine halbe Identität zu speichern.

    Die Identität wird deshalb **aus dem Symbol abgeleitet** statt an 16
    Stellen von Hand eingetragen — dieselbe Rechnung, die der Resolver
    anstellt. Eine Vorrichtung, die weniger weiß als die Wirklichkeit, prüft
    einen Fall, den es nicht gibt; genau daran ist in Übergabe 2B die
    `quotes`-Tabelle ohne `currency` gescheitert.

    Wo die Identität selbst der Prüfgegenstand ist, steht sie weiterhin
    ausdrücklich im Test — abgeleitet wäre sie dort ein Orakel, das sich selbst
    bestätigt. Ebenso bei **suffixlosen** Symbolen (`ARKK`): Aus ihnen lässt
    sich keine Börse rechnen, die Auflösung nimmt sie dort vom Börsencode des
    Anbieters. Ein ausdrücklich übergebenes `ticker`/`mic` gewinnt deshalb.
    """
    ticker, mic = split_symbol(symbol)
    return ResolvedInstrument(
        symbol=symbol,
        ticker=fields.pop("ticker", ticker),
        mic=fields.pop("mic", mic),
        **fields,
    )


class FakeResolver:
    """Liefert eine vorgegebene Resolution.

    ``None`` steht weiterhin für „kenne ich nicht" — die bestehenden Tests
    schreiben es so, und der Service muss beide Schreibweisen vertragen, weil
    `NotFound` genau dasselbe bedeutet.
    """

    def __init__(self, resolved) -> None:
        self._resolved = NotFound() if resolved is None else resolved

    def handles(self, isin: str) -> bool:
        return True

    def resolve_isin(self, isin: str):
        return self._resolved


def _etf_quote() -> RawQuote:
    return RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        volume=1000,
        type="etf",
    )


def test_etf_wird_mit_justetf_angereichert() -> None:
    # `source` kommt aus der Quelle, nicht aus dem Service — ein Fake, der
    # justETF nachbildet, muss sich deshalb auch so beschriften.
    details = EtfDetails(
        ter=0.19, provider="Vanguard", replication="Physical",
        source="yfinance+justetf",
    )
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(details),
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.type == "etf"
    assert result.ter == 0.19
    assert result.provider == "Vanguard"
    assert result.currency == "EUR"
    assert result.source == "yfinance+justetf"


def test_aktie_wird_nicht_angereichert() -> None:
    stock = RawQuote(
        symbol="BRYN.DE",
        price=430.05,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="stock",
    )
    service = QuoteService(
        FakeQuoteProvider(stock),
        FakeEtfProvider(EtfDetails(ter=0.99)),  # würde ignoriert
        FakeResolver(
            _resolved("BRYN.DE", isin="US0846707026", type="stock")
        ),
    )

    result = service.get_quote_by_isin("US0846707026")

    assert result.type == "stock"
    assert result.ter is None
    assert result.source == "yfinance"


def test_ausgefallene_quellen_werfen_unavailable_statt_not_found() -> None:
    """„Konnte nicht nachsehen" ist kein „gibt es nicht".

    Vorher lief beides über dasselbe ``None`` und wurde zu 404. Ein Konsument
    gab das Papier daraufhin auf, obwohl nur das Netz weg war.
    """
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(Unavailable(error="openfigi: HTTP 503; yahoo: timeout")),
    )

    with pytest.raises(QuoteUnavailableError) as unavailable:
        service.get_quote_by_isin("IE00B3RBWM25")

    # Der Text landet im Antwortkörper — er muss die Quellen nennen.
    assert "openfigi" in str(unavailable.value)
    assert "yahoo" in str(unavailable.value)


def test_keine_zustaendige_quelle_ist_ein_not_found() -> None:
    """Niemand war zuständig — dann gibt es das Papier hier nicht."""
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(NotResponsible(reason="keine zuständige Quelle")),
    )

    with pytest.raises(InstrumentNotFoundError):
        service.get_quote_by_isin("XX0000000000")


def test_unbekannte_isin_wirft_not_found() -> None:
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(None),
    )

    with pytest.raises(InstrumentNotFoundError):
        service.get_quote_by_isin("XX0000000000")


def test_kein_kurs_wirft_unavailable() -> None:
    service = QuoteService(
        FakeQuoteProvider(None),
        FakeEtfProvider(None),
        FakeResolver(_resolved("NOPE.DE")),
    )

    with pytest.raises(QuoteUnavailableError):
        service.get_quote_by_symbol("NOPE.DE")


def test_gbp_pence_wird_originalgetreu_uebernommen() -> None:
    pence = RawQuote(
        symbol="EQQQ.L",
        price=54211.0,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="GBp",
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(pence),
        FakeEtfProvider(None),
        FakeResolver(_resolved("EQQQ.L")),
    )

    result = service.get_quote_by_symbol("EQQQ.L")

    assert result.currency == "GBp"
    assert result.price == 54211.0


def test_etf_uebernimmt_volatilitaet_und_thesaurierend_von_justetf() -> None:
    details = EtfDetails(ter=0.19, volatility=9.95, accumulating=True)
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(details),
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.volatility == 9.95
    assert result.accumulating is True


def test_die_fondswaehrung_blutet_nicht_in_die_handelswaehrung() -> None:
    """Zwei Begriffe, zwei Felder.

    Die Fondswährung darf nicht in `currency` rutschen — bei einem Euro-Kurs
    stünde sonst USD daneben.
    """
    euro_quote = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        volume=1000,
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(euro_quote),
        FakeEtfProvider(EtfDetails(fund_currency="USD", fund_domicile="Ireland")),
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.currency == "EUR"
    assert result.fund_currency == "USD"
    assert result.fund_domicile == "Ireland"


def test_preis_ohne_waehrung_ist_kein_verwertbarer_kurs() -> None:
    """Der Vertrag verlangt die Währung — geraten wird nicht.

    „Wird schon Euro sein" ist bei einem Londoner Listing in Pence falsch, und
    eine Depotposition mit unbekannter Währung fällt aus jeder Rechnung. Statt
    einen Preis ohne Währung auszuliefern, meldet die Beschaffung einen
    Fehler; der Router bildet ihn auf 502 ab (`errors.incomplete_core` im
    Vertragsartefakt).
    """
    without_currency = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency=None,
        volume=1000,
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(without_currency),
        FakeEtfProvider(None),
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    with pytest.raises(QuoteUnavailableError):
        service.get_quote_by_isin("IE00B3RBWM25")


def test_die_pflichtfelder_kommen_aus_dem_vertragsartefakt() -> None:
    """Die Prüfung liest, was der Vertrag zusagt — sie hält keine eigene Liste.

    Zwei Listen liefen auseinander, und dann verspräche `GET /fields` etwas
    anderes, als der Code durchlässt.
    """
    from app.contract import required_fields

    assert "currency" in required_fields("quote")
    assert "price" in required_fields("quote")


def _lvmh_quote_with_foreign_isin() -> RawQuote:
    """Der Pariser Kurs, den yfinance mit der kanadischen Zweitnotierung meldet.

    Gemessen am 2026-08-19: `MC.PA` trägt bei yfinance `CA50244Q1037` — ein
    kanadisches Hinterlegungspapier. Der Name stimmt, die Gattung nicht.
    """
    return RawQuote(
        symbol="MC.PA",
        price=487.5,
        quote_time="2026-08-19T17:35:00+00:00",
        currency="EUR",
        type="stock",
        isin="CA50244Q1037",
    )


def test_die_aufgeloeste_isin_gewinnt_gegen_die_des_anbieters() -> None:
    """Wer eine ISIN eingibt, bekommt sie zurück — nicht die des Anbieters.

    Bisher galt `raw.isin or resolved.isin`: Die Meldung von yfinance schlug die
    Eingabe. Gespeichert wurde damit ein anderes Wertpapier als das gesuchte.
    """
    service = QuoteService(
        FakeQuoteProvider(_lvmh_quote_with_foreign_isin()),
        FakeEtfProvider(None),
        FakeResolver(_resolved("MC.PA", isin="FR0000121014")),
    )

    result = service.get_quote_by_isin("FR0000121014")

    assert result.isin == "FR0000121014"


def test_abweichende_anbieter_isin_wird_protokolliert() -> None:
    """Still verwerfen wäre so falsch wie still übernehmen.

    Die Abweichung ist ein Befund über die Quelle — sie gehört ins Log, damit
    sie auffällt, statt in der Antwort zu verschwinden.
    """
    service = QuoteService(
        FakeQuoteProvider(_lvmh_quote_with_foreign_isin()),
        FakeEtfProvider(None),
        FakeResolver(_resolved("MC.PA", isin="FR0000121014")),
    )

    with structlog.testing.capture_logs() as logs:
        service.get_quote_by_isin("FR0000121014")

    mismatches = [entry for entry in logs if entry["event"] == "isin_mismatch"]
    assert len(mismatches) == 1
    assert mismatches[0]["log_level"] == "warning"
    assert mismatches[0]["requested"] == "FR0000121014"
    assert mismatches[0]["reported"] == "CA50244Q1037"
    assert mismatches[0]["symbol"] == "MC.PA"


def test_uebereinstimmende_isin_wird_nicht_protokolliert() -> None:
    """Der Normalfall bleibt still — sonst warnt das Log bei jedem Abruf."""
    matching = RawQuote(
        symbol="MC.PA",
        price=487.5,
        quote_time="2026-08-19T17:35:00+00:00",
        currency="EUR",
        type="stock",
        isin="FR0000121014",
    )
    service = QuoteService(
        FakeQuoteProvider(matching),
        FakeEtfProvider(None),
        FakeResolver(_resolved("MC.PA", isin="FR0000121014")),
    )

    with structlog.testing.capture_logs() as logs:
        service.get_quote_by_isin("FR0000121014")

    assert [entry for entry in logs if entry["event"] == "isin_mismatch"] == []


def test_ohne_aufgeloeste_isin_gilt_weiterhin_die_des_anbieters() -> None:
    """Beim Abruf per Symbol gibt es keine Eingabe, die gewinnen könnte.

    Dort ist die Meldung des Anbieters die einzige Quelle — und bleibt es.
    """
    service = QuoteService(
        FakeQuoteProvider(_lvmh_quote_with_foreign_isin()),
        FakeEtfProvider(None),
        FakeResolver(None),
    )

    result = service.get_quote_by_symbol("MC.PA")

    assert result.isin == "CA50244Q1037"


def test_annualized_volatility_zu_wenig_daten_ist_none() -> None:
    assert annualized_volatility([100.0, 101.0]) is None
    assert annualized_volatility([]) is None


def test_gescheiterte_anreicherung_markiert_die_antwort_als_unvollstaendig() -> None:
    """Ein Ausfall bei justETF muss sich in der Antwort niederschlagen.

    Sonst sieht sie aus wie eine erfolgreiche Abfrage ohne ETF-Extras — und das
    Repository schreibt den gespeicherten Stand mit lauter ``NULL`` zu.
    """
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None),  # justETF nicht erreichbar
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.metadata_complete is False
    assert result.ter is None
    assert result.source == "yfinance"


def test_erfolgreiche_anreicherung_gilt_als_vollstaendig() -> None:
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(EtfDetails(ter=0.19, provider="Vanguard")),
        FakeResolver(
            _resolved("VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    assert service.get_quote_by_isin("IE00B3RBWM25").metadata_complete is True


def test_eine_aktie_gilt_als_vollstaendig() -> None:
    """Bei einer Aktie ist nichts anzureichern — es gibt also nichts zu schützen.

    Bliebe sie auf ``False``, würde das Repository ihre Metadatenfelder nie
    mehr aktualisieren.
    """
    stock_quote = RawQuote(
        symbol="APC.DE",
        price=262.95,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="stock",
    )
    service = QuoteService(
        FakeQuoteProvider(stock_quote),
        FakeEtfProvider(None),
        FakeResolver(
            _resolved("APC.DE", isin="US0378331005", type="stock")
        ),
    )

    assert service.get_quote_by_isin("US0378331005").metadata_complete is True


def test_unbekannte_gattung_gilt_nicht_als_vollstaendig() -> None:
    """Ohne Gattung weiß die Antwort nichts über die ETF-Felder — und sagt das.

    Der ETF-Zweig entscheidet über `metadata_complete`; wird er übersprungen,
    blieb das Feld auf seiner Vorgabe ``True``, und das Repository durfte den
    gepflegten justETF-Stand mit nichts überschreiben. Yahoo liefert nicht
    immer einen ``quote_type``, und der Resolver ist nicht auf jedem Weg dabei
    — dann steht hier ``None``, und „vollständig" wäre eine Behauptung.
    """
    without_type = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type=None,
    )
    service = QuoteService(
        FakeQuoteProvider(without_type),
        FakeEtfProvider(EtfDetails(ter=0.19, provider="Vanguard")),
        FakeResolver(_resolved("VGWL.DE", isin="IE00B3RBWM25")),
    )

    assert service.get_quote_by_isin("IE00B3RBWM25").metadata_complete is False


def test_europaeischer_etf_ohne_isin_bleibt_geschuetzt() -> None:
    """Ein europäisch aussehendes Papier ohne ISIN behält seinen Stand.

    Die Zuständigkeit ist beantwortbar — EUR spricht für justETF —, aber
    justETF arbeitet über die ISIN und kann ohne sie nichts liefern. Die
    Antwort weiß damit nichts über die ETF-Felder und darf den gespeicherten
    Stand nicht ersetzen.
    """
    etf_without_isin = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(etf_without_isin),
        FakeEtfProvider(None, responsible=True),  # zuständig, liefert nichts
        FakeResolver(_resolved("VGWL.DE")),
    )

    assert service.get_quote_by_symbol("VGWL.DE").metadata_complete is False


def test_die_zustaendigkeit_bekommt_boerse_und_waehrung_mit() -> None:
    """Ohne die beiden Angaben kann die Quelle ohne ISIN nichts entscheiden."""
    etf = RawQuote(
        symbol="XIC.TO",
        price=41.2,
        quote_time="2026-08-21T20:00:00+00:00",
        currency="CAD",
        type="etf",
    )
    enricher = FakeEtfProvider(EtfDetails(provider="BlackRock"), responsible=True)
    service = QuoteService(
        FakeQuoteProvider(etf),
        enricher,
        FakeResolver(_resolved("XIC.TO", exchange="Toronto")),
    )

    service.get_quote_by_symbol("XIC.TO")

    assert enricher.seen_responsibility == [(None, None, "CAD")]


def _us_etf_quote() -> RawQuote:
    return RawQuote(
        symbol="VTI",
        price=291.4,
        quote_time="2026-08-19T20:00:00+00:00",
        currency="USD",
        type="etf",
        isin="US9229087690",
    )


def test_nicht_zustaendige_quelle_liefert_vollstaendige_metadaten() -> None:
    """Ein US-ETF ist vollständig — es gibt für ihn nichts anzureichern.

    justETF führt nur europäische Papiere. Für einen Nutzer aus den USA oder
    Kanada galt bisher jeder ETF als unvollständig, weil „nicht zuständig" und
    „ausgefallen" beide als ``fetch_etf() is None`` ankamen. Folge: `source`
    steht in `_ETF_META_FIELDS` und wurde deshalb nie geschrieben — die Spalte
    „Quelle" blieb in der Oberfläche dauerhaft leer.
    """
    service = QuoteService(
        FakeQuoteProvider(_us_etf_quote()),
        FakeEtfProvider(None, responsible=False),
        FakeResolver(None),
    )

    # `VTI` liegt an der Arca und trägt kein Suffix — die Identität kommt hier
    # aus der gespeicherten Zeile, wie im Betrieb auch.
    result = service.get_quote_for_known(
        "VTI", isin="US9229087690", instrument_type="etf", ticker="VTI", mic="ARCX"
    )

    assert result.metadata_complete is True
    assert result.source == "yfinance"


def test_zustaendige_quelle_ohne_antwort_bleibt_unvollstaendig() -> None:
    """Der Schutz für europäische Papiere bleibt unangetastet.

    Dieselbe leere Antwort, aber diesmal von einer zuständigen Quelle: Das
    heißt „gerade nicht erreichbar" und darf den gepflegten Stand nicht
    ersetzen.
    """
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None, responsible=True),
        FakeResolver(None),
    )

    result = service.get_quote_for_known(
        "VGWL.DE", isin="IE00B3RBWM25", instrument_type="etf"
    )

    assert result.metadata_complete is False


def test_etf_ohne_isin_aber_mit_waehrung_ist_beantwortbar() -> None:
    """Die Währung beantwortet die Zuständigkeit, wenn die ISIN fehlt.

    Vorher galt: ohne ISIN keine Aussage, also konservativ unvollständig. Das
    traf einen US- oder kanadischen ETF dauerhaft — sein `source` blieb leer,
    weil das Feld geschützt und nie geschrieben wurde. USD sagt aber deutlich,
    dass justETF hier nichts führt: nichts zu holen, nichts zu schützen.
    """
    service = QuoteService(
        FakeQuoteProvider(
            RawQuote(
                symbol="ARKK", price=61.2, quote_time="2026-08-19T20:00:00+00:00",
                currency="USD", type="etf",
            )
        ),
        FakeEtfProvider(None, responsible=False),
        FakeResolver(None),
    )

    # Identität ausgeschrieben, wie sie im Betrieb aus der gespeicherten Zeile
    # kommt: `ARKK` trägt kein Suffix, also lässt sich aus dem Symbol allein
    # kein Handelsplatz rechnen — bei US-Papieren nie.
    result = service.get_quote_for_known(
        "ARKK", instrument_type="etf", ticker="ARKK", mic="ARCX"
    )

    assert result.metadata_complete is True


def test_ohne_waehrung_kommt_die_zustaendigkeitsfrage_gar_nicht_auf() -> None:
    """Der Fall „niemand weiß etwas" ist im Service unerreichbar.

    Ohne Währung greift schon die Core-Prüfung aus T-24 — die Antwort kommt
    nie bis zum ETF-Zweig. Deshalb steht dort kein konservativer Sonderfall
    mehr; die Quellen behandeln ihn trotzdem so, weil sie auch von anderswo
    aufgerufen werden (siehe `test_zustaendigkeit_ohne_jeden_hinweis_bleibt_konservativ`).
    """
    service = QuoteService(
        FakeQuoteProvider(
            RawQuote(
                symbol="ARKK", price=61.2, quote_time="2026-08-19T20:00:00+00:00",
                currency=None, type="etf",
            )
        ),
        FakeEtfProvider(None, responsible=False),
        FakeResolver(None),
    )

    # Ohne Währung greift schon die Core-Prüfung — der Vertrag verlangt sie.
    with pytest.raises(QuoteUnavailableError):
        service.get_quote_for_known(
            "ARKK", instrument_type="etf", ticker="ARKK", mic="ARCX"
        )


def test_die_identitaet_der_aufloesung_reist_bis_zur_speicherung_mit() -> None:
    """T-21, Teil 2: `ticker` und `mic` dürfen unterwegs nicht verlorengehen.

    Der Resolver ermittelt sie, das Repository schreibt sie — dazwischen liegt
    die Antwort des Service. Ohne diese Zeile fiele die Identität genau hier
    heraus, und beide Enden sähen trotzdem richtig aus.

    Am REST-Rand erscheinen die Felder noch nicht (`exclude=True`); das ist
    Teil 3 samt Vertragsversion.
    """
    service = QuoteService(
        FakeQuoteProvider(_etf_quote()),
        FakeEtfProvider(None, responsible=False),
        FakeResolver(
            ResolvedInstrument(
                symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf",
                ticker="VGWL", mic="XETR",
            )
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert (result.ticker, result.mic) == ("VGWL", "XETR")


def test_die_herkunft_nennt_die_quelle_die_geantwortet_hat() -> None:
    """**Der Befund aus dem CSV-Lauf T-37.**

    `source` stand als Konstante ``"yfinance"`` im Code. Im Online-Profil fiel
    das nie auf — dort *ist* yfinance die Kursquelle. Im CSV-Profil trug eine
    Zeile, deren Kurs aus einer Datei kam, trotzdem `source: yfinance`.

    Das ist keine Kosmetik: `source` ist das Feld, an dem ein Benutzer abliest,
    woher ein Wert stammt — die Oberfläche zeigt es im Aufklappbereich als
    „Quelle". Derselbe Fehlertyp wie die Fehlermeldungen, die bis T-36
    OpenFIGI und Yahoo namentlich nannten, obwohl das Profil andere Quellen
    führte.

    Geprüft wird mit einem **anderen** Namen als dem eingebauten; sonst
    bestünde der Test auch dann, wenn die Konstante zurückkäme.
    """

    class AusEinerDatei(FakeQuoteProvider):
        name = "prices-file-quote"

    service = QuoteService(
        AusEinerDatei(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(_resolved("VGWL.DE", isin="IE00B3RBWM25", type="stock")),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.source == "prices-file-quote"


def test_eine_namenlose_quelle_heisst_unbekannt_und_nicht_yfinance() -> None:
    """Der Rückfall ist bewusst **kein** Anbietername.

    Eine Quelle, die ihren Namen nicht nennt, ist unbekannt — und genau das
    soll dastehen. Auf einen eingebauten Namen zurückzufallen wäre dieselbe
    Behauptung wie vorher, nur seltener.
    """

    class OhneNamen(FakeQuoteProvider):
        name = ""

    service = QuoteService(
        OhneNamen(_etf_quote()),
        FakeEtfProvider(None),
        FakeResolver(_resolved("VGWL.DE", isin="IE00B3RBWM25", type="stock")),
    )

    assert service.get_quote_by_isin("IE00B3RBWM25").source == "unbekannt"
