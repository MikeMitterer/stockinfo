# Spec: StockInfo-Dashboard

## Context

StockInfo ist eine Python/FastAPI-App, die Aktien-/ETF-Kurse per REST liefert und
in SQLite cacht (Instrumente + Kurs-Zeitreihe), mit Lazy-TTL und periodischem
Hintergrund-Refresh. Bisher gibt es nur `/health` und die `/quote`-Endpoints.

Gebraucht wird ein **eigenständiges TypeScript-Dashboard**, das den Zustand der App
sichtbar macht und steuerbar: den **DB-Inhalt** (welche Wertpapiere sind gecacht,
mit letztem Kurs), das **Environment/Config**, mindestens ein **aktives Element**
(Kursdaten aktualisieren) sowie einen **Graph der Kurshistorie**.

## Ziele

- DB-Visualisierung: Liste aller gecachten Instrumente mit letztem Kurs und
  Anzahl History-Punkte.
- Environment-Visualisierung: aktuelle Konfiguration (TTL, Intervalle,
  Default-Börse, DB-Pfad, Version, Host/Port); Secrets nur als „gesetzt/nicht".
- Aktive Elemente: globaler Refresh, Per-Instrument-Refresh, Instrument
  hinzufügen (ISIN/Symbol), Instrument löschen.
- Kurshistorie als Liniengraph pro Instrument.

## Entscheidungen (aus Brainstorming)

- **Stack:** Vue 3 + Vite + TypeScript + **SCSS**.
- **Chart:** Chart.js (+ vue-chartjs).
- **Ort:** Unterordner `dashboard/` im StockInfo-Repo.
- **Auth:** vorerst keine (API_KEY leer); Dashboard und API laufen lokal.
- **Architektur:** SPA gegen die FastAPI-API; Backend wird um Read-/Admin-Endpoints
  erweitert. (Verworfen: Dashboard liest die SQLite-Datei direkt — bricht die
  eigenständige-App-Grenze und funktioniert nicht über Docker/Netz.)

## Architektur

```
Browser (Vue-SPA, dashboard/)
   │  fetch (VITE_API_BASE_URL, Default http://localhost:8000)
   ▼
FastAPI (app/) ── dashboard-Router (neu) + quotes-Router (bestehend)
   ▼
CachedQuoteService / QuoteRepository ── SQLite
```

Komponente → Composable → `api/client` → FastAPI. Kein API-Call in Komponenten
(laut code-standards). Loading/Error-State lebt im Composable.

## Backend-Erweiterung (app/)

Neuer Router `app/routers/dashboard.py`, eingehängt in `main.py`. CORS-Middleware
(`allow_origins` aus neuer Setting `cors_origins`, Default `["http://localhost:5173"]`;
`allow_credentials=False`, da keine Auth — vermeidet die `*`+credentials-Falle).

### Endpoints

- `GET /instruments` → `list[InstrumentSummary]`
  - Felder je Instrument: `isin, symbol, exchange, name, type, currency, provider,
    ter, replication, fund_size, meta_fetched_at, latest_price, latest_quote_time,
    latest_currency, latest_fetched_at, history_count`.
  - Repo: neue Methode `list_instruments_with_latest()` (Instrument + jüngster
    Quote-Join + `COUNT(quotes)`).
- `GET /env` → `EnvInfo`
  - `version, database_path, cache_ttl_hours, refresh_interval_hours,
    metadata_ttl_days, default_exchange, host, port, api_key_set: bool,
    openfigi_key_set: bool`. Keine Secret-Werte, nur Booleans.
- `POST /refresh` → `RefreshResult { total, refreshed }` — ruft `refresh_all()`.
- `POST /refresh/{isin}` → `QuoteResponse` — force-refresh eines Instruments
  (TTL umgangen). Service: neue Methode `refresh_one(isin)`.
- `DELETE /instruments/{isin}` → `204` — Repo: neue Methode `delete_instrument(isin)`
  (löscht Instrument; Quotes via `ON DELETE CASCADE`). `404`, wenn unbekannt.
- **Hinzufügen:** kein neuer Endpoint — Dashboard ruft `GET /quote/{isin}` bzw.
  `GET /quote?symbol=` (löst auf + cacht + legt Instrument an).
- **Graph:** bestehendes `GET /quote/{isin}/history?from=&to=&limit=`.

### Neue Pydantic-Modelle
`InstrumentSummary`, `EnvInfo`, `RefreshResult` in `app/models.py`.

## Frontend (`dashboard/`)

Vite-Projekt, Vue 3 `<script setup lang="ts">`, TypeScript strict, SCSS.

```
dashboard/
  index.html
  package.json          # vue, vue-chartjs, chart.js, consola; dev: vite, vitest, sass, typescript, vue-tsc
  vite.config.ts
  tsconfig.json
  .env.example          # VITE_API_BASE_URL=http://localhost:8000
  src/
    main.ts
    App.vue             # Layout: Toolbar + EnvironmentPanel + InstrumentsTable + HistoryChart
    api/client.ts       # typisierter fetch-Wrapper (get/post/del), Basis-URL, Fehlerbehandlung
    types.ts            # InstrumentSummary, EnvInfo, QuotePoint, RefreshResult
    composables/
      useInstruments.ts        # Liste laden (GET /instruments)
      useEnvironment.ts        # GET /env
      useHistory.ts            # GET /quote/{isin}/history
      useRefresh.ts            # POST /refresh (global)
      useInstrumentActions.ts  # add (GET /quote), refreshOne (POST /refresh/{isin}), remove (DELETE)
    components/
      Toolbar.vue         # globaler Refresh-Button + AddInstrument-Formular (ISIN/Symbol)
      EnvironmentPanel.vue
      InstrumentsTable.vue # Zeilen mit Aktionen (Refresh/Löschen), Auswahl → Chart
      HistoryChart.vue     # Chart.js-Linienchart der Kurshistorie
    styles/
      _variables.scss
      base.scss
  tests/
    useInstruments.spec.ts  # fetch gemockt
    useInstrumentActions.spec.ts
    api-client.spec.ts
```

### Composable-Vertrag (einheitlich)
Jedes Composable gibt reaktive `data`/`loading`/`error` + Aktions-Funktionen zurück
(Muster aus code-standards). `vi.mock` vor Imports in Tests.

### Chart
`HistoryChart.vue` bekommt `points: QuotePoint[]` als Prop und rendert eine Linie
(x = `quote_time`, y = `price`). Währung im Achsen-/Tooltip-Label.

## Datenfluss (Beispiele)

- Start: `App.vue` lädt `useEnvironment` + `useInstruments`.
- Zeilenklick: `useHistory.load(isin)` → `HistoryChart` zeigt Linie.
- „Aktualisieren" (global): `useRefresh.trigger()` → danach `useInstruments.reload()`.
- „Hinzufügen": `useInstrumentActions.add(isinOrSymbol)` → `useInstruments.reload()`.
- „Löschen": `useInstrumentActions.remove(isin)` → Liste + Chart aktualisieren.

## Fehlerbehandlung

- `api/client` wirft bei non-2xx einen typisierten Fehler mit Status + Detail.
- Composables fangen ihn, setzen `error`, loggen mit `consola` (kein stilles
  Schlucken). UI zeigt generische Meldung; Details im Log.

## Testing

- Backend: pytest für die neuen Repo-Methoden (`list_instruments_with_latest`,
  `delete_instrument`) und die neuen Endpoints (TestClient, Service gemockt).
- Frontend: Vitest für Composables und `api/client` (globales `fetch` gemockt).

## Verifikation (End-to-End)

1. Backend: `make dev`; `curl /instruments`, `/env`, `POST /refresh`,
   `POST /refresh/{isin}`, `DELETE /instruments/{isin}` liefern erwartete Codes.
2. Dashboard: `cd dashboard && npm install && npm run dev`; Tabelle zeigt gecachte
   Instrumente, EnvironmentPanel zeigt Config, globaler Refresh + Zeilen-Aktionen
   funktionieren, Zeilenklick zeigt den Kurshistorie-Graph.
3. `npm run test` (Vitest) und `pytest` grün.

## Aus dem Scope (vorerst)

- Keine Auth (API_KEY leer).
- Keine Dockerisierung des Dashboards.
- Keine Makefile-Targets fürs Dashboard (npm-Scripts genügen; bei Bedarf später).
- Keine Bearbeitung von Config-Werten im UI (Environment ist read-only).
