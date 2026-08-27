# T-27a · Contract-Kit für alle Rollen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | wartet · Plugin-MVP 2/4 | zu schätzen | öffentliches Testkit — Contracts, Szenarien, Doubles | — |

**Löst:** Heute gibt es `ResolverContract` und `MetadataContract` — zwei von
fünf Rollen. Ein Plugin kann damit die ISIN-Auflösung nachweisen und bliebe für
Kurse, Historie und Devisen trotzdem implizit an yfinance gebunden.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-22 für die vollständige Rollenabdeckung (`DailyCloseProvider`
und `FxProvider` fehlen dort noch als Protokolle).
**Muss vor Abschluss von T-23 stehen** — T-23 braucht die Doubles als
Abnahmemittel, und die App ist laut T-23 selbst der erste Plugin-Autor.

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** T-22 → **T-27a** →
> T-27b → T-23. Erst nach Codex-Freigabe von T-22 beginnen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Contract-Suite je Rolle | alle fünf vorhanden: Resolver, Metadata, Quote, Daily, FX | | |
| 2 | Quote-Contract | Preis **mit Pflichtwährung**, endliche Werte, Fehler statt geratener Ersatzwerte | | |
| 3 | Daily-Contract | Datum, Schlusskurs, Währung, Sortierung, **keine Duplikate**, adjusted/unadjusted deklariert | | |
| 4 | FX-Contract | Base/Quote, positive endliche Rate, Zeitpunkt, Identitäts- und Fehlerfall | | |
| 5 | fachliche Invarianten | ISIN-Prüfziffer, Anfrage-ISIN = Ergebnis-ISIN, **echter MIC statt Sammelcode**, gültige Währung, sinnvolle Datumsfolge | | |
| 6 | Szenarioformat | ein Fall wird **einmal** beschrieben; Format, Validierung und ein **transportneutraler** Runner-Vertrag stehen. Dass derselbe Fall offline **und** real läuft, nimmt T-27b ab | | |
| 7 | Golden Cases | erwarteter Ticker/MIC stammt **nicht** aus der Aufzeichnung, sondern aus gepflegten Daten | | |
| 8 | `FakeSource` | vorgebbare Antwort je Anfrage, Aufrufprotokoll für Reihenfolge und Anzahl | | |
| 9 | Fake-Uhr | TTL, Half-open und Reset ohne echte Wartezeit prüfbar | | |
| 10 | globaler Zustand | zwei Testfälle beeinflussen sich nicht | | |
| 11 | `make test-plugin-api` | grün | | |

---

## Details

### Fünf Rollen, fünf Contract-Suiten

| Rolle | Verbindliche Prüfungen |
|---|---|
| Resolver | Zuständigkeit, bekannt, unbekannt, Fehler, gültiger Ticker und **echter** MIC |
| Metadata | deklarierte Felder, Typ, Einheit, Währung bei Beträgen, Herkunft, Plausibilität |
| Quote | Preis und **Pflichtwährung**, Zeitpunkte, endliche Werte, Fehler statt Raten |
| Daily | Datum, Schlusskurs, Währung, Sortierung, keine Duplikate, adjusted/unadjusted |
| FX | Base/Quote, positive endliche Rate, Zeitpunkt, Identitäts- und Fehlerfall |

Gemeinsam für alle: stabiler eindeutiger Name, unterstützte `api_version`,
verständliche Diagnose bei fehlender Pflichtkonfiguration, kein Durchreichen
fremder Ausnahmen, nur deklarierte Ergebnisarten, klarer Unterschied zwischen
*nicht zuständig*, *nicht gefunden* und *vorübergehend nicht verfügbar*, und
kein veränderter globaler Zustand zwischen zwei Fällen.

### Fachliche Prüfung geht weiter, als ich angenommen hatte

Ich hatte formuliert, Contract-Tests bewiesen „Form und Fehlerverhalten, nicht
fachliche Richtigkeit". Das war zu pessimistisch. Maschinell prüfbar sind
durchaus: ISIN-Prüfziffer, Übereinstimmung von Anfrage- und Ergebnis-ISIN,
echter MIC statt Sammelcode, gültige Währung, endliche Zahlen, sinnvolle
Datumsreihenfolge, keine doppelten Tagespunkte, Typ- und Einheitenverträglichkeit
sowie die deklarierten Plausibilitätsgrenzen.

**Was bleibt:** Ob der Anbieter bei einem *zukünftigen* Papier das gewünschte
Listing wählt, beweist kein Test. Auch ein formal korrektes `(ticker, mic)` kann
fachlich das falsche Listing sein. Golden Cases erhöhen die Sicherheit
erheblich, ersetzen aber niemanden, der den Markt kennt — und genau so gehört es
in die Plugin-Dokumentation.

### Ein Szenario, zwei Betriebsarten

Ein Autor beschreibt seine Fälle **einmal**: stabile Fall-ID, Anfrage, erwartete
Ergebnisart, bei bekannten Papieren die unabhängig festgelegten Kernwerte,
optionale Plausibilitätsregeln für dynamische Werte, und ob der Fall im
Real-Modus laufen darf.

Derselbe Fall läuft dann als **Replay** (deterministisch, ohne Netz, bei jedem
Commit) und als **Real** (gegen den echten Anbieter, vor einem Release).

**Die Abnahme dieser beiden Betriebsarten liegt bei T-27b**, nicht hier: Der
HTTP-Runner, der sie umsetzt, gehört dorthin — und T-27b hängt an T-27a. Hier
wird nur das gemeinsame Format samt Validierung und ein transportneutraler
Runner-Vertrag abgenommen, damit T-27a fertig sein kann, bevor T-27b darauf
aufbaut.

**Der wichtigste Fallstrick:** Der erwartete Ticker und MIC dürfen **nicht** aus
der Aufzeichnung erzeugt werden. Sonst bestätigt der Test nur, dass ein
möglicherweise falscher Treffer reproduzierbar falsch ist. Golden-Erwartungen
sind kleine, bewusst geprüfte Daten und werden getrennt von den
Anbieter-Aufzeichnungen gepflegt.

### Doubles — Werkzeug hier, Verantwortung beim Host

Das Kit liefert skriptbare Doubles: vorgegebene Antwort je Anfrage,
Aufrufprotokoll für Reihenfolge und Anzahl, alle vier Ergebnisarten plus
Ausnahme und ungültige Antwort, steuerbare Verzögerung, Fake-Uhr.

**Kein** behaupteter Abbruch eines endlos hängenden Aufrufs — siehe T-23.

Die Kettensemantik selbst bleibt beim Host: T-20 prüft die Aggregation bis zum
HTTP-Status, T-23 Reihenfolge, Registry und Schutzschalter, T-26 Merge und
REST-Projektion, T-25 die Profilrotation. So wird das öffentliche Kit nicht mit
StockInfo-Interna beladen.

---

## Auflösung

_(offen)_
