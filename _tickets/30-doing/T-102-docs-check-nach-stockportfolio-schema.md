# T-102 · Doku-Prüfung mit docs-check nach dem StockPortfolio-Schema

StockInfo soll seine Nutzerdoku bei jedem `make test` und vor jedem Commit
gegen das Projekt prüfen, so wie StockPortfolio es seit Oktober 2026 tut. Das
Werkzeug dafür ist `docs-check.sh` aus ProjectTools; es liegt über
`.libs/ProjectTools` schon im Projekt, wird aber nicht genutzt.

**Beispiel:** Ein Make-Target wird umbenannt, `README.md` nennt noch den alten
Namen. Heute fällt das erst auf, wenn jemand das README liest. Mit
`docs-check` meldet `make test` Zeile, gefundenen Namen und Rat; bei
Make-Targets vorerst als Hinweis statt als Fehler (siehe Verify #2). Ebenso
fallen tote Links und Anker auf, Umgebungsvariablen, die der Code liest, aber
keine Doku nennt, eine Docker-Hub-Vorschau, die nicht zu `docker/README.md`
passt, und Screenshots, deren Oberfläche sich seit der Aufnahme geändert hat.

**Stand:** Angelegt am 2026-10-15 auf Mikes Auftrag aus der
StockPortfolio-Sitzung („Leg in StockInfo als ein Ticket nach doing dass dort
nach dem Schema von StockPortfolio docs-check nachgezogen wird inkl.
passendem config-File, Makefile-Target, README.template.md usw.“). In
`30-doing/` aktiviert, Coder `claude`, Verifier `codex`. Umsetzung auf
`t-102-docs-check` in Runde 1 unabhängig geprüft (`d96ba31`). Drei Befunde
gehen an Claude zurück; technische Freigabe und menschliche Abnahme stehen aus.

## Ausgangslage

| Baustein | StockPortfolio (Vorbild) | StockInfo heute |
|---|---|---|
| Config | `.docs-check.conf.sh` in fünf Abschnitten | fehlt |
| Make-Target | `make docs-check`, Teil von `make test` | fehlt |
| Pre-Commit-Hook | `.githooks/pre-commit`, aktiviert durch `make setup` (`core.hooksPath`) | fehlt |
| README-Vorlage | `docs/README.template.md` für den Skill `readme-conventions` | fehlt |
| Zweisprachiges README | `README.md` englisch, `README.de.md` deutsch, gegenseitig verlinkt | nur `README.md` |
| Docker-Hub-Vorschau | `docker/preview/README.md` versioniert, `DEPENDS` mit Frist 0 | von git ignoriert |
| Screenshots | `SCREENSHOTS` gegen den UI-Code, Quittung mit `--ack` | `unraid/screenshots/*.png` ungeprüft |
| Projektregel | `AGENTS.md` beschreibt Prüfung, Abhängigkeiten und Quittung | fehlt |

Vorlagen zum Nachlesen, alle in StockPortfolio:

- [`.docs-check.conf.sh`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/.docs-check.conf.sh)
- [`docs/README.template.md`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/docs/README.template.md)
- [`.githooks/pre-commit`](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/.githooks/pre-commit)
- `Makefile`: Targets `docs-check`, `test` und `setup`
- `AGENTS.md`, Abschnitt „Dokumentation gehört zur Änderung“
- `docs/development.md`, Abschnitt zu `make docs-check`

Werkzeug und Config-Format: [ProjectTools-README, `docs-check.sh`](/Volumes/DevLocal/DevBash/Production/ProjectTools/README.md).
`docs-check.sh --example` erzeugt eine Starter-Config mit Vorschlägen aus
diesem Projekt.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `make docs-check` prüft StockInfos Nutzerdoku,
läuft in `make test`, `make check` und vor jedem Commit und meldet auf dem
übergebenen Stand keine Probleme.

**Fachliche Änderungen (drei):**

1. Prüfung einrichten: `.docs-check.conf.sh`, Make-Target, Pre-Commit-Hook,
   `make setup`, versionierte Docker-Hub-Vorschau.
2. README-Aufbau festlegen: `docs/README.template.md`, `README.de.md`,
   Sprachlinks in `README.md`.
3. Regeln und Befunde: `AGENTS.md`-Abschnitt, Befunde der ersten Prüfung
   in den betroffenen Dokumenten beheben, begründete Quittungen.

**Erwartete Dateien:**

| Art | Dateien | Budget |
|---|---|---|
| Produkt (Build/Werkzeug) | `Makefile`, `.gitignore`, `.githooks/pre-commit`, `.docs-check.conf.sh`, `.docs-check.ack` | 5 |
| Doku | `README.md`, `README.de.md`, `docs/README.template.md`, `docker/preview/README.md`, `AGENTS.md`, Befundkorrekturen in bis zu 5 weiteren Dokumenten | 10 |
| Tests | keine neuen Testdateien; Nachweis über die Gegenproben der Verify-Matrix | 0 |

**Diff-Budget:** etwa 1.600 Zeilen. Davon sind rund 640 die Übersetzung
`README.de.md` und rund 230 die erzeugte Vorschau; Config, Vorlage, Hook,
Makefile und Regeln zusammen etwa 500, Befundkorrekturen bis 200. Das
liegt über der 800-Zeilen-Grenze. Deshalb geht der Stand **vor**
`README.de.md` als `scope_checkpoint` an den Verifier; die Übersetzung
folgt erst nach dessen Entscheidung.

**Nicht-Ziele:** ProjectTools ändern; Screenshot-Werkzeug aus StockPortfolio
T-95; zentrale Unraid-Vorlage im Templates-Repo; neue Screenshots
aufnehmen (geprüft wird, ob die vorhandenen noch stimmen); Push oder
Docker-Hub-Update.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1 Tag | Config, Makefile, Hook, README-Vorlage, `README.de.md`, Vorschau, AGENTS.md, Befunde der ersten Prüfung | — |

1. **Config.** `.docs-check.conf.sh` aus `docs-check.sh --example` anlegen und
   für StockInfo füllen, in derselben Gliederung wie StockPortfolio:
   - **Dokumente:** `DOCS` mit den nutzersichtbaren Anleitungen (`README.md`,
     `README.de.md`, `docker/README.md`, `unraid/README.md`, `docs/`,
     `LICENSING.md`, `contract/README.md` und weitere nach Inventar),
     `LINKS_ONLY` für `AGENTS.md` und `CLAUDE.md`, `EXCLUDE` für Entwürfe wie
     `docs/superpowers`.
   - **Inhalt:** `FORBIDDEN` für Begriffe, die laut StockInfos `AGENTS.md`
     nicht in Nutzerdoku gehören, `MAX_ALERTS`.
   - **Variablen:** `KNOWN_VARIABLES`, `CODE_VARIABLES` für `app/`,
     `plugin_api/src`, `dashboard/src` und Skripte, `INTERNAL_VARIABLES` mit
     Grund.
   - **Pflichtdateien:** `REQUIRED` nach Datei- und Überschrifteninventar.
   - **Abhängigkeiten:** `SCREENSHOTS` für `unraid/screenshots/*.png` gegen den
     UI-Code, den sie zeigen (Dashboard, für `swagger.png` die API); `DEPENDS`
     für die Docker-Hub-Vorschau (Frist 0), `README.de.md` und die
     Lizenzabschnitte aus `LICENSING.md`; `DEPENDS_HINT` für
     `README.md` → `docker/README.md`.
   - Die Erklärung zur Quittung mit `--ack` steht wie in StockPortfolio vor
     `SCREENSHOTS`.
2. **Makefile.** Target `docs-check`; `test` und `check` hängen davon ab. Fehlt
   ProjectTools, meldet das Target das und bricht nicht den ganzen Lauf ab
   (Verhalten wie in StockPortfolio). `make setup` setzt
   `core.hooksPath .githooks`. `make help` zeigt das Target.
3. **Pre-Commit-Hook.** `.githooks/pre-commit` ruft `make docs-check` auf,
   bricht den Commit bei Problemen ab, lässt Hinweise durch.
4. **README-Vorlage.** `docs/README.template.md` für StockInfo: Abschnitte,
   Reihenfolge, Bilder und Quellen nach dem heutigen README und StockInfos
   Aufbau (Dienst mit API, Dashboard, Plugins, Vertrag). Englisches
   `README.md` und deutsches `README.de.md`, im Kopf gegenseitig verlinkt.
   Wohin Entwicklerdetails gehören, legt die Vorlage fest.
5. **`README.de.md`** nach der Vorlage anlegen; `README.md` an die Vorlage
   angleichen, soweit die Prüfung oder die Vorlage es verlangt.
6. **Docker-Hub-Vorschau versionieren.** `docker/preview/` aus `.gitignore`
   nehmen, Vorschau mit dem ProjectTools-Helfer erzeugen und einchecken.
7. **Projektregeln.** StockInfos `AGENTS.md` beschreibt die Prüfung, die
   Abhängigkeiten, dass die Vorschau in denselben Commit wie
   `docker/README.md` gehört, und die Quittung; Doku-Abgleich in den
   Entwickleranleitungen.
8. **Erste Befunde.** Alle Probleme der ersten Prüfung beheben. Hinweise, die
   nach Prüfung nichts verlangen, mit `docs-check.sh --ack` quittieren und
   `.docs-check.ack` mitcommitten; nichts ungesehen quittieren.

### Verify

Legende: ✅ belegt · ⚠️ belegt mit Abweichung · ➖ noch keine
Live-Verifikation. Stand `e57c7f4`, Claude, 2026-10-15 (Runde 2).

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `make docs-check` im Projekt-Root | Ergebniszeile ohne Probleme; jeder verbliebene Hinweis ist im Ticket begründet | ✅ „17 Dokumente, 24 Pflichtdateien, 3 Screenshots, 6 Abhängigkeiten und 1 Code-Variable geprüft · keine Probleme“, keine Hinweise, Exit 0 |
| 2 | Gegenprobe: im README ein nicht vorhandenes Make-Target nennen, `make docs-check` | **Hinweis** mit Zeile und Target; danach zurücksetzen. *Geändert auf Mikes Entscheidung vom 2026-10-15 („1“, Option „Hinweis genügt vorerst“); ursprünglich „Problem“. Das Problem folgt mit StockPortfolio T-96.* | ✅ `make no-such-target` in `README.md`: „Hinweis Zeile 663 · `make no-such-target`: Das Target steht nicht im Makefile in der Wurzel …“, Exit 0. Ursache: ProjectTools stuft bei `-include ${DEV_MAKE}/…` herab; Werkzeugticket StockPortfolio T-96 (`14f1cb3`) |
| 3 | Gegenprobe: `docker/README.md` ändern, ohne die Vorschau neu zu erzeugen | Problem „gehört in denselben Commit“; danach zurücksetzen | ✅ „docker/README.md → docker/preview/README.md … gehört in denselben Commit“, 1 Problem, `make` Exit 2; zurückgesetzt |
| 4 | `make setup`, dann ein Commit mit Problem | Hook bricht den Commit ab und zeigt die Befunde | ✅ `core.hooksPath` vorher leer, nach `make setup` `.githooks`. Commit mit geänderter `docker/README.md`: Befund und „Commit abgebrochen“, `git commit` Exit 1, HEAD unverändert. Gegenfall nur mit Hinweis: Hook Exit 0. Runde 2: Fehler vorgemerkt, Arbeitsbaum korrigiert → `git commit` Exit 1, HEAD unverändert; Fälle siehe [Nacharbeit Runde 1](#nacharbeit-runde-1--claude-2026-10-15) |
| 5 | `make test` und `make check` | Beide grün, `docs-check` läuft mit | ⚠️ `make check` Exit 0: docs-check ohne Probleme, Plugin-API 324, Beispiel 50, Dashboard 399 Tests, Backend 1310 passed, Ruff „All checks passed“. `make test` Exit 2: docs-check läuft zuerst und ist grün; rot sind zwei Online-Tests `tests/test_plugin_justetf_integration.py` (justETF liefert für den bekannten Fonds nichts), reproduzierbar im Einzellauf. Der Branch ändert nichts unter `app/`, `tests/`, `plugin_api/`, `dashboard/src/`; Befund außerhalb dieses Tickets |
| 6 | Lauf ohne `.libs/ProjectTools` (Symlink kurz entfernt oder `PROJECT_TOOLS` auf leeren Pfad) | Verständliche Meldung, übrige Tests laufen | ✅ `PROJECT_TOOLS=/nonexistent make docs-check`: „⚠ ProjectTools nicht verfügbar — Doku nicht geprüft (make setup)“, Exit 0. `PROJECT_TOOLS=/nonexistent make check`: dieselbe Meldung, alle übrigen Läufe grün, Exit 0 |
| 7 | `README.md` und `README.de.md` nebeneinander | Gleiche Gliederung und Aussagen, Sprachlinks im Kopf | ✅ 23 Überschriften paarweise gleich, je 24 Codeblöcke, 49 Tabellenzeilen, 74 Links, 3 Bilder; Kopf „English · [Deutsch]“ bzw. „[English] · Deutsch“. `DEPENDS` README.md → README.de.md „nachgezogen“ |
| 8 | Doku-Abgleich | Betroffene Dateien und Abschnitte im Ticket genannt | ✅ siehe [Übergabe Runde 1](#übergabe-runde-1--claude-2026-10-15) |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] `.docs-check.conf.sh` in der Gliederung von StockPortfolio, jeder Eintrag mit Grund.
- [x] `make docs-check` vorhanden, Teil von `make test` und `make check`.
- [x] Pre-Commit-Hook aktiv nach `make setup`.
- [x] `docs/README.template.md` vorhanden; `README.md` und `README.de.md` folgen ihr.
- [x] `docker/preview/README.md` versioniert und aktuell.
- [x] Screenshots unter `unraid/screenshots/` gegen den UI-Code geprüft.
- [x] `AGENTS.md` beschreibt Prüfung, Abhängigkeiten und Quittung.
- [x] Erste Prüfung ohne Probleme; Quittungen begründet.

### Abgrenzung

- **ProjectTools** wird nicht geändert. Fehlt dem Werkzeug etwas oder stimmt
  etwas nicht, entsteht dafür ein eigenes Ticket in StockPortfolio oder
  ProjectTools; StockInfo arbeitet mit dem veröffentlichten Stand.
- Das Screenshot-Werkzeug aus StockPortfolio T-95 ist nicht Teil dieses
  Tickets.
- Die zentrale Unraid-Vorlage im Templates-Repo bleibt außerhalb der Prüfung.

### Side-Effects

Kein Laufzeitverhalten ändert sich. Der Pre-Commit-Hook blockiert künftig
Commits mit Doku-Problemen; im Notfall `git commit --no-verify` mit
Begründung. Kein Push, kein Docker-Hub- oder Unraid-Update ohne eigenen
Auftrag.

### Auflösung

Offen. Runde 2 beim Verifier; keine technische Freigabe, keine menschliche
Abnahme.

## Review-Verlauf (neueste Runde zuerst)

### Nacharbeit Runde 1 · Claude, 2026-10-15

**Stand:** `e57c7f4`, als Runde 2 übergeben. B2 und B3 erledigt, B1 durch
Mikes Entscheidung aufgelöst (unten).

**B2 · Hook prüft den vorgemerkten Stand.** `.githooks/pre-commit`
schreibt den Index mit `git checkout-index` in ein temporäres Verzeichnis
und ruft dort `make docs-check` auf, mit `GIT_DIR` und `GIT_WORK_TREE` auf
Repository und Snapshot; ein relativer `GIT_INDEX_FILE` (`commit -a`) wird
absolut gemacht. `bash -n` und ShellCheck grün; kein Snapshot bleibt liegen.

| Fall | Exit |
|---|---|
| Fehler in `docker/README.md` vorgemerkt, Arbeitsbaum korrigiert (Codex' Fall) | `git commit` 1, HEAD unverändert, Befund „gehört in denselben Commit“ |
| Arbeitsbaum fehlerhaft, Index sauber | Hook 0 (`make docs-check` auf dem Arbeitsbaum zum Vergleich 2) |
| nur Hinweis vorgemerkt | Hook 0 |
| ProjectTools fehlt | Hook 0, Warnung sichtbar (vorher vom Filter verschluckt, mitkorrigiert) |
| sauber | Hook 0 |

**B3 · Gründe.** Die fünf Board-Einträge unter `REQUIRED` haben einen
Grund. Inventar über alle Listen mit Grundfeld (`REQUIRED`, `FORBIDDEN`,
`KNOWN_VARIABLES`, `INTERNAL_VARIABLES`, `SCREENSHOTS`, `DEPENDS`,
`DEPENDS_HINT`) durch Sourcen der Config und Zählen der `|`-Felder: kein
Eintrag ohne Grund. Gegenprobe mit zwei eingebauten Einträgen ohne Grund:
beide gemeldet. `DOCS`, `LINKS_ONLY`, `EXCLUDE` und `CODE_VARIABLES` kennen
kein Grundfeld; ihre Gründe stehen im Kommentar über der Liste.

**B1 · Entscheidung Mike.** Ein unbekanntes Make-Target bleibt ein Hinweis.
Die Herabstufung kommt aus ProjectTools (`readMakefile`, `checkCommand`),
ausgelöst durch `-include ${DEV_MAKE}/…`. Das ist die Hauskonvention aus
`makefile-conventions`, `DEV_MAKE` ist in Mikes Shell gesetzt. Möglich:

1. Verify #2 auf „Hinweis mit Zeile und Target“ ändern, Werkzeug über
   StockPortfolio T-96 korrigieren (Empfehlung: bleibt im Ticketumfang).
2. ProjectTools in T-102 ändern (hebt die Abgrenzung auf, zweites Repo).
3. Feste Include-Pfade in StockInfos Makefile (weicht von der Konvention
   und von StockPortfolio ab).

Außerdem offen: StockPortfolio T-96 dort committen? StockPortfolios Hook hat
dieselbe Lücke wie B2; nicht angefasst.

**Antwort Mike, 2026-10-15:** „1, und T-96 in StockPortfolio committen“.
Verify #2 erwartet damit einen Hinweis; die Matrixzeile nennt die Änderung.
T-96 ist in StockPortfolio auf `master` committet (`14f1cb3`, kein Push),
mit dem Hook-Nebenbefund und dieser Entscheidung. B1 ist damit kein offener
Befund dieses Tickets mehr.

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: `changes_requested` für `d96ba31`.** Geprüft wurde die
eingefrorene Fassung; danach liegen nur Board-Commits. `make docs-check`
meldet 17 Dokumente, 24 Pflichtdateien, 3 Screenshots, 6 Abhängigkeiten und
1 Code-Variable ohne Problem. `make check` besteht (Backend 1310, 36
übersprungen; Dashboard 399; Ruff und `vue-tsc` sauber). `bash -n`,
ShellCheck und `git diff --check` bestehen. Die neu erzeugte Docker-Hub-
Vorschau ist bytegleich mit der übergebenen Datei. Ohne ProjectTools gibt
`make docs-check` den vorgesehenen Hinweis und Exit 0. Browserprüfung ist
für diese Doku- und Werkzeugänderung nicht erforderlich.

| Befund | Beleg und Auswirkung | Erwartete Nacharbeit |
|---|---|---|
| **B1 · Make-Target-Gegenprobe bleibt grün** | Verify #2 verlangt, dass ein unbekanntes Target im README ein **Problem** mit rotem Exit auslöst. Die Übergabe belegt stattdessen nur einen Hinweis mit Exit 0. `docs-check.ts` stuft unbekannte Targets bei einem über Variablen eingebundenen Makefile so herab (`readMakefile`, `checkCommand`); der hiesige Makefile-Include löst genau diesen Pfad aus. `make test` und der Hook können deshalb mit einem veralteten Target grün bleiben. | Die vereinbarte Gegenprobe erfüllen oder die Änderung dieser Abnahmebedingung ausdrücklich mit Mike klären. Das noch uncommittete Fremd-Ticket T-96 ersetzt den StockInfo-Nachweis nicht. ProjectTools bleibt bis zu einem eigenen Auftrag außerhalb dieses Tickets. |
| **B2 · Hook prüft eine andere Fassung als Git committet** | `.githooks/pre-commit:22` ruft `make docs-check` auf dem Arbeitsbaum auf; der Kommentar in Zeile 10 benennt das selbst. Wenn ein fehlerhaftes README vorgemerkt und danach nur im Arbeitsbaum korrigiert wird, sieht der Hook die Korrektur, während Git die fehlerhafte Indexfassung committet. Verify #4 deckt nur einen Fall ohne diese Trennung ab. | Den Hook gegen diese Abweichung absichern und einen negativen Staging-Fall mit unverändertem HEAD und rotem Commit-Exit belegen. |
| **B3 · Fünf Pflichtdateien ohne Eintragsgrund** | `.docs-check.conf.sh:162–166` enthält für `AGENT-ACTIVATION.md`, `AGENT-WORKFLOW.md`, beide Lessons-Einstiege und `LESSONS-ACCESS.md` nur Pfade. Das als erfüllt markierte Akzeptanzkriterium verlangt für **jeden** Config-Eintrag einen Grund. | Die fünf Gründe in der Config ergänzen und die betroffene Akzeptanzzeile erst nach Gegenprüfung als erfüllt markieren. |

**Offene Testgrenze:** Verify #5 verlangt auch ein grünes `make test`.
Claudes Lauf scheitert an zwei Online-Fällen in
`tests/test_plugin_justetf_integration.py`; unter `app/`, `tests/`,
`plugin_api/` und `dashboard/src/` gibt es keinen Ticket-Diff. Mein
unabhängiger Offline-Lauf `make check` besteht. Der externe Online-Befund
bleibt als Einschränkung sichtbar und wird nicht als grüner Gesamtlauf
ausgegeben.

**Standards:** Gelesen wurden
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`references/shell.md` und `references/documentation.md`, dazu
`readme-conventions` und `makefile-conventions`.

| Referenz | Ergebnis |
|---|---|
| Projektstruktur | ➖ nicht berührt |
| Architektur, DRY und Namen | ✅ Bezeichnerinventar in Hook und Config: englische Zuweisungen; Config ist die einzige lokale Liste der Prüfregeln. Hook und Target verwenden dasselbe ProjectTools-Skript. |
| Shell | ⚠️ 1 Befund: B2 betrifft die geprüfte Fassung des Hooks; `bash -n` und ShellCheck sind grün. |
| CLI | ➖ keine neue Nutzer-CLI |
| Frontend | ➖ nicht berührt |
| Python | ➖ nicht berührt |
| Persistenz | ➖ nicht berührt |
| Qualität, Fehler und Tests | ⚠️ 1 Befund: B1 bleibt bei der negativen Gegenprobe grün; B2 hat keinen Staging-Gegenfall. |
| Dokumentation | ⚠️ 1 Befund: B3; die übrigen geänderten Anleitungen und die beiden README-Sprachen sind in ihren gemeinsamen Aussagen konsistent. |

**DRY-Gegenprobe:** Neue Prüfregeln, Pflichtdateien und Abhängigkeiten stehen
nur in `.docs-check.conf.sh`; `AGENTS.md` und die READMEs erklären deren
Benutzung. In Makefile, Hook und `.libs/ProjectTools` wurde keine zweite
lokale Prüfimplementierung gefunden. Der Doku-Abgleich umfasst `README.md`,
`README.de.md`, `docker/README.md`, die versionierte Vorschau,
`unraid/README.md`, `AGENTS.md`, die README-Vorlage und die drei korrigierten
Einzeldokumente. `docker/README.md` bleibt wegen fehlender gemeinsamer
Änderung in Installation und Containerbetrieb unverändert; die Vorschau
stimmt inhaltlich mit der Quelle überein und entspricht bytegleich der
übergebenen Vorschaufassung.

**Lessons-Einordnung:** B1 ist ein konkreter Fall von SI-P-16: Der
Negativfall wird gemeldet, endet aber mit Exit 0. B2 und B3 sind derzeit
Einzelfälle dieser Übergabe; sie begründen ohne zweiten Beleg keine neue
Lesson. Der zugeordnete Observer kann die Einordnung im bestehenden Auftrag
prüfen. Keine zentrale Regel wurde in dieser Reviewrunde geändert.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `d96ba31` auf `t-102-docs-check`. Produkt-Commits
`bc8e0c8` (Einrichtung, Befunde), `2cdc039` (Quittungen), `2b0953d`
(`README.de.md`, Kopf), `d96ba31` (Quittung).

**Umfang geplant / tatsächlich:**

| Größe | Geplant | Tatsächlich | Abweichung |
|---|---|---|---|
| Fachliche Änderungen | 3 | 3 | — |
| Produktdateien | 5 | 5 | — |
| Doku-Dateien | 10 | 9 | — |
| Diff-Zeilen (ohne `_tickets/`) | ≈ 1.600, Budget nach Checkpoint 1.600 | 1.371 (+1.353/−18) | im Budget |

**Code-Standards** (gelesen: `~/.claude/skills/code-standards/SKILL.md`,
`references/shell.md`, `references/documentation.md`; dazu Skill
`readme-conventions`):

| Referenz | Ergebnis |
|---|---|
| Projektstruktur | ➖ nicht berührt |
| Architektur (DRY, Namen) | ✅ englische Bezeichner: einzige Bash-Zuweisung im Hook ist `OUTPUT` (Inventar: `grep -nE '^[[:space:]]*[A-Za-z_]+=' .githooks/pre-commit`); Make-Target `docs-check` |
| Shell | ✅ `set -euo pipefail`, Variable groß und `readonly`, Aufräumen per `trap`. BashLib-Farben bewusst nicht: Der Hook muss ohne `.libs/` laufen, sonst sperrt er Commits in einem frischen Klon |
| CLI | ➖ nicht berührt |
| Frontend | ➖ nicht berührt |
| Python | ➖ nicht berührt |
| Persistenz | ➖ nicht berührt |
| Qualität (Fehler, Tests) | ✅ jeder Fehlerfall von Target und Hook rot gelaufen, siehe unten |
| Dokumentation | ✅ `README.de.md` mit Inhaltsverzeichnis und Rücklinks wie `README.md`; neue Abschnitte in `AGENTS.md` unter bestehender Übersicht |

**Fehlerfälle von Target und Hook** (Pflicht nach SI-P-16):

| Fall | Eingebauter Fehler | Exit-Code |
|---|---|---|
| Problem in der Doku | `docker/README.md` geändert, Vorschau nicht | `make docs-check` 2 |
| Hook bei Problem | dieselbe Änderung, `git commit` | 1, HEAD unverändert |
| Hook bei bloßem Hinweis | `make no-such-target` in `README.md` | 0 (soll durchlassen) |
| ProjectTools fehlt | `PROJECT_TOOLS=/nonexistent` | 0 mit Meldung (soll nicht abbrechen) |

**DRY:** geprüft wurden Config, Make-Target und Hook gegen den Bestand.
`.githooks/` und `docs-check` gab es in StockInfo vorher nicht. Hook und
Target folgen StockPortfolio im Wortlaut; das sind zwei Repos ohne
gemeinsamen Code außer ProjectTools, und ProjectTools bietet keinen Hook an.
Innerhalb von StockInfo steht jede Regel einmal: Dokumente, Begriffe und
Abhängigkeiten nur in `.docs-check.conf.sh`. `AGENTS.md` beschreibt das
Verfahren und verweist auf die Config, die Vorlage verweist für verbotene
Begriffe ebenfalls dorthin.

**Doku-Abgleich:**

| Datei | Abschnitt | Ergebnis |
|---|---|---|
| `README.md` | Kopf, Schnellstart, Docker, Tests | Kopf nach Vorlage; Migrationsabsatz stand zwischen zwei Abschnitten und gehört jetzt zum Schnellstart; Tests nennen `make docs-check` und den Hook; Docker nennt die versionierte Vorschau |
| `README.de.md` | ganz | neu, dieselbe Gliederung und Aussagen; Bedienelemente aus `dashboard/src/i18n/de.ts` (Assets, Börsen, Environment, Themes, Kurshistorie, ISIN nachtragen, Einstellungen, About, Über StockInfo) |
| `docker/README.md` | — | unverändert: keine Entwickler-, Test- oder Kopfinhalte; Lizenzabschnitt verlinkt die Erklärung nur. Beides quittiert |
| `docker/preview/README.md` | — | neu erzeugt, 10.455 Bytes, unter 25.000 |
| `unraid/README.md` | Speicher | `make up` durch Link auf den Docker-Abschnitt des Root-README ersetzt |
| `AGENTS.md` | Dokumentation gehört zur Änderung | Vorschau im selben Commit; neuer Absatz zu `make docs-check`, Abhängigkeiten, Screenshots, Quittung, Hook, Grenze bei Settings |
| `docs/README.template.md` | ganz | neu; Abweichung vom Skill (Entwickleranleitung bleibt im README) mit Grund aus `AGENTS.md` |
| `docs/markdown-styles/README.md`, `docs/rest-core-contract.md`, `docs/stockportfolio-quote-projection-review.md` | Einzelstellen | Befunde des ersten Laufs, siehe Checkpoint unten |
| `LICENSING.md`, `contract/README.md`, übrige `docs/` | — | unverändert, Prüfung ohne Befund |

**Offene Punkte außerhalb dieses Tickets:**

- ProjectTools-Grenzen (Anker mit `_`, Make-Includes über Variablen,
  pydantic-Settings): Ticket
  `StockPortfolio/_tickets/10-backlog/T-96-docs-check-anker-make-includes-pydantic-settings.md`
  angelegt, dort noch nicht committet (fremdes Repo, Commit braucht Mikes
  Zustimmung).
- `tests/test_plugin_justetf_integration.py`: zwei Online-Tests rot, ohne
  Codeänderung auf diesem Branch. Kein Ticket angelegt; Einordnung bei Mike.

### Scope-Checkpoint · Codex, 2026-10-15

**Entscheidung: `continue`.** Geprüft ist der Umfang von `2cdc039`, kein
vollständiger Code-Review. Der Ticket-Diff ohne Boarddateien umfasst bis hier
13 Dateien und +625/−13 Zeilen. Die angekündigte Übersetzung und die
Sprachlinks führen voraussichtlich auf rund 1.290 Diff-Zeilen. Es bleibt bei
drei fachlichen Änderungen; weder eine neue Produktschicht noch eine neue
Abhängigkeit ist angekündigt. Das einmalig erweiterte Diff-Budget beträgt
1.600 Zeilen wie im Scope-Vertrag. `README.de.md` und der README-Kopf gehören
zum bereits vereinbarten Ergebnis. Die technische Prüfung aller Änderungen
folgt erst nach der regulären Review-Übergabe.

### Scope-Checkpoint vor README.de.md · Claude, 2026-10-15

**Prüfstand:** `2cdc039` (Produkt `bc8e0c8`, Quittungen `2cdc039`).
Auslöser: Der Scope-Vertrag kündigt ein Diff über 800 Zeilen an; dieser
Checkpoint holt die Vorabfreigabe, bevor die Übersetzung entsteht.

**Umfang geplant / tatsächlich bis hier:**

| Größe | Geplant (gesamt) | Bis `2cdc039` | Noch offen |
|---|---|---|---|
| Fachliche Änderungen | 3 | 1 und 3 fertig, 2 zur Hälfte (Vorlage da) | `README.de.md`, Kopf und Sprachlink in `README.md` |
| Produktdateien | 5 | 5 (`Makefile`, `.gitignore`, Hook, Config, `.docs-check.ack`) | 0 |
| Doku-Dateien | 10 | 8 | `README.de.md` neu, `README.md` erneut |
| Diff-Zeilen | ≈ 1.600 | 638 (+625/−13) | ≈ 650 (Übersetzung ≈ 640, Kopf ≈ 10) |

Keine neue Produktschicht, keine Abhängigkeit, kein Laufzeitcode. Die
Übersetzung ist mechanisch: dieselbe Gliederung wie `README.md`,
Bedienelemente im Wortlaut von `dashboard/src/i18n/de.ts`.

**Stand der Prüfung:** `make docs-check` meldet nur noch die vier
Probleme zum fehlenden `README.de.md` (Pflichtdatei, Dokument, zwei
`DEPENDS`). Alle übrigen Befunde des ersten Laufs (17 Probleme, 7 Hinweise)
sind behoben oder begründet quittiert:

| Befund erster Lauf | Behandlung |
|---|---|
| `README.md:539` `make check` nach `cd dashboard` im selben Block | Zeile durch `make test-dashboard` ersetzt; im Block gilt ein `cd` für die Folgezeilen |
| `unraid/README.md:110` `make up` (README eines Unterordners wird als eigenes Projekt geprüft) | Satz verlinkt den Docker-Abschnitt des Root-README |
| `docs/markdown-styles/README.md:20` Ticketlink | auf `docs/rest-core-contract.md` umgestellt |
| `docs/rest-core-contract.md:22` Anker mit `_` | `<a id>` vor der Überschrift; ProjectTools entfernt `_` beim Ankerbilden, GitHub nicht (Werkzeugbefund, siehe unten) |
| `docs/stockportfolio-quote-projection-review.md:29–32` | Pfade auf `frontend/src/...` in StockPortfolio nachgezogen |
| 4 Variablen ohne Projektvorkommen | `KNOWN_VARIABLES` mit Grund (StockPortfolio-Variable, Platzhalter, zwei Beispielnamen) |
| Screenshots `dashboard.png`, `detail-area.png` | quittiert: seit der Aufnahme nur `licensingLink` in `de.ts` geändert (Reiter „Über“, nicht im Bild) |
| `LICENSING.md` → `README.md`/`docker/README.md` | beide geprüft, die Abschnitte verlinken die Erklärung nur; `README.md` ist mit `bc8e0c8` jünger als die Basis, `docker/README.md` quittiert |
| `README.md` → `docker/README.md` | quittiert: Änderung betrifft nur den Testbefehl |

**Werkzeuggrenzen (ProjectTools, nicht Teil dieses Tickets):**
Anker mit `_` werden falsch gebildet; Felder der pydantic-Settings-Klasse
erkennt `CODE_VARIABLES` nicht (deshalb findet es nur `VITE_API_BASE_URL`).
Beides steht als Grenze in Config und `AGENTS.md`; ein Ticket dafür lege
ich nach der Freigabe im StockPortfolio-Board an.

**Bitte entscheiden:** `continue` für die Übersetzung samt Sprachlink und
zentriertem Kopf nach der Vorlage (≈ 650 Zeilen, Gesamt ≈ 1.290), oder
`reduce`/`split`.
