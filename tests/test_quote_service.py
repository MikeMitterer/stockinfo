"""Tests für die Orchestrierung im QuoteService (Provider gemockt)."""

import pytest
import structlog
from stockinfo_plugin.types import NotFound, NotResponsible, Unavailable

from app.providers.base import EtfDetails, RawQuote, ResolvedInstrument
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
)


class FakeQuoteProvider:
    """Liefert einen vorgegebenen RawQuote (oder None)."""

    def __init__(self, raw: RawQuote | None) -> None:
        self._raw = raw

    def fetch_quote(self, symbol: str) -> RawQuote | None:
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
        self.gesehene_zustaendigkeit: list[tuple] = []

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        self.gesehene_zustaendigkeit.append((isin, exchange, currency))
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
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
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
            ResolvedInstrument(symbol="BRYN.DE", isin="US0846707026", type="stock")
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

    with pytest.raises(QuoteUnavailableError) as fehler:
        service.get_quote_by_isin("IE00B3RBWM25")

    # Der Text landet im Antwortkörper — er muss die Quellen nennen.
    assert "openfigi" in str(fehler.value)
    assert "yahoo" in str(fehler.value)


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
        FakeResolver(ResolvedInstrument(symbol="NOPE.DE")),
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
        FakeResolver(ResolvedInstrument(symbol="EQQQ.L")),
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
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
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
    euro_kurs = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        volume=1000,
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(euro_kurs),
        FakeEtfProvider(EtfDetails(fund_currency="USD", fund_domicile="Ireland")),
        FakeResolver(
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
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
    ohne_waehrung = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency=None,
        volume=1000,
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(ohne_waehrung),
        FakeEtfProvider(None),
        FakeResolver(
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
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


def _lvmh_quote_mit_fremder_isin() -> RawQuote:
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
        FakeQuoteProvider(_lvmh_quote_mit_fremder_isin()),
        FakeEtfProvider(None),
        FakeResolver(ResolvedInstrument(symbol="MC.PA", isin="FR0000121014")),
    )

    result = service.get_quote_by_isin("FR0000121014")

    assert result.isin == "FR0000121014"


def test_abweichende_anbieter_isin_wird_protokolliert() -> None:
    """Still verwerfen wäre so falsch wie still übernehmen.

    Die Abweichung ist ein Befund über die Quelle — sie gehört ins Log, damit
    sie auffällt, statt in der Antwort zu verschwinden.
    """
    service = QuoteService(
        FakeQuoteProvider(_lvmh_quote_mit_fremder_isin()),
        FakeEtfProvider(None),
        FakeResolver(ResolvedInstrument(symbol="MC.PA", isin="FR0000121014")),
    )

    with structlog.testing.capture_logs() as logs:
        service.get_quote_by_isin("FR0000121014")

    mismatches = [e for e in logs if e["event"] == "isin_mismatch"]
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
        FakeResolver(ResolvedInstrument(symbol="MC.PA", isin="FR0000121014")),
    )

    with structlog.testing.capture_logs() as logs:
        service.get_quote_by_isin("FR0000121014")

    assert [e for e in logs if e["event"] == "isin_mismatch"] == []


def test_ohne_aufgeloeste_isin_gilt_weiterhin_die_des_anbieters() -> None:
    """Beim Abruf per Symbol gibt es keine Eingabe, die gewinnen könnte.

    Dort ist die Meldung des Anbieters die einzige Quelle — und bleibt es.
    """
    service = QuoteService(
        FakeQuoteProvider(_lvmh_quote_mit_fremder_isin()),
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
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
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
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    assert service.get_quote_by_isin("IE00B3RBWM25").metadata_complete is True


def test_eine_aktie_gilt_als_vollstaendig() -> None:
    """Bei einer Aktie ist nichts anzureichern — es gibt also nichts zu schützen.

    Bliebe sie auf ``False``, würde das Repository ihre Metadatenfelder nie
    mehr aktualisieren.
    """
    aktie = RawQuote(
        symbol="APC.DE",
        price=262.95,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="stock",
    )
    service = QuoteService(
        FakeQuoteProvider(aktie),
        FakeEtfProvider(None),
        FakeResolver(
            ResolvedInstrument(symbol="APC.DE", isin="US0378331005", type="stock")
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
    ohne_typ = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type=None,
    )
    service = QuoteService(
        FakeQuoteProvider(ohne_typ),
        FakeEtfProvider(EtfDetails(ter=0.19, provider="Vanguard")),
        FakeResolver(ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25")),
    )

    assert service.get_quote_by_isin("IE00B3RBWM25").metadata_complete is False


def test_europaeischer_etf_ohne_isin_bleibt_geschuetzt() -> None:
    """Ein europäisch aussehendes Papier ohne ISIN behält seinen Stand.

    Die Zuständigkeit ist beantwortbar — EUR spricht für justETF —, aber
    justETF arbeitet über die ISIN und kann ohne sie nichts liefern. Die
    Antwort weiß damit nichts über die ETF-Felder und darf den gespeicherten
    Stand nicht ersetzen.
    """
    etf_ohne_isin = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency="EUR",
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(etf_ohne_isin),
        FakeEtfProvider(None, responsible=True),  # zuständig, liefert nichts
        FakeResolver(ResolvedInstrument(symbol="VGWL.DE")),
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
        FakeResolver(ResolvedInstrument(symbol="XIC.TO", exchange="Toronto")),
    )

    service.get_quote_by_symbol("XIC.TO")

    assert enricher.gesehene_zustaendigkeit == [(None, None, "CAD")]


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

    result = service.get_quote_for_known(
        "VTI", isin="US9229087690", instrument_type="etf"
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

    result = service.get_quote_for_known("ARKK", instrument_type="etf")

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
        service.get_quote_for_known("ARKK", instrument_type="etf")


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
