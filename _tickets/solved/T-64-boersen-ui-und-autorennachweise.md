# T-64 · Handelsplätze im UI erklären und Plugin-Autoren prüfbar anbinden

T-30 liefert die Deklaration zusätzlicher MICs, den Aufnahmeweg und die
REST-Auskunft. Dieses Ticket ergänzt die Exchanges-Oberfläche und den
ausführbaren Nachweis für Plugin-Autoren. Neue Plugin-Handelsplätze sollen
ohne Frontendänderung erscheinen, mit klarer Auskunft über die deklarierte
Unterstützung. Beispielsweise zeigt XBUD nun „regional · Kurs“ und eine
inaktive Archivquelle getrennt davon.

**Von Mike am 2026-09-09 als erledigt bestätigt.** Oberfläche,
Autor-Vertragstests und Beispiel sind umgesetzt und von Claude freigegeben.
Der noch fehlende Plugin-Hinweis mit Autorenlink wird ausschließlich in
[T-67](../T-67-boersenabweichung-anzeigen.md) umgesetzt und geprüft.
Die Seite lädt Katalog und Unterstützung aus REST, bietet Suche und Neuladen
und wechselt bei schmalem Fenster in eine Liste. Autor-Harness, US-Beispiel
und Anleitung sind nachgezogen. Das Beispiel verlangt Plugin-API 0.3;
die Paketveröffentlichung gehört nicht zum Ticketumfang.

## Für dich

Mike hat seine Einschätzung „T-64 sollte erledigt sein“ am 2026-09-09 ergänzt:
„Ah - warte bei T-64 sind die Plugin-Authoren noch nicht eingebunden...“.
Damit wurde das Ticket zunächst wieder geöffnet. Anschließend hat Mike die
Überschneidung mit T-67 bestätigt und den Abschluss beauftragt:
„Vermerke das bei T-64 und damit ist T-64 dann erledigt“.
Für T-64 ist kein weiterer Handgriff nötig.

Die Anforderung ist durch Mikes Ergänzung geklärt. Aktuell ist kein weiterer
Handgriff nötig. Oben auf der Börsenseite soll stehen, dass Plugins zusätzliche
Handelsplätze und MICs ergänzen können. Ein Link führt zur Autorenanleitung
auf GitHub. Die vorhandenen Autor-Vertragstests belegen diesen UI-Hinweis nicht.

Mikes Ergänzung im Wortlaut:

Unter "Einbindung" verstehe ich einen Hinweis im oberen Teil der Seit, dass durch neue Plugins
die Börsenplätze und die entsprechenden MICs erweitert werden können. Zu dem Hinweis gehört ein
Link auf GH zu dem plugin-authors.md-File

Die Umsetzung ist bereits in [T-67](../T-67-boersenabweichung-anzeigen.md)
beauftragt: unter der Einleitung der Börsenseite, auf Deutsch und Englisch,
auch auf schmalen Bildschirmen. Das Linkziel ist
[`docs/plugin-authors.md` auf GitHub](https://github.com/MikeMitterer/stockinfo/blob/master/docs/plugin-authors.md).
Prüfpunkt #5 ist an T-67 (`extras`) abgegeben. Es gibt dafür genau eine
Umsetzung und Prüfung; der fehlende Hinweis wird hier nicht als umgesetzt
oder bestanden gewertet. T-64 ist mit Mikes Entscheidung abgeschlossen.

## Umsetzung und technische Nachweise

### Gegenprüfung · Codex, 2026-09-09

Der zunächst daraus abgeleitete Ticketabschluss wurde nach Mikes Hinweis
zurückgenommen. Die folgenden Testergebnisse bleiben gültig, decken den
Plugin-Hinweis mit Autorenlink aber nicht ab.

Die gezielten Tests auf dem aktuellen Stand sind grün:
**12 UI-Tests, 8 Autoren-Vertragstests und 50 Beispieltests**. Geprüft sind
Darstellung in DE/EN, Suche, Neuladen, entfernte Pluginangaben, kompakte Ansicht
sowie gültige und ungültige Börsendeklarationen und das ausführbare Beispiel.

Im Repository ausgeführt:

```bash
npm --prefix dashboard test -- tests/components/ExchangesPanel.spec.ts tests/composables/useExchanges.spec.ts
env PYTHONPATH=plugin_api/src:plugin_api/examples/us-example/src .venv/bin/python -m pytest -q plugin_api/tests/test_exchange_contract.py plugin_api/examples/us-example/tests
```

Die geprüften Fälle bestehen. Der UI-Lauf meldet Sass-Deprecations sowie
Vue-/i18n-Hinweise aus der Testeinbettung; alle Tests bestehen. Browser, Build,
Gesamtsuite und Paketveröffentlichung wurden bei dieser Gegenprüfung nicht
erneut ausgeführt. Die Browsernachweise und Claudes unabhängige Freigabe
(`e427013`, Runde 1) stehen unten.

Die nachfolgende Matrix beschreibt den abgenommenen Stand vom 2026-09-08.
Spätere Änderungen an Kursquellenanzeige und Sammelcodes gehören zu T-21;
dessen laufendes Review wird durch diese Gegenprüfung nicht ersetzt.

**Doku-Abgleich:** `docs/plugin-authors.md`, Abschnitt „Declare venues and
coverage“, beschreibt Deklaration, Prüfung und Beispiel samt Checkout-Befehl.
Für die geprüften Fälle war dort keine Änderung nötig. Bei Umsetzung des
Hinweises werden Linkziel und Beschreibung erneut gegen die Anleitung geprüft.

### Scope-Vertrag · 2026-09-08

Ergebnis: Ein per REST neu gelieferter MIC erscheint ohne Frontendänderung
mit Herkunft und rollenbezogener Unterstützung; entfernte Angaben verschwinden
beim Neuladen. Drei fachliche Änderungen:

1. REST-Typen und Exchanges-Darstellung: MIC zuerst, Suche, Quellen/Rollen,
   getrennte Sammelcodes, Desktop-Tabelle und kompakte Liste, DE/EN.
   App-Suffix als eigene Spalte (Mikes UI-Nachtrag vom 2026-09-08).
2. Erneutes Laden mit Lade-/Fehlerzustand über die bestehende App-Anbindung.
3. Vorhandenen Autor-Vertrag um Deklarationsprüfung ergänzen und das
   US-Beispiel samt Paketanforderung und Anleitung nachziehen.

Erwartet: höchstens **10 Produktdateien** (ExchangesPanel, eine gemeinsame
Unterstützungsanzeige, AppDashboard, useExchanges, types, de/en, Autor-Harness,
US-Quelle und deren pyproject), **6 Test-/Dokudateien**, insgesamt
**800 manuelle Diff-Zeilen**. Keine neue Abhängigkeit, kein Backend-Endpunkt,
kein neues Schema, kein ISO-Import, keine Änderung bestehender Aliase oder
Arbeitsdaten. Der Autor-Harness verwendet die vorhandene öffentliche
Validierung; katalogabhängige Konflikte bleiben beim Host.

Reihenfolge: beobachtbare UI- und Vertragsfälle zunächst rot, Darstellung und
Harness implementieren, gezielte Gegenproben, normale Tests/Lint/Build,
Browserprüfung mit isolierten Daten in DE/EN und schmalem Fenster; danach Claude.

Abhängigkeit: [T-30](T-30-plugin-boersenauskunft.md), dessen REST-Auskunft
die einzige Datenquelle der Oberfläche ist. Der
[Gesamtentwurf](../../docs/superpowers/specs/2026-09-08-plugin-exchanges-design.md)
beschreibt das vereinbarte Verhalten.

- Exchanges zeigt MIC, Handelsplatz, Region und Unterstützung mit Quelle und
  Rolle. Nicht angegeben, inaktiv und bestandsabhängig bleiben unterscheidbar.
- App-Suffixe sind zusätzliche Information; Sammelcodes wie US stehen
  separat mit Mitgliedern. Keine Behauptung eines vollständigen ISO-Katalogs.
- Geerbte Autor-Vertragsprüfungen kontrollieren die neuen Deklarationen;
  ein ausführbares Beispiel demonstriert sie ohne Host-Interna.
- Tests für Quelle/Rolle und fehlende Deklaration sowie Browserlauf in DE/EN
  und schmalem Fenster. Kein eigenes Test-Subsystem.

| # | Nachweis | AI | Human |
|---|---|:--:|---|
| 1 | Browser mit echtem REST: XBUD, Plugin regional, Kurs und Tagesreihe korrekt; nach Profilwechsel und Neuladen verschwinden XBUD und regional. | ✅ | |
| 2 | Browser: archive inaktiv und bestandsabhängig; legacy nicht angegeben. Backend-Ausfall leert alte Angaben und zeigt übersetzten Fehler; Neuladen stellt die Ansicht wieder her. | ✅ | |
| 3 | DE/EN, 1440/390 px ohne horizontalen Überlauf. Suche nach Quelle und MIC, US samt Mitgliedern getrennt; Standard XBUD im Browser, Standard US im Komponententest. | ✅ | |
| 4 | 6 gezielte Harness-Fälle, 50 US-Beispieltests; ungültiger MIC, fremde Rolle, Umfang, Währung und Duplikat werden abgewiesen. | ✅ | |
| 5 | Unter der Einleitung der Börsenseite erklärt ein Hinweis, dass Plugins weitere Handelsplätze und MICs ergänzen können. Link öffnet `docs/plugin-authors.md` auf GitHub; Hinweis und Link sind in DE/EN auf Desktop und Mobil nutzbar. Am 2026-09-09 von Mike an T-67, Prüfpunkt `extras`, abgegeben; hier kein Umsetzungsnachweis. | ➖ | |

### Eigene Prüfung · Codex, 2026-09-08

```bash
make test ARGS="-m 'not integration'"
npm --prefix dashboard run build
npm --prefix dashboard test -- --run tests/components/ExchangesPanel.spec.ts tests/composables/useExchanges.spec.ts
PYTHONPATH=plugin_api/src:plugin_api/examples/us-example/src .venv/bin/python -m pytest -q plugin_api/examples/us-example/tests
.venv/bin/pytest -q plugin_api/tests/test_exchange_contract.py
```

Gesamtlauf: **1135 Backend** bestanden, 29 übersprungen, 8 Integrationstests
abgewählt; **321 Plugin-API**, 1 übersprungen; **50 Beispiel**;
**342 Dashboard in 51 Dateien**, einschließlich ESLint ohne Warnungen.
Build samt TypeScript-Prüfung grün. Bestehende Sass-Deprecation und Hinweis
zur Bundlegröße bleiben. Ruff und Bezeichnerinventare (Python-AST,
TS-Compiler-API) der berührten Dateien geprüft. Log:
`/tmp/stockinfo-t64-suite.log`, `/tmp/stockinfo-t64-build.log`.

Gegenproben, jeweils zurückgenommen: Inaktiv-Marke entfernt → 2 UI-Fälle rot;
Suchfilter entfernt → 1 UI-Fall rot; Harness-Validierung ausgelassen →
5 Vertragsfälle rot. Danach 6 gezielte UI-/Composable-Fälle und 56
Harness-/Beispielfälle grün. Logs: `/tmp/stockinfo-t64-mutant-{inactive,search,validation}.log`.

Browser: eigener normaler Uvicorn-Start auf `http://127.0.0.1:8896/#/exchanges`,
frischer temporärer Datenpfad
`/var/folders/1g/t8rp3mj157z2kfc6ch_t3nw40000gn/T/stockinfo-t64-browser.l40wspp5`.
Datei-Plugin mit regional (XBUD, Kurs/Markt, Tagesreihe/Bestand), archive
(nicht einsatzbereit) und legacy (ohne Deklaration), ohne Online-Anbieter.
Keine Requests oder Mutationen an der Arbeitsdatenbank. Gemessen:
`innerWidth == scrollWidth` bei 390 und 1440; kompakte Liste bzw. Tabelle.
EN über Sprachspeicher der isolierten Origin aktiviert. Nach Herausnehmen
von regional/archive aus dem Testprofil, Serverneustart und Klick auf Reload
waren XBUD und regional sowohl aus REST als auch aus der bestehenden UI weg.
Serverausfall: „Exchanges could not be loaded“, keine alte Tabelle;
nach Neustart und Reload wieder Daten. Browserkonsole vor dem absichtlich
erzeugten Netzfehler ohne Fehler. Automatische Tests decken zusätzlich
mehrere deklarierende Quellen, Standardsammelcode und Pluginentfernung ab.

Keine Online-/Docker-Prüfung behauptet. Die Autorenanleitung nennt den
Checkout-Befehl ausdrücklich, damit das noch unveröffentlichte API-Paket 0.3
keinen erfolgreichen Registry-Installationslauf vortäuscht.

UI-Nachtrag Mike: App-Suffix in eigener Spalte. Zwei DE/EN-Assertions waren
vorher rot und sind nach Trennung grün; 4 Komponententests, ESLint und Build
erneut bestanden. Browser: Spalten MIC, Handelsplatz, App-Suffix, Region,
Quellen/Rollen; Xetra hat `.DE` allein in der Suffixzelle. Bei 1024 und
390 px kein horizontaler Überlauf, mobil bleibt das Suffix beschriftet.
Zweiter UI-Nachtrag Mike: Mobil steht das vorhandene Suffix auf einer eigenen
Zeile, fett, größer und in Akzentfarbe. Browser bei 390 px: `.DE` mit 18 px
und Schriftgewicht 700; fehlende Suffixe bleiben normal beschriftet.
Komponententests, Build und ESLint nachgezogen und erneut grün.
Weiterer Farbauftrag Mike: MICs und vorhandene App-Suffixe generell in
Akzentfarbe, einschließlich der MIC-Mitglieder der Sammelcodes. Eigener
Browserlauf nach Build bei 1787/390 px: XETR und .DE verwenden beide den
Akzent-Token (`rgb(229, 94, 31)` im aktiven Theme), kein horizontaler Überlauf.
4 Komponententests und ESLint erneut grün. Die noch nicht begonnene
Review-Übergabe wurde dafür geordnet zurückgenommen; Runde 1 bleibt erhalten.

## Unabhängiges Review · Claude, 2026-09-08

Runde 1, Prüfstand `e427013`, Basis `f624670`: **approved**. Drei Mutanten
selbst wiederholt: Suchfilter 1 rot, Inaktiv-Marke 2 rot, Harness-Validierung
5 rot. 1135 Backend, 321 Plugin-API und 342 Dashboard selbst nachgemessen;
ESLint, TypeScript und Build grün. i18n-Inventar: 318 Schlüssel je Sprache,
keine Differenz, keine unbekannten Aufrufe. Python-/TS-Bezeichner geprüft.
10 Produktdateien, 646 manuelle Zeilen einschließlich Ticket bestätigt.

Browser, visuelle Nachträge und Profilwechsel bleiben ausschließlich Codex’
Belege; Claude nutzte den temporären Legacy-only-Server nicht. Keine
Online-, Docker- oder Release-Prüfung. Vollständiger Reviewtext im
STATUS-Verlauf von git. Technische Freigabe ersetzt Mikes Abschluss nicht.

## Herkunft

Claude entschied am 2026-09-08 im Scope-Checkpoint zu `d0e6ad0`: `split`.
T-30 behält Plugin/Core/REST; UI, Browserlauf, Autor-Harness und Beispiel
werden separat geliefert. Der Split selbst änderte die Priorität nicht;
Mikes anschließender UI-Auftrag priorisiert T-64 direkt nach T-30.
