"""Per-Stage-Timing des Live-Fetch — im Unraid-Container ausführen.

Zeigt, welcher externe Call die Sekunden frisst (OpenFIGI, yfinance, justETF).

Nutzung:
    docker cp probe.py stockinfo:/probe.py
    docker exec -it stockinfo python /probe.py [ISIN] [SYMBOL]

Default: IE00B4L5Y983 / EUNL.DE (iShares Core MSCI World).
"""
import sys
import time

ISIN = sys.argv[1] if len(sys.argv) > 1 else "IE00B4L5Y983"
SYM = sys.argv[2] if len(sys.argv) > 2 else "EUNL.DE"


def lap(label: str, since: float) -> float:
    """Gibt die vergangene Zeit seit ``since`` aus und liefert den neuen Zeitpunkt."""
    now = time.perf_counter()
    print(f"{label:26s} {now - since:7.2f}s", flush=True)
    return now


t0 = time.perf_counter()
import httpx
import yfinance as yf
import justetf_scraping

t = lap("import", t0)

# 1. OpenFIGI: ISIN -> Ticker (Xetra)
try:
    response = httpx.post(
        "https://api.openfigi.com/v3/mapping",
        json=[{"idType": "ID_ISIN", "idValue": ISIN, "micCode": "XETR"}],
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    print("   openfigi:", response.status_code, flush=True)
except Exception as exc:
    print("   openfigi ERR:", type(exc).__name__, exc, flush=True)
t = lap("openfigi map_isin", t)

# 2. yfinance: die drei Calls aus fetch_quote
ticker = yf.Ticker(SYM)
for name in ("fast_info.last_price", "get_info", "isin"):
    try:
        if name == "fast_info.last_price":
            ticker.fast_info.last_price
        elif name == "get_info":
            ticker.get_info()
        else:
            _ = ticker.isin
    except Exception as exc:
        print(f"   {name} ERR:", type(exc).__name__, exc, flush=True)
    t = lap(name, t)

# 3. yfinance: Historie für die Volatilitaets-Berechnung
try:
    history = ticker.history(start="2025-08-01", interval="1d", auto_adjust=True)
    print("   history rows:", len(history), flush=True)
except Exception as exc:
    print("   history ERR:", type(exc).__name__, exc, flush=True)
t = lap("history(1y)", t)

# 4. justETF-Scraping (ETF-Anreicherung)
try:
    overview = justetf_scraping.get_etf_overview(ISIN)
    print("   justetf:", "OK" if overview else "leer", flush=True)
except Exception as exc:
    print("   justetf ERR:", type(exc).__name__, exc, flush=True)
t = lap("justetf overview", t)

print(f"{'TOTAL':26s} {time.perf_counter() - t0:7.2f}s", flush=True)
