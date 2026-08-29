"""Die vorhandene Yahoo-Suche in der Resolver-Rolle des Plugin-Vertrags.

**Die letzte Quelle, die den Vertrag nicht sprach — und die einzige, bei der
das im Betrieb wehtat.** Bis T-35 baute `_yahoo_search` in der Registry direkt
`app.resolver.YFinanceResolver`, eine Klasse mit den **Core**-Signaturen
`handles(isin: str)` und `resolve_isin(isin)`. Seit Runde 3 adaptiert
`_build_one` aber **jede** Quelle („Jede Quelle spricht den Vertrag") und
stülpte ihr den `ResolverAdapter` über, der `handles(ResolveRequest)` und
`resolve(request)` erwartet.

Das Ergebnis war schlimmer als ein Ausfall. Gemessen am 2026-08-28:

    handles("US0378331005")     -> True      # falsch, aber unauffällig
    resolve_isin("XX00000000")  -> AttributeError: 'YFinanceResolver'
                                   object has no attribute 'resolve'

`handles` bekam ein `ResolveRequest`-Objekt statt einer Zeichenkette und sagte
trotzdem `True` — die Quelle nahm die Anfrage also an. Erst danach fiel sie um,
und `CompositeResolver` fängt in seiner Kaskade nichts ab. Jede ISIN, die
OpenFIGI **nicht** kennt, endete damit in einem `500` statt in einem sauberen
„nicht gefunden" — ausgerechnet der Fallback für US-Titel, für den diese Quelle
überhaupt existiert.

**Warum eine Hülle und keine Reparatur am Adapter.** Der Adapter ist richtig:
Er übersetzt den Vertrag in die Sprache des Core. Ihn beide Formen erraten zu
lassen hieße, den Übergangszustand dauerhaft zu machen — genau das
`contract_roles`-Feld, das Runde 3 aus gutem Grund entfernt hat. Die Quelle
gehört auf den Vertrag gehoben, nicht der Vertrag auf die Quelle gesenkt.

Wie bei OpenFIGI steht hier **keine** Fachlogik: Welche Symbolform Yahoo
kennt, wie die Suche fragt und was ein Treffer ist, entscheidet
`YFinanceResolver`.
"""

from typing import Any

from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    Resolution,
    Resolved,
    Resolver,
    ResolveRequest,
)

from app.providers.base import ResolvedInstrument
from app.resolver import DEFAULT_EXCHANGE, YFinanceResolver


class YahooSearchResolverPlugin(Resolver):
    """ISIN → Ticker + MIC über die Yahoo-Suche, in der Resolver-Rolle."""

    name = "yahoo-search"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund"})

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        resolver: YFinanceResolver | None = None,
        default_exchange: str = DEFAULT_EXCHANGE,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
            resolver: Die vorhandene Anbindung; im Test wird eine
                hereingereicht.
            default_exchange: MIC der bevorzugten Börse. Dient nur als
                Rückfall — die Anfrage bringt ihre eigene mit.
        """
        super().__init__(config)
        self._default_exchange = default_exchange
        self._resolver = resolver

    def _core(self, request: ResolveRequest) -> YFinanceResolver:
        """Der Kern-Resolver für **diese** Anfrage.

        Die bevorzugte Börse steht im `ResolveRequest`, nicht im Konstruktor:
        Ein Plugin wird einmal gebaut und viele Male gefragt, und die Vorgabe
        gehört zur Frage. Eine hereingereichte Instanz gewinnt — sonst ließe
        sich die Quelle nicht ohne Netz prüfen.
        """
        if self._resolver is not None:
            return self._resolver
        return YFinanceResolver(request.preferred_mic or self._default_exchange)

    def handles(self, request: ResolveRequest) -> bool:
        """Diese Quelle braucht eine ISIN — mehr nicht.

        Sie ist der **Fallback** hinter OpenFIGI und hält sich deshalb nicht
        selbst für unzuständig. Die Kaskade fragt sie ohnehin erst, wenn die
        Quellen davor nichts geliefert haben.
        """
        return bool(request.isin)

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Fragt die Yahoo-Suche und übersetzt ihre Antwort.

        Returns:
            `Resolved` nur mit **vollständiger** Identität. Ein Treffer ohne
            Ticker oder echten MIC wird zu `NotFound` — dieselbe Regel wie bei
            OpenFIGI, und aus demselben Grund: Der Core baut aus beiden das
            Symbol, mit dem er später den Kurs holt.
        """
        answer = self._core(request).resolve_isin(request.isin or "")

        if not isinstance(answer, ResolvedInstrument):
            # NotFound, Unavailable und NotResponsible kommen bereits aus
            # `stockinfo_plugin.types`.
            return answer

        if not answer.ticker or not answer.mic:
            return NotFound()

        return Resolved(
            identity=ListedIdentity(
                ticker=answer.ticker,
                mic=answer.mic,
                isin=answer.isin or request.isin,
            ),
            name=answer.name,
            instrument_type=answer.type,
        )

    def configuration_problem(self) -> str:
        """Yahoo braucht keinen Schlüssel — und sagt das."""
        return ""
