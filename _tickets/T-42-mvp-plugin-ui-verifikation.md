# T-42 · MVP plugin UI verification

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (laufender Stack) | offen | Konzept 2 h, Lauf 3 h | risikobasierte Browser-Abnahme der fertigen Plugin-Kette; danach dieselbe kurze Matrix für Mike | — |

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
| **1** | Konzept-Handoff an Codex | höchstens 12 Fälle; jeder unterscheidet einen benannten Plugin-Fehler und nennt Profil, Eingabe, Ergebnis und Quelle | ➖ | |
| **2** | YAML-Profil im Browser | BTC, Anleihe/History und Fonds lassen sich aufnehmen und bleiben nach Neustart mit korrekter Gattung und Herkunft sichtbar | ➖ | |
| **3** | Online-Profil im Browser | Online gewinnt bei Überlappung; YAML schließt eine echte Lücke; Aktie/ETF, BTC, Bond und `fund` sind vertreten | ➖ | |
| **4** | Rollen im UI/Netzwerk | Resolver, Quote, Daily, Metadaten und FX werden mindestens einmal über einen echten Eintrittspfad unterschieden | ➖ | |
| **5** | Diagnose und Fehler | `/sources`, sichtbare Fehlermeldungen, Konsole und fehlgeschlagene Requests widersprechen dem angezeigten Zustand nicht | ➖ | |
| **6** | Regression | betroffene Tests, beide Profil-Smokes, Ruff, Build und vollständiges `make test` sind nach dem finalen Browserstand grün | ➖ | |
| **7** | Mike-Handoff | dieselben kurzen Schritte sind ohne Entwicklungswissen nachvollziehbar; Human-Spalte ist leer und bereit zur Abnahme | ➖ | |

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
