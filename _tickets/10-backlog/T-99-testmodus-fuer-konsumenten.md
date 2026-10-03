# T-99 · Testmodus für Konsumenten ohne Zugriff auf StockInfos Innenleben

StockPortfolio braucht für sichtbare Browserprüfungen einen **echten
StockInfo-Server mit festen Testkursen**, ohne Netz und mit leerer
temporärer Datenbank. StockInfo bietet dafür keinen Startweg von außen.
StockPortfolio baut den Server deshalb selbst aus StockInfos internen
Modulen zusammen und bricht bei jedem internen Umbau, obwohl sich die
HTTP-Schnittstelle nicht ändert.

**Beispiel:** Nach dem Umzug der Persistenz nach `app/persistence/`
(`2b5f908`, 2026-10-02) startete StockPortfolios Teststack nicht mehr:

```text
File "…/StockPortfolio/scripts/stockinfo-test-server.py", line 207, in run_single_server
    from app.db import init_db
ModuleNotFoundError: No module named 'app.db'
```

StockPortfolio hat die zwei Importe in seinem T-81 nachgezogen. Der nächste
Umbau trifft es wieder.

**Zweites Beispiel, am selben Tag:** Seit T-94 (`8991a55`, 2026-10-02)
erwartet StockInfo von einer Devisenquelle `FxQuote` mit Kurs und Zeitpunkt
statt einer Zahl. StockPortfolios lokale Devisenquelle lieferte weiter die
Zahl; `GET /fx?base=USD&quote=EUR` antwortete mit HTTP 500:

```text
File "…/StockInfo/app/services/fx_service.py", line 157, in _fetch_or_fallback
    self._repository.save_fx_rate(base, quote, found.rate, found.quote_time, now, source)
AttributeError: 'float' object has no attribute 'rate'
```

Ohne CORS-Header in der Fehlerantwort meldete der Browser zuerst einen
CORS-Fehler; USD-Positionen ließen sich im Teststack nicht mehr umrechnen.
Der Stack meldete sich trotzdem bereit, weil seine Startprüfung `/fx` nicht
abfragte. StockPortfolio hat die Quelle in seinem T-79 auf `FxQuote`
umgestellt und prüft `/fx` jetzt beim Start. Diesmal brach also keine
Modulstruktur, sondern die Schnittstelle einer Quelle.

**Stand:** Angelegt am 2026-10-03 aus StockPortfolio auf Mikes Auftrag
(„ja, leg das Ticket im StockInfo-Board an“). Zweites Beispiel am selben Tag
ergänzt (Mike: „ja, ergänze das in T-99“). Noch nicht eingeplant. Für Mike ist
aktuell kein Handgriff nötig.

## Ausgangslage aus Konsumentensicht

StockPortfolios `scripts/stockinfo-test-server.py` lädt `app.main.app` im
eigenen Prozess und ersetzt die externen Quellen. Dafür kennt es heute:

| StockInfo-Innenleben | Wofür StockPortfolio es braucht |
|---|---|
| `app.persistence.db.init_db`, `app.persistence.repository.QuoteRepository` | Temporäre Datenbank anlegen und mit Testinstrumenten füllen |
| `QuoteService`, `CachedQuoteService`, `DailyHistoryService`, `DailyCloseSync`, `CachedFxService` | Dienste mit lokalen Quellen neu zusammensetzen |
| `get_cached_quote_service`, `get_daily_history_service`, `get_fx_service` | Per `dependency_overrides` in der App austauschen |
| `app.providers.base.RawQuote`, `FxQuote`, `SourceAnswer`, `stockinfo_plugin.types.NotFound` | Antworten der lokalen Kurs-, Verlaufs- und Devisenquelle bauen; die Form dieser Antworten (seit T-94 `FxQuote`) ist ebenfalls Innenleben |
| `app.detail_models.DetailDefinition`, `DetailInput` | Detailwerte (TER, Fondsgröße, Anbieter) vorbelegen |
| `app.routers.migration.get_gate` | Migrationssperre starten |
| `tests.boundaries.EmptyEtfEnricher` | ETF-Anreicherung abschalten — eine Klasse aus StockInfos Testordner |

Was StockPortfolio dabei erwartet:

- **Echte Routen und echtes Verhalten:** Validierung, Cache, SQLite und
  Antwortformen wie im Betrieb. Ein nachgebauter Fake-Server prüfte nur
  StockPortfolios eigene Annahmen.
- **Feste Testdaten:** Instrumente mit Identität, Kurs, Währung, Verlauf,
  Devisenkursen und Detailwerten aus einer Datei, die StockPortfolio
  mitbringt. Darunter bewusste Randfälle (Kryptopaar, OTC-Anleihe,
  mehrdeutiges Symbol, Pence-Listing) und ein lesbarer Demobestand.
- **Kein Netz, keine Arbeitsdaten:** keine Abrufe bei Quellen, kein
  Start-Scheduler, Datenbank nur im temporären Ordner.
- **Gezielte Fehlantworten:** StockPortfolio speist heute über eine eigene
  Middleware Fehler ein (zum Beispiel 503 für den Typkatalog), um seine
  Fehlermeldungen zu prüfen.
- **CORS** für die Browser-Herkunft des Teststacks (`http://127.0.0.1:5175`).

## Auswirkung

- Jeder interne Umbau in StockInfo kann StockPortfolios Browserprüfungen
  stilllegen; der Fehler fällt erst beim nächsten Start auf, oft mitten in
  einem fremden Ticket.
- StockPortfolio muss StockInfos Klassen, Konstruktoren und Testordner
  kennen. Das widerspricht der Trennung: StockPortfolio soll nur den
  HTTP-Vertrag kennen.
- StockInfos Umbauten werden unnötig riskant: Wer dort Module verschiebt
  oder die Schnittstelle einer Quelle ändert, sieht nicht, dass ein anderes
  Repository davon abhängt. Zwei Brüche an einem Tag (Persistenz-Umzug und
  T-94) zeigen, dass es kein Einzelfall ist.

## Gewünschtes Ergebnis

Ein Konsument startet einen StockInfo-Testserver über einen dokumentierten,
stabilen Weg und übergibt nur Testdaten und Port. Er braucht dafür keine
Kenntnis von StockInfos Modulen. Wie das aussieht — Startoption,
Umgebungsvariable, eigene Testquelle als Plugin, Datenformat, Umgang mit
Fehlantworten — entscheidet, wer StockInfo kennt.

## Akzeptanzkriterien

- [ ] Ein dokumentierter Startweg liefert StockInfos echte Routen mit
      Testdaten aus einer Datei, ohne Netz und mit temporärer Datenbank.
- [ ] Der Startweg gilt als Teil des Vertrags: Interne Umbauten halten ihn
      stabil, Änderungen werden wie Vertragsänderungen angekündigt.
- [ ] Die Testdaten decken Kurs, Verlauf, Devisenkurse und Detailwerte ab.
- [ ] Es gibt einen Weg, gezielte Fehlantworten zu erzeugen, oder eine
      begründete Abgrenzung, warum das beim Konsumenten bleibt.
- [ ] Die Anleitung beschreibt Aufruf, Datenformat und Grenzen für fremde
      Leser.

## Folgen für StockPortfolio

Ist der Startweg da, stellt StockPortfolio `scripts/stockinfo-test-server.py`
in einem eigenen Ticket auf ihn um und entfernt alle Importe aus StockInfo.
Das geschieht im StockPortfolio-Board, nicht hier.
