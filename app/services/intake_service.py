"""Der Aufnahmeweg — aus einem rohen Feldwert wird ein Instrument.

**Hier liegt die Fachregel, nicht im Router und nicht in
`app/routers/validation.py`** (T-21 Teil 3, Abschnitt A). Der Router übersetzt
zwischen HTTP und Service; was `identifier` bedeutet, entscheidet allein der
Core. Läge die Zuordnung in der Request-Validierung, stünde eine
Identitätsregel in einer Schicht, die HTTP-Formen prüft — und das Dashboard
bräuchte über kurz oder lang eine eigene Kopie davon.

Der Dienst gibt ein typisiertes Ergebnis zurück und nicht bloß die Identität:
Der Erfolgsvertrag verlangt ein vollständiges `InstrumentSummary` **und** die
Unterscheidung „neu angelegt" gegen „gab es schon". Lieferte er nur
`(ticker, mic)`, müsste der Router die Summary selbst beschaffen und den
vorherigen Datenbankzustand ein zweites Mal ermitteln — genau die Fach- und
Repository-Logik, die er nicht enthalten darf.
"""

from dataclasses import dataclass

import structlog

from app.exchanges import identity_from_input, input_failure, is_isin
from app.services.quote_cache import CachedQuoteService, StoredQuote
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteUnavailableError,
)

logger = structlog.get_logger()

# Der Rohwert ist leer oder nur Leerraum — kein Ticker, keine ISIN, nichts.
REASON_EMPTY = "identifier_empty"

# Die Form passt zu keinem der beiden Wege: weder ISIN noch zerlegbares Symbol.
# Die drei genaueren Symbolgründe kommen aus `rejection_reason`.
REASON_UNKNOWN_FORM = "identifier_unknown_form"

# Form und Zerlegung stimmen, aber die Quellen kennen das Papier nicht.
REASON_NOT_FOUND = "instrument_not_found"


@dataclass(frozen=True)
class IntakeResult:
    """Das aufgenommene Papier und ob es in diesem Aufruf entstanden ist.

    `summary` ist die Rohform eines `InstrumentSummary` — dieselbe Zeile, die
    `GET /instruments` liefert, damit der Aufrufer nach der Aufnahme nicht
    noch einmal die Liste holen muss, um Ticker und echten MIC zu sehen.
    """

    summary: dict
    created: bool


class IntakeRejected(Exception):
    """Der Rohwert führt zu keinem Papier — mit Kennung und Parametern.

    Die Kennung ist maschinenlesbar und wird **nicht** im Backend übersetzt:
    Ein deutscher Backendtext in der englischen Oberfläche wäre auch bei
    sauberem Parsen falsch. Die Übersetzung liegt im Dashboard.
    """

    def __init__(self, code: str, **params: str) -> None:
        super().__init__(code)
        self.code = code
        self.params = params


class IntakeService:
    """Nimmt einen rohen Feldwert entgegen und macht daraus ein Instrument."""

    def __init__(self, quotes: CachedQuoteService) -> None:
        self._quotes = quotes

    def add(self, identifier: str) -> IntakeResult:
        """Löst den Rohwert auf, beschafft den Kurs und speichert das Papier.

        Zwei Formen sind zugesagt und werden hier auseinandergehalten: die
        ISIN und ein Symbol, das seinen Handelsplatz nennt — entweder über den
        Provider-Alias (`EUNL.DE`) oder über den echten MIC (`EUNL.XETR`).
        Beide Symbolformen ergeben **dieselbe** kanonische Identität und
        denselben Abrufalias; der Alias entsteht ausschließlich in
        `provider_alias`.

        Args:
            identifier: Der rohe Feldwert, ungetrimmt.

        Returns:
            Das Ergebnis samt `created`.

        Raises:
            IntakeRejected: Der Wert führt zu keiner Identität, oder die
                Quellen kennen das Papier nicht.
            QuoteUnavailableError: Die Quelle ist nicht erreichbar. Bewusst
                **nicht** in `IntakeRejected` umgewandelt — der Aufrufer hat
                nichts falsch gemacht, und der Router macht daraus ein `502`.
        """
        value = identifier.strip().upper()
        if not value:
            raise IntakeRejected(REASON_EMPTY)

        try:
            stored = self._store(value)
        except InstrumentNotFoundError as exc:
            raise IntakeRejected(REASON_NOT_FOUND, identifier=value) from exc
        except QuoteUnavailableError as exc:
            # **Aufgenommen ist nicht bepreist** (T-31, Matrix `#9`). Eine
            # OTC-Anleihe wird erkannt — Identität, Name und Gattung stehen
            # fest —, und trotzdem liefert keine Quelle einen Preis. Das
            # Papier gehört damit in den Bestand; sein Kurs ist eine andere
            # Frage, die `GET /quote/{isin}` mit `quote_unavailable`
            # beantwortet.
            #
            # **Nur `isin_only`, und das ist der Unterschied zwischen einer
            # kaputten Quelle und einem Papier ohne Quelle.** Ein Listing hat
            # einen Handelsplatz und damit definitionsgemäß jemanden, der es
            # bepreist; liefert niemand, ist etwas ausgefallen — und eine Zeile
            # anzulegen verstellte den Blick darauf. Eine OTC-Anleihe hat
            # dagegen von vornherein keine Kursquelle, und ihr Fehlen ist der
            # Normalfall, nicht die Störung.
            #
            # Genau das sagt das Ticket: „Erfassen funktioniert mit
            # `isin_only` sofort", und der Preis kommt getrennt über die
            # Datei-Quelle. Weiter zu fassen hieße, einen Ausfall als Erfolg
            # zu verbuchen — der bestehende Test `test_eine_tote_quelle_ist_
            # ein_502_mit_kennung` hält genau diese Grenze fest.
            if exc.resolved is None or exc.resolved.kind != "isin_only":
                raise
            stored = self._quotes.store_resolved(exc.resolved)

        summary = self._quotes.get_instrument_summary(stored.instrument_id)
        if summary is None:
            # Unerreichbar, solange die Speicherung ihre eigene Zeile findet —
            # aber ein `None` hier stillschweigend als leere Summary
            # auszuliefern hieße, dem Aufrufer eine Aufnahme zu melden, die
            # nicht stattgefunden hat.
            raise QuoteUnavailableError(value)

        logger.info(
            "instrument_intake",
            identifier=value,
            ticker=summary.get("ticker"),
            mic=summary.get("mic"),
            created=stored.created,
        )
        return IntakeResult(summary, created=stored.created)

    def _store(self, value: str) -> StoredQuote:
        """Wählt den Weg — ISIN oder Symbol — und beschafft über ihn.

        Die Zerlegung selbst steht in `identity_from_input`; hier wird sie nur
        **benutzt**. Scheitert sie, sagt `input_failure` warum — mit denselben
        Kennungen, mit denen der Umzugsbericht ablehnt: Es ist dieselbe Frage
        an dasselbe Symbol, nur an anderer Stelle gestellt.
        """
        if is_isin(value):
            return self._quotes.store_by_isin(value)

        identity = identity_from_input(value)
        if identity is None:
            raise IntakeRejected(
                input_failure(value) or REASON_UNKNOWN_FORM, identifier=value
            )

        # **Über die Identität, nicht über den Alias.** Der Alias ist für die
        # US-Plätze mehrdeutig: `AAPL.XNAS` und `AAPL.XNYS` heißen beide
        # `AAPL`. Ihn hier zu bilden und damit nachzuschlagen warf genau die
        # Börse weg, die der Benutzer gerade genannt hatte — auf leerem Bestand
        # ein `500`, bei vorhandenem `AAPL/XNYS` eine Antwort mit der falschen
        # Börse. Gebildet wird er erst dort, wo die Kursquelle ihn braucht.
        return self._quotes.store_by_identity(*identity)
