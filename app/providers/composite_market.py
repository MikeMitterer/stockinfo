"""Kurs- und Historienquellen der Reihe nach fragen.

`sources.yaml` erlaubt für `quotes` und `daily` seit T-22 mehrere Quellen.
Ausgeführt wurde davon nur die erste: Eine Anleihe ohne Online-Kurs erreichte
das dahinter konfigurierte `yaml-file` nie, und der Benutzer sah ein Papier
ohne Preis, obwohl der Wert in seiner Datei stand.

**Zwei schmale Klassen statt einer allgemeinen Kette.** Die beiden Rollen
sehen sich ähnlich und unterscheiden sich an genau der Stelle, auf die es
ankommt: Für einen Kurs ist ein Ergebnis ein `RawQuote`; für eine Tagesreihe
ist auch die **leere Liste** eines — „nachgesehen, in diesem Zeitraum nichts".
Eine gemeinsame Kette müsste diesen Unterschied als Parameter tragen, und ein
Parameter, der die Bedeutung eines Rückgabewerts umschaltet, ist genau die
Sorte Abstraktion, die man beim Lesen zweimal prüfen muss.

Die Auflösung und die Metadatenkaskade haben ihre eigenen Composites; sie
bleiben unberührt. Reihenfolge, Nebenläufigkeit, Wiederholungen und
Zeitgrenzen sind ausdrücklich nicht Gegenstand: Gefragt wird der Reihe nach,
und die erste Antwort gilt.
"""

from app.providers.base import (
    Identity,
    RawQuote,
    ResolvedInstrument,
)


class _Chain:
    """Was beide Kaskaden teilen: die geordneten Quellen und ihr Name."""

    def __init__(self, *providers: object) -> None:
        """
        Args:
            *providers: Die Quellen in der Reihenfolge der Konfiguration.

        Raises:
            ValueError: Ohne Quellen. Eine leere Kette antwortet nie, und
                stillschweigend ``None`` zu liefern hieße, einen
                Konfigurationsfehler als Ausfall auszugeben — der Betreiber
                suchte beim Anbieter nach einer Ursache, die in seiner
                `sources.yaml` steht.
        """
        if not providers:
            raise ValueError("eine Kaskade ohne Quellen kann nichts beantworten")
        self._providers = providers

    @property
    def name(self) -> str:
        """Der Name der **ersten** Quelle.

        Das Protokoll verlangt einen Namen seit T-37. „composite" zu nennen
        hülfe niemandem: Wo der Name auftaucht, soll ein Betreiber eine Quelle
        wiedererkennen, die er selbst eingetragen hat. Welche Quelle eine
        einzelne Antwort geliefert hat, steht an der Antwort — nicht an der
        Kette.
        """
        return getattr(self._providers[0], "name", "unbekannt")


class CompositeQuoteProvider(_Chain):
    """Fragt Kursquellen der Reihe nach; der erste Kurs gewinnt."""

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        """Der erste gelieferte Kurs.

        Args:
            instrument: Das aufgelöste Papier.

        Returns:
            Der erste Kurs, oder ``None`` wenn keine Quelle einen hatte. Der
            Aufrufer sieht damit denselben Fall wie bei einer einzelnen
            Quelle, und sein Rückfall auf den gespeicherten Stand greift
            unverändert.
        """
        for provider in self._providers:
            quote = provider.fetch_quote(instrument)
            if quote is not None:
                return quote
        return None


class CompositeDailyCloseProvider(_Chain):
    """Fragt Historienquellen der Reihe nach; die erste Auskunft gewinnt."""

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        identity: Identity | None = None,
        instrument_type: str | None = None,
    ) -> list[dict] | None:
        """Die erste Auskunft — **einschließlich der leeren Reihe**.

        ``[]`` heißt „nachgesehen, in diesem Zeitraum nichts" und ist damit
        eine belastbare Antwort; die nächste Quelle danach zu fragen hieße,
        eine Antwort zu suchen, die es nicht gibt — im Zweifel eine *andere*,
        weil eine zweite Quelle für denselben Zeitraum Werte führen kann, die
        die erste bewusst nicht hat.

        ``None`` heißt „konnte nicht nachsehen" und fällt weiter. Bleibt es
        dabei, ist auch die Gesamtantwort ``None``: `DailyCloseSync`
        unterscheidet daran, ob es sein Wasserzeichen vorrücken darf.

        Args:
            symbol: Das Anbieter-Symbol.
            start: Untere Grenze, falls gesetzt.
            identity: Die Identität des Papiers — seit T-23 nötig, weil das
                Symbol allein die Börse nicht eindeutig nennt.
            instrument_type: Die Gattung, falls bekannt.

        Returns:
            Die erste gelieferte Reihe, oder ``None`` nach dem Gesamtausfall.
        """
        for provider in self._providers:
            closes = provider.fetch_daily_closes(
                symbol, start, identity=identity, instrument_type=instrument_type
            )
            if closes is not None:
                return closes
        return None
