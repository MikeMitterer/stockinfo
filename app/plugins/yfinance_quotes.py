"""Die vorhandene yfinance-Anbindung in drei Rollen des Plugin-Vertrags.

Eine Klasse, drei Rollen — `QuoteSource`, `DailyCloseSource`, `FxSource`. Das
ist kein Kunstgriff, sondern die Wirklichkeit: yfinance beantwortet alle drei
Fragen, und sie künstlich auf drei Klassen zu verteilen hieße, dieselbe
Anbindung dreimal zu halten. Genau diese Mehrfachrolle war der Grund, warum die
Protokolle `DailyCloseSource` und `FxSource` so lange gefehlt haben.

Wie in den anderen Plugins steht hier **keine** Fachlogik: Der Abruf, die
Prüfung auf brauchbare Kurse und die Zeitstempel stehen in
`app/providers/yfinance_provider.py`.

**Das Symbol ist die Stelle, an der die beiden Welten nicht deckungsgleich
sind, und das wird hier benannt statt geglättet.** yfinance kennt Symbole wie
``RY.TO``; der Vertrag fragt mit ``ticker`` **und** ``mic``. Aus beidem ein
Symbol zu bilden, ist eine Zuordnung, die nur die App kennt — sie kommt aus
`app.exchanges.provider_alias`. Ein Plugin ohne diese Tabelle könnte die Frage
nicht beantworten, und das ist der ehrliche Grund, warum diese Quelle
eingebaut bleibt und nicht als Beispiel für Fremdautoren taugt.
"""

from datetime import date, datetime, timezone
from typing import Any

from stockinfo_plugin import (
    DailyBar,
    DailyRequest,
    DailyResult,
    DailySeries,
    FxRate,
    FxRequest,
    FxResult,
    ListedIdentity,
    NotFound,
    NotResponsible,
    PairIdentity,
    Quote,
    QuoteRequest,
    QuoteResult,
    Unavailable,
)
from stockinfo_plugin.invariants import currency_problem, is_finite_price
from stockinfo_plugin.sources import DailyCloseSource, FxSource, QuoteSource

from app.exchanges import EXCHANGES, provider_alias
from app.providers.base import INSTRUMENT_TYPES
from app.providers.yfinance_provider import YFinanceProvider


class YFinancePlugin(QuoteSource, DailyCloseSource, FxSource):
    """Kurse, Tagesreihen und Wechselkurse über die vorhandene yfinance-Anbindung."""

    name = "yfinance"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair"})
    # **Ausgeschrieben, seit eine leere Menge „nichts zugesagt" heisst.** Sie
    # stand hier gar nicht, und der Vorfilter las das als „alles" — die Zusage
    # im Vertrag war damit folgenlos. yfinance bepreist tatsaechlich jede
    # Gattung des Katalogs; das steht jetzt da, statt es zu unterstellen.
    SUPPORTED_TYPES = frozenset(INSTRUMENT_TYPES)

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        provider: YFinanceProvider | None = None,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
            provider: Die vorhandene Anbindung; im Test wird eine hereingereicht.
        """
        super().__init__(config)
        self._provider = provider or YFinanceProvider()

    def _symbol(self, identity: object) -> str | None:
        """Die Identität als yfinance-Symbol — oder ``None``, wenn keins passt.

        Zwei Formen, zwei Schreibweisen, und die Weiche läuft über ``kind`` und
        **nie** über die Gestalt des Symbols:

        * `listed` → `provider_alias`, das weiß, dass Toronto ``.TO`` heißt und
          Xetra ``.DE``.
        * `pair` → ``{base}-{quote_currency}``, also ``BTC-EUR``. yfinance
          kennt diese Schreibweise nativ.

        Der Bindestrich ist damit **Trennzeichen der Paarform** und kein
        Erkennungsmerkmal: Aus ``BTC-EUR`` zu schließen, es handle sich um ein
        Paar, wäre genau das Raten aus der Symbolform, das T-31 Matrix `#5`
        verbietet. Die Form steht schon fest, wenn diese Methode gerufen wird.

        Eine `isin_only`-Anleihe hat hier keine Schreibweise — sie wird vom
        Vorfilter gar nicht erst hergeschickt, und `handles` sagt ``False``.

        **Die Prüfung auf `EXCHANGES` davor ist nicht Zierde, sie ist gemessen.**
        `provider_alias` liefert bei einer unbekannten Börse den **nackten
        Ticker** zurück — das ist für die US-Plätze richtig, die keinen Alias
        führen, und für alles andere still falsch::

            provider_alias('AAPL', 'XNAS') -> 'AAPL'    # richtig, US ohne Alias
            provider_alias('RY',   'ZZZZ') -> 'RY'      # ZZZZ ist unbekannt …

        Im zweiten Fall fragte yfinance danach das **NYSE**-Listing von `RY` ab
        und lieferte einen Kurs — den falschen, in der falschen Währung, ohne
        dass irgendwo ein Fehler entstünde. Dasselbe Muster wie beim
        OpenFIGI-Sammelcode: Eine Antwort, die man nicht richtig geben kann,
        gibt man nicht.
        """
        if isinstance(identity, PairIdentity):
            return f"{identity.base}-{identity.quote_currency}"
        if not isinstance(identity, ListedIdentity):
            return None
        if identity.mic not in EXCHANGES:
            return None
        return provider_alias(identity.ticker, identity.mic)

    # ─── Kurs ────────────────────────────────────────────────────────────────

    def handles(self, request: object) -> bool:
        """Zuständig, sobald sich ein Symbol bilden lässt.

        Die drei Rollen teilen sich diese Methode, weil sie dieselbe Frage
        stellen: Kenne ich eine Schreibweise für diesen Handelsplatz? Bei
        `FxRequest` gibt es keinen — dort zählt, ob beide Währungen taugen.
        """
        if isinstance(request, FxRequest):
            return not currency_problem(request.base) and not currency_problem(
                request.quote
            )
        identity = getattr(request, "identity", None)
        return identity is not None and self._symbol(identity) is not None

    def fetch_quote(self, request: QuoteRequest) -> QuoteResult:
        """Holt einen Kurs.

        Returns:
            `Quote` mit Pflichtwährung und Zeitpunkt. `NotResponsible`, wenn
            sich kein Symbol bilden lässt; `NotFound`, wenn yfinance nichts
            liefert; `Unavailable`, wenn die Antwort unbrauchbar ist.
        """
        symbol = self._symbol(request.identity)
        if not symbol:
            return NotResponsible(
                f"keine yfinance-Schreibweise für {request.identity}"
            )

        raw = self._provider.fetch_quote(symbol)
        if raw is None:
            return NotFound()
        if not raw.currency:
            # **Ein Kurs ohne Währung ist keiner.** Er sähe in der Datenbank aus
            # wie ein Wert und wäre eine Zahl ohne Bedeutung.
            return Unavailable(f"{symbol}: Kurs ohne Währung")
        problem = currency_problem(raw.currency)
        if problem:
            return Unavailable(f"{symbol}: {problem}")
        if not is_finite_price(raw.price):
            return Unavailable(f"{symbol}: unbrauchbarer Kurs {raw.price!r}")

        return Quote(
            price=float(raw.price),
            currency=raw.currency,
            as_of=self._as_of(raw.quote_time),
            volume=raw.volume,
        )

    # ─── Tagesreihe ──────────────────────────────────────────────────────────

    def fetch_daily(self, request: DailyRequest) -> DailyResult:
        """Holt Tagesschlusskurse.

        **`adjusted=True`, und das ist keine Formalie.** Die Anbindung ruft
        `ticker.history(..., auto_adjust=True)` — die Kurse sind also um Splits
        und Ausschüttungen bereinigt. Hier `False` zu melden wäre die
        gefährlichere Sorte Fehler: Der Wert stimmte, seine Bedeutung nicht,
        und ein Verbraucher, der unbereinigte Kurse erwartet, rechnete mit
        einer Rendite, die es so nie gab.

        **Das Ende wird hier gefiltert, nicht dort.** `fetch_daily_closes`
        kennt nur einen Startpunkt. Ein `end` ins Leere laufen zu lassen wäre
        die stille Variante: Der Aufrufer bekäme mehr, als er wollte, und
        merkte es nicht.

        Returns:
            `DailySeries` mit Währung und aufsteigenden Tagen. Die Sortierung
            kommt aus der Anbindung; der Vertrag prüft sie, und das ist der
            richtige Ort dafür — hier sie noch einmal herzustellen hieße, einen
            Fehler zu verdecken, statt ihn zu melden.
        """
        symbol = self._symbol(request.identity)
        if not symbol:
            return NotResponsible(
                f"keine yfinance-Schreibweise für {request.identity}"
            )

        answer = self._provider.fetch_daily_closes(
            symbol, request.start.isoformat() if request.start else None
        )
        # Ohne Wert hat der Anbieter nichts geliefert; `disturbed` sagt, ob das
        # eine Störung war. Beides einzuebnen machte aus einem Ausfall ein
        # „gibt es nicht", und die App hörte auf zu fragen.
        if not answer.is_hit:
            if answer.disturbed:
                return Unavailable(f"{symbol}: Tagesreihe nicht abrufbar")
            return NotFound()
        closes = answer.value or []
        if not closes:
            return NotFound()

        rows = [
            row
            for row in closes
            if request.end is None or self._as_day(row["date"]) <= request.end
        ]
        if not rows:
            return NotFound()

        currency = rows[0].get("currency")
        if not currency:
            return Unavailable(f"{symbol}: Tagesreihe ohne Währung")

        bars = tuple(
            DailyBar(day=self._as_day(row["date"]), close=float(row["close"]))
            for row in rows
        )
        return DailySeries(bars=bars, currency=currency, adjusted=True)

    # ─── Devisen ─────────────────────────────────────────────────────────────

    def fetch_rate(self, request: FxRequest) -> FxResult:
        """Holt einen Wechselkurs.

        Der Identitätsfall geht ohne Anbieter: Eine Einheit einer Währung
        kostet genau eine Einheit derselben. Über einen Anbieter gerechnet käme
        0,9999… heraus, und der Vertrag verlangt **genau** 1.0.
        """
        if not self.handles(request):
            # **Befund des Vertrags.** Vorher fragte diese Methode den Anbieter
            # auch dann, wenn `handles` abgelehnt hatte — und ließ dessen
            # Ausnahme durch. Eine Quelle, die bei Unzuständigkeit trotzdem
            # zugreift, verbraucht Kontingent für eine Frage, die sie gar nicht
            # beantworten will; und `NotFound` statt `NotResponsible` ließe die
            # Kette zu früh abbrechen.
            return NotResponsible(
                f"{request.base}/{request.quote} ist kein gültiges Währungspaar"
            )

        if request.base == request.quote:
            return FxRate(
                base=request.base,
                quote=request.quote,
                rate=1.0,
                as_of=datetime.now(timezone.utc),
            )

        answer = self._provider.fetch_fx_rate(request.base, request.quote)
        if not answer.is_hit:
            # Dieselbe Weiche wie bei der Tagesreihe: Ein Abruf, der geworfen
            # hat, ist eine Störung; eine Antwort ohne Kurs heißt „führe ich
            # nicht".
            return (
                Unavailable(f"{request.base}{request.quote}: Kurs nicht abrufbar")
                if answer.disturbed
                else NotFound()
            )
        rate = answer.value
        if not is_finite_price(rate):
            return Unavailable(f"unbrauchbarer Kurs {rate!r}")

        return FxRate(
            base=request.base,
            quote=request.quote,
            rate=float(rate),
            as_of=datetime.now(timezone.utc),
        )

    # ─── Umformungen ─────────────────────────────────────────────────────────

    @staticmethod
    def _as_of(stamp: str) -> datetime:
        """Der Zeitstempel der Anbindung, **mit** Zone.

        Ein `datetime` ohne Zone wäre nach `has_timezone` kein Zeitpunkt und
        stürzte beim ersten Vergleich mit `TypeError` ab. Fehlt die Zone in der
        Angabe, wird UTC angenommen und das hier gesagt — nicht offengelassen.
        """
        try:
            moment = datetime.fromisoformat(stamp)
        except (TypeError, ValueError):
            return datetime.now(timezone.utc)
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)

    @staticmethod
    def _as_day(value: object) -> date:
        """Das Datum einer Zeile als `date`."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        return date.fromisoformat(str(value)[:10])

    def configuration_problem(self) -> str:
        """yfinance braucht keinen Schlüssel — und sagt das."""
        return ""
