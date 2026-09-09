# T-67 · Abweichende Börse sichtbar machen

Ein gefundenes Papier kann an einer anderen Börse notieren als aktuell
bevorzugt. Nach dem Absenden der Asset-Erfassung zeigt ein Dialog diesen
Unterschied vor dem Speichern:
etwa NYSE Arca (ARCX) gegenüber Xetra (XETR), mit beiden Währungen.

Die Meldung ist nach T-21 und T-65 umgesetzt; das unabhängige Review steht aus.
Codex implementiert, Claude prüft; die Kette steht in [STATUS.md](STATUS.md).
Aktuell ist keine zusätzliche Prüfung durch Mike angesetzt.

## Auftrag und Umfang

Abgetrennt durch Claudes Scope-Checkpoint zu T-21 am 2026-09-09, Prüfstand
8af898c, Entscheidung split. Keine Vertagung oder neue Produktentscheidung:
Mike hat den sichtbaren Vergleich bereits beauftragt. T-21 #2e verweist hierher.

**Nachsteuerung Mike, 2026-09-09:** Der Hinweis erscheint beim Absenden der
Erfassung, vor dem Speichern. Mike: „Der User kann dann entscheiden ob er das
Asset dennoch aufnehmen möchte oder den Vorgang abbricht. Entscheidet er sich
für die Aufnahmen dann ist das Thema erledigt“.
Die verworfene Listen-/Tooltipdarstellung ist entfernt.

**Scope-Vertrag (Claude: continue):** Beim Submit prüft der normale Aufnahmeweg
vor seiner Speicherung, ob das neue Listing vom bevorzugten MIC abweicht.
Dann erscheint ein Dialog mit tatsächlichem und bevorzugtem Handelsplatz,
MIC und Währung sowie „Dennoch aufnehmen“ / „Abbrechen“. Abbruch schreibt
nichts; Bestätigung nimmt das angezeigte oder inzwischen an der bevorzugten
Börse gefundene Listing auf. Danach kein
Listenhinweis und keine erneute Rückfrage beim Lesen oder Aktualisieren.
Gleicher MIC, pair, isin_only und bereits vorhandene Listings brauchen keine
Rückfrage. Fehlende/unbekannte Präferenz erzeugt keine erfundene Abweichung.

**Technischer Zuschnitt:** Der bestehende POST erhält eine
optionale angeforderte Börsenprüfung (`check_exchange`) und die bestätigte
Listing-Identität (`confirmed_listing`). Das Dashboard fordert die Prüfung
an; direkte API-Aufnahme bleibt eine direkte Aufnahme. Bei nötiger Entscheidung
antwortet er mit 202 und einer typisierten Bestätigungsanforderung statt einer
InstrumentSummary. Der gemeinsame Cache-/Speicherweg ruft vor dem ersten
Schreiben eine vom IntakeService gelieferte Prüfung mit dem fertigen Kurs auf.
So stehen die echte Währung und das Listing fest, ohne eine Zeile anzulegen.
Bei Bestätigung wird erneut geprüft und nur das bestätigte Listing akzeptiert;
eine geänderte Auflösung braucht eine neue Entscheidung, solange die Börse
weiterhin von der bevorzugten abweicht. Kein Draft-Repository,
Token-Speicher oder DB-Schema, kein Speichern mit anschließendem Zurücklöschen.
Bestehende Abdeckungs- und Identitätsprüfungen bleiben im selben Pfad.

**Zusätzlich von Mike ausdrücklich beauftragt, ohne weitere Tickets:**

- „API & Links“ ganz rechts in der Reihe der Einstellungs-Tabs.
- GitHub-Symbol mit Repo-Link direkt hinter „powered by MangoLila“, mit
  Trennpunkt davor auf breiten Ansichten und danach vor der Statusinfo auch mobil.
- Unter der Einleitung der Börsenseite erklären, dass weitere Handelsplätze
  über Plugins implementiert werden können; Link auf docs/plugin-authors.md.

Der Plugin-Hinweis übernimmt Prüfpunkt #5 aus
[T-64](solved/T-64-boersen-ui-und-autorennachweise.md). Mikes Ergänzung dort meint
Handelsplätze und MICs sowie den Link zur Anleitung auf GitHub. Mike hat T-64
am 2026-09-09 geschlossen und diesen Rest ausdrücklich hierher abgegeben.
Umsetzung und Nachweis stehen ausschließlich bei `extras`; keine Doppelprüfung.

**Scope-Checkpoint, Claude: continue, Prüfstand 11e77fa, Basis 9f13a7f:**
Freigegeben sind 18 Produktdateien, 8 Test-/Dokudateien und 1000 manuelle
Diff-Zeilen; die einmalige Budgeterweiterung ist damit verbraucht. Der
generierte OpenAPI-Snapshot zählt als Datei, nicht als manuelle Diff-Zeile. Drei
Fachänderungen: Aufnahmeentscheidung vor Speicherung, Dialog/Bestätigung,
Mikes drei kleine UI-Ergänzungen. Produktflächen: IntakeService, QuoteCache,
Aufnahme-Router, Container, Python-/TS-Modelle, useInstrumentActions,
AppDashboard, ConfirmExchangeDialog, DE/EN, useHashTab, StatusBar,
ExchangesPanel, config und LinksPanel. Tests: echte Aufnahme mit temporärer
DB, Composable und Dialog, bestehende StatusBar-Tests; T-67 und REST-Vertrag.
Neue Backend-/API-Fläche ersetzt die reine UI-Annahme; deshalb Scope-Prüfung.
Auflage vor Backendbeginn: `contract/core-contract.json` samt `core_version`
4.2.0 → 4.3.0 und neu erzeugtem `contract/openapi-core-snapshot.json` mitziehen,
dazu `tests/test_contract.py` und `tests/test_contract_openapi.py`. Die optionalen
Anfragefelder und die zusätzliche 202-Antwort sind eine additive Erweiterung
des geschlossenen Kernvertrags, daher Minor-Erhöhung. Keine neue Abhängigkeit,
Migration oder Änderung im Foundation-Repo.

## Verifikation

| # | Beobachtbares Ergebnis | AI |
|---|---|:--:|
| 2e | Nach Submit zeigt der Dialog ARCX bei XETR mit beiden MICs, Namen und echter Kurswährung vor dem Speichern, Desktop/Mobil DE/EN | ✅ |
| matching | Gleicher MIC, pair und isin_only lösen keine Abweichung aus | ✅ |
| missing | Keine erfundene Abweichung bei fehlendem Katalog/unbekannter Präferenz | ✅ |
| interaction | Vor Submit keine Rückfrage; Abbrechen schreibt nichts, Bestätigung speichert das bestätigte oder inzwischen bevorzugte Listing; danach keine erneute Warnung | ✅ |
| extras | Tab-Reihenfolge, GitHub-Link und Plugin-Autorenhinweis in DE/EN, Desktop/Mobil | ✅ |

Rote Tests am öffentlichen Aufnahme-Composable mit echtem API-Client und
kontrollierten Fetch-Antworten, negativer Mutant, Dashboard-Suite mit ESLint
und Build. Isolierter Browserlauf über das echte Formular mit temporären
Daten, beide Sprachen und Breiten. Danach unabhängiges Review über STATUS.md.


## Korrektur zu Runde 1 · Codex

Claude gab `9c1eb3d` mit zwei Befunden zurück. **B1 behoben:** Die bevorzugte
Börse beendet die Rückfrage auch dann, wenn zuvor ein anderes Listing
bestätigt wurde. Der Wechsel ARCX → XNYS bleibt 202 ohne Speicherung;
ARCX → XETR liefert 201 und speichert. Die Präferenz ist damit wie bei der
ersten Aufnahme maßgeblich. Test, REST-Anleitung und Vertragsaussage nennen
jetzt dieselbe Ausnahme. Die frühere Forderung nach einer Bestätigung auch
bei XETR im historischen Nachweis unten ist überholt.

**B2 behoben:** Beide Importblöcke sortiert. Der frühere Ruff-Lauf nutzte nur
die Default-Regeln und war kein Nachweis für Importsortierung/Quote-Stil.
Die betroffenen Dateien sind jetzt ausdrücklich mit `--select I,Q` geprüft.

Der korrigierte öffentliche Akzeptanztest wurde zuerst rot ausgeführt:
zwei XETR-Fälle scheiterten an 202 statt 201. Danach bestanden 108 gezielte Tests einschließlich aller 35
Abdeckungs-/Aufnahmefälle; 29 bestehende Vertragsfälle ausgelassen.
Ruff `--select I,Q` über alle acht berührten Python-Dateien grün. Logs:
`/tmp/t67-r2-red.log` und `/tmp/t67-r2-targeted.log`.
Runde 2: Claude hat `a8b3a18` freigegeben (`d21affe`); B1/B2 geschlossen.
Seine Selbstheilung korrigierte ausschließlich die Zeichensetzung im Vertrag.

## Nachweise aus Runde 1 · historischer Prüfstand 9c1eb3d

Die API unterbricht nur die angeforderte Neuaufnahme vor dem ersten Schreiben.
Abbrechen bleibt lokal. Bestätigung sendet die konkret angezeigte Identität;
eine veränderte Auflösung verlangt erneut eine Entscheidung, auch wenn das
neue Listing jetzt auf der bevorzugten Börse liegt. Vorhandene Listings,
Paare und reine ISIN-Instrumente werden ohne Rückfrage behandelt. Der Dialog
zeigt echte Kurswährung und getrennt die Katalogwährung der Präferenz.

Mike bestätigt am 2026-09-09: „Meldung ist OK“. Seine Nachträge zu den
Trennpunkten am GitHub-Icon und zur Du-Anrede sind umgesetzt. Das Inventar
des deutschen Katalogs ergab zwei Texte mit formeller Anrede: Sicherung vor
Datenumzug und Datenbankausfall. Beide korrigiert; neutrale Texte und „Sie“
als Bezug auf zuvor genannte Papiere bleiben unverändert.

- **2e / interaction:** Echte FastAPI-Aufnahme mit frischer temporärer DB in
  Datei- und gemischtem Profil. ISIN und MIC-Eingabe liefern zuerst 202 ohne
  gespeichertes Instrument, bestätigter POST 201, erneute Aufnahme 200.
  Geänderte Auflösung nach XNYS oder XETR bleibt bis Bestätigung ungespeichert.
- **matching / missing:** Gleicher MIC, Paar, reine ISIN sowie leere und
  unbekannte Präferenz geprüft; keine erfundene Abweichung.
- **Roter Ausgang:** sechs Backend- und sechs Composable-Fälle scheiterten am
  sofortigen Speichern beziehungsweise fehlender Entscheidung. Nach Ergänzung
  des Wechsels zur bevorzugten Börse zunächst zwei weitere rote Fälle.
- **Negativer Mutant:** Prüfung vor Speicherung entfernt; acht öffentliche
  Aufnahmefälle rot. Original wiederhergestellt, 108 gezielte Backend- und
  Vertragstests bestanden, 29 bestehende Vertragsfälle ausgelassen.
- **Gesamtlauf:** `make test` mit erlaubtem Netzwerkzugriff: 1177 Backend
  bestanden / 29 ausgelassen, 323 Plugin-API / 1 ausgelassen, 50 Beispieltests,
  378 Dashboardtests. Der erste Sandboxlauf scheiterte an acht Onlinefällen
  wegen fehlendem Netzwerk; er ist kein grüner Nachweis.
- **Browser:** Isolierter lokaler Server und Dateiprofil mit VTI/ARCX/CHF und
  SAP/XETR/EUR. Submit, Abbrechen, Bestätigen und anschließender Bestand geprüft;
  Fokus auf Abbrechen/Cancel. DE/EN, Desktop 1440 und Mobil 390 Pixel; kein
  horizontaler Überlauf. Repo-/Autorenlink, Tab-Reihenfolge und Trennpunkte
  sichtbar geprüft. Keine Betriebsdaten verwendet.
- **Statisch:** Python-AST- und TS-Compiler-Inventare gelesen; deutsche
  Bezeichner in den ohnehin berührten Vertragstests mechanisch umbenannt.
  Ruff, Dashboard-ESLint und Typecheck/Build erfolgreich.

Logs: `/tmp/t67-intake-red.log`, `/tmp/t67-actions-red.log`,
`/tmp/t67-changed-red.log`, `/tmp/t67-mutation.log`,
`/tmp/t67-final-targeted.log`, `/tmp/t67-full-tests-2.log`,
`/tmp/t67-final-dashboard.log`, `/tmp/t67-final-build.log`.

**Doku-Abgleich:** `docs/rest-core-contract.md` beschreibt den Aufnahmeablauf;
`contract/core-contract.json` und generierter OpenAPI-Ausschnitt enthalten die
additive Core-Version 4.3.0. Der Link auf `docs/plugin-authors.md` nutzt den
bestehenden Autorenvertrag; dort keine eigene Änderung. T-64s abgegebener
Plugin-Hinweis ist einmalig in `extras` nachgewiesen. Keine Migrationshinweise
für eine hypothetische Nutzerbasis und kein Docker-Langzeitnachweis.


**Umfang geplant/tatsächlich:** 3/3 Fachänderungen, 18/18 Produktdateien,
8/8 Test-/Dokudateien; 817/1000 manuelle Diff-Zeilen einschließlich Ticket.
Der generierte OpenAPI-Snapshot ist von der manuellen Zeilenzahl ausgenommen.
Die mechanischen englischen Bezeichner in den angefassten Vertragstests und
Mikes letzte UI-Text-/Trennpunktkorrekturen sind darin enthalten.

## Nachtrag Mike · ursprüngliche Eingabe und Fließtext, Runde 3

Nach erfolgreicher Runde 2 verlangt Mike die ursprüngliche Eingabe **fett**
in einem natürlich formulierten Fließtext. Der Dialog erklärt in DE/EN die
gefundene Börse und Kurswährung sowie die bevorzugte Börse. Mike hat den
Wortlaut selbst festgelegt: erst an der bevorzugten Börse nicht gefunden,
dann in einem neuen Absatz die Alternative. Zusätzliche technische Angaben
zu MICs und Katalogwährung entfallen nach dieser konkreten Textvorgabe.
Die Aufnahmeentscheidung und der Backend-Vertrag sind unverändert.

**Grund für Runde 3 / Rundenlimit:** neue UI-Vorgaben nach bereits erteilter
Freigabe, keine verschleppten Restbefunde. Bekannte offene Befunde: keine.
Offen ist Claudes unabhängige Prüfung dieses Nachtrags; bei einem Blocker
bleibt T-67 aktiv und T-25 wartet. Keine automatische Übergabe an Mike.

**Nachweise:** zwei Dialogfälle zunächst rot ohne Eingabe; anschließend
378 Dashboardtests einschließlich DE/EN-Dialog und ESLint grün. Typecheck und
Build grün. Logs: `/tmp/t67-input-red.log`, `/tmp/t67-user-text-tests.log`,
`/tmp/t67-user-text-build.log`. Browser mit isolierter DB: DE/Desktop 1440 mit
`US9229087690`, EN/Mobil 390 mit `vti.arcx`, Eingabe jeweils unverändert und
Schriftgewicht 700, kein horizontaler Überlauf. Mobiler Dialog 358 Pixel breit. Mikes finaler Wortlaut wurde anschließend
auf DE/Mobil als zwei Absätze mit fetter ISIN im Browser nachgeprüft.
Vor diesem reinen Textnachtrag auch Runde-2-Verhalten im Browser nachgestellt:
ARCX → XETR bestätigt direkt 201; ARCX → XNYS bleibt 202, Abbrechen speichert
nichts. GitHub-Trennpunkte, Tab-Reihenfolge und Plugin-Link erneut geprüft.

**Doku-Abgleich:** Aufnahmeabschnitt in `docs/rest-core-contract.md` nennt
Fließtext und fett hervorgehobene Eingabe. Keine neue API oder Fachlogik.

Umfang weiterhin 18 Produkt- und 8 Test-/Dokudateien; einschließlich dieses
Nachtrags 889/1000 manuelle Diff-Zeilen. TS-Compiler-Namensinventar englisch.
