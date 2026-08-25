"""Der Identitäts-Umzug des Bestands — was er täte, bevor er es tut.

Dieses Modul **rechnet vor**. Es ändert nichts. Das ist der ganze Zweck: Seit
der Entscheidung nach Runde 16 darf eine nicht auflösbare Altzeile nirgends
als halbe Identität weiterleben, und was nicht migriert werden kann, verlässt
den gültigen Bestand. Ein solcher Schritt darf dem Benutzer nicht als
Überraschung beim nächsten Start begegnen — er muss ihn vorher sehen,
mitsamt dem Preis in Kurspunkten.

`init_db()` läuft im FastAPI-Lifespan, also **bevor** die App den ersten
Request bedient (`app/main.py`). Ein UI, das erst danach erreichbar wird, kann
niemanden mehr warnen. Deshalb trennt Teil 2 das Erkennen vom Ausführen, und
die Vorschau hier ist die Hälfte, die ohne jede Schreiboperation auskommt.
"""

from dataclasses import dataclass

import structlog

from app.exchanges import is_canonical_ticker, is_real_mic, mic_for_alias

logger = structlog.get_logger()

# Stabile Ablehnungsgründe.
#
# **Kennungen, keine Sätze.** Der Text gehört ins UI und muss in DE und EN
# vorliegen; hier steht nur, *was* der Fall ist. Ein freier Text an dieser
# Stelle wäre nicht übersetzbar, nicht prüfbar und bei der ersten Umformulierung
# ein stiller Bruch für jeden, der darauf reagiert.
REASON_NO_SUFFIX = "symbol_without_exchange_suffix"
REASON_UNKNOWN_SUFFIX = "unknown_exchange_suffix"
REASON_NON_CANONICAL_TICKER = "non_canonical_ticker"

REJECTION_REASONS = frozenset(
    {REASON_NO_SUFFIX, REASON_UNKNOWN_SUFFIX, REASON_NON_CANONICAL_TICKER}
)


@dataclass(frozen=True)
class Rejection:
    """Eine Zeile, die den gültigen Bestand verlässt — samt Preis.

    `quotes` und `daily_closes` stehen **getrennt** da, weil sie verschiedene
    Dinge sind: die Intraday-Zeitreihe und die Tagesschlusskurse. Der reale
    Fall aus der Messung hängt an den Tagesschlüssen — `GOLD.SG` trägt 257
    davon —, und eine einzige Summe hätte das verwischt.
    """

    instrument_id: int
    symbol: str
    isin: str | None
    reason: str
    quotes: int
    daily_closes: int


@dataclass(frozen=True)
class Migration:
    """Eine Zeile, die ihre kanonische Identität bekommt."""

    instrument_id: int
    symbol: str
    ticker: str
    mic: str


@dataclass(frozen=True)
class MigrationPlan:
    """Was ein Lauf tun **würde** — ohne dass etwas geschehen ist.

    `unchanged` zählt die Zeilen, die ihre Identität schon tragen. Sie stehen
    hier, damit die Vorschau eine vollständige Bilanz zeigt: Ohne sie könnte
    der Benutzer nicht sehen, dass die genannten Zeilen *alle* betroffenen
    sind.
    """

    migrated: tuple[Migration, ...]
    rejected: tuple[Rejection, ...]
    unchanged: int

    @property
    def is_pending(self) -> bool:
        """Steht überhaupt etwas an?

        Eine leere Datenbank und ein bereits umgezogener Bestand sind beide
        **nicht** ausstehend — und beide müssen es sein, sonst verlangte eine
        frische Installation eine Bestätigung für nichts.
        """
        return bool(self.migrated or self.rejected)

    @property
    def lost_daily_closes(self) -> int:
        """Tagesschlusskurse, die mit den abgelehnten Zeilen verschwinden."""
        return sum(rejection.daily_closes for rejection in self.rejected)

    @property
    def lost_quotes(self) -> int:
        """Intraday-Kurspunkte, die mit den abgelehnten Zeilen verschwinden."""
        return sum(rejection.quotes for rejection in self.rejected)


def rejection_reason(symbol: str) -> str | None:
    """Warum lässt sich aus diesem Symbol keine Identität gewinnen?

    ``None`` heißt: **doch**, die Zeile migriert. Die Funktion ist damit das
    genaue Gegenstück zu `identity_of` — genau eine der beiden liefert ein
    Ergebnis, nie beide und nie keine. Gäbe sie auch für `EUNL.DE` einen Grund
    zurück, könnte ein Aufrufer eine migrierende Zeile mit einer Ablehnung
    beschriften, ohne dass der Typ ihn daran hindert.

    Die drei Gründe sind die drei Wege, auf denen die Zerlegung scheitert —
    hier aber **eigens formuliert**, nicht aus einem `(None, None)`
    zurückgeraten. Ein Grund, der nur „die andere Funktion sagt nein"
    bedeutet, sagt dem Benutzer nichts.

    Args:
        symbol: Das gespeicherte Listing-Symbol, etwa ``'VTI'``.

    Returns:
        Eine der Kennungen aus `REJECTION_REASONS`, oder ``None`` wenn die
        Zeile migriert.
    """
    if identity_of(symbol) is not None:
        return None

    if not symbol or "." not in symbol:
        # `VTI`, `AAPL`: Suffixlos notiert bei Yahoo genau ein Markt, die USA
        # — und dort führt die Tabelle nur den Sammelcode `US`. Welcher der
        # fünf Handelsplätze gemeint ist, weiß das Symbol nicht.
        return REASON_NO_SUFFIX

    ticker, _, alias = symbol.partition(".")
    if mic_for_alias(alias) is None:
        # `FOO.ZZ`: Ein Suffix, das der Katalog nicht führt. Es an einen MIC
        # zu binden, ohne die Börse aufzunehmen, hinge in der Luft.
        return REASON_UNKNOWN_SUFFIX

    # Die Börse steht fest, der Ticker nicht: `BRK-B.DE`, `RDS-A.L`. Der
    # Bindestrich ist Yahoos Zeichensetzung, nicht die der Börse, und ihn
    # umzuschreiben wäre geraten.
    return REASON_NON_CANONICAL_TICKER


def identity_of(symbol: str) -> tuple[str, str] | None:
    """Die kanonische Identität eines Altsymbols — oder ``None``.

    Bewusst eine eigene, sehr kleine Funktion statt eines Aufrufs von
    `split_symbol`: Sie liefert hier ein **Ergebnis oder nichts**, während
    `split_symbol` ein Tupel aus zwei Optionalen zurückgibt, das jeder
    Aufrufer wieder auseinandernehmen muss. Die Regel selbst ist dieselbe und
    steht weiterhin dort; geprüft wird sie gegen ausgeschriebene Erwartungen.

    Args:
        symbol: Das gespeicherte Listing-Symbol.

    Returns:
        `(ticker, mic)`, oder ``None`` wenn sich keine gewinnen lässt.
    """
    if not symbol or "." not in symbol:
        return None

    ticker, _, alias = symbol.partition(".")
    mic = mic_for_alias(alias)
    if mic is None or not is_canonical_ticker(ticker):
        return None
    return ticker, mic


def keeps_its_identity(ticker: str | None, mic: str | None) -> bool:
    """Trägt diese Zeile bereits eine **vollständige** kanonische Identität?

    Entschieden wird nach den Daten. Vollständig heißt: ein Ticker **und** ein
    echter MIC. Der Sammelcode `US` zählt nicht — er ist ein interner
    Suchcode und darf im kanonischen Feld nie stehen; eine Zeile, die ihn
    trägt, wird deshalb neu bewertet statt durchgewunken.

    Args:
        ticker: Der gespeicherte Ticker.
        mic: Der gespeicherte MIC.

    Returns:
        ``True``, wenn die Zeile so bleiben darf, wie sie ist.
    """
    return bool(ticker) and is_real_mic(mic)
