# StockInfo — Analyse-Tab (Live-Timing) + Volatilität aus akkumulierendem EOD-Cache

**Datum:** 2026-08-10
**Status:** Design freigegeben

## Ziel

Zwei unabhängige Verbesserungen, motiviert durch eine Latenz-Analyse (Cache-Miss auf
Unraid bis 21 s, Cache-Hit 24 ms):

- **Feature A — Analyse-Tab:** Ein Diagnose-Menüpunkt im Dashboard, der für *ein* Asset
  den Live-Fetch instrumentiert ausführt und die Zeit **pro Stage** (OpenFIGI, fast_info,
  get_info, isin, History, justETF) plus Total anzeigt. Bringt die bisher manuelle
  `scripts/probe.py`-Messung als On-Demand-Funktion in die App — aus der Server-Umgebung.
- **Feature B — Volatilität aus dem akkumulierenden EOD-Cache:** Die 1-Jahres-Volatilität
  wird nicht mehr bei *jedem* Kurs-Fetch neu von yfinance geladen, sondern aus dem
  bereits existierenden, inkrementell akkumulierenden `daily_closes`-Cache berechnet.

## Motivation

Ein Cache-Miss löst heute eine Kette externer Calls aus. Zwei davon sind teuer und
liefern quasi-statische Daten: das justETF-Scraping und — vor allem — die
Volatilitätsberechnung. `quote_service._compute_volatility` (`app/services/quote_service.py:162`)
ruft bei **jedem** Live-Fetch `fetch_daily_closes(symbol, start=370 Tage)` **direkt** bei
yfinance ab und lädt so jedes Mal ein ganzes Jahr Tagesdaten neu.

Der inkrementelle, akkumulierende EOD-Cache existiert bereits — aber nur im
`DailyHistoryService` (`app/services/daily_history.py`), genutzt vom
`/quote/{isin}/daily`-Endpoint:

- Tabelle `daily_closes` mit `ON CONFLICT (instrument_id, date)`-Upsert → Daten
  akkumulieren, dedupliziert pro Tag (`app/repository.py:136`).
- `daily_meta`-Wasserzeichen (`fetched_from`/`fetched_to`) → es wird nur das Delta
  (`fetched_to → heute`) nachgeladen (`app/services/daily_history.py:77`).
- Wasserzeichen werden nur nach **erfolgreichem** Fetch fortgeschrieben → ein
  Provider-Fehler hinterlässt keine dauerhafte Datenlücke.

Feature B schließt die Volatilität an genau diesen Cache an. Damit gilt automatisch:
einmal geholte Jahresdaten bleiben erhalten, Folgeläufe holen nur das Delta, und über
Jahre App-Laufzeit akkumuliert die Historie (z. B. 10 Jahre) von selbst.

---

## Feature A — Analyse-Tab

### Backend

Neuer Endpoint im `dashboard`-Router:

```
GET /analyze?isin=<ISIN>      # entweder isin …
GET /analyze?symbol=<SYMBOL>  # … oder symbol (genau eines, sonst 422)
```

Antwortmodell `AnalyzeResult` (neu in `app/models.py`):

```
AnalyzeResult:
  symbol: str
  isin:   str | None
  total:  float                 # Sekunden
  stages: list[AnalyzeStage]

AnalyzeStage:
  stage:   str                  # "openfigi" | "fast_info" | "get_info" | "isin"
                                #  | "history" | "justetf"
  seconds: float
  status:  "ok" | "error" | "empty" | "skipped"
  detail:  str | None           # z. B. "257 rows", HTTP-Status, Fehlertyp
```

**Messlogik als wiederverwendbare Einheit.** Die Timing-Logik aus `scripts/probe.py`
wandert in eine neue Backend-Komponente `app/services/analyzer.py` (`QuoteAnalyzer`) —
kein Duplikat. Der Analyzer bekommt Resolver + Quote-Provider + ETF-Provider injiziert
(dieselben Instanzen wie der `QuoteService`, verdrahtet im `container.py`) und misst deren
Boundaries einzeln mit `time.perf_counter()`.

Verhalten:

- **Cache wird bewusst umgangen** — der Zweck ist die Messung des echten externen Pfades.
- Ablauf: Symbol bestimmen (bei ISIN via Resolver → das ist die `openfigi`-Stage; bei
  direkter Symboleingabe entfällt sie / `status="skipped"`), dann `fast_info`, `get_info`,
  `isin`, `history` (fester Zeitraum ~1 Jahr), `justetf` (nur wenn ETF, sonst `skipped`).
- Jede Stage ist **best-effort**: ein Fehler bricht die Analyse nicht ab, sondern wird als
  `status="error"` mit `detail` (Exception-Typ) erfasst; die Messung läuft weiter.
- Kein Persistieren, kein Verändern des Caches.

### Frontend

- Neuer Tab `analysis`: `TabKey` in `types.ts` erweitern, Eintrag in `AppHeader.vue`
  (`tabs`), Icon in `NavIcon.vue`, Routing in `App.vue` (`v-else-if activeTab === 'analysis'`).
- Neue Komponente `AnalysisPanel.vue`:
  - **Eingabe:** Dropdown der bestehenden Instrumente (aus `useInstruments`) **plus** ein
    Freitextfeld für ISIN **oder** Symbol. Button „Analysieren".
  - **Ausgabe:** Tabelle/Balken pro Stage (Stage · Dauer · Status/Detail) + Total-Zeile.
    Langsamste Stage(s) visuell hervorgehoben. Fehlerhafte Stages farblich markiert.
  - Ladezustand während der Messung (kann mehrere Sekunden dauern).
  - Kurzer Hinweistext: „Löst echte externe Abfragen aus (kein Cache)."
- Neues Composable `useAnalysis.ts` (analog `useEnvironment.ts`): ruft `/analyze` über
  `apiClient`, hält `result`/`loading`/`error`.
- API-Pfad in `api/paths.ts` ergänzen.
- **i18n:** neue Keys unter `nav.analysis` und `analysis.*` in `i18n/de.ts` **und**
  `i18n/en.ts` (Stage-Labels, Spaltenüberschriften, Hinweistext, Fehlermeldung).

### Fehlerbehandlung A

- Weder `isin` noch `symbol` gesetzt, oder beide → `422`.
- Instrument/Symbol nicht auflösbar → die `openfigi`-Stage ist `status="empty"`; die
  Analyse liefert trotzdem ein Ergebnis (die Kette bricht nicht hart ab). Der Endpoint
  gibt `200` mit dem Teil-Ergebnis zurück — Diagnose soll auch Fehlversuche zeigen.
- Frontend zeigt Backend-Fehler als dismissible Banner (bestehendes `ErrorBanner`-Muster).

---

## Feature B — Volatilität aus dem akkumulierenden EOD-Cache (Ansatz B1)

### Kernidee

Volatilität aus dem Kurs-Fetch **herauslösen**. `QuoteService._build` liefert nur noch den
Kurs (schnell, ohne 1-Jahres-Download). Die Volatilität wird in der Cache-/Scheduler-Schicht
(`CachedQuoteService`) berechnet, die Zugriff auf Repository und Daily-Cache hat.

### Änderungen

1. **`QuoteService._build`**: Der Block `if response.volatility is None: … _compute_volatility(...)`
   (`app/services/quote_service.py:142`) entfällt. `_compute_volatility` wird aus dem
   `QuoteService` entfernt. Volatilität aus justETF-Anreicherung (`_enrich_etf`) bleibt
   unverändert erhalten — sie wird, wenn vorhanden, weiter bevorzugt.

2. **Neue Berechnung in der Cache-Schicht.** `CachedQuoteService` bekommt Zugriff auf einen
   Volatilitäts-Helfer, der:
   - via der bestehenden inkrementellen `_sync`-Logik das Delta der `daily_closes`
     nachzieht (nur `fetched_to → heute`),
   - die letzten ~1 Jahr Closes aus `repository.get_daily_closes(instrument_id, start=~370d)`
     liest,
   - `annualized_volatility(closes)` (bleibt in `quote_service.py`, reine Funktion) anwendet,
   - das Ergebnis auf dem Instrument persistiert (`instruments.volatility`).

   Die Inkrement-Sync-Logik aus `DailyHistoryService._sync`/`_fetch_and_store` wird dafür
   wiederverwendet, nicht dupliziert.

   **Wichtig — Abhängigkeitsrichtung:** `DailyHistoryService` hängt bereits von
   `CachedQuoteService` ab (`app/container.py:42`). `CachedQuoteService` darf daher **nicht**
   umgekehrt von `DailyHistoryService` abhängen (Zyklus). Lösung: die inkrementelle
   Sync-Logik in eine eigenständige, zustandslose Einheit ziehen (z. B.
   `DailyCloseSync(repository, provider)`), die *beide* Services nutzen. `CachedQuoteService`
   bekommt dann `DailyCloseSync` + eine reine Volatilitäts-Berechnung injiziert — nicht den
   `DailyHistoryService`.

3. **Wann wird gerechnet.** Volatilität wird beim **Refresh** aktualisiert
   (`refresh_all` im Scheduler, `refresh_one`), nicht im lesenden Cache-Hit-Pfad. Ein
   normaler Kurs-Request bleibt damit schlank. Fehlt die Volatilität bei einem erstmalig
   angelegten Instrument, wird sie beim ersten Refresh nachgezogen.

4. **Akkumulation.** Kein neuer Speicher-Mechanismus nötig — `daily_closes` wächst via
   Upsert-by-date weiter. Über Jahre steht die volle Historie zur Verfügung; die
   Volatilität nutzt daraus jeweils das letzte Jahr.

### Auswirkung

- Pro Refresh entfällt der direkte 1-Jahres-Download; stattdessen nur noch ein Delta-Fetch
  (meist wenige Tage) — und das nur, wenn `daily_closes` nicht ohnehin schon aktuell ist.
- Weniger externe Calls = geringere Rate-Limit-Exposure = seltenere Latenz-Spikes.
- Das `metadata_ttl_days`-Setting bleibt vorerst unangetastet (separates Thema); es wird
  durch diesen Ansatz nicht benötigt, weil die Delta-Logik über die `daily_meta`-Wasser-
  zeichen ohnehin nichts Doppeltes holt.

### Fehlerbehandlung B

- Delta-Fetch schlägt fehl (Netz/Rate-Limit) → Wasserzeichen bleiben stehen (bestehendes
  Verhalten), Volatilität behält den letzten bekannten Wert auf dem Instrument.
- Zu wenige Datenpunkte (< 5) → `annualized_volatility` liefert `None`; Volatilität bleibt
  leer, kein Fehler.

---

## Nicht im Scope (YAGNI)

- Passives Monitoring / Persistenz historischer Analyse-Läufe (nur On-Demand-Messung).
- Zugriffsschutz/Authentifizierung für den Analyse-Tab (interne App).
- justETF-Timeout-Kappung und `metadata_ttl_days`-Verdrahtung (eigene, spätere Themen).
- Stale-while-revalidate im Request-Pfad (verworfen: würde veraltete Kurse ausliefern).

## Testing

**Feature A**
- `analyzer.py`: Unit-Tests mit Fake-Providern (deterministische Dauern/Fehler) → prüfen,
  dass alle Stages erfasst werden, Fehler die Kette nicht abbrechen, `skipped`/`empty`
  korrekt gesetzt sind.
- Endpoint-Test (`tests/test_api_dashboard.py`-Stil): `422` bei fehlender/doppelter
  Eingabe; `200` mit Stage-Liste im Normalfall; Cache wird nicht verändert.
- Frontend: `AnalysisPanel`/`useAnalysis` Vitest — Rendern der Stages, Lade-/Fehlerzustand.

**Feature B**
- Volatilität wird aus gecachten `daily_closes` berechnet, ohne dass der Quote-Provider
  bei einem reinen Kurs-Fetch `fetch_daily_closes` aufruft (Fake-Provider zählt Aufrufe).
- Delta-Sync: zweiter Refresh holt nur neue Tage (Wasserzeichen-Verhalten).
- Bestehende Tests (`test_quote_service`, `test_daily_history`, `test_refresh`) bleiben grün
  bzw. werden an die verschobene Volatilitätslogik angepasst.

## Betroffene Dateien (Überblick)

**Backend:** `app/models.py` (AnalyzeResult/Stage), `app/services/analyzer.py` (neu),
`app/routers/dashboard.py` (`/analyze`), `app/container.py` (Analyzer + Volatilitäts-
Verdrahtung), `app/services/quote_service.py` (Volatilität raus), `app/services/quote_cache.py`
(Volatilität rein), `app/services/daily_sync.py` (neu — gemeinsame `DailyCloseSync`-Einheit),
`app/services/daily_history.py` (nutzt `DailyCloseSync` statt eigener `_sync`-Logik).

**Frontend:** `dashboard/src/types.ts`, `AppHeader.vue`, `NavIcon.vue`, `App.vue`,
`components/AnalysisPanel.vue` (neu), `composables/useAnalysis.ts` (neu), `api/paths.ts`,
`i18n/de.ts`, `i18n/en.ts`.

**Sonstiges:** `scripts/probe.py` bleibt als eigenständiges Container-Tool erhalten.
