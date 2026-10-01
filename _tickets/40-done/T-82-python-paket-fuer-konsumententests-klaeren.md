# T-82 · Python-Paket für StockPortfolio-Tests einbinden

StockPortfolios lokales Skript `scripts/stockinfo-test-server.py` wird mit
StockInfos Python-Umgebung gestartet. Für die einheitliche CLI-Hilfe und
Farbausgabe soll es `projecttools.ui.colors` aus dem paketierbaren
ProjectTools-Python-Teil nutzen können. Diese Bibliothek ist derzeit nicht
als Abhängigkeit der StockInfo-Umgebung deklariert. Ein bloßer
`sys.path`-Eingriff oder ein absoluter Rechnerpfad würde den Aufruf an
eine lokale Verzeichnisstruktur binden.

**Auswirkung für den Konsumenten:** Ohne geklärten Installationsweg kann
StockPortfolio das Skript nicht zuverlässig auf anderen Rechnern mit der
gemeinsamen CLI-Darstellung starten. Der bestehende Teststack und StockInfos
Produkt-API sollen davon unberührt bleiben.

**Stand:** Aktiviert von Mike am 2026-10-01, Coder `claude`, Verifier
`codex`. Die Paketstruktur liegt bereits in ProjectTools
(`mmit-projecttools`, `pyproject.toml` im Repo-Root).

**Vorgabe Mike, 2026-10-01:** „Zu T-82 kannst du dir das Makefile in
StockPortfolio ansehen - das erstellt mit setup das .venv. requirements.txt
kannst du im ProjectRoot ablegen - im Prizip gleich wie bei StockPortfolio.
Schau dass das Projekt eigenständig bleibt. Zieh nicht selbständig
iregendwelche Querverweise zu StockPortfolio“.

## Entscheidung

`make setup` richtet die Entwicklungsumgebung ein: `.libs`-Links per
`scripts/setup-libs.sh` (Hausvorlage), `.venv` mit Python 3.11+, Pakete
aus `requirements-dev.txt`, Dashboard-Pakete per `npm ci`. Das Paket
kommt als `-e ./.libs/ProjectTools` in **`requirements-dev.txt`** im
Projekt-Root.

Warum nicht `requirements.txt`: In StockInfo beschreibt diese Datei die
Laufzeit der App. Der Docker-Build installiert sie, und im Image gibt es
`.libs/` nicht; der Build bräche ab. `requirements-dev.txt` bindet
`requirements.txt` ohnehin ein und ist die Datei, die die Anleitung für die
Entwicklungsumgebung schon nennt.

Grenze: Der Weg setzt die ProjectTools-Quelle auf dem Rechner voraus
(`PROJECT_TOOLS` oder vorhandener Link). Ohne sie bricht `make setup` mit
der Meldung von `setup-libs.sh` ab. Produkt, API und Image bleiben unberührt.

## Scope-Vertrag

- **Ergebnis:** Nach `make setup` in einem frischen Checkout ist
  `projecttools.ui.colors` mit `.venv/bin/python` importierbar, ohne
  Rechnerpfad und ohne `sys.path`-Eingriff.
- **Fachliche Änderungen (2):** `setup`-Target samt `scripts/setup-libs.sh`;
  ProjectTools-Eintrag in `requirements-dev.txt`.
- **Dateien:** `Makefile`, `requirements-dev.txt`, `scripts/setup-libs.sh`
  (neu), `README.md` (Quick start); dieses Ticket.
- **Budget:** 4 Projektdateien, 1 Ticketdatei, 250 Diff-Zeilen.
- **Nicht-Ziele:** keine Änderung an App, Image, `requirements.txt`, Tests
  der App; keine Verweise auf andere Projekte in Code oder Anleitungen;
  kein Eingriff in fremde venvs.

## Klärung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Python-Umgebung für den lokalen StockPortfolio-Testaufruf | — |

Prüfen, ob StockInfos bestehende Projekt-venv die richtige Umgebung für
dieses Konsumentenwerkzeug ist und wie das ProjectTools-Paket dort
reproduzierbar verfügbar wird. Dabei den lokalen Entwicklungsweg, frische
Checkouts und den Aufruf aus StockPortfolio betrachten. Einen anderen
Installationsweg nur wählen, wenn er den gleichen maschinenunabhängigen
Aufruf ermöglicht. Die Entscheidung und ihre Grenze im Ticket begründen.

### Verify

Legende: ✅ bestätigt, ◑ teilweise, ⚠️ Nacharbeit, ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | In einer frischen StockInfo-Umgebung den dokumentierten Installationsweg ausführen | `projecttools.ui.colors` ist ohne absoluten Rechnerpfad und ohne `sys.path`-Änderung importierbar | ✅ |
| 2 | StockPortfolios Testskript mit der vorgesehenen Python-Umgebung und `--help` starten | Hilfe erscheint ohne laufenden Dienst und ohne Seiteneffekte | ✅ |
| 3 | Den Teststack nach der gewählten Einbindung starten, Status prüfen und stoppen | StockInfo und StockPortfolio bleiben über den dokumentierten Aufruf erreichbar; fremde Prozesse und Daten bleiben unangetastet | ✅ |
| 4 | StockInfos bestehende Tests und die betroffenen Entwickleranleitungen prüfen | Keine Regression; Installationsschritte und Zuständigkeit sind nachvollziehbar | ◑ |

**Belege (Claude, 2026-10-01):**

1. Lokaler Link `.libs/ProjectTools` entfernt (nicht versioniert), dann
   `make setup VENV=<scratchpad>/fresh-venv`. `setup-libs.sh` legt den Link
   neu an und meldet „✓ Setup fertig“; `import projecttools.ui.colors` mit
   `mmit-projecttools 0.1.0` gelingt. Der Pfad in `sys.path` stammt aus pips
   editierbarer Installation, nicht aus Projektcode. `make setup` im Root
   lief ebenfalls zweimal hintereinander durch (idempotent).
2. `<StockInfo>/.venv/bin/python scripts/stockinfo-test-server.py --help`
   im Konsumentenprojekt: Hilfe mit gemeinsamem Theme, Exit 0, kein Dienst
   gestartet; `cli_theme.has_theme()` ist `True`.
3. Dasselbe Skript mit `--run --port 18083` (StockInfo-Testserver, temporäre
   DB): `/ready` 200, `--status` nennt die eigene PID, `--stop` beendet nur
   diese; danach keine Antwort mehr auf 18083. Mikes laufendes Backend auf
   Port 8000 blieb unberührt. `--stack` lief nicht; er gehört zum
   Konsumentenprojekt und verwendet dessen eigene Umgebung.
4. `make test`: Backend 1245 bestanden / 35 übersprungen, Plugin-API 323,
   Beispiel-Plugin 50, Dashboard 52 Dateien / 389 Tests samt ESLint;
   `npm run build` erfolgreich, auch nach `npm ci` mit den von npm
   gemeldeten blockierten Installationsskripten. `shellcheck` ohne Befund;
   `setup-libs.sh` ohne Argument und mit `--info` Exit 0.

**Hausvorlage veraltet:** `makefile-conventions/setup-libs.sh` prüft noch
`ProjectTools/src/python/colors.py`. Seit dem Paketumbau liegt die Datei
unter `src/python/projecttools/ui/colors.py`. StockInfos Kopie ist
korrigiert. Auf Mikes Auftrag ist auch die Vorlage korrigiert: PersonalSkills
`master` `39cb1ae` (Fast-Forward, Tests 24/24). Im installierten Skill wirkt
sie, sobald dessen Checkout `master` übernimmt; er steht derzeit auf einem
anderen Ticketbranch. Die Funktionskommentare aus Codex' Selbstheilung
(`d6c5d3b`, `a3bd3b1`) stehen nur in StockInfos Kopie, nicht in der Vorlage.

### Akzeptanzkriterien

- [x] Der für StockInfo gewählte Installationsweg ist begründet und reproduzierbar.
- [x] StockPortfolios Skript kann die gemeinsame CLI-Darstellung über den Paketimport nutzen, ohne Rechnerpfad im Code.
- [x] Hilfe und Teststack funktionieren auf dem dokumentierten Entwicklungsweg.
- [x] Betroffene Anleitungen in beiden Repositories sind auf Konsistenz geprüft; nötige Anpassungen sind dokumentiert (StockPortfolio T-75 bleibt offen).

### Doku-Abgleich

- `README.md` → Requirements und Quick start: `make setup` statt der
  Handbefehle; `.libs`, Umgebungsvariablen, `PYTHON_BOOTSTRAP` und der
  Hinweis, dass das Image nichts davon braucht.
- `make hints`: Zeile „Erster Start“ (`make setup` → Konfiguration
  anlegen → `make dev`).
- `docker/README.md` und `unraid/README.md`: unverändert; sie beschreiben
  den Container, der weder `.libs` noch `requirements-dev.txt` verwendet.
- Keine neuen Verweise auf andere Projekte in Code oder Anleitungen
  (Vorgabe Mike). Die Anleitung des Konsumentenprojekts nennt bereits
  StockInfos `.venv/bin/python`; dort ist nichts zu ändern.

### Side-Effects

Kein Eingriff in StockInfos Kurs- oder API-Vertrag. Keine globale
Python-Installation und keine automatische Änderung fremder Projekt-venvs.
ProjectTools bleibt ein eigenes Repository mit eigenem Commit.

### Auflösung

Umgesetzt auf `t-82-python-paket-konsumententests`; Übergabe an Verifier
`codex`.

**B1 aus Runde 1 · Entscheidung Mike, 2026-10-01:** Die veraltete Aussage
steht in StockPortfolios `README.md` (Zeile 426–427), nicht in StockInfo.
StockPortfolio war im Review von T-72; ein Commit dort hätte den geprüften
Stand verschoben. Mike wählte: als StockPortfolio-Ticket führen. Angelegt als
`StockPortfolio/_tickets/10-backlog/T-75-stockinfo-einzelserver-hilfe-doku.md`
mit dem Textvorschlag; die Datei ist dort bewusst nicht committet, weil der
Review noch läuft. StockInfos Anleitungen sind unverändert stimmig; Runde 2
enthält keinen Produktedit.

**Abschluss · Mike, 2026-10-01:** „T-82 ist erledigt, push es“. Codex hat
Runde 2 freigegeben (`2a3cc0c`), lokal nach `master` gemergt (`e90766d`),
auf Mikes Anweisung gepusht. Die README-Zeile bearbeitet StockPortfolio T-75.

### Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `changes_requested`.** Die Übergabe `fa5b240` wurde gegen
`849454f` unabhängig geprüft. Dazwischen liegt nur die T-86-Messnotiz
`ff21c5c`. Der finale geprüfte T-82-Stand enthält die verhaltensneutrale
Selbstheilung `a3bd3b1`: Vier Bash-Funktionskommentare nennen nun Parameter
und Rückgabewert; das Root-README nennt Node.js samt npm zutreffend als
Voraussetzung für `make setup`. Produktlogik, Abhängigkeiten, Testdaten und
Erwartungen wurden im Review nicht geändert.

**Verify #1 ✅:** `make setup VENV=/private/tmp/t82-verifier.LkC7C7/.venv`
legte eine frische Python-3.11-venv an, installierte die deklarierten Pakete
und `npm ci` und lief beim zweiten Aufruf erneut erfolgreich. Aus dieser
venv importiert `projecttools.ui.colors` aus der verlinkten ProjectTools-Quelle;
`mmit-projecttools` meldet Version 0.1.0. Kein absoluter Rechnerpfad und kein
`sys.path`-Eingriff stehen in den geänderten Projektdateien.

**Verify #2 ✅:** Der StockPortfolio-Einzelserver zeigte mit der frischen
StockInfo-venv bei `--help` die gemeinsame CLI-Hilfe und startete keinen
Dienst. **Verify #3 ✅:** Der Einzelserver verwendete eine temporäre Datenbank;
`/ready` antwortete mit 200, `--status` erkannte die eigene PID und `--stop`
beendete sie. Zusätzlich startete StockPortfolios eigener `--stack`-Weg mit
StockInfos Projekt-venv StockInfo auf Port 18084, die Konto-API auf 8080 und
das Frontend auf 5175. `--run` und `--status` bestätigten Endpunkte und CORS;
`--stop` entfernte nur die eigenen Prozesse und temporären Kontodaten.

**Verify #4 ⚠️:** `make test` bestand mit 1245 Backend-Tests (35 übersprungen),
323 Plugin-API-Tests (1 übersprungen), 50 Beispiel-Plugin-Tests und
52 Dashboard-Testdateien mit 389 Tests; Dashboard-Lint bestand. Der Build
bestand einschließlich `vue-tsc`. `shellcheck`, `bash -n`, `make help`,
`make hints`, Skriptaufrufe ohne Argument, mit `--help` und `--info` sowie
`git diff --check` bestanden. Nach der Selbstheilung wurden der betroffene
Setup-Lauf, ShellCheck, Bash-Syntax und die Skript-Smokes wiederholt. Der
Anleitungsabgleich ist wegen B1 unten noch offen.

**Code-Standards:** Gelesen wurden
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`architecture.md`, `shell.md`, `cli.md`, `quality.md` und
`documentation.md` sowie `makefile-conventions/SKILL.md` mit der
`setup-libs.sh`-Vorlage. Architektur ✅ Entwicklungs-Setup ohne App-Änderung;
Shell ✅ Link-Logik aus der Hausvorlage, ShellCheck und vollständige
Funktionskommentare nach Selbstheilung; CLI ✅ ausdrückliches `--install`,
Hilfe ohne Argument und Kurz-/Langformen; Qualität/Tests ✅ frischer
Installationsweg, Einzelserver und vollständiger Stack unabhängig geprüft;
Dokumentation ⚠️ 1 Befund (B1); Makefile ✅ Setup-Gruppe, Hilfetext und
ausführbarer Installationspfad. Python, Frontend/i18n und Persistenz ➖ kein
Quellcode in diesen Gruppen geändert. Bezeichnerinventar des neuen Bash-
Skripts: alle Funktions- und Variablennamen englisch. DRY ✅: Der
Übergabediff und der berührte Setup-Code nutzen eine tabellengesteuerte
Link-Funktion und eine ProjectTools-Abhängigkeit in `requirements-dev.txt`;
keine parallele Installationslogik oder zweite Paketliste.

**Doku-Abgleich:** `README.md` (Requirements und Quick start) beschreibt die
neue Einrichtung; `make hints` nennt denselben Startweg. Die zunächst
stehengebliebene Aussage „Node.js optional“ widersprach dem unbedingten
`npm ci` in `make setup`; `a3bd3b1` nennt Node.js und npm nun ausdrücklich
für diesen Weg. `docker/README.md` und `unraid/README.md` bleiben sachlich
unverändert: Das Dockerfile installiert `requirements.txt`, nicht
`requirements-dev.txt`, und benötigt die `.libs`-Links nicht. StockPortfolios
Skript und README wurden gelesen, der Teststack ausgeführt; dort wurde nichts
geändert. **B1:** `../StockPortfolio/README.md` im Abschnitt zum lokalen
Teststack sagt für den StockInfo-Einzelserver weiterhin „uses plain help with
the current StockInfo environment“ (Zeile 426). Nach T-82 ist
`projecttools.ui.colors` in StockInfos venv installiert; der unabhängige
`--help`-Lauf nutzte den gemeinsamen Formatter (`has_theme() == True`). Die
Anleitung des
Konsumentenprojekts muss diese Aussage an den nun gültigen Stand anpassen.
Danach sind die betroffenen Abschnitte beider READMEs erneut auf Konsistenz
zu prüfen. Dieser Repo-übergreifende Doku-Befund wird wegen der Schreibgrenze
nicht vom StockInfo-Verifier in StockPortfolio geändert.

**Umfang und offener gemeinsamer Stand:** Der tatsächliche T-82-Diff
`849454f..fa5b240` ohne T-86 und STATUS umfasst 5 Dateien, +284/−22;
die OUTBOX nennt +282/−22. Nach `a3bd3b1` sind es +294/−23. Die
Hausvorlage `makefile-conventions/setup-libs.sh` prüft weiterhin den
veralteten Pfad `ProjectTools/src/python/colors.py`; die Übernahme in die
gemeinsame Skill-Quelle bleibt offen und ist kein StockInfo-Produktedit.
Keine menschliche Ticketabnahme oder Änderung der Human-Spalte erfolgte.

### Verifier-Prüfung · Runde 2 (Codex, 2026-10-01)

**Ergebnis: technisch `approved` unter Mikes dokumentierter
Folgeticket-Entscheidung.** `2a3cc0c` gegen `c68d5ba` ändert nur dieses
Ticket und `STATUS.md`; `git diff --check` ist sauber. Es gibt keinen neuen
Produktedit, keinen geänderten Paketvertrag und keinen Anlass, die grünen
Setup-, Test- und Stack-Läufe aus Runde 1 zu wiederholen. Der geprüfte
T-82-Produktstand bleibt `a3bd3b1`.

**B1 eingeordnet:** Der falsche Satz steht weiterhin in
`../StockPortfolio/README.md:426`. Mike hat entschieden, ihn als eigenes
StockPortfolio-Ticket bearbeiten zu lassen. T-75 enthält den genauen Satz,
die betroffene Anleitung und zwei Verify-Handgriffe. Entgegen dem Stand der
OUTBOX ist es inzwischen im StockPortfolio-Commit `deaaf46` erfasst und laut
dortigem `STATUS.md` nach T-74 eingeplant. T-82 fügt StockInfo keine
Querverweise hinzu. Verify #4 bleibt ◑, weil die fremde aktuelle Anleitung
bis T-75 noch falsch ist; die nötige Anpassung ist benannt und durch Mikes
Entscheidung getrennt beauftragt. Dies ist keine Abnahme von StockPortfolio
T-75 und keine Aussage, dass dessen README bereits korrigiert sei.

**Gemeinsame Vorlage:** In PersonalSkills-`master` enthält `39cb1ae` den
richtigen Prüfpfad `ProjectTools/src/python/projecttools/ui/colors.py`.
Der installierte Skill zeigt noch den alten Pfad, weil sein Checkout auf
`t-45-central-agentlessons-entry` steht. Diese Übernahme bleibt bis zur
Aktualisierung des installierten Checkouts sichtbar offen; StockInfos lokale
Kopie funktioniert und wurde in Runde 1 geprüft. Die gemeldeten 24
PersonalSkills-Tests wurden hier nicht wiederholt.

**Standards und Doku-Abgleich:** Die in Runde 1 gelesenen
`code-standards/SKILL.md`-Referenzen (`architecture.md`, `shell.md`,
`cli.md`, `quality.md`, `documentation.md`) und
`makefile-conventions/SKILL.md` bleiben für den unveränderten Produktstand
maßgeblich. Architektur, Shell, CLI, Qualität/Tests, Makefile und DRY ✅ wie
in Runde 1 belegt; Python, Frontend/i18n und Persistenz ➖. Dokumentation
für StockInfo ✅: Root-README, Docker-README, Unraid-README und `make hints`
wurden in Runde 1 abgeglichen. Die abweichende StockPortfolio-Anleitung ist
als T-75 offen und erklärt das ◑ bei Verify #4. Kein Produktcode wurde im
Review geändert; menschliche Abnahme und Ticketabschluss bleiben unberührt.
