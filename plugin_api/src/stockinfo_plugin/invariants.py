"""Was sich an einer Antwort **maschinell** prüfen lässt.

Ich hatte im Entwurf zu T-27a geschrieben, Contract-Tests bewiesen „Form und
Fehlerverhalten, nicht fachliche Richtigkeit". Das war zu pessimistisch. Eine
ISIN trägt ihre eigene Prüfziffer; ein MIC hat eine festgelegte Gestalt; ein
Betrag ohne Währung ist bedeutungslos; eine Kursreihe mit zwei Einträgen für
denselben Tag ist unabhängig von jedem Marktwissen falsch. Das alles ist
prüfbar, ohne den Markt zu kennen.

**Was bleibt:** Ob ein Anbieter bei einem Papier das *gewünschte* Listing
wählt, beweist keine dieser Funktionen. Ein formal einwandfreies
``(ticker, mic)`` kann fachlich das falsche Listing sein — dagegen helfen nur
Golden Cases und jemand, der den Markt kennt.

**Warum diese Regeln im öffentlichen Paket stehen und nicht in der App.** Es
sind Aussagen über ISO 6166 und ISO 10383, nicht über StockInfo. Ein
Plugin-Autor in Toronto muss sie anwenden können, ohne die App zu
installieren — und `app/exchanges.py` bezieht sie von hier, statt sie ein
zweites Mal zu formulieren. Genau daran ist Runde 1 von T-22 gescheitert: Ein
Vertrag, der zweimal dasteht, läuft beim ersten Sonderfall auseinander.
"""

import math
import re
from datetime import date, datetime

# Eine ISIN nach ISO 6166: Ländercode, neun alphanumerische Stellen, Prüfziffer.
ISIN_PATTERN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")

# Ein MIC nach ISO 10383: genau vier Zeichen, Großbuchstaben oder Ziffern.
MIC_PATTERN = re.compile(r"[A-Z0-9]{4}")

# Eine Währung nach ISO 4217: genau drei Großbuchstaben.
CURRENCY_PATTERN = re.compile(r"[A-Z]{3}")

MINOR_UNIT_CODES = frozenset({"GBX", "ZAC", "ILA", "USX", "CNX"})
"""Kürzel für **Untereinheiten** — keine ISO-4217-Währungen.

Der Anlass ist gemessen: Die Londoner Börse notiert in Pence, und Anbieter
beschriften das als ``GBX`` oder ``GBp``. Wer das als Währung durchlässt, zeigt
einen Kurs, der um den Faktor 100 falsch ist — und weil ``GBX`` wie ein
Währungscode aussieht, fällt es niemandem auf.

Hier stehen **nur** die Schreibweisen in Großbuchstaben. ``GBp`` und ``ZAc``
scheitern schon an `CURRENCY_PATTERN`, weil ein ISO-4217-Code durchgehend groß
geschrieben ist. Sie zusätzlich in diese Menge aufzunehmen wäre gefährlich:
Verglichen würde dann groß normalisiert, und ``GBp`` normalisiert zu ``GBP`` —
das Pfund wäre plötzlich keine Währung mehr.

Eine Quelle, die in Untereinheiten liefert, **rechnet um**, bevor sie antwortet.
Das ist Arbeit für den, der die Quelle kennt, und nicht für jeden Verbraucher
danach.
"""


def isin_is_wellformed(isin: str | None) -> bool:
    """Hat der Wert die **Gestalt** einer ISIN?

    Geprüft wird mit `fullmatch`: In Python matcht ``$`` auch vor einem
    abschließenden Zeilenumbruch, und ``"US0378331005\\n"`` ginge sonst durch.

    Args:
        isin: Der zu prüfende Wert, oder ``None``.

    Returns:
        ``True`` bei zwölf Zeichen in der Form ``LL999999999P``.
    """
    return bool(isin) and bool(ISIN_PATTERN.fullmatch(isin))


def isin_check_digit_is_valid(isin: str | None) -> bool:
    """Stimmt die Prüfziffer nach ISO 6166?

    Das ist die Stelle, an der ein Contract-Test **fachlich** wird: Ein
    Tippfehler in einer von Hand gepflegten Tabelle erzeugt fast immer eine
    ISIN mit falscher Prüfziffer. Ohne diese Prüfung wandert er unbemerkt in
    die Datenbank und fällt erst auf, wenn eine Quelle nichts findet — und dann
    sieht es nach einem Ausfall der Quelle aus.

    Das Verfahren: Buchstaben werden zu zwei Ziffern (``A`` = 10 … ``Z`` = 35),
    danach Luhn über die gesamte Ziffernfolge **einschließlich** der Prüfziffer.
    Die Summe muss durch zehn teilbar sein.

    Args:
        isin: Der zu prüfende Wert, oder ``None``.

    Returns:
        ``True``, wenn die Gestalt **und** die Prüfziffer stimmen. Ein nicht
        wohlgeformter Wert ist nie gültig — sonst müsste jeder Aufrufer beides
        einzeln fragen und einer vergäße es.
    """
    if not isin_is_wellformed(isin):
        return False
    digits = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in isin  # type: ignore[union-attr]
    )
    total = 0
    # Von rechts: jede zweite Ziffer wird verdoppelt, zweistellige Ergebnisse
    # werden quersummiert (14 → 5). Die Prüfziffer selbst zählt einfach mit.
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def mic_is_wellformed(mic: str | None) -> bool:
    """Hat der Wert die Gestalt eines MIC nach ISO 10383?

    „Der Tabelle unbekannt" ist kein Gütesiegel: Ein Verzeichnis aller MICs
    führt weder diese App noch dieses Paket, und `XNAS` gehört zu den Werten,
    die eine manuelle Zuordnung setzen soll. Geprüft wird deshalb die
    Schreibweise, nicht die Mitgliedschaft in einer Liste.
    """
    return bool(mic) and bool(MIC_PATTERN.fullmatch(mic))


def is_real_mic(mic: str | None, collectors: frozenset[str] = frozenset()) -> bool:
    """Ist das ein echter MIC — oder ein interner Sammelcode?

    Ein Sammelcode fasst mehrere Börsen unter einer Kennung zusammen, weil eine
    bestimmte Quelle es so verlangt. StockInfo führt zum Beispiel ``US`` als
    OpenFIGI-Suchcode für NYSE und NASDAQ. Das ist kein MIC, und ein Feld, das
    mal echte MICs und mal solche Codes enthält, wird beim ersten Anbieter zum
    Problem, der echte MICs erwartet.

    **Die Codes selbst gehören nicht hierher.** Welche Sammelcodes es gibt,
    hängt daran, welche Quellen jemand benutzt — das weiß die App, nicht der
    Vertrag. Deshalb werden sie hereingereicht. Die Längenregel fängt das
    heutige ``US`` ohnehin ab; die Menge bleibt trotzdem im Vertrag vorgesehen,
    weil ein künftiger vierstelliger Sammelcode sonst durchginge.

    Args:
        mic: Der zu prüfende Code, oder ``None``.
        collectors: Bekannte Sammelcodes des Aufrufers.

    Returns:
        ``True``, wenn der Wert als kanonischer MIC taugt.
    """
    return mic_is_wellformed(mic) and mic not in collectors


def currency_is_valid(code: str | None) -> bool:
    """Ist das ein Währungscode nach ISO 4217 — und keine Untereinheit?

    Siehe `MINOR_UNIT_CODES`: ``GBX`` besteht die Formprüfung und ist trotzdem
    keine Währung. Der Fehler kostet den Faktor 100 und sieht dabei völlig
    harmlos aus.

    Args:
        code: Der zu prüfende Code, oder ``None``.

    Returns:
        ``True`` bei drei Großbuchstaben, die keine Untereinheit bezeichnen.
    """
    if not code or not CURRENCY_PATTERN.fullmatch(code):
        return False
    return code not in MINOR_UNIT_CODES


def is_finite_price(value: object) -> bool:
    """Ist das eine brauchbare Kurszahl — endlich und positiv?

    ``NaN`` und ``inf`` entstehen still: eine Division durch ein fehlendes
    Volumen, ein leeres Feld, das als ``float("nan")`` durchgereicht wird. Sie
    überleben jede Typprüfung, jeden Vergleich und landen in der Datenbank, wo
    sie jede spätere Rechnung anstecken. Ein Preis von ``0`` ist ebenfalls kein
    Kurs, sondern eine fehlende Angabe, die sich als Zahl ausgibt.

    ``bool`` wird ausgeschlossen, weil ``True`` in Python eine Zahl ist und
    ``isinstance(True, int)`` gilt — ein Wahrheitswert als Preis ist immer ein
    Fehler des Anbieters, nie eine Absicht.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value > 0


def has_timezone(moment: datetime | None) -> bool:
    """Trägt der Zeitpunkt eine Zeitzone?

    Ein Kurszeitpunkt ohne Zone ist unbrauchbar, sobald zwei Börsen im Spiel
    sind: ``17:30`` ist in Toronto ein anderer Augenblick als in Frankfurt, und
    welcher gemeint war, weiß danach niemand mehr. Die Angabe kostet den
    Anbieter nichts und ist hinterher nicht rekonstruierbar.
    """
    return moment is not None and moment.tzinfo is not None


def days_are_ordered(days: tuple[date, ...] | list[date]) -> bool:
    """Ist die Datumsfolge **streng** aufsteigend?

    Streng, nicht nur aufsteigend: Zwei Einträge für denselben Tag sind der
    häufigere Fehler von beiden. Sie entstehen, wenn ein Anbieter zwei
    Seiten liefert, die sich am Rand überlappen — und der Verbraucher zählt
    danach einen Tag doppelt, ohne dass irgendetwas auffällt.
    """
    return all(earlier < later for earlier, later in zip(days, days[1:]))
