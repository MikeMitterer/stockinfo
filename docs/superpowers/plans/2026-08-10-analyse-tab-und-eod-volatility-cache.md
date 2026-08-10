# Analyse-Tab + Volatilität aus akkumulierendem EOD-Cache — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Einen On-Demand-Analyse-Menüpunkt (Stage-Timing pro Asset) ins Dashboard bringen und die 1-Jahres-Volatilität aus dem bestehenden, inkrementell akkumulierenden `daily_closes`-Cache berechnen statt bei jedem Kurs-Fetch neu von yfinance zu laden.

**Architecture:** Backend-Services in `app/services/`, dünne Router in `app/routers/`, Composition-Root in `app/container.py`. Frontend: Vue-3-`<script setup>`-Komponenten mit Composables je Datenquelle, Tab-Navigation über `useHashTab` + `AppHeader`. Die inkrementelle EOD-Sync-Logik wird in eine gemeinsam nutzbare `DailyCloseSync`-Einheit gezogen, die sowohl `DailyHistoryService` als auch `CachedQuoteService` verwenden.

**Tech Stack:** Python 3, FastAPI, Pydantic, SQLite (WAL), structlog, pytest — yfinance/justETF/OpenFIGI als externe Quellen. Frontend: Vue 3, TypeScript, vue-i18n, Vitest + @vue/test-utils.

## Global Constraints

- **Sprache:** Alle Docstrings, Kommentare und User-facing-Texte auf Deutsch; Code-Bezeichner Englisch (bestehende Konvention).
- **Bash-Variablen** (nur falls Scripts berührt werden): GROSS, `local -r`/`readonly` wo möglich.
- **i18n:** Jeder neue UI-Text als Key in **`de.ts` UND `en.ts`** — `de.ts` ist die Schema-Quelle.
- **DRY/YAGNI/TDD:** Test zuerst, kein Duplizieren der Sync-Logik, kein Feature über den Spec hinaus.
- **Commits:** Conventional Commits, häufig, ein Commit je Task. Commit-Footer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- **Backend-Tests:** `.venv/bin/pytest`. **Frontend-Tests:** `npm test` im `dashboard/`-Verzeichnis (`vitest run`).
- **Abhängigkeitsrichtung:** `DailyHistoryService` → `CachedQuoteService` besteht bereits; `CachedQuoteService` darf NICHT von `DailyHistoryService` abhängen. Gemeinsame Logik nur über `DailyCloseSync`.

---

## Teil B — Volatilität aus akkumulierendem EOD-Cache

### Task 1: `DailyCloseSync` extrahieren, `DailyHistoryService` darauf umstellen

**Files:**
- Create: `app/services/daily_sync.py`
- Modify: `app/services/daily_history.py`
- Test: `tests/test_daily_sync.py` (neu)
- Verify unchanged: `tests/test_daily_history.py` (muss ohne Änderung grün bleiben)

**Interfaces:**
- Produces:
  - `class DailyCloseProvider(Protocol)` mit `fetch_daily_closes(symbol: str, start: str | None = None) -> list[dict] | None` (aus `daily_history.py` hierher verschoben).
  - `class DailyCloseSync` mit `__init__(self, repository: QuoteRepository, provider: DailyCloseProvider)` und `sync(self, instrument_id: int, symbol: str, desired_start: str | None) -> bool`. Rückgabe `False` nur, wenn noch nie abgefragt wurde **und** der Erst-Fetch fehlschlägt (kein Cache vorhanden); sonst `True`.

- [ ] **Step 1: Failing test schreiben** — `tests/test_daily_sync.py`

```python
"""Tests für die gemeinsame inkrementelle EOD-Sync-Einheit."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "sync.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _seed(repo: QuoteRepository) -> dict:
    repo.save_quote(
        QuoteResponse(
            isin="IE00B3RBWM25", symbol="VGWL.DE", currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="etf",
        )
    )
    return repo.get_instrument_by_isin("IE00B3RBWM25")


class FakeProvider:
    def __init__(self, rows: list[dict] | None) -> None:
        self.calls: list[str | None] = []
        self._rows = rows

    def fetch_daily_closes(self, symbol: str, start: str | None = None):
        self.calls.append(start)
        return self._rows


def test_sync_holt_bei_leerem_cache_und_setzt_wasserzeichen(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)

    start = (date.today() - timedelta(days=370)).isoformat()
    assert sync.sync(inst["id"], inst["symbol"], start) is True
    assert repo.get_daily_meta(inst["id"]) is not None
    assert len(repo.get_daily_closes(inst["id"])) == 1


def test_sync_meldet_false_bei_fehlgeschlagenem_erstabruf(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    sync = DailyCloseSync(repo, FakeProvider(None))  # Provider-Fehler
    assert sync.sync(inst["id"], inst["symbol"], None) is False
    assert repo.get_daily_meta(inst["id"]) is None


def test_sync_holt_beim_zweiten_lauf_nur_das_delta(repo: QuoteRepository) -> None:
    inst = _seed(repo)
    provider = FakeProvider([{"date": "2026-07-11", "close": 161.0, "currency": "EUR"}])
    sync = DailyCloseSync(repo, provider)
    start = (date.today() - timedelta(days=370)).isoformat()

    sync.sync(inst["id"], inst["symbol"], start)
    provider.calls.clear()
    sync.sync(inst["id"], inst["symbol"], start)  # gleicher Zeitraum, Cache aktuell genug

    # nur ein Delta-Fetch (fetched_to < heute), nicht erneut die volle Historie
    assert provider.calls == [repo.get_daily_meta(inst["id"])["fetched_to"]] or provider.calls == []
```

- [ ] **Step 2: Test ausführen, Fehlschlag bestätigen**

Run: `.venv/bin/pytest tests/test_daily_sync.py -v`
Expected: FAIL mit `ModuleNotFoundError: app.services.daily_sync`

- [ ] **Step 3: `app/services/daily_sync.py` implementieren**

```python
"""Inkrementelle EOD-Synchronisation — gemeinsam genutzte Einheit.

Zieht fehlende Tages-Schlusskurse anhand der Fetch-Wasserzeichen nach und
speichert sie im akkumulierenden ``daily_closes``-Cache. Wird sowohl vom
``DailyHistoryService`` (Chart-Historie) als auch vom ``CachedQuoteService``
(Volatilität) verwendet — daher zustandslos und ohne Kenntnis der Aufrufer.
"""

from datetime import date
from typing import Protocol

import structlog

from app.repository import QuoteRepository

logger = structlog.get_logger()


class DailyCloseProvider(Protocol):
    """Liefert echte Tages-Schlusskurse zu einem Symbol.

    ``None`` signalisiert einen Fehler (Netz, Rate-Limit); eine leere Liste
    bedeutet 'erfolgreich abgefragt, aber keine Daten vorhanden'.
    """

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None: ...


class DailyCloseSync:
    """Synchronisiert den ``daily_closes``-Cache inkrementell (nur fehlende Tage)."""

    def __init__(self, repository: QuoteRepository, provider: DailyCloseProvider) -> None:
        """
        Args:
            repository: SQLite-Persistenz (daily_closes, daily_meta).
            provider: Quelle für echte EOD-Kurse (yfinance).
        """
        self._repository = repository
        self._provider = provider

    def sync(self, instrument_id: int, symbol: str, desired_start: str | None) -> bool:
        """Lädt nur fehlende Tage nach — anhand der Fetch-Wasserzeichen.

        ``fetched_to`` = bis wann bereits abgefragt, ``fetched_from`` = ab wann
        (``None`` = gesamte Historie). Wasserzeichen werden nur nach einem
        **erfolgreichen** Fetch fortgeschrieben — ein Provider-Fehler hinterlässt
        keine dauerhafte Datenlücke.

        Returns:
            ``False`` nur, wenn noch nie abgefragt wurde und der Erst-Fetch
            fehlschlägt (kein Cache vorhanden); sonst ``True``.
        """
        today = date.today().isoformat()
        meta = self._repository.get_daily_meta(instrument_id)

        if meta is None:  # noch nie abgefragt → gesamten Zeitraum holen
            if not self._fetch_and_store(instrument_id, symbol, desired_start):
                return False
            self._repository.set_daily_meta(instrument_id, desired_start, today)
            return True

        fetched_from = meta["fetched_from"]
        fetched_to = meta["fetched_to"]

        if fetched_to is None or fetched_to < today:  # neue Tage seither
            if self._fetch_and_store(instrument_id, symbol, fetched_to):
                fetched_to = today

        if fetched_from is not None:  # gesamte Historie noch nicht geholt
            if desired_start is None:  # 'max' verlangt → alles holen
                if self._fetch_and_store(instrument_id, symbol, None):
                    fetched_from = None
            elif desired_start < fetched_from:  # weiter zurück verlangt
                if self._fetch_and_store(instrument_id, symbol, desired_start):
                    fetched_from = desired_start

        self._repository.set_daily_meta(instrument_id, fetched_from, fetched_to)
        return True

    def _fetch_and_store(
        self, instrument_id: int, symbol: str, start: str | None
    ) -> bool:
        """Holt EOD-Kurse ab ``start`` und schreibt sie in den Cache.

        Returns:
            True bei erfolgreichem Fetch (auch ohne neue Zeilen), False wenn
            der Provider einen Fehler signalisiert.
        """
        rows = self._provider.fetch_daily_closes(symbol, start=start)
        if rows is None:
            logger.warning("daily_sync_failed", symbol=symbol, start=start)
            return False
        self._repository.upsert_daily_closes(instrument_id, rows)
        logger.debug("daily_synced", symbol=symbol, start=start, rows=len(rows))
        return True
```

- [ ] **Step 4: `DailyHistoryService` auf `DailyCloseSync` umstellen** — `app/services/daily_history.py`

Der öffentliche Konstruktor bleibt `(repository, provider, quotes)` (keine Test-Churn). Intern wird eine `DailyCloseSync` gebaut und `_sync`/`_fetch_and_store` entfallen. Ersetze den Datei-Inhalt durch:

```python
"""Langfrist-Historie — echte Tages-Schlusskurse (yfinance), inkrementell gecacht.

Die erste Anfrage holt die Historie von yfinance und legt sie in SQLite ab.
Folgende Anfragen liefern aus dem Cache und laden nur die Differenz (neue bzw.
fehlende Tage) nach — nicht jede Anfrage landet bei yfinance.
"""

from datetime import date, timedelta

import structlog

from app.models import DailyPoint
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseProvider, DailyCloseSync
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import QuoteUnavailableError

logger = structlog.get_logger()

# Zeitraum-Kürzel → Anzahl Tage rückwärts ('max' = alles)
_PERIOD_DAYS = {"1w": 7, "1m": 31, "3m": 93, "1y": 366}


class DailyHistoryService:
    """Liefert Tages-Schlusskurse über einen Zeitraum, inkrementell gecacht."""

    def __init__(
        self,
        repository: QuoteRepository,
        provider: DailyCloseProvider,
        quotes: CachedQuoteService,
    ) -> None:
        """
        Args:
            repository: SQLite-Persistenz (daily_closes).
            provider: Quelle für echte EOD-Kurse (yfinance).
            quotes: Dienst, um ein Instrument bei Bedarf erst anzulegen.
        """
        self._repository = repository
        self._sync = DailyCloseSync(repository, provider)
        self._quotes = quotes

    def get_daily(
        self,
        *,
        isin: str | None = None,
        symbol: str | None = None,
        period: str = "1m",
    ) -> list[DailyPoint]:
        """Gibt die Tages-Schlusskurse für den Zeitraum zurück.

        Raises:
            QuoteUnavailableError: Instrument unbekannt und nicht beschaffbar,
                oder Erst-Abruf der Historie fehlgeschlagen.
        """
        instrument = self._quotes.ensure_instrument(isin=isin, symbol=symbol)
        desired_start = self._period_start(period)
        if not self._sync.sync(instrument["id"], instrument["symbol"], desired_start):
            raise QuoteUnavailableError(instrument["symbol"])
        rows = self._repository.get_daily_closes(instrument["id"], desired_start)
        return [
            DailyPoint(date=row["date"], close=row["close"], currency=row["currency"])
            for row in rows
        ]

    @staticmethod
    def _period_start(period: str) -> str | None:
        """Berechnet das Startdatum zu einem Zeitraum-Kürzel ('max' = None)."""
        if period == "max":
            return None
        days = _PERIOD_DAYS.get(period, 31)
        return (date.today() - timedelta(days=days)).isoformat()
```

- [ ] **Step 5: Beide Test-Suites ausführen**

Run: `.venv/bin/pytest tests/test_daily_sync.py tests/test_daily_history.py -v`
Expected: PASS (neue Sync-Tests grün, bestehende History-Tests unverändert grün)

- [ ] **Step 6: Commit**

```bash
git add app/services/daily_sync.py app/services/daily_history.py tests/test_daily_sync.py
git commit -m "refactor(daily): inkrementelle EOD-Sync in wiederverwendbare DailyCloseSync ziehen

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Volatilität aus dem Cache berechnen, aus `QuoteService` entfernen

**Files:**
- Modify: `app/services/quote_service.py` (Volatilität raus, `annualized_volatility` bleibt)
- Modify: `app/repository.py` (neue Methode `set_volatility`)
- Modify: `app/services/quote_cache.py` (Volatilität aus Cache im Refresh-Pfad)
- Modify: `app/container.py` (Verdrahtung `DailyCloseSync` → `CachedQuoteService`)
- Modify: `tests/test_quote_service.py` (closes-basierten Test entfernen)
- Test: `tests/test_quote_cache.py` (neue Volatilitäts-Tests)

**Interfaces:**
- Consumes: `DailyCloseSync.sync(...)` (Task 1), `annualized_volatility(closes: list[float]) -> float | None` (bestehend in `quote_service.py`).
- Produces:
  - `QuoteRepository.set_volatility(self, instrument_id: int, volatility: float) -> None`
  - `CachedQuoteService.__init__(self, quote_service, repository, ttl_hours, daily_sync: DailyCloseSync)` (neuer Parameter `daily_sync`).

- [ ] **Step 1: Failing test schreiben** — Ergänze `tests/test_quote_cache.py` um zwei Tests

```python
from datetime import date, timedelta

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import annualized_volatility


class _FakeDailyProvider:
    """Liefert feste Tages-Schlusskurse für die Volatilitätsberechnung."""

    def __init__(self, closes: list[float]) -> None:
        self._closes = closes

    def fetch_daily_closes(self, symbol: str, start: str | None = None):
        return [
            {"date": f"2026-01-{i + 1:02d}", "close": c, "currency": "EUR"}
            for i, c in enumerate(self._closes)
        ]


class _StockQuoteService:
    """Minimaler QuoteService-Stub: liefert eine Aktien-Antwort ohne Volatilität."""

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        return QuoteResponse(
            isin=isin, symbol="AAPL.DE", currency="EUR", price=100.0,
            quote_time="2026-07-13T10:00:00+00:00",
            fetched_at="2026-07-13T10:00:00+00:00", type="stock", volatility=None,
        )


def test_refresh_one_berechnet_volatilitaet_aus_cache(tmp_path) -> None:
    db_path = str(tmp_path / "vola.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    closes = [100.0, 101.0, 99.5, 102.0, 100.5, 103.0, 101.5]
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider(closes))
    service = CachedQuoteService(_StockQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("US0378331005")

    assert result.volatility == annualized_volatility(closes)
    stored = repo.get_instrument_by_isin("US0378331005")
    assert stored["volatility"] == result.volatility


def test_refresh_behaelt_justetf_volatilitaet(tmp_path) -> None:
    """Liefert der QuoteService bereits eine Volatilität (justETF), wird sie nicht überschrieben."""

    class _EtfQuoteService:
        def get_quote_by_isin(self, isin: str) -> QuoteResponse:
            return QuoteResponse(
                isin=isin, symbol="VGWL.DE", currency="EUR", price=160.0,
                quote_time="2026-07-13T10:00:00+00:00",
                fetched_at="2026-07-13T10:00:00+00:00", type="etf", volatility=9.95,
            )

    db_path = str(tmp_path / "vola2.db")
    init_db(db_path)
    repo = QuoteRepository(db_path)
    daily_sync = DailyCloseSync(repo, _FakeDailyProvider([100.0, 200.0, 50.0, 300.0, 80.0]))
    service = CachedQuoteService(_EtfQuoteService(), repo, ttl_hours=6, daily_sync=daily_sync)

    result = service.refresh_one("IE00B3RBWM25")

    assert result.volatility == 9.95  # justETF-Wert bleibt
```

- [ ] **Step 2: Test ausführen, Fehlschlag bestätigen**

Run: `.venv/bin/pytest tests/test_quote_cache.py -k volatilitaet -v`
Expected: FAIL — `CachedQuoteService.__init__() got an unexpected keyword argument 'daily_sync'`

- [ ] **Step 3: `QuoteRepository.set_volatility` ergänzen** — `app/repository.py` (nach `set_isin` einfügen)

```python
    def set_volatility(self, instrument_id: int, volatility: float) -> None:
        """Aktualisiert gezielt die Volatilität eines Instruments."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE instruments SET volatility = ? WHERE id = ?",
                (volatility, instrument_id),
            )
```

- [ ] **Step 4: Volatilität aus `QuoteService._build` entfernen** — `app/services/quote_service.py`

Ändere das Ende von `_build` von:

```python
        if instrument_type == "etf" and isin:
            self._enrich_etf(response, isin)

        # Volatilität aus Tages-Schlusskursen berechnen, wenn justETF keine
        # liefert (Aktien generell, ETFs ohne justETF-Wert).
        if response.volatility is None:
            response.volatility = self._compute_volatility(resolved.symbol)
        return response
```

zu:

```python
        if instrument_type == "etf" and isin:
            self._enrich_etf(response, isin)
        return response
```

Entferne die gesamte Methode `_compute_volatility` (Zeilen ~162–186). Behalte die Funktion `annualized_volatility` (wird von der Cache-Schicht genutzt). Passe den Import an: `from datetime import datetime, timezone` (`timedelta` entfällt).

- [ ] **Step 5: Volatilität im Refresh-Pfad von `CachedQuoteService` berechnen** — `app/services/quote_cache.py`

Ergänze die Imports:

```python
from datetime import date, datetime, timedelta, timezone

from app.services.daily_sync import DailyCloseSync
from app.services.quote_service import (
    InstrumentNotFoundError,
    QuoteService,
    QuoteUnavailableError,
    annualized_volatility,
)
```

Erweitere den Konstruktor um `daily_sync`:

```python
    def __init__(
        self,
        quote_service: QuoteService,
        repository: QuoteRepository,
        ttl_hours: int,
        daily_sync: DailyCloseSync,
    ) -> None:
        self._quote_service = quote_service
        self._repository = repository
        self._ttl_hours = ttl_hours
        self._daily_sync = daily_sync
        self._refresh_lock = threading.Lock()
```

Füge zwei Methoden hinzu und lasse die Refresh-Pfade sie nutzen:

```python
    def _save_fresh_with_volatility(self, fresh: QuoteResponse) -> QuoteResponse:
        """Persistiert einen frischen Kurs und ergänzt die Volatilität aus dem Cache.

        Nur wenn der Kurs selbst keine Volatilität mitbringt (justETF liefert für
        ETFs bereits eine — die bleibt bevorzugt). Wird ausschließlich im
        Refresh-Pfad aufgerufen, damit der lesende Request-Pfad schlank bleibt.
        """
        instrument_id = self._repository.save_quote(fresh)
        if fresh.volatility is None:
            volatility = self._volatility_from_cache(instrument_id, fresh.symbol)
            if volatility is not None:
                fresh.volatility = volatility
                self._repository.set_volatility(instrument_id, volatility)
        return fresh

    def _volatility_from_cache(self, instrument_id: int, symbol: str) -> float | None:
        """Berechnet die 1-Jahres-Volatilität aus dem akkumulierenden EOD-Cache.

        Zieht zunächst das Delta nach (nur fehlende Tage) und rechnet dann über
        die letzten ~370 Tage. Best-effort: fehlende/zu wenige Daten → ``None``.
        """
        start = (date.today() - timedelta(days=370)).isoformat()
        self._daily_sync.sync(instrument_id, symbol, start)
        rows = self._repository.get_daily_closes(instrument_id, start)
        closes = [row["close"] for row in rows if row.get("close") is not None]
        return annualized_volatility(closes)
```

Ersetze in `_refresh_all_locked`, `refresh_one` und `refresh_one_by_symbol` die Aufrufe von `self._save_fresh(...)` durch `self._save_fresh_with_volatility(...)`. Der lesende Pfad `_get` behält `self._save_fresh(...)` (kein Volatilitäts-Fetch im Request).

Konkret:
- `_refresh_all_locked`: `self._save_fresh(self._fetch_live(instrument))` → `self._save_fresh_with_volatility(self._fetch_live(instrument))`
- `refresh_one`: `return self._save_fresh(self._quote_service.get_quote_by_isin(isin))` → `return self._save_fresh_with_volatility(self._quote_service.get_quote_by_isin(isin))`
- `refresh_one_by_symbol`: analog mit `get_quote_by_symbol`

- [ ] **Step 6: Container-Verdrahtung** — `app/container.py`

Ergänze den Import und baue `DailyCloseSync`:

```python
from app.services.daily_sync import DailyCloseSync
```

In `get_cached_quote_service`, direkt vor dem `return`:

```python
    repository = QuoteRepository(settings.database_path)
    daily_sync = DailyCloseSync(repository, YFinanceProvider())
    return CachedQuoteService(
        quote_service, repository, settings.cache_ttl_hours, daily_sync
    )
```

- [ ] **Step 7: closes-basierten QuoteService-Test entfernen** — `tests/test_quote_service.py`

Entferne die Klasse `FakeDailyQuoteProvider` (Zeilen ~34–45) und den Test `test_volatilitaet_wird_aus_tageskursen_berechnet_wenn_justetf_fehlt` (Zeilen ~169–188) — dieses Verhalten liegt jetzt in `CachedQuoteService` (getestet in Task 2, Step 1). Behalte `test_etf_uebernimmt_volatilitaet_und_thesaurierend_von_justetf` und `test_annualized_volatility_zu_wenig_daten_ist_none`.

- [ ] **Step 8: Gesamte Backend-Suite ausführen**

Run: `.venv/bin/pytest -q`
Expected: PASS (inkl. `test_refresh.py`, `test_api_dashboard.py`, `test_daily_history.py`).
Falls `test_refresh.py` `CachedQuoteService` direkt konstruiert: dort den `daily_sync`-Parameter ergänzen (mit einem Fake-Provider oder `DailyCloseSync(repo, <fake>)`).

- [ ] **Step 9: Commit**

```bash
git add app/services/quote_service.py app/services/quote_cache.py app/repository.py app/container.py tests/test_quote_service.py tests/test_quote_cache.py
git commit -m "feat(volatility): Volatilität aus akkumulierendem EOD-Cache statt pro Fetch neu laden

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Teil A — Analyse-Tab

### Task 3: `AnalyzeResult`/`AnalyzeStage`-Modelle + `QuoteAnalyzer`-Service

**Files:**
- Modify: `app/models.py` (neue Modelle)
- Create: `app/services/analyzer.py`
- Modify: `app/container.py` (`get_quote_analyzer`)
- Test: `tests/test_analyzer.py` (neu)

**Interfaces:**
- Produces:
  - `AnalyzeStage(BaseModel)`: `stage: str`, `seconds: float`, `status: str` (`"ok"|"error"|"empty"|"skipped"`), `detail: str | None = None`.
  - `AnalyzeResult(BaseModel)`: `symbol: str`, `isin: str | None = None`, `total: float`, `stages: list[AnalyzeStage]`.
  - `QuoteAnalyzer.__init__(self, resolver: InstrumentResolver, etf_provider: EtfEnricher, ticker_factory=yf.Ticker)` und `analyze(self, *, isin: str | None = None, symbol: str | None = None) -> AnalyzeResult`.
- Consumes: `InstrumentResolver`, `EtfEnricher` (aus `app.providers.base`).

- [ ] **Step 1: Modelle ergänzen** — `app/models.py` (ans Dateiende)

```python
class AnalyzeStage(BaseModel):
    """Eine gemessene Stage des Live-Fetch (Diagnose)."""

    stage: str = Field(description="openfigi | fast_info | get_info | isin | history | justetf")
    seconds: float
    status: str = Field(description="ok | error | empty | skipped")
    detail: str | None = None


class AnalyzeResult(BaseModel):
    """Timing-Aufschlüsselung eines Live-Fetch für ein Wertpapier."""

    symbol: str
    isin: str | None = None
    total: float
    stages: list[AnalyzeStage]
```

- [ ] **Step 2: Failing test schreiben** — `tests/test_analyzer.py`

```python
"""Tests für den QuoteAnalyzer (externe Calls über Fakes)."""

from app.providers.base import EtfDetails, ResolvedInstrument
from app.services.analyzer import QuoteAnalyzer


class _FakeResolver:
    def __init__(self, resolved: ResolvedInstrument | None) -> None:
        self._resolved = resolved

    def resolve_isin(self, isin: str) -> ResolvedInstrument | None:
        return self._resolved


class _FakeEtf:
    def __init__(self, details: EtfDetails | None) -> None:
        self._details = details

    def fetch_etf(self, isin: str) -> EtfDetails | None:
        return self._details


class _FakeFastInfo:
    last_price = 128.6
    currency = "EUR"


class _FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.fast_info = _FakeFastInfo()
        self.isin = "IE00B4L5Y983"

    def get_info(self) -> dict:
        return {"longName": "Test ETF"}

    def history(self, **kwargs):
        return [1, 2, 3]  # len() = "3 rows"


def _analyzer(resolved=None, details=None) -> QuoteAnalyzer:
    return QuoteAnalyzer(
        _FakeResolver(resolved or ResolvedInstrument(symbol="EUNL.DE", type="etf")),
        _FakeEtf(details or EtfDetails(ter=0.2)),
        ticker_factory=_FakeTicker,
    )


def test_analyze_per_isin_liefert_alle_stages() -> None:
    result = _analyzer().analyze(isin="IE00B4L5Y983")
    stages = {s.stage: s for s in result.stages}
    assert set(stages) >= {"openfigi", "fast_info", "get_info", "isin", "history", "justetf"}
    assert stages["openfigi"].status == "ok"
    assert stages["history"].detail == "3 rows"
    assert result.symbol == "EUNL.DE"
    assert result.total >= 0.0


def test_analyze_per_symbol_ueberspringt_openfigi() -> None:
    result = _analyzer().analyze(symbol="AAPL")
    stages = {s.stage: s for s in result.stages}
    assert stages["openfigi"].status == "skipped"
    assert stages["fast_info"].status == "ok"


def test_stage_fehler_bricht_kette_nicht_ab() -> None:
    class _BoomTicker(_FakeTicker):
        def get_info(self) -> dict:
            raise RuntimeError("boom")

    analyzer = QuoteAnalyzer(
        _FakeResolver(ResolvedInstrument(symbol="EUNL.DE", type="etf")),
        _FakeEtf(None),
        ticker_factory=_BoomTicker,
    )
    result = analyzer.analyze(isin="IE00B4L5Y983")
    stages = {s.stage: s for s in result.stages}
    assert stages["get_info"].status == "error"
    assert stages["get_info"].detail == "RuntimeError"
    assert stages["isin"].status == "ok"  # Kette läuft weiter


def test_nicht_aufloesbare_isin_liefert_teilergebnis() -> None:
    analyzer = QuoteAnalyzer(_FakeResolver(None), _FakeEtf(None), ticker_factory=_FakeTicker)
    result = analyzer.analyze(isin="XX0000000000")
    stages = {s.stage: s for s in result.stages}
    assert stages["openfigi"].status == "empty"
    assert stages["fast_info"].status == "skipped"
```

- [ ] **Step 3: Test ausführen, Fehlschlag bestätigen**

Run: `.venv/bin/pytest tests/test_analyzer.py -v`
Expected: FAIL mit `ModuleNotFoundError: app.services.analyzer`

- [ ] **Step 4: `app/services/analyzer.py` implementieren**

```python
"""On-Demand-Diagnose — misst die Dauer der einzelnen Live-Fetch-Stages.

Bewusst cache-umgehend: der Zweck ist die Messung des echten externen Pfades
(OpenFIGI, yfinance-Teilcalls, justETF) aus der Server-Umgebung. Jede Stage ist
best-effort — ein Fehler bricht die Analyse nicht ab, sondern wird erfasst.
"""

import time
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import structlog
import yfinance as yf

from app.models import AnalyzeResult, AnalyzeStage
from app.providers.base import EtfEnricher, InstrumentResolver

logger = structlog.get_logger()


class QuoteAnalyzer:
    """Führt einen instrumentierten Live-Fetch aus und liefert das Stage-Timing."""

    def __init__(
        self,
        resolver: InstrumentResolver,
        etf_provider: EtfEnricher,
        ticker_factory: Callable[[str], Any] = yf.Ticker,
    ) -> None:
        """
        Args:
            resolver: Löst ISINs zu Symbolen auf (OpenFIGI-Stage).
            etf_provider: justETF-Anreicherung (justetf-Stage).
            ticker_factory: Erzeugt ein Ticker-Objekt (fast_info, get_info, isin,
                history). Default ``yf.Ticker``; in Tests überschrieben.
        """
        self._resolver = resolver
        self._etf_provider = etf_provider
        self._ticker_factory = ticker_factory

    def analyze(
        self, *, isin: str | None = None, symbol: str | None = None
    ) -> AnalyzeResult:
        """Misst alle Stages eines Live-Fetch und liefert das Ergebnis.

        Genau eines von ``isin``/``symbol`` muss gesetzt sein (Validierung im
        Router). Bei ISIN wird zuerst aufgelöst (openfigi-Stage); bei direkter
        Symboleingabe entfällt sie (``skipped``).
        """
        stages: list[AnalyzeStage] = []
        start_total = time.perf_counter()

        resolved_symbol = symbol
        resolved_isin = isin

        if isin and not symbol:
            resolved, stage = self._measure_resolve(isin)
            stages.append(stage)
            resolved_symbol = resolved.symbol if resolved else None
        else:
            stages.append(AnalyzeStage(stage="openfigi", seconds=0.0, status="skipped"))

        if resolved_symbol is None:  # nicht auflösbar → Rest überspringen
            for name in ("fast_info", "get_info", "isin", "history", "justetf"):
                stages.append(AnalyzeStage(stage=name, seconds=0.0, status="skipped"))
            return AnalyzeResult(
                symbol=symbol or isin or "",
                isin=resolved_isin,
                total=round(time.perf_counter() - start_total, 3),
                stages=stages,
            )

        ticker = self._ticker_factory(resolved_symbol)
        stages.append(self._measure("fast_info", lambda: _touch_fast_info(ticker)))
        stages.append(self._measure("get_info", ticker.get_info))
        stages.append(self._measure("isin", lambda: getattr(ticker, "isin", None)))
        stages.append(
            self._measure(
                "history",
                lambda: ticker.history(
                    start=(date.today() - timedelta(days=370)).isoformat(),
                    interval="1d",
                    auto_adjust=True,
                ),
                detail=_rows_detail,
            )
        )

        if resolved_isin:
            stages.append(
                self._measure("justetf", lambda: self._etf_provider.fetch_etf(resolved_isin))
            )
        else:
            stages.append(AnalyzeStage(stage="justetf", seconds=0.0, status="skipped"))

        return AnalyzeResult(
            symbol=resolved_symbol,
            isin=resolved_isin,
            total=round(time.perf_counter() - start_total, 3),
            stages=stages,
        )

    def _measure_resolve(self, isin: str) -> tuple[Any, AnalyzeStage]:
        """Misst die OpenFIGI-Auflösung; ``empty`` wenn kein Symbol gefunden."""
        start = time.perf_counter()
        try:
            resolved = self._resolver.resolve_isin(isin)
        except Exception as exc:  # noqa: BLE001 — Diagnose erfasst Fehler
            return None, AnalyzeStage(
                stage="openfigi", seconds=_elapsed(start), status="error",
                detail=type(exc).__name__,
            )
        if resolved is None:
            return None, AnalyzeStage(stage="openfigi", seconds=_elapsed(start), status="empty")
        return resolved, AnalyzeStage(
            stage="openfigi", seconds=_elapsed(start), status="ok", detail=resolved.symbol
        )

    @staticmethod
    def _measure(
        name: str,
        fn: Callable[[], Any],
        detail: Callable[[Any], str | None] | None = None,
    ) -> AnalyzeStage:
        """Führt ``fn`` aus, misst die Dauer und erfasst Erfolg/Fehler/Leer."""
        start = time.perf_counter()
        try:
            value = fn()
        except Exception as exc:  # noqa: BLE001 — Diagnose erfasst Fehler
            return AnalyzeStage(
                stage=name, seconds=_elapsed(start), status="error",
                detail=type(exc).__name__,
            )
        seconds = _elapsed(start)
        if value is None:
            return AnalyzeStage(stage=name, seconds=seconds, status="empty")
        return AnalyzeStage(
            stage=name, seconds=seconds, status="ok",
            detail=detail(value) if detail else None,
        )


def _touch_fast_info(ticker: Any) -> Any:
    """Erzwingt den fast_info-Zugriff (last_price) — löst den Netzwerk-Call aus."""
    return ticker.fast_info.last_price


def _rows_detail(history: Any) -> str:
    """Formatiert die Zeilenzahl einer History als Detail-Text."""
    try:
        return f"{len(history)} rows"
    except TypeError:
        return "n/a"


def _elapsed(start: float) -> float:
    """Vergangene Zeit seit ``start`` in Sekunden, auf 3 Stellen gerundet."""
    return round(time.perf_counter() - start, 3)
```

- [ ] **Step 5: Test ausführen, Erfolg bestätigen**

Run: `.venv/bin/pytest tests/test_analyzer.py -v`
Expected: PASS

- [ ] **Step 6: `get_quote_analyzer` im Container ergänzen** — `app/container.py`

```python
from app.services.analyzer import QuoteAnalyzer
```

```python
@lru_cache
def get_quote_analyzer() -> QuoteAnalyzer:
    """Baut den (gecachten) QuoteAnalyzer aus der aktuellen Konfiguration."""
    settings = get_settings()
    resolver = CompositeResolver(
        OpenFigiResolver(
            OpenFigiClient(settings.openfigi_api_key), settings.default_exchange
        ),
        YFinanceResolver(),
    )
    return QuoteAnalyzer(resolver, JustEtfProvider())
```

- [ ] **Step 7: Commit**

```bash
git add app/models.py app/services/analyzer.py app/container.py tests/test_analyzer.py
git commit -m "feat(analyze): QuoteAnalyzer für Stage-Timing eines Live-Fetch

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `/analyze`-Endpoint

**Files:**
- Modify: `app/routers/dashboard.py`
- Test: `tests/test_api_dashboard.py` (ergänzen)

**Interfaces:**
- Consumes: `get_quote_analyzer` (Task 3), `AnalyzeResult`, `normalize_isin` (bestehend in `app/routers/validation.py`).
- Produces: `GET /analyze?isin=…|?symbol=…` → `AnalyzeResult`.

- [ ] **Step 1: Failing test schreiben** — `tests/test_api_dashboard.py` (ergänzen)

```python
from app.container import get_quote_analyzer
from app.models import AnalyzeResult, AnalyzeStage


def test_analyze_verlangt_genau_eine_kennung(client) -> None:
    assert client.get("/analyze").status_code == 422
    assert client.get("/analyze?isin=IE00B4L5Y983&symbol=EUNL.DE").status_code == 422


def test_analyze_liefert_stages(client, app) -> None:
    class _StubAnalyzer:
        def analyze(self, *, isin=None, symbol=None) -> AnalyzeResult:
            return AnalyzeResult(
                symbol="EUNL.DE", isin=isin, total=1.23,
                stages=[AnalyzeStage(stage="openfigi", seconds=0.5, status="ok")],
            )

    app.dependency_overrides[get_quote_analyzer] = lambda: _StubAnalyzer()
    try:
        response = client.get("/analyze?isin=IE00B4L5Y983")
    finally:
        app.dependency_overrides.pop(get_quote_analyzer, None)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1.23
    assert body["stages"][0]["stage"] == "openfigi"
```

Hinweis: Nutze die in `tests/test_api_dashboard.py` bereits vorhandenen `client`/`app`-Fixtures. Existiert dort keine `app`-Fixture, ergänze sie analog zur `client`-Fixture (`from app.main import app`), damit `dependency_overrides` gesetzt werden kann.

- [ ] **Step 2: Test ausführen, Fehlschlag bestätigen**

Run: `.venv/bin/pytest tests/test_api_dashboard.py -k analyze -v`
Expected: FAIL mit `404` (Route existiert noch nicht)

- [ ] **Step 3: Endpoint implementieren** — `app/routers/dashboard.py`

Imports ergänzen:

```python
from app.container import get_cached_quote_service, get_quote_analyzer
from app.models import (
    AnalyzeResult,
    EnvInfo,
    InstrumentSummary,
    IsinUpdate,
    QuoteResponse,
    RefreshResult,
)
from app.services.analyzer import QuoteAnalyzer
```

Dependency + Route (nach der `environment`-Route):

```python
AnalyzerDep = Annotated[QuoteAnalyzer, Depends(get_quote_analyzer)]


@router.get("/analyze", response_model=AnalyzeResult)
def analyze(
    analyzer: AnalyzerDep,
    isin: str | None = None,
    symbol: str | None = None,
) -> AnalyzeResult:
    """Misst die Dauer der Live-Fetch-Stages für ein Wertpapier (Diagnose).

    Genau eines von ``isin``/``symbol`` angeben. Löst echte externe Abfragen aus
    (kein Cache).
    """
    if bool(isin) == bool(symbol):
        raise HTTPException(
            status_code=422, detail="Genau eines von isin oder symbol angeben"
        )
    return analyzer.analyze(
        isin=normalize_isin(isin) if isin else None, symbol=symbol
    )
```

- [ ] **Step 4: Test ausführen, Erfolg bestätigen**

Run: `.venv/bin/pytest tests/test_api_dashboard.py -k analyze -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routers/dashboard.py tests/test_api_dashboard.py
git commit -m "feat(analyze): GET /analyze-Endpoint für Stage-Timing

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Frontend — Typen, API-Pfad, `useAnalysis`-Composable

**Files:**
- Modify: `dashboard/src/types.ts`
- Modify: `dashboard/src/api/paths.ts`
- Create: `dashboard/src/composables/useAnalysis.ts`
- Test: `dashboard/tests/api/paths.spec.ts` (ergänzen), `dashboard/tests/composables/useAnalysis.spec.ts` (neu)

**Interfaces:**
- Produces:
  - `types.ts`: `AnalyzeStage` (`stage: string; seconds: number; status: string; detail: string | null`), `AnalyzeResult` (`symbol: string; isin: string | null; total: number; stages: AnalyzeStage[]`). `TabKey` und `NavIconName` um `'analysis'` erweitert.
  - `paths.ts`: `analyzePath(ref: InstrumentRef): string` → `/analyze?isin=…` bzw. `/analyze?symbol=…`.
  - `useAnalysis()`: `{ result: Ref<AnalyzeResult | null>; loading: Ref<boolean>; error: Ref<string | null>; analyze: (ref: InstrumentRef) => Promise<void> }`.

- [ ] **Step 1: Typen ergänzen** — `dashboard/src/types.ts`

`TabKey` erweitern und Analyse-Typen anfügen:

```typescript
/** Aktive Unterseite/Tab des Dashboards. */
export type TabKey = 'assets' | 'exchanges' | 'environment' | 'links' | 'themes' | 'analysis'
```

```typescript
export interface AnalyzeStage {
  stage: string
  seconds: number
  status: string
  detail: string | null
}

export interface AnalyzeResult {
  symbol: string
  isin: string | null
  total: number
  stages: AnalyzeStage[]
}
```

- [ ] **Step 2: Failing test für `analyzePath`** — `dashboard/tests/api/paths.spec.ts` (ergänzen)

```typescript
import { analyzePath } from '../../src/api/paths'

describe('analyzePath', () => {
  it('nutzt die ISIN als Query', () => {
    expect(analyzePath({ isin: 'IE00B4L5Y983', symbol: 'EUNL.DE' })).toBe(
      '/analyze?isin=IE00B4L5Y983',
    )
  })
  it('fällt ohne ISIN auf das Symbol zurück', () => {
    expect(analyzePath({ isin: null, symbol: 'AAPL' })).toBe('/analyze?symbol=AAPL')
  })
})
```

- [ ] **Step 3: Test ausführen, Fehlschlag bestätigen**

Run (in `dashboard/`): `npm test -- paths`
Expected: FAIL — `analyzePath is not a function`

- [ ] **Step 4: `analyzePath` implementieren** — `dashboard/src/api/paths.ts` (anfügen)

```typescript
/**
 * Baut den /analyze-Pfad — ISIN bevorzugt, sonst Symbol, jeweils als Query.
 *
 * @param ref - Instrument mit ISIN und/oder Symbol
 * @returns `/analyze?isin={isin}` bzw. `/analyze?symbol={symbol}`
 */
export function analyzePath(ref: InstrumentRef): string {
  return ref.isin
    ? `/analyze?isin=${encodeURIComponent(ref.isin)}`
    : `/analyze?symbol=${encodeURIComponent(ref.symbol)}`
}
```

- [ ] **Step 5: Failing test für `useAnalysis`** — `dashboard/tests/composables/useAnalysis.spec.ts`

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('consola', () => ({
  consola: { error: vi.fn(), warn: vi.fn(), info: vi.fn() },
}))

import { useAnalysis } from '../../src/composables/useAnalysis'

afterEach(() => vi.unstubAllGlobals())

describe('useAnalysis', () => {
  it('lädt das Analyse-Ergebnis', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ symbol: 'EUNL.DE', isin: 'IE00B4L5Y983', total: 1.2, stages: [] }),
        { status: 200 },
      ),
    ))
    const { result, analyze } = useAnalysis()
    await analyze({ isin: 'IE00B4L5Y983', symbol: 'EUNL.DE' })
    expect(result.value?.symbol).toBe('EUNL.DE')
  })

  it('setzt error bei Fehlschlag', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('boom', { status: 502 })))
    const { error, analyze } = useAnalysis()
    await analyze({ isin: null, symbol: 'NOPE' })
    expect(error.value).not.toBeNull()
  })
})
```

- [ ] **Step 6: Test ausführen, Fehlschlag bestätigen**

Run (in `dashboard/`): `npm test -- useAnalysis`
Expected: FAIL — Modul `useAnalysis` fehlt

- [ ] **Step 7: `useAnalysis` implementieren** — `dashboard/src/composables/useAnalysis.ts`

```typescript
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import { analyzePath } from '../api/paths'
import { translate } from '../i18n'
import type { AnalyzeResult, InstrumentRef } from '../types'

/** Führt eine On-Demand-Stage-Analyse für ein Instrument aus. */
export function useAnalysis(): {
  result: Ref<AnalyzeResult | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  analyze: (ref: InstrumentRef) => Promise<void>
} {
  const result = ref<AnalyzeResult | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function analyze(ref: InstrumentRef): Promise<void> {
    loading.value = true
    error.value = null
    try {
      result.value = await apiClient.get<AnalyzeResult>(analyzePath(ref))
    } catch (err) {
      error.value = translate('errors.analysis')
      consola.error('useAnalysis.analyze', err)
    } finally {
      loading.value = false
    }
  }

  return { result, loading, error, analyze }
}
```

- [ ] **Step 8: Beide Frontend-Tests ausführen**

Run (in `dashboard/`): `npm test -- paths useAnalysis`
Expected: PASS (der `errors.analysis`-Key wird in Task 6 ergänzt; `translate` liefert bis dahin den Key-String zurück — der Test prüft nur `!= null`).

- [ ] **Step 9: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/api/paths.ts dashboard/src/composables/useAnalysis.ts dashboard/tests/api/paths.spec.ts dashboard/tests/composables/useAnalysis.spec.ts
git commit -m "feat(dashboard): useAnalysis-Composable + analyzePath

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Frontend — Tab-Verdrahtung, `AnalysisPanel`, i18n

**Files:**
- Modify: `dashboard/src/composables/useHashTab.ts` (TABS)
- Modify: `dashboard/src/components/NavIcon.vue` (Icon `analysis`)
- Modify: `dashboard/src/components/AppHeader.vue` (Tab-Eintrag)
- Modify: `dashboard/src/App.vue` (Panel rendern)
- Create: `dashboard/src/components/AnalysisPanel.vue`
- Modify: `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`
- Test: `dashboard/tests/components/AnalysisPanel.spec.ts` (neu)

**Interfaces:**
- Consumes: `useAnalysis` (Task 5), `AnalyzeResult`/`AnalyzeStage` (Task 5), `InstrumentSummary` (bestehend).
- `AnalysisPanel` Props: `instruments: InstrumentSummary[]`.

- [ ] **Step 1: TABS + Icon-Registry erweitern**

`dashboard/src/composables/useHashTab.ts`:
```typescript
const TABS: TabKey[] = ['assets', 'exchanges', 'environment', 'links', 'themes', 'analysis']
```

`dashboard/src/components/NavIcon.vue` — `KNOWN_ICONS` erweitern und einen SVG-Zweig ergänzen:
```typescript
const KNOWN_ICONS: NavIconName[] = ['assets', 'environment', 'links', 'exchanges', 'themes', 'analysis']
```
Im Template vor dem `<template v-else>`-Fallback (Lupe/Stoppuhr-Motiv):
```html
    <template v-else-if="name === 'analysis'">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35M11 8v3l2 2" />
    </template>
```

- [ ] **Step 2: i18n-Keys ergänzen** — `dashboard/src/i18n/de.ts`

In `nav` ergänzen: `analysis: 'Analyse',`
In `errors` ergänzen: `analysis: 'Analyse fehlgeschlagen',`
Neuer Top-Level-Block (z.B. nach `env`):
```typescript
  analysis: {
    title: 'Live-Analyse',
    hint: 'Misst die Dauer der einzelnen Abfrage-Schritte. Löst echte externe Abfragen aus (kein Cache).',
    pickInstrument: 'Instrument wählen',
    orEnter: 'oder ISIN/Symbol eingeben',
    placeholder: 'ISIN oder Symbol (z.B. EUNL.DE)',
    run: 'Analysieren',
    running: 'Messe…',
    colStage: 'Schritt',
    colSeconds: 'Dauer',
    colStatus: 'Status',
    total: 'Gesamt',
    empty: 'Noch keine Messung — Instrument wählen und „Analysieren" klicken.',
  },
```

`dashboard/src/i18n/en.ts` — dieselben Keys mit englischen Werten:
```typescript
  // nav: analysis: 'Analysis'
  // errors: analysis: 'Analysis failed'
  analysis: {
    title: 'Live analysis',
    hint: 'Measures the duration of each fetch step. Triggers real external requests (no cache).',
    pickInstrument: 'Pick instrument',
    orEnter: 'or enter ISIN/symbol',
    placeholder: 'ISIN or symbol (e.g. EUNL.DE)',
    run: 'Analyze',
    running: 'Measuring…',
    colStage: 'Step',
    colSeconds: 'Duration',
    colStatus: 'Status',
    total: 'Total',
    empty: 'No measurement yet — pick an instrument and click “Analyze”.',
  },
```

- [ ] **Step 3: Failing test für `AnalysisPanel`** — `dashboard/tests/components/AnalysisPanel.spec.ts`

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AnalysisPanel from '../../src/components/AnalysisPanel.vue'
import { i18n } from '../../src/i18n'

describe('AnalysisPanel', () => {
  it('rendert die Stages eines Ergebnisses', async () => {
    const wrapper = mount(AnalysisPanel, {
      global: { plugins: [i18n] },
      props: { instruments: [] },
    })
    // Ergebnis direkt setzen (kein Netzwerk) — Panel zeigt Stage-Zeilen
    ;(wrapper.vm as any).result = {
      symbol: 'EUNL.DE', isin: 'IE00B4L5Y983', total: 1.2,
      stages: [{ stage: 'openfigi', seconds: 0.5, status: 'ok', detail: null }],
    }
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('openfigi')
    expect(wrapper.text()).toContain('0.5')
  })
})
```
> Falls `i18n` nicht als benannter Export aus `../../src/i18n` verfügbar ist, den vorhandenen Export prüfen (`src/i18n/index.ts`) und im Test entsprechend importieren (dieselbe Art, wie andere Component-/Composable-Tests die i18n-Instanz beziehen).

- [ ] **Step 4: Test ausführen, Fehlschlag bestätigen**

Run (in `dashboard/`): `npm test -- AnalysisPanel`
Expected: FAIL — Komponente fehlt

- [ ] **Step 5: `AnalysisPanel.vue` implementieren** — `dashboard/src/components/AnalysisPanel.vue`

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAnalysis } from '../composables/useAnalysis'
import { isIsin } from '../api/paths'
import type { InstrumentRef, InstrumentSummary } from '../types'

const props = defineProps<{ instruments: InstrumentSummary[] }>()

const { t } = useI18n()
const { result, loading, error, analyze } = useAnalysis()

const selectedSymbol = ref<string>('')
const freeInput = ref<string>('')

// Freitext hat Vorrang; sonst das gewählte Listen-Instrument.
const target = computed<InstrumentRef | null>(() => {
  const raw = freeInput.value.trim()
  if (raw) {
    return isIsin(raw.toUpperCase())
      ? { isin: raw.toUpperCase(), symbol: raw }
      : { isin: null, symbol: raw }
  }
  const found = props.instruments.find((i) => i.symbol === selectedSymbol.value)
  return found ? { isin: found.isin, symbol: found.symbol } : null
})

async function run(): Promise<void> {
  if (target.value) await analyze(target.value)
}
</script>

<template>
  <section class="analysis card">
    <h2>{{ t('analysis.title') }}</h2>
    <p class="hint">{{ t('analysis.hint') }}</p>

    <div class="controls">
      <select v-model="selectedSymbol" :aria-label="t('analysis.pickInstrument')">
        <option value="">{{ t('analysis.pickInstrument') }}</option>
        <option v-for="i in instruments" :key="i.symbol" :value="i.symbol">
          {{ i.symbol }} — {{ i.name ?? i.isin }}
        </option>
      </select>
      <input
        v-model="freeInput"
        type="text"
        :placeholder="t('analysis.placeholder')"
        :aria-label="t('analysis.orEnter')"
      />
      <button :disabled="loading || !target" @click="run">
        {{ loading ? t('analysis.running') : t('analysis.run') }}
      </button>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <table v-if="result" class="stages">
      <thead>
        <tr>
          <th>{{ t('analysis.colStage') }}</th>
          <th>{{ t('analysis.colSeconds') }}</th>
          <th>{{ t('analysis.colStatus') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in result.stages" :key="s.stage" :class="s.status">
          <td>{{ s.stage }}</td>
          <td class="num">{{ s.seconds.toFixed(2) }}s</td>
          <td>{{ s.status }}<span v-if="s.detail"> · {{ s.detail }}</span></td>
        </tr>
        <tr class="total">
          <td>{{ t('analysis.total') }}</td>
          <td class="num">{{ result.total.toFixed(2) }}s</td>
          <td>{{ result.symbol }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="hint">{{ t('analysis.empty') }}</p>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.analysis {
  .hint { color: $color-muted; margin: 0 0 1rem; font-size: 0.85rem; max-width: 72ch; }
  .controls { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1rem; }
  select, input { padding: 0.4rem 0.6rem; border-radius: $radius; border: 1px solid $color-border; background: $color-surface; color: $color-text; }
  input { flex: 1; min-width: 12rem; }
  .err { color: #e5484d; margin: 0.5rem 0; }
  table.stages { width: 100%; border-collapse: collapse; font-family: $font-mono; font-variant-numeric: tabular-nums; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid $color-border; }
  .num { text-align: right; }
  tr.error td { color: #e5484d; }
  tr.total td { font-weight: 700; border-top: 2px solid $color-border; }
}
</style>
```

- [ ] **Step 6: Panel in `App.vue` verdrahten**

Import ergänzen: `import AnalysisPanel from './components/AnalysisPanel.vue'`.
Im `<template>` einen Zweig ergänzen (die `instruments`-Ref existiert bereits über `useInstruments`):
```html
    <AnalysisPanel v-else-if="activeTab === 'analysis'" :instruments="instruments" />
```
(vor `<ThemesPanel v-else />` einfügen).

- [ ] **Step 7: Tab in `AppHeader.vue` ergänzen** — im `tabs`-Array:
```typescript
    { key: 'analysis', label: t('nav.analysis'), icon: 'analysis' },
```

- [ ] **Step 8: Frontend-Tests + Typecheck + Build ausführen**

Run (in `dashboard/`):
```bash
npm test
npx vue-tsc --noEmit
npm run build
```
Expected: alle Tests PASS, keine Typfehler, Build erfolgreich.

- [ ] **Step 9: Commit**

```bash
git add dashboard/src/components/AnalysisPanel.vue dashboard/src/components/NavIcon.vue dashboard/src/components/AppHeader.vue dashboard/src/App.vue dashboard/src/composables/useHashTab.ts dashboard/src/i18n/de.ts dashboard/src/i18n/en.ts dashboard/tests/components/AnalysisPanel.spec.ts
git commit -m "feat(dashboard): Analyse-Tab mit Stage-Timing-Panel

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Abschluss-Verifikation

- [ ] **Backend gesamt:** `.venv/bin/pytest -q` → alles grün.
- [ ] **Frontend gesamt:** in `dashboard/`: `npm test && npx vue-tsc --noEmit && npm run build`.
- [ ] **End-to-End (lokal):** App starten (`Procfile.dev` / uvicorn), im Dashboard den Analyse-Tab öffnen, ein Instrument wählen bzw. eine ISIN eingeben, „Analysieren" — Stage-Timing erscheint. Einen Kurs zweimal abrufen (Miss → Hit) und prüfen, dass ein Refresh die Volatilität aus dem Cache setzt (kein 1-Jahres-Download pro Kurs-Fetch mehr — via `structlog`-Logs `daily_synced`/kein wiederholtes `history`).
- [ ] Verwende dazu die `verify`-Skill (falls vorhanden), um die Änderung im echten App-Flow zu treiben.

---

## Self-Review (bereits durchgeführt beim Schreiben)

- **Spec-Coverage:** Feature A (Endpoint Task 3/4, Frontend Task 5/6), Feature B1 (Task 1/2), Abhängigkeits-Zyklus via `DailyCloseSync` (Task 1), justETF-Volatilität bleibt bevorzugt (Task 2 Test), Akkumulation über `daily_closes`-Upsert (bestehend, genutzt in Task 1/2). Out-of-Scope-Punkte werden bewusst nicht berührt.
- **Platzhalter:** Keine „TBD"/„TODO"/„handle edge cases"-Stellen; jeder Schritt enthält den konkreten Code.
- **Typkonsistenz:** `DailyCloseSync.sync`, `set_volatility`, `CachedQuoteService(..., daily_sync=)`, `QuoteAnalyzer.analyze`, `AnalyzeResult/AnalyzeStage`, `analyzePath`, `useAnalysis` durchgängig gleich benannt in Definition und Verwendung.
