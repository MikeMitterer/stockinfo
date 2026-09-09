# T-21 · Identität auf MIC + Ticker umstellen

## Restumsetzung Börsenabweichung · Auftrag Mike, 2026-09-09

Codex implementiert, Claude prüft unabhängig über [STATUS.md](STATUS.md).
Mike: „OK, dann erledige das. Den Docker-Langzeittest können wir nicht
machen, das wird sich zeigen.“ Die historischen Docker-Zeilen bleiben
Prüfhistorie; daraus folgt kein offener Abschlussriegel mehr.

**Nachsteuerung Mike:** „Die Plugins geben die MICs zurück die unterstützt
werden. Aus - den US-Sammelcode sollte es überhautp nicht mehr geben“.
Damit sind die alten Anforderungen #2e2/#2e3 zum Sammelcode abgelöst.
Codex hatte sie zunächst in neue UI-Tests übernommen; noch kein Produktcode
entstanden. Dieser verworfene Testentwurf ist kein Produktnachweis.

### Verbindlicher Scope nach Claudes Split

Claude hat 8af898c am 2026-09-09 als Scope-Checkpoint geprüft: **split**,
keine Produktfreigabe, review_round bleibt 0. Katalogbereinigung und Anzeige
sind unabhängig prüfbare Ergebnisse. Die einmalige Budgeterweiterung bleibt
unverbraucht. Befund: app/plugin_adapters.py muss den entfallenden
COLLECTOR_CODES-Import und das Argument an identity_problem mitziehen.

**T-21 liefert einen Katalog und Auswahlwege ausschließlich für konkrete MICs.**
CollectorDef, COLLECTORS, COLLECTOR_CODES und die REST-/TS-Collector-Variante
entfallen; die bestehende Plugin-MIC-Formprüfung bleibt die gemeinsame Regel.
Resolver verwenden einen einzelnen bevorzugten MIC. Die FIGI-Sonderregel US
und die Heimatzuordnung US → US entfallen, ohne eine beliebige US-Börse zu
wählen. Unbekannte Präferenzen bleiben als unbekannt ausgewiesen; bestehender
protokollierter Resolver-Default-Rückfall, keine neue Startvalidierung.

**Budget ab c03b54c:** 8 Produktdateien, 8 Test-/Dokudateien, 800 manuelle
Diff-Zeilen. Produktflächen: app/exchanges.py, app/models.py,
app/routers/dashboard.py, app/resolver.py, app/providers/openfigi_provider.py,
app/plugin_adapters.py und dashboard/src/types.ts. Bis zu drei reine
Kommentardateien sind im Split zusätzlich genannt (migration.py,
plugins/yfinance_quotes.py, plugins/openfigi_resolver.py). Kommentare nur bei
nötiger Berührung nachziehen, keine historische Generalbereinigung.

**Kein** Datenbank-/Migrationsumbau, neuer Endpunkt, neue Abhängigkeit,
Test-Subsystem oder Änderung der Plugin-Marktabdeckung. Collector aus dem
Dashboard-Katalogvertrag zu entfernen ist ausdrücklich beauftragt; der
geschlossene Kurs-Core und die Plugin-API bleiben unverändert. Der
MIC-Vergleich folgt direkt in [T-67](T-67-boersenabweichung-anzeigen.md),
einschließlich Mikes drei zusätzlichen UI-Handgriffe ohne weitere Tickets.

### Aktuelle Prüfmatrix des Restumfangs

Die folgenden Zeilen lösen für diese Prüfnummern die alten Snapshots im
Historienabschnitt ab. Human-Antworten bleiben unverändert.

| # | Nachweis | AI |
|---|---|:--:|
| 2e | An [T-67](T-67-boersenabweichung-anzeigen.md) übergeben, unmittelbar nach dieser Bereinigung | ➖ |
| 2e2 | Alte US-Sammelpräferenz entfällt; konkrete US-MICs bleiben einzeln nutzbar | ➖ |
| 2e3 | Kein Collector im REST-/UI-Katalog oder in Auswahl-/Heimatregeln | ➖ |
| 2b6c | Docker-Pending-Langzeitnachweis: von Mike aus dem Abschlussumfang genommen | ➖ |

Entscheidende Akzeptanzfälle am öffentlichen Eingang: GET /exchanges liefert
nur MIC-Einträge und weist US als unbekannt aus; echte Resolverauswahl
unterscheidet XNAS und ARCX. Ein US-Länderpräfix löst keine Sammelabfrage aus.
Plugin-Adapter nehmen weiter konkrete US-Identitäten an und weisen ungültige
Identitäten ab. Rote Tests vor Produktcode; schlanker negativer Mutant;
Backend-/Dashboard-Suiten und statische Checks vor unabhängiger Übergabe.
Kein Docker-Langzeittest. UI-Browsernachweise gehören zum anschließenden T-67.

## Beauftragte Ergänzung: Abdeckung bei der Aufnahme

Mikes ausdrücklicher Umsetzungsauftrag und die UI-Tests werden in
[T-65](T-65-asset-aufnahme-prueft-boersenabdeckung.md) umgesetzt. Claude hat
im Scope-Checkpoint `f3b383b` die getrennte Prüfung dieses Nutzerwegs
empfohlen (`split`). T-65 folgt aufgrund des bestehenden Auftrags unmittelbar
auf die Korrekturen dieses Nachtrags; keine neue Entscheidung erforderlich.

## Nachtrag Börsenabdeckung · 2026-09-08

Mike beauftragt die Deklaration ausdrücklich in T-21. Die Exchanges-Seite
soll die tatsächlich konfigurierten Quellen zeigen: Online-Abdeckung je
Rolle, YAML ausschließlich für im aktuellen Dateibestand vertretene
Instrumente mit passenden Daten. Ein YAML-Eintrag verspricht keine allgemeine
Marktabdeckung. Beide Profile werden geprüft; derzeit ist kein Handgriff
von Mike erforderlich.

**Scope-Vertrag:** Drei Änderungen: (1) eingebaute Online-Plugins deklarieren
bekannte MICs je Rolle; (2) der additive Plugin-Hook `get_mic_support(config)`
liefert aktuelle Bestandsabdeckung, YAML wertet seine Datei aus; (3) REST und
UI unterscheiden Online-Funktionen, Dateibestand und fehlende Abdeckung.
Der Host sammelt die Deklarationen auch bei getrennten Klassen einer Quelle
(yfinance-Kurse und Metadaten). Statische Deklarationen bleiben kompatibel.
Die bestehende Marktabdeckungszusage garantiert weiterhin keinen Einzeltreffer.

Erwartet höchstens **15 Produktdateien**, **6 Test-/Dokudateien** und
**800 manuelle Diff-Zeilen** ab `337450e`: fünf Online-Pluginmodule samt
MIC-Konstante, Registry/Katalog, Source-Vertrag und YAML-Beispiel,
ExchangeSupport/ExchangesPanel und DE/EN; Vertragstests, Backend-Profiltests,
Dashboardtests und Autorenanleitung/Ticket. Kein neuer Endpunkt, Schema,
Datenbankzugriff, Datenmigration, Online-Download oder Umbau des Symbolformats.
Keine Änderungen an Arbeitsbeständen. Unbekannte Drittanbieter-Zusagen bleiben
als unbekannt erkennbar; fehlende Angaben werden nicht als Abdeckung erfunden.

UI-Nachsteuerung Mike: keine Rollenlisten oder Abdeckungs-Badges je Quelle.
Die Tabelle zeigt MIC, nutzbaren App-Suffix als zweite Spalte, Handelsplatz
und kompakte Kursquellen. Ohne Alias zeigt sie den als Eingabe gültigen MIC-Suffix,
beispielsweise `.XNAS`. YAML erscheint als Datei; die Erklärung gilt zentral.
Ausführliche Rollen-/Abdeckungsangaben bleiben im REST-Vertrag erhalten.
Quellennamen verlinken zum Infobereich am Seitenende; beide Eingabebeispiele
sind fett hervorgehoben (weitere explizite UI-Aufträge von Mike).
Die bestehende Hash-Navigation erhält dafür einen `source`-Queryparameter
auf Exchanges; Direktlinks müssen auch bei verzögert eintreffenden Daten
funktionieren. Dafür wird `useHashTab.ts` samt bestehendem Test ergänzt
(insgesamt weiterhin höchstens 15 Produktdateien, jetzt 7 Test-/Dokudateien).
Weiterer UI-Auftrag: nicht abgedeckte Zeilen samt MIC/Suffix ausgrauen.
Eine kleine gemeinsame Auswahlfunktion unter `utils/` hält Zeilenfarbe und
Quellenanzeige konsistent; damit 16 statt 15 Produktdateien (+7 %, im Riegel).
Standardmäßig zeigt die Seite nur abgedeckte Börsen; der vollständige Katalog
ist optional über einen Schiebeschalter einblendbar. Dieser erscheint nur,
wenn mindestens eine Börse nicht abgedeckt ist. Der Sammelcode-Abschnitt
entfällt auf Mikes Wunsch aus der UI; die REST-Auskunft bleibt vollständig.

Prüffolge: gezielte rote Profil-/Dateibestandtests, Implementierung, isolierte
REST-Profile einschließlich Dateiänderung/-fehler und Entfernung von Quellen,
DE/EN-Komponententests, Gesamtsuiten/Lint/Build, Desktop-/Mobil-Smoke und Claude.

| # | Nachweis | AI |
|---|---|:--:|
| coverage-online | Aktive Online-Quellen deklarieren ihre Rollen; entfernte Quellen verschwinden. | ✅ |
| coverage-yaml | Reines YAML zeigt nur vorhandene MICs je Datenrolle, Aktualisierung und Fehler ohne alte Zusage. | ✅ |
| coverage-ui | Online/Fallback und reines YAML sind auf Desktop/Mobil in DE/EN unterscheidbar. | ✅ |

**Nachweise Codex:** 1142 Backendtests bestanden, 29 übersprungen,
8 Integrationstests abgewählt; 322 Plugin-API-Tests (1 übersprungen),
50 Beispieltests und 370 Dashboardtests in 51 Dateien bestanden.
Ruff, ESLint und TypeScript/Build grün. Zwei gezielte Profiltests waren vor
Implementierung rot. Eine Gegenprobe ohne YAML-Datenprüfung rötet beide
Profiltests; die Zulassung von Metadaten als Kursquelle rötet vier UI-Tests.
Mutanten zurückgenommen, betroffene Tests danach erneut grün.

```bash
make test-backend ARGS='-m not\ integration'
make test-plugin-api test-example
make test-dashboard
npm --prefix dashboard run build
```

Logs: `/tmp/t21-coverage-{backend,api,ui,build,targeted}.log`,
Gegenproben `/tmp/t21-coverage-mutant-{yaml,ui-final}.log`.
Alle Backend-Profiltests starten mit nachweislich fehlender Testdatenbank.
Keine Arbeitsdaten oder Zugangsdaten gelesen/geändert. Keine Online-Kurse
abgerufen: geprüft werden die Deklaration, Auswahl und lokale Dateidaten,
nicht die aktuelle Lieferfähigkeit jeder einzelnen Börse.

Browser: isolierter Server auf 8896, eigene temporäre Datenbank und Fachdatei.
Online/Fallback zeigt 38 deklarierte Börsen und kompakte Kursquellen;
YAML-only zunächst XNAS/XPAR, nach zusätzlichem Toronto-Kurs und „Neu laden“
auch XTSE. Vollständiger Katalog optional: 38 Zeilen, fehlende Abdeckung
in Textfarbe gedämpft (RGB 170/160/151), verfügbare Codes Akzent (229/94/31).
Desktop 1440/1787 und Mobil 390 ohne horizontalen Überlauf. DE/EN geprüft;
Suffix zweite Spalte, SAP.DE/SAP.XETR fett (700), Quellenlink setzt Fokus
auf den Infotitel. Direktlink `#/exchanges?source=yaml-file` funktioniert
auch nach normalem App-Start. Reiner YAML-Betrieb zeigt keine Online-Quelle.
Schiebeschalter bei 35 nicht abgedeckten Börsen sichtbar; Einschalten zeigt
38 Zeilen, davon 35 grau (MIC und Suffix), mobil ohne Überlauf. Im
Online-Profil mit 38 abgedeckten Börsen kein Schalter. Sammelcode-Abschnitt
entfernt. Eigene Testtabs geschlossen, Testserver beendet.
Python-AST- und TS-Compiler-Inventare: englische Bezeichner; deutsche Testnamen.

**Mikes Rückmeldung:** „UI - viel besser“. Das ist die Rückmeldung zur
überarbeiteten Oberfläche; kein Abschluss des gesamten Tickets T-21.
Claude hat Runde 2 (`2c1d01b`) geprüft: B1 (doppelte Hash-Auswertung) und
B2 (vorausgesetztes `_config` im Autorenvertrag) sowie mechanische Mitzieher.
Korrigiert in `f3b383b`: gemeinsamer Hash-Leser; eigener Konstruktor ohne
Basiskonfiguration erlaubt, Fixture-Anforderung dokumentiert; Imports/Quotes
konsistent, Hook hinter Klassenattributen. Neuer Konstruktor-Test zuerst rot
mit AttributeError, danach grün. 15 gezielte Backend/API-Tests, 21 Hash-/UI-Tests,
1142 Backend (29 skip, 8 deselected), 323 API (1 skip), 50 Beispiel und
370 Dashboardtests grün; Build und Ruff grün. Bezeichnerinventar geprüft.
Logs `/tmp/t21-r3-{backend,api,ui,build}.log`. Erneutes Review steht aus.
Die Aufnahme-Ergänzung ist nach Scope-Entscheid in T-65 getrennt; diese
Runde enthält ausschließlich Korrekturen zum bereits geprüften Nachtrag.

## Aktuelle Teilumsetzung #2g · 2026-09-08

Scope-Vertrag: Nur die übersetzten Fehlertexte werden korrigiert. Ohne
verwertbare Fehlerkennung bleibt die übersetzte Aktionsmeldung stehen;
`code`/`params` behalten ihre fachliche Übersetzung. Unbekannte Kennungen
erscheinen weiter im übersetzten Rückfallsatz. Freier Servertext, kaputtes
JSON und `statusText` sind keine UI-Meldungen.

Zwei fachliche Änderungen: Transport ohne statusText-Rückfall; Anzeige ohne
Rohtext-Rückfall. Erwartet **2 Produktdateien** (`api/client.ts`, `api/reason.ts`),
**4 Test-/Dokudateien** (Client-, Reason-, Aktions-Tests, dieses Ticket),
**300 manuelle Diff-Zeilen**. Kein Backend-/Schema-/API-Umbau, keine neuen
Abhängigkeiten, keine Börsenabweichungs-UI und kein Docker-Langzeittest.

Prüffolge: DE/EN-Aktionsfälle vom Transport bis zur Fehlermeldung rot zeigen,
beide Rückfälle entfernen, bekannte/unbekannte Kennung, kaputtes/leeres JSON,
fehlgeschlagenes Lesen und Netzwerkfehler gezielt prüfen; UI-Smoke und
Dashboard-Gesamtlauf/Lint/Build, dann unabhängiges Review.

**Stand: #2g umgesetzt und von Claude in Runde 1 technisch freigegeben (`1985037`).**
Das Ticket insgesamt bleibt offen. Die früheren #2g-Zeilen weiter unten
sind historische Nachweise; die folgende Zeile ist der aktuelle Prüfstatus.

| # | Nachweis | AI |
|---|---|:--:|
| 2g | Bekannte/unbekannte Kennungen, Rawtext, kaputtes/leeres JSON, JSON-Primitiv/Array, Legacy-detail, Lesefehler und Netzwerkfehler in DE/EN; kein Rohtext oder statusText im UI. | ✅ |

Bekannte `code`/`params`-Fachmeldungen bleiben erhalten. Ältere Antworten nur
mit freiem `detail`-Text zeigen jetzt die übersetzte Aktionsmeldung; dieser
bewusste Rückfall verhindert unübersetzte Server- und Proxy-Texte.

```bash
npm --prefix dashboard test -- --run tests/api/reason.spec.ts tests/api/client.spec.ts tests/composables/useInstrumentActions.spec.ts
make test-dashboard
npm --prefix dashboard run build
```

**48 gezielte Tests** bestanden, vorher 17 rot. **363 Dashboardtests in
51 Dateien** bestanden, einschließlich ESLint; TypeScript/Build grün.
Zwei zurückgenommene Mutanten: Rohtext-Rückfall wieder eingebaut → 12 rot;
statusText-Rückfall wieder eingebaut → 1 rot. Danach gezielte 48 erneut grün.
Logs: `/tmp/stockinfo-t21-fallback-final.log`,
`/tmp/stockinfo-t21-dashboard.log`, `/tmp/stockinfo-t21-build.log`,
`/tmp/stockinfo-t21-mutant-{body,status}.log`.
TS-Compiler-Inventar der fünf geänderten Code-/Testdateien: Bezeichner englisch.

Browser-Smoke auf `http://127.0.0.1:8896/#/assets`, isolierte Testdaten aus T-64:
Nur `/quote` wurde im Testtab über `fetch` mit HTTP 502 und dem defekten Körper
`{"detail":` ersetzt. DE: „Hinzufügen von „DEMO.XBUD“ fehlgeschlagen“;
EN: „Adding “DEMO.XBUD” failed“. Weder JSON noch „Bad Gateway“ erschienen.
Dies ist eine kontrollierte Browserantwort, kein echter Proxy-Ausfall.
Nach Wiederherstellen des echten Transports lieferte derselbe Server HTTP 400
mit `symbol_without_exchange_suffix`; dessen deutscher Erklärungssatz erschien
korrekt im Toast. Eigener Testtab geschlossen; Arbeitsdaten unverändert.
Keine Backend-, Online-, Docker- oder Migrationsprüfung für diese UI-Korrektur
behauptet. Geplant/tatsächlich: 2/2 Produktdateien, 4/4 Test-/Dokudateien,
300/132 manuelle Zeilen vor der Statusübergabe.

## Unabhängiges Review #2g · Claude, 2026-09-08

Runde 1 dieser Teilkorrektur, `1985037`, Basis `fa128b2`: **approved**.
Claude hat alle fünf Antwortformen über echtes `ApiError → reasonOf` mit dem
i18n-Bundle in DE/EN geprüft. Strukturierte Kennungen bleiben übersetzt;
Legacy-detail, Rohtext und leere Antworten liefern keinen unübersetzten Grund.
363 Dashboardtests, ESLint, TypeScript und Build selbst nachgemessen;
zusätzlich 57 gezielte API-/Aktionsfälle. Mutanten: statusText-Rückfall 1 rot;
beide Rohtext-Durchreichungen zusammen 14 rot (Codex’ engerer Mutant: 12).
Scope und englische Bezeichner bestätigt, Produktcode unverändert.

Browser nicht unabhängig wiederholt. Die geringere Detailtiefe bei alten
Freitext-Antworten ist ausdrücklich akzeptierte Folge von #2g; mehr
Backend-Fehlerkennungen wären eine separate Portfolio-Entscheidung.
Die aktive Kette endet damit bei `portfolio_review`, Owner Mike.
**T-21 als Ganzes bleibt offen**: Börsenabweichungsanzeige und Docker-Pending-
Langzeitnachweis fehlen weiterhin; daraus folgt keine neue Implementierung.
Der eigene temporäre Server auf 8896 wurde nach dem Review beendet.

## Historische Verifikation · Codex, 2026-09-07

**Ergebnis: Der freigegebene Identitätskern besteht die gezielten aktuellen
Regressionstests; das gesamte Ticket ist weiterhin nicht abschlussreif.**
Geprüft wurde der Arbeitsstand bei `de8501b`. Der Auftrag „T-21 - verifiziere
das Ticket“ hebt die bisherige Einfrierung nicht als Implementierungsauftrag
auf. Keine Produktänderung und keine neue Freigabe der damals ungeprüften 4A-Fassung.

### Befunde des damaligen Prüfstands

| Bezug | Ergebnis | Beleg |
|---|---|---|
| #2e, #2e2, #2e3 | Anzeige der Abweichung von der bevorzugten Börse fehlt weiterhin. Tatsächliche Börse/Währung allein erfüllen den erwarteten Vergleich nicht. | AST-Inventar der Backend-Antwortmodelle und Dashboard-Routen sowie TS-Compiler-Inventar der Dashboard-Skripte: kein Abweichungsmodell/-pfad und keine Vergleichslogik. `ExchangesResponse` liefert die Präferenz, `InstrumentSummary` die Identität; die geforderte Darstellung wird nicht aufgebaut. |
| #2g | Die Zusage „immer übersetzt, nie statusText oder rohes JSON“ wird nicht vollständig erfüllt. | `dashboard/src/api/client.ts`, `request`: bei scheiterndem Lesen des Fehlerkörpers Rückfall auf `response.statusText`. `dashboard/src/api/reason.ts`, `reasonOf`: bei nicht parsebarem Körper wird der Rohtext übernommen. Ein Körper wie `{"detail":` kann deshalb unverändert in `describeFailure` landen. Der vorhandene Test bestätigt sogar die Durchreichung von `Internal Server Error`. Codebefund, kein neuer Browser-Live-Test. |
| #2b6c | Docker-Langzeittest im Migrations-Pending-Zustand bleibt ohne frischen Nachweis. | In dieser Prüfung kein Image-/Containerlauf. T-63 enthält allgemeine Docker-Tests; deren Anlage erfüllt die spezielle Zeit- und Pending-Bedingung nicht. |

### Prüfauftrag für #2g · Entscheidung vom 2026-09-07

Mit der Zurückstellung von [T-34](postponed/T-34-zusage-gegen-laufzeit.md)
bleibt die gezielte Fehlertext-Prüfung beim offenen Fehlertext-Punkt #2g.
Bei dessen Korrektur sind bekannte und unbekannte Fehlerkennungen in DE/EN,
kaputtes JSON, leere Antworten, scheiterndes Lesen des Fehlerkörpers und
Netzwerkfehler zu prüfen. Rohes Server-JSON und `statusText` dürfen nicht als
UI-Fehlertext erscheinen; vorhandene strukturierte Fachmeldungen bleiben
erhalten. Ein allgemeines AST-Framework für sämtliche Backend-Kennungen ist
keine Voraussetzung dieser Korrektur. Diese Zuordnung ist kein Nachweis einer
bereits erfolgten Umsetzung oder Verifikation von #2g.

### Zugehörige Smoke-Skripte

Auf Mikes Rückfrage ebenfalls im Code geprüft, nicht ausgeführt:
`T-21-smoke.sh` prüft weiterhin jedes Asset auf Ticker/MIC und berücksichtigt
`pair`/`isin_only` nicht. `T-21c-smoke.sh` verlangt fest `core_version = 2.0.0`
(statt des heutigen 4.2.0). `T-21b-smoke.sh` prüft historische Online-
Aufnahmefälle, unter anderem Apple und die Ablehnung von `BRK-B`.
Die drei Skripte sind keine frisch bestätigten aktuellen Abschlussprüfungen.
Sie bleiben bis zum Ticketabschluss beim Ticket und werden dann gemeinsam
archiviert; die neu ausgeführten Regressionstests stehen oben.

### Was inzwischen überholt ist

Die globale alte Invariante „jedes Instrument hat Ticker und MIC“ gilt seit
T-31 nur für `listed`. `pair` und `isin_only` sind gültige eigene Formen.
`identity_status = resolved` ist kein aktuelles Speicherziel. Der Core steht
inzwischen auf 4.2.0; die damalige Forderung nach dem Sprung auf 2.0.0 ist ein
historischer Auslieferungsnachweis. T-23 ist längst abgeschlossen und wird
nicht wieder durch alte Blockertexte gesperrt. T-19 ist abgeschlossen: Eine
andere Börsenzuordnung erfolgt über Löschen und Neuanlegen.

### Frisch ausgeführte Prüfungen

**281 Backendtests und 48 Dashboardtests bestanden.** Backend: Identität,
Aufnahmewege, Mehrdeutigkeit, Börsenkatalog, Migrationsplanung/-anwendung,
Gate und Schichtengrenzen. Dashboard: Fehlerübersetzung/Transport,
Migrationsoberfläche, App-Gate, Börsenansicht, Instrumentaktionen und Proxy.

```bash
# #1–3b, #5: gezielte Identitäts-, Migrations- und Aufnahmeprüfungen
.venv/bin/pytest -q tests/test_identity_migration.py tests/test_identity_creation.py tests/test_identity_intake_paths.py tests/test_identity_new_forms.py tests/test_resolver_identity.py tests/test_symbol_ambiguity.py tests/test_exchange_catalog.py tests/test_exchanges.py tests/test_migration_apply.py tests/test_migration_endpoints.py tests/test_migration_guard.py tests/test_migration_plan.py tests/test_migration_reason_catalogue.py tests/test_boundaries.py
# #2b6i, #2b8/#2b9, #2g: vorhandene Dashboard-Regressionen
npm --prefix dashboard test -- tests/api/reason.spec.ts tests/api/client.spec.ts tests/components/MigrationGate.spec.ts tests/components/AppGate.spec.ts tests/components/ExchangesPanel.spec.ts tests/composables/useInstrumentActions.spec.ts tests/viteProxy.spec.ts
```

Die grünen Tests ersetzen die fehlenden Zusagen oben nicht. Kein vollständiger
`make test`-Lauf, kein neuer Online-/Browser-/Docker-Test, keine Migration einer
Kopie des aktuellen Produktionsbestands und keine neue vollständige
Bezeichnerprüfung. Die alte Human-Matrix und historische Freigaben bleiben
unverändert. Für den Abschluss müssen die offenen Anforderungen umgesetzt
oder von Mike ausdrücklich aus dem Umfang genommen werden.

---


| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | eingefroren nach Übergabe 3 | 1 Tag | Schema-Migration, Symbolerzeugung | — |

**Löst:** Der Identifikator eines Papiers ist heute das **Yahoo-Symbol**
(`EUNL.DE`) — in der Datenbank, in der API, im Dashboard. Damit ist yfinance
nicht ersetzbar, sondern nur ergänzbar. Jede zweite Kursquelle müsste Yahoos
Suffix-Schreibweise nachbilden.

**Der Brocken der Serie.** Alles andere ist klein dagegen.

> **Stand nach Codex-Runde 4.** Zwei frühere Fassungen sind überholt: `symbol`
> wird **nicht** `NULL`-fähig (es bleibt am REST-Rand zugesagt), verliert aber
> seinen **globalen Eindeutigkeits-Index** — der gehört auf `(ticker, mic)`.

**Hängt an: T-24** — erst muss feststehen, was die API zusagt und wie eindeutig
adressiert wird. **Blockiert:** T-23 (ein Plugin, das Yahoo-Symbole erwarten
muss, ist kein Plugin).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Portfolio-Rebaseline Mike, 2026-08-27.** T-21 wird nach der bereits
> freigegebenen Übergabe 3 eingefroren: Produktstand `2dd0dc3`, Freigabe
> `d3fecb8`, anschließender Statusstand `ce55202`. Die 4A-Änderungen
> `7a14d79`/`48fff52` sind **nicht** Teil dieses freigegebenen Sockels; Runde
> 52 wurde bewusst nicht mehr geprüft. 4A und 4B werden nach dem ersten
> funktionsfähigen Plugin-MVP wieder aufgenommen. Bis dahin blockieren sie
> T-22, T-27a, T-27b und T-23 nicht.

> **Drei Übergaben statt einer** *(Claude, 2026-08-22)* — ein Tag Arbeit ist für
> einen Diff-Review zu viel am Stück. Die Schnitte liegen dort, wo das Ticket
> selbst schon trennt:
>
> | | Umfang | Zeilen | Commit |
> |---|---|---|---|
> | **Teil 1** | Schema, Migration, Meldung offener Fälle, Index-Umzug | `#1`, `#2`, `#3b` | `be5f38d` ✔ abgenommen |
> | **Teil 2** | Erzeugung neuer Papiere, Yahoo-Normalisierung | `#5` | `6abce88` ✔ abgenommen |
> | **Teil 2b** | `ExchangeDef` aufräumen (`figi_id_type`, `figi_value` zum Provider) | — | `556c23d` ✔ abgenommen |
> | **Teil 3** | in **vier** Übergaben, siehe Entwurf: 1 Börsenkatalog · 2 Migration **samt ihrer Meldung** · 3 Aufnahmeweg samt `core_version 2.0.0` · 4 Börsenabweichung, Fehlerpfad, Inventur | `#2b`, `#2d`, `#2e`, `#3`, `#4` | offen |
> | ~~Handzuordnung~~ | ~~offene Zuordnungen von Hand setzbar, eigener Status~~ | ~~`#2c`~~ | **gestrichen**, siehe Kasten |
>
> **Teil 2b abgetrennt** *(Claude, 2026-08-23)* — das Aufräumen von
> `ExchangeDef` ist ein reiner Umbau ohne Verhaltensänderung und hat mit der
> Erzeugung nichts zu tun. In einer Übergabe mit ihr vermischt, stünde ein
> Diff zur Prüfung, in dem sich Verhalten und Verschiebung nicht trennen
> lassen — bei einem Ticket, das in Teil 1 neun Runden gebraucht hat, ist das
> der schlechtere Schnitt.
>
> `#6` (`make test`) läuft in jeder Übergabe mit.

> **Teil 3 ist aufgeteilt** *(Entscheidung Mike, 2026-08-24, nach Codex-Runde 9)*
>
> Der Entwurf war über das Ticket hinausgewachsen. Zwei Themen liegen jetzt als
> eigene Tickets im Board:
>
> * [`T-29`](rejected/T-29-alias-lebenszyklus-und-providerwechsel.md) —
>   **Provider-Alias: Eigentümer, Lebenszyklus, Wechsel.** Wer `symbol` besitzt,
>   was beim Providerwechsel damit geschieht, Backup-Pflicht und
>   Best-Effort-Restore. **Revidiert `T-25:94-110`.**
>   *Nachtrag 2026-09-07: verworfen. Der Alias ist seit T-23/T-31 kein
>   Abrufschlüssel mehr, die Bestandsschutzregel steht in T-30, den
>   JSON-Export/Import hat Mike gestrichen.*
> * [`T-30`](T-30-plugin-boersenauskunft.md) — **plugin-deklarierte
>   Börsenauskunft.** Neuer `plugin_api`-Typ samt Merge-, Vorrang-, Kollisions-,
>   Provenienz- und Invalidierungsregeln.
>
> **Teil 3 stärkt die Zusage zu `symbol` deshalb nicht.** Der Sprung auf
> `core_version 2.0.0` betrifft `ticker`, `mic`, `listing_id` und den strengeren
> Aufnahmeweg — nicht die Bedeutung von `symbol`. Die wird in T-29 geklärt.
> *Nachtrag 2026-09-07: Sie hat sich stattdessen erledigt. Seit `API_VERSION 2`
> trägt `QuoteRequest` nur die Identität, und `symbol` ist ein daraus
> abgeleiteter Anzeigewert. Was davon offenblieb, steht in T-30.*

> **Die Handzuordnung ist gestrichen — der Symbolweg verlangt die Kombination
> künftig im Vertrag** *(Claude, 2026-08-24; Entscheidungen Mike)*
>
> **Entwurf:** [`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md`](../docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md)
>
> **⚠️ Codex: die Messungen bitte eigenständig nachvollziehen**, nicht anhand
> dieser Zusammenfassung. Der ganze Zuschnitt hängt an ihnen.
>
> **Erster Anlauf, und warum er falsch war.** Zuerst stand hier, der
> automatische Weg hole die offenen Fälle von selbst ein — gemessen am
> ISIN-Weg, und dort stimmt es: `VTI` → `ARCX`, `AAPL` → `XNAS` über
> `YAHOO_EXCHANGE_MICS`. Diese Messung übersah aber einen **zweiten
> Aufnahmeweg**. Mikes Rückfrage, ob es hier überhaupt um die Migration gehe,
> hat ihn aufgedeckt:
>
> | Quelle | Wann | Heilt sich selbst? |
> |---|---|---|
> | Migration (`app/db.py:277`) | beim Start, offline, Altbestand | ja, sobald eine ISIN-Auflösung läuft |
> | Symbolweg (`app/services/quote_service.py:179`) | laufend, bei jedem suffixlosen Symbol | **nein** |
>
> Eine über `GET /quote?symbol=AAPL` angelegte Zeile bleibt bei jedem weiteren
> Abruf offen. Der Grund steht im Kommentar von `get_quote_for_known` selbst —
> *„der Scheduler löst nichts auf, er holt nur Kurse."* Die Auffrischung zieht
> die Zuordnung aus `split_symbol(symbol)`, und das liefert für `AAPL`
> dauerhaft `(None, None)`.
>
> **Die Lösung ist deshalb nicht Reparatur, sondern Verhinderung.** Der
> Symbolweg verlangt künftig die vollständige Kombination: bekanntes Suffix
> **oder** `mic` als Parameter. Ein suffixloses Symbol ohne `mic` wird mit 400
> abgelehnt, statt stillschweigend eine dauerhaft offene Zeile anzulegen. Damit
> entstehen die Fälle gar nicht erst, die `#2c` hätte aufräumen sollen.
>
> **Das ist eine bewusste Umkehr gegenüber Teil 2**, dessen Kommentar wörtlich
> dagegen argumentiert (*„nähme ihm eine Abfrage weg, die es heute gibt"*). Neu
> ist das Wissen, dass genau diese Abfrage die unzuordenbaren Zeilen erzeugt.
> Der Parameter ist zudem seit jeher als *„Vollständiges Yahoo-Symbol inkl.
> Suffix"* dokumentiert — suffixlose Symbole waren nie zugesagt.
>
> **`core_version` steigt auf `2.0.0`** (Entscheidung Mike): Eine Anfrage, die
> heute 200 liefert, liefert künftig 400.
>
> ~~**Der Migrationspfad wird nicht eng gesehen** (Entscheidung Mike): Was sich
> einfach migrieren lässt, wird migriert; der Rest bleibt offen und bekommt
> eine verständliche Meldung.~~ **Überholt nach Runde 16** — der Rest bleibt
> *nicht* offen, er kommt gar nicht erst in den Bestand. Es gilt der Kasten
> „Der Zwischenzustand — aufgehoben" weiter unten. `GOLD.SG` löst weiterhin ein
> Eintrag `XSTU`/`.SG` in `EXCHANGES`, und **der muss vor der Migration da
> sein** — sonst kostet die Ablehnung 257 Tageskurse.
>
> **Was damit ebenfalls entfällt:** die Entwurfsfrage aus Runde 3 nach einem
> eigenen Status für von Hand gesetzte Zuordnungen. Den braucht es nur, *weil*
> es manuelle Zuordnungen gibt. ~~`identity_status` bleibt zweiwertig.~~
> **`identity_status` entfällt ersatzlos** — die Spalte hätte nur noch einen
> Wert.
>
> **Was dazukommt:** Sichtbar zu machen sind ~~zwei Zustände — offene
> Zuordnungen *und*~~ **seit Runde 16 zwei verschiedene Dinge:** der
> **Migrationsbericht** über Zeilen, die *nicht* in den Bestand gekommen sind,
> und im laufenden Betrieb „von der Vorzugsbörse abgewichen" mit beiden MICs
> und Währungen (erwartet `XETR`/EUR, tatsächlich `ARCX`/USD). Heute ist
> Letzteres nur die Logzeile `resolve_foreign_exchange`; im Dashboard sieht
> niemand, dass ein Papier in USD hereinkommt, obwohl XETR eingestellt ist.
> Eine **offene Zuordnung als Instrumentzustand** gibt es nicht mehr.
> 3. Eine **falsche** automatische Zuordnung überschreiben. Der einzige Fall,
>    in dem wirklich ein Mensch entscheiden muss — und es ist Korrektur, nicht
>    Erstzuordnung. Taucht er auf, ist er ein eigenes Ticket.

> **Verify `#2` verlangt für `AAPL` mehr, als die Migration wissen kann**
> *(Claude, 2026-08-22)*
>
> Die Zeile erwartet `AAPL` → `AAPL`/**`XNAS`** direkt nach der Migration. Das
> Ticket sagt zwei Absätze weiter aber selbst: Für suffixlose Symbole liefert
> die Börsentabelle nur den Sammelcode `US`, und „welcher echte MIC gilt,
> **steht dort nicht** — das muss aus dem aufgelösten Listing kommen".
>
> Beides zusammen geht nicht. Die Migration läuft beim Start und offline; sie
> müsste OpenFIGI fragen, um `XNYS` von `XNAS` zu unterscheiden — ein Start,
> der Netz braucht und in ein Rate-Limit laufen kann, und das für jede
> bestehende Zeile.
>
> ~~**Umgesetzt ist deshalb:** Die Zeile bekommt
> `identity_status = legacy_unresolved` und erscheint in der Liste offener
> Zuordnungen; den echten MIC trägt der nächste erfolgreiche Auflösungslauf
> nach.~~
>
> **Seit Runde 16 gilt stattdessen:** Ein suffixloses Symbol wird weiterhin
> **nicht geraten** — aber die Zeile bleibt auch nicht offen liegen. Sie wird
> **abgelehnt** und erscheint im Migrationsbericht mit Grund und verlorenen
> Kurspunkten; der Weg zurück ist die Neuerfassung über den Aufnahmeweg. Der
> Kern des Kastens stimmt unverändert: Die Migration läuft offline und **kann**
> den echten MIC nicht wissen. Nur die Folge daraus ist eine andere.
>
> Verify `#2` prüft entsprechend `EUNL.DE` → `EUNL`/`XETR` und `XIC.TO` →
> `XIC`/`XTSE` **nach der Migration**, `AAPL` dagegen als **abgelehnten** Fall.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | bestehende Datenbank, Migration laufen lassen | zerlegbare Instrumente haben `ticker` und `mic`; **nicht** zerlegbare werden abgelehnt und gemeldet, nicht geraten | ➖ [^a] | |
| 1b | dieselbe Migration auf einer **Kopie des echten Bestands** | ~~keine Zeile und kein Kurspunkt geht verloren~~ **neu:** kein Kurspunkt einer *migrierten* Zeile geht verloren, auch beim zweiten Start nicht; abgelehnte Zeilen verschwinden **absichtlich** und stehen mit ihrer Kurspunktzahl im Bericht | ➖ [^g] | |
| 2 | Stichprobe nach der Migration | `EUNL.DE` → `EUNL`/`XETR`, `XIC.TO` → `XIC`/`XTSE`; `AAPL` wird **abgelehnt** statt geraten | ➖ [^b] | |
| 2b | Instrument mit Fremdsymbol (`BRK-B`) | erscheint im **Migrationsbericht** mit Grund und verlorenen Kurspunkten — nicht mehr als offene Zeile im Bestand | ✅ [^m] | |
| 2b4 | Bericht und Ablehnung | entstehen in **derselben Transaktion**; ein zweiter Start dupliziert sie nicht; der Eintrag bleibt abrufbar, **nachdem** die aktive Zeile weg ist | ✅ [^n] | |
| 2b5 | Auslieferung von Teil 2 | **zweiphasig:** Phase 1 erkennt die ausstehende Migration und rechnet vor, ohne etwas zu ändern; erst die Bestätigung löst sie aus. Gleichzeitigkeit im Commit genügt **nicht** — `init_db()` läuft im Lifespan, bevor das UI erreichbar ist | ✅ [^o] | |
| 2b6 | Phase 1, serverseitig verriegelt — **Routentabellen-Test** | jeder Pfad der Allowlist (statische UI, `/health`, Healthcheck-Endpunkt, `/ready`, Vorschau, Bestätigung, Bericht) antwortet; je ein normaler **Lese-** und **Schreibpfad** (`/quote`, `/refresh`, `PUT`, `DELETE`) wird mit stabiler Kennung abgewiesen; DB und Vorschau bleiben unverändert | ✅ [^p] | |
| 2b6b | `/ready` in Phase 1 | antwortet **`503`** mit `status: "migration_pending"`, unterscheidbar vom `503` bei unerreichbarer DB; `status` ist ein `Literal`, kein freier `str` | ✅ [^q] | |
| 2b6e | `GET /operational` (neu) | `200`/`migration_pending` in Phase 1, `200`/`starting` während der Betrieb anläuft, `200`/`serving` im Normalbetrieb, `503`/`degraded` bei unerreichbarer DB **und** bei gescheitertem Betriebsstart. Der Docker-`HEALTHCHECK` zieht hierher um | ✅ [^r] | |
| 2b6f | eine Routenquelle | Guard und Routentabellen-Test lesen **dieselbe** Allowlist-Konstante; ein Test vergleicht die `HEALTHCHECK`-URL im `Dockerfile` gegen genau diesen Pfad — sonst driften sie unbemerkt bis zum Deployment | ✅ [^s] | |
| 2b6h | statische Dateien im Pending-Zustand | der Test **baut das Dashboard** und fordert **`GET /`** (belegt die geladene HTML) sowie *jede* real ausgelieferte Datei **rekursiv** an — insbesondere `/stockinfo-icon.svg` aus `index.html:6` und die Dateien unter `/assets`. Keine handgepflegte Kopie; unbekannte Pfade und Fach-APIs bleiben gesperrt | ⚠️ [^t] | |
| 2b6j | `/` als URL-Alias | steht **ausdrücklich** in der Allowlist, als exakter Pfad und nie als Präfix, unter der Bedingung `index.html` im begrenzten `static_dir`. Fehlt `static_dir` ganz (lokal: Vorgabe `/app/web`), ist der statische Teil leer | ✅ [^u] | |
| 2b6i | Vite-Dev-Proxy | `/migration`, `/operational` und `/ready` stehen in `apiPrefixes` (`dashboard/api-prefixes.ts`); ein Test hält die Liste gegen **jeden Pfad, den die App wirklich anfordert** — der Fehler ist als `solved/T-04-vite-proxy-fehlende-praefixe.md` schon einmal passiert | ⚠️ [^v] | |
| 2b6g | Diagnose-Verbraucher | `README.md:31-32` und `:202-205`, `docker/Dockerfile:71-75`, `app/main.py:70-76` und `tests/test_api.py:204-240` sind auf die **drei** Fragen abgeglichen; die widerlegte Restart-/Traffic-Begründung steht nirgends mehr | ✅ [^w] | |
| 2b6c | Image-Test | Pending-Zustand überdauert `start-period` + 3 × `interval`; Healthcheck-Endpunkt bleibt `200`, `/ready` bleibt `503`, Vorschau und Bestätigung durchgehend erreichbar. **Keine** Restart-/Routing-Zusage — die gälte nur für eine konkrete Orchestrator-Konfiguration | ➖ [^x] | |
| 2b6d | Bestätigung | gegen parallele und doppelte Aufrufe verriegelt; Scheduler und normale Endpunkte werden **genau einmal** freigegeben | ✅ [^y] | |
| 2b7 | Vorschau, Bericht und Meldungen | **stabile Reason-Codes** statt freier Texte, DE/EN übersetzt — in Teil 2, nicht erst in Teil 4 | ✅ [^z] | |
| 2b8 | Pflicht-UI des Umzugs | die Oberfläche zeigt vor der Zustimmung **jedes** Papier, das den Bestand verlässt, mit Grund und Kurspunktzahl, dazu die Bilanz und den Backup-Hinweis; danach denselben Bericht. Die Weiche steht **über** dem Dashboard, damit im Pending-Zustand kein Dutzend `503` vorausläuft | ✅ [^ac] | |
| 2b9 | Betriebszustände im UI | die Oberfläche liest `/ready` und unterscheidet die vier Lagen; `degraded` mit erreichbarer Datenbank führt in den Wiederholungsweg, nicht in „Server prüfen" | ⚠️ [^ad] | |
| 2b2 | nach erfolgreichem Start | Invariante `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`; kein Instrument-/Quote-Endpunkt serialisiert eine halbe Identität | ✅ [^aa] | |
| 2b3 | Reihenfolge Katalog vor Migration | `GOLD.SG` migriert (257 Tageskurse bleiben), wird **nicht** abgelehnt — der Katalog mit `XSTU` steht vorher | ✅ [^ab] | |
| ~~2c~~ | ~~derselbe Fall, manuelle Zuordnung~~ | **gestrichen** — der Symbolweg verlangt die Kombination künftig im Vertrag, damit entstehen die Fälle nicht mehr. Siehe Kasten „Die Handzuordnung ist gestrichen" | ➖ | |
| 2d | Aufnahmefeld: nackter Ticker `AAPL` | 400, Text nennt beide Auswege mit Beispiel; `AAPL.XNAS` legt die Zeile `resolved` an | | |
| 2d2 | `EUNL.DE` und `EUNL.XETR`, dazu `GOLD.SG` und `GOLD.XSTU` | je Paar **dieselbe** Identität *und* **derselbe** Provider-Alias; geprüft wird auch, womit die Quelle aufgerufen wurde | | |
| 2e | Papier abseits der Vorzugsbörse (`VTI` bei `XETR`) | erscheint als „abgewichen" mit beiden MICs; tatsächliche Währung aus den Kursdaten, nicht aus der Tabelle | | |
| 2e2 | `AAPL`/`XNAS` bei `DEFAULT_EXCHANGE=US` | **keine** Abweichung — der Sammelcode umfasst die US-Plätze | | |
| 2e3 | `VOD`/`XLON` bei `DEFAULT_EXCHANGE=US` | Abweichung mit `kind: collector` und erwarteter Währung `USD`, **ohne** erwarteten MIC | | |
| 2f | Aufnahmeweg über den **echten** Weg Router → Intake-Service → Repository, für ISIN, `TICKER.DE`, `TICKER.XETR` und unbekannte Form | keine eigene Core-Komponente gemockt, nur die Außengrenzen; geprüft wird auch die **Methode** (`POST`) und dass im Router keine Fachregel sitzt | ✅ [^ae] | |
| 2h | Börsenauskunft (`catalog`) | serialisiert **keinen** Sammelcode in ein `mic`-Feld; `US` erscheint als eigener Eintragstyp und bleibt als `DEFAULT_EXCHANGE` samt Mitgliedern nutzbar; **kein** Börseneintrag trägt eine eigene Mitgliedschaftsliste | ✅ [^i] | |
| 2h2 | Katalog-Vertrag: Alias und Provenienz | `alias` ist in Python, OpenAPI und TypeScript **optional** — fehlend **oder** `null`, in allen drei Schichten. Der Leerstring ist verboten; das trägt das Backend (`min_length=1`, im OpenAPI-Schema sichtbar), nicht TypeScript. Die fünf US-Plätze liefern `null`. `provenance` ist eine **diskriminierte Union**: Core ohne Plugin-ID, Plugin mit verpflichtender nichtleerer ID; beide ungültigen Kombinationen werden abgelehnt | ✅ [^j] | |
| 2h3 | Auswahl der bevorzugten Börse bei aliaslosen Plätzen | `DEFAULT_EXCHANGE=XNAS` wählt den NASDAQ-Treffer, auch wenn ein Arca-Treffer vorn steht; beim Sammelcode `US` verdrängt ein punktloser Treffer mit unbekanntem Börsencode kein gültiges Mitglied. Der Fremdbörsen-Fallback bleibt | ✅ [^k] | |
| 2h4 | Börsenableitung eines Yahoo-Treffers | **eine** Ableitung für Auswahl **und** Identität (`_exchange_of`): Ein bekanntes Suffix entscheidet allein und wird nie von Yahoos `exchange` überstimmt; Yahoos Code gilt nur für suffixlose Symbole. Auswahl und gespeicherter MIC können demselben Treffer keine verschiedenen Börsen zuschreiben | ✅ [^l] | |
| 2i | `POST /instruments/intake` | Neuanlage `201` mit `InstrumentSummary`, bestehendes Papier `200` mit demselben Typ, unauflösbar `400`, Quelle tot `502` — je im OpenAPI-Snapshot zugesagt und über die echte Kette geprüft | ✅ [^af] [^aj] | |
| 2i2 | Identitätskonflikt am HTTP-Rand | `AAPL/XNAS` ohne ISIN neben `AAPL/XNYS` mit ihr ergibt einen typisierten `409` mit `code: identity_conflict` und beiden Seiten in `params` — **kein** `500`. Der Fall ist an **jedem** speichernden Vertragsendpunkt zugesagt, nicht nur am Aufnahmeweg | ✅ [^al] | |
| 2i3 | mehrdeutiges Symbol, lesend **und** verändernd | zwei Listings mit dem Alias `AAPL`: `GET /quote?symbol=AAPL` antwortet `409`/`symbol_ambiguous` mit beiden Kandidaten samt `listing_id` statt still der älteren Notierung; `DELETE /instruments/by-symbol/AAPL` löscht **nichts** statt beide Zeilen samt Historie; `PUT .../isin` schreibt nichts. Ein eindeutiges Symbol und der Aufnahmeweg bleiben unberührt | ✅ [^am] | |
| 2j | Schichtengrenze am Aufnahmeweg | der Intake-Service liefert `IntakeResult(summary, created)`; im Router steht **kein zweiter Existenz-Check** und keine Repository-Abfrage, er mappt nur `created` auf `201`/`200` | ✅ [^ag] | |
| 2j2 | `created` unter Parallelität | kommt aus der **schreibenden Transaktion**, nicht aus einem Preflight; im abgefangenen UNIQUE-Rennen ist `created=false`, nicht `201` | ✅ [^ah] [^aj] | |
| ~~2j3~~ | ~~`GET /instruments` mit einer `legacy_unresolved`-Zeile~~ | **entfällt** — mit der Entscheidung nach Runde 16 gibt es diesen Zustand nicht mehr. `ticker`, `mic` und `listing_id` sind Pflicht, siehe `#2b2` | ➖ | |
| 2k | Übergabe 2 als Einheit | `core_version 2.0.0`, Vertragsartefakt und Snapshot kommen **mit** der ersten Änderung am geschlossenen Core, nicht danach — zwischenzeitlich gibt es keinen öffentlich geänderten, aber unzugesagten Endpunkt | ✅ [^ai] [^ak] | |
| 2g | Fehlerpfad im Dashboard, **je in DE und EN** | bekannte Kennung, unbekannte Kennung, kaputtes JSON, leerer Rumpf, Netzwerkfehler — alle ergeben einen übersetzten Text, nie `statusText` und nie rohes JSON | | |
| 3 | `GET /instruments` | `symbol` weiterhin vorhanden und unverändert (Profil-Links hängen daran) | ✅ [^d] | |
| 3b | Datenbank-Schema | Eindeutigkeit liegt auf `(ticker, mic)`; `symbol` ist **nicht mehr** global unique | ✅ [^e] | |
| 4 | Dashboard, Assets-Tabelle | unverändert; Yahoo- und extraETF-Links funktionieren | | |
| 5 | neues Papier aufnehmen — **auf jedem Weg** | `ticker`/`mic` werden gefüllt, `symbol` daraus erzeugt | ✅ [^h] | |
| 6 | `make test` | Backend, Plugin-API und Dashboard grün | ✅ [^f] | |

> **⚠️ Zu allen Fußnoten unterhalb dieser Zeile** *(2026-08-24, nach Runde 16)*
>
> Sie beschreiben **Belege des alten Zielzustands** und stehen als Historie da,
> nicht als geltende Erwartung. Wo sie offene `NULL`-Zeilen,
> `identity_status = legacy_unresolved` oder „bleibt offen" als richtiges
> Ergebnis führen, ist genau das seit der Entscheidung **falsch**: Solche Zeilen
> kommen nicht mehr in den Bestand.
>
> Deshalb stehen die betroffenen Zeilen `#1`, `#1b`, `#2` und `#2b` in der
> AI-Spalte wieder auf `➖`. Sie werden erst hochgestuft, wenn neue Tests
> Ablehnung, Bericht und die `NULL`-Invariante belegen. Die **Human-Spalte
> bleibt unberührt** — sie gehört Mike.

[^a]: `tests/test_identity_migration.py`, **zwanzig** Tests gegen eine
    nachgestellte Alt-Datenbank mit vier bezeichnenden Fällen. Zerlegt werden `EUNL.DE` und
    `XIC.TO`; `AAPL` (suffixlos) und `BRK-B` (fremde Schreibweise) bleiben
    offen. Die Migration läuft zweimal — sie muss idempotent sein.
[^b]: `test_bekannte_suffixe_werden_zerlegt` und die beiden Gegenproben
    `test_suffixloses_symbol_wird_nicht_geraten` /
    `test_fremde_schreibweise_wird_nicht_geraten`. Dazu
    `tests/test_exchanges.py` mit der Rückrechnung selbst — einschließlich
    `test_kein_suffix_ist_doppelt_vergeben`: Käme eine Börse mit belegtem
    Suffix dazu, wäre `split_symbol` stillschweigend mehrdeutig, und dieser
    Test schlägt an, statt dass die Migration falsch zuordnet.
[^c]: **Nur als Protokollmeldung.** `test_die_offenen_faelle_werden_gemeldet`
    belegt, dass die Migration `identity_unresolved` mit Anzahl und Symbolen
    schreibt. Eine abfragbare *Liste* offener Zuordnungen ist Teil 3 — dort
    steht auch der Grund je Fall.
[^d]: Der Index auf `symbol` ist weg, die Spalte nicht: `symbol TEXT NOT NULL`
    steht unverändert im Schema, und die 370 Tests der Suite fahren die
    bestehenden Symbol-Endpunkte weiter durch.
[^e]: `test_die_eindeutigkeit_liegt_auf_ticker_und_mic` prüft beides:
    `idx_instruments_symbol` ist verschwunden, `idx_instruments_ticker_mic`
    ist eindeutig. Zwei weitere Tests halten die Folgen fest — mehrere offene
    Zeilen dürfen nebeneinander stehen (SQLite zählt `NULL` als eigenen Wert),
    ein echter Konflikt fällt weiterhin auf.
[^f]: `.venv/bin/pytest tests/ -q` → `392 passed, 29 skipped`;
    `make test-plugin-api` → 36; Ruff sauber.
[^i]: `tests/test_api_dashboard.py::test_kein_katalogeintrag_serialisiert_einen_sammelcode_als_mic`
    prüft die Antwort selbst: kein `mic`-Feld an einem Sammelcode, kein
    Börseneintrag mit `mic == "US"`.
    `test_der_sammelcode_bleibt_eine_zulaessige_vorgabe` hält fest, dass `US`
    als `DEFAULT_EXCHANGE` weiter gilt und als `collector` ausgewiesen wird.
    `tests/test_exchange_catalog.py::test_die_mitgliedschaft_steht_nur_am_sammelcode`
    deckt die Gegenrichtung ab.
[^j]: Nachtrag aus Runde 25 — die erste Umsetzung führte `alias` trotz des
    Entwurfs als Pflichtfeld mit `""` bei den US-Plätzen, und `Provenance`
    konnte `plugin` ohne ID wie `core` mit ID ausdrücken.
    `tests/test_exchange_catalog.py` prüft jetzt beide Richtungen: fehlender
    und `null`-Alias gültig, `""` abgelehnt, US-Eintrag serialisiert `null`;
    für die Provenienz die zwei gültigen und **vier** ungültigen
    Kombinationen. `test_der_alias_ist_im_openapi_vertrag_optional` misst den
    ausgelieferten Vertrag statt des Modells.
    `dashboard/tests/types/provenance.spec.ts` hält die TypeScript-Seite mit
    `@ts-expect-error` fest — `vue-tsc` prüft `tests/` mit, ein Aufweichen des
    Typs bricht `npm run build`. **Live gegengeprüft:** Die Zeile absichtlich
    gültig gemacht → `TS2578: Unused '@ts-expect-error' directive`, Build rot.

    **Korrektur aus Runde 26:** `alias: string | null` verlangte die Property
    weiterhin und war damit strenger als der ausgelieferte Vertrag, in dem
    `alias` nicht in `required` steht. Jetzt `alias?: string | null`, und der
    Test führt **beide** zulässigen Formen — `null` und weggelassen. Ebenfalls
    live gegengeprüft: Typ auf die alte Form zurückgesetzt →
    `TS2741: Property 'alias' is missing`, Build rot.

    Der verbotene Leerstring ist **keine** TypeScript-Zusage: Ein Stringtyp
    kann „mindestens ein Zeichen" nicht ausdrücken. Er liegt bei Pydantic und
    steht als `minLength: 1` im OpenAPI-Schema.
[^k]: `tests/test_resolver.py::test_yahoo_unterscheidet_eine_us_boerse_vom_sammelcode`
    und `…::test_yahoo_laesst_einen_unbekannten_punktlosen_treffer_nicht_gewinnen`.
    In beiden steht der **falsche** Treffer zuerst, sonst bewiese die Reihenfolge
    nichts. **Mutationsgeprüft:** die alte Regel („kein Alias → jedes punktlose
    Symbol zählt") wieder eingesetzt → beide Tests rot, der zweite mit genau dem
    `resolve_isin_ambiguous`/`Unavailable`-Pfad aus dem Befund.
    Der Fremdbörsen-Fallback bleibt von
    `test_yahoo_nimmt_den_ersten_treffer_wenn_die_boerse_fehlt` gedeckt.
[^l]: Nachtrag aus Runde 27. Die Auswahl prüfte Suffix **oder** Yahoo-Code,
    `_identity` dagegen Suffix und *nur bei dessen Fehlen* den Code. Für
    `WRONG.DE` mit dem Code `NMS` hieß das: Die Auswahl hielt ihn bei
    `DEFAULT_EXCHANGE=XNAS` für eine NASDAQ-Notierung, `_identity` gab ihm
    `XETR` — und der gültige NASDAQ-Treffer dahinter fiel raus.

    Jetzt hat die Rangfolge einen Ort: `_exchange_of(symbol, exchange_code)`.
    `_identity` baut darauf auf und fügt allein die Ticker-Prüfung hinzu; die
    Auswahl fragt dieselbe Funktion. Der Alias-Lookup selbst liegt in
    `app.exchanges.mic_for_alias`, den auch `split_symbol` benutzt — eine
    Umkehrung von `ExchangeDef.alias`, nicht zwei.

    `preferred_aliases` ist damit **entfallen**: Es existierte nur, um die
    Auswahl zu beantworten, und diese Frage hat jetzt eine andere, einzige
    Antwort. Eine zweite Aliasregel danebenstehen zu lassen wäre genau der
    Zustand, aus dem dieser Befund entstand.

    `test_yahoo_laesst_das_suffix_nicht_vom_boersencode_ueberstimmen` deckt die
    Konfliktreihenfolge ab; beide Treffer tragen denselben Yahoo-Code, allein
    das Suffix unterscheidet sie. **Mutationsgeprüft:** die alte
    Oder-Verknüpfung wieder eingesetzt → Test rot mit `'WRONG.DE' != 'RIGHT'`.

<!-- Übergabe 2A — Migration, Backend -->

[^m]: `tests/test_migration_apply.py::test_was_geht_hinterlaesst_seinen_bericht`
    und `…::test_der_bericht_nennt_genug_zur_neuerfassung`. Der Eintrag trägt
    Symbol, ISIN, Name, Börse, Gattung, Währung, Grund und **beide**
    Kurspunktzahlen getrennt — `quotes` und `daily_closes` sind verschiedene
    Dinge, und der gemessene Fall hängt an den Tagesschlüssen.
[^n]: `tests/test_migration_apply.py`, vier Tests: Der Bericht überlebt die
    gelöschte Zeile; ein Abbruch lässt **alles** stehen (Rollback-Test); ein
    zweiter Lauf dupliziert nichts; die Kurspunkte der Bleibenden überleben.
    Die Idempotenz ist **verhaltensmäßig** geprüft, nicht per `UNIQUE`: Eine
    Eindeutigkeitsbedingung hätte denselben Test bestanden, ohne dass der Lauf
    idempotent wäre.

    **Dabei gefunden:** `executescript` setzt vor dem Ausführen ein `COMMIT`
    ab — dokumentiertes `sqlite3`-Verhalten. Die Tabellenanlage hätte die
    offene Transaktion beendet und „alles oder nichts" zu einer Zusage ohne
    Deckung gemacht. Jetzt eine einzelne `execute`-Anweisung; der
    Rollback-Test belegt es.
[^o]: `tests/test_migration_plan.py::test_die_vorschau_schreibt_nicht` prüft an
    einer **schreibgeschützten** Verbindung, dass Phase 1 nichts ändert —
    mutationsgeprüft mit einer `ALTER TABLE`-Zeile, die den Test rot macht
    (`attempt to write a readonly database`). Ein Test, der nur die Zeilen
    hinterher vergleicht, hätte die Schemaänderung übersehen.

    `tests/test_migration_endpoints.py::test_der_start_erkennt_den_ausstehenden_umzug`
    fährt denselben Nachweis über den **echten Lifespan**.
[^p]: `tests/test_migration_endpoints.py`: Der Routentabellen-Test zählt **aus
    der Allowlist** auf (nicht aus einer Kopie) und fordert jeden Pfad
    wirklich an; sechs Lese- **und** Schreibwege werden mit der stabilen
    Kennung `migration_pending` abgewiesen, darunter `/quote`, `/refresh`,
    `DELETE /instruments/1` und ausdrücklich auch die **Lese**wege
    `/instruments` und `/exchanges`. `test_die_gesperrten_wege_lassen_die_datenbank_in_ruhe`
    vergleicht die Vorschau vor und nach den abgewiesenen Requests.
[^q]: `tests/test_migration_endpoints.py::test_ready_und_operational_beantworten_verschiedene_fragen`
    samt Gegenprobe im Normalbetrieb — ohne sie bewiese der Test nur, dass
    *irgendetwas* `503` sagt. `status` ist als `Literal` im Modell und damit
    im OpenAPI-Vertrag.
[^r]: Derselbe Test, plus `test_im_normalbetrieb_sagen_beide_ja`. Der
    `HEALTHCHECK` ist auf `/operational` umgezogen; die widerlegte
    Restart-/Traffic-Begründung im Dockerfile-Kommentar ist ersetzt.

    **Scope-Abweichung, bewusst:** Der Schnitt hatte den Dockerfile bei 2B.
    Er gehört zum Endpunkt — sonst liefert 2A einen Healthcheck-Endpunkt, den
    niemand benutzt, während `/ready` im Pending-Zustand `503` sagt und den
    Container als unhealthy markiert.

    **`starting` kam in Runde 33 dazu** (Codex-Befund aus Runde 32). Zwischen
    festgeschriebenem Umzug und zurückgekehrtem `RefreshScheduler.start()`
    meldeten beide Endpunkte Normalbetrieb; bei einem hängenden Start
    dauerhaft. `/operational` bleibt dabei bewusst auf `200` — ein `503`
    machte den `HEALTHCHECK` ausgerechnet auf dem **erfolgreichen** Weg kurz
    `unhealthy`. `/ready` sagt in derselben Lage `503`, denn dort ist die
    Frage die Freigabe des Fachbetriebs.
    `…::test_waehrend_der_start_laeuft_meldet_niemand_normalbetrieb` hält den
    Rückruf mitten im Scheduler-Start an und fragt **währenddessen**; ohne die
    Zwischenlage liest der Test `(200, "ok")` statt `(503, "starting")`
    (mutationsgeprüft).
[^s]: `tests/test_migration_endpoints.py::test_der_dockerfile_zeigt_auf_denselben_pfad`
    liest die `HEALTHCHECK`-Zeile und vergleicht sie gegen `HEALTHCHECK_PATH`.
    Der Dockerfile kann kein Python importieren, also kann er die Konstante
    nicht teilen — geprüft werden kann er.
[^t]: **Mit Einschränkung.** Der Test fordert `GET /` an (und belegt die
    geladene Dashboard-HTML) sowie **jede real ausgelieferte Datei rekursiv**,
    einschließlich `/stockinfo-icon.svg` und der Dateien unter `/assets`; dazu
    die Gegenprobe, dass ein unbekannter Pfad gesperrt bleibt.

    Was er **nicht** tut: das Dashboard selbst bauen. Er benutzt
    `dashboard/dist`, wenn es da ist, und überspringt sonst. Auf einem frisch
    ausgecheckten Baum ohne `make build` prüft er also nichts. Das steht hier,
    statt die Zeile grün zu machen.

    Beim ersten Anlauf kam `GET /` als **404** zurück, nicht als 503 — der
    Guard ließ es durch, es war nur nichts gemountet, weil `main.py` beim
    Import den Container-Pfad `/app/web` sieht. Ohne diesen Befund hätte der
    Test „gesperrt" mit „gar nicht da" verwechselt und wäre grün geblieben.
[^u]: `tests/test_migration_guard.py`, vier Tests: `/` nur bei vorhandener
    `index.html`, als exakter Pfad und **nie** als Präfix (`/quote/EUNL.DE`
    bleibt gesperrt); ohne Verzeichnis ist die Menge leer; ein Symlink aus dem
    Verzeichnis hinaus wird nicht freigegeben — mutationsgeprüft.
[^v]: **Mit Einschränkung.** `dashboard/tests/viteProxy.spec.ts` liest die
    Pfad-Literale aus dem Quelltext der App und hält **jeden** gegen die
    Präfixliste — eine abgeschriebene Erwartungsliste hätte nur belegt, dass
    zwei Listen gleich sind. Gemessen: Ohne `/migration` meldet er drei
    ungedeckte Pfade.

    **Was er nicht tut:** einen Dev-Server starten und je Präfix eine echte
    Antwort holen. Er prüft die Konfiguration, nicht den laufenden Proxy, und
    er findet nur Literale — zur Laufzeit gebaute Pfade (`instrumentPath`)
    stehen nicht darin. Genau die Literale sind aber die Klasse, die in T-04
    gefehlt hat.
[^w]: `docker/Dockerfile` und die Docstrings in `app/main.py` waren schon in
    2A abgeglichen; `README.md` und `tests/test_api.py:204-240` sind es
    seit 2B.

    **Ein Fehler von mir dabei:** In Runde 34 hatte ich `README.md:31-32` als
    „klar historische Passage" eingestuft und liegen gelassen. Die Version
    **ist** 0.6.0 — das ist der Changelog der laufenden Auslieferung, und der
    Satz „The Docker healthcheck now uses `/ready`" war darin seit 2A falsch.
    Jetzt stehen dort die drei Fragen und der zweiphasige Umzug.
[^x]: **Nicht in 2A.** Der Image-Test braucht ein gebautes Image und gehört
    zu 2B.
[^y]: Dass die Freigabe genau einmal gewinnt, ist mit acht Threads an einer
    Barriere geprüft
    (`tests/test_migration_guard.py::test_die_freigabe_gewinnt_genau_ein_aufrufer`),
    und ein zweiter `POST /migration/confirm` bekommt `409`
    (`…::test_eine_zweite_bestaetigung_laeuft_ins_leere`).

    **Der Scheduler war zuerst vergessen.** Er startet im Lifespan, und der
    ist längst durch, wenn der Benutzer bestätigt — nach einem bestätigten
    Umzug wäre der Hintergrund-Refresh bis zum nächsten Neustart ausgeblieben.
    Der Dienst hätte gesund ausgesehen, `/ready` hätte `ok` gesagt, und
    trotzdem wäre kein einziger neuer Kurs gekommen. Aufgefallen ist es beim
    Schreiben dieser Fußnote, nicht beim Bauen.

    Behoben über `MigrationGate.on_release`: Der Lifespan hinterlegt den
    Start, die Bestätigung ruft ihn. Ein Rückruf statt eines Imports, weil der
    Endpunkt sonst `app.main` importieren müsste, das ihn selbst einbindet.
    `…::test_die_bestaetigung_startet_den_scheduler` prüft beides — dass er
    anläuft und dass ein zweiter Aufruf ihn nicht noch einmal startet.

    **Der Wiederholungsweg war zuerst unverriegelt** (Codex-Befund aus Runde
    32). Der erste Umzug war gegen Parallelität geschützt, der in Runde 32
    nachgezogene Retry umging den Anspruch vollständig: Acht gleichzeitige
    zweite Bestätigungen liefen alle in denselben Rückruf. Anspruch und
    Ausführung liegen deshalb jetzt in **derselben** Methode
    (`MigrationGate.retry_release`), und der Riegel ist eine einzige
    `Enum`-Zustandsgröße statt dreier Flags — eine halb umgeschaltete Lage
    kann es damit nicht mehr geben.
    `…::test_der_wiederholte_start_gewinnt_ebenfalls_genau_ein_aufrufer` und
    `test_migration_endpoints.py::test_parallele_wiederholungen_starten_genau_einen_scheduler`
    schicken acht Threads an einer Barriere los; gemessen ohne den Anspruch:
    acht Rückrufe statt einem, und ohne die zusätzliche Sperre in
    `app/main.py` auch acht wirklich gestartete Scheduler.
[^z]: Die Reason-Codes sind stabil und stehen an einer Stelle
    (`app/migration.py`), Vorschau und Bericht teilen ein Antwortmodell, und
    `tests/test_migration_plan.py` prüft jeden Code gegen eine ausgeschriebene
    Erwartung.

    **Die DE/EN-Übersetzung ist seit 2B da** und liegt unter
    `migration.reason.*` in beiden Katalogen.
    `tests/test_migration_reason_catalogue.py` hält sie **über die
    Sprachgrenze hinweg** gegen `REJECTION_REASONS`: Jede Kennung braucht
    einen Satz, jeder Satz eine Kennung, und beide Kataloge müssen dieselbe
    Menge tragen. Ohne diese Prüfung merkte niemand, dass eine neue Kennung im
    Backend zwei TypeScript-Dateien nicht erreicht — im UI stünde dann die rohe
    Kennung statt eines Grundes. Mutationsgeprüft: ein entfernter Schlüssel
    macht den Test rot.

    Ein Grund fällt trotzdem nie ganz weg: Kennt der Katalog eine Kennung
    nicht, zeigt die Liste sie **roh** an, statt die Zeile ohne Begründung zu
    lassen.
[^aa]: `tests/test_migration_apply.py::test_nach_dem_umzug_ist_die_halbe_identitaet_unmoeglich`
    und `./_tickets/T-21-smoke.sh` `#2e`. Beide prüfen nicht nur, dass gerade
    keine halbe Zeile **da** ist, sondern dass keine mehr **entstehen kann**:
    Der `INSERT` ohne Identität muss scheitern. Eine Zählung
    `COUNT(*) WHERE ticker IS NULL` hätte die schwächere Aussage getroffen.

    Dass kein Endpunkt eine halbe Identität serialisiert, folgt daraus — es
    gibt keine Zeile mehr, die es könnte.
[^ac]: **Im Browser durchgefahren**, nicht nur getestet: Alt-Bestand auf
    eigenem Port, Vorschau mit Bilanz (2 umziehen, 2 gehen) und den echten
    Verlustzahlen (`VTI`: 14 Kurspunkte, 28 Tagesschlusskurse), Backup-Hinweis,
    Klick auf „Umzug jetzt ausführen", Bericht mit denselben Zeilen, „Weiter
    zum Dashboard" — und danach die Tabelle mit den beiden migrierten Papieren,
    **ohne** Fehlermeldung.

    **Genau dieser Durchgang hat einen Fehler gefunden, den kein Test zeigte.**
    Nach dem Umzug meldete die Oberfläche „Instrumente konnten nicht geladen
    werden"; dahinter ein `500` mit `no such column: q.currency`. Ursache war
    das Test-Fixture: Es legte eine `quotes`-Tabelle ohne `volume` und
    `currency` an — eine Alt-Datenbank, die es nie gegeben hat (der echte
    Bestand trägt beide, nachgesehen mit `PRAGMA table_info`). Der Fehler
    konnte nur deshalb bis in die Oberfläche laufen, weil **jede** Prüfung bei
    `/migration/report` endete und keine den Weg danach ging. Das Schema steht
    jetzt einmal in `tests/legacy_schema.py` statt dreimal abgeschrieben, und
    `…::test_nach_dem_umzug_liefert_der_bestand_wieder_aus` geht den Weg
    danach. Mutationsgeprüft: ohne die beiden Spalten wird er rot.

    Automatisiert: `dashboard/tests/components/MigrationGate.spec.ts`
    (9 Fälle) — Liste, Bilanz, Backup-Hinweis, Bestätigung, Bericht und die
    rohe Kennung als Rückfall.
[^ad]: **Mit Einschränkung.** Die Abbildung von `/ready` auf die Lage ist in
    `dashboard/tests/composables/useMigration.spec.ts` geprüft, einschließlich
    des Falls, der die Trennung überhaupt nötig macht: `degraded` trägt zwei
    verschiedene Lagen, und erst `database` (`ok` gegen `error`) trennt sie.
    Mutationsgeprüft: Fällt die Unterscheidung weg, wird der Test rot.

    **Nicht im Browser gesehen** habe ich den Bildschirm „Umzug erledigt,
    Betrieb nicht angelaufen" — den erzwingt man nur mit einem gescheiterten
    `RefreshScheduler.start`, also nicht ohne Eingriff in den Produktcode. Er
    steht als Testfall, nicht als Augenschein.
[^ae]: `tests/test_identity_intake_paths.py` — die echte Kette Router →
    Intake-Service → Cache-Dienst → Quote-Service → Repository auf einer
    echten SQLite-Datei. Ersetzt sind allein die Außengrenzen (Kursquelle,
    ETF-Anreicherung, EOD-Historie), **keine** eigene Core-Komponente.

    `test_beide_eingabeformen_ergeben_dasselbe_listing` prüft beide Formen
    gegen dieselbe Identität **und** dasselbe gespeicherte `symbol`: Ein Test
    nur auf die Identität hätte einen falschen Abrufalias nicht bemerkt.
    `test_die_zweite_form_findet_dasselbe_papier_wieder` ist die schärfere
    Fassung — `EUNL.DE` anlegen, dann `EUNL.XETR` schicken, dieselbe
    `listing_id`.

    Beim Bauen gefunden: `EUNL.XETR` wurde vorher **gar nicht** erkannt.
    `identity_from_symbol` zerlegt gespeicherte Symbole, und die tragen immer
    den Provider-Alias; die MIC-Form ist eine reine Eingabeform. Neu ist
    `identity_from_input` — der Aliasweg läuft durch die vorhandene Funktion,
    nur die MIC-Form kommt dazu.

    **Runde 40, Befund 1 von Codex:** Die aliaslosen Börsen fehlten. `AAPL.XNAS`
    und `AAPL.XNYS` tragen denselben Abrufalias `AAPL` — der Aufnahmeweg bildete
    ihn und schlug damit nach, womit die genannte Börse verlorenging: auf leerem
    Bestand ein `500`, bei vorhandenem `AAPL/XNYS` eine Antwort mit der falschen
    Börse. Der Fehler saß dabei eine Ebene tiefer als sein Fundort, denn auch
    `_find_instrument_id` suchte über `symbol`. Nachgeschlagen wird jetzt ISIN,
    dann `(ticker, mic)`, dann Symbol **nur wenn es zerlegbar ist**.

    Zwei Kettentests halten beide Lagen fest, dazu der doppeldeutige Suffix in
    `test_exchanges.py` — mutationsgeprüft, samt der Gegenprobe, dass ein
    vierstelliger Alias **derselben** Börse kein Konflikt ist.

    Live: `./_tickets/T-21c-smoke.sh --run`, **13/13** mit Netz. Der Smoke
    zeigte dabei eine falsche Erwartung von mir: Yahoo liefert für `AAPL` eine
    ISIN, und `one_active_listing_per_isin` lässt kein zweites Listing zu — die
    Zeile **wandert** auf die genannte Börse. Ohne ISIN stehen beide
    Notierungen nebeneinander, so im Kettentest gebaut.
[^af]: **Alle vier Zeilen des Erfolgsvertrags** sind über die echte Kette
    geprüft und stehen im OpenAPI-Snapshot: `201` bei Neuanlage, `200` beim
    bekannten Papier (beide mit `InstrumentSummary`), `400` mit
    `{code, params}` für alle Ablehnungsgründe, `502` bei toter Quelle. Der
    Rumpf liegt **nicht** unter `detail` — eigens geprüft.

    In Runde 39 stand hier `◑`: Der `502`-Fall war zugesagt, aber nicht
    durchgespielt. `test_eine_tote_quelle_ist_ein_502_mit_kennung` schließt
    das, und zwar über die **Außengrenze** — die Kursquelle liefert nichts,
    alles andere läuft echt.

    Dabei kam ein zweiter Befund heraus (Codex, Runde 39): `identifier: ""`
    lief wegen `min_length=1` in FastAPIs untypisiertes `422`, während
    `identifier: " "` den zugesagten `400 identifier_empty` bekam. Die
    Kennung war damit ausgerechnet für den häufigeren Fall unerreichbar — ein
    leeres Feld abzuschicken ist normal, ein Leerzeichen hineinzuschreiben
    nicht. Die Längenprüfung ist gefallen; die Leere beantwortet der Service.
[^ag]: `test_der_router_kennt_die_eingabeformen_nicht` prüft die
    Schichtengrenze **mechanisch**: Im Router-Modul darf weder
    `identity_from_input` noch `split_symbol`, `EXCHANGES` oder `is_isin`
    vorkommen. Ein Test, der nur das Verhalten prüft, bliebe grün, wenn die
    Regel dorthin zurückfiele — sie täte ja dasselbe.

    Der Router mappt `created` auf den Status und serialisiert `summary`;
    einen zweiten Existenz-Check gibt es nicht, weil er keine
    Repository-Abfrage hat.
[^ah]: **Zwei Tests mit klarer Rollenteilung**, und die Rollen sind gemessen,
    nicht behauptet: `test_ein_verlorenes_rennen_meldet_keine_neuanlage`
    erzwingt den Konflikt (der Preflight sieht die vorhandene Zeile **einmal**
    nicht) und ist der Beleg. `test_genau_ein_paralleler_erstschreiber_legt_an`
    ist die realistische Probe mit acht Threads.

    Eine Mutationsprobe hat gezeigt, dass der `IntegrityError`-Zweig unter
    Threads nur in **zwei von drei** Läufen überhaupt erreicht wird — der
    Thread-Test allein wäre also kein Beleg gewesen. Dieselbe Probe hat einen
    Fehler im Test selbst gefunden: Er prüfte `count(True) == 1` und blieb
    grün, obwohl die Hälfte der Schreiber abstürzte (eine Ausnahme im Thread
    lässt pytest kalt). Er zählt jetzt zuerst die Gesamtzahl der Rückmeldungen.
[^ai]: `contract/core-contract.json` steht auf `2.0.0`, der Endpunkt ist
    aufgenommen, `ticker` und `mic` sind Pflichtfelder von `quote` und
    `instrument`, `listing_id` von `instrument`. Der Snapshot ist neu erzeugt
    (`UPDATE_CORE_SNAPSHOT=1`), `test_der_core_entspricht_dem_schnappschuss`
    grün, und `./_tickets/T-21c-smoke.sh` prüft zusätzlich, dass `/fields` zur
    Laufzeit dieselbe Version nennt.

    **`listing_id` steht bewusst nicht auf `quote`** — sie entsteht beim
    Anlegen der Zeile, und `ensure_core_complete` prüft *vor* dem Speichern.
    Sie dort zuzusagen hieße, der Beschaffung eine Speicher-Identität
    abzuverlangen, die es zu dem Zeitpunkt nicht gibt.

    Der Sprung hat zwei Lücken aufgedeckt, weil `ensure_core_complete` seine
    Pflichtliste **aus dem Artefakt** liest: `_from_cache` setzte `ticker`/`mic`
    nicht, und `get_quote_for_known` rechnete die Identität allein aus dem
    Symbol zurück — bei aliaslosen Börsen `(None, None)`, also wäre die
    Auffrischung **jedes US-Papiers** ein `502` geworden.

    **Runde 40, Befund 2 von Codex:** Das Paket widersprach sich trotzdem noch.
    Das Artefakt sagte Pflicht, das veröffentlichte OpenAPI-Schema führte
    `ticker` und `mic` als optional **und** nullable — ein generierter Client
    durfte also genau den Zustand annehmen, den `2.0.0` abschafft. Ursache war
    `str | None` im Modell: Die Pflicht stand nur im Artefakt und wurde erst
    zur Laufzeit geprüft. Beide sind jetzt auch im Modell nicht nullbar, und
    ein fehlender Wert scheitert **vor** dem Bauen (`require_core_values`)
    statt als `ValidationError` mit `500`.

    Dasselbe galt seit T-24 unbemerkt für `currency` — mitkorrigiert, weil ein
    Vertragstest sonst am eigenen Vertrag gescheitert wäre.

    `test_jedes_pflichtfeld_des_artefakts_ist_im_schema_auch_zugesagt` hält
    beide Quellen gegeneinander. Er prüft **nur** die Nullability, und das ist
    Absicht: Bei einem Antwortmodell sagt die `required`-Liste nichts, weil ein
    Feld mit Vorgabewert trotzdem immer serialisiert wird. Eine Prüfung darüber
    sähe strenger aus, als sie ist.

    `docs/rest-core-contract.md` steht auf `2.0.0` und nennt, was der Sprung
    bricht; der Verweis von `instrument.listing_id` auf das nicht existente
    `quote.listing_id` ist ersetzt.
[^aj]: **Codex Runde 42 — Parallelitäts- und Kollisionspfade sind noch offen.**
    Der normale `_find_instrument_id`-Aufruf reicht `(ticker, mic)` weiter;
    der Retry nach `sqlite3.IntegrityError` ruft dieselbe Funktion weiter nur
    mit ISIN und `symbol` auf. Eine deterministische Gegenprobe mit
    `AAPL/XNAS`, ohne ISIN und einem erzwungen verlorenen Rennen endet deshalb
    mit `IntegrityError` statt `created=false`; die beiden Lookups sahen
    nacheinander `(AAPL, XNAS)` und `(None, None)`.

    Eine zweite Gegenprobe legt `AAPL/XNAS` ohne ISIN und `AAPL/XNYS` mit ISIN
    an und lässt dieselbe ISIN danach nach `XNAS` wandern. Die Aktualisierung
    läuft in den eindeutigen `(ticker, mic)`-Index, statt beide Erkenntnisse
    zusammenzuführen. Beide Fälle enden aktuell mit HTTP 500 am Aufnahmeweg.

    **Runde 43:** Der Retry-Fall ist korrigiert. Der zweite Fall trägt nun im
    Repository den Namen `IdentityConflictError`, bleibt am echten
    Intake-Endpunkt aber ein untypisierter HTTP 500, weil Service und Router
    ihn nicht behandeln. Seine spätere Datenzusammenführung wird wegen der
    offenen `listing_id`-/Historienpolitik als eigenes Plugin-Folgeticket
    geschnitten; T-21 braucht davor einen typisierten 409 samt Kettentest.

    **Runde 44:** Beide Fälle sind geschlossen. Der Konflikt wird zentral in
    `app/main.py` auf `409`/`identity_conflict` abgebildet und über die echte
    Kette geprüft (`#2i2`, [^al]). Die Zusammenführung selbst bleibt ein
    eigenes Folgeticket — der `409` sagt, was der Fall ist, er löst ihn nicht.
    Ob `#2i` und `#2j2` damit von `◑` auf `✅` steigen, entscheidet Codex: Die
    Einschränkung stammt aus seinem Review, und sie sich selbst aufzuheben
    wäre genau das selbstbestätigende Orakel aus `CLAUDE-REVIEW-PATTERNS.md`.

    **Codex Runde 44:** Der neue `identity_conflict`-Pfad ist geschlossen;
    T-21 bleibt dennoch offen, weil die bereits in T-24 zugesagte allgemeine
    Symbol-Mehrdeutigkeit noch nicht umgesetzt ist. Zwei gespeicherte Zeilen
    `AAPL/XNAS` und `AAPL/XNYS` mit demselben `symbol=AAPL` ergeben an
    `GET /quote?symbol=AAPL` weiterhin `200` für die ältere Zeile statt `409
    symbol_ambiguous` mit beiden `listing_id`. Ein aktueller Core-Vertrag darf
    diese Zusage nicht zugleich führen und als „noch an keinem Endpunkt
    umgesetzt“ kennzeichnen.

    **Codex Runde 45:** Auch dieser letzte Vorbehalt ist geschlossen. Eine
    gemeinsame Repository-Auskunft liefert bei Mehrdeutigkeit alle Kandidaten,
    und die acht bestandsbezogenen Symbolwege antworten mit `409
    symbol_ambiguous`, ohne Daten zu verändern. Die zuvor offenen Zeilen `#2i`,
    `#2j2` und `#2k` sind nach unabhängiger Laufzeit-, Vertrags- und
    Parallelitätsprüfung auf `✅` gehoben; Übergabe 3 ist freigegeben.
[^ak]: **Codex Runde 42 — das Artefakt und OpenAPI sind noch nicht
    deckungsgleich.** Gegen `app.openapi()` fehlen in der `required`-Liste:
    `quote.cached/stale`, `instrument.history_count/manual_fields/
    shadowed_fields`, `daily.currency`, `history.currency` und
    `fx.cached/stale`; `daily.currency` und `history.currency` sind zusätzlich
    nullable. Die neue Querprüfung erfasst nur `quote` und `instrument` und
    prüft die `required`-Liste ausdrücklich nicht. In einem Antwortschema ist
    diese Liste trotzdem die Zusage, ob ein JSON-Feld vorhanden sein muss;
    ein Pydantic-Default garantiert das nur im aktuellen Erzeuger, nicht im
    veröffentlichten Schema für Konsumenten.
[^al]: **Zwei Tests, zwei verschiedene Fragen** — und beide sind ohne ihre
    Korrektur nachweislich rot gelaufen, nicht bloß behauptet.

    `test_der_zweite_anspruch_auf_dieselbe_identitaet_ist_ein_409` in
    `tests/test_identity_intake_paths.py` läuft über die **echte** Kette
    Router → Intake-Service → Cache-Dienst → Quote-Service → Repository mit
    echter SQLite-Datei; ersetzt ist allein die Kursquelle, und die meldet
    hier die ISIN — genau das löst die Kollision aus. Ohne den Handler in
    `app/main.py` schlägt der Test mit `IdentityConflictError` aus
    `app/repository.py:589` fehl. Geprüft wird nicht nur der Status, sondern
    der Rumpf: `{code, params}` mit `ticker`, `mic` und `isin`.

    `test_der_konflikt_steht_auch_in_der_veroeffentlichten_form` fragt die
    laufende `openapi.json` ab und verlangt den `409` samt `ErrorDetail`-Rumpf
    an jedem speichernden Vertragsendpunkt.

    **Korrektur aus Runde 45:** In Runde 44 stand hier „alle drei", und die
    Liste im Test hatte drei Einträge — `POST /instruments/intake`,
    `GET /quote`, `GET /quote/{isin}`. Es sind **sieben**: Auch die vier
    Historien- und Tageskurs-Wege legen ein unbekanntes Papier über
    `ensure_instrument` an und laufen damit durch `save_quote`. Die Zahl war
    nicht gemessen, sondern von den Endpunkten abgeschrieben, die ich gerade
    angefasst hatte — `P-02` in Reinform. Die vier fehlenden sagen den Fall
    jetzt zu und stehen im Test.

    **Nicht im Smoke-Script.** Der Fall braucht zwei Zeilen, die über den
    normalen Weg nicht nebeneinander entstehen: Yahoo meldet zu `AAPL` immer
    die ISIN, also zieht die zweite Eingabe die erste Zeile um, statt eine
    zweite anzulegen (`#2f`, live gemessen). Es ist ein Zustand aus
    gewachsenem Bestand, und ihn im Script von Hand in die Datenbank zu
    schreiben hieße, den Beleg zu bauen, den man messen will.
[^am]: **`tests/test_symbol_ambiguity.py`, sieben Tests über die echte Kette.**
    Der Aufbau ist kein Sonderfall: Zwei Listings mit dem Alias `AAPL` sind
    genau der Bestand, den `#2f` verlangt. Mehrdeutig ist nicht der Bestand,
    sondern die **Frage** nach dem Alias.

    Geprüft sind ein lesender Weg (`GET /quote?symbol=`) und **zwei**
    verändernde (`DELETE /instruments/by-symbol/`, `PUT .../isin`). Der
    Löschweg ist der schärfere Fall und wird deshalb doppelt geprüft — Status
    **und** Bestand danach: `DELETE FROM instruments WHERE symbol = ?` entfernte
    bei zwei gleichnamigen Listings beide samt Kurshistorie über den Cascade.
    Ein Test nur auf den Status wäre grün geblieben, hätte der `409` nach dem
    Löschen gegriffen.

    Zwei Gegenrichtungen stehen daneben, damit das Orakel sich nicht selbst
    bestätigt: Ein **eindeutiges** Symbol muss weiterhin `200` liefern, und der
    Aufnahmeweg muss `AAPL.XNAS` neben `AAPL.XNYS` weiterhin anlegen dürfen.
    Ohne sie wäre auch die zu scharfe Fassung „jedes doppelte Symbol ist ein
    Fehler" grün gelaufen — sie hätte `#2f` gebrochen.

    Ein siebter Test hält die Fixture gegen die Laufzeit:
    `contract/fixtures/quote-409-ambiguous-symbol.json` wird von außen gelesen,
    ohne StockInfo zu starten. Ihre erste Fassung zeigte zwei Kandidaten mit
    **derselben** ISIN — einen Zustand, den `isin TEXT UNIQUE` verbietet.

    **Gegenprobe gelaufen:** Wird allein die Mehrdeutigkeitserkennung in
    `_unique_symbol_row` stillgelegt, fallen **fünf** der sieben Tests — die
    drei Endpunktwege, die Rumpfprüfung und der Fixture-Wächter. Grün bleiben
    genau die zwei Gegenrichtungen, und das ist die Aussage: Sie prüfen den
    Normalfall, der von der Regel unberührt bleiben muss.
[^ab]: `./_tickets/T-21-smoke.sh --run` gegen eine Sicherung des **echten**
    Bestands: `GOLD.SG` migriert zu `GOLD/XSTU` und behält seine **257**
    Tagesschlusskurse, `VGWL.DE` seine 2234. Abgelehnt wird allein `VTI` mit
    einem Kurspunkt. Genau die Bilanz aus dem Entwurf; das Original war
    hinterher byte-identisch.
[^h]: `./_tickets/T-21b-smoke.sh --run` — **sechs Checks live gegen das echte
    Netz**, auf frischen temporären Datenbanken, über den HTTP-Weg. Zwei
    Läufe, weil die Kaskade zwei Wege hat: `VGWL.DE → VGWL/XETR` über die
    eigene Börsentabelle (`#5a`) mit der Rückrechnung `VGWL + Suffix(XETR) =
    VGWL.DE` (`#5b`), und `AAPL → AAPL/XNAS` über Yahoos Börsencode (`#5c`).

    **Damit ist die Lücke aus Teil 1 geschlossen**, und zwar dort, wo das
    Ticket sie verortet hat: Der echte MIC kommt aus dem aufgelösten Listing,
    nicht aus der Börsentabelle und nicht geraten.

    Die **Gegenprobe** trägt den Lauf: `BRK-B` wird abgelehnt (`#5d`, HTTP
    502) und hinterlässt **keine** Zeile (`#5e`). Ohne sie prüfte das Script
    nur, dass Erfolgsfälle gelingen. Dazu `#5f`: jede Zeile eine eigene
    `listing_id` — die entsteht jetzt beim Anlegen statt erst beim nächsten
    Start.

    Dazu 15 neue Tests (`tests/test_resolver_identity.py`,
    `tests/test_identity_creation.py`). **Drei Mutanten belegen, dass sie
    beißen**: `canonical_identity` alles durchwinken lassen (2 Tests fallen),
    Yahoos Bindestrich zum Punkt raten (1), eine leere Identität die
    gespeicherte überschreiben lassen (1).

    **Runde 3 hat gezeigt, dass dieses ✅ zu früh kam** (Codex): Geprüft war
    der ISIN-Weg. StockInfo hat aber drei Aufnahmewege, und zwei gingen an der
    Identitätsbildung vorbei — wer ein unbekanntes `VGWL.DE` über
    `GET /quote?symbol=` aufnahm, bekam `ticker=NULL, mic=NULL,
    legacy_unresolved`, obwohl das Symbol eindeutig zerlegbar ist.

    Unsichtbar blieb das, weil meine Tests an beiden Enden ansetzten: Die
    Speicherung bekam die fertige Identität **von Hand** übergeben, der
    Service-Test prüfte nur den ISIN-Pfad. Beide Enden sahen richtig aus, die
    Strecke dazwischen war nie gelaufen.

    `tests/test_identity_intake_paths.py` schließt das: die **echte Kette** —
    Router → Cache-Dienst → Quote-Service → Repository auf echter SQLite —,
    ersetzt sind nur die Außengrenzen, an denen sonst das Netz hinge. Zwei
    Mutanten belegen, dass die Tests beißen.

    Der dritte Weg (`get_quote_for_known`, über den der Scheduler läuft) hatte
    dasselbe Loch und trägt jetzt offene Zeilen **nach**. Damit ist die zweite
    Einschränkung unten erledigt, statt eine Fußnote zu bleiben.

    **Ein Unterschied bleibt, und zwar mit Absicht:** Der Symbol-Weg lehnt ein
    unzerlegbares Symbol **nicht** ab. Auf dem ISIN-Weg wählt StockInfo eine
    Notierung aus mehreren aus — eine halb geratene Identität wäre dort eine
    Entscheidung, die niemand getroffen hat. Auf dem Symbol-Weg nennt der
    Aufrufer das Listing selbst; ihm die Auskunft zu verweigern, weil die
    Börsentabelle für suffixlose Symbole nur einen Sammelcode führt, nähme ihm
    eine Abfrage weg, die es heute gibt. Die Zeile entsteht sichtbar offen.

    **Runde 4** hat am Verhalten nichts mehr geändert, aber am Werkzeug: Die
    leeren Außengrenzen der Tests standen viermal nebeneinander und liegen
    jetzt in `tests/boundaries.py`. `tests/test_boundaries.py` vergleicht sie
    über `inspect.signature` gegen `EtfEnricher` und `DailyCloseProvider` —
    eine Grenze mit `*args, **kwargs` nimmt sonst jeden Aufruf an und verdeckt
    einen gebrochenen Vertrag ausgerechnet in dem Test, der die echte Kette
    prüfen soll.

    Was dabei **offen geblieben** ist und nicht zu `#5` gehört:

    * `XNAS`, `XNYS`, `ARCX`, `XASE`, `BATS` stehen nicht in `EXCHANGES`. Aus
      `(AAPL, XNAS)` lässt sich deshalb **kein** Yahoo-Symbol zusammensetzen —
      die Rückrichtung MIC → Suffix fehlt für die US-Plätze. Heute stört das
      nichts (das Symbol ist gespeichert), aber T-23 braucht sie: Dort setzt
      jede Quelle ihr Format selbst zusammen.
    * ~~Der Nachtrag einer offenen Zeile passiert nur über die ISIN.~~
      **Erledigt in Runde 3:** Auch der Weg für bekannte Papiere trägt nach,
      also auch der Scheduler-Refresh. ~~Offen bleibt nur, was sich aus dem
      Symbol nicht zerlegen lässt (`GOLD.SG`, `VTI`) — dafür ist die manuelle
      Zuordnung aus Teil 3 da.~~ **Nachgemessen 2026-08-24, mit einer wichtigen
      Einschränkung:** Auf dem **ISIN-Weg** trägt der Yahoo-Weg nach (`VTI` →
      `ARCX`). Auf dem **Symbolweg** nicht — `get_quote_for_known` löst nicht
      auf, es holt nur Kurse, und `split_symbol('AAPL')` bleibt für immer
      `(None, None)`. Deshalb verlangt Teil 3 dort die Kombination im Vertrag,
      statt hinterher zu reparieren.
    * ~~Eine **von Hand** gesetzte Zuordnung ist von einer maschinellen nicht
      zu unterscheiden — beide tragen `resolved`. Teil 3 braucht dafür einen
      eigenen Status.~~ **Hinfällig seit 2026-08-24:** Mit der gestrichenen
      Handzuordnung gibt es keine manuelle Zuordnung, die ein Auflösungslauf
      überschreiben könnte. `identity_status` bleibt zweiwertig.
    * **Verhaltensänderung, absichtlich:** Ein Yahoo-Treffer an einer Börse,
      die `EXCHANGES` nicht führt (`GOLD.SG`, Stuttgart), wird jetzt
      abgelehnt statt übernommen. Das ist die Regel des Tickets — wer die
      Börse aufnehmen will, trägt sie in die Tabelle ein, dann greift wieder
      der Suffix-Weg.

[^g]: `./_tickets/T-21-smoke.sh --run` gegen eine **Sicherung** von
    `data/stockinfo.db` (sechs gewachsene Papiere, 48 Kurspunkte) — das
    Original wird nur gelesen. Die Sicherung entsteht über die
    SQLite-Backup-API, nicht per `cp`: Die App läuft im WAL-Modus, und eine
    Dateikopie ließe committete Einträge aus — der Lauf liefe dann an genau
    den neuesten Fällen vorbei (Codex, Runde 2). Neun Checks grün: 6 Instrumente vorher und
    nachher, 48 Kurspunkte vorher und nachher, sechs eindeutige `listing_id`,
    vier zerlegt (`VGWL.DE`, `EUNL.DE`, `APC.DE`, `BRYN.DE` → `XETR`), zwei
    offen (`GOLD.SG` — das Suffix `.SG` steht nicht in der Tabelle — und
    `VTI`, suffixlos), Indizes umgezogen **und eindeutig**. Das Script
    migriert **zweimal**; genau dort hat die Alt-Bereinigung in Runde 1
    Listings gelöscht.

    Die Prüfungen rechnen nach statt zu behaupten, und zwar in der
    **Gegenrichtung**: Was dieser Lauf zugeordnet hat, muss sich aus
    `(ticker, mic)` wieder zu `symbol` zusammensetzen; offene Zeilen tragen
    weder Ticker noch MIC; bereits bestehende Zuordnungen bleiben unverändert
    (`#2c`) und dürfen keinen Sammelcode tragen (`#2d`). Ein Lauf, der nichts
    zugeordnet hat, gilt als **nicht geprüft**.

    `#2d` prüft, dass jede Zeile in **genau einem** gültigen Zustand steht:
    `resolved` verlangt Ticker und echten MIC, `legacy_unresolved` verlangt
    beide Felder leer, ein unbekannter Status ist ein Fehler. Nur auf den
    Sammelcode zu sehen genügte nicht — eine Zeile, die `resolved` behauptet
    und nichts trägt, kam sonst durch (Codex, Runde 5).

    **Die Regel gehört in den Produktcode, nicht nur ins Prüf-Script**
    (Codex, Runde 6): Vollständig ist eine Identität erst mit einem
    **echten** MIC — `is_real_mic` in `app/exchanges.py` ist die eine Stelle,
    die das entscheidet, benutzt von Migration und Prüfung. Der Sammelcode
    `US` überlebt die Migration damit nicht mehr; er wird neu bewertet und
    landet bei den offenen Fällen.

    Entschieden wird dabei nach den **Daten**, nicht nach der Beschriftung:
    Eine vollständige Zuordnung mit kaputtem Status behält ihre Identität, nur
    der Status wird korrigiert und protokolliert. Meine erste Fassung hatte
    sie überschrieben — genau der Verlust, den das Ticket verhindern will.

    **Unbekannt heißt nicht gültig** (Codex, Runde 7): `is_real_mic` ließ
    zunächst jeden der Tabelle unbekannten String durch — auch `NOT-A-MIC`,
    `xnAs` oder `XNAS ` mit Leerzeichen. Geprüft wird jetzt zusätzlich die
    Schreibweise nach ISO 10383: genau vier Zeichen, Großbuchstaben oder
    Ziffern. `XNAS` bleibt erlaubt, weil die Tabelle eine Auswahl der
    auflösbaren Börsen ist und kein Verzeichnis aller MICs. Geprüft wird mit
    `fullmatch`: `$` matcht in Python auch **vor** einem abschließenden
    Zeilenumbruch, und `XNAS\n` wäre durchgegangen — ein Wert, den der
    Eindeutigkeits-Index sogar von `XNAS` unterscheidet (Codex, Runde 8).

    `#2d` im Prüf-Script hat dafür ein **eigenes** Urteil, formuliert über die
    Zeichenmenge statt über ein Muster. Ein Orakel darf die Funktion nicht
    befragen, die es prüft — sonst bestätigt es nur, dass sie mit sich selbst
    übereinstimmt. Gegengeprüft mit absichtlich kaputtem Validator
    (`match` statt `fullmatch`): `#2d` schlägt an, Exit 1. Ein leerer Bestand lässt den Lauf **fehlschlagen** —
    vorher hätte er dort grün gemeldet, ohne einen einzigen Fall geprüft zu
    haben (Codex, Runde 2). Gegenproben: leere Datenbank → Exit 1; ein
    committeter Eintrag im WAL → wird mitgesichert und mitgezählt (7 statt 6).

    **Das Oracle rechnet vorwärts** (Codex, Runde 3): Die Migration zerlegt
    `symbol` → `(ticker, mic)`, die Prüfung setzt `(ticker, mic)` → `symbol`
    zusammen. Mit derselben Funktion zu prüfen hieße, sich selbst recht zu
    geben — und es verwarf einen gültigen Zielzustand: Ein von Hand
    zugeordnetes `VTI` → `VTI/XNAS` behält sein suffixloses `symbol`.
    Nachvalidiert wird deshalb nur, was **dieser Lauf** zugeordnet hat; `#2c`
    hält zusätzlich fest, dass bestehende Zuordnungen unverändert bleiben.
    Gegenprobe mit `WALONLY/XNAS` im WAL: angenommen.

---

## Details

### Warum es geht — die Rückrechnung ist eindeutig

Gemessen am 2026-08-19 über die vollständige Börsentabelle:

```
Börsen gesamt: 33
Suffixe doppelt vergeben: keine — Zuordnung ist eindeutig

EUNL.DE  -> ticker=EUNL  suffix=.DE  mic=XETR
XIC.TO   -> ticker=XIC   suffix=.TO  mic=XTSE
VTI      -> ticker=VTI   suffix=''   → Sammelcode US, **kein** MIC
```

Die letzte Zeile zeigt zugleich die Grenze der Messung: Für suffixlose Symbole
liefert die Tabelle nur den Sammelcode `US`. Welcher echte MIC gilt (`XNYS`
gegen `XNAS`), steht dort nicht — das muss aus dem aufgelösten Listing kommen.

Kein Suffix ist doppelt belegt. **Für Symbole, die aus der eigenen Regel
stammen**, ist die Zerlegung damit eindeutig.

Das gilt aber nicht für alle: Was der Yahoo-Fallback geliefert hat, folgt der
Konvention nicht zwingend (siehe unten). Diese Fälle werden **gemeldet**, nicht
geraten — „jedes Symbol lässt sich zerlegen" wäre eine Behauptung, die der
nächste Bestand widerlegt.

### Was `symbol` heute erzwingt

```
app/db.py:21    symbol TEXT NOT NULL
app/db.py:172   CREATE UNIQUE INDEX idx_instruments_symbol
```

Pflichtfeld **und** global eindeutig. Bleibt das so, braucht auch ein Instrument,
das ausschließlich über EODHD oder Twelve Data verwaltet wird, ein gültiges,
eindeutiges **Yahoo**-Symbol. Yahoo wäre dann weiterhin Teil der Identität — das
Ticket verfehlte sein eigenes Ziel.

**Weg (revidiert nach Codex-Runde 3):** `symbol` **bleibt verpflichtend** — die
erste Fassung wollte es `NULL`-fähig machen.

Der Grund ist **nicht** StockPortfolio: Das gehört demselben Autor, ist nicht
öffentlich und wäre in einem Zug mitzuändern. Der Grund ist, dass StockInfo
selbst verteilt wird — GitHub, Docker Hub, Unraid-Template. Wer die API direkt
nutzt, bekäme den Bruch ab, und man erfährt es nicht.

Was an `symbol` hängt, zeigt der Testkonsument stellvertretend:

```text
src/api/types.ts:17        symbol: string                      // nicht nullable
src/types/portfolio.ts:29  symbol: string                      // Pflicht je Position
src/api/mappers.ts:56      return entry.isin ?? entry.symbol   // Cache-Schlüssel
```

Die dritte Stelle bräche **still**: Der Cache-Schlüssel wäre `undefined`.

Stattdessen **additiv**: `ticker` und `mic` kommen dazu und werden die
kanonische Identität; `symbol` bleibt als stabiler Listing-Bezeichner erhalten
und wird nach derselben Regel erzeugt wie bisher. Das ist kein Anbieter-Alias —
das Format gehört der App (`resolver.py:130` bildet es aus der eigenen
`EXCHANGES`-Tabelle), nicht Yahoo.

**Der Eindeutigkeits-Index zieht mit um — aber nicht ersatzlos.** `symbol`
bleibt Pflichtfeld und verliert den globalen Unique-Index; an seine Stelle tritt
`(ticker, mic)` **und** eine `listing_id` als Schlüssel für Maschinen. Den Index
nur zu entfernen wäre ein stiller Bruch: `get_instrument_by_symbol` nimmt per
`ORDER BY id LIMIT 1` die ältere Zeile, und `DELETE /instruments/by-symbol/…`
träfe dann das falsche Instrument. Die Regeln dafür stehen in **T-24**.

Sind später mehrere Anbieter-Aliase nötig, gehören sie in eine eigene Tabelle
statt als Spalten in die Instrumentenzeile.

### Der eine Pfad, der die Migration bricht

`resolver.py:170` übernimmt im Yahoo-Fallback `top["symbol"]` — den String, den
Yahoos Suche liefert. Der folgt der eigenen Konvention **nicht** zwingend
(`BRK-B` mit Bindestrich). Solche Symbole sind später nicht sicher in `ticker` +
`mic` zu zerlegen.

**Entschieden (Codex, 2026-08-20): normalisieren, wenn eindeutig — sonst
ablehnen und sichtbar machen. Niemals raten.**

Der Yahoo-Adapter kennt Yahoos Eigenheiten, also gehört das Wissen dorthin:

1. Yahoos Börsencode über eine **explizite** Tabelle auf einen echten MIC abbilden
2. den Ticker nur für **bekannte, umkehrbare** Fälle in die kanonische Form bringen
3. das ursprüngliche Yahoo-Symbol als Provider-Alias behalten
4. `Resolved` erst liefern, wenn echter MIC **und** kanonischer Ticker feststehen

`BRK-B` darf **nicht** per Bindestrich-zu-Punkt-Regel zu `BRK.B` geraten werden —
diese Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
etwas anderes. Bleibt ein Treffer mehrdeutig: mit Grund in `/sources` und Log
sichtbar machen, nicht als `(ticker, mic)` speichern, `Unavailable` zurückgeben
~~und einen Weg zur Zuordnung von Hand anbieten~~ — **seit Runde 16:** mit
**stabilem Reason-Code** ablehnen. Der Rückweg ist die Neuerfassung über den
Aufnahmeweg (ISIN, `TICKER.DE` oder `TICKER.XETR`), nicht eine Handzuordnung.

„Übernehmen und als nicht zerlegbar markieren" wäre die schlechtere Variante:
Sie macht die gerade eingeführte kanonische Identität wieder optional und
belastet jedes spätere Quote- oder Daily-Plugin erneut mit einem Yahoo-Sonderfall.

### `US` ist kein MIC

`EXCHANGES` führt `US` als Sammelcode für NYSE/NASDAQ (OpenFIGI `exchCode=US`).
Das ist **kein** ISO-10383-MIC. Ein Feld, das mal echte MICs und mal diesen
internen Code enthält, wird beim ersten Anbieter, der echte MICs erwartet, zum
Problem.

**Entschieden (Codex, 2026-08-20):** Das kanonische Feld heißt `mic` und enthält
**ausschließlich echte MICs** (`XNYS`, `XNAS`). Der Sammelcode `US` bleibt als
interner OpenFIGI-Suchcode erhalten, taucht aber nie im kanonischen Feld auf.
Niemals raten, und niemals beide Codearten unter einem Namen führen.

Das betrifft auch T-18: Die Kaskade über die Heimatbörse muss auf echte MICs
abbilden, nicht auf den Sammelcode.

### Was sich sonst ändert

* `instruments` bekommt `ticker` und `mic` (nicht `exchange_mic` — der Name trüge sonst wieder zwei Codearten)
* Migration zerlegt bestehende Symbole über die Suffix-Tabelle
* Wer Kurse holt, setzt sein Format selbst zusammen — Yahoo `{ticker}{suffix}`,
  EODHD `{ticker}.{code}`, Twelve Data `symbol` + `mic_code`
* `ExchangeDef` verliert seine OpenFIGI-Spalten (`figi_id_type`, `figi_value`);
  dieses Wissen zieht zum OpenFIGI-Provider

### Warum das die Anbieterfrage löst

Recherchiert am 2026-08-19: **Kein kommerzieller Dienst verlangt ein eigenes
Identitätssystem.** Alle arbeiten mit Ticker plus Börse, nur die Schreibweise
unterscheidet sich — EODHD hängt `.XETRA` an, Twelve Data nimmt den MIC nach
ISO 10383 als eigenen Parameter. Und MIC ist bereits der Schlüssel der
`EXCHANGES`-Tabelle.

Quellen: [EODHD Exchanges API](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours),
[Twelve Data Docs](https://twelvedata.com/docs)

### ~~Der Zwischenzustand~~ — aufgehoben, es gibt keine halbe Identität mehr

> **Entscheidung Mike, 2026-08-24 (nach Runde 16).** Der unten beschriebene
> Zwischenzustand ist **aufgehoben**. Eine nicht auflösbare Altzeile darf
> nirgendwo als `NULL`-Identität weiterleben — nicht im aktiven Bestand, nicht
> im REST-Vertrag, nicht im UI.
>
> **Stattdessen:** Was einfach und eindeutig auflösbar ist, wird migriert. Alles
> andere kommt **nicht** in den gültigen Bestand und wird dem Benutzer mit altem
> Symbol, konkretem Grund, verlorenen Kurspunkten und der Aufforderung zur
> Neuerfassung gemeldet. `ticker` und `mic` sind danach Pflicht; als Invariante
> gilt `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`. Eine Quarantäne darf
> die Rohinformation halten, ist aber kein aktiver Instrumentdatensatz.
>
> **Der dritte Ausweg, den der Text unten für ausgeschlossen hielt** — „Daten
> löschen" — ist damit gewählt, aber unter einer Bedingung, die er nicht kannte:
> Es wird nicht stillschweigend gelöscht, sondern **abgelehnt und benannt**.
> Nachgemessen kostet das im echten Bestand ein einziges Papier (`VTI`, null
> Tageskurse), sofern `XSTU` vorher im Katalog steht. Steht es das nicht, kostet
> es `GOLD.SG` mit **257** Kurspunkten — siehe die Reihenfolgewarnung im
> Entwurf.
>
> `identity_status` entfällt damit ersatzlos: Die Spalte hätte nur noch einen
> Wert.

~~Wären `ticker` und `mic` sofort `NOT NULL`, könnte die Migration eine nicht
zerlegbare Zeile weder stehen lassen noch melden: Sie müsste raten, den Start
blockieren oder Daten löschen.~~

~~**Also braucht es einen ausdrücklichen Zwischenzustand:** die neuen Spalten
sind zunächst `NULL`-fähig, eine Kennzeichnung wie
`identity_status = legacy_unresolved` markiert offene Fälle, der Altdatensatz
bleibt lesbar und nutzbar, und erst nach erfolgreicher Zuordnung wird
`(ticker, mic)` zur Pflicht.~~

~~Ohne diesen Zustand ist „später von Hand zuordnen" ein Versprechen, das die
Migration technisch nicht halten kann.~~ **Der Satz stimmt weiter — und ist
genau deshalb hinfällig:** Weil die Migration „später von Hand" nicht halten
kann, wird seit Runde 16 gar nichts mehr versprochen, was sie nicht halten
kann. Sie lehnt ab und meldet.

### Risiko

Die Migration ist die einzige der Serie, die bestehende Daten anfasst. Vor dem
Lauf eine Kopie der Datenbank, und die Zerlegung vorher als Trockenlauf über die
echten Daten prüfen — ein Symbol, das die Tabelle nicht kennt, muss auffallen
statt still `NULL` zu werden.

**Die Eindeutigkeit der Suffixe gilt für den Bestand, nicht für die Zukunft.**
Gemessen wurde die heutige `EXCHANGES`-Tabelle. Nicht abgedeckt sind neue oder
unbekannte Suffixe, suffixlose Nicht-US-Symbole, von Hand eingetragene Symbole
und Ticker, in denen ein Punkt zum Namen gehört (`BRK.A`). Die Migration muss
solche Fälle **melden** statt zu raten — ~~und danach braucht es einen Weg, sie
von Hand zuzuordnen.~~ **Seit Runde 16:** Sie werden abgelehnt und im Bericht
genannt; der Weg zurück ist die Neuerfassung über den Aufnahmeweg, nicht eine
Handzuordnung.

---

## Auflösung

_(offen)_
