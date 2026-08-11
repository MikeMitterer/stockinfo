# Währungen: weltweite Default-Börsen + FX-Endpoint — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** StockInfo weltweit nutzbar machen — eine pro Region konfigurierbare Default-Börse (Währung folgt aus dem Live-Quote) plus ein FX-Endpoint für gemischte Depots — jeweils mit Backend **und** Dashboard-Oberfläche.

**Architecture:** Backend-Services in `app/services/`, dünne Router in `app/routers/`, Composition-Root `app/container.py`. Frontend: Vue-3-`<script setup>`-Komponenten mit Composable je Datenquelle, Tab-Navigation über `useHashTab` + `AppHeader`. Die Börsentabelle wird die eine Quelle der Wahrheit (Backend `EXCHANGES` → `/exchanges` → datengetriebenes Panel).

**Tech Stack:** Python 3, FastAPI, Pydantic, SQLite (WAL), structlog, pytest — yfinance/OpenFIGI als Quellen. Frontend: Vue 3, TypeScript, vue-i18n, Vitest + @vue/test-utils.

## Global Constraints

- **Sprache:** Docstrings/Kommentare Deutsch, Bezeichner Englisch. Match existing style.
- **Eine ISIN = eine Zeile.** Keine Änderung der Instrument-Identität, kein Schema-Rekey.
- **Währung nie hartkodiert** — sie stammt immer aus dem Live-Quote; die `currency` in der Börsentabelle ist reine Anzeige.
- **Rückwärtskompatibilität:** Defaults reproduzieren heutiges Verhalten (`default_exchange="XETR"`, `strict_exchange=false`). Response-Felder `currency/price/quote_time/stale/fetched_at` unverändert.
- **FX-Semantik:** `rate` = wie viel `quote` für 1 `base` (`base`=von, `quote`=nach, multiplizieren). Yahoo liefert beide Richtungen direkt (`{BASE}{QUOTE}=X`).
- **i18n:** jeder neue UI-Text in `de.ts` UND `en.ts` (`de.ts` ist Schema-Quelle; `en.ts` nutzt `satisfies typeof de`).
- **TDD, DRY, YAGNI.** Test zuerst. Ein Commit je Task. Conventional Commits. Commit-Footer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Backend-Tests:** `.venv/bin/pytest`. **Frontend:** in `dashboard/`: `npm test`, `npx vue-tsc --noEmit`, `npm run build`.
- **Reihenfolge:** Stufe 1 (Tasks 1–3, 7) ist tragend; Stufe 2 (Tasks 4–6, 8) ist „nice to have" für gemischte Depots.

---

## Task 1: Weltweite `EXCHANGES`-Tabelle + OpenFIGI-Auflösung je Börse (inkl. US-Composite)

**Files:**
- Modify: `app/resolver.py` (EXCHANGES → angereicherte Tabelle, OpenFigiResolver)
- Modify: `app/providers/openfigi_provider.py` (map_isin: micCode ODER exchCode)
- Test: `tests/test_resolver.py`, `tests/test_providers.py`

**Interfaces:**
- Produces:
  - `ExchangeDef` dataclass: `suffix: str`, `name: str`, `region: str`, `currency: str`, `figi_id_type: str = "micCode"`, `figi_value: str = ""` (leer ⇒ Dict-Key wird verwendet).
  - `EXCHANGES: dict[str, ExchangeDef]` — weltweit; Key ist der MIC bzw. `"US"`.
  - `OpenFigiClient.map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None`.

- [ ] **Step 1: Failing tests** — ergänze `tests/test_resolver.py`

```python
from app.resolver import EXCHANGES, ExchangeDef, OpenFigiResolver


class _FakeFigi:
    """Zeichnet den letzten map_isin-Aufruf auf und liefert einen festen Ticker."""

    def __init__(self, ticker: str | None) -> None:
        self.ticker = ticker
        self.calls: list[tuple] = []

    def map_isin(self, isin: str, id_value: str, id_type: str = "micCode") -> str | None:
        self.calls.append((isin, id_value, id_type))
        return self.ticker


def test_tsx_bildet_punkt_to_symbol() -> None:
    figi = _FakeFigi("RY")
    resolved = OpenFigiResolver(figi, "XTSE").resolve_isin("CA7800871021")
    assert resolved is not None
    assert resolved.symbol == "RY.TO"
    assert figi.calls == [("CA7800871021", "XTSE", "micCode")]


def test_us_nutzt_exchcode_und_leeres_suffix() -> None:
    figi = _FakeFigi("AAPL")
    resolved = OpenFigiResolver(figi, "US").resolve_isin("US0378331005")
    assert resolved is not None
    assert resolved.symbol == "AAPL"  # kein Suffix
    assert figi.calls == [("US0378331005", "US", "exchCode")]


def test_unbekannte_boerse_faellt_auf_xetr_zurueck() -> None:
    figi = _FakeFigi("EUNL")
    resolved = OpenFigiResolver(figi, "NOPE").resolve_isin("IE00B4L5Y983")
    assert resolved is not None
    assert resolved.symbol == "EUNL.DE"


def test_us_ist_in_tabelle_mit_exchcode() -> None:
    assert EXCHANGES["US"].figi_id_type == "exchCode"
    assert EXCHANGES["US"].suffix == ""
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/pytest tests/test_resolver.py -v`
Expected: FAIL (`ExchangeDef` / geänderte Signatur fehlt)

- [ ] **Step 3: `app/providers/openfigi_provider.py` — map_isin verallgemeinern**

Ersetze `map_isin` durch:

```python
    def map_isin(
        self, isin: str, id_value: str, id_type: str = "micCode"
    ) -> str | None:
        """Liefert den Ticker einer ISIN an einer Börse.

        Args:
            isin: ISIN des Wertpapiers.
            id_value: Wert des Auflösungsmerkmals (z.B. 'XETR' für micCode,
                'US' für exchCode).
            id_type: OpenFIGI-Feld — 'micCode' (einzelne Börse) oder 'exchCode'
                (z.B. das US-Composite).

        Returns:
            Ticker (z.B. 'VGWL') oder ``None``, wenn kein Mapping gefunden wird.
        """
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-OPENFIGI-APIKEY"] = self._api_key
        payload = [{"idType": "ID_ISIN", "idValue": isin, id_type: id_value}]
        try:
            response = httpx.post(
                _ENDPOINT, json=payload, headers=headers, timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning(
                "openfigi_failed", isin=isin, id_type=id_type, id_value=id_value,
                error=str(exc),
            )
            return None
        return self._extract_ticker(data)
```

- [ ] **Step 4: `app/resolver.py` — ExchangeDef + Welt-Tabelle + Resolver**

Ersetze die `EXCHANGES`-Definition und `OpenFigiResolver.resolve_isin`. Neuer Kopf:

```python
from dataclasses import dataclass

import structlog
import yfinance as yf

from app.providers.base import QUOTE_TYPE_MAP, InstrumentResolver, ResolvedInstrument
from app.providers.openfigi_provider import OpenFigiClient

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
```

`OpenFigiResolver.resolve_isin` neu:

```python
    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        """Löst eine ISIN zum Yahoo-Symbol der konfigurierten Börse auf."""
        exch = EXCHANGES.get(self._default_exchange)
        if exch is None:
            logger.warning(
                "unknown_default_exchange", configured=self._default_exchange
            )
            exch = EXCHANGES[DEFAULT_EXCHANGE]
        id_value = exch.figi_value or self._default_exchange
        ticker = self._client.map_isin(isin, id_value, id_type=exch.figi_id_type)
        if not ticker:
            logger.warning(
                "openfigi_resolve_empty", isin=isin, exchange=self._default_exchange
            )
            return None
        return ResolvedInstrument(
            symbol=f"{ticker}{exch.suffix}", isin=isin, exchange=exch.name
        )
```

`OpenFigiResolver.__init__` bleibt `(client, default_exchange=DEFAULT_EXCHANGE)`. `YFinanceResolver` und `CompositeResolver` bleiben unverändert. Beachte: der Fallback in `resolve_isin` nutzt jetzt `EXCHANGES.get(...) is None` statt des früheren `EXCHANGES.get(key, EXCHANGES[DEFAULT])` (wegen der Warnung).

- [ ] **Step 5: `tests/test_providers.py` — map_isin-Aufrufe anpassen**

Falls dort `map_isin` mit alter Signatur aufgerufen wird, auf `map_isin(isin, id_value, id_type=...)` umstellen. `_extract_ticker`-Tests bleiben unverändert.

- [ ] **Step 6: Volle Suite**

Run: `.venv/bin/pytest -q`
Expected: PASS. Bestehende Resolver-Tests ggf. an `ExchangeDef` anpassen (falls sie das alte Tupel-Format annahmen).

- [ ] **Step 7: Commit**

```bash
git add app/resolver.py app/providers/openfigi_provider.py tests/test_resolver.py tests/test_providers.py
git commit -m "feat(resolver): weltweite Börsentabelle + OpenFIGI micCode/exchCode-Auflösung (US-Composite)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `strict_exchange`-Config + Resolver-Komposition + `/env`-Sichtbarkeit

**Files:**
- Modify: `app/config.py` (strict_exchange)
- Modify: `app/container.py` (Komposition nach strict-Flag)
- Modify: `app/models.py` (EnvInfo.strict_exchange), `app/routers/dashboard.py` (/env)
- Test: `tests/test_resolver.py` (oder neu `tests/test_container.py`), `tests/test_api_dashboard.py`

**Interfaces:**
- Consumes: `CompositeResolver`, `OpenFigiResolver`, `YFinanceResolver` (Task 1).
- Produces: `Settings.strict_exchange: bool = False`; `EnvInfo.strict_exchange: bool`.

- [ ] **Step 1: Failing test** — `tests/test_api_dashboard.py` ergänzen (nutzt die `client`-Fixture)

```python
def test_env_zeigt_strict_exchange(client) -> None:
    body = client.get("/env").json()
    assert "strict_exchange" in body
    assert body["strict_exchange"] is False  # Default
```

Und ein Kompositionstest gegen die **echte** Container-Funktion — neue Datei `tests/test_container.py`:

```python
from types import SimpleNamespace

from app.container import _build_resolver
from app.resolver import CompositeResolver, OpenFigiResolver


def _settings(strict: bool) -> SimpleNamespace:
    return SimpleNamespace(openfigi_api_key="", default_exchange="XETR", strict_exchange=strict)


def test_strict_hat_keinen_yahoo_fallback() -> None:
    resolver = _build_resolver(_settings(strict=True))
    assert isinstance(resolver, OpenFigiResolver)  # nur OpenFIGI, kein Fallback


def test_nicht_strict_hat_composite_mit_fallback() -> None:
    resolver = _build_resolver(_settings(strict=False))
    assert isinstance(resolver, CompositeResolver)
```

Dieser Test ruft die tatsächlich im Container verwendete Funktion `_build_resolver` auf (keine Kopie der Logik).

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/pytest tests/test_api_dashboard.py -k strict tests/test_container.py -v`
Expected: FAIL (`strict_exchange` fehlt in EnvInfo/Settings)

- [ ] **Step 3: `app/config.py`** — nach `default_exchange`:

```python
    strict_exchange: bool = False  # True = nur Default-Börse, sonst 404 (kein Fallback)
```

- [ ] **Step 4: `app/container.py`** — Resolver-Aufbau in eine testbare Funktion ziehen

Neue modulweite Funktion (oberhalb von `get_cached_quote_service`):

```python
def _build_resolver(settings: Settings) -> InstrumentResolver:
    """Baut den Resolver: strikt nur OpenFIGI, sonst mit Yahoo-Fallback."""
    figi_resolver = OpenFigiResolver(
        OpenFigiClient(settings.openfigi_api_key), settings.default_exchange
    )
    if settings.strict_exchange:
        return figi_resolver
    return CompositeResolver(figi_resolver, YFinanceResolver())
```

Und in `get_cached_quote_service` den bisherigen `CompositeResolver(...)`-Aufbau durch
`resolver = _build_resolver(settings)` ersetzen. Nötige Imports ergänzen (`Settings`,
`InstrumentResolver` aus `app.providers.base`).

- [ ] **Step 5: `app/models.py` (EnvInfo) + `app/routers/dashboard.py` (/env)**

`EnvInfo` um `strict_exchange: bool` erweitern (nach `default_exchange`). In `environment()` ergänzen: `strict_exchange=settings.strict_exchange,`.

- [ ] **Step 6: Suite**

Run: `.venv/bin/pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/config.py app/container.py app/models.py app/routers/dashboard.py tests/test_container.py tests/test_api_dashboard.py
git commit -m "feat(resolver): strict_exchange-Schalter (kein Fallback → 404) + /env

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `GET /exchanges`-Endpoint (eine Quelle der Wahrheit)

**Files:**
- Modify: `app/models.py` (ExchangeInfo, ExchangesResponse)
- Modify: `app/routers/dashboard.py` (/exchanges)
- Test: `tests/test_api_dashboard.py`

**Interfaces:**
- Produces: `ExchangeInfo{mic, suffix, name, region, currency}`; `ExchangesResponse{default_exchange, exchanges: list[ExchangeInfo]}`; Route `GET /exchanges`.

- [ ] **Step 1: Failing test** — `tests/test_api_dashboard.py`

```python
def test_exchanges_liefert_welttabelle_und_default(client) -> None:
    body = client.get("/exchanges").json()
    assert body["default_exchange"] == "XETR"
    mics = {e["mic"]: e for e in body["exchanges"]}
    assert mics["XTSE"]["suffix"] == ".TO"
    assert mics["US"]["suffix"] == ""  # kein Suffix
    assert mics["XETR"]["currency"] == "EUR"
```

- [ ] **Step 2: Run, verify fail** — `.venv/bin/pytest tests/test_api_dashboard.py -k exchanges -v` → 404.

- [ ] **Step 3: `app/models.py`**

```python
class ExchangeInfo(BaseModel):
    """Eine auflösbare Börse (aus der Backend-Tabelle)."""

    mic: str
    suffix: str
    name: str
    region: str
    currency: str


class ExchangesResponse(BaseModel):
    """Weltweite Börsentabelle + die konfigurierte Default-Börse der Instanz."""

    default_exchange: str
    exchanges: list[ExchangeInfo]
```

- [ ] **Step 4: `app/routers/dashboard.py`** — Import + Route

```python
from app.resolver import EXCHANGES
from app.models import (
    EnvInfo, ExchangeInfo, ExchangesResponse, InstrumentSummary,
    IsinUpdate, QuoteResponse, RefreshResult,
)


@router.get("/exchanges", response_model=ExchangesResponse)
def exchanges(settings: SettingsDep) -> ExchangesResponse:
    """Gibt die weltweite Börsentabelle und die konfigurierte Default-Börse zurück."""
    return ExchangesResponse(
        default_exchange=settings.default_exchange,
        exchanges=[
            ExchangeInfo(
                mic=mic, suffix=d.suffix, name=d.name, region=d.region, currency=d.currency
            )
            for mic, d in EXCHANGES.items()
        ],
    )
```

- [ ] **Step 5: Run** — `.venv/bin/pytest -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add app/models.py app/routers/dashboard.py tests/test_api_dashboard.py
git commit -m "feat(exchanges): GET /exchanges als eine Quelle der Wahrheit für Börsen

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: FX-Provider + `FxRate`-Modell + `fx_ttl_hours`-Config

**Files:**
- Modify: `app/models.py` (FxRate)
- Modify: `app/providers/yfinance_provider.py` (fetch_fx_rate)
- Modify: `app/config.py` (fx_ttl_hours)
- Test: `tests/test_providers.py`

**Interfaces:**
- Produces: `FxRate` (siehe unten); `YFinanceProvider.fetch_fx_rate(base: str, quote: str) -> float | None`; `Settings.fx_ttl_hours: int = 1`.

- [ ] **Step 1: Failing test** — `tests/test_providers.py`

```python
def test_yfinance_fetch_fx_rate(monkeypatch) -> None:
    class _FxFast:
        last_price = 1.1538
    class _FxTicker:
        fast_info = _FxFast()
    captured = {}
    def fake_ticker(symbol):
        captured["symbol"] = symbol
        return _FxTicker()
    monkeypatch.setattr(yfinance_module.yf, "Ticker", fake_ticker)

    rate = YFinanceProvider().fetch_fx_rate("EUR", "USD")

    assert rate == 1.1538
    assert captured["symbol"] == "EURUSD=X"


def test_yfinance_fetch_fx_rate_ohne_wert_gibt_none(monkeypatch) -> None:
    class _NoRate:
        fast_info = type("F", (), {"last_price": None})()
    monkeypatch.setattr(yfinance_module.yf, "Ticker", lambda s: _NoRate())
    assert YFinanceProvider().fetch_fx_rate("EUR", "USD") is None
```

- [ ] **Step 2: Run, verify fail** — `.venv/bin/pytest tests/test_providers.py -k fx_rate -v`.

- [ ] **Step 3: `app/models.py`** — FxRate

```python
class FxRate(BaseModel):
    """Ein Wechselkurs: 1 ``base`` = ``rate`` ``quote`` (base=von, quote=nach)."""

    base: str
    quote: str
    rate: float
    quote_time: str
    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str
```

- [ ] **Step 4: `app/providers/yfinance_provider.py`** — fetch_fx_rate

```python
    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        """Holt den Wechselkurs 1 base = ? quote von Yahoo (Symbol '{BASE}{QUOTE}=X').

        Returns:
            Kurs als float, oder ``None`` bei Fehler bzw. fehlendem Kurs.
        """
        symbol = f"{base}{quote}=X"
        try:
            rate = self._fast_attr(yf.Ticker(symbol).fast_info, "last_price")
        except Exception as exc:
            logger.warning("fetch_fx_failed", pair=f"{base}{quote}", error=str(exc))
            return None
        if rate is None:
            logger.warning("fetch_fx_no_rate", pair=f"{base}{quote}")
            return None
        return float(rate)
```

- [ ] **Step 5: `app/config.py`** — nach den Cache-Einstellungen:

```python
    fx_ttl_hours: int = 1  # maximales Alter eines Devisenkurses, bevor neu geholt wird
```

- [ ] **Step 6: Run** — `.venv/bin/pytest -q` → PASS.

- [ ] **Step 7: Commit**

```bash
git add app/models.py app/providers/yfinance_provider.py app/config.py tests/test_providers.py
git commit -m "feat(fx): FxRate-Modell + yfinance fetch_fx_rate + fx_ttl_hours

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: `fx_rates`-Cache + Repository + `CachedFxService`

**Files:**
- Modify: `app/db.py` (fx_rates-Tabelle im Schema)
- Modify: `app/repository.py` (get_fx_rate/save_fx_rate)
- Create: `app/services/fx_service.py` (CachedFxService, FxUnavailableError)
- Modify: `app/container.py` (get_fx_service)
- Test: `tests/test_fx_service.py` (neu)

**Interfaces:**
- Consumes: `FxRate` (Task 4), `QuoteRepository`.
- Produces: `QuoteRepository.get_fx_rate(base, quote) -> dict | None`, `save_fx_rate(base, quote, rate, quote_time, fetched_at) -> None`; `CachedFxService.get_rate(base: str, quote: str) -> FxRate`; `FxUnavailableError`; `get_fx_service() -> CachedFxService`.

- [ ] **Step 1: Failing test** — `tests/test_fx_service.py`

```python
"""Tests für den cachenden FX-Service."""

from pathlib import Path

import pytest

from app.db import init_db
from app.repository import QuoteRepository
from app.services.fx_service import CachedFxService, FxUnavailableError


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "fx.db")
    init_db(db_path)
    return QuoteRepository(db_path)


class _FakeFx:
    def __init__(self, rate: float | None) -> None:
        self.rate = rate
        self.calls = 0

    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        self.calls += 1
        return self.rate


def test_gleiche_waehrung_ist_eins_ohne_fetch(repo: QuoteRepository) -> None:
    provider = _FakeFx(None)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "EUR")
    assert result.rate == 1.0
    assert result.source == "identity"
    assert provider.calls == 0


def test_miss_holt_live_und_speichert(repo: QuoteRepository) -> None:
    provider = _FakeFx(1.15)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("eur", "usd")  # wird normalisiert
    assert result.base == "EUR" and result.quote == "USD"
    assert result.rate == 1.15 and result.cached is False
    # zweiter Aufruf → Cache, kein weiterer Fetch
    provider.rate = 999.0
    again = service.get_rate("EUR", "USD")
    assert again.rate == 1.15 and again.cached is True and provider.calls == 1


def test_fetch_fehler_mit_cache_liefert_stale(repo: QuoteRepository) -> None:
    repo.save_fx_rate("EUR", "USD", 1.10, "2020-01-01T00:00:00+00:00",
                      "2020-01-01T00:00:00+00:00")  # uralt → nicht frisch
    provider = _FakeFx(None)  # Fetch schlägt fehl
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "USD")
    assert result.rate == 1.10 and result.stale is True


def test_fetch_fehler_ohne_cache_wirft(repo: QuoteRepository) -> None:
    service = CachedFxService(_FakeFx(None), repo, ttl_hours=1)
    with pytest.raises(FxUnavailableError):
        service.get_rate("EUR", "USD")
```

- [ ] **Step 2: Run, verify fail** — `.venv/bin/pytest tests/test_fx_service.py -v`.

- [ ] **Step 3: `app/db.py`** — fx_rates ins `_SCHEMA` (wird bei jedem `init_db` idempotent angelegt)

```sql
CREATE TABLE IF NOT EXISTS fx_rates (
    base       TEXT NOT NULL,
    quote      TEXT NOT NULL,
    rate       REAL NOT NULL,
    quote_time TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (base, quote)
);
```

- [ ] **Step 4: `app/repository.py`** — FX-Methoden

```python
    def get_fx_rate(self, base: str, quote: str) -> dict | None:
        """Gibt den gecachten Wechselkurs für ein Paar zurück (oder ``None``)."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM fx_rates WHERE base = ? AND quote = ?", (base, quote)
            ).fetchone()
            return dict(row) if row else None

    def save_fx_rate(
        self, base: str, quote: str, rate: float, quote_time: str, fetched_at: str
    ) -> None:
        """Speichert/aktualisiert einen Wechselkurs (Upsert auf (base, quote))."""
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO fx_rates (base, quote, rate, quote_time, fetched_at) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (base, quote) DO UPDATE SET "
                "rate = excluded.rate, quote_time = excluded.quote_time, "
                "fetched_at = excluded.fetched_at",
                (base, quote, rate, quote_time, fetched_at),
            )
```

- [ ] **Step 5: `app/services/fx_service.py`** (neu)

```python
"""Cachende Devisenkurs-Beschaffung — Lazy-TTL über yfinance.

Analog zu CachedQuoteService: frischer Cache → nutzen; sonst frisch holen und
speichern; schlägt das Holen fehl, aber ein alter Wert liegt vor, wird dieser
als ``stale`` geliefert statt eines Fehlers.
"""

from datetime import datetime, timezone
from typing import Protocol

import structlog

from app.models import FxRate

logger = structlog.get_logger()


class FxRateProvider(Protocol):
    """Liefert einen Wechselkurs (1 base = ? quote)."""

    def fetch_fx_rate(self, base: str, quote: str) -> float | None: ...


class FxUnavailableError(Exception):
    """Es konnte kein Wechselkurs beschafft werden und kein Cache liegt vor."""


class FxRepository(Protocol):
    def get_fx_rate(self, base: str, quote: str) -> dict | None: ...
    def save_fx_rate(
        self, base: str, quote: str, rate: float, quote_time: str, fetched_at: str
    ) -> None: ...


class CachedFxService:
    """Legt einen TTL-Cache (SQLite) vor die Live-FX-Beschaffung."""

    def __init__(
        self, provider: FxRateProvider, repository: FxRepository, ttl_hours: int
    ) -> None:
        self._provider = provider
        self._repository = repository
        self._ttl_hours = ttl_hours

    def get_rate(self, base: str, quote: str) -> FxRate:
        """Liefert den Wechselkurs 1 base = ? quote (aus Cache oder frisch).

        Raises:
            FxUnavailableError: Kein Kurs beschaffbar und kein Cache vorhanden.
        """
        base, quote = base.upper(), quote.upper()
        now = datetime.now(timezone.utc).isoformat()
        if base == quote:
            return FxRate(
                base=base, quote=quote, rate=1.0, quote_time=now, source="identity",
                cached=False, stale=False, fetched_at=now,
            )

        cached = self._repository.get_fx_rate(base, quote)
        if cached and self._is_fresh(cached["fetched_at"]):
            return self._from_cache(cached, stale=False)

        rate = self._provider.fetch_fx_rate(base, quote)
        if rate is None:
            if cached:
                logger.warning("serving_stale_fx", base=base, quote=quote)
                return self._from_cache(cached, stale=True)
            raise FxUnavailableError(f"{base}{quote}")

        self._repository.save_fx_rate(base, quote, rate, now, now)
        return FxRate(
            base=base, quote=quote, rate=rate, quote_time=now, source="yfinance",
            cached=False, stale=False, fetched_at=now,
        )

    def _is_fresh(self, fetched_at: str) -> bool:
        """Prüft, ob ein Zeitstempel jünger als die TTL ist."""
        try:
            timestamp = datetime.fromisoformat(fetched_at)
        except ValueError:
            return False
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return age < self._ttl_hours * 3600

    @staticmethod
    def _from_cache(row: dict, stale: bool) -> FxRate:
        """Baut eine FxRate aus einer gespeicherten Zeile."""
        return FxRate(
            base=row["base"], quote=row["quote"], rate=row["rate"],
            quote_time=row["quote_time"], source="cache", cached=True, stale=stale,
            fetched_at=row["fetched_at"],
        )
```

- [ ] **Step 6: `app/container.py`** — Factory

```python
from app.providers.yfinance_provider import YFinanceProvider  # bereits importiert
from app.services.fx_service import CachedFxService


@lru_cache
def get_fx_service() -> CachedFxService:
    """Baut den (gecachten) CachedFxService aus der aktuellen Konfiguration."""
    settings = get_settings()
    return CachedFxService(
        YFinanceProvider(), QuoteRepository(settings.database_path), settings.fx_ttl_hours
    )
```

- [ ] **Step 7: Run** — `.venv/bin/pytest -q` → PASS.

- [ ] **Step 8: Commit**

```bash
git add app/db.py app/repository.py app/services/fx_service.py app/container.py tests/test_fx_service.py
git commit -m "feat(fx): fx_rates-Cache + CachedFxService (TTL, serve-stale)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: `GET /fx`-Endpoint

**Files:**
- Create: `app/routers/fx.py`
- Modify: `app/main.py` (Router einbinden)
- Test: `tests/test_api_fx.py` (neu)

**Interfaces:**
- Consumes: `get_fx_service`, `CachedFxService`, `FxUnavailableError`, `FxRate`.
- Produces: `GET /fx?base=&quote=` → `FxRate`.

- [ ] **Step 1: Failing test** — `tests/test_api_fx.py`

```python
"""Tests des /fx-Endpoints."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import get_fx_service
from app.main import app
from app.models import FxRate


class _StubFx:
    def get_rate(self, base: str, quote: str) -> FxRate:
        return FxRate(
            base=base.upper(), quote=quote.upper(), rate=1.15,
            quote_time="t", source="yfinance", cached=False, stale=False, fetched_at="t",
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_fx_service] = lambda: _StubFx()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_fx_liefert_rate(client: TestClient) -> None:
    body = client.get("/fx?base=EUR&quote=USD").json()
    assert body["rate"] == 1.15
    assert body["base"] == "EUR" and body["quote"] == "USD"


def test_fx_validiert_codes(client: TestClient) -> None:
    assert client.get("/fx?base=EU&quote=USD").status_code == 422
    assert client.get("/fx?base=EURO&quote=USD").status_code == 422
    assert client.get("/fx").status_code == 422  # fehlende Parameter
```

- [ ] **Step 2: Run, verify fail** — `.venv/bin/pytest tests/test_api_fx.py -v` → 404/Fehler.

- [ ] **Step 3: `app/routers/fx.py`** (neu)

```python
"""Devisenkurs-Endpoint — 1 base = rate quote (base=von, quote=nach)."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.container import get_fx_service
from app.models import FxRate
from app.services.fx_service import CachedFxService, FxUnavailableError

router = APIRouter(tags=["fx"])

FxDep = Annotated[CachedFxService, Depends(get_fx_service)]
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


@router.get("/fx", response_model=FxRate)
def fx(service: FxDep, base: str, quote: str) -> FxRate:
    """Liefert den Wechselkurs 1 base = ? quote.

    Beispiel: ``/fx?base=EUR&quote=USD`` → ~1,15 (1 EUR = 1,15 USD).
    """
    if not _CURRENCY.match(base) or not _CURRENCY.match(quote):
        raise HTTPException(
            status_code=422,
            detail="base und quote müssen 3-Buchstaben-Währungscodes sein",
        )
    try:
        return service.get_rate(base, quote)
    except FxUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Kein Wechselkurs für {base.upper()}/{quote.upper()}",
        ) from exc
```

- [ ] **Step 4: `app/main.py`** — Router einbinden

```python
from app.routers import dashboard, fx, quotes
...
app.include_router(quotes.router)
app.include_router(dashboard.router)
app.include_router(fx.router)
```

(Reihenfolge: vor `mount_dashboard`, wie die anderen Router.)

- [ ] **Step 5: Run** — `.venv/bin/pytest -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add app/routers/fx.py app/main.py tests/test_api_fx.py
git commit -m "feat(fx): GET /fx-Endpoint (Validierung, 422/502)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Frontend — Börsen datengetrieben + `strict_exchange` sichtbar

**Files:**
- Modify: `dashboard/src/types.ts` (ExchangeInfo, ExchangesResponse, EnvInfo.strict_exchange)
- Create: `dashboard/src/composables/useExchanges.ts`
- Modify: `dashboard/src/components/ExchangesPanel.vue` (datengetrieben)
- Modify: `dashboard/src/components/EnvironmentPanel.vue` (strict_exchange)
- Modify: `dashboard/src/i18n/de.ts` + `en.ts`
- Modify: `dashboard/src/App.vue` (Exchanges-Panel lädt Daten)
- Test: `dashboard/tests/composables/useExchanges.spec.ts` (neu), `dashboard/tests/components/ExchangesPanel.spec.ts` (neu)

**Interfaces:**
- Produces: `ExchangeInfo {mic,suffix,name,region,currency}`, `ExchangesResponse {default_exchange, exchanges: ExchangeInfo[]}`; `useExchanges()` → `{data, loading, error, load}`.

- [ ] **Step 1: Typen** — `dashboard/src/types.ts`

```typescript
export interface ExchangeInfo {
  mic: string
  suffix: string
  name: string
  region: string
  currency: string
}

export interface ExchangesResponse {
  default_exchange: string
  exchanges: ExchangeInfo[]
}
```

`EnvInfo` um `strict_exchange: boolean` erweitern (nach `default_exchange`).

- [ ] **Step 2: Failing test** — `dashboard/tests/composables/useExchanges.spec.ts`

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

import { useExchanges } from '../../src/composables/useExchanges'

afterEach(() => vi.unstubAllGlobals())

describe('useExchanges', () => {
  it('lädt die Börsentabelle', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ default_exchange: 'XETR', exchanges: [{ mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' }] }),
      { status: 200 },
    )))
    const { data, load } = useExchanges()
    await load()
    expect(data.value?.default_exchange).toBe('XETR')
    expect(data.value?.exchanges[0].mic).toBe('XETR')
  })
})
```

- [ ] **Step 3: Run, verify fail** — in `dashboard/`: `npm test -- useExchanges`.

- [ ] **Step 4: `dashboard/src/composables/useExchanges.ts`**

```typescript
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { translate } from '../i18n'
import type { ExchangesResponse } from '../types'

/** Lädt die weltweite Börsentabelle inkl. konfigurierter Default-Börse. */
export function useExchanges(): {
  data: Ref<ExchangesResponse | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const data = ref<ExchangesResponse | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      data.value = await apiClient.get<ExchangesResponse>('/exchanges')
    } catch (err) {
      error.value = translate('errors.exchanges')
      consola.error('useExchanges.load', err)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}
```

- [ ] **Step 5: i18n** — `de.ts`: in `errors` `exchanges: 'Börsen konnten nicht geladen werden',`; in `env` `strictExchange: 'Strikte Börse',`; in `exchanges` `default: 'Standard',` (Badge für die konfigurierte Börse). `en.ts` spiegelbildlich (`'Exchanges could not be loaded'`, `'Strict exchange'`, `'Default'`). Die vorhandenen `exchanges.*`-Keys (colSuffix, colExchange, colRegion, colCurrency, regions.*, noSuffix, standard, penceNote) bleiben.

- [ ] **Step 6: `ExchangesPanel.vue`** — datengetrieben

Ersetze die hartkodierte `exchanges`-Konstante durch die geladene Liste (Prop oder direkt via `useExchanges`). Empfohlen: Panel bekommt die Daten von `App.vue` als Prop, konsistent mit `EnvironmentPanel`:

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ExchangesResponse } from '../types'

defineProps<{ data: ExchangesResponse | null }>()
const { t } = useI18n()
</script>

<template>
  <section v-if="data" class="exchanges card">
    <h2>{{ t('exchanges.title') }}</h2>
    <p class="hint">{{ t('exchanges.hint', { example: 'GOLD.SG' }) }}</p>
    <div class="scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('exchanges.colSuffix') }}</th><th>{{ t('exchanges.colExchange') }}</th>
            <th>{{ t('exchanges.colRegion') }}</th><th>{{ t('exchanges.colCurrency') }}</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ex in data.exchanges" :key="ex.mic"
              :class="{ 'is-default': ex.mic === data.default_exchange }">
            <td class="mono suffix">{{ ex.suffix || t('exchanges.noSuffix') }}</td>
            <td>{{ ex.name }}</td>
            <td class="dim">{{ t(`exchanges.regions.${ex.region}`) }}</td>
            <td class="mono">{{ ex.currency }}</td>
            <td>
              <span v-if="ex.mic === data.default_exchange" class="badge std">{{ t('exchanges.default') }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
```

Styles: bestehende `.badge.std`/`.suffix`/`.dim` behalten; `.is-default td { background: color-mix(in srgb, $color-accent 8%, transparent); }` ergänzen. Die `region`-Werte im Backend (`germany|usa|europe|global`) decken die vorhandenen `exchanges.regions.*`-Keys ab.

- [ ] **Step 7: `App.vue`** — Exchanges-Daten laden und reichen

`useExchanges` einbinden, in `onMounted` mitladen, und `<ExchangesPanel :data="exchanges" />` statt ohne Prop rendern. `strict_exchange` fließt über das bestehende `env`-Objekt ins `EnvironmentPanel`.

- [ ] **Step 8: `EnvironmentPanel.vue`** — Zeile für `strict_exchange`

Nach der `defaultExchange`-Zeile:

```html
      <div><dt>{{ t('env.strictExchange') }}</dt><dd>{{ env.strict_exchange ? t('env.yes') : t('env.no') }}</dd></div>
```

- [ ] **Step 9: Component-Test** — `dashboard/tests/components/ExchangesPanel.spec.ts`

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ExchangesPanel from '../../src/components/ExchangesPanel.vue'
import { i18n } from '../../src/i18n'

describe('ExchangesPanel', () => {
  it('rendert Börsen und markiert die Default-Börse', () => {
    const wrapper = mount(ExchangesPanel, {
      global: { plugins: [i18n] },
      props: { data: { default_exchange: 'XETR', exchanges: [
        { mic: 'XETR', suffix: '.DE', name: 'Xetra', region: 'germany', currency: 'EUR' },
        { mic: 'US', suffix: '', name: 'NYSE / NASDAQ', region: 'usa', currency: 'USD' },
      ] } },
    })
    expect(wrapper.text()).toContain('Xetra')
    expect(wrapper.text()).toContain('NYSE / NASDAQ')
    expect(wrapper.find('tr.is-default').text()).toContain('Xetra')
  })
})
```

> Prüfe den Export der i18n-Instanz in `src/i18n/index.ts` und importiere sie im Test genauso wie andere Component-Tests.

- [ ] **Step 10: Verify** — in `dashboard/`: `npm test`, `npx vue-tsc --noEmit`, `npm run build`. Alle grün.

- [ ] **Step 11: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/composables/useExchanges.ts dashboard/src/components/ExchangesPanel.vue dashboard/src/components/EnvironmentPanel.vue dashboard/src/App.vue dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts dashboard/tests/composables/useExchanges.spec.ts dashboard/tests/components/ExchangesPanel.spec.ts
git commit -m "feat(dashboard): Börsen-Panel datengetrieben (/exchanges) + strict_exchange sichtbar

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Frontend — Devisen-Tab (`FxPanel`)

**Files:**
- Modify: `dashboard/src/types.ts` (FxRate, TabKey `'fx'`)
- Modify: `dashboard/src/api/paths.ts` (fxPath)
- Create: `dashboard/src/composables/useFx.ts`, `dashboard/src/components/FxPanel.vue`
- Modify: `dashboard/src/composables/useHashTab.ts`, `components/NavIcon.vue`, `components/AppHeader.vue`, `App.vue`
- Modify: `dashboard/src/i18n/de.ts` + `en.ts`
- Test: `dashboard/tests/api/paths.spec.ts`, `dashboard/tests/composables/useFx.spec.ts` (neu), `dashboard/tests/components/FxPanel.spec.ts` (neu)

**Interfaces:**
- Produces: `FxRate` (TS), `TabKey` + `'fx'`, `fxPath(base, quote): string`, `useFx()` → `{result, loading, error, convert}`.

- [ ] **Step 1: Typen** — `dashboard/src/types.ts`

```typescript
export interface FxRate {
  base: string
  quote: string
  rate: number
  quote_time: string
  source: string | null
  cached: boolean
  stale: boolean
  fetched_at: string
}
```

`TabKey` um `'fx'` erweitern.

- [ ] **Step 2: Failing test** — `dashboard/tests/api/paths.spec.ts`

```typescript
import { fxPath } from '../../src/api/paths'

describe('fxPath', () => {
  it('baut den /fx-Pfad mit encodeURIComponent', () => {
    expect(fxPath('EUR', 'USD')).toBe('/fx?base=EUR&quote=USD')
  })
})
```

- [ ] **Step 3: Run, verify fail** — in `dashboard/`: `npm test -- paths`.

- [ ] **Step 4: `dashboard/src/api/paths.ts`** — fxPath (anfügen)

```typescript
/**
 * Baut den /fx-Pfad für ein Währungspaar. rate = 1 base in quote.
 *
 * @param base - Ausgangswährung (von)
 * @param quote - Zielwährung (nach)
 */
export function fxPath(base: string, quote: string): string {
  return `/fx?base=${encodeURIComponent(base)}&quote=${encodeURIComponent(quote)}`
}
```

- [ ] **Step 5: Failing test** — `dashboard/tests/composables/useFx.spec.ts`

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

import { useFx } from '../../src/composables/useFx'

afterEach(() => vi.unstubAllGlobals())

describe('useFx', () => {
  it('holt den Kurs', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const { result, convert } = useFx()
    await convert('EUR', 'USD')
    expect(result.value?.rate).toBe(1.15)
  })

  it('setzt error bei Fehlschlag', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, convert } = useFx()
    await convert('EUR', 'XXX')
    expect(error.value).not.toBeNull()
  })
})
```

- [ ] **Step 6: `dashboard/src/composables/useFx.ts`**

```typescript
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { fxPath } from '../api/paths'
import { translate } from '../i18n'
import type { FxRate } from '../types'

/** Holt einen Wechselkurs (1 base = rate quote). */
export function useFx(): {
  result: Ref<FxRate | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  convert: (base: string, quote: string) => Promise<void>
} {
  const result = ref<FxRate | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function convert(base: string, quote: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      result.value = await apiClient.get<FxRate>(fxPath(base, quote))
    } catch (err) {
      error.value = translate('errors.fx')
      consola.error('useFx.convert', err)
    } finally {
      loading.value = false
    }
  }

  return { result, loading, error, convert }
}
```

- [ ] **Step 7: Tab-Verdrahtung**

- `useHashTab.ts`: `TABS` um `'fx'` erweitern.
- `NavIcon.vue`: `KNOWN_ICONS` um `'fx'`; SVG-Zweig vor dem `v-else`-Fallback (Wechsel-Pfeile):
```html
    <template v-else-if="name === 'fx'">
      <path d="M4 7h13l-3-3M20 17H7l3 3" />
    </template>
```
- `AppHeader.vue`: im `tabs`-Array `{ key: 'fx', label: t('nav.fx'), icon: 'fx' },`.

- [ ] **Step 8: `FxPanel.vue`** (neu)

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFx } from '../composables/useFx'

const { t } = useI18n()
const { result, loading, error, convert } = useFx()

const base = ref<string>('EUR')
const quote = ref<string>('USD')

function swap(): void {
  ;[base.value, quote.value] = [quote.value, base.value]
}

async function run(): Promise<void> {
  const b = base.value.trim().toUpperCase()
  const q = quote.value.trim().toUpperCase()
  if (b.length === 3 && q.length === 3) await convert(b, q)
}
</script>

<template>
  <section class="fx card">
    <h2>{{ t('fx.title') }}</h2>
    <p class="hint">{{ t('fx.hint') }}</p>

    <div class="controls">
      <input v-model="base" maxlength="3" class="code" :aria-label="t('fx.base')" />
      <button class="swap" :title="t('fx.swap')" @click="swap">⇄</button>
      <input v-model="quote" maxlength="3" class="code" :aria-label="t('fx.quote')" />
      <button :disabled="loading" @click="run">
        {{ loading ? t('fx.converting') : t('fx.convert') }}
      </button>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="result" class="result">
      <p class="rate mono">1 {{ result.base }} = {{ result.rate }} {{ result.quote }}</p>
      <dl>
        <div><dt>{{ t('fx.quoteTime') }}</dt><dd class="mono">{{ result.quote_time }}</dd></div>
        <div><dt>{{ t('fx.source') }}</dt><dd class="mono">{{ result.source }}</dd></div>
        <div><dt>{{ t('fx.status') }}</dt>
          <dd><span :class="['badge', result.stale ? 'warn' : 'std']">
            {{ result.stale ? t('fx.stale') : t('fx.fresh') }}</span></dd></div>
      </dl>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.fx {
  .hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; max-width: 72ch; }
  .controls { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
  .code { width: 5rem; text-transform: uppercase; text-align: center; padding: 0.4rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; font-family: $font-mono; }
  .swap { background: $color-surface-2; border: 1px solid $color-border; border-radius: $radius; padding: 0.4rem 0.6rem; }
  .err { color: #e5484d; }
  .rate { font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0 1rem; }
  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.9rem 1.5rem; }
  dt { color: $color-muted; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
  dd { margin: 0; }
  .badge { &.std { color: $color-accent; background: color-mix(in srgb, $color-accent 15%, transparent); }
           &.warn { color: $health-warn; background: color-mix(in srgb, $health-warn 18%, transparent); } }
}
</style>
```

- [ ] **Step 9: `App.vue`** — Render-Zweig

Import `FxPanel`, im `<template>` vor `<ThemesPanel v-else />`:
```html
    <FxPanel v-else-if="activeTab === 'fx'" />
```

- [ ] **Step 10: i18n** — de.ts + en.ts

de.ts: `nav.fx: 'Devisen'`; `errors.fx: 'Wechselkurs konnte nicht geladen werden'`; neuer Block:
```typescript
  fx: {
    title: 'Devisen',
    hint: 'Wechselkurs 1 Basis = x Ziel. Beispiel: EUR→USD ≈ 1,15.',
    base: 'Basiswährung', quote: 'Zielwährung', swap: 'Tauschen',
    convert: 'Umrechnen', converting: 'Hole…',
    quoteTime: 'Kurszeit', source: 'Quelle', status: 'Status',
    fresh: 'aktuell', stale: 'veraltet',
  },
```
en.ts spiegelbildlich (`nav.fx: 'FX'`, `errors.fx: 'Exchange rate could not be loaded'`, `fx: { title: 'FX', hint: 'Rate 1 base = x quote. Example: EUR→USD ≈ 1.15.', base: 'Base', quote: 'Quote', swap: 'Swap', convert: 'Convert', converting: 'Fetching…', quoteTime: 'Quote time', source: 'Source', status: 'Status', fresh: 'fresh', stale: 'stale' }`).

- [ ] **Step 11: Component-Test** — `dashboard/tests/components/FxPanel.spec.ts`

```typescript
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({ consola: { error: vi.fn() } }))
import FxPanel from '../../src/components/FxPanel.vue'
import { i18n } from '../../src/i18n'

afterEach(() => vi.unstubAllGlobals())

describe('FxPanel', () => {
  it('zeigt den Kurs nach dem Umrechnen', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ base: 'EUR', quote: 'USD', rate: 1.15, quote_time: 't', source: 'yfinance', cached: false, stale: false, fetched_at: 't' }),
      { status: 200 },
    )))
    const wrapper = mount(FxPanel, { global: { plugins: [i18n] } })
    await wrapper.find('button:last-of-type').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('1 EUR = 1.15 USD')
  })
})
```

- [ ] **Step 12: Verify** — in `dashboard/`: `npm test`, `npx vue-tsc --noEmit`, `npm run build`. Alle grün.

- [ ] **Step 13: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/api/paths.ts dashboard/src/composables/useFx.ts dashboard/src/components/FxPanel.vue dashboard/src/composables/useHashTab.ts dashboard/src/components/NavIcon.vue dashboard/src/components/AppHeader.vue dashboard/src/App.vue dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts dashboard/tests/api/paths.spec.ts dashboard/tests/composables/useFx.spec.ts dashboard/tests/components/FxPanel.spec.ts
git commit -m "feat(dashboard): Devisen-Tab (FxPanel) über /fx

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Abschluss-Verifikation

- [ ] Backend: `.venv/bin/pytest -q` → grün.
- [ ] Frontend (in `dashboard/`): `npm test && npx vue-tsc --noEmit && npm run build`.
- [ ] E2E (verify-Skill falls vorhanden): App starten; im Dashboard den Börsen-Tab öffnen (weltweite Liste, Default markiert), den Devisen-Tab EUR→USD rechnen (Kurs + Zeit + Frisch-Badge), und mit `DEFAULT_EXCHANGE=US` bzw. `STRICT_EXCHANGE=true` per Env eine US-Instanz gegenchecken (Kurse in USD; unbekannte Notierung → 404 statt Ersatzwährung).

## Self-Review (beim Schreiben durchgeführt)

- **Spec-Coverage:** Stufe 1 (Task 1 Welt-Tabelle/US, Task 2 strict+config+/env, Task 3 /exchanges, Task 7 UI), Stufe 2 (Task 4 Provider/Modell/config, Task 5 Cache/Service, Task 6 Endpoint, Task 8 UI). FX-Semantik, „eine ISIN eine Zeile", Rückwärtskompatibilität, i18n de+en berücksichtigt.
- **Platzhalter:** keine; der einzige Live-zu-verifizierende Punkt (OpenFIGI-US-Composite-Feld) ist in Task 1 mit Fake-Test abgedeckt und in der Abschluss-Verifikation als Live-Check benannt.
- **Typkonsistenz:** `ExchangeDef`, `map_isin(isin, id_value, id_type)`, `FxRate`, `CachedFxService.get_rate`, `fxPath(base, quote)`, `useFx.convert`, `ExchangeInfo`/`ExchangesResponse` durchgängig gleich benannt in Definition und Verwendung.
