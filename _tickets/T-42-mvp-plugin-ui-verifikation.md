# T-42 · MVP plugin UI verification

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (laufender Stack) | Nacharbeit nach Codex-Runde 3 | Konzept 2 h, Lauf 3 h | risikobasierte Browser-Abnahme der fertigen Plugin-Kette; danach dieselbe kurze Matrix für Mike | — |

- **Angelegt:** 2026-08-31, nach technischer Freigabe von T-39
- **Hängt ab von:** T-31, T-38, T-37, T-41, T-35 und T-39 freigegeben
- **Reihenfolge:** nächstes aktives Ticket; T-40 ruht bis zu Mikes
  ausdrücklichem Kommando

**Löst:** Die Plugin-Implementierung ist technisch geprüft, aber Mike braucht
eine kurze, belastbare Abnahme aus Benutzersicht. Claude entwirft zuerst die
Browser-Matrix aus den tatsächlich umgesetzten Tickets; Codex prüft das
Konzept. Erst danach läuft Claude die freigegebenen Fälle im Browser, behebt
kleine eindeutig lokale Fehler und übergibt dieselbe Matrix an Mike.

---

## Scope-Vertrag

### Phase A · Konzept, noch kein Browserlauf

- Die freigegebenen Plugin-Tickets werden als Inventar gelesen; alte
  Zwischenstände und T-28 erzeugen keine Anforderungen.
- Höchstens **12 sichtbare Fälle** decken die Risikogrenzen ab, nicht jede
  frühere Verify-Zeile einzeln.
- Jeder Fall nennt Profil, Eingabe, sichtbares Ergebnis, erwartete Quelle und
  den einen Fehler, den er unterscheiden soll.
- Das Konzept geht vollständig an Codex. Vor dessen `approved` gibt es weder
  Browserlauf noch Produktänderung.

### Phase B · Claude-Browserlauf

- Zwei reale Profile: reines Ein-Datei-YAML und Online/YFinance mit demselben
  YAML-Plugin als letztem Fallback.
- Sichtbare Kernfälle: normale Aktie/ETF, `BTC-EUR`, Anleihe mit manueller
  History, `fund`, mindestens eine Online-/YAML-Überlappung sowie FX.
- Geprüft werden Aufnahme, Liste, Drilldown, Preis/Herkunft, Historie,
  Metadaten, `/sources`-Diagnose, Neustart/Persistenz und relevante
  Fehlermeldungen — aber nur dort, wo der Fall die Plugin-Kette wirklich
  unterscheidet.
- Claude dokumentiert Konsole und fehlgeschlagene Requests. Ein grüner
  Screenshot ohne Datenherkunft ist kein Beleg.

### Fehlerbehandlung und Grenze

- Ein kleiner, eindeutiger lokaler Fehler darf im Ticket korrigiert und erneut
  geprüft werden. Sobald Vertrag, Schema, neue UI-Fläche, Abhängigkeit oder
  mehr als drei Produktdateien nötig werden, stoppt Claude vor dem Edit am
  Scope-Checkpoint.
- Keine neue Browser-Testinfrastruktur, kein Record/Replay, keine dauerhafte
  E2E-Suite und keine Wiederholung aller Backend-/Contract-Tests als eigene
  Fälle.
- Human-Spalte bleibt bis zu Mikes Lauf leer. Claude schreibt dort niemals.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung · ◑ teilweise ·
➖ keine Live-Verifikation · `AI` nur KI · `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Konzept-Handoff an Codex | höchstens 12 Fälle; jeder unterscheidet einen benannten Plugin-Fehler und nennt Profil, Eingabe, Ergebnis und Quelle | ✅ [^concept-r1] | |
| **2** | YAML-Profil im Browser | BTC, Anleihe/History und Fonds lassen sich aufnehmen und bleiben nach Neustart mit korrekter Gattung und Herkunft sichtbar | ✅ | |
| **3** | Online-Profil im Browser | Online gewinnt bei Überlappung; YAML schließt eine echte Lücke; Aktie/ETF, BTC, Bond und `fund` sind vertreten | ✅ | |
| **4** | Rollen im UI/Netzwerk | Resolver, Quote, Daily, Metadaten und FX werden mindestens einmal über einen echten Eintrittspfad unterschieden | ✅ | |
| **5** | Diagnose und Fehler | `/sources`, sichtbare Fehlermeldungen, Konsole und fehlgeschlagene Requests widersprechen dem angezeigten Zustand nicht | ⚠️ [^fx] | |
| **6** | Regression | betroffene Tests, beide Profil-Smokes, Ruff, Build und vollständiges `make test` sind nach dem finalen Browserstand grün | ✅ | |
| **7** | Mike-Handoff | dieselben kurzen Schritte sind ohne Entwicklungswissen nachvollziehbar; Human-Spalte ist leer und bereit zur Abnahme | ✅ | |

[^fx]: Der FX-Fehlerweg meldet einen Sachverhalt falsch — siehe „Zwei
    Befunde am Fehlerweg" unten. Er ist gemessen, nicht behoben: Ein
    Statuscode ist REST-Vertrag und damit checkpoint-pflichtig.

[^concept-r1]: Codex hat Phase A gegen `a0fc993` geprüft und drei rein
    textuelle Ausführungsdetails in `fab3540` präzisiert. Phase B ist damit
    freigegeben; die übrigen Zeilen bleiben bis zum echten Lauf offen.

---

## Phase A · Das Konzept (2026-08-31)

**Zwölf Fälle, und jeder ist gegen einen Fehler geschrieben, den es gab.** Die
Herkunftsspalte nennt ihn: fast jede Zeile unten stammt aus einem Befund, der
in einem der freigegebenen Tickets wirklich aufgetreten ist. Ein Fall, der
keinen benannten Fehler unterscheidet, prüft nur, dass die App startet.

Profil **Y** = reines Ein-Datei-YAML (`yaml-file` in allen fünf Rollen).
Profil **O** = Online/YFinance mit demselben `yaml-file` als letztem Glied
jeder Kette, einschließlich `resolvers`.

### Profil Y — die Identitätsformen und die Gattungen

| # | Eingabe | Sichtbar erwartet | Quelle | Unterscheidet den Fehler |
|---|---|---|---|---|
| **Y1** | `BTC-EUR` | Zeile `CRYPTO`, 94.500,00 EUR, ISIN-Spalte sagt „hat keine — Währungspaar" | `yaml-file` | Ein Papier ohne Börse ist nicht aufnehmbar oder bekommt eine erfundene — die `pair`-Form aus T-31 |
| **Y2** | `DE0001102531` | Zeile `BOND`, 99,42 EUR; Tagesreihe zeigt **drei** Punkte (99,18 / 99,31 / 99,42) | `yaml-file` | Ohne `price` bleibt die Anleihe preislos, statt den jüngsten gepflegten Schlusskurs zu nehmen (T-37 `#5`) |
| **Y3** | `DE0009848119` | Zeile **`FUND`**, 142,50 EUR; im Drilldown ein Hinweis, der **keine** Gattung behauptet | `yaml-file` | Ein Publikumsfonds erscheint als `etf` und löst damit die ETF-Anreicherung aus (T-35 Befund B); der Hinweis nennt jedes Nicht-ETF „eine Aktie" (T-35 Befund C) |
| **Y4** | Neustart des Dienstes auf **derselben** Datenbank | Alle drei Papiere unverändert sichtbar; `GET /migration` meldet `pending: false` | — | Ein regulär aufgenommenes Krypto-Papier versetzt die App beim nächsten Start in den Migrationszustand und bietet an, es zu löschen (T-35 Befund A) |

### Profil O — die Kaskade

| # | Eingabe | Sichtbar erwartet | Quelle | Unterscheidet den Fehler |
|---|---|---|---|---|
| **O1** | `IE00B4L5Y983` | Kurs **und** TER, Anbieter, Domizil im Drilldown; „Quelle: justetf" | Kurs yfinance, Metadaten justETF | Fehlt die Gattung, wird die Metadatenquelle **gar nicht erst** gefragt — leer ohne Meldung (T-38 `#5`) |
| **O2** | dasselbe Papier, das die YAML-Datei mit **abweichendem** Wert führt | der **Online**-Wert steht da, nicht der aus der Datei | yfinance | Die Datei überschreibt einen gültigen Online-Treffer (T-37 `#4`) |
| **O3** | `DE0001102531` | 99,42 EUR aus der Datei — obwohl online kein Kurs existiert | `yaml-file` | Die Kette bricht nach der ersten Quelle ab (T-41); und ohne `yaml-file` in `resolvers` scheitert schon die **Aufnahme** (T-35, Doku-Befund) |
| **O4** | `/fx` CAD→EUR; temporäre lokale Quelle `fx-miss` antwortet zuerst mit `NotFound` | Kurs erscheint, Feld „Quelle" nennt **`yaml-file`** | `yaml-file` | Die Herkunft nennt die Quelle, die vorn steht, statt der, die geliefert hat (T-41 Runde 2) |
| **O5** | `XX0000000000` | verständliche Meldung mit der Kennung im Text; **keine** neue Zeile; genau **ein** fehlgeschlagener Request | — | „Hinzufügen fehlgeschlagen" ohne Grund, und eine halbe Zeile bleibt in der Datenbank zurück (T-35 Befund 4) |

### Das fremde Plugin über den Entry-Point

| # | Eingabe | Sichtbar erwartet | Quelle | Unterscheidet den Fehler |
|---|---|---|---|---|
| **P1** | `stockinfo-source-us-example==0.1.0` gepinnt, Neustart, dann `US0378331005` | in `/sources` in **beiden** Rollen einsatzbereit; Zeile `AAPL`, NASDAQ, USD | `us-example` | Das installierte Wheel wird nicht über seinen Entry-Point bis in Registry und UI geladen (T-39) |
| **P2** | dasselbe Plugin, **ohne** gesetzte `US_MARKET_API_KEY` | `/sources` zeigt es als nicht einsatzbereit **mit lesbarem Grund**; die übrige Kette arbeitet weiter | — | Eine Quelle steht still und sagt nicht warum; oder sie reißt die ganze Kette mit (T-23/T-39) |

### Die Rollen, einmal jede

| # | Eingabe | Sichtbar erwartet | Quelle | Unterscheidet den Fehler |
|---|---|---|---|---|
| **R1** | Profil Y: World-ETF aufnehmen und Drilldown öffnen; Bond-Chart öffnen; CAD→EUR rechnen | Auflösung/Kurs/Metadaten am ETF, Tagesreihe am Bond und FX kommen über die zugehörigen REST-Requests **alle fünf** aus derselben Datei | `yaml-file` | Eine Rolle steht in `/sources` als konfiguriert, wird aber über keinen echten Eintritt je gefragt (T-37 `#2`) |

### Was bewusst **kein** Browserfall ist

- **Leere Tagesreihe gegen Ausfall** (T-41 `#2`). Der Unterschied entscheidet,
  ob ein Wasserzeichen vorrückt — im Browser sehen beide Fälle gleich aus. Er
  ist am Composite direkt geprüft, und ein Browserfall würde ihn behaupten
  statt zeigen.
- **Contract-Kit, Mutanten, Invarianten.** Das sind Aussagen über den Vertrag,
  nicht über die Oberfläche; sie stehen in den Suiten und laufen in `make
  test` mit.
- **Jede frühere Verify-Zeile einzeln.** T-35 allein hat 28. Die zwölf oben
  decken die Risikogrenzen; die übrigen prüfen dieselbe Grenze ein zweites Mal.
- **Der Drilldown-Text in allen fünf Nicht-ETF-Gattungen.** Y3 zeigt einen
  Fall; die übrigen vier sind im Dashboard-Test parametrisiert.

### Was der Lauf mitschreibt

Je Fall: die tatsächlich angezeigten Werte, die Herkunftsangabe, und bei den
Kaskadenfällen der **Gegenwert** aus der jeweils anderen Quelle — ohne ihn
belegt „online gewinnt" nichts. Dazu Konsole und fehlgeschlagene Requests über
den ganzen Lauf, gemessen und nicht behauptet: Ein grüner Screenshot ohne
Datenherkunft ist kein Beleg.

**Vorbereitung, die zum Lauf gehört:** O2 braucht ein Papier, das in beiden
Quellen mit **unterschiedlichem** Wert steht — `IE00B4L5Y983` führt die
Beispieldatei mit 128,21, online steht ein anderer Kurs. Für O4 liegt im
temporären Datenverzeichnis eine einzelne `data/plugins/fx_miss.py`: eine
`FxSource`, die CAD→EUR übernimmt und `NotFound` liefert. Die Kette lautet
`fx: [fx-miss, yaml-file]`; die Datei wird weder committet noch zur neuen
Testinfrastruktur. So entsteht der entscheidende Unterschied deterministisch,
ohne Yahoo-Verfügbarkeit zu raten. Beides sind Laufkonfiguration und
Testdaten, keine Produktänderungen.

### Codex-Freigabe Phase A · Runde 1

Die zwölf Fälle decken die drei Identitätsformen, `fund`, Online-vor-YAML,
YAML-Lücke, Quote-/Daily-/FX-Herkunft, Metadaten, Neustart, Fehlermeldung und
beide externen Ladewege ab. Die ausgelassenen Contract-/Mutantenfälle bleiben
zu Recht unterhalb des Browsers; dort wäre ihre Unterscheidung nicht sichtbar.

Vor dem Lauf wurden nur drei Angaben mechanisch präzisiert: der vollständige
Paketname des Beispiel-Wheels, konkrete Eingaben für die Fünf-Rollen-Inventur
und ein temporäres `fx-miss`-Dateiplugin als deterministischer erster
FX-Non-Hit. Damit hängt kein Orakel von einem zufällig bei Yahoo fehlenden Paar
ab. Phase B darf genau diese Matrix ausführen; neue Fälle oder dauerhafte
Browser-Infrastruktur entstehen daraus nicht.

---

## Phase B · Der Lauf, unterbrochen vom Breitenalarm (2026-08-31)

### Was gelaufen ist, bevor der Riegel griff

Profil Y, alle Werte im Browser abgelesen:

| Fall | Ergebnis | Beleg |
|---|---|---|
| **Y1** | `BTC-EUR` · `CRYPTO` · 94.500,00 EUR · ISIN-Spalte leer | die `pair`-Form trägt |
| **Y2** | `DE0001102531` · `BOND` · 99,42 EUR; 1M-Chart zeigt **drei** Punkte (99,18 / 99,31 / 99,42), Skala 99,16–99,44 | die gepflegte History ist die Kursquelle |
| **Y3** | `DE0009848119` · **`FUND`** · 142,50 EUR; Drilldown: „dieses Papier ist keiner" | Gattung **und** Hinweistext stimmen |
| **R1** | `IE00B4L5Y983` · `ETF` · 128,21 EUR · TER 0,20 % · Anbieter iShares · Domizil Ireland · „Quelle: yaml-file" | Auflösung, Kurs, Metadaten aus derselben Datei |

Damit sind vier der fünf Rollen über echte Eintrittspfade belegt (Auflösung,
Kurs, Tagesreihe, Metadaten). Offen: FX, Y4 (Neustart) und das gesamte
Online-Profil einschließlich P1/P2.

### Fünf Anzeigebefunde, von Mike im Lauf gesehen

Vier sind behoben (`288c527`), der fünfte steht offen:

| # | Befund | Ursache, gemessen | Stand |
|---|---|---|---|
| **A** | Zeile rechts abgeschnitten | `main.content` `max-width: 1200px` → Container 1123 px, Tabelle 1245 px; Aktionsspalte hinter `overflow-x`, 600 px Fenster ungenutzt | behoben, Überlauf **0** |
| **B** | ISIN-Platzhalter zu lang | „hat keine — Währungspaar" = 24 Zeichen dehnte die Spalte auf 214 px | behoben, 116 px; Grund im Hover-Titel |
| **C** | Symbol = ISIN bei `isin_only` | `instruments.symbol` ist Pflicht, dort steht die ISIN; die UI zeigte sie doppelt und behauptete ein Börsensymbol | behoben, Strich mit Hover-Grund (`symbolOf()`) |
| **D** | nur `ETF` sah aus wie ein Label | das CSS kannte zwei Gattungen, seit T-31/T-38 gibt es sechs | behoben; Auszeichnung steht jetzt **vor** den Sonderfällen |
| **E** | Caret gehört **vor** die Symbolspalte, nicht hinein | noch nicht untersucht | **offen — wartet auf den Checkpoint** |

Befund D ist die dritte Ausprägung desselben Musters an einem Tag: eine zweite
Stelle, die eine getroffene Entscheidung nicht nachgezogen hat — nach
`_FIGI_TYPES` und dem Migrationswächter in T-35.

### Scope-Entscheidung nach dem Breitenalarm

Codex entscheidet am Stand `288c527`: **`continue`**. Die vier bereits
umgesetzten Anzeigekorrekturen bleiben als kleine Mitzieher des einen
MVP-Browserlaufs zusammen. Ein Split würde keine unabhängig nutzbare Funktion
abtrennen, sondern nur denselben visuellen Abnahmelauf auf mehrere Tickets
verteilen.

Für diesen von Mike begleiteten Browserlauf ersetzt die Art der Änderung die
starre Dateizahl: Kleine sichtbare UI-Befunde, die Mike während des Laufs
direkt zur Behebung freigibt, darf Claude sofort korrigieren und passend
testen. Das umfasst Befund E und gleichartige Kleinigkeiten aus den noch
offenen Fällen. Die Produktkommentare werden dabei auf die dauerhafte
Invariante gekürzt; Messwerte, Ticketnummern und Entstehungshistorie bleiben
hier im Ticket.

Der gelockerte Riegel gilt nicht für Vertrag, Schema, Abhängigkeiten, neue
Architektur oder eine eigenständige größere Funktion. Dafür bleibt ein neuer
Scope-Checkpoint Pflicht. Der tatsächliche Datei- und Zeilenumfang wird bei
der normalen Übergabe vollständig ausgewiesen.

---

## Phase B · Der vollständige Lauf (2026-08-31)

Drei Profile, alle Werte im Browser abgelesen oder über den öffentlichen
Eintritt gemessen. `data/stockinfo.db` blieb unberührt — weiterhin 19. August,
638.976 Bytes.

### Profil Y · die Identitätsformen

| Fall | Gemessen | Beleg |
|---|---|---|
| **Y1** | `BTC-EUR` · `CRYPTO` · 94.500,00 EUR · ISIN-Spalte leer mit Hover-Grund | die `pair`-Form trägt bis in die Anzeige |
| **Y2** | `DE0001102531` · `BOND` · 99,42 EUR; 1M-Chart mit **drei** Punkten (99,18 / 99,31 / 99,42), Skala 99,16–99,44 | die gepflegte History **ist** die Kursquelle |
| **Y3** | `DE0009848119` · **`FUND`** · 142,50 EUR; Drilldown: „dieses Papier ist keiner" | Gattung und Hinweistext stimmen beide |
| **Y4** | Neustart auf derselben Datenbank: alle vier Papiere unverändert, `GET /migration` → `pending: false`, `unchanged: 4`, `/sources` → 200 | **kein** Migrationszustand durch das Krypto-Papier |
| **R1** | ETF 128,21 EUR + TER 0,20 % + iShares + Ireland; Bond-Chart; `/fx` CAD→EUR = 0,641 mit `Quelle: yaml-file` | alle **fünf** Rollen aus einer Datei, über echte Eintrittspfade |

### Profil O · die Kaskade

Kette: `resolvers: [openfigi, yahoo-search, yaml-file]`,
`quotes: [yfinance, yaml-file]`, `fx: [fx-miss, yaml-file]`.

| Fall | Gemessen | Der Gegenwert, ohne den es nichts belegt |
|---|---|---|
| **O1** | `IE00B4L5Y983` · 127,49 EUR · **TER 0,20 %, Vola 10,63 %, Thes. Ja** | die Metadatenkette wurde gefragt — ohne Gattung wäre sie übersprungen worden |
| **O2** | derselbe ETF: **127,49** EUR | die Datei führt **128,21**; online hat gewonnen. Auch der Name ist der von OpenFIGI, nicht der der Datei |
| **O3** | `DE0001102531` · 99,42 EUR | online existiert kein Kurs; ohne `yaml-file` in `resolvers` scheiterte schon die Aufnahme |
| **O4** | `/fx` CAD→EUR = 0,641, Feld **Quelle: `yaml-file`** | `fx-miss` steht **vor** ihr in der Kette und liefert `NotFound` |
| **O5** | „Zu XX0000000000 hat keine der eingerichteten Quellen ein Wertpapier gefunden"; **null** Zeilen in `instruments` | die Meldung nennt die Kennung, die Datenbank bleibt sauber |

### Das fremde Plugin

| Fall | Gemessen |
|---|---|
| **P1** | `plugin_env_installed packages=1`, `plugins_loaded names=['us-example', 'yaml-file']`; in `/sources` in **beiden** Rollen einsatzbereit; `US0378331005` → `AAPL` / `XNAS` / 231,40 USD / „Apple Inc." |
| **P2** | ohne gesetzte Umgebungsvariable: `configured: false` mit dem Satz „api_key is missing — set providers.us-example.api_key in sources.yaml, e.g. to …"; die übrige Kette arbeitet weiter (SAP → `SAP.DE` / 189,22 EUR) |

---

## Sechs Anzeigebefunde, von Mike im Lauf gesehen

Alle behoben und gemessen — `288c527`, `13d4652`, `35ddf27`.

| # | Befund | Ursache | Nachher |
|---|---|---|---|
| **A** | Zeile rechts abgeschnitten | `main.content` `max-width: 1200px` → Container 1123 px, Tabelle 1245 px | Überlauf **0** |
| **B** | ISIN-Platzhalter zu lang | 24 Zeichen Erklärtext dehnten die Spalte auf 214 px | 116 px, Grund im Hover-Titel |
| **C** | Symbol = ISIN bei `isin_only` | `instruments.symbol` ist Pflichtspalte und trägt dort die ISIN | Strich mit Hover-Grund; `symbolOf()` als Gegenstück zu `isinOf()` |
| **D** | nur `ETF` sah aus wie ein Label | das CSS kannte zwei Gattungen, seit T-31/T-38 gibt es sechs | Auszeichnung **vor** den Sonderfällen; die siebte Gattung sieht neutral aus, nicht unfertig |
| **E** | Caret gehört vor die Symbolspalte | es stand in der Zelle unter der Überschrift „Symbol" | eigene Spalte, eigenes `aria-label` |
| **F** | Caret schrumpfte bei schmalem Fenster | `width` ist in einer Tabelle ein Wunsch: 15×15 → **5×15**, also verzerrt | `min-width`; nachgemessen 15×15 bei 900, 1000, 1150 px |

Befund D ist die dritte Ausprägung desselben Musters an einem Tag — nach
`_FIGI_TYPES` und dem Migrationswächter in T-35: eine zweite Stelle, die eine
getroffene Entscheidung nicht nachgezogen hat.

**Auf Nachfrage geprüft statt zugesichert:** Ein Inventar über alle Vue-Dateien
findet **null** feste Texte zwischen Tags; alle 44 Attributtexte laufen über
`t(…)` oder eine Variable, die ihrerseits aus dem Katalog kommt. Die Suche ist
gegengeprüft — sie findet ein eingeschmuggeltes „Hinzufügen".

---

## Zwei Befunde am Fehlerweg — gemessen, nicht behoben

Aufgefallen, weil Mike fragte, warum ein Kurs nicht geladen werden konnte:

```
GET /fx?base=CAD&quote=USD  →  HTTP 502
{"detail":"Kein Wechselkurs für CAD/USD"}
```

1. **Der Statuscode ist falsch.** `502` heißt „die Gegenstelle ist
   ausgefallen". Hier wurde die Quelle gefragt und hat geantwortet, dass sie
   dieses Paar nicht führt — das ist ein `404`. Genau diese Unterscheidung
   führt T-31 im Plugin-Vertrag als `NotFound` gegen `Unavailable`;
   `app/routers/fx.py:31` wirft beides zusammen. Ein Betreiber sucht daraufhin
   den Fehler bei seiner Quelle statt in seiner Datei.
2. **Deutscher Fließtext statt einer Kennung.** Dieselbe Sorte, die T-35
   Befund 4 abgeschafft hat. Das Dashboard kann deshalb nur seine eigene
   Kategorie zeigen („Wechselkurs konnte nicht geladen werden") und nicht den
   Grund — es wirft nichts weg, es bekommt nichts.

**Nicht angefasst:** Ein Statuscode ist REST-Vertrag und damit
checkpoint-pflichtig. Derselbe Befund steht seit T-35 für `normalize_isin`
offen; beide gehören in ein gemeinsames kleines Ticket.

---

## Regression nach dem finalen Stand

```
ruff check app tests plugin_api/{src,tests,examples}   → All checks passed
pytest -q tests -m "not integration"                    → 939 passed, 29 skipped
pytest -q plugin_api/tests                              → 295 passed, 1 skipped
make test-example                                       → 45 passed
vitest run (dashboard)                                  → 274 passed
./_tickets/T-35-smoke.sh --run                          → 20/20
PROFILE=yaml ./_tickets/T-35-smoke.sh --run             → 20/20
git diff --check                                        → sauber
```

### Codex-Review Phase B · Runde 3

Der Browserlauf selbst ist belastbar: Die Gegenwerte unterscheiden
Online-vor-YAML, YAML-Lücke und FX-Fallback; Neustart und fremdes Wheel laufen
über ihre echten Eintrittspfade. Codex hat unabhängig Build und Ruff, 39
direkt betroffene Dashboard-Tests, das vollständige `make test` (947 + 295 +
45 + 274) sowie beide T-35-Smokes mit je 20/20 bestätigt.

Vor der Freigabe bleiben drei kleine Nacharbeiten:

1. Die mobile `InstrumentCard` zeigt bei `isin_only` weiterhin die ISIN als
   Symbol, obwohl die Desktop-Tabelle dafür bereits `symbolOf()` benutzt.
   Außerdem sind die neuen Gründe nur per `title`-Hover erreichbar; Touch und
   Tastatur brauchen denselben vorhandenen Hinweisweg.
2. Die neue Typdarstellung samt `bond`-/`etc`-/`fund`-Zuordnung steht doppelt
   in Karte und Tabelle. Sie wird auf eine Wissensquelle reduziert und in
   beiden Darstellungen gegen denselben neuen Typ geprüft.
3. O1 bekommt den tatsächlich sichtbaren Quelltext als Beleg; die neuen
   Testkommentare verlieren Prozesschronik. Nach der Korrektur laufen das
   echte `make test`, der Build und beide Smokes nochmals.

Der separat gefundene REST-Fehlerweg wird nur als T-44-Follow-up erfasst. Er
ist kein Anlass, T-42 um einen Vertragsumbau zu erweitern. T-43 ist ebenfalls
ein eigenes späteres Ticket und wurde in dieser Runde nicht freigegeben.

---

## Runde 3 · die drei Nacharbeiten

**1 · Dieselbe Regel endete am Desktop.** `InstrumentCard.vue` zeigte
weiterhin `item.symbol` und damit die ISIN als Börsensymbol — `symbolOf()`
war nur in der Tabelle angewendet. Das ist dieselbe vergessene zweite Stelle,
die dieser Lauf an drei anderen Orten aufgedeckt hat, diesmal von mir selbst
erzeugt. Behoben; Gegenprobe je für Karte und Tabelle.

Dazu die Auskunft: Der Grund für einen Strich lebte nur im `title`-Hover —
auf einem Touchgerät nicht erreichbar, für die Tastatur nicht fokussierbar.
Er steht jetzt im vorhandenen `InfoHint` daneben, in beiden Ansichten und für
beide Fälle (fehlendes Symbol, fehlende ISIN).

**2 · Die Typregel stand zweimal.** Die neutrale Grunddarstellung und die
Zuordnungen für `bond`, `etc` und `fund` waren in Karte und Tabelle fast
identisch dupliziert — die zweite Wissensquelle, die der Browserbefund selbst
gewesen war. Sie liegt jetzt als `@mixin instrument-type-badge` in
`styles/_variables.scss`; beide Ansichten binden ihn ein. Je ein Test prüft,
dass eine Gattung **ohne** eigene Farbe die Pille trotzdem bekommt.

**3 · O1 nachgesehen statt behauptet.** Der Drilldown zeigt tatsächlich:

```
TER 0,20 % | Vola 1J 10,63 % | Thes. Ja | Anbieter iShares |
Replikationsart Physical(Optimized sampling) | Fondsvolumen 127.875,00 |
Fondsdomizil Ireland | Fondswährung USD | Quelle: justetf |
Stand der Quelle: 31.08.2026, 10:59
```

Die Erwartung im Konzept stimmte — `Quelle: justetf`, nicht die kombinierte
Form. Sie war nur nicht belegt. Die Testkommentare sind auf die Invariante
gekürzt; „bis T-42" und die Messwerte stehen hier.

### Regression, als Ganzes gelaufen

```
make test        → 947 Backend + 295 Plugin-API + 45 Beispiel + 278 Dashboard
npm run build    → ✓
ruff check       → All checks passed
./_tickets/T-35-smoke.sh --run                → 20/20
PROFILE=yaml ./_tickets/T-35-smoke.sh --run   → 20/20
git diff --check → sauber
data/stockinfo.db → unverändert, 19. August
```

Der FX-/`normalize_isin`-Fehlerweg ist als **T-44** angelegt und
ausdrücklich **nicht** in die `priority_chain` geschoben.

---

## Runde 5 · zwei Nachträge aus dem begleiteten Lauf

Beide auf Mikes direkte Ansage während des Laufs, also unter der für T-42
gelockerten Regel für sichtbare UI-Befunde.

**Der Strich trägt seinen Grund selbst.** Das Fragezeichen aus Runde 3 war an
einer einzelnen Zelle inkonsistent: Die Tabelle ist voller Striche — TER,
Vola, Thesaurierung —, und keiner davon trägt eins. `EmptyReason` macht
stattdessen den Strich selbst zum Auslöser, sichtbar nur durch den gepunkteten
Unterstrich wie bei einer Abkürzung. Damit gilt eine Regel statt einer
Ausnahme, und die Auskunft bleibt trotzdem erreichbar: Der Auslöser ist ein
`button` und greift bei Maus, Tastaturfokus und Berührung. `UxInfoHint` kam
dafür nicht in Frage — sein Auslöser ist fest das Frage-/Info-Zeichen.

**Der Klick endet am Strich.** Ein Klick darauf öffnete den Chart der Zeile.
`@click.stop` stand am Aufrufort und lief ins Leere: Wurzelelement von
`EmptyReason` ist das Tooltip, und dort landen durchgereichte Attribute — nicht
am Knopf. Der Klick endet jetzt im Knopf selbst, unabhängig davon, wie ein
Aufrufer die Komponente einbettet.

**Zur Messung, weil sie zweimal falsch war:** Die Koordinaten aus
`getBoundingClientRect()` und die des Klick-Werkzeugs weichen in dieser
Umgebung um rund 40 px ab. Meine ersten beiden Gegenproben landeten dadurch in
der Zeile darunter und öffneten deren Chart — ich habe zweimal „behoben"
gemeldet, ohne die Stelle getroffen zu haben. Erst der aus dem Bildschirmfoto
abgelesene Klick trifft; er löst **null** Requests aus und öffnet keinen Chart.

**Offen, bei Mike:** Der Strich ist 8 × 20 px. Wer die Zelle statt des
Zeichens trifft, klickt die Zeile — das ist kein Defekt, aber ein zu kleines
Ziel (Richtwert Maus ~24 px, Touch 44). Ob der Klickbereich per Polsterung
wachsen soll, ohne dass das Zeichen größer wird, entscheidet Mike.

---

## Runde 6 · der Strich, in drei Anläufen

Mike hat den Fall dreimal zurückgegeben, und jedes Mal zu Recht. Die Kette
steht hier vollständig, weil sie zeigt, wie eine falsche erste Frage drei
Runden kostet.

| Anlauf | Was ich tat | Was Mike sah |
|---|---|---|
| 1 | Klick unterbunden (`@click.stop` an der Komponente) | „Klicke ich auf den Bindestrich, bekomme ich ‚Historie kann nicht geladen werden'" |
| 2 | Klick durchgelassen | „Neben dem Strich funktioniert es, auf dem Strich nicht" — der `.stop` lag am Aufrufort und lief ins Leere, weil das Wurzelelement das Tooltip ist |
| 3 | Klick öffnet den Kursverlauf wie die Zeile | „Klicke ich auf EUNL.DE, klappt die Detailansicht auf, klicke ich auf den Bindestrich, öffnet sich die Kursansicht" |
| 4 | Der Strich sitzt **im** Umschalter, der Hinweis nur um den Text | stimmt |

**Die Ursache, gemessen statt vermutet:** Naive UI hängt am Auslöser eines
Tooltips eigene Handler auf und verschluckt einen Klick, der von dort kommt.
Solange der Knopf im Tooltip lag, kam sein Handler nie an — nachweisbar an
`aria-expanded`, das nach dem Klick unverändert `false` blieb. Jetzt liegt der
Hinweis im Knopf statt umgekehrt: Die Aktion gehört dem Knopf, die Erklärung
dem Text.

**Und die ursprüngliche Fehlermeldung war keine.** „Historie kann nicht
geladen werden" erschien, weil ich zwischen zwei Messungen den Server
gestoppt hatte, während Mikes Browser offen war — die Statuszeile zeigte
folgerichtig „Offline". Mike hat es erkannt, nicht ich. Beide Endpunkte
antworten in beiden Profilen mit `200` und Daten.

**Ein echter Befund kam beim Nachgehen heraus** und steht jetzt als dritter in
T-44: `GET /quote/by-symbol/BTC-EUR/daily` antwortet mit `502` für ein Papier,
das schlicht keine Tagesreihe hat.

**Zur Datenbank:** `data/stockinfo.db` trug zwischenzeitlich einen frischen
Zeitstempel. Nachgewiesen: Weder `pytest` noch die beiden Smokes fassen sie an
(mtime vor und nach jedem Lauf identisch). Inhalt unverändert — sechs
Instrumente, jüngstes vom 19. August, gleiche Größe.

---

## Nicht-Ziele

- Keine neue Asset-Klasse `cash`, keine Immobilien.
- Keine neuen Provider oder Plugin-Rollen.
- Keine Universalisierung des Agenten-Regelwerks; das bleibt T-40.
- Kein Anspruch, jede Kombination abzudecken. Die Matrix beantwortet, ob die
  gebaute Plugin-Kette im MVP aus Benutzersicht stimmt.

## Auflösung

_(offen — zuerst Claudes Konzept, dann Codex-Freigabe, dann Browserlauf und
Mikes unveränderte Human-Spalte)_
