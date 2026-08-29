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

_NON_CURRENCY_CODES = frozenset({"XXX", "XTS"})
"""Codes, die ISO 4217 vergibt, um **keine** Währung zu bezeichnen.

``XXX`` heißt wörtlich „keine Währung", ``XTS`` ist für Tests reserviert. Beide
stehen in der Norm und müssen trotzdem abgewiesen werden — sie sind genau der
Platzhalter, den ein Anbieter einsetzt, wenn er nichts weiß. Sie durchzulassen
hieße, den Zweck der Prüfung an ihrer formal korrektesten Stelle aufzugeben.
"""

ISO_4217_AS_OF = "2026-01-01"
"""Stand der Liste unten — das `Pblshd`-Datum der offiziellen List One.

Steht in jeder Meldung über einen unbekannten Code, sonst weiß der Autor nicht,
ob sein Code neu ist oder falsch.

**Es ist ausdrücklich das Datum der Quelle, nicht das der letzten Durchsicht.**
Vorher stand hier ein selbstgesetztes ``"2026-08"``, während die Liste zwei
zurückgezogene Codes enthielt — die Angabe behauptete eine Aktualität, die
niemand hergestellt hatte, und genau deshalb hat sie niemandem gefehlt. Ein
Datum, das von der Quelle stammt, lässt sich gegen sie prüfen.
"""

ISO_4217 = frozenset(
    """
    AED AFN ALL AMD AOA ARS AUD AWG AZN
    BAM BBD BDT BHD BIF BMD BND BOB BOV BRL BSD BTN BWP BYN BZD
    CAD CDF CHE CHF CHW CLF CLP CNY COP COU CRC CUP CVE CZK
    DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP
    GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF
    IDR ILS INR IQD IRR ISK JMD JOD JPY
    KES KGS KHR KMF KPW KRW KWD KYD KZT
    LAK LBP LKR LRD LSL LYD
    MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN
    NAD NGN NIO NOK NPR NZD OMR
    PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF
    SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL
    THB TJS TMT TND TOP TRY TTD TWD TZS
    UAH UGX USD USN UYI UYU UYW UZS
    VED VES VND VUV WST
    XAD XAF XAG XAU XBA XBB XBC XBD XCD XCG XDR XOF XPD XPF XPT XSU XUA
    YER ZAR ZMW ZWG
    """.split()
)
"""Die vergebenen alphabetischen Codes nach ISO 4217.

**Warum eine Liste und nicht nur eine Formprüfung.** ``ZZZ`` hat die Gestalt
eines Codes und ist keiner; genau so sieht das Feld aus, wenn ein Anbieter
nichts hat und trotzdem etwas hinschreibt. Ohne Liste wäre die zugesagte
„gültige Währung" eine reine Formaussage — der Befund aus Runde 1.

`XXX` und `XTS` fehlen mit Absicht (siehe `_NON_CURRENCY_CODES`), die
Metallcodes `XAU`/`XAG`/`XPT`/`XPD` stehen drin: Sie sind vergeben, und einen
vergebenen Code abzuweisen ist der schlimmere Fehler.

**Sie ist die Kopie einer fremden Liste, und Kopien veralten.** Runde 2 hat das
belegt: Bei behauptetem Stand ``2026-08`` enthielt sie noch `BGN`, obwohl
Bulgarien zum 1. Januar 2026 den Euro eingeführt hat. Der Abgleich gegen die
offizielle List One hat danach zwei weitere Abweichungen derselben Art
gezeigt — `ANG` war seit dem 30. Juni 2025 zurückgezogen (abgelöst durch
`XCG`), und `XAD` fehlte, obwohl es vergeben ist. Genannt worden war nur `BGN`;
gefunden hat die anderen beiden erst der vollständige Vergleich.

Daraus die Pflege-Regel: **Ein neuer Stand wird gegen die List One als Ganzes
abgeglichen, nicht am einzelnen gemeldeten Code repariert.**

    curl -s https://www.six-group.com/dam/download/financial-information/\\
    data-center/iso-currrency/lists/list-one.xml

`ISO_4217_AS_OF` übernimmt danach das `Pblshd`-Datum der Datei, und
`test_der_gemeldete_stand_und_die_liste_gehoeren_zusammen` schlägt an, wenn nur
eines von beidem angefasst wurde.

Bleibt die Liste trotzdem zurück, meldet `currency_problem` einen neu
vergebenen Code mit `ISO_4217_AS_OF`, statt ihn stumm abzulehnen.
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


def currency_is_wellformed(code: str | None) -> bool:
    """Hat der Wert die **Gestalt** eines ISO-4217-Codes?

    Drei Großbuchstaben, mehr nicht. Das ist ausdrücklich **keine** Aussage
    darüber, ob der Code vergeben ist — dafür `currency_is_valid`. Die Trennung
    steht hier, weil die schwächere Prüfung eine ehrliche Verwendung hat: Wer
    einen Code nur weiterreicht, statt mit ihm zu rechnen, braucht die
    Vergabeliste nicht.
    """
    return bool(code) and bool(CURRENCY_PATTERN.fullmatch(code))


def currency_problem(code: str | None) -> str:
    """Was mit diesem Währungscode nicht stimmt — leer, wenn er taugt.

    Eine Funktion und nicht drei Prüfungen in jedem Vertrag: Die Unterscheidung
    zwischen „sieht nicht aus wie ein Code", „ist eine Untereinheit" und „ist
    nicht vergeben" ist genau das, was der Meldung ihren Wert gibt. In drei
    Verträgen nachgebaut liefe sie beim ersten Sonderfall auseinander.

    Args:
        code: Der zu prüfende Code, oder ``None``.

    Returns:
        Die Beanstandung als Satz, oder ``""``.
    """
    if not currency_is_wellformed(code):
        return f"{code!r} hat nicht die Gestalt eines ISO-4217-Codes (drei Großbuchstaben)"
    if code in MINOR_UNIT_CODES:
        return (
            f"{code!r} bezeichnet eine Untereinheit, keine Währung — wer in "
            "Pence oder Cent notiert, rechnet vor der Antwort um"
        )
    if code in _NON_CURRENCY_CODES:
        return (
            f"{code!r} ist nach ISO 4217 ausdrücklich keine Währung, sondern "
            "ein Platzhalter beziehungsweise ein Testcode"
        )
    if code not in ISO_4217:
        return (
            f"{code!r} ist kein vergebener ISO-4217-Code. Falls er neu vergeben "
            f"wurde, gehört er in ISO_4217 ({ISO_4217_AS_OF})"
        )
    return ""


def currency_is_valid(code: str | None) -> bool:
    """Ist das ein **vergebener** Währungscode nach ISO 4217?

    **Verschärft nach Runde 1.** Vorher prüfte diese Funktion nur die Gestalt,
    hieß aber „valid" — und ``ZZZ`` kam durch. Das ist der Fehler, den sie
    verhindern soll: Ein Anbieter, der Unsinn in das Währungsfeld schreibt,
    sieht mit einer reinen Formprüfung genauso aus wie einer, der es richtig
    macht.

    Die Kehrseite ist ehrlich zu nennen: Wird ein Code **neu** vergeben, weist
    diese Funktion ihn ab, bis `ISO_4217` nachgezogen ist. Das ist ein lauter
    Fehlschlag in einem Test mit einer Meldung, die genau das sagt — und damit
    das kleinere Übel gegenüber einem stillen Datenfehler in der Datenbank.

    Args:
        code: Der zu prüfende Code, oder ``None``.

    Returns:
        ``True``, wenn der Code vergeben und keine Untereinheit ist.
    """
    return currency_problem(code) == ""


def is_finite_number(value: object) -> bool:
    """Ist das überhaupt eine Zahl, mit der sich rechnen und vergleichen lässt?

    ``NaN`` und ``inf`` entstehen still: eine Division durch ein fehlendes
    Volumen, ein leeres Feld, das als ``float("nan")`` durchgereicht wird. Sie
    überleben jede Typprüfung und jeden Vergleich — ``NaN`` ist sogar mit sich
    selbst nicht gleich — und stecken danach jede Rechnung an.

    ``bool`` wird ausgeschlossen, weil ``True`` in Python eine Zahl ist und
    ``isinstance(True, int)`` gilt. Ein Wahrheitswert an einer Zahlenstelle ist
    immer ein Fehler, nie eine Absicht.

    **Warum das eine eigene Funktion ist und nicht in `is_finite_price`
    steckt:** Ein Kurs muss zusätzlich positiv sein, eine Bereichsgrenze nicht
    — ``(-10, 10)`` ist ein völlig richtiger Bereich für eine Tagesveränderung.
    Die gemeinsame Hälfte steht hier, damit die beiden Aufrufer sie nicht
    getrennt pflegen und beim ersten Sonderfall auseinanderlaufen.

    **Integer werden nicht durch `math.isfinite` geschickt** — Befund aus
    Runde 3. Ein Python-Integer ist beliebig groß, `math.isfinite` erwartet
    aber einen `float` und wandelt vorher um; bei ``10**10000`` scheitert
    genau diese Umwandlung mit `OverflowError`. Ausgerechnet die Prüfung, die
    unbrauchbare Zahlen abfangen soll, flog also bei einer **gültigen** Zahl —
    und riss den Lauf mit, den sie schützen sollte. Nach dem Typ-Guard oben ist
    ein Integer immer endlich; die Frage stellt sich nur bei `float`.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int):
        return True
    return math.isfinite(value)


def is_finite_price(value: object) -> bool:
    """Ist das eine brauchbare Kurszahl — endlich und positiv?

    Zur Endlichkeit siehe `is_finite_number`. Ein Preis von ``0`` ist darüber
    hinaus kein Kurs, sondern eine fehlende Angabe, die sich als Zahl ausgibt.
    """
    return is_finite_number(value) and value > 0  # type: ignore[operator]


def has_timezone(moment: datetime | None) -> bool:
    """Trägt der Zeitpunkt einen **wirksamen** Zeitzonenbezug?

    Ein Kurszeitpunkt ohne Zone ist unbrauchbar, sobald zwei Börsen im Spiel
    sind: ``17:30`` ist in Toronto ein anderer Augenblick als in Frankfurt, und
    welcher gemeint war, weiß danach niemand mehr. Die Angabe kostet den
    Anbieter nichts und ist hinterher nicht rekonstruierbar.

    **Geprüft wird `utcoffset()`, nicht `tzinfo`** — das war ein Befund aus
    Runde 1 und er trifft genau die Lücke, die man ohne Nachdenken lässt: Eine
    `tzinfo`-Instanz, deren `utcoffset()` ``None`` liefert, ist erlaubt, und
    Python selbst behandelt einen solchen Zeitpunkt als **naiv** — er lässt
    sich nicht mit einem echten aware-Zeitpunkt vergleichen und wirft dabei
    `TypeError`. Ein Test auf `tzinfo is not None` hätte also gerade den Fall
    durchgelassen, der später beim ersten Vergleich abstürzt.
    """
    return moment is not None and moment.utcoffset() is not None


def days_are_ordered(days: tuple[date, ...] | list[date]) -> bool:
    """Ist die Datumsfolge **streng** aufsteigend?

    Streng, nicht nur aufsteigend: Zwei Einträge für denselben Tag sind der
    häufigere Fehler von beiden. Sie entstehen, wenn ein Anbieter zwei
    Seiten liefert, die sich am Rand überlappen — und der Verbraucher zählt
    danach einen Tag doppelt, ohne dass irgendetwas auffällt.
    """
    return all(earlier < later for earlier, later in zip(days, days[1:]))


def identity_problem(
    identity: object, collectors: frozenset[str] = frozenset()
) -> str:
    """Was mit dieser Identität nicht stimmt — leer, wenn sie taugt.

    Je Form etwas anderes, und genau darum steht es hier und nicht in jedem
    Vertrag noch einmal: Ein Ticker gehört zur `listed`-Form und sagt bei einem
    Währungspaar nichts; eine `pair`-Identität braucht statt der Börse eine
    Quote-Währung, weil *sie* die Frage „wo gilt dieser Preis?" beantwortet.

    Die Prüfung ist bewusst **strukturell**. Ob ``XTSE`` das *gewünschte*
    Listing ist oder ``BTC`` als Basiswert existiert, weiß sie nicht — dafür
    braucht es Marktwissen, und das steht nicht im Vertrag.

    Args:
        identity: Eine `ListedIdentity`, `PairIdentity` oder
            `IsinOnlyIdentity`.
        collectors: Interne Sammelcodes, die kein echter Handelsplatz sind.

    Returns:
        Die Beanstandung als Satz, oder ``""``.
    """
    # Lokaler Import: `types` bezieht seine Regeln von hier, und ein
    # Modulimport in die andere Richtung schlösse den Kreis.
    from stockinfo_plugin.types import (
        IsinOnlyIdentity,
        ListedIdentity,
        PairIdentity,
    )

    if isinstance(identity, ListedIdentity):
        if not identity.ticker or identity.ticker.strip() != identity.ticker:
            return f"ticker fehlt oder trägt Leerzeichen: {identity.ticker!r}"
        if not is_real_mic(identity.mic, collectors):
            return (
                f"mic {identity.mic!r} ist kein MIC nach ISO 10383 — vier "
                "Zeichen, Großbuchstaben oder Ziffern, und kein interner "
                "Sammelcode. Ohne echte Börse ist der Ticker mehrdeutig"
            )
        if identity.isin is not None and not isin_check_digit_is_valid(identity.isin):
            return f"isin {identity.isin!r} hat keine gültige Prüfziffer"
        return ""

    if isinstance(identity, PairIdentity):
        if not identity.base or identity.base.strip() != identity.base:
            return f"base fehlt oder trägt Leerzeichen: {identity.base!r}"
        problem = currency_problem(identity.quote_currency)
        if problem:
            return f"quote_currency {problem}"
        return ""

    if isinstance(identity, IsinOnlyIdentity):
        if not isin_check_digit_is_valid(identity.isin):
            return (
                f"isin {identity.isin!r} hat keine gültige Prüfziffer — bei "
                "dieser Form ist sie die ganze Identität"
            )
        return ""

    return (
        f"{type(identity).__name__} ist keine Identitätsform des Vertrags "
        "(listed, pair, isin_only)"
    )


def resolution_problem(resolved: object) -> str:
    """Was einer Auflösung zu einer **brauchbaren** Antwort fehlt (T-38).

    `identity_problem` beantwortet, ob das Papier *identifiziert* ist. Diese
    Funktion beantwortet die zweite Hälfte: ob die Antwort auch **trägt**, was
    ein Host von ihr braucht.

    **Warum das nicht der Typ allein erledigt.** Seit T-38 haben ``name`` und
    ``instrument_type`` keinen Vorgabewert mehr — damit lassen sie sich nicht
    mehr weglassen. Füllen mit nichts geht weiter: ``name=""`` und
    ``name="   "`` sind gültige Zeichenketten und genau so nützlich wie
    ``None``. Der Anlass ist gemessen: Im UI-Lauf vom 2026-08-28 kamen leere
    Werte durch, wurden gespeichert und angezeigt, und die Metadatenkaskade
    lief nie an — ohne eine einzige Meldung.

    **Eine Funktion für drei Verwender**, und das ist der Zweck: Das
    Contract-Kit prüft damit die Antwort eines Plugins, die Host-Grenze prüft
    dieselbe Antwort noch einmal, und ein Plugin-Autor kann sie selbst rufen,
    bevor er antwortet. Drei Fassungen dieser Regel liefen genau so
    auseinander wie die drei Identitätsrekonstruktionen vor T-31.

    Der Gattungskatalog wird hier **nicht** geprüft. Er ist offen, und was
    darin steht, entscheidet der Host — der Vertrag verlangt nur, dass
    überhaupt etwas gesagt wird.

    Args:
        resolved: Eine `types.Resolved`-Antwort.

    Returns:
        Die Beanstandung als Satz, oder ``""`` wenn die Antwort trägt.
    """
    for field_name in ("name", "instrument_type"):
        value = getattr(resolved, field_name, None)
        if value is None:
            return f"{field_name} fehlt — seit T-38 ein Pflichtfeld"
        if not isinstance(value, str):
            return f"{field_name} ist {type(value).__name__}, keine Zeichenkette"
        if not value.strip():
            return (
                f"{field_name} ist leer — ein Pflichtfeld mit nichts darin ist "
                "dasselbe wie ein fehlendes, nur schwerer zu finden"
            )
    return ""
