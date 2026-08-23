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
    """Definition einer Börse: Suffix, Anzeige, Region, Währung.

    ``currency`` ist nur Anzeige — die reale Kurswährung stammt aus dem Live-Quote.

    **Was hier nicht steht.** Bis T-21 trug jede Zeile zwei Spalten mit, die
    nur OpenFIGI etwas angingen (`figi_id_type`, `figi_value`). Sie sind zum
    Provider gezogen: Sonst legte jede weitere Kursquelle ihre eigenen zwei
    Spalten dazu, und die Börsentabelle würde zur Sammelstelle für
    Anbieter-Eigenheiten. Sie beschreibt die **Börse**, nicht den Weg zu ihr.
    """

    suffix: str
    name: str
    region: str  # "germany" | "usa" | "europe" | "global"
    currency: str


# Weltweite Börsentabelle: Key = MIC (bzw. 'US'). Erweiterbar per Zeile.
EXCHANGES: dict[str, ExchangeDef] = {
    # Amerika
    "US": ExchangeDef("", "NYSE / NASDAQ", "usa", "USD"),
    "XTSE": ExchangeDef(".TO", "Toronto", "global", "CAD"),
    "XTSX": ExchangeDef(".V", "TSX Venture", "global", "CAD"),
    "BVMF": ExchangeDef(".SA", "São Paulo (B3)", "global", "BRL"),
    "XMEX": ExchangeDef(".MX", "Mexiko", "global", "MXN"),
    # Europa
    "XETR": ExchangeDef(".DE", "Xetra", "germany", "EUR"),
    "XFRA": ExchangeDef(".F", "Frankfurt", "germany", "EUR"),
    "XLON": ExchangeDef(".L", "London LSE", "europe", "GBp"),
    "XMIL": ExchangeDef(".MI", "Mailand", "europe", "EUR"),
    "XPAR": ExchangeDef(".PA", "Paris (Euronext)", "europe", "EUR"),
    "XAMS": ExchangeDef(".AS", "Amsterdam", "europe", "EUR"),
    "XBRU": ExchangeDef(".BR", "Brüssel", "europe", "EUR"),
    "XLIS": ExchangeDef(".LS", "Lissabon", "europe", "EUR"),
    "XMAD": ExchangeDef(".MC", "Madrid", "europe", "EUR"),
    "XWBO": ExchangeDef(".VI", "Wien", "europe", "EUR"),
    "XSWX": ExchangeDef(".SW", "SIX Swiss", "europe", "CHF"),
    "XSTO": ExchangeDef(".ST", "Stockholm", "europe", "SEK"),
    "XCSE": ExchangeDef(".CO", "Kopenhagen", "europe", "DKK"),
    "XOSL": ExchangeDef(".OL", "Oslo", "europe", "NOK"),
    "XHEL": ExchangeDef(".HE", "Helsinki", "europe", "EUR"),
    "XWAR": ExchangeDef(".WA", "Warschau", "europe", "PLN"),
    # Asien-Pazifik
    "XTKS": ExchangeDef(".T", "Tokio", "global", "JPY"),
    "XHKG": ExchangeDef(".HK", "Hongkong", "global", "HKD"),
    "XSHG": ExchangeDef(".SS", "Shanghai", "global", "CNY"),
    "XSHE": ExchangeDef(".SZ", "Shenzhen", "global", "CNY"),
    "XASX": ExchangeDef(".AX", "Sydney (ASX)", "global", "AUD"),
    "XSES": ExchangeDef(".SI", "Singapur", "global", "SGD"),
    "XNSE": ExchangeDef(".NS", "Indien NSE", "global", "INR"),
    "XBOM": ExchangeDef(".BO", "Indien BSE", "global", "INR"),
    "XKRX": ExchangeDef(".KS", "Korea (KRX)", "global", "KRW"),
    "XTAI": ExchangeDef(".TW", "Taiwan", "global", "TWD"),
    # Afrika / Nahost
    "XJSE": ExchangeDef(".JO", "Johannesburg", "global", "ZAR"),
    "XTAE": ExchangeDef(".TA", "Tel Aviv", "global", "ILS"),
}
DEFAULT_EXCHANGE = "XETR"

# Codes, die **mehrere** Handelsplätze zusammenfassen. Sie stehen in der
# Tabelle, weil StockInfo über sie sucht — im kanonischen Feld `mic` dürfen sie
# nie landen.
#
# Vorher war dieses Merkmal indirekt zu haben: „wird bei OpenFIGI über
# `exchCode` gesucht" hieß „ist kein echter MIC". Die Kopplung war bequem und
# falsch — ein Sammelcode bleibt einer, auch wenn ihn nie jemand bei OpenFIGI
# sucht. Mit dem Umzug der Anbieter-Spalten wird sie ausdrücklich.
COLLECTOR_CODES = frozenset({"US"})

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

    ticker, _, rest = symbol.partition(".")
    suffix = f".{rest}"
    for mic, definition in EXCHANGES.items():
        if definition.suffix == suffix and mic not in COLLECTOR_CODES:
            # Ein Sammelcode steht für mehrere Handelsplätze und taugt nicht
            # als kanonischer MIC — auch dann nicht, wenn er ein Suffix trüge.
            return (ticker, mic) if is_canonical_ticker(ticker) else (None, None)
    return None, None


def home_exchange(isin: str) -> str | None:
    """Die Heimatbörse zum Emissionsland einer ISIN.

    Args:
        isin: ISIN des Wertpapiers.

    Returns:
        Der MIC der Heimatbörse, oder ``None`` wenn das Präfix keiner
        zugeordnet ist.
    """
    return HOME_EXCHANGES.get(isin[:2].upper()) if len(isin) >= 2 else None
