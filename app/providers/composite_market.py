"""Kurs- und Historienquellen der Reihe nach fragen.

`sources.yaml` legt für `quotes` und `daily` mehrere Quellen in verbindlicher
Reihenfolge fest. Eine Anleihe ohne Online-Kurs kann so das dahinter
konfigurierte `yaml-file` erreichen.

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

from dataclasses import replace

from app.providers.base import (
    Identity,
    RawQuote,
    ResolvedInstrument,
    SourceAnswer,
    declared_name,
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

        Das Protokoll verlangt einen Namen. „composite" zu nennen hülfe
        niemandem: Wo der Name auftaucht, soll ein Betreiber eine Quelle
        wiedererkennen, die er selbst eingetragen hat.
        """
        return getattr(self._providers[0], "name", "unbekannt")


class CompositeQuoteProvider(_Chain):
    """Fragt Kursquellen der Reihe nach; der erste Kurs gewinnt."""

    def cacheable_for(self, instrument: ResolvedInstrument) -> bool:
        """Darf ein Kurs zu diesem Papier zwischengespeichert werden?"""
        return _cacheable_chain(self._providers, instrument)

    def fetch_quote(self, instrument: ResolvedInstrument) -> RawQuote | None:
        """Der erste gelieferte Kurs.

        Die Antwort trägt die Quelle, die sie **geliefert** hat. Der Name der
        Kaskade ist der der ersten Quelle und wäre hier die falsche Auskunft:
        Fällt die erste durch, stammt der Metadatenstand von der zweiten, und
        ein Betreiber suchte den Fehler sonst bei einer Quelle, die gar nichts
        geantwortet hat.

        Notiert wird das **an der Antwort**, nicht an der Kaskade. Ein Feld
        „zuletzt geliefert" am Anbieter wäre bei zwei gleichzeitigen Anfragen
        die Herkunft der jeweils anderen. Eine Quelle, die sich selbst
        beschriftet, behält ihre Angabe.

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
                if quote.source:
                    return quote
                return replace(quote, source=declared_name(provider))
        return None


def _cacheable_chain(providers: tuple, instrument: ResolvedInstrument) -> bool:
    """Darf ein Kurs zu diesem Papier zwischengespeichert werden?

    **Maßgeblich ist die erste Quelle, die dafür infrage kommt** — nicht die
    Kette als Ganzes. Eine Dateiquelle hinter einer Online-Quelle macht einen
    von der vorderen bedienten Wert nicht cachefrei; sonst fragte jede
    Seitenansicht das Netz neu und liefe in dessen Ratenlimit. Quellen ohne
    die Auskunft gelten als zwischenspeicherbar.
    """
    for provider in providers:
        serves = getattr(provider, "serves", None)
        if serves is None:
            continue
        disturbed = getattr(provider, "disturbed", None)
        # **Eine gestörte Quelle zählt, als käme sie infrage.** Ob sie das
        # Papier führt, weiß sie gerade selbst nicht — ihre Auskunft hängt an
        # dem, was nicht lesbar ist. Sie zu überspringen hieße, den
        # gespeicherten Wert als aktuellen auszugeben, obwohl niemand ihn
        # bestätigt hat.
        if not serves(instrument) and not (disturbed is not None and disturbed()):
            continue
        answer = getattr(provider, "cacheable_for", None)
        return True if answer is None else bool(answer(instrument))
    return True


class CompositeDailyCloseProvider(_Chain):
    """Fragt Historienquellen der Reihe nach; die erste Auskunft gewinnt."""

    def fetch_daily_closes(
        self,
        symbol: str,
        start: str | None = None,
        *,
        identity: Identity | None = None,
        instrument_type: str | None = None,
    ) -> SourceAnswer[list[dict]]:
        """Die erste Auskunft — **einschließlich der leeren Reihe**.

        ``[]`` heißt „nachgesehen, in diesem Zeitraum nichts" und ist damit
        eine belastbare Antwort; die nächste Quelle danach zu fragen hieße,
        eine Antwort zu suchen, die es nicht gibt — im Zweifel eine *andere*,
        weil eine zweite Quelle für denselben Zeitraum Werte führen kann, die
        die erste bewusst nicht hat.

        Ohne Wert fällt es weiter. Bleibt es dabei, hat die Kette nichts —
        und `disturbed` sagt dann, **warum**: Es genügt eine einzige gestörte
        Quelle, damit das Ausbleiben ein Ausfall ist und keine Auskunft. Hat
        dagegen jede Quelle sauber „habe ich nicht" gesagt, ist die Kette
        vollständig durchgelaufen; das ist eine Antwort, nur eine negative.

        `DailyCloseSync` unterscheidet am Wert, ob es sein Wasserzeichen
        vorrücken darf; der Router unterscheidet an `disturbed`, ob er `404`
        oder `502` schuldet.

        Args:
            symbol: Das Anbieter-Symbol.
            start: Untere Grenze, falls gesetzt.
            identity: Die Identität des Papiers; das Symbol allein nennt die
                Börse nicht immer eindeutig.
            instrument_type: Die Gattung, falls bekannt.

        Returns:
            Die erste gelieferte Reihe; sonst eine leere Antwort, deren
            `disturbed` die Störungen der ganzen Kette zusammenfasst.
        """
        disturbed = False
        for provider in self._providers:
            answer = provider.fetch_daily_closes(
                symbol, start, identity=identity, instrument_type=instrument_type
            )
            if answer.is_hit:
                return answer
            disturbed = disturbed or answer.disturbed
        return SourceAnswer(disturbed=disturbed)
