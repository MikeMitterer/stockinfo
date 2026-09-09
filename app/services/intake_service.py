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

from collections.abc import Callable
from dataclasses import dataclass

import structlog
from stockinfo_plugin import Identity, ListedIdentity

from app.exchanges import EXCHANGES, REASON_NO_SUFFIX, identity_from_input, input_failure, is_isin
from app.models import IntakeConfirmation, ListedIdentityOut, PreferredExchange, QuoteResponse
from app.services.quote_cache import CachedQuoteService, StoredQuote
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteUnavailableError,
    UnresolvableSymbolError,
)

logger = structlog.get_logger()

# Der Rohwert ist leer oder nur Leerraum — kein Ticker, keine ISIN, nichts.
REASON_EMPTY = "identifier_empty"

# Die Form passt zu keinem der beiden Wege: weder ISIN noch zerlegbares Symbol.
# Die drei genaueren Symbolgründe kommen aus `rejection_reason`.
REASON_UNKNOWN_FORM = "identifier_unknown_form"

# Form und Zerlegung stimmen, aber die Quellen kennen das Papier nicht.
REASON_NOT_FOUND = "instrument_not_found"

# Der Handelsplatz ist erkannt, aber das aktive Profil bietet dafür keine Kurse.
REASON_NOT_COVERED = "exchange_not_covered"


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


class ExchangeConfirmationRequired(Exception):
    """Unterbricht die Aufnahme vor Speicherung für eine bewusste Entscheidung."""

    def __init__(self, confirmation: IntakeConfirmation) -> None:
        super().__init__("exchange_confirmation_required")
        self.confirmation = confirmation


class IntakeService:
    """Nimmt einen rohen Feldwert entgegen und macht daraus ein Instrument."""

    def __init__(
        self, quotes: CachedQuoteService, covered_mics: frozenset[str],
        preferred_mic: str | None = None
    ) -> None:
        self._quotes = quotes
        self._covered_mics = covered_mics
        self._preferred_mic = preferred_mic

    def add(
        self, identifier: str, *, check_exchange: bool = False,
        confirmed_listing: ListedIdentityOut | None = None,
    ) -> IntakeResult:
        """Löst den Rohwert auf, beschafft den Kurs und speichert das Papier.

        Unterstützt sind ISIN, quellenbestimmte Paare und ein Symbol, das
        seinen Handelsplatz nennt — entweder über den
        Provider-Alias (`EUNL.DE`) oder über den echten MIC (`EUNL.XETR`).
        Beide Symbolformen ergeben **dieselbe** kanonische Identität und
        denselben Abrufalias; der Alias entsteht ausschließlich in
        `provider_alias`.

        Args:
            identifier: Der rohe Feldwert, ungetrimmt.
            check_exchange: Bei neuer Börsenabweichung vor Speicherung unterbrechen.
            confirmed_listing: Zuvor angezeigte und vom Aufrufer bestätigte Identität.

        Returns:
            Das Ergebnis samt `created`.

        Raises:
            ExchangeConfirmationRequired: Neues Listing benötigt eine Entscheidung.
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
            before_store = None
            if check_exchange:
                def before_store(quote: QuoteResponse) -> None:
                    self._check_exchange(quote, confirmed_listing)
            stored = self._store(value, before_store)
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

    def _store(
        self, value: str, before_store: Callable[[QuoteResponse], None] | None,
    ) -> StoredQuote:
        """Wählt den Weg — ISIN oder Symbol — und beschafft über ihn.

        Die Zerlegung selbst steht in `identity_from_input`; hier wird sie nur
        **benutzt**. Scheitert sie, sagt `input_failure` warum — mit denselben
        Kennungen, mit denen der Umzugsbericht ablehnt: Es ist dieselbe Frage
        an dasselbe Symbol, nur an anderer Stelle gestellt.
        """
        options = {"before_store": before_store} if before_store is not None else {}
        if is_isin(value):
            return self._quotes.store_by_isin(
                value, check_identity=self._check_identity, **options
            )

        identity = identity_from_input(value)
        if identity is None:
            failure = input_failure(value) or REASON_UNKNOWN_FORM
            if failure == REASON_NO_SUFFIX:
                def check_unlisted(resolved: Identity | None) -> None:
                    if isinstance(resolved, ListedIdentity):
                        raise IntakeRejected(REASON_NO_SUFFIX, identifier=value)

                try:
                    return self._quotes.store_by_symbol(
                        value, check_identity=check_unlisted, **options
                    )
                except UnresolvableSymbolError as exc:
                    raise IntakeRejected(failure, identifier=value) from exc
            raise IntakeRejected(
                failure, identifier=value
            )

        self._check_identity(ListedIdentity(ticker=identity[0], mic=identity[1]))

        # **Über die Identität, nicht über den Alias.** Der Alias ist für die
        # US-Plätze mehrdeutig: `AAPL.XNAS` und `AAPL.XNYS` heißen beide
        # `AAPL`. Ihn hier zu bilden und damit nachzuschlagen warf genau die
        # Börse weg, die der Benutzer gerade genannt hatte — auf leerem Bestand
        # ein `500`, bei vorhandenem `AAPL/XNYS` eine Antwort mit der falschen
        # Börse. Gebildet wird er erst dort, wo die Kursquelle ihn braucht.
        return self._quotes.store_by_identity(*identity, **options)

    def _check_identity(self, identity: Identity | None) -> None:
        """Nur Listings benötigen eine Kursquelle für ihren Handelsplatz."""
        if (
            isinstance(identity, ListedIdentity)
            and identity.mic not in self._covered_mics
        ):
            raise IntakeRejected(REASON_NOT_COVERED, mic=identity.mic)


    def _check_exchange(self, quote: QuoteResponse, confirmed: ListedIdentityOut | None) -> None:
        """Vergleicht das neue Listing vor Speicherung mit der bekannten Präferenz."""
        identity = quote.identity
        preferred = EXCHANGES.get(self._preferred_mic)
        if not isinstance(identity, ListedIdentityOut) or preferred is None:
            return
        if identity == confirmed or (confirmed is None and identity.mic == self._preferred_mic):
            return
        actual = EXCHANGES.get(identity.mic)
        raise ExchangeConfirmationRequired(IntakeConfirmation(
            identity=identity, name=quote.name, currency=quote.currency,
            exchange=actual.name if actual else identity.mic,
            preferred=PreferredExchange(mic=self._preferred_mic, name=preferred.name, currency=preferred.currency),
        ))
