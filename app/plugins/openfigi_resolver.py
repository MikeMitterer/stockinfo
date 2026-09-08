"""Die vorhandene OpenFIGI-Auflösung in der Resolver-Rolle des Plugin-Vertrags.

**Dieses Modul entscheidet nichts.** Es delegiert an
`app.resolver.OpenFigiResolver` und übersetzt dessen Antwort in die Typen des
Vertrags. Der HTTP-Aufruf, das Anfrageformat, die Yahoo-Symbolregel, die
Kaskade „bevorzugte Börse, dann Heimatbörse aus dem ISIN-Präfix" (T-18) und die
Weigerung, mit einem Sammelcode zu fragen (T-21) — all das steht dort und wird
von hier benutzt.

**Der erste Anlauf hat genau das nicht getan, und der Fehler ist lehrreich.**
Er baute die Kette `figi_lookup → map_isin → NotFound/Unavailable` ein zweites
Mal nach. Dabei ging verloren, was der Kern-Resolver längst weiß:

    _try_exchange(): if not is_real_mic(mic): return None

Der Sammelcode `US` fasst sechs Handelsplätze zusammen. OpenFIGI beantwortet
darauf „welcher Ticker", nicht „welche Börse" — ohne echten MIC ist die
Identität unvollständig, und deshalb wird **gar nicht erst gefragt**. Mein
Nachbau fragte trotzdem, bekam `AAPL` und lieferte `Resolved(mic="US")`: einen
Treffer, dessen MIC keiner ist. `ResolverContract` verbietet genau das, und
`is_real_mic("US")` ist `False`.

Ich hatte das sogar gemessen — und aus der Messung den falschen Schluss
gezogen, nämlich die Prüfung zu lockern statt der vorhandenen Entscheidung zu
folgen. Eine zweite Fassung derselben Fachlogik ist nicht nur doppelt, sie ist
die **ältere**.

Übersetzt wird deshalb nur noch:

    ResolvedInstrument mit ticker und mic  →  Resolved
    ResolvedInstrument ohne Identität      →  NotFound
    NotFound / Unavailable / NotResponsible →  unverändert durchgereicht

Die letzte Zeile ist wörtlich zu nehmen: `app.providers.base.Resolution`
benutzt für die Fehlfälle bereits `stockinfo_plugin.types`. Der Vertrag ist an
dieser Stelle schon gemeinsam — hier bleibt nur der Treffer zu übersetzen.
"""

from types import MappingProxyType
from typing import Any

import structlog
from stockinfo_plugin import (
    ListedIdentity,
    MicCoverage,
    NotFound,
    NotResponsible,
    Resolution,
    Resolved,
    Resolver,
    ResolveRequest,
)
from stockinfo_plugin.invariants import isin_check_digit_is_valid

from app.plugins.exchange_support import ONLINE_MICS
from app.providers.base import ResolvedInstrument
from app.providers.openfigi_provider import OpenFigiClient
from app.resolver import OpenFigiResolver as CoreOpenFigiResolver

logger = structlog.get_logger()


class OpenFigiResolverPlugin(Resolver):
    """ISIN → Ticker + MIC, über den Kern-Resolver der App.

    Der Name trägt das ``Plugin`` mit Absicht: `app.resolver.OpenFigiResolver`
    gibt es bereits, und zwei gleichnamige Klassen mit verschiedener Aufgabe
    sind der kürzeste Weg zu einer Verwechslung, die niemand bemerkt.
    """

    name = "openfigi"
    cost = "free"
    api_version = 2
    MIC_SUPPORT = MappingProxyType({
        "resolvers": MicCoverage(ONLINE_MICS),
    })
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "bond"})

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        client: OpenFigiClient | None = None,
        home_fallback: bool = True,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
                ``api_key`` ist optional und hebt nur das Ratenlimit.
            client: Der OpenFIGI-Client. Ohne Angabe wird einer aus der
                Konfiguration gebaut.
            home_fallback: Ob bei erfolglosem Versuch die Heimatbörse aus dem
                ISIN-Präfix gefragt wird — die Kaskade aus T-18.
        """
        super().__init__(config)
        self._client = client or OpenFigiClient(api_key=self.api_key)
        self._home_fallback = home_fallback

    @property
    def api_key(self) -> str:
        """Der Schlüssel, falls einer konfiguriert ist."""
        return str(self._config.get("api_key", ""))

    def handles(self, request: ResolveRequest) -> bool:
        """Diese Quelle braucht eine ISIN mit **gültiger Prüfziffer**.

        Ein Tippfehler in einer von Hand gepflegten Tabelle erzeugt fast immer
        eine ISIN mit falscher Prüfziffer. Danach zu fragen verbraucht ein
        Ratenlimit für eine Frage, die nicht stimmen kann.

        Über die Börse wird hier **nicht** geurteilt: Ob ein Merkmal taugt,
        entscheidet der Kern-Resolver — und er tut es strenger, als eine
        Formprüfung es könnte.
        """
        return isin_check_digit_is_valid(request.isin)

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Fragt den Kern-Resolver und übersetzt seine Antwort.

        Returns:
            `Resolved` nur mit **vollständiger** Identität — Ticker und echter
            MIC. Fehlt sie, ist das `NotFound`: Der Vertrag kennt keinen
            Treffer ohne Identität, und einen zu erfinden wäre schlimmer als
            keiner.
        """
        if not self.handles(request):
            return NotResponsible(
                "OpenFIGI braucht eine ISIN mit gültiger Prüfziffer"
            )

        core = CoreOpenFigiResolver(
            self._client,
            default_exchange=request.preferred_mic,
            home_fallback=self._home_fallback,
        )
        answer = core.resolve_isin(request.isin or "")

        if not isinstance(answer, ResolvedInstrument):
            # NotFound, Unavailable und NotResponsible kommen bereits aus
            # `stockinfo_plugin.types` — der Vertrag ist hier schon gemeinsam.
            return answer

        if not answer.ticker or not answer.mic:
            # Der Kern-Resolver setzt beide Felder nur, wenn die Zuordnung
            # eindeutig ist; er rät nichts. Ein `Resolved` ohne sie bestünde
            # `ResolverContract` nicht — und zwar zu Recht.
            return NotFound()

        # **Dieselbe Regel für Name und Gattung** (T-38). `FigiMatch` führt
        # beide als ``| None``: OpenFIGI kann eine ISIN einem Ticker zuordnen,
        # ohne zu wissen, *was* das Papier ist. Bis T-38 kam so ein Treffer
        # durch und erzeugte die halbe Zeile, wegen der dieses Ticket
        # existiert.
        #
        # `NotFound` und nicht `Unavailable`: Der Dienst war erreichbar und hat
        # geantwortet — seine Antwort trägt nur nicht, was der Vertrag
        # verlangt. Das Papier fällt damit an den Yahoo-Fallback dahinter, und
        # genau dafür gibt es ihn.
        if not answer.name or not answer.type:
            logger.info(
                "openfigi_incomplete",
                isin=request.isin,
                has_name=bool(answer.name),
                has_type=bool(answer.type),
            )
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
        """Diese Quelle läuft auch ohne Schlüssel — und sagt das.

        Ein `configuration_problem`, das hier einen Schlüssel verlangte, wäre
        eine Diagnose, die im Normalfall spricht. Nach dem dritten Mal liest
        sie niemand mehr, und dann fehlt sie dort, wofür sie gebaut wurde.
        """
        return ""
