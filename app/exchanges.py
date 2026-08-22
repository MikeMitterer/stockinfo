"""Börsentabelle und Symbol-Rückrechnung — ohne Netz-Abhängigkeiten.

Bewusst ein eigenes Modul: `app/db.py` braucht die Zerlegung für die
Identitäts-Migration aus T-21, und die Schema-Schicht soll dafür nicht den
Resolver samt yfinance mitziehen.

Das Symbolformat ist eine **Vereinbarung der App**, keine Abhängigkeit zu
Yahoo: Es entsteht hier aus `ticker` und dem Suffix der eigenen Tabelle.
"""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class ExchangeDef:
    """Definition einer Börse: Anzeige, Yahoo-Suffix, OpenFIGI-Auflösung.

    ``currency`` ist nur Anzeige — die reale Kurswährung stammt aus dem Live-Quote.
    ``figi_value`` leer ⇒ der Dict-Key (MIC) wird als Auflösungswert verwendet.
    """

    suffix: str
    name: str
    region: str  # "germany" | "usa" | "europe" | "global"
    currency: str
    figi_id_type: str = "micCode"
    figi_value: str = ""


# Weltweite Börsentabelle: Key = MIC (bzw. 'US'). Erweiterbar per Zeile.
EXCHANGES: dict[str, ExchangeDef] = {
    # Amerika
    "US": ExchangeDef("", "NYSE / NASDAQ", "usa", "USD", "exchCode", "US"),
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
      `BRK.B` daraus zu machen wäre geraten.

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
        if definition.suffix == suffix and definition.figi_id_type == "micCode":
            # `figi_id_type` unterscheidet echte MICs vom Sammelcode `US`:
            # Nur die einzelnen Börsen werden über `micCode` aufgelöst.
            return (ticker, mic) if ticker else (None, None)
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
