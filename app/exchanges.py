"""Börsentabelle und Symbol-Rückrechnung — ohne Netz-Abhängigkeiten.

Bewusst ein eigenes Modul: `app/db.py` braucht die Zerlegung für die
Identitäts-Migration aus T-21, und die Schema-Schicht soll dafür nicht den
Resolver samt yfinance mitziehen.

Das Symbolformat ist eine **Vereinbarung der App**, keine Abhängigkeit zu
Yahoo: Es entsteht hier aus `ticker` und dem Suffix der eigenen Tabelle.
"""

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

# Ein MIC nach ISO 10383: genau vier Zeichen, Großbuchstaben oder Ziffern.
#
# Ohne Anker, weil er mit `fullmatch` benutzt wird: `$` würde in Python auch
# **vor** einem abschließenden Zeilenumbruch matchen, und `"XNAS\n"` käme
# durch — ein Wert, den der Eindeutigkeits-Index sogar von `XNAS`
# unterscheidet.
_MIC_PATTERN = re.compile(r"[A-Z0-9]{4}")

# Ein kanonischer Ticker: Großbuchstaben und Ziffern, sonst nichts.
#
# Ebenfalls ohne Anker und mit `fullmatch` — aus demselben Grund wie oben.
_TICKER_PATTERN = re.compile(r"[A-Z0-9]+")

# Stabile Ablehnungsgründe — **Kennungen, keine Sätze.**
#
# Der Text gehört ins UI und muss in DE und EN vorliegen; hier steht nur, *was*
# der Fall ist. Ein freier Text an dieser Stelle wäre nicht übersetzbar, nicht
# prüfbar und bei der ersten Umformulierung ein stiller Bruch für jeden, der
# darauf reagiert.
#
# Sie standen bis T-21 Übergabe 3 in `app/migration.py`. Seit der Aufnahmeweg
# dieselben drei Fälle beantwortet, gehören sie zur Regel und nicht zu einem
# ihrer beiden Aufrufer — `app.migration` reicht sie unverändert weiter, damit
# Werte, Tests und die i18n-Schlüssel des Dashboards unberührt bleiben.
REASON_NO_SUFFIX = "symbol_without_exchange_suffix"
REASON_UNKNOWN_SUFFIX = "unknown_exchange_suffix"
REASON_NON_CANONICAL_TICKER = "non_canonical_ticker"

REJECTION_REASONS = frozenset(
    {REASON_NO_SUFFIX, REASON_UNKNOWN_SUFFIX, REASON_NON_CANONICAL_TICKER}
)

# Der Suffix ist der Alias der einen und der MIC einer **anderen** Börse.
#
# Nur für die **Eingabe**, nicht für den Umzugsbericht: Ein gespeichertes
# Symbol trägt immer den Alias, dort stellt sich die Frage nicht. Deshalb steht
# die Kennung außerhalb von `REJECTION_REASONS` — der Reason-Katalog des
# Berichts bliebe sonst mit einem Grund stehen, den er nie vergeben kann.
REASON_AMBIGUOUS_SUFFIX = "ambiguous_exchange_suffix"

# Eine ISIN nach ISO 6166: Ländercode, neun alphanumerische Stellen, Prüfziffer.
#
# Steht **hier** und nicht mehr in `app/routers/validation.py`, seit der
# Aufnahmeweg dieselbe Frage stellt: Ein Service darf nicht in der
# Router-Schicht importieren, und eine zweite Kopie liefe beim ersten Sonderfall
# auseinander. Die Form eines Wertpapierkennzeichens ist Fachwissen, keine
# HTTP-Prüfung — dass ein `422` daraus wird, entscheidet der Router.
ISIN_PATTERN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


@dataclass(frozen=True)
class ExchangeDef:
    """Definition einer **Börse**: Alias, Anzeige, Region, Währung.

    ``currency`` ist nur Anzeige — die reale Kurswährung stammt aus dem Live-Quote.

    ``alias`` ist das **nackte Token ohne Punkt** (``'DE'``, ``'SG'``).
    Bis T-21 Teil 3 stand hier ``'.DE'`` mit Punkt, während `split_symbol` den
    Teil *hinter* dem Punkt verglich — zwei Schichten, die ohne eine nirgends
    beschriebene Normalisierung aneinander vorbeigesucht hätten. Den Punkt
    setzt jetzt ausschließlich `provider_alias`.

    ``None`` heißt „diese Börse hängt kein Kürzel an den Ticker" — bei den
    US-Plätzen der Normalfall. Fünf teilen sich die Abwesenheit, und genau
    deshalb ist die Rückrechnung von ``AAPL`` auf einen MIC nicht möglich.

    **Abwesenheit ist `None`, nicht `''`.** Der Leerstring wäre ein magischer
    Wert: ein Alias, der zufällig aus null Zeichen besteht. Er zwingt jede
    Schicht — Python, REST, TypeScript — zu derselben ungeschriebenen
    Übereinkunft, und T-30 müsste seinen deklarativ gemeldeten Alias an eine
    Form anfügen, die Abwesenheit nicht benennen kann. Der Alias ist **einer
    oder keiner**, und der Typ sagt das.

    **Was hier nicht steht.** Bis T-21 trug jede Zeile zwei Spalten mit, die
    nur OpenFIGI etwas angingen (`figi_id_type`, `figi_value`). Sie sind zum
    Provider gezogen: Sonst legte jede weitere Kursquelle ihre eigenen zwei
    Spalten dazu, und die Börsentabelle würde zur Sammelstelle für
    Anbieter-Eigenheiten. Sie beschreibt die **Börse**, nicht den Weg zu ihr.
    """

    alias: str | None
    name: str
    region: str  # "germany" | "usa" | "europe" | "global"
    currency: str


@dataclass(frozen=True)
class CollectorDef:
    """Ein **Sammelcode** — mehrere Handelsplätze unter einem Suchbegriff.

    Kein Handelsplatz und deshalb **kein MIC**: `US` steht für „irgendwo in
    den USA" und taugt nie als kanonischer Wert in `instruments.mic`. Bis
    Teil 3 lag der Eintrag trotzdem in derselben Tabelle wie die Börsen, und
    `GET /exchanges` lieferte ihn als ``mic="US"`` aus — einen Wert, den
    `is_real_mic` im selben Modul ablehnt.

    ``members`` ist die **einzige** Stelle, an der die Zugehörigkeit steht.
    Sie zusätzlich an jede Börse zu schreiben wäre dieselbe Regel zweimal und
    liefe beim Plugin-Merge auseinander, sobald zwei Quellen dieselbe Börse
    beisteuern.
    """

    name: str
    region: str
    currency: str
    members: tuple[str, ...]


# Weltweite Börsentabelle: Key = MIC (bzw. 'US'). Erweiterbar per Zeile.
EXCHANGES: dict[str, ExchangeDef] = {
    # Amerika — die fünf US-Plätze führen keinen Alias, und das steht als
    # `None` da, nicht als Leerstring. Aus `AAPL` lässt sich weiterhin kein MIC
    # ableiten; neu ist nur die Gegenrichtung, `(AAPL, XNAS)` → `AAPL`.
    "XNAS": ExchangeDef(None, "NASDAQ", "usa", "USD"),
    "XNYS": ExchangeDef(None, "NYSE", "usa", "USD"),
    "ARCX": ExchangeDef(None, "NYSE Arca", "usa", "USD"),
    "XASE": ExchangeDef(None, "NYSE American", "usa", "USD"),
    "BATS": ExchangeDef(None, "Cboe BZX", "usa", "USD"),
    "XTSE": ExchangeDef("TO", "Toronto", "global", "CAD"),
    "XTSX": ExchangeDef("V", "TSX Venture", "global", "CAD"),
    "BVMF": ExchangeDef("SA", "São Paulo (B3)", "global", "BRL"),
    "XMEX": ExchangeDef("MX", "Mexiko", "global", "MXN"),
    # Europa
    "XETR": ExchangeDef("DE", "Xetra", "germany", "EUR"),
    "XFRA": ExchangeDef("F", "Frankfurt", "germany", "EUR"),
    "XSTU": ExchangeDef("SG", "Stuttgart", "germany", "EUR"),
    "XLON": ExchangeDef("L", "London LSE", "europe", "GBp"),
    "XMIL": ExchangeDef("MI", "Mailand", "europe", "EUR"),
    "XPAR": ExchangeDef("PA", "Paris (Euronext)", "europe", "EUR"),
    "XAMS": ExchangeDef("AS", "Amsterdam", "europe", "EUR"),
    "XBRU": ExchangeDef("BR", "Brüssel", "europe", "EUR"),
    "XLIS": ExchangeDef("LS", "Lissabon", "europe", "EUR"),
    "XMAD": ExchangeDef("MC", "Madrid", "europe", "EUR"),
    "XWBO": ExchangeDef("VI", "Wien", "europe", "EUR"),
    "XSWX": ExchangeDef("SW", "SIX Swiss", "europe", "CHF"),
    "XSTO": ExchangeDef("ST", "Stockholm", "europe", "SEK"),
    "XCSE": ExchangeDef("CO", "Kopenhagen", "europe", "DKK"),
    "XOSL": ExchangeDef("OL", "Oslo", "europe", "NOK"),
    "XHEL": ExchangeDef("HE", "Helsinki", "europe", "EUR"),
    "XWAR": ExchangeDef("WA", "Warschau", "europe", "PLN"),
    # Asien-Pazifik
    "XTKS": ExchangeDef("T", "Tokio", "global", "JPY"),
    "XHKG": ExchangeDef("HK", "Hongkong", "global", "HKD"),
    "XSHG": ExchangeDef("SS", "Shanghai", "global", "CNY"),
    "XSHE": ExchangeDef("SZ", "Shenzhen", "global", "CNY"),
    "XASX": ExchangeDef("AX", "Sydney (ASX)", "global", "AUD"),
    "XSES": ExchangeDef("SI", "Singapur", "global", "SGD"),
    "XNSE": ExchangeDef("NS", "Indien NSE", "global", "INR"),
    "XBOM": ExchangeDef("BO", "Indien BSE", "global", "INR"),
    "XKRX": ExchangeDef("KS", "Korea (KRX)", "global", "KRW"),
    "XTAI": ExchangeDef("TW", "Taiwan", "global", "TWD"),
    # Afrika / Nahost
    "XJSE": ExchangeDef("JO", "Johannesburg", "global", "ZAR"),
    "XTAE": ExchangeDef("TA", "Tel Aviv", "global", "ILS"),
}

# Sammelcodes — **getrennt** von den Börsen, weil sie keine sind.
#
# `US` bleibt ein gültiger `DEFAULT_EXCHANGE` und ein gültiger
# OpenFIGI-Suchcode; es ist nur kein Handelsplatz. Wer es als `mic` speichert,
# erzeugt genau den Zustand, den T-21 austreibt.
COLLECTORS: dict[str, CollectorDef] = {
    "US": CollectorDef(
        name="NYSE / NASDAQ",
        region="usa",
        currency="USD",
        members=("XNAS", "XNYS", "ARCX", "XASE", "BATS"),
    ),
}
DEFAULT_EXCHANGE = "XETR"

# Abgeleitet, nicht gepflegt: Die Sammelcodes **sind** die Schlüssel von
# `COLLECTORS`. Eine zweite Liste danebenzustellen hieße, dieselbe Regel an
# zwei Orten zu führen — und genau das ist in Teil 3 aufgefallen, als der
# frühere Entwurf sie zusätzlich als Mitgliedschaft an jede Börse schreiben
# wollte: dreimal dasselbe Wissen.
COLLECTOR_CODES = frozenset(COLLECTORS)

# Emissionsland (ISIN-Präfix) → Heimatbörse. Der Rückfall der Kaskade: Findet
# die bevorzugte Börse nichts, ist die Heimatbörse der beste nächste Versuch.
#
# **Eine Heuristik, kein Gesetz.** Das Präfix nennt die ausgebende Stelle, nicht
# den gewünschten Handelsplatz. Deshalb stehen hier nur Länder, bei denen die
# Zuordnung eindeutig genug ist — `IE` und `LU` fehlen bewusst: Ein irischer
# oder luxemburgischer Fonds wird europaweit gehandelt und hat an seinem
# Domizil oft gar kein Listing. Für sie übernimmt der Yahoo-Fallback.
HOME_EXCHANGES: dict[str, str] = {
    "AT": "XWBO",
    "AU": "XASX",
    "BE": "XBRU",
    "BR": "BVMF",
    "CA": "XTSE",
    "CH": "XSWX",
    "CN": "XSHG",
    "DE": "XETR",
    "DK": "XCSE",
    "ES": "XMAD",
    "FI": "XHEL",
    "FR": "XPAR",
    "GB": "XLON",
    "HK": "XHKG",
    "IL": "XTAE",
    "IN": "XNSE",
    "IT": "XMIL",
    "JP": "XTKS",
    "KR": "XKRX",
    "MX": "XMEX",
    "NL": "XAMS",
    "NO": "XOSL",
    "PL": "XWAR",
    "PT": "XLIS",
    "SE": "XSTO",
    "SG": "XSES",
    "TW": "XTAI",
    "US": "US",
    "ZA": "XJSE",
}


def is_real_mic(mic: str | None) -> bool:
    """Ist das ein echter MIC — oder einer der internen Sammelcodes?

    Die Tabelle führt `US` als OpenFIGI-Suchcode für NYSE und NASDAQ zusammen.
    Das ist **kein** ISO-10383-MIC, und ein Feld, das mal echte MICs und mal
    diesen Code enthält, wird beim ersten Anbieter zum Problem, der echte MICs
    erwartet (T-21).

    Geprüft wird **beides**:

    1. **Die Schreibweise.** Ein MIC nach ISO 10383 hat genau vier Zeichen,
       Großbuchstaben oder Ziffern. „Der Tabelle unbekannt" ist kein
       Gütesiegel — meine erste Fassung ließ jeden nichtleeren String durch,
       und damit hätte auch `NOT-A-MIC`, `xnAs` oder `XNAS ` im kanonischen
       Feld stehen können. Geprüft wird mit `fullmatch`: `$` matcht in Python
       auch vor einem abschließenden Zeilenumbruch, und `"XNAS\n"` wäre
       durchgegangen.
    2. **Kein Sammelcode.** Geprüft gegen `COLLECTOR_CODES`. Die Längenregel
       fängt das heutige `US` schon ab; die Prüfung bleibt trotzdem, weil ein
       künftiger vierstelliger Sammelcode sonst durchginge.

    Ein MIC, den die Tabelle nicht kennt, aber richtig geschrieben ist, gilt
    als echt: `XNAS` steht dort nicht und ist genau der Wert, den eine
    manuelle Zuordnung setzen soll. Die Tabelle ist eine Auswahl der Börsen,
    die StockInfo auflösen kann — kein Verzeichnis aller MICs.

    Args:
        mic: Der zu prüfende Code, oder ``None``.

    Returns:
        ``True`` wenn der Wert als kanonischer MIC taugt.
    """
    if not mic or not _MIC_PATTERN.fullmatch(mic):
        return False
    return mic not in COLLECTOR_CODES


def canonical_identity(
    ticker: str | None, mic: str | None
) -> tuple[str, str] | None:
    """Die eine Stelle, die eine **neue** Identität für gültig erklärt.

    Vollständig ist sie nur zu zweit: kanonischer Ticker **und** echter MIC.
    Eine halbe Zuordnung wird nicht gespeichert — ein Ticker ohne Handelsplatz
    ist bei jeder Quelle mehrdeutig, und ein Handelsplatz ohne Ticker sagt gar
    nichts.

    **Der Status ist mit T-21 Teil 3 entfallen.** Die Funktion gab früher
    `(ticker, mic, status)` zurück und schrieb das Ergebnis als
    `identity_status` in die Zeile. Seit eine halbe Identität nirgends mehr
    weiterleben darf, hätte die Spalte nur noch einen einzigen Wert — und die
    beste Zahl an Quellen für einen Wert, den es nicht mehr gibt, ist null.
    Geblieben ist die Vollständigkeitsaussage; sie führt jetzt zu **Annahme
    oder Ablehnung** statt zu einer Beschriftung.

    **Strenger als das, was der Bestand tragen darf.** `keeps_its_identity` in
    `app/migration.py` beurteilt *gespeicherte* Zeilen milder — eine von Hand
    gesetzte Zuordnung wie `RDS-A`/`XLON` bleibt dort stehen, statt beim
    nächsten Start verworfen zu werden. Streng beim Erzeugen, nachsichtig beim
    Annehmen: Sonst löschte ein Regel-Nachziehen menschliche Arbeit.

    Args:
        ticker: Vorgeschlagener Ticker, oder ``None``.
        mic: Vorgeschlagener MIC, oder ``None``.

    Returns:
        `(ticker, mic)` bei vollständiger Zuordnung, sonst ``None``.
    """
    if is_canonical_ticker(ticker) and is_real_mic(mic):
        assert ticker is not None and mic is not None  # von beiden Prüfungen
        return ticker, mic
    return None


def is_canonical_ticker(ticker: str | None) -> bool:
    """Taugt dieser Ticker als kanonische Hälfte der Identität?

    Erlaubt sind Großbuchstaben und Ziffern — `EUNL`, `AAPL`, `7203` (Tokio
    notiert numerisch). Alles andere ist **anbieterspezifische Zeichensetzung**
    und wird nicht übernommen:

    * Yahoo schreibt Anteilsklassen mit Bindestrich (`BRK-B`),
    * OpenFIGI mit Schrägstrich (`BRK/B`),
    * an der NYSE selbst steht ein Punkt (`BRK.B`).

    Drei Schreibweisen desselben Papiers — welche die richtige ist, entscheidet
    die Börse, nicht der Anbieter, bei dem der Wert gerade herkam. Eine davon
    zur kanonischen zu erklären hieße raten, und geraten wird hier nichts: Der
    Fall bleibt offen und sichtbar, bis ihn jemand von Hand zuordnet.

    Der Punkt ist zusätzlich **doppeldeutig**: In `EUNL.DE` trennt er die
    Börse ab, in `BRK.B` die Anteilsklasse. Ein Ticker mit Punkt würde die
    Zerlegung `f"{ticker}{suffix}"` unumkehrbar machen.

    Args:
        ticker: Der zu prüfende Ticker, oder ``None``.

    Returns:
        ``True`` wenn der Wert als kanonischer Ticker taugt.
    """
    return bool(ticker) and bool(_TICKER_PATTERN.fullmatch(ticker))


def split_symbol(symbol: str) -> tuple[str | None, str | None]:
    """Rechnet ein Symbol auf `(ticker, mic)` zurück — oder gibt auf.

    Die Umkehrung von `f"{ticker}{suffix}"`. Sie ist möglich, weil in der
    Börsentabelle kein Suffix doppelt vergeben ist (gemessen am 2026-08-19
    über alle 33 Börsen).

    **Zwei Fälle bleiben bewusst offen**, und in beiden ist ``(None, None)``
    die richtige Antwort:

    * **Suffixlos** (`AAPL`). Die Tabelle führt dafür nur den Sammelcode `US`
      — kein ISO-10383-MIC. Ob `XNYS` oder `XNAS` gilt, weiß erst das
      aufgelöste Listing. Ein Feld, das mal echte MICs und mal einen internen
      Suchcode enthält, wird beim ersten Anbieter zum Problem, der echte MICs
      erwartet.
    * **Fremde Schreibweise** (`BRK-B` aus der Yahoo-Suche). Der Bindestrich
      ist anbieterspezifisch und bedeutet bei anderen Tickern etwas anderes;
      `BRK.B` daraus zu machen wäre geraten. Das gilt auch, wenn die **Börse**
      feststeht: `RDS-A.L` hat ein bekanntes Suffix, trägt aber weiterhin
      Yahoos Zeichensetzung im Ticker. Geprüft wird deshalb mit
      `is_canonical_ticker` — derselben Regel, an der sich die Erzeugung neuer
      Papiere misst. Sonst gälte für gewachsene Zeilen eine andere Wahrheit
      als für neue.

    Args:
        symbol: Das gespeicherte Listing-Symbol, z.B. ``'EUNL.DE'``.

    Returns:
        `(ticker, mic)` bei eindeutiger Zerlegung, sonst ``(None, None)``.
    """
    identity = identity_from_symbol(symbol)
    return identity if identity is not None else (None, None)


def identity_from_symbol(symbol: str) -> tuple[str, str] | None:
    """Die kanonische Identität eines Symbols — **die** Regel, einmal.

    `split_symbol` ist die ältere Form derselben Auskunft und gibt ein Tupel
    aus zwei Optionalen zurück, das jeder Aufrufer wieder auseinandernehmen
    muss; sie ruft jetzt hier durch.

    **Warum die Trennung überhaupt entstand:** Der Umzug in `app/migration.py`
    brauchte ein „Ergebnis oder nichts" und bekam eine eigene, gleich
    aussehende Funktion. Zwei Implementierungen derselben Fachregel laufen
    beim ersten neuen Fall auseinander — dann entscheidet die Migration anders
    als der übrige Core, und zwar über die Identität von Papieren.

    Args:
        symbol: Das gespeicherte Listing-Symbol, z.B. ``'EUNL.DE'``.

    Returns:
        `(ticker, mic)` bei eindeutiger Zerlegung, sonst ``None``.
    """
    if not symbol or "." not in symbol:
        return None

    ticker, _, alias = symbol.partition(".")
    mic = mic_for_alias(alias)
    if mic is None or not is_canonical_ticker(ticker):
        return None
    return ticker, mic


def identity_from_input(value: str) -> tuple[str, str] | None:
    """Die kanonische Identität aus einer **Benutzereingabe** — beide Formen.

    Der Unterschied zu `identity_from_symbol` ist kein Zufall und keine
    Verdopplung, sondern die Trennung zweier Fragen:

    * `identity_from_symbol` zerlegt ein **gespeichertes** Symbol. Die trägt
      StockInfo selbst zusammen, und zwar immer mit dem Provider-Alias
      (`EUNL.DE`) — die Form ist bekannt, weil wir sie erzeugen.
    * Hier steht die **Eingabe** eines Menschen. Sie darf laut
      Eingabeentscheidung (Mike, 2026-08-24) neben dem Alias auch den echten
      MIC nennen: `EUNL.XETR` meint dasselbe Listing wie `EUNL.DE`.

    Der Aliasweg läuft deshalb durch `identity_from_symbol` — er wird nicht
    nachgebaut, sondern benutzt. Nur die MIC-Form kommt hier dazu.

    **Ein doppeldeutiges Token wird abgelehnt, nicht entschieden.** Zeigt der
    Suffix als Alias auf die eine und als MIC auf eine **andere** Börse, gibt
    es keine richtige Wahl — nur zwei falsche. Der frühere Entwurf ließ hier
    „der Alias gewinnt" stehen; das ist eine stille Entscheidung über den
    Handelsplatz eines fremden Papiers, und der Benutzer bekäme ein anderes
    Listing, als er genannt hat. Heute kann der Fall nicht eintreten (kein
    Alias ist vierstellig), aber ein Plugin darf den Katalog erweitern — und
    dann entscheidet diese Zeile.

    Die Länge allein entscheidet nichts: Ein vierstelliger Alias, der auf
    **dieselbe** Börse zeigt wie der gleichnamige MIC, ist kein Konflikt.

    **Ein unbekannter MIC zählt nicht.** `is_real_mic` allein genügt nicht: Es
    prüft die Schreibweise, nicht die Zuständigkeit. `FOO.ZZZZ` wäre formal
    ein MIC, aber StockInfo könnte das Papier weder abrufen noch einen Alias
    dafür bilden — die Kursquelle bekäme den nackten Ticker und suchte in den
    USA. Verlangt wird deshalb ein Eintrag im Katalog.

    Args:
        value: Der getrimmte, großgeschriebene Rohwert, etwa ``'EUNL.XETR'``.

    Returns:
        `(ticker, mic)`, oder ``None``. Warum es ``None`` wurde, sagt
        `input_failure`.
    """
    if not value or "." not in value:
        return None
    ticker, _, suffix = value.partition(".")
    if not is_canonical_ticker(ticker):
        return None
    if suffix_is_ambiguous(suffix):
        return None

    identity = identity_from_symbol(value)
    if identity is not None:
        return identity

    if suffix in EXCHANGES and is_real_mic(suffix):
        return ticker, suffix
    return None


def suffix_is_ambiguous(suffix: str) -> bool:
    """Zeigt dieser Suffix als Alias und als MIC auf **verschiedene** Börsen?

    Die eine Stelle, die den Konflikt feststellt — `identity_from_input` lehnt
    daraufhin ab, `input_failure` benennt ihn. Getrennt formuliert liefen die
    beiden beim ersten Plugin-Katalog auseinander.

    Args:
        suffix: Das nackte Token hinter dem Punkt.

    Returns:
        ``True``, wenn beide Deutungen existieren und auf verschiedene Börsen
        zeigen. Zeigen sie auf dieselbe, ist nichts doppeldeutig.
    """
    by_alias = mic_for_alias(suffix)
    if by_alias is None or suffix not in EXCHANGES:
        return False
    return by_alias != suffix


def input_failure(value: str) -> str | None:
    """Warum führt diese Eingabe zu keiner Identität?

    Das Gegenstück zu `identity_from_input` — genau eine der beiden liefert
    ein Ergebnis. Dieselben drei Kennungen, mit denen der Umzugsbericht
    ablehnt: Es ist dieselbe Frage an dasselbe Symbol, nur an anderer Stelle
    gestellt. Zwei Kennungsfamilien für einen Sachverhalt hätten dem Dashboard
    zwei Übersetzungskataloge beschert.

    Der Unterschied zu `rejection_reason` liegt allein im Suffixtest: Hier
    gelten **beide** Formen. `EUNL.XETR` ist eine gültige Eingabe, aber kein
    gültiges gespeichertes Symbol.

    Args:
        value: Der getrimmte, großgeschriebene Rohwert.

    Returns:
        Eine der Kennungen, oder ``None`` wenn die Eingabe trägt.
    """
    if identity_from_input(value) is not None:
        return None
    if not value or "." not in value:
        return REASON_NO_SUFFIX

    ticker, _, suffix = value.partition(".")
    if not is_canonical_ticker(ticker):
        return REASON_NON_CANONICAL_TICKER
    if suffix_is_ambiguous(suffix):
        # Zwei Deutungen, zwei Börsen — hier wird nicht gewählt, sondern
        # gesagt, dass die Eingabe nicht entscheidbar ist.
        return REASON_AMBIGUOUS_SUFFIX
    if mic_for_alias(suffix) is None and suffix not in EXCHANGES:
        return REASON_UNKNOWN_SUFFIX
    # Der Suffix steht im Katalog, ist aber kein echter MIC — der Sammelcode
    # `US`. Er ist kein Handelsplatz, und welcher der fünf gemeint ist, sagt
    # die Eingabe nicht.
    return REASON_UNKNOWN_SUFFIX


def mic_for_alias(alias: str) -> str | None:
    """Welche Börse hängt diesen Alias an? — die Umkehrung von `ExchangeDef.alias`.

    Die **eine** Stelle, die vom Alias zurück auf die Börse schließt. Sie ist
    möglich, weil kein Alias doppelt vergeben ist; `test_kein_alias_ist_doppelt_vergeben`
    hält das fest.

    Eigens herausgezogen, weil zwei Schichten die Frage stellen: die Zerlegung
    eines gespeicherten Symbols (`split_symbol`) und die Auswahl der
    bevorzugten Börse im Resolver. Beantworteten sie sie getrennt, liefen sie
    beim ersten neuen Eintrag auseinander.

    Args:
        alias: Das nackte Token hinter dem Punkt, etwa ``'DE'``.

    Returns:
        Der MIC der Börse, oder ``None`` — auch für den Leerstring, denn eine
        Börse *ohne* Alias lässt sich nicht über ihn finden.
    """
    return next(
        (mic for mic, definition in EXCHANGES.items() if definition.alias == alias),
        None,
    )


def preference_kind(code: str) -> str | None:
    """Was ist dieser Vorgabewert — eine Börse, ein Sammelcode, oder nichts?

    `DEFAULT_EXCHANGE` darf beides sein: `XETR` meint einen Handelsplatz,
    `US` meint „irgendwo in den USA". Seit die beiden in getrennten Tabellen
    liegen, muss ein Aufrufer wissen, welches von beiden er in der Hand hält —
    sonst baut sich jeder seine eigene Regel aus zwei Lookups.

    Args:
        code: Der konfigurierte Wert, etwa aus `DEFAULT_EXCHANGE`.

    Returns:
        ``'exchange'``, ``'collector'`` oder ``None`` für einen unbekannten
        Wert.
    """
    if code in EXCHANGES:
        return "exchange"
    if code in COLLECTORS:
        return "collector"
    return None


def preferred_mics(code: str) -> tuple[str, ...]:
    """Die Handelsplätze, die zu einer Präferenz gehören — Börse **oder** Sammelcode.

    Die **eine** Stelle, die „was umfasst dieser Vorgabewert?" beantwortet.
    Eine Börse umfasst sich selbst, ein Sammelcode seine Mitglieder.

    Ein unbekannter Code fällt auf `DEFAULT_EXCHANGE` zurück — dieselbe
    Nachsicht wie in der Auflösungskaskade, damit eine vertippte Konfiguration
    die Auswahl nicht leer laufen lässt.

    **Warum die MICs und nicht nur die Aliase.** Die fünf US-Plätze führen
    keinen Alias, und über den Alias sind sie deshalb ununterscheidbar:
    `XNAS` und der Sammelcode `US` sähen beide gleich aus. Wer nur die Aliase
    kennt, muss die Abwesenheit als „alles Punktlose zählt" deuten — und wählt
    dann für `DEFAULT_EXCHANGE=XNAS` einen Arca-Treffer. Der MIC trägt die
    Unterscheidung, die dem Alias fehlt.

    Args:
        code: Der konfigurierte Vorgabewert.

    Returns:
        Die MICs der umfassten Handelsplätze, nie leer.
    """
    if code in EXCHANGES:
        return (code,)
    collector = COLLECTORS.get(code)
    if collector is not None:
        return tuple(mic for mic in collector.members if mic in EXCHANGES)
    return (DEFAULT_EXCHANGE,)


def provider_alias(ticker: str, mic: str) -> str:
    """Baut aus der kanonischen Identität das abrufbare Symbol.

    **Die einzige Stelle, die den Punkt setzt.** Aus der Identität entsteht
    das Symbol, nie umgekehrt — und ohne Alias bleibt es beim nackten Ticker,
    weil die US-Plätze keinen führen.

    Wem der so entstandene Wert *gehört* und was bei einem Providerwechsel mit
    ihm geschieht, klärt T-29. Hier geht es nur um seine Bildung.

    Args:
        ticker: Kanonischer Ticker, etwa ``'EUNL'``.
        mic: Echter MIC, etwa ``'XETR'``.

    Returns:
        Das Symbol, etwa ``'EUNL.DE'`` — oder ``'AAPL'``, wenn die Börse
        keinen Alias führt.
    """
    definition = EXCHANGES.get(mic)
    alias = definition.alias if definition else None
    return f"{ticker}.{alias}" if alias else ticker


def is_isin(value: str) -> bool:
    """Trägt dieser Wert die Form einer ISIN?

    Die Frage stellt der Aufnahmeweg, um einen rohen Feldwert einem der beiden
    Wege zuzuordnen: ISIN oder Symbol. Geprüft wird die **Form**, nicht die
    Existenz — ob es das Papier gibt, weiß erst die Auflösung.

    Args:
        value: Der bereits getrimmte und großgeschriebene Rohwert.

    Returns:
        ``True`` bei ISIN-Form.
    """
    return bool(value) and bool(ISIN_PATTERN.fullmatch(value))


def home_exchange(isin: str) -> str | None:
    """Die Heimatbörse zum Emissionsland einer ISIN.

    Args:
        isin: ISIN des Wertpapiers.

    Returns:
        Der MIC der Heimatbörse, oder ``None`` wenn das Präfix keiner
        zugeordnet ist.
    """
    return HOME_EXCHANGES.get(isin[:2].upper()) if len(isin) >= 2 else None
