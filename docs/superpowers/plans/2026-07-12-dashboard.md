# StockInfo-Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein eigenständiges Vue-Dashboard, das DB-Inhalt und Environment der StockInfo-App visualisiert, Kursdaten aktualisiert (global + pro Instrument), Instrumente hinzufügt/löscht und die Kurshistorie als Graph zeigt.

**Architecture:** Vue-3-SPA (`dashboard/`) gegen die FastAPI-API. Das Backend wird um Read-/Admin-Endpoints erweitert (`/instruments`, `/env`, `/refresh`, `/refresh/{isin}`, `DELETE /instruments/{isin}`) plus CORS. Keine API-Calls in Komponenten — alles über Composables.

**Tech Stack:** Backend: FastAPI, SQLite (bestehend). Frontend: Vue 3 + Vite + TypeScript (strict) + SCSS, Chart.js/vue-chartjs, consola, Vitest.

## Global Constraints

- Python: `.venv`, Tools via `.venv/bin/*`; Lint/Format `ruff`; Tests `pytest`.
- Backend-Konventionen: Router = nur HTTP; Fachlogik in Services; Repository kapselt Raw-SQL; Type Hints überall; Pydantic-Modelle für Responses; `structlog`-Logging; Funktionen ≤ ~30 Zeilen; Google-Docstrings.
- Frontend-Konventionen: `<script setup lang="ts">`; keine API-Calls in Komponenten (nur Composables); Props/Emits typisiert; kein `any`; explizite Rückgabetypen; `consola` statt `console.log`; kein stilles Verschlucken von Fehlern.
- Commits: Conventional Commits, deutsche Subjects. Jeder Task endet mit Commit.
- CORS: `allow_credentials=False` (nie `*` + credentials).

---

## Task 1: Backend — Dashboard-Response-Modelle

**Files:**
- Modify: `app/models.py`
- Test: `tests/test_dashboard_models.py`

**Interfaces:**
- Produces: `InstrumentSummary`, `EnvInfo`, `RefreshResult` (Pydantic-Modelle) in `app.models`.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_dashboard_models.py
from app.models import EnvInfo, InstrumentSummary, RefreshResult


def test_instrument_summary_defaults() -> None:
    summary = InstrumentSummary(symbol="VGWL.DE", history_count=3)
    assert summary.symbol == "VGWL.DE"
    assert summary.isin is None
    assert summary.latest_price is None
    assert summary.history_count == 3


def test_env_info_und_refresh_result() -> None:
    env = EnvInfo(
        version="0.1.0",
        database_path="data/stockinfo.db",
        cache_ttl_hours=6,
        refresh_interval_hours=6,
        metadata_ttl_days=7,
        default_exchange="XETR",
        host="0.0.0.0",
        port=8000,
        api_key_set=False,
        openfigi_key_set=True,
    )
    assert env.api_key_set is False
    assert RefreshResult(total=5, refreshed=4).refreshed == 4
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `.venv/bin/pytest tests/test_dashboard_models.py -v`
Expected: FAIL (`ImportError: cannot import name 'InstrumentSummary'`).

- [ ] **Step 3: Modelle ergänzen**

Am Ende von `app/models.py` anhängen:

```python
class InstrumentSummary(BaseModel):
    """Ein Instrument mit seinem letzten Kurs — für die DB-Übersicht."""

    isin: str | None = None
    symbol: str
    exchange: str | None = None
    name: str | None = None
    type: str | None = None
    currency: str | None = None
    provider: str | None = None
    ter: float | None = None
    replication: str | None = None
    fund_size: float | None = None
    meta_fetched_at: str | None = None
    latest_price: float | None = None
    latest_quote_time: str | None = None
    latest_currency: str | None = None
    latest_fetched_at: str | None = None
    history_count: int = 0


class EnvInfo(BaseModel):
    """Sichtbarer Ausschnitt der Konfiguration (Secrets nur als Booleans)."""

    version: str
    database_path: str
    cache_ttl_hours: int
    refresh_interval_hours: int
    metadata_ttl_days: int
    default_exchange: str
    host: str
    port: int
    api_key_set: bool
    openfigi_key_set: bool


class RefreshResult(BaseModel):
    """Ergebnis eines globalen Refresh-Laufs."""

    total: int
    refreshed: int
```

- [ ] **Step 4: Test ausführen (muss bestehen)**

Run: `.venv/bin/pytest tests/test_dashboard_models.py -v`
Expected: PASS (2 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/models.py tests/test_dashboard_models.py
git commit -m "feat(models): Dashboard-Response-Modelle (InstrumentSummary, EnvInfo, RefreshResult)"
```

---

## Task 2: Backend — Repository: Übersicht + Löschen

**Files:**
- Modify: `app/repository.py`
- Test: `tests/test_repository_dashboard.py`

**Interfaces:**
- Consumes: `QuoteRepository`, `save_quote`, `get_connection` (bestehend).
- Produces:
  - `QuoteRepository.list_instruments_with_latest() -> list[dict]` — je Instrument alle Spalten plus `latest_price, latest_quote_time, latest_currency, latest_fetched_at, history_count`.
  - `QuoteRepository.delete_instrument(isin: str) -> bool` — löscht per ISIN (Quotes via Cascade); `True`, wenn etwas gelöscht wurde.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_repository_dashboard.py
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "dash.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def _save(repo: QuoteRepository, isin: str, symbol: str, price: float, t: str) -> None:
    repo.save_quote(
        QuoteResponse(
            isin=isin, symbol=symbol, currency="EUR", price=price,
            quote_time=t, fetched_at=t, type="etf", ter=0.19, provider="Vanguard",
        )
    )


def test_list_instruments_with_latest(repo: QuoteRepository) -> None:
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 160.0, "2026-07-12T10:00:00+00:00")
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 161.0, "2026-07-12T11:00:00+00:00")

    rows = repo.list_instruments_with_latest()
    assert len(rows) == 1
    row = rows[0]
    assert row["symbol"] == "VGWL.DE"
    assert row["latest_price"] == 161.0  # jüngster Kurs
    assert row["history_count"] == 2


def test_delete_instrument(repo: QuoteRepository) -> None:
    _save(repo, "IE00B3RBWM25", "VGWL.DE", 160.0, "2026-07-12T10:00:00+00:00")

    assert repo.delete_instrument("IE00B3RBWM25") is True
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is None
    assert repo.delete_instrument("IE00B3RBWM25") is False  # nichts mehr da
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `.venv/bin/pytest tests/test_repository_dashboard.py -v`
Expected: FAIL (`AttributeError: 'QuoteRepository' object has no attribute 'list_instruments_with_latest'`).

- [ ] **Step 3: Repository-Methoden ergänzen**

In `app/repository.py` in der Klasse `QuoteRepository` ergänzen (nach `list_instruments`):

```python
    def list_instruments_with_latest(self) -> list[dict]:
        """Gibt alle Instrumente inkl. jüngstem Kurs und History-Anzahl zurück."""
        query = """
            SELECT i.*,
                   q.price      AS latest_price,
                   q.quote_time AS latest_quote_time,
                   q.currency   AS latest_currency,
                   q.fetched_at AS latest_fetched_at,
                   (SELECT COUNT(*) FROM quotes WHERE instrument_id = i.id)
                       AS history_count
            FROM instruments i
            LEFT JOIN quotes q ON q.id = (
                SELECT id FROM quotes WHERE instrument_id = i.id
                ORDER BY quote_time DESC LIMIT 1
            )
            ORDER BY i.symbol
        """
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
            return [dict(row) for row in rows]

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument (und seine Quotes via Cascade) anhand der ISIN.

        Returns:
            True, wenn ein Instrument gelöscht wurde, sonst False.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM instruments WHERE isin = ?", (isin,)
            )
            return cursor.rowcount > 0
```

- [ ] **Step 4: Test ausführen (muss bestehen)**

Run: `.venv/bin/pytest tests/test_repository_dashboard.py -v`
Expected: PASS (2 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/repository.py tests/test_repository_dashboard.py
git commit -m "feat(repository): Instrumentenübersicht mit letztem Kurs und Löschen per ISIN"
```

---

## Task 3: Backend — Service: refresh_one, list_instruments, delete + Config CORS

**Files:**
- Modify: `app/services/quote_cache.py`, `app/config.py`
- Test: `tests/test_quote_cache_dashboard.py`

**Interfaces:**
- Consumes: `CachedQuoteService` (mit `_quote_service`, `_repository`), `QuoteRepository.list_instruments_with_latest/delete_instrument`.
- Produces:
  - `CachedQuoteService.list_instruments() -> list[dict]`
  - `CachedQuoteService.delete_instrument(isin: str) -> bool`
  - `CachedQuoteService.refresh_one(isin: str) -> QuoteResponse` (Live-Fetch per ISIN + speichern; TTL umgangen).
  - `Settings.cors_origins: list[str]` (Default `["http://localhost:5173"]`).

- [ ] **Step 1: Test schreiben**

```python
# tests/test_quote_cache_dashboard.py
from pathlib import Path

import pytest

from app.db import init_db
from app.models import QuoteResponse
from app.repository import QuoteRepository
from app.services.quote_cache import CachedQuoteService


class FakeQuoteService:
    def __init__(self) -> None:
        self.calls = 0

    def get_quote_by_isin(self, isin: str) -> QuoteResponse:
        self.calls += 1
        return QuoteResponse(
            isin=isin, symbol="VGWL.DE", currency="EUR", price=200.0,
            quote_time="2026-07-12T20:00:00+00:00",
            fetched_at="2026-07-12T20:00:00+00:00", type="etf",
        )

    def get_quote_by_symbol(self, symbol: str) -> QuoteResponse:  # pragma: no cover
        return self.get_quote_by_isin(symbol)


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "svc.db")
    init_db(db_path)
    return QuoteRepository(db_path)


def test_refresh_one_forciert_und_speichert(repo: QuoteRepository) -> None:
    fake = FakeQuoteService()
    service = CachedQuoteService(fake, repo, ttl_hours=6)

    result = service.refresh_one("IE00B3RBWM25")

    assert fake.calls == 1
    assert result.price == 200.0
    assert repo.get_instrument_by_isin("IE00B3RBWM25") is not None


def test_list_und_delete(repo: QuoteRepository) -> None:
    service = CachedQuoteService(FakeQuoteService(), repo, ttl_hours=6)
    service.refresh_one("IE00B3RBWM25")

    listed = service.list_instruments()
    assert len(listed) == 1 and listed[0]["symbol"] == "VGWL.DE"
    assert service.delete_instrument("IE00B3RBWM25") is True
    assert service.list_instruments() == []
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `.venv/bin/pytest tests/test_quote_cache_dashboard.py -v`
Expected: FAIL (`AttributeError: ... 'refresh_one'`).

- [ ] **Step 3: Service-Methoden ergänzen**

In `app/services/quote_cache.py` in der Klasse `CachedQuoteService` ergänzen (nach `refresh_all`):

```python
    def refresh_one(self, isin: str) -> QuoteResponse:
        """Aktualisiert ein einzelnes Instrument per ISIN live und speichert es.

        Umgeht die TTL bewusst.

        Raises:
            InstrumentNotFoundError: ISIN nicht auflösbar.
            QuoteUnavailableError: Kein Kurs beschaffbar.
        """
        fresh = self._quote_service.get_quote_by_isin(isin)
        self._repository.save_quote(fresh)
        return fresh

    def list_instruments(self) -> list[dict]:
        """Gibt alle Instrumente inkl. letztem Kurs zurück (für das Dashboard)."""
        return self._repository.list_instruments_with_latest()

    def delete_instrument(self, isin: str) -> bool:
        """Löscht ein Instrument samt Historie; True bei Erfolg."""
        return self._repository.delete_instrument(isin)
```

- [ ] **Step 4: Config erweitern**

In `app/config.py` im `Settings`-Block unter „ISIN-Auflösung" ergänzen:

```python
    # Dashboard / CORS
    cors_origins: list[str] = ["http://localhost:5173"]
```

- [ ] **Step 5: Tests ausführen (müssen bestehen)**

Run: `.venv/bin/pytest tests/test_quote_cache_dashboard.py -v`
Expected: PASS (2 Tests).

- [ ] **Step 6: Commit**

```bash
git add app/services/quote_cache.py app/config.py tests/test_quote_cache_dashboard.py
git commit -m "feat(service): refresh_one, Instrumentenliste, Löschen + CORS-Origins-Setting"
```

---

## Task 4: Backend — Dashboard-Router + CORS

**Files:**
- Create: `app/routers/dashboard.py`
- Modify: `app/main.py`
- Test: `tests/test_api_dashboard.py`

**Interfaces:**
- Consumes: `get_cached_quote_service`, `CachedQuoteService.{list_instruments,delete_instrument,refresh_one,refresh_all}`, Modelle aus Task 1, `get_settings`, `__version__`.
- Produces: HTTP-Routen `GET /instruments`, `GET /env`, `POST /refresh`, `POST /refresh/{isin}`, `DELETE /instruments/{isin}`; CORS-Middleware auf `app`.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_api_dashboard.py
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import get_cached_quote_service
from app.main import app
from app.models import QuoteResponse
from app.services.quote_service import InstrumentNotFoundError


class FakeService:
    def list_instruments(self) -> list[dict]:
        return [{"symbol": "VGWL.DE", "isin": "IE00B3RBWM25", "history_count": 2,
                 "latest_price": 161.0}]

    def refresh_all(self) -> int:
        return 3

    def refresh_one(self, isin: str) -> QuoteResponse:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        return QuoteResponse(isin=isin, symbol="VGWL.DE", currency="EUR",
                             price=161.0, quote_time="t", fetched_at="t", type="etf")

    def delete_instrument(self, isin: str) -> bool:
        return not isin.startswith("XX")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_cached_quote_service] = FakeService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_instruments(client: TestClient) -> None:
    r = client.get("/instruments")
    assert r.status_code == 200
    assert r.json()[0]["symbol"] == "VGWL.DE"


def test_env(client: TestClient) -> None:
    r = client.get("/env")
    assert r.status_code == 200
    body = r.json()
    assert body["default_exchange"] == "XETR"
    assert "api_key_set" in body and "version" in body


def test_refresh_global(client: TestClient) -> None:
    r = client.post("/refresh")
    assert r.status_code == 200
    assert r.json()["refreshed"] == 3


def test_refresh_one_und_404(client: TestClient) -> None:
    assert client.post("/refresh/IE00B3RBWM25").status_code == 200
    assert client.post("/refresh/XX0000000000").status_code == 404


def test_delete(client: TestClient) -> None:
    assert client.delete("/instruments/IE00B3RBWM25").status_code == 204
    assert client.delete("/instruments/XX0000000000").status_code == 404
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `.venv/bin/pytest tests/test_api_dashboard.py -v`
Expected: FAIL (404 auf `/instruments`, Route existiert nicht).

- [ ] **Step 3: Router anlegen**

```python
# app/routers/dashboard.py
"""Dashboard-Endpoints — DB-Übersicht, Environment, Refresh, Löschen.

Nur HTTP-Belange; Fachlogik liegt im CachedQuoteService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app import __version__
from app.config import Settings, get_settings
from app.container import get_cached_quote_service
from app.models import EnvInfo, InstrumentSummary, QuoteResponse, RefreshResult
from app.services.quote_cache import CachedQuoteService
from app.services.quote_service import InstrumentNotFoundError, QuoteUnavailableError

router = APIRouter(tags=["dashboard"])

ServiceDep = Annotated[CachedQuoteService, Depends(get_cached_quote_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/instruments", response_model=list[InstrumentSummary])
def list_instruments(service: ServiceDep) -> list[dict]:
    """Gibt alle gecachten Instrumente mit letztem Kurs zurück."""
    return service.list_instruments()


@router.get("/env", response_model=EnvInfo)
def environment(settings: SettingsDep) -> EnvInfo:
    """Gibt den sichtbaren Ausschnitt der Konfiguration zurück (Secrets maskiert)."""
    return EnvInfo(
        version=__version__,
        database_path=settings.database_path,
        cache_ttl_hours=settings.cache_ttl_hours,
        refresh_interval_hours=settings.refresh_interval_hours,
        metadata_ttl_days=settings.metadata_ttl_days,
        default_exchange=settings.default_exchange,
        host=settings.host,
        port=settings.port,
        api_key_set=bool(settings.api_key),
        openfigi_key_set=bool(settings.openfigi_api_key),
    )


@router.post("/refresh", response_model=RefreshResult)
def refresh_all(service: ServiceDep) -> RefreshResult:
    """Aktualisiert alle bekannten Instrumente live."""
    total = len(service.list_instruments())
    refreshed = service.refresh_all()
    return RefreshResult(total=total, refreshed=refreshed)


@router.post("/refresh/{isin}", response_model=QuoteResponse)
def refresh_one(isin: str, service: ServiceDep) -> QuoteResponse:
    """Aktualisiert ein einzelnes Instrument per ISIN."""
    try:
        return service.refresh_one(isin)
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Keine Auflösung für {isin}") from exc
    except QuoteUnavailableError as exc:
        raise HTTPException(status_code=502, detail=f"Kein Kurs für {isin}") from exc


@router.delete("/instruments/{isin}", status_code=204)
def delete_instrument(isin: str, service: ServiceDep) -> Response:
    """Löscht ein Instrument samt Historie."""
    if not service.delete_instrument(isin):
        raise HTTPException(status_code=404, detail=f"Unbekannte ISIN {isin}")
    return Response(status_code=204)
```

- [ ] **Step 4: Router + CORS in main.py einhängen**

In `app/main.py` die Imports ergänzen:

```python
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dashboard, quotes
```

(die bestehende Zeile `from app.routers import quotes` ersetzen). Nach `app.include_router(quotes.router)` ergänzen:

```python
app.include_router(dashboard.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 5: Tests ausführen (müssen bestehen)**

Run: `.venv/bin/pytest tests/test_api_dashboard.py -v && .venv/bin/ruff check app tests`
Expected: PASS (6 Tests) + „All checks passed!".

- [ ] **Step 6: Commit**

```bash
git add app/routers/dashboard.py app/main.py tests/test_api_dashboard.py
git commit -m "feat(api): Dashboard-Endpoints (instruments, env, refresh, delete) + CORS"
```

---

## Task 5: Frontend — Vite/Vue/TS/SCSS-Gerüst

**Files:**
- Create: `dashboard/package.json`, `dashboard/vite.config.ts`, `dashboard/tsconfig.json`, `dashboard/index.html`, `dashboard/.env.example`, `dashboard/.gitignore`, `dashboard/src/main.ts`, `dashboard/src/App.vue`, `dashboard/src/styles/_variables.scss`, `dashboard/src/styles/base.scss`

**Interfaces:**
- Produces: lauffähiges Vite-Projekt; `App.vue` als Platzhalter-Shell; `npm run dev`/`build`/`test` verfügbar.

- [ ] **Step 1: package.json anlegen**

```json
{
  "name": "stockinfo-dashboard",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "chart.js": "^4.4.3",
    "consola": "^3.2.3",
    "vue": "^3.5.13",
    "vue-chartjs": "^5.3.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.1",
    "@vue/test-utils": "^2.4.6",
    "jsdom": "^25.0.1",
    "sass": "^1.83.0",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "vitest": "^2.1.8",
    "vue-tsc": "^2.2.0"
  }
}
```

- [ ] **Step 2: Konfigurationsdateien anlegen**

`dashboard/vite.config.ts`:

```ts
/// <reference types="vitest/config" />
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: { port: 5173 },
  test: { environment: 'jsdom' },
})
```

`dashboard/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "types": ["vite/client", "vitest/globals"]
  },
  "include": ["src", "tests"]
}
```

`dashboard/index.html`:

```html
<!doctype html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>StockInfo Dashboard</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

`dashboard/.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
```

`dashboard/.gitignore`:

```
node_modules/
dist/
.env
```

- [ ] **Step 3: SCSS + App-Shell + main.ts anlegen**

`dashboard/src/styles/_variables.scss`:

```scss
$color-bg: #0f172a;
$color-surface: #1e293b;
$color-text: #e2e8f0;
$color-muted: #94a3b8;
$color-accent: #38bdf8;
$color-danger: #f87171;
$radius: 8px;
```

`dashboard/src/styles/base.scss`:

```scss
@use './variables' as *;

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: $color-bg;
  color: $color-text;
}

button {
  cursor: pointer;
  border: none;
  border-radius: $radius;
  padding: 0.4rem 0.8rem;
  background: $color-accent;
  color: $color-bg;
  font-weight: 600;

  &:disabled { opacity: 0.5; cursor: default; }
}
```

`dashboard/src/App.vue`:

```vue
<script setup lang="ts">
// Wird in Task 9 mit Composables und Komponenten gefüllt.
</script>

<template>
  <main class="app">
    <h1>StockInfo Dashboard</h1>
  </main>
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;
}
</style>
```

`dashboard/src/main.ts`:

```ts
import { createApp } from 'vue'

import App from './App.vue'
import './styles/base.scss'

createApp(App).mount('#app')
```

- [ ] **Step 4: Installieren und Build prüfen**

Run:
```bash
cd dashboard && npm install && npm run build
```
Expected: Build ohne Fehler, `dashboard/dist/` entsteht.

- [ ] **Step 5: Commit**

```bash
git add dashboard/
git commit -m "feat(dashboard): Vue+Vite+TS+SCSS-Gerüst"
```

---

## Task 6: Frontend — Typen + API-Client

**Files:**
- Create: `dashboard/src/types.ts`, `dashboard/src/api/client.ts`, `dashboard/tests/api-client.spec.ts`

**Interfaces:**
- Produces:
  - Typen `InstrumentSummary`, `EnvInfo`, `QuotePoint`, `RefreshResult`.
  - `apiClient.get<T>(path)`, `apiClient.post<T>(path)`, `apiClient.del(path)`, `ApiError`.

- [ ] **Step 1: Test schreiben**

```ts
// dashboard/tests/api-client.spec.ts
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiClient } from '../src/api/client'

afterEach(() => vi.unstubAllGlobals())

describe('apiClient', () => {
  it('get parst JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ symbol: 'VGWL.DE' }]), { status: 200 }),
    ))
    const data = await apiClient.get<Array<{ symbol: string }>>('/instruments')
    expect(data[0].symbol).toBe('VGWL.DE')
  })

  it('wirft ApiError bei non-2xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('nope', { status: 404 }),
    ))
    await expect(apiClient.get('/quote/XX')).rejects.toBeInstanceOf(ApiError)
  })

  it('del toleriert 204', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(apiClient.del('/instruments/IE00B3RBWM25')).resolves.toBeUndefined()
  })
})
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `cd dashboard && npx vitest run tests/api-client.spec.ts`
Expected: FAIL (Modul `../src/api/client` fehlt).

- [ ] **Step 3: Typen + Client anlegen**

`dashboard/src/types.ts`:

```ts
export interface InstrumentSummary {
  isin: string | null
  symbol: string
  exchange: string | null
  name: string | null
  type: string | null
  currency: string | null
  provider: string | null
  ter: number | null
  replication: string | null
  fund_size: number | null
  meta_fetched_at: string | null
  latest_price: number | null
  latest_quote_time: string | null
  latest_currency: string | null
  latest_fetched_at: string | null
  history_count: number
}

export interface EnvInfo {
  version: string
  database_path: string
  cache_ttl_hours: number
  refresh_interval_hours: number
  metadata_ttl_days: number
  default_exchange: string
  host: string
  port: number
  api_key_set: boolean
  openfigi_key_set: boolean
}

export interface QuotePoint {
  price: number
  quote_time: string
  volume: number | null
  currency: string | null
  fetched_at: string
}

export interface RefreshResult {
  total: number
  refreshed: number
}
```

`dashboard/src/api/client.ts`:

```ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/** Fehler mit HTTP-Status und Detailtext aus der API. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`API ${status}: ${detail}`)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText)
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string): Promise<T> => request<T>(path),
  post: <T>(path: string): Promise<T> => request<T>(path, { method: 'POST' }),
  del: (path: string): Promise<void> => request<void>(path, { method: 'DELETE' }),
}
```

- [ ] **Step 4: Test ausführen (muss bestehen)**

Run: `cd dashboard && npx vitest run tests/api-client.spec.ts`
Expected: PASS (3 Tests).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/types.ts dashboard/src/api/client.ts dashboard/tests/api-client.spec.ts
git commit -m "feat(dashboard): Typen und typisierter API-Client"
```

---

## Task 7: Frontend — Composables (Instrumente, Environment, History)

**Files:**
- Create: `dashboard/src/composables/useInstruments.ts`, `useEnvironment.ts`, `useHistory.ts`, `dashboard/tests/composables.spec.ts`

**Interfaces:**
- Consumes: `apiClient`, Typen.
- Produces:
  - `useInstruments() -> { instruments: Ref<InstrumentSummary[]>, loading, error, load() }`
  - `useEnvironment() -> { env: Ref<EnvInfo|null>, loading, error, load() }`
  - `useHistory() -> { points: Ref<QuotePoint[]>, loading, error, load(isin) }`

- [ ] **Step 1: Test schreiben**

```ts
// dashboard/tests/composables.spec.ts
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useEnvironment } from '../src/composables/useEnvironment'
import { useHistory } from '../src/composables/useHistory'
import { useInstruments } from '../src/composables/useInstruments'

afterEach(() => vi.unstubAllGlobals())

function stubFetch(body: unknown, status = 200): void {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), { status }),
  ))
}

describe('composables', () => {
  it('useInstruments lädt Liste', async () => {
    stubFetch([{ symbol: 'VGWL.DE', history_count: 2 }])
    const { instruments, loading, load } = useInstruments()
    await load()
    expect(loading.value).toBe(false)
    expect(instruments.value[0].symbol).toBe('VGWL.DE')
  })

  it('useEnvironment lädt Env', async () => {
    stubFetch({ version: '0.1.0', default_exchange: 'XETR' })
    const { env, load } = useEnvironment()
    await load()
    expect(env.value?.default_exchange).toBe('XETR')
  })

  it('useHistory setzt error bei Fehler', async () => {
    stubFetch('boom', 502)
    const { error, load } = useHistory()
    await load('IE00B3RBWM25')
    expect(error.value).not.toBeNull()
  })
})
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `cd dashboard && npx vitest run tests/composables.spec.ts`
Expected: FAIL (Module fehlen).

- [ ] **Step 3: Composables anlegen**

`dashboard/src/composables/useInstruments.ts`:

```ts
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { InstrumentSummary } from '../types'

/** Lädt die Liste aller gecachten Instrumente. */
export function useInstruments(): {
  instruments: Ref<InstrumentSummary[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const instruments = ref<InstrumentSummary[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      instruments.value = await apiClient.get<InstrumentSummary[]>('/instruments')
    } catch (err) {
      error.value = 'Instrumente konnten nicht geladen werden'
      consola.error('useInstruments.load', err)
    } finally {
      loading.value = false
    }
  }

  return { instruments, loading, error, load }
}
```

`dashboard/src/composables/useEnvironment.ts`:

```ts
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { EnvInfo } from '../types'

/** Lädt den sichtbaren Ausschnitt der Backend-Konfiguration. */
export function useEnvironment(): {
  env: Ref<EnvInfo | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
} {
  const env = ref<EnvInfo | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      env.value = await apiClient.get<EnvInfo>('/env')
    } catch (err) {
      error.value = 'Environment konnte nicht geladen werden'
      consola.error('useEnvironment.load', err)
    } finally {
      loading.value = false
    }
  }

  return { env, loading, error, load }
}
```

`dashboard/src/composables/useHistory.ts`:

```ts
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { QuotePoint } from '../types'

/** Lädt die Kurshistorie eines Instruments per ISIN. */
export function useHistory(): {
  points: Ref<QuotePoint[]>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: (isin: string) => Promise<void>
} {
  const points = ref<QuotePoint[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function load(isin: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      points.value = await apiClient.get<QuotePoint[]>(
        `/quote/${isin}/history?limit=500`,
      )
    } catch (err) {
      error.value = 'Historie konnte nicht geladen werden'
      consola.error('useHistory.load', err)
    } finally {
      loading.value = false
    }
  }

  return { points, loading, error, load }
}
```

- [ ] **Step 4: Test ausführen (muss bestehen)**

Run: `cd dashboard && npx vitest run tests/composables.spec.ts`
Expected: PASS (3 Tests).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/composables tests
git commit -m "feat(dashboard): Composables für Instrumente, Environment und Historie"
```

---

## Task 8: Frontend — Aktions-Composables (Refresh, Hinzufügen, Löschen)

**Files:**
- Create: `dashboard/src/composables/useRefresh.ts`, `useInstrumentActions.ts`, `dashboard/tests/actions.spec.ts`

**Interfaces:**
- Consumes: `apiClient`, `RefreshResult`.
- Produces:
  - `useRefresh() -> { refreshing: Ref<boolean>, result: Ref<RefreshResult|null>, error, trigger() }`
  - `useInstrumentActions() -> { busy: Ref<boolean>, error, add(identifier), refreshOne(isin), remove(isin) }`
  - `isIsin(value: string): boolean`

- [ ] **Step 1: Test schreiben**

```ts
// dashboard/tests/actions.spec.ts
import { afterEach, describe, expect, it, vi } from 'vitest'

import { isIsin, useInstrumentActions } from '../src/composables/useInstrumentActions'
import { useRefresh } from '../src/composables/useRefresh'

afterEach(() => vi.unstubAllGlobals())

describe('actions', () => {
  it('isIsin erkennt ISINs', () => {
    expect(isIsin('IE00B3RBWM25')).toBe(true)
    expect(isIsin('VGWL.DE')).toBe(false)
  })

  it('add ruft /quote/{isin} bei ISIN', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('IE00B3RBWM25')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote/IE00B3RBWM25')
  })

  it('add ruft /quote?symbol bei Symbol', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await useInstrumentActions().add('VGWL.DE')
    expect(fetchMock.mock.calls[0][0]).toContain('/quote?symbol=VGWL.DE')
  })

  it('trigger setzt result', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ total: 2, refreshed: 2 }), { status: 200 }),
    ))
    const { result, trigger } = useRefresh()
    await trigger()
    expect(result.value?.refreshed).toBe(2)
  })
})
```

- [ ] **Step 2: Test ausführen (muss fehlschlagen)**

Run: `cd dashboard && npx vitest run tests/actions.spec.ts`
Expected: FAIL (Module fehlen).

- [ ] **Step 3: Composables anlegen**

`dashboard/src/composables/useRefresh.ts`:

```ts
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'
import type { RefreshResult } from '../types'

/** Globaler Refresh aller Instrumente. */
export function useRefresh(): {
  refreshing: Ref<boolean>
  result: Ref<RefreshResult | null>
  error: Ref<string | null>
  trigger: () => Promise<void>
} {
  const refreshing = ref<boolean>(false)
  const result = ref<RefreshResult | null>(null)
  const error = ref<string | null>(null)

  async function trigger(): Promise<void> {
    refreshing.value = true
    error.value = null
    try {
      result.value = await apiClient.post<RefreshResult>('/refresh')
    } catch (err) {
      error.value = 'Refresh fehlgeschlagen'
      consola.error('useRefresh.trigger', err)
    } finally {
      refreshing.value = false
    }
  }

  return { refreshing, result, error, trigger }
}
```

`dashboard/src/composables/useInstrumentActions.ts`:

```ts
import { consola } from 'consola'
import { ref, type Ref } from 'vue'

import { apiClient } from '../api/client'

/** Prüft, ob ein String das ISIN-Format hat (2 Buchstaben, 9 alphanum., 1 Ziffer). */
export function isIsin(value: string): boolean {
  return /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(value)
}

/** Aktionen auf einzelnen Instrumenten: hinzufügen, aktualisieren, löschen. */
export function useInstrumentActions(): {
  busy: Ref<boolean>
  error: Ref<string | null>
  add: (identifier: string) => Promise<void>
  refreshOne: (isin: string) => Promise<void>
  remove: (isin: string) => Promise<void>
} {
  const busy = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function run(action: () => Promise<unknown>, message: string): Promise<void> {
    busy.value = true
    error.value = null
    try {
      await action()
    } catch (err) {
      error.value = message
      consola.error('useInstrumentActions', message, err)
    } finally {
      busy.value = false
    }
  }

  async function add(identifier: string): Promise<void> {
    const trimmed = identifier.trim()
    const path = isIsin(trimmed)
      ? `/quote/${trimmed}`
      : `/quote?symbol=${encodeURIComponent(trimmed)}`
    await run(() => apiClient.get(path), 'Hinzufügen fehlgeschlagen')
  }

  async function refreshOne(isin: string): Promise<void> {
    await run(() => apiClient.post(`/refresh/${isin}`), 'Aktualisieren fehlgeschlagen')
  }

  async function remove(isin: string): Promise<void> {
    await run(() => apiClient.del(`/instruments/${isin}`), 'Löschen fehlgeschlagen')
  }

  return { busy, error, add, refreshOne, remove }
}
```

- [ ] **Step 4: Test ausführen (muss bestehen)**

Run: `cd dashboard && npx vitest run tests/actions.spec.ts`
Expected: PASS (4 Tests).

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/composables dashboard/tests/actions.spec.ts
git commit -m "feat(dashboard): Aktions-Composables (Refresh, Hinzufügen, Löschen)"
```

---

## Task 9: Frontend — Komponenten + App-Verdrahtung

**Files:**
- Create: `dashboard/src/components/EnvironmentPanel.vue`, `InstrumentsTable.vue`, `Toolbar.vue`, `HistoryChart.vue`
- Modify: `dashboard/src/App.vue`

**Interfaces:**
- Consumes: alle Composables, Typen, `vue-chartjs`.
- Produces: fertige UI. `HistoryChart` Prop `points: QuotePoint[]`, `currency: string | null`. `InstrumentsTable` Props `instruments`, Emits `select(isin)`, `refresh(isin)`, `remove(isin)`. `Toolbar` Emits `refresh`, `add(identifier)`.

- [ ] **Step 1: EnvironmentPanel.vue**

```vue
<script setup lang="ts">
import type { EnvInfo } from '../types'

defineProps<{ env: EnvInfo | null }>()
</script>

<template>
  <section v-if="env" class="env">
    <h2>Environment</h2>
    <dl>
      <div><dt>Version</dt><dd>{{ env.version }}</dd></div>
      <div><dt>DB-Pfad</dt><dd>{{ env.database_path }}</dd></div>
      <div><dt>Cache-TTL (h)</dt><dd>{{ env.cache_ttl_hours }}</dd></div>
      <div><dt>Refresh-Intervall (h)</dt><dd>{{ env.refresh_interval_hours }}</dd></div>
      <div><dt>Metadaten-TTL (d)</dt><dd>{{ env.metadata_ttl_days }}</dd></div>
      <div><dt>Default-Börse</dt><dd>{{ env.default_exchange }}</dd></div>
      <div><dt>Host:Port</dt><dd>{{ env.host }}:{{ env.port }}</dd></div>
      <div><dt>API-Key gesetzt</dt><dd>{{ env.api_key_set ? 'ja' : 'nein' }}</dd></div>
      <div><dt>OpenFIGI-Key gesetzt</dt><dd>{{ env.openfigi_key_set ? 'ja' : 'nein' }}</dd></div>
    </dl>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.env {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;

  dl { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; }
  dt { color: $color-muted; font-size: 0.8rem; }
  dd { margin: 0; font-weight: 600; }
}
</style>
```

- [ ] **Step 2: Toolbar.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (event: 'refresh'): void
  (event: 'add', identifier: string): void
}>()

defineProps<{ refreshing: boolean; busy: boolean }>()

const identifier = ref<string>('')

function submit(): void {
  const value = identifier.value.trim()
  if (value) {
    emit('add', value)
    identifier.value = ''
  }
}
</script>

<template>
  <header class="toolbar">
    <button :disabled="refreshing" @click="emit('refresh')">
      {{ refreshing ? 'Aktualisiere…' : 'Alle aktualisieren' }}
    </button>
    <form class="add" @submit.prevent="submit">
      <input v-model="identifier" placeholder="ISIN oder Symbol (z.B. VGWL.DE)" />
      <button type="submit" :disabled="busy">Hinzufügen</button>
    </form>
  </header>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.toolbar {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;

  .add { display: flex; gap: 0.5rem; }
  input {
    padding: 0.4rem 0.6rem;
    border-radius: $radius;
    border: 1px solid $color-muted;
    background: $color-surface;
    color: $color-text;
    min-width: 260px;
  }
}
</style>
```

- [ ] **Step 3: InstrumentsTable.vue**

```vue
<script setup lang="ts">
import type { InstrumentSummary } from '../types'

defineProps<{ instruments: InstrumentSummary[]; selectedIsin: string | null }>()

const emit = defineEmits<{
  (event: 'select', isin: string): void
  (event: 'refresh', isin: string): void
  (event: 'remove', isin: string): void
}>()
</script>

<template>
  <section class="table">
    <h2>Instrumente</h2>
    <table>
      <thead>
        <tr>
          <th>Symbol</th><th>ISIN</th><th>Name</th><th>Typ</th>
          <th>Kurs</th><th>TER</th><th>Punkte</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in instruments"
          :key="item.symbol"
          :class="{ selected: item.isin === selectedIsin }"
          @click="item.isin && emit('select', item.isin)"
        >
          <td>{{ item.symbol }}</td>
          <td>{{ item.isin ?? '—' }}</td>
          <td>{{ item.name ?? '—' }}</td>
          <td>{{ item.type ?? '—' }}</td>
          <td>{{ item.latest_price ?? '—' }} {{ item.latest_currency ?? '' }}</td>
          <td>{{ item.ter ?? '—' }}</td>
          <td>{{ item.history_count }}</td>
          <td class="actions" @click.stop>
            <button v-if="item.isin" @click="emit('refresh', item.isin)">↻</button>
            <button v-if="item.isin" class="danger" @click="emit('remove', item.isin)">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.table {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;
  margin: 1rem 0;
  overflow-x: auto;

  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid $color-bg; }
  tbody tr { cursor: pointer; &:hover { background: rgba(255, 255, 255, 0.04); } }
  tr.selected { background: rgba(56, 189, 248, 0.15); }
  .actions { display: flex; gap: 0.3rem; }
  .danger { background: $color-danger; }
}
</style>
```

- [ ] **Step 4: HistoryChart.vue**

```vue
<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { computed } from 'vue'
import { Line } from 'vue-chartjs'

import type { QuotePoint } from '../types'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend,
)

const props = defineProps<{ points: QuotePoint[]; currency: string | null }>()

const chartData = computed(() => {
  const ordered = [...props.points].reverse() // älteste zuerst
  return {
    labels: ordered.map((point) => point.quote_time),
    datasets: [
      {
        label: `Kurs${props.currency ? ` (${props.currency})` : ''}`,
        data: ordered.map((point) => point.price),
        borderColor: '#38bdf8',
        tension: 0.2,
      },
    ],
  }
})

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <section class="chart">
    <h2>Kurshistorie</h2>
    <p v-if="points.length === 0" class="empty">Kein Instrument gewählt oder keine Historie.</p>
    <div v-else class="canvas">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.chart {
  background: $color-surface;
  border-radius: $radius;
  padding: 1rem;

  .canvas { height: 320px; }
  .empty { color: $color-muted; }
}
</style>
```

- [ ] **Step 5: App.vue verdrahten**

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'

import EnvironmentPanel from './components/EnvironmentPanel.vue'
import HistoryChart from './components/HistoryChart.vue'
import InstrumentsTable from './components/InstrumentsTable.vue'
import Toolbar from './components/Toolbar.vue'
import { useEnvironment } from './composables/useEnvironment'
import { useHistory } from './composables/useHistory'
import { useInstrumentActions } from './composables/useInstrumentActions'
import { useInstruments } from './composables/useInstruments'
import { useRefresh } from './composables/useRefresh'

const { env, load: loadEnv } = useEnvironment()
const { instruments, load: loadInstruments } = useInstruments()
const { points, load: loadHistory } = useHistory()
const { refreshing, trigger } = useRefresh()
const { busy, add, refreshOne, remove } = useInstrumentActions()

const selectedIsin = ref<string | null>(null)
const selectedCurrency = ref<string | null>(null)

onMounted(async () => {
  await Promise.all([loadEnv(), loadInstruments()])
})

async function select(isin: string): Promise<void> {
  selectedIsin.value = isin
  selectedCurrency.value =
    instruments.value.find((item) => item.isin === isin)?.latest_currency ?? null
  await loadHistory(isin)
}

async function onRefreshAll(): Promise<void> {
  await trigger()
  await loadInstruments()
}

async function onAdd(identifier: string): Promise<void> {
  await add(identifier)
  await loadInstruments()
}

async function onRefreshOne(isin: string): Promise<void> {
  await refreshOne(isin)
  await loadInstruments()
  if (selectedIsin.value === isin) await loadHistory(isin)
}

async function onRemove(isin: string): Promise<void> {
  await remove(isin)
  if (selectedIsin.value === isin) {
    selectedIsin.value = null
    points.value = []
  }
  await loadInstruments()
}
</script>

<template>
  <main class="app">
    <h1>StockInfo Dashboard</h1>
    <Toolbar :refreshing="refreshing" :busy="busy" @refresh="onRefreshAll" @add="onAdd" />
    <EnvironmentPanel :env="env" />
    <InstrumentsTable
      :instruments="instruments"
      :selected-isin="selectedIsin"
      @select="select"
      @refresh="onRefreshOne"
      @remove="onRemove"
    />
    <HistoryChart :points="points" :currency="selectedCurrency" />
  </main>
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;

  h1 { color: $color-accent; }
}
</style>
```

- [ ] **Step 6: Build + Typecheck prüfen**

Run: `cd dashboard && npm run build`
Expected: `vue-tsc` ohne Typfehler, Build erzeugt `dist/`.

- [ ] **Step 7: Commit**

```bash
git add dashboard/src
git commit -m "feat(dashboard): UI-Komponenten (Toolbar, Environment, Tabelle, Chart) + App-Verdrahtung"
```

---

## Task 10: End-to-End-Verifikation

**Files:** keine (Verifikation).

- [ ] **Step 1: Backend-Tests + Lint**

Run: `.venv/bin/ruff check app tests && .venv/bin/pytest -q`
Expected: „All checks passed!" + alle Tests grün.

- [ ] **Step 2: Frontend-Tests + Build**

Run: `cd dashboard && npm run test && npm run build`
Expected: Vitest grün, Build ohne Fehler.

- [ ] **Step 3: Manueller End-to-End-Test**

```bash
# Terminal 1: Backend
make dev
# Terminal 2: ein Instrument anlegen, dann Dashboard
curl -s "http://localhost:8000/quote/IE00B3RBWM25" >/dev/null
cd dashboard && cp .env.example .env && npm run dev
```
Im Browser (http://localhost:5173) prüfen:
- EnvironmentPanel zeigt Config (XETR, TTL etc.).
- Tabelle zeigt VGWL.DE mit letztem Kurs und Punktzahl.
- „Hinzufügen" mit `US0846707026` → neue Zeile nach Reload.
- Zeilenklick → HistoryChart zeichnet die Linie.
- „↻" aktualisiert die Zeile, „✕" entfernt sie.
- „Alle aktualisieren" läuft ohne Fehler.

- [ ] **Step 4: Abschluss-Commit (falls Anpassungen nötig waren)**

```bash
git add -A
git commit -m "test(dashboard): End-to-End-Verifikation abgeschlossen"
```

---

## Self-Review Notes

- **Spec-Abdeckung:** DB-Visualisierung (Task 2/4/9 InstrumentsTable), Environment (Task 4/9 EnvironmentPanel), globaler Refresh (Task 3/4/8/9), Per-Instrument-Refresh (Task 3/4/8/9), Hinzufügen (Task 8/9 via `/quote`), Löschen (Task 2/3/4/8/9), History-Graph (Task 7/9 HistoryChart), CORS (Task 3/4), keine Auth (überall), Vitest/pytest (Task 6–10). Alle Spec-Punkte haben Tasks.
- **Typ-Konsistenz:** `InstrumentSummary`/`EnvInfo`/`QuotePoint`/`RefreshResult` identisch in Backend-Modellen (Task 1) und Frontend-Typen (Task 6). Emit-/Prop-Namen in Task 9 konsistent mit `App.vue`.
- **Platzhalter:** keine offen.
