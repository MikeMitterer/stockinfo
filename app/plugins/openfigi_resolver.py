"""Die vorhandene OpenFIGI-Anbindung in der Resolver-Rolle des Plugin-Vertrags.

Der Punkt dieses Plugins ist, was **nicht** darin steht: der HTTP-Aufruf, das
Anfrageformat, die Auswertung der Antwort, die Regel für brauchbare
Yahoo-Symbole. Das alles steht in `app/providers/openfigi_provider.py` und wird
von hier benutzt.

Ein Plugin, das seine API neu schreiben muss, um den Vertrag zu erfüllen, wäre
der Fehler und nicht die Lösung. Übersetzt wird nur, was die Rolle verlangt:

    OpenFigiClient.map_isin()                    →  Resolved | NotFound
    SourceUnavailableError                       →  Unavailable
    ISIN ohne Prüfziffer, MIC ohne Form          →  NotResponsible

Die mittlere Zeile ist die wichtigste. Der Client unterscheidet „kenne ich
nicht" von „konnte nicht fragen", und diese Unterscheidung kostete ihn einmal
einen Umbau: Solange beides als ``None`` zurückkam, wurde aus einem Ausfall ein
404, und die App hörte auf zu fragen, statt es später erneut zu versuchen. Der
Vertrag hat für beides einen eigenen Typ — hier treffen die beiden Sichten
aufeinander, und deshalb wird hier übersetzt und nicht neu entschieden.
"""

from typing import Any

from stockinfo_plugin import (
    NotFound,
    NotResponsible,
    Resolution,
    Resolved,
    ResolveRequest,
    Resolver,
    Unavailable,
)
from stockinfo_plugin.invariants import isin_check_digit_is_valid

from app.providers.base import SourceUnavailableError
from app.providers.openfigi_provider import OpenFigiClient, figi_lookup


class OpenFigiResolver(Resolver):
    """ISIN + MIC → Ticker, über den vorhandenen `OpenFigiClient`."""

    name = "openfigi"
    cost = "free"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        client: OpenFigiClient | None = None,
    ) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.
                ``api_key`` ist optional und hebt nur das Ratenlimit.
            client: Ein vorbereiteter Client. Ohne Angabe wird einer aus der
                Konfiguration gebaut.
        """
        super().__init__(config)
        self._client = client or OpenFigiClient(api_key=self.api_key)

    @property
    def api_key(self) -> str:
        """Der Schlüssel, falls einer konfiguriert ist."""
        return str(self._config.get("api_key", ""))

    def handles(self, request: ResolveRequest) -> bool:
        """Diese Quelle braucht eine **gültige** ISIN und ein Börsenmerkmal.

        Bei der ISIN wird die Prüfziffer geprüft und nicht nur die Gestalt: Ein
        Tippfehler in einer von Hand gepflegten Tabelle erzeugt fast immer eine
        ISIN mit falscher Prüfziffer. OpenFIGI danach zu fragen verbraucht
        Ratenlimit für eine Frage, die nicht stimmen kann.

        **Beim Börsenmerkmal wird ausdrücklich *nicht* auf einen MIC geprüft**,
        und das ist gemessen: Apple ist über ``micCode=XNAS`` bei OpenFIGI
        nicht zu finden, über ``exchCode=US`` schon. ``US`` ist Sammelcode und
        kein MIC — eine Prüfung mit `mic_is_wellformed` würde also genau den
        Weg abweisen, auf dem der Dienst US-Papiere überhaupt kennt.

        Was hier zählt, ist deshalb: Kann `figi_lookup` daraus ein
        Anfragemerkmal machen? Welche Codes das sind, weiß OpenFIGI und nicht
        dieser Vertrag.
        """
        return isin_check_digit_is_valid(request.isin) and bool(
            request.preferred_mic and request.preferred_mic.strip()
        )

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Fragt OpenFIGI nach dem Listing.

        Returns:
            `Resolved` mit Ticker und MIC, `NotResponsible` bei einer Anfrage,
            die nicht hierher gehört, `NotFound`, wenn OpenFIGI das Papier an
            dieser Börse nicht kennt, und `Unavailable` bei einer Störung.
        """
        if not self.handles(request):
            return NotResponsible(
                "OpenFIGI braucht eine ISIN mit gültiger Prüfziffer und einen MIC"
            )

        id_type, id_value = figi_lookup(request.preferred_mic)
        try:
            ticker = self._client.map_isin(
                request.isin or "", id_value=id_value, id_type=id_type
            )
        except SourceUnavailableError as error:
            return Unavailable(str(error))

        if not ticker:
            # `NotFound` trägt bewusst keinen Grund: „gibt es hier nicht" ist
            # die ganze Aussage. Ein Freitext daneben lüde dazu ein, ihn
            # auszuwerten — und dann hinge Verhalten an einer Formulierung.
            return NotFound()
        return Resolved(ticker=ticker, mic=request.preferred_mic, isin=request.isin)

    def configuration_problem(self) -> str:
        """Diese Quelle läuft auch ohne Schlüssel — und sagt das.

        Ein `configuration_problem`, das hier einen Schlüssel verlangte, wäre
        eine Diagnose, die im Normalfall spricht. Nach dem dritten Mal liest
        sie niemand mehr, und dann fehlt sie dort, wofür sie gebaut wurde.
        """
        return ""
