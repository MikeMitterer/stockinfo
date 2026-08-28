"""Tests für die Cache-/TTL-Logik (echte temp-DB, gemockter QuoteService)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.quote_cache import CachedQuoteService, RefreshInProgressError
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteUnavailableError,
    annualized_volatility,
)
from tests.boundaries import empty_daily_sync


class FakeQuoteService:
    """Zählt Aufrufe und liefert eine vorgegebene Antwort (oder wirft)."""

    def __init__(
        self,
        response: QuoteResponse | None,
        raises: bool = False,
        exception: type[Exception] = QuoteUnavailableError,
    ) -> None:
        self._response = response
        self._raises = raises
        self._exception = exception
        self.calls = 0

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        self.calls += 1
        if self._raises:
            raise self._exception(isin)
        return self._response

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        return self.get_quote_by_isin(symbol)

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        return self.get_quote_by_isin(isin or symbol)


def _response(fetched_at: str, price: float = 160.98) -> QuoteResponse:
    # `ticker` und `mic` stehen seit T-21 Teil 3 ausgeschrieben da: Sie sind
    # Pflicht, und sie hier aus dem Symbol zu rechnen hieße, die
    # Zerlegungsregel im Testaufbau ein zweites Mal zu führen.
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        ticker="VGWL",
        mic="XETR",
        currency="EUR",
        price=price,
        quote_time=fetched_at,
        fetched_at=fetched_at,
        type="etf",
    )


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "cache.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hours_ago(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_cache_miss_beschafft_und_speichert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is not None


def test_frischer_cache_vermeidet_zweiten_fetch(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.get_by_isin("IE00B3RBWM25")  # füllt Cache
    result = service.get_by_isin("IE00B3RBWM25")  # Cache-Hit

    assert fake.calls == 1  # kein zweiter Live-Fetch
    assert result.cached is True
    assert result.stale is False


def test_abgelaufener_cache_beschafft_neu(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10)))  # alter Kurs
    fake = FakeQuoteService(_response(_now(), price=200.0))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.cached is False
    assert result.price == 200.0


def test_stale_bei_fehler_und_vorhandenem_cache(repo: QuoteRepository) -> None:
    repo.save_quote(_response(_hours_ago(10), price=155.0))  # alter Kurs
    fake = FakeQuoteService(None, raises=True)  # Live-Beschaffung schlägt fehl
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.stale is True
    assert result.cached is True
    assert result.price == 155.0


def test_fehler_ohne_cache_propagiert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(None, raises=True)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    with pytest.raises(QuoteUnavailableError):
        service.get_by_isin("IE00B3RBWM25")


def test_stale_auch_bei_resolver_ausfall(repo: QuoteRepository) -> None:
    """Resolver-Ausfall (InstrumentNotFoundError) → stale Cache statt 404."""
    repo.save_quote(_response(_hours_ago(10), price=155.0))  # alter Kurs
    fake = FakeQuoteService(None, raises=True, exception=InstrumentNotFoundError)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.stale is True
    assert result.price == 155.0


def test_resolver_ausfall_ohne_cache_propagiert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService(None, raises=True, exception=InstrumentNotFoundError)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    with pytest.raises(InstrumentNotFoundError):
        service.get_by_isin("IE00B3RBWM25")


def test_refresh_all_verweigert_parallellauf(repo: QuoteRepository) -> None:
    """Läuft bereits ein Refresh, wird ein zweiter Aufruf abgewiesen."""
    service = CachedQuoteService(
        FakeQuoteService(_response(_now())), repo, ttl_hours=6,
        daily_sync=empty_daily_sync(repo),
    )

    assert service._refresh_lock.acquire(blocking=False)  # Lauf simulieren
    try:
        with pytest.raises(RefreshInProgressError):
            service.refresh_all()
    finally:
        service._refresh_lock.release()

    assert service.refresh_all() == 0  # nach Freigabe läuft es wieder


class _FakeDailyProvider:
    """Liefert feste Tages-Schlusskurse für die Volatilitätsberechnung."""

    def __init__(self, closes: list[float]) -> None:
        self._closes = closes

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        ticker: str | None = None,
        mic: str | None = None,
    ):
        return [
            {"date": f"2026-01-{index + 1:02d}", "close": close, "currency": "EUR"}
            for index, close in enumerate(self._closes)
        ]


class _StockQuoteService:
    """Minimaler QuoteService-Stub: liefert eine Aktien-Antwort ohne Volatilität."""

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        return QuoteResponse(
            isin=isin, symbol="AAPL.DE", ticker="AAPL", mic="XETR",
            currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="stock", volatility=None,
        )

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        return self.get_quote_by_isin(isin or symbol, enrich_etf)


def test_refresh_one_berechnet_volatilitaet_aus_cache(tmp_path) -> None:
    db_path = str(tmp_path / "vola.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    closes = [100.0, 101.0, 99.5, 102.0, 100.5, 103.0, 101.5]
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider(closes))
    service = CachedQuoteService(_StockQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("US0378331005")

    assert result.volatility == annualized_volatility(closes)
    stored = repo.get_instrument_by_isin("US0378331005")
    assert stored["volatility"] == result.volatility


def test_refresh_behaelt_justetf_volatilitaet(tmp_path) -> None:
    """Liefert der QuoteService bereits eine Volatilität (justETF), wird sie nicht überschrieben."""

    class _EtfQuoteService:
        def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
            return QuoteResponse(
                isin=isin, symbol="VGWL.DE", ticker="VGWL", mic="XETR",
                currency="EUR", price=160.0,
                quote_time="2026-07-13T10:00:00+00:00",
                fetched_at="2026-07-13T10:00:00+00:00", type="etf", volatility=9.95,
            )

    db_path = str(tmp_path / "vola2.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider([100.0, 200.0, 50.0, 300.0, 80.0]))
    service = CachedQuoteService(_EtfQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("IE00B3RBWM25")

    assert result.volatility == 9.95  # justETF-Wert bleibt


def test_refresh_behaelt_letzte_volatilitaet_bei_fehlgeschlagener_neuberechnung(
    tmp_path,
) -> None:
    """EOD-Cache leer und Delta-Fetch tot → letzter bekannter Wert bleibt erhalten."""

    class _FailingDailyProvider:
        """Liefert nie Kurse (leerer EOD-Cache, Delta-Fetch schlägt fehl)."""

        def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        ticker: str | None = None,
        mic: str | None = None,
    ):
            return None

    db_path = str(tmp_path / "vola3.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    daily_sync = DailyCloseSync(repo, _FailingDailyProvider())
    service = CachedQuoteService(_StockQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    repo.save_quote(_StockQuoteService().get_quote_by_isin("US0378331005"))
    stored_before = repo.get_instrument_by_isin("US0378331005")
    repo.set_volatility(stored_before["id"], 12.5)  # vorherige, bereits bekannte Volatilität

    result = service.refresh_one("US0378331005")

    assert result.volatility == 12.5  # nicht mit None überschrieben
    stored = repo.get_instrument_by_isin("US0378331005")
    assert stored["volatility"] == 12.5


class _RecordingQuoteService:
    """Merkt sich, ob justETF gefragt werden sollte."""

    def __init__(self, response: QuoteResponse) -> None:
        self._response = response
        self.enrich_calls: list[bool] = []

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        self.enrich_calls.append(enrich_etf)
        return self._response

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        return self.get_quote_by_isin(symbol, enrich_etf)

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        self.enrich_calls.append(enrich_etf)
        return self._response


def _age_metadata(repo: QuoteRepository, meta_fetched_at: str) -> None:
    """Setzt den Zeitstempel des Metadatenstands direkt in der DB."""
    import sqlite3

    with sqlite3.connect(repo._database_path) as connection:  # noqa: SLF001
        connection.execute(
            "UPDATE instruments SET meta_fetched_at = ?", (meta_fetched_at,)
        )


def test_junge_etf_kennzahlen_loesen_keinen_justetf_abruf_aus(repo) -> None:
    """`metadata_ttl_days` war reine Anzeige — justETF lief bei jedem Kurs mit.

    Kurse und Kennzahlen altern verschieden schnell: Ein Kurs ist nach Stunden
    veraltet, ein Fondsdomizil ändert sich in Jahren nicht. Der Sammelrefresh
    kostete dadurch einen Scrape je ETF und Runde.
    """
    fake = _RecordingQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _age_metadata(repo, _now())  # Kennzahlen von gerade eben

    service = CachedQuoteService(
        fake, repo, ttl_hours=0, daily_sync=empty_daily_sync(repo), metadata_ttl_days=7
    )
    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [False], "junger Stand — justETF bleibt außen vor"


def test_alte_etf_kennzahlen_loesen_einen_justetf_abruf_aus(repo) -> None:
    fake = _RecordingQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _age_metadata(repo, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat())

    service = CachedQuoteService(
        fake, repo, ttl_hours=0, daily_sync=empty_daily_sync(repo), metadata_ttl_days=7
    )
    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [True]


def test_unbekanntes_papier_wird_immer_angereichert(repo) -> None:
    """Sonst bekäme ein frisch hinzugefügter ETF seine Kennzahlen nie."""
    fake = _RecordingQuoteService(_response(_now()))
    service = CachedQuoteService(
        fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo), metadata_ttl_days=7
    )

    service.get_by_isin("IE00B3RBWM25")

    assert fake.enrich_calls == [True]


def test_handrefresh_uebergeht_die_metadaten_ttl(repo) -> None:
    """Wer bewusst auf ↻ drückt, will frische Zahlen — auch die Kennzahlen.

    Der Sammel- und der Hintergrundlauf halten sich an die TTL; der Griff zum
    einzelnen Papier ist die ausdrückliche Ansage, jetzt nachzusehen.
    """
    fake = _RecordingQuoteService(_response(_now()))
    repo.save_quote(_response("2026-01-01T00:00:00+00:00"))
    _age_metadata(repo, _now())  # Kennzahlen taufrisch — die TTL griffe

    service = CachedQuoteService(
        fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo), metadata_ttl_days=7
    )
    service.refresh_one("IE00B3RBWM25")

    assert fake.enrich_calls == [True]


class _DriftingResolution:
    """QuoteService, dessen ISIN-Auflösung bei jedem Aufruf eine andere Börse trifft.

    Genau das passiert in echt: `CompositeResolver` fragt zuerst OpenFIGI
    (Xetra, EUR) und fällt bei Ausfall auf die Yahoo-Suche zurück, die das
    primäre Listing liefert — bei einem iShares-Papier die Londoner Notierung
    in GBP. Wer über die ISIN geht, bekommt also mal das eine, mal das andere.
    """

    def __init__(self) -> None:
        self.isin_calls = 0
        self.symbol_calls = 0
        self.known_calls = 0

    def _response_for(self, symbol: str, currency: str, exchange: str) -> QuoteResponse:
        return QuoteResponse(
            isin="IE00BCRY6557",
            symbol=symbol,
            # Der Ticker steht vor dem Punkt. Die Börsen stehen ausgeschrieben
            # da, statt aus dem Suffix gerechnet zu werden — die Fake-Quelle
            # soll die Zerlegungsregel des Produkts nicht nachbauen.
            ticker=symbol.split(".")[0],
            mic={"DE": "XETR", "L": "XLON", "MI": "XMIL"}[symbol.split(".")[1]],
            currency=currency,
            exchange=exchange,
            price=101.19,
            quote_time=_now(),
            fetched_at=_now(),
            type="etf",
        )

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        self.isin_calls += 1
        # Erster Aufruf trifft Xetra, jeder weitere London.
        if self.isin_calls == 1:
            return self._response_for("IS3M.DE", "EUR", "Xetra")
        return self._response_for("IS3M.L", "GBP", "London")

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        self.symbol_calls += 1
        return self._response_for(symbol, "EUR", "Xetra")

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        self.known_calls += 1
        return self._response_for(symbol, "EUR", exchange or "Xetra")


def test_refresh_loest_bekanntes_instrument_nicht_neu_auf(repo: QuoteRepository) -> None:
    """Ein bekanntes Papier behält seine Börse — auch wenn die Auflösung wandert.

    Der Fall aus der Praxis: Nach einem Sammel-Refresh notierten zwei
    Positionen plötzlich in USD und GBP, fielen damit aus der Währungsrechnung
    des Depots und verfälschten Gesamtwert und Anteile.
    """
    fake = _DriftingResolution()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    # Erster Kontakt: Das Papier ist unbekannt und wird aufgelöst.
    service.get_by_isin("IE00BCRY6557")
    assert fake.isin_calls == 1

    result = service.refresh_one("IE00BCRY6557")

    assert result.currency == "EUR"
    assert result.symbol == "IS3M.DE"
    # Entscheidend: Die ISIN wurde kein zweites Mal aufgelöst.
    assert fake.isin_calls == 1
    assert fake.known_calls == 1

    stored = repo.get_instrument_by_isin("IE00BCRY6557")
    assert stored["symbol"] == "IS3M.DE"


def test_refresh_all_loest_bekannte_instrumente_nicht_neu_auf(repo: QuoteRepository) -> None:
    """Derselbe Schutz für den Sammellauf — Scheduler und Dashboard gehen hier durch."""
    fake = _DriftingResolution()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.get_by_isin("IE00BCRY6557")
    refreshed = service.refresh_all()

    assert refreshed == 1
    assert fake.isin_calls == 1
    stored = repo.get_instrument_by_isin("IE00BCRY6557")
    assert stored["symbol"] == "IS3M.DE"


def test_refresh_einer_unbekannten_isin_loest_weiterhin_auf(repo: QuoteRepository) -> None:
    """Ohne Auflösung ließe sich nie ein neues Papier aufnehmen."""
    fake = _DriftingResolution()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.refresh_one("IE00BCRY6557")

    assert fake.isin_calls == 1


class _WithoutType:
    """Live-Antwort ohne `type` — yfinance liefert nicht immer einen quote_type.

    Der gefährliche Fall: Ohne Typ läuft `_build` am ETF-Zweig vorbei,
    `metadata_complete` bleibt auf seiner Vorgabe `True`, und das Repository
    darf die von justETF gepflegten Felder überschreiben — mit nichts.
    """

    def __init__(self) -> None:
        self.seen_type: str | None = "nie aufgerufen"

    def _response_for(self, instrument_type: str | None) -> QuoteResponse:
        return QuoteResponse(
            isin="IE00B3RBWM25",
            symbol="VGWL.DE",
            ticker="VGWL",
            mic="XETR",
            currency="EUR",
            exchange="Xetra",
            price=161.0,
            quote_time=_now(),
            fetched_at=_now(),
            type=instrument_type,
        )

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        return self._response_for("etf")

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        return self._response_for("etf")

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        self.seen_type = instrument_type
        # Der Live-Abruf weiß den Typ diesmal nicht — er muss vom Aufrufer kommen.
        return self._response_for(instrument_type)


def test_refresh_reicht_den_gespeicherten_typ_durch(repo: QuoteRepository) -> None:
    """Ohne Typ liefe der Refresh am ETF-Schutz vorbei und löschte die Kennzahlen.

    `resolve_isin` war der zweite Lieferant von `type`; wer ein bekanntes Papier
    ohne Auflösung auffrischt, muss ihn deshalb aus der gespeicherten Zeile
    mitgeben.
    """
    fake = _WithoutType()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    # Erster Kontakt legt das Instrument als ETF an.
    service.get_by_isin("IE00B3RBWM25")
    assert repo.get_instrument_by_isin("IE00B3RBWM25")["type"] == "etf"

    service.refresh_one("IE00B3RBWM25")

    assert fake.seen_type == "etf"
    assert repo.get_instrument_by_isin("IE00B3RBWM25")["type"] == "etf"


def test_lesepfad_loest_bekanntes_instrument_nicht_neu_auf(repo: QuoteRepository) -> None:
    """Derselbe Schutz wie beim Refresh — nur auf dem meistgenutzten Endpunkt.

    `GET /quote/{isin}` mit abgelaufener TTL ging weiterhin über
    `get_quote_by_isin` und damit durch den Resolver. Das Ergebnis wird
    gespeichert, also konnte eine gepflegte Xetra-Zeile beim schlichten
    Nachschlagen zu `IS3M.L`/GBP werden — genau der Fall, gegen den
    `get_quote_for_known` gebaut wurde.
    """
    fake = _DriftingResolution()
    # Bekanntes Papier mit abgelaufenem Kurs.
    repo.save_quote(
        QuoteResponse(
            isin="IE00BCRY6557", symbol="IS3M.DE", ticker="IS3M", mic="XETR",
            currency="EUR", exchange="Xetra",
            price=100.0, quote_time=_hours_ago(10), fetched_at=_hours_ago(10),
            type="etf",
        )
    )
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00BCRY6557")

    assert fake.isin_calls == 0  # entscheidend: keine erneute Auflösung
    assert fake.known_calls == 1
    assert result.symbol == "IS3M.DE"
    assert result.currency == "EUR"
    assert repo.get_instrument_by_isin("IE00BCRY6557")["symbol"] == "IS3M.DE"


def test_lesepfad_per_symbol_loest_bekanntes_instrument_nicht_neu_auf(
    repo: QuoteRepository,
) -> None:
    """`GET /quote/symbol/{symbol}` trägt dasselbe Risiko und braucht denselben Schutz."""
    fake = _DriftingResolution()
    repo.save_quote(
        QuoteResponse(
            isin="IE00BCRY6557", symbol="IS3M.DE", ticker="IS3M", mic="XETR",
            currency="EUR", exchange="Xetra",
            price=100.0, quote_time=_hours_ago(10), fetched_at=_hours_ago(10),
            type="etf",
        )
    )
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_symbol("IS3M.DE")

    assert fake.symbol_calls == 0
    assert fake.known_calls == 1
    assert result.currency == "EUR"


def test_unbekannte_isin_wird_im_lesepfad_weiterhin_aufgeloest(
    repo: QuoteRepository,
) -> None:
    """Ohne Auflösung käme nie ein neues Papier herein — der Fallback bleibt."""
    fake = _DriftingResolution()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.get_by_isin("IE00BCRY6557")

    assert fake.isin_calls == 1
    assert fake.known_calls == 0


class _RecordingCall:
    """Hält fest, mit welchen Angaben `get_quote_for_known` gerufen wurde."""

    def __init__(self) -> None:
        self.known_calls = 0
        self.symbol_calls = 0
        self.gesehene_isin: str | None = None
        self.seen_type: str | None = None
        self.gesehene_boerse: str | None = None

    def _response_for(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(
            isin="IE00B4L5Y983", symbol=symbol, ticker=symbol.split(".")[0],
            mic="XETR", currency="EUR", exchange="Xetra",
            price=129.1, quote_time=_now(), fetched_at=_now(), type="etf",
        )

    def get_quote_by_isin(self, isin: str, enrich_etf: bool = True) -> QuoteResponse:
        return self._response_for("EUNL.DE")

    def get_quote_by_symbol(self, symbol: str, enrich_etf: bool = True) -> QuoteResponse:
        self.symbol_calls += 1
        return self._response_for(symbol)

    def get_quote_for_known(
        self,
        symbol: str,
        isin: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        ticker: str | None = None,
        mic: str | None = None,
        enrich_etf: bool = True,
    ) -> QuoteResponse:
        self.known_calls += 1
        self.gesehene_isin = isin
        self.seen_type = instrument_type
        self.gesehene_boerse = exchange
        return self._response_for(symbol)


def test_refresh_per_symbol_reicht_die_gespeicherte_zeile_durch(
    repo: QuoteRepository,
) -> None:
    """Sonst greift der ETF-Schutz nicht und der Refresh-Knopf bleibt wirkungslos.

    `get_quote_by_symbol` gab weder ISIN noch Gattung mit. Ohne ISIN läuft die
    justETF-Anreicherung gar nicht erst an (`enrich_etf and isin` in `_build`),
    die Antwort meldet `metadata_complete=False` — und TER, Anbieter und
    Domizil bleiben stehen, wo sie sind. Der Knopf an der Zeile tat damit
    nichts von dem, was er verspricht.
    """
    fake = _RecordingCall()
    repo.save_quote(
        QuoteResponse(
            isin="IE00B4L5Y983", symbol="EUNL.DE", ticker="EUNL", mic="XETR",
            currency="EUR", exchange="Xetra",
            price=128.7, quote_time=_now(), fetched_at=_now(), type="etf",
        )
    )
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.refresh_one_by_symbol("EUNL.DE")

    assert fake.known_calls == 1
    assert fake.symbol_calls == 0
    assert fake.gesehene_isin == "IE00B4L5Y983"
    assert fake.seen_type == "etf"
    assert fake.gesehene_boerse == "Xetra"


def test_refresh_eines_unbekannten_symbols_geht_weiter_ueber_die_suche(
    repo: QuoteRepository,
) -> None:
    """Ein Papier ohne gespeicherte Zeile hat nichts durchzureichen."""
    fake = _RecordingCall()
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    service.refresh_one_by_symbol("EUNL.DE")

    assert fake.symbol_calls == 1
    assert fake.known_calls == 0


def _drop_currency(repo: QuoteRepository, isin: str = "IE00B3RBWM25") -> None:
    """Nimmt Kurspunkt **und** Instrument die Währung — ein Altbestand ohne sie."""
    instrument = repo.get_instrument_by_isin(isin)
    with repo._connect() as connection:  # noqa: SLF001 — Altbestand nachstellen
        connection.execute(
            "UPDATE quotes SET currency = NULL WHERE instrument_id = ?",
            (instrument["id"],),
        )
        connection.execute(
            "UPDATE instruments SET currency = NULL WHERE id = ?", (instrument["id"],)
        )


def test_frischer_cache_ohne_waehrung_liefert_keinen_kurs(
    repo: QuoteRepository,
) -> None:
    """Die Währungspflicht gilt auch für den meistgenutzten Weg.

    Der Live-Pfad prüfte den Core, der Cache-Pfad nicht — und über den läuft
    der Normalfall. Eine Antwort ohne Währung ist auch dann unverwertbar, wenn
    sie aus dem eigenen Bestand kommt.
    """
    repo.save_quote(_response(_now()))
    _drop_currency(repo)
    fake = FakeQuoteService(_response(_now()))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    with pytest.raises(QuoteUnavailableError):
        service.get_by_isin("IE00B3RBWM25")

    assert fake.calls == 0, "der Cache war frisch — es hätte kein Live-Abruf laufen dürfen"


def test_stale_cache_ohne_waehrung_liefert_keinen_kurs(repo: QuoteRepository) -> None:
    """Auch der Notnagel darf keinen unverwertbaren Kurs ausliefern.

    Schlägt die frische Beschaffung fehl, wird sonst der alte Wert gereicht —
    und der trüge hier keine Währung. Ein Fehler ist die richtige Antwort:
    Eine Position mit unbekannter Währung fällt aus jeder Depotrechnung.
    """
    repo.save_quote(_response(_hours_ago(10)))
    _drop_currency(repo)
    service = CachedQuoteService(
        FakeQuoteService(None, raises=True), repo, ttl_hours=6,
        daily_sync=empty_daily_sync(repo),
    )

    with pytest.raises(QuoteUnavailableError):
        service.get_by_isin("IE00B3RBWM25")


def test_cache_mit_waehrung_am_instrument_bleibt_nutzbar(repo: QuoteRepository) -> None:
    """Die Gegenprobe: Trägt das Listing eine Währung, genügt das.

    Sonst hätte die Verschärfung jeden älteren Kurspunkt unbrauchbar gemacht,
    dessen Zeile die Währung nicht mitführt.
    """
    repo.save_quote(_response(_now()))
    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    with repo._connect() as connection:  # noqa: SLF001
        connection.execute(
            "UPDATE quotes SET currency = NULL WHERE instrument_id = ?",
            (instrument["id"],),
        )
    service = CachedQuoteService(
        FakeQuoteService(_response(_now())), repo, ttl_hours=6,
        daily_sync=empty_daily_sync(repo),
    )

    assert service.get_by_isin("IE00B3RBWM25").currency == "EUR"


def test_historienpunkt_ohne_waehrung_erbt_die_des_listings(
    repo: QuoteRepository,
) -> None:
    """Auch `history.currency` ist Pflicht — und gehört zum Listing.

    Ältere Kurspunkte können ohne Währung gespeichert sein: Vor der
    Währungspflicht ging eine Antwort ohne sie durch. Beim Lesen gilt deshalb
    die Währung des Instruments, statt einen vertragswidrigen Punkt
    auszuliefern.
    """
    repo.save_quote(_response(_now()))  # Instrument in EUR
    instrument = repo.get_instrument_by_isin("IE00B3RBWM25")
    with repo._connect() as connection:  # noqa: SLF001 — Altbestand nachstellen
        connection.execute(
            "UPDATE quotes SET currency = NULL WHERE instrument_id = ?",
            (instrument["id"],),
        )

    service = CachedQuoteService(
        FakeQuoteService(_response(_now())), repo, ttl_hours=6,
        daily_sync=empty_daily_sync(repo),
    )

    points = service.get_history("IE00B3RBWM25")

    assert points, "keine Punkte geliefert"
    assert all(point.currency == "EUR" for point in points)


def _maintained_etf(fetched_at: str) -> QuoteResponse:
    """Ein ETF mit vollständigem, aus der Quelle stammendem Metadatenstand."""
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        ticker="VGWL",
        mic="XETR",
        currency="EUR",
        price=160.98,
        quote_time=fetched_at,
        fetched_at=fetched_at,
        type="etf",
        ter=0.2,
        provider="Vanguard",
        replication="Physical",
        accumulating=True,
        source="yfinance+justetf",
    )


def _incomplete_response(fetched_at: str, price: float) -> QuoteResponse:
    """Frischer Kurs ohne ETF-Extras — justETF wurde nicht gefragt."""
    return QuoteResponse(
        isin="IE00B3RBWM25",
        symbol="VGWL.DE",
        ticker="VGWL",
        mic="XETR",
        currency="EUR",
        price=price,
        quote_time=fetched_at,
        fetched_at=fetched_at,
        type="etf",
        source="yfinance",
        metadata_complete=False,
    )


def test_incomplete_response_traegt_den_gespeicherten_stand(
    repo: QuoteRepository,
) -> None:
    """Was in der Datenbank steht, muss auch in der Antwort stehen.

    Kurs-TTL abgelaufen, Metadaten-TTL noch frisch: justETF wird zu Recht nicht
    gefragt, die frische Antwort hat deshalb keine ETF-Felder. Das Repository
    schützt seinen Stand — die Antwort an den Client wurde aber unverändert
    durchgereicht. Gemessen am 2026-08-19: `ter` in der Antwort ``null``, in der
    Datenbank ``0.2``.
    """
    repo.save_quote(_maintained_etf(_hours_ago(10)))
    fake = FakeQuoteService(_incomplete_response(_now(), price=170.0))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.price == 170.0  # der Kurs ist frisch
    assert result.ter == 0.2
    assert result.provider == "Vanguard"
    assert result.replication == "Physical"
    assert result.accumulating is True
    assert result.source == "yfinance+justetf"


def test_vollstaendige_antwort_darf_einen_wert_auch_leeren(
    repo: QuoteRepository,
) -> None:
    """Der gespeicherte Stand füllt Lücken — er überstimmt die Quelle nicht.

    Hat justETF geantwortet und nennt einen Wert nicht mehr, ist das eine
    Aussage. Sie muss durchkommen, sonst ließe sich eine Kennzahl nie wieder
    loswerden — und die Antwort widerspräche der Zeile, die daneben gespeichert
    wird.
    """
    repo.save_quote(_maintained_etf(_hours_ago(10)))
    complete = _incomplete_response(_now(), price=170.0)
    complete.metadata_complete = True
    fake = FakeQuoteService(complete)
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.get_by_isin("IE00B3RBWM25")

    assert result.ter is None
    assert result.source == "yfinance"


def test_auch_der_refresh_haelt_den_gespeicherten_stand(
    repo: QuoteRepository,
) -> None:
    """Derselbe Fehler auf dem Refresh-Pfad: justETF ausgefallen, Werte weg.

    `refresh_one` fragt justETF ausdrücklich — antwortet die Quelle nicht, ist
    die frische Antwort genauso unvollständig wie oben, und der Knopf an der
    Zeile leerte die Anzeige.
    """
    repo.save_quote(_maintained_etf(_hours_ago(10)))
    fake = FakeQuoteService(_incomplete_response(_now(), price=170.0))
    service = CachedQuoteService(fake, repo, ttl_hours=6, daily_sync=empty_daily_sync(repo))

    result = service.refresh_one("IE00B3RBWM25")

    assert result.price == 170.0
    assert result.ter == 0.2
    assert result.provider == "Vanguard"
