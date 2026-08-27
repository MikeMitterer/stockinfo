"""Die Rollen, die ein Plugin ausfüllen kann.

Innerhalb der App sind die Verträge ``Protocol`` — strukturelle Typisierung,
niemand muss erben. Nach außen sind es **Basisklassen**, und das aus drei
Gründen: Sie liefern brauchbare Vorgaben, sie versammeln die Dokumentation des
Vertrags an einer Stelle, und die Registry kann beim Laden mit ``isinstance``
prüfen, statt auf Zuruf zu vertrauen.

Ein Plugin erfüllt eine Rolle oder mehrere. Die kommerziellen Anbieter decken
üblicherweise alle ab — Auflösung, Kurs, Historie, Devisen aus einer Hand.
"""

from typing import Any

from stockinfo_plugin.types import (
    API_VERSION,
    Cost,
    DailyRequest,
    DailyResult,
    FieldSpec,
    FxRequest,
    FxResult,
    QuoteRequest,
    QuoteResult,
    Reading,
    ResolveRequest,
    Resolution,
)


class Source:
    """Gemeinsame Grundlage aller Quellen.

    Eine Unterklasse setzt mindestens `name`. Alles andere hat Vorgaben, die
    für den einfachen Fall stimmen.
    """

    name: str = ""
    """Eindeutiger Kurzname, taucht in Konfiguration und Protokoll auf."""

    api_version: int = API_VERSION
    """Vertragsversion, gegen die dieses Plugin gebaut wurde."""

    cost: Cost = "free"
    """Was eine Anfrage kostet — **Information, keine Sortierregel**.

    Die Reihenfolge der Kette bestimmt ausschließlich `sources.yaml`. Dieser
    Wert dient der Anzeige und der Warnung („diese Kette fragt eine
    kostenpflichtige Quelle zuerst"), damit eine teure Quelle nicht unbemerkt
    vor einer kostenlosen steht.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: Der eigene Abschnitt aus der Quellen-Konfiguration.

        Die App reicht **nur** diesen Abschnitt herein — nicht ihre
        Einstellungen, nicht die Datenbank, nicht andere Quellen. Das ist eine
        Vertrags-, **keine Sicherheitsgrenze**: Fremder Python-Code kann
        Umgebungsvariablen und Dateisystem ohnehin lesen. Gemeint ist, dass
        nichts davon als stabile Schnittstelle zugesagt wird — wer sich an
        Interna bindet, bricht beim nächsten Umbau.

        Wer echte Isolation braucht, findet sie hier nicht; siehe „Was bewusst
        nicht gebaut wird" im Design.
        """
        self._config = config or {}

    def is_configured(self) -> bool:
        """Ist diese Quelle einsatzbereit?

        Der Ort für „API-Key vorhanden?", „Datei existiert?", „Kontingent
        übrig?". Eine Quelle, die ``False`` meldet, wird gar nicht erst in die
        Kette aufgenommen — damit erübrigt sich jede Fallunterscheidung in der
        Verdrahtung der App.

        Returns:
            ``True``, wenn die Quelle arbeiten kann.
        """
        return True

    def close(self) -> None:
        """Aufräumen beim Herunterfahren. Vorgabe: nichts zu tun."""


class Resolver(Source):
    """Rolle: findet zu einem Papier das Listing an einer Börse."""

    def handles(self, request: ResolveRequest) -> bool:
        """Ist diese Quelle für die Anfrage zuständig?

        Wird **vor** `resolve` gefragt, damit eine unzuständige Quelle keine
        Anfrage und kein Kontingent kostet. Der Zuständigkeitsbereich ist
        typischerweise ein Länderpräfix der ISIN, eine Menge von Börsen oder
        eine Gattung.

        Args:
            request: Die zu beantwortende Anfrage.

        Returns:
            ``True``, wenn `resolve` sinnvoll aufgerufen werden kann.
        """
        return True

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Beantwortet die Anfrage.

        **Wirft nicht.** Jeder Fehler wird zu `Unavailable`; die Kette soll
        entscheiden, nicht abstürzen. Wer hier eine Ausnahme durchlässt,
        besteht den Contract-Test nicht.

        Args:
            request: Die zu beantwortende Anfrage.

        Returns:
            `Resolved` bei Treffer, sonst `NotResponsible`, `NotFound` oder
            `Unavailable` — der Unterschied entscheidet über 404 gegen 502 und
            darüber, ob die Kette weitersucht.
        """
        raise NotImplementedError


class MetadataSource(Source):
    """Rolle: ergänzt Kennzahlen zu einem bekannten Papier (TER, Anbieter, …).

    Zwei Dinge unterscheiden diese Rolle vom Resolver, und beide folgen aus der
    Praxis:

    **Die Feldmenge ist variabel.** Eine Quelle liefert acht Kennzahlen, die
    nächste nur den Anbieter. `fetch` gibt deshalb eine Liste zurück, keinen
    festen Datensatz — was nicht drinsteht, wurde nicht geliefert, und das ist
    etwas anderes als „ist leer".

    **Jeder Wert trägt seine Einheit.** Gemessen an zwei Quellen für dieselbe
    Kostenquote: ``0.19`` bei der einen, ``0.0003`` bei der anderen, beide
    nennen es „TER". Ohne Einheit am Wert ist die Zahl bedeutungslos.

    Was eine Quelle liefern kann, deklariert sie vorab in `FIELDS`. Die App
    weiß dadurch, wie sie umrechnet, prüft und beschriftet — auch bei Feldern,
    die sie selbst nicht kennt.
    """

    FIELDS: tuple[FieldSpec, ...] = ()
    """Welche Felder diese Quelle liefern kann. Was hier fehlt, wird verworfen."""

    def handles(self, request: ResolveRequest) -> bool:
        """Führt diese Quelle das Papier? Siehe `Resolver.handles`.

        Der übliche Zuständigkeitsbereich sind Domizil oder Gattung: Eine
        Datenbank europäischer Fonds hat zu einem US-Papier nichts — und das
        ist eine andere Aussage als „gerade nicht erreichbar".
        """
        return True

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Holt die Kennzahlen.

        **Wirft nicht.** Jeder Fehler wird zu ``None``.

        Args:
            request: Das Papier, zu dem Kennzahlen gesucht werden.

        Returns:
            Die gefundenen Werte. Eine **leere Liste** heißt „nachgesehen,
            nichts gefunden" — eine gültige Aussage, die einen gespeicherten
            Stand ersetzen darf. ``None`` heißt „konnte nicht nachsehen" und
            schützt ihn.

            Der Unterschied ist nicht kosmetisch: Ein einzelner Ausfall hat in
            dieser App schon einmal einen gepflegten Datenbestand mit ``NULL``
            überschrieben. Wer unsicher ist, gibt ``None`` zurück.
        """
        raise NotImplementedError

    def declared(self, name: str) -> FieldSpec | None:
        """Sucht die Deklaration eines Feldes.

        Args:
            name: Feldname.

        Returns:
            Die `FieldSpec` oder ``None``, wenn das Feld nicht deklariert ist.
        """
        return next((spec for spec in self.FIELDS if spec.name == name), None)


class QuoteSource(Source):
    """Rolle: liefert den aktuellen Kurs zu einem Listing.

    Die Anfrage nennt **Ticker und MIC**, nicht ein fertiges Anbieter-Symbol.
    Wie daraus ``EUNL.DE`` oder ``EUNL.XETRA`` wird, weiß nur diese Quelle —
    und muss keine andere wissen.
    """

    def handles(self, request: QuoteRequest) -> bool:
        """Führt diese Quelle dieses Listing? Siehe `Resolver.handles`.

        Der übliche Zuständigkeitsbereich ist eine Menge von Börsen: Ein
        Anbieter für den nordamerikanischen Markt hat zu ``XWBO`` nichts — und
        das ist eine andere Aussage als „gerade nicht erreichbar".
        """
        return True

    def fetch_quote(self, request: QuoteRequest) -> QuoteResult:
        """Holt den aktuellen Kurs.

        **Wirft nicht.** Jeder Fehler wird zu `Unavailable`.

        **Und rät nicht.** Wo der Anbieter keine Währung mitliefert, ist die
        Antwort `Unavailable`, nicht ein Kurs mit geratener Währung. Ein Kurs
        ohne Währung ist eine Zahl, und als solche wurde er in dieser App schon
        einmal mit einem Betrag in einer anderen Währung verrechnet.

        Args:
            request: Ticker, MIC und optional die ISIN.

        Returns:
            `Quote` bei Treffer, sonst `NotResponsible`, `NotFound` oder
            `Unavailable`.
        """
        raise NotImplementedError


class DailyCloseSource(Source):
    """Rolle: liefert Tages-Schlusskurse zu einem Listing."""

    def handles(self, request: DailyRequest) -> bool:
        """Führt diese Quelle die Historie dieses Listings?"""
        return True

    def fetch_daily(self, request: DailyRequest) -> DailyResult:
        """Holt die Schlusskurse im angefragten Zeitraum.

        **Wirft nicht.** Jeder Fehler wird zu `Unavailable`.

        Eine `DailySeries` mit **leerer** ``bars``-Folge ist eine gültige
        Antwort: „nachgesehen, in diesem Zeitraum lag nichts". Sie ist etwas
        anderes als `NotFound` („dieses Papier kenne ich nicht") und etwas
        anderes als `Unavailable` („konnte nicht nachsehen"). Der Unterschied
        entscheidet, ob ein gespeicherter Stand überschrieben werden darf.

        Args:
            request: Ticker, MIC und der gewünschte Zeitraum.

        Returns:
            `DailySeries` mit streng aufsteigenden, doppelfreien Tagen, sonst
            `NotResponsible`, `NotFound` oder `Unavailable`.
        """
        raise NotImplementedError


class FxSource(Source):
    """Rolle: liefert Wechselkurse zwischen zwei Währungen."""

    def handles(self, request: FxRequest) -> bool:
        """Kennt diese Quelle dieses Währungspaar?"""
        return True

    def fetch_rate(self, request: FxRequest) -> FxResult:
        """Holt den Wechselkurs.

        **Wirft nicht.** Jeder Fehler wird zu `Unavailable`.

        Bei ``base == quote`` ist die Antwort **genau** ``1.0``. Das ist keine
        Formalie: Eine Quelle, die dafür ``0.9998`` meldet, rechnet über einen
        Umweg — und derselbe Umweg verfälscht dann jedes andere Paar auch, nur
        unsichtbar.

        Args:
            request: Ausgangs- und Zielwährung.

        Returns:
            `FxRate` bei Treffer, sonst `NotResponsible`, `NotFound` oder
            `Unavailable`.
        """
        raise NotImplementedError
