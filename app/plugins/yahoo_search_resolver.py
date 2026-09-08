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

from types import MappingProxyType
from typing import Any

from stockinfo_plugin import (
    ListedIdentity,
    MicCoverage,
    NotFound,
    PairIdentity,
    Resolution,
    Resolved,
    Resolver,
    ResolveRequest,
    Unsupported,
)

from app.plugins.exchange_support import ONLINE_MICS
from app.providers.base import ResolvedInstrument
from app.resolver import DEFAULT_EXCHANGE, YFinanceResolver


class YahooSearchResolverPlugin(Resolver):
    """ISIN → Ticker + MIC über die Yahoo-Suche, in der Resolver-Rolle."""

    name = "yahoo-search"
    cost = "free"
    api_version = 2
    MIC_SUPPORT = MappingProxyType({
        "resolvers": MicCoverage(ONLINE_MICS),
    })
    # **`pair` und `crypto` seit T-31.** Yahoo führt `BTC-EUR` nativ und
    # meldet `quoteType: CRYPTOCURRENCY`; ohne diese beiden Zeilen wies der
    # Vorfilter die Quelle ab, die als einzige antworten konnte — und die
    # Aufnahme einer Coin scheiterte an einer Deklaration statt an einer
    # fehlenden Fähigkeit.
    SUPPORTED_KINDS = frozenset({"listed", "pair"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto"})

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
        return bool(request.isin or request.symbol)

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Fragt die Yahoo-Suche und übersetzt ihre Antwort.

        **Zwei Einstiege, eine Quelle.** Liegt eine ISIN vor, wird über sie
        gesucht; sonst über das Symbol. Der Symbolweg ist der einzige, über
        den ein Papier ohne ISIN — eine Coin — überhaupt hereinkommt.

        Returns:
            `Resolved` nur mit **vollständiger** Identität. Ein Treffer ohne
            Ticker oder echten MIC wird zu `NotFound` — dieselbe Regel wie bei
            OpenFIGI, und aus demselben Grund: Der Core baut aus beiden das
            Symbol, mit dem er später den Kurs holt.
        """
        core = self._core(request)
        if request.isin:
            answer = core.resolve_isin(request.isin)
        else:
            answer = core.resolve_symbol(request.symbol or "")

        if not isinstance(answer, ResolvedInstrument):
            # NotFound, Unavailable und NotResponsible kommen bereits aus
            # `stockinfo_plugin.types`.
            return answer

        # **Die nicht geführte Gattung wird zuerst entschieden** (T-31, Matrix
        # `#6`) — und zwar vor der Pflichtfeldprüfung darunter, nicht danach.
        #
        # `Unsupported` braucht keinen Namen; es trägt nur die Gattung. Stünde
        # die Pflichtprüfung davor, käme ein Index **ohne** Namen als
        # `NotFound` heraus, und der Benutzer läse wieder den Zufallsbefund,
        # den T-31 gerade abgeschafft hat. Die Reihenfolge ist hier also keine
        # Stilfrage, sondern die Zusicherung selbst.
        if answer.type and answer.type not in self.SUPPORTED_TYPES:
            return Unsupported(instrument_type=answer.type)

        # **Pflichtfelder vor der Formweiche** (T-38). Fehlt Name oder
        # Gattung, ist die Antwort für jede Identitätsform unbrauchbar — die
        # Prüfung hinter die Weiche zu schreiben hieße, sie beim nächsten
        # Formzuwachs einmal zu vergessen.
        #
        # Genau diese Quelle hat den Befund ausgelöst: Im UI-Lauf vom
        # 2026-08-28 lieferte die Yahoo-Suche eine vollständige Identität mit
        # leerem Namen und leerer Gattung, und die App nahm es an.
        if not answer.name or not answer.type:
            return NotFound()

        if answer.kind == "pair":
            return Resolved(
                identity=PairIdentity(
                    base=answer.base or "", quote_currency=answer.quote_currency or ""
                ),
                name=answer.name,
                instrument_type=answer.type,
            )

        if not answer.ticker or not answer.mic:
            # **Hier stand `NotFound` — über ein Papier, das gerade erkannt
            # wurde.** Der Kommentar daneben behauptete, die Gattung reise
            # mit; die Zeile darunter warf sie weg, weil `Resolved` eine
            # Identität verlangt und ein Index keine der drei Formen trägt.
            # Der Benutzer las am Ende „das Symbol nennt keinen
            # Handelsplatz" — richtig beobachtet und am Grund vorbei.
            #
            # Seit `API_VERSION` 2 gibt es die Antwort dafür. Unterschieden
            # werden **zwei** Fälle, und der Unterschied ist genau Matrix `#6`:
            #
            # * Eine Gattung, die diese Quelle **nicht zusagt** (`index`,
            #   `currency`, `future`): `Unsupported`. Sie sagt damit nichts
            #   über StockInfo — was der Host führt, entscheidet er selbst.
            #   Diese Weiche steht seit T-38 **weiter oben**, weil sie ohne
            #   Namen auskommt und die Pflichtfeldprüfung sie sonst
            #   überholt hätte.
            # * Eine zugesagte Gattung ohne Handelsplatz (`AAPL` ohne
            #   auflösbare Börse): weiterhin `NotFound`. Das Papier gäbe es,
            #   nur ist es hier nicht identifizierbar.
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
