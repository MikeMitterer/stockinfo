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


# Der Wert der Spalte `identity_status`. Er steht hier und nicht in `db.py`,
# weil ihn zwei Wege setzen — die Migration des Bestands und das Anlegen neuer
# Papiere — und beide dieselbe Regel brauchen.
IDENTITY_RESOLVED = "resolved"
IDENTITY_UNRESOLVED = "legacy_unresolved"


def canonical_identity(
    ticker: str | None, mic: str | None
) -> tuple[str | None, str | None, str]:
    """Die eine Stelle, die eine **neue** Identität für gültig erklärt.

    Vollständig ist sie nur zu zweit: kanonischer Ticker **und** echter MIC.
    Eine halbe Zuordnung wird nicht gespeichert — ein Ticker ohne Handelsplatz
    ist bei jeder Quelle mehrdeutig, und ein Handelsplatz ohne Ticker sagt gar
    nichts. Beides zusammen leer und als offen beschriftet ist der ehrlichere
    Zustand: Er taucht in der Liste offener Zuordnungen auf, statt eine
    Zuordnung vorzutäuschen.

    **Strenger als das, was der Bestand tragen darf.** `_identity_is_complete`
    in `app/db.py` beurteilt *gespeicherte* Zeilen milder — eine von Hand
    gesetzte Zuordnung wie `RDS-A`/`XLON` bleibt dort stehen, statt beim
    nächsten Start verworfen zu werden. Streng beim Erzeugen, nachsichtig beim
    Annehmen: Sonst löschte ein Regel-Nachziehen menschliche Arbeit.

    Args:
        ticker: Vorgeschlagener Ticker, oder ``None``.
        mic: Vorgeschlagener MIC, oder ``None``.

    Returns:
        `(ticker, mic, status)` — bei unvollständiger Zuordnung
        ``(None, None, IDENTITY_UNRESOLVED)``.
    """
    if is_canonical_ticker(ticker) and is_real_mic(mic):
        return ticker, mic, IDENTITY_RESOLVED
    return None, None, IDENTITY_UNRESOLVED


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
    if not symbol or "." not in symbol:
        return None, None

    ticker, _, alias = symbol.partition(".")
    for mic, definition in EXCHANGES.items():
        if definition.alias and definition.alias == alias:
            return (ticker, mic) if is_canonical_ticker(ticker) else (None, None)
    return None, None


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


def preferred_aliases(code: str) -> tuple[str, ...]:
    """Die Aliase der Handelsplätze, die zu einer Präferenz gehören.

    Aus `preferred_mics` abgeleitet, nicht daneben gepflegt: Die Frage „welche
    Plätze umfasst der Vorgabewert?" hat genau eine Antwort, und die steht dort.

    Börsen ohne Alias steuern **nichts** bei, statt eine Abwesenheit in die
    Liste zu legen. Ein leeres Ergebnis heißt deshalb genau eines: „keiner der
    in Frage kommenden Plätze hängt ein Kürzel an". Es heißt **nicht** „jedes
    punktlose Symbol gehört dazu" — welche Plätze gemeint sind, sagt allein
    `preferred_mics`.

    Args:
        code: Der konfigurierte Vorgabewert.

    Returns:
        Die vorhandenen Aliase, möglicherweise keiner.
    """
    return tuple(
        alias for mic in preferred_mics(code) if (alias := EXCHANGES[mic].alias)
    )


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


def home_exchange(isin: str) -> str | None:
    """Die Heimatbörse zum Emissionsland einer ISIN.

    Args:
        isin: ISIN des Wertpapiers.

    Returns:
        Der MIC der Heimatbörse, oder ``None`` wenn das Präfix keiner
        zugeordnet ist.
    """
    return HOME_EXCHANGES.get(isin[:2].upper()) if len(isin) >= 2 else None
