# T-68 · Ticketordner nach Arbeitsstand ordnen

Geplante, laufende und abgeschlossene Arbeit soll schon im Dateibrowser
unterscheidbar sein. Im bisherigen Root liegen diese Zustände nebeneinander.

**Von Mike beauftragt, aber erst nach den laufenden Arbeiten ausführen.**
Andere Instanzen arbeiten noch mit den bisherigen Ticketpfaden. Dieses Ticket
aktiviert sich nicht selbst und ändert die laufende Prioritätskette nicht.

## Für dich

Die Ordnernamen und ihre Reihenfolge sind entschieden. Keine weitere
Entscheidung dazu nötig. Vor dem Verschieben muss feststehen, dass die anderen
Instanzen ihre laufenden Arbeiten und Reviews beendet haben. Ein Wechsel des
Owners allein reicht dafür nicht.

Mike, 2026-09-09:

> Das passt dann so. Aktuell arbeiten andere Instanzen an einigen Tickets. Danach kannst du dann die Struktu umstellen und in STATUS.md usw. die Info nachziehen

Ergänzung von Mike, 2026-09-09: Alte Skripte in `solved/` bleiben inhaltlich
unverändert. Die neuen Regeln gelten auch für das Skill
`task-verification-workflow` und seine Vorlagen.

## Vereinbarte Ordner

```text
_tickets/
├── .agents/
├── 10-backlog/
├── 20-ready/
├── 30-doing/
├── 40-done/
├── 80-iced/
└── 90-rejected/
```

| Ordner | Bedeutung |
|---|---|
| `10-backlog/` | Gewollte Arbeit, noch nicht zur Ausführung eingeplant |
| `20-ready/` | Beauftragt und als Nächstes dran |
| `30-doing/` | Begonnen, einschließlich Review und Nacharbeit |
| `40-done/` | Abgeschlossen |
| `80-iced/` | Auf Eis, ohne geplante Wiederaufnahme |
| `90-rejected/` | Bewusst verworfen |

Im Root bleiben `README.md`, `STATUS.md` und `QUESTIONS.md`. Die fünf
Agentendokumente ziehen nach `.agents/`. Die Ordnernummern bestimmen
die Anzeige im Dateibrowser. Die Arbeitsreihenfolge steht weiterhin in
`STATUS.md`; die genaue Bearbeitungsphase und die Rollen werden dort geführt.

## Umsetzung

1. Den dann aktuellen Bestand erfassen und die laufenden Arbeiten prüfen.
   Die heutige Ticketliste ist keine feste Verschiebeliste: Bis zur Umstellung
   können weitere Tickets abgeschlossen oder neu eingeplant sein.
2. `solved/` nach `40-done/`, `postponed/` nach `80-iced/` und `rejected/` nach
   `90-rejected/` verschieben. Root-Tickets nach ihrem tatsächlichen Stand
   zuordnen. Bestehende Prüfungen und menschliche Antworten erhalten.
3. Ticketpfade und Verweise gemeinsam nachziehen: `STATUS.md`, Board-README,
   Projektregeln, Reviewvertrag, Aktivierungsanweisungen und Scheduler.
   Insbesondere entfällt die bisherige Prüfung „aktives Ticket direkt im Root“.
   Aktive Arbeit muss auf ein Ticket in `30-doing/` zeigen; vor Beginn des
   nächsten Tickets erfolgt der Wechsel aus `20-ready/` samt Statusanpassung.
4. Verweise in aktueller Dokumentation, Specs, Tests und noch verwendeten
   Skripten prüfen. Bereits archivierte Skripte aus `solved/` wandern mit dem
   Ordner nach `40-done/`, bleiben aber inhaltlich unverändert. Für sie sind
   weder Reparaturen noch erneute Testläufe Teil dieses Auftrags. Historische
   Berichte nicht fachlich umschreiben; nötige Linkkorrekturen sind erlaubt.
5. Die neue Ablage und die Regeln für Aufnahme, Arbeitsbeginn, Review und
   Abschluss im Ticket-Skill und in `_tickets/README.md` nachziehen. Der Skill
   beschreibt die allgemeinen Regeln, die README deren Anwendung in StockInfo.
   Die Agenten dürfen erst wieder mit den neuen Pfadregeln arbeiten, wenn
   Verschiebungen, Skill und Verweise stimmen.

## Ticket-Skill mit umstellen

Geprüft am 2026-09-09: Codex und Claude verwenden über ihre Skill-Verzeichnisse
dieselbe Quelle unter
`/Volumes/DevLocal/DevKI/Production/PersonalSkills/task-verification-workflow/`.
Die Änderung erfolgt dort einmal, zusammen mit der Board-Umstellung.
Bis dahin bleiben die geladenen Regeln für die laufenden Arbeiten unverändert.

| Datei | Nötige Anpassung |
|---|---|
| `SKILL.md` | Prinzip „Ort = Status“, Ordnerbaum, Aufnahme und Abschluss, Skriptbeispiele sowie Board-Pfade im Abschnitt zur Agentenkommunikation auf die sechs Ordner umstellen |
| `templates/ticket.md` | Verweis auf `solved/` ersetzen; die zusätzliche Statusspalte mit Vorgabe `ready` nicht als zweite Quelle für den Ordnerstatus weiterführen |
| `templates/QUESTIONS.md` | Archivverweis im Merksatz auf `40-done/` ändern |

Die Skill-Regeln für neue oder künftig geänderte Ticket-Skripte verwenden
die neuen Pfade. Die Ausnahme für bereits archivierte StockInfo-Skripte steht
in diesem Ticket; sie verlangt keine rückwirkende Überarbeitung archivierter
Prüfskripte. Die weiterhin gültigen Beispiele im Skill werden dagegen angepasst.

Bestehende Boards anderer Projekte werden durch die Skill-Änderung nicht
automatisch verschoben. Deren dokumentierte Ablage gilt bis zu einer eigenen
Umstellung weiter. Beide Skill-Zugänge werden am Ende auf dieselbe aktualisierte
Quelle geprüft. Das PersonalSkills-Repository gehört damit zum Änderungsumfang.

## Dateinamen der Agentenregeln · Prüfung vom 2026-09-09

Mike verlangt auch hier eine klare Trennung: Claude und Codex können jeweils
Coder oder Verifier sein. Ein Agentenname im Dateinamen darf keine feste Rolle
vorgeben. Geprüft wurden die Aufgaben, Einleitungen und Abschnitte der fünf
Agentendateien sowie ihre Verweise in `AGENTS.md` und im Ticket-Skill.

**Namensschema für die vereinbarte Ablage; noch keine Dateien umbenannt:**

| Bisher | Vorschlag | Grund |
|---|---|---|
| `CODEX-REVIEW-AUTOMATION.md` | `AGENT-WORKFLOW.md` | Gemeinsame Regeln für Implementierung, Übergabe, Review und Abschluss; gilt für beide Agenten und beide Rollen |
| `AGENT-ACTIVATION.md` | unverändert | Startanweisungen für die jeweiligen Laufzeiten; Rollen kommen aus STATUS |
| `CODEX-IN-CONTEXT-SCHEDULER.md` | unverändert | Tatsächlich Codex-spezifische Laufzeit; bedient abhängig von STATUS beide Rollen |
| `CLAUDE-REVIEW-PATTERNS.md` | `CLAUDE-LESSONS.md` | Belegte Fehler und Erfahrungen aus Claudes Arbeit, einschließlich Implementierung und Review |
| `CODEX-REVIEW-PATTERNS.md` | `CODEX-LESSONS.md` | Belegte Fehler und Erfahrungen aus Codex-Arbeit, einschließlich Implementierung und Review |

Die Agentennamen in den Erfahrungssammlungen bezeichnen die Herkunft der
Belege, nicht deren Leser oder dessen aktuelle Rolle. Allgemeine Regeln gelten
für beide Agenten. Gemeinsame Ablaufregeln wie das Rundenlimit gehören einmal
ins gemeinsame Regelwerk; Projektvorgaben gehören in `CLAUDE.md`. Die
Erfahrungssammlungen behalten Anlass, Belege und Verweise auf diese Regeln.

Der ausführende Agent bleibt im jeweiligen Beleg erkennbar. Historische
Autorenschaft, Review-Rollen und Befunde werden nicht durch Umbenennen geändert.
`STATUS.md` bleibt die Quelle für die aktuelle Rollenverteilung. Die
Projekt-Einstiegsdateien `AGENTS.md` und `CLAUDE.md` außerhalb von `_tickets/`
sind von dieser Namensprüfung nicht zur Umbenennung vorgesehen.

Die später verwendeten Namen müssen gemeinsam in Board-Regeln, Aktivierung,
Scheduler, Ticket-Skill, Vorlagen und aktuellen Verweisen nachgezogen werden.
Die bereits vereinbarte Wartebedingung gilt auch für diese Umbenennungen.

### Eigener Ordner für Agentendokumente · beschlossen

Mike bestätigt am 2026-09-09 die Ablage und verlangt ausdrücklich, die
Verweise mit anzupassen. Die fünf Agentendokumente werden nach
`_tickets/.agents/` verschoben, mit den oben genannten Namen.
Sie beschreiben die Zusammenarbeit am
Ticketboard und bleiben damit bei dessen Dateien. Der gemeinsame Ordner
gehört weder ausschließlich zu Claude noch zu Codex.

`STATUS.md`, `README.md` und `QUESTIONS.md` bleiben im sichtbaren Board-Root:
aktueller Arbeitsstand, Board-Anleitung und offene Fragen sollen direkt
zugänglich sein. Die Projekt-Einstiege `AGENTS.md` und `CLAUDE.md` bleiben
im Projekt-Root und verweisen ausdrücklich auf die verschobenen Regeln.

Der versteckte Ordner wird mit Git versioniert. Beim Datei-Inventar und bei
Linkprüfungen muss er ausdrücklich einbezogen werden. Die Board-README
verlinkt ihn. Keine automatische Erkennung dieses Ordners voraussetzen.
Auch relative Links innerhalb der verschobenen Dateien, Ankerlinks und
Pfadangaben in Startprompts werden angepasst und geprüft. Dazu gehören
Verweise aus Projektregeln, Board-Dateien, aktueller Dokumentation und dem
Ticket-Skill samt Vorlagen. Für archivierte Skripte gilt weiterhin die
vereinbarte Ausnahme. Bis zur gemeinsamen Umstellung bleiben die bisherigen
Pfade gültig.

## Observer-Auftrag ausgelagert

Der vollständige Auftrag samt CLI- und Loop-Prüfungen liegt nach Claudes
Scope-Entscheidung `6177c76` in [T-69](T-69-observer-instanzen-und-loop.md).
Er folgt direkt auf T-68. Die frühere Prüfmatrix #7–10 wird dort als #1–4
geführt; sie ist durch die Ordnerumstellung nicht bestanden.

## Reihenfolge und Grenzen

### Aktivierungsanleitung geprüft · 2026-09-09

Auf Mikes Auftrag wurde `AGENT-ACTIVATION.md` bereits redaktionell angepasst.
Der Claude-Startprompt verweist jetzt auf den Abschnitt „Claude-Durchlauf“
in derselben Datei. Rollenprüfung, Priorität, Pflicht-Skill, Autorensammlung
und Übergaberegeln bleiben über den Durchlauf und den gemeinsamen Workflow
erhalten. Die fachlichen Regeln werden nicht mehr im Startbefehl wiederholt.
Vorhandene laufende Jobs wurden weder geändert noch neu gestartet.

Die Observer-Aktivierung ist ausdrücklich als Vorbereitung für dieses Ticket
aufgenommen. Claude erhält eine kurze Loop-Vorlage; beim Codex-Kurzbefehl
muss die Verfügbarkeit des bisherigen In-Context-Schedulers in der gestarteten
CLI noch geprüft werden. Dessen aktueller Vertrag unterstützt den Observer
noch nicht. Keine ungetestete Gleichsetzung der Codex-Laufzeiten.

`/loop 5m <Prompt>`, Job-Verwaltung und Wiederanlauf wurden gegen die
[offizielle Claude-Dokumentation](https://code.claude.com/docs/en/scheduled-tasks)
geprüft. Die frühere pauschale Aussage zur Löschung beim Ausstieg wurde
korrigiert. Das ist eine Dokumentations- und Ablaufprüfung, kein Live-Test.
Die praktische Prüfung bleibt in T-69 offen.

Doku-Abgleich: `AGENT-ACTIVATION.md` und dieses Ticket angepasst. Bestehende
Dateinamen und Einstiegsanker bleiben erhalten; die übrigen Verweise werden
bei der vereinbarten Umstellung nachgezogen.
Prüfergebnis: Claude-Startprompt von 2.471 auf 97 Zeichen gekürzt;
lokale Markdown-Links samt Ankern beider Dateien geprüft, bisherige
Einstiegsanker erhalten, `git diff --check` ohne Befund.

### Fachliche Reihenfolge

Mikes fachliche Reihenfolge bleibt erhalten: **T-25 gehört zum Plugin-Abschluss;
T-63 folgt als Prüfung des Containers, danach das MCP-Vorhaben.** T-66 gehört
als späteres Vorhaben ins Backlog. Dabei Konzeptabschluss und noch nicht
beauftragte Umsetzung auseinanderhalten; die Ablage startet keinen Bauauftrag.

Kein neues Board-Werkzeug und keine zusätzliche Statusdatei. Die Umstellung
ändert weder Produktverhalten noch bisherige Freigaben oder Review-Runden.

## Prüfung

| # | Erwartetes Ergebnis | AI |
|---|---|:--:|
| 1 | Vorherige Ticket- und Begleitdateien vollständig vorhanden; jedes Ticket genau einem Ordner zugeordnet | ➖ |
| 2 | Aktuelle Ticketlinks und Arbeitsanweisungen verwenden gültige Pfade; keine veraltete Root-Pflicht. Alte Pfadtexte in archivierten Skripten sind von der Anpassung ausgenommen | ➖ |
| 3 | Status, Prioritätskette und Ordner passen zusammen; Backlog, Iced, Done und Rejected starten keine Arbeit | ➖ |
| 4 | Noch verwendete Skripte und betroffene vorhandene Prüfungen funktionieren nach dem Umzug; archivierte Skripte aus `solved/` sind inhaltlich unverändert und werden nicht erneut ausgeführt; Arbeitsdaten bleiben unberührt | ➖ |
| 5 | README, Ticket-Skill samt Vorlagen und Agentenregeln erklären denselben Ablauf; bisherige Nachweise und menschliche Antworten bleiben erhalten | ➖ |
| 6 | Codex und Claude lesen dieselbe aktualisierte Skill-Quelle; andere bestehende Boards werden nicht automatisch umgestellt | ➖ |

## Stand

**Begonnen; Scope-Checkpoint vor der Umstellung.** Claude hat T-25 mit
`c1ce421` nach `solved/` verschoben und den Einstieg mit `debb3d1` aktualisiert.
Mike bestätigt anschließend: „Ja, ist durch“. Damit ist die Wartebedingung
für die gemeinsame Umstellung erfüllt. Noch keine Ordner verschoben,
Skill-Quelldateien geändert oder Observer eingerichtet.

## Scope-Vertrag · 2026-09-09

**Entscheidung Claude `6177c76`: `split`.** T-68 liefert ausschließlich die
Ablageänderung mit allen Verweisen und dem gemeinsamen Skill. Der vollständige
Observer-Auftrag wird als T-69 direkt angeschlossen. Budget für T-68:
2 Produkt-/Skriptdateien, 110 Test-/Dokudateien, 2.500 Inhalts-Diff-Zeilen;
damit ist die einmalige Erweiterung verbraucht. Die nachfolgenden Angaben zum
Checkpoint dokumentieren den eingereichten Zuschnitt.

### Lieferung und Review über beide Repositorys

Die Auflage aus `6177c76` wird vor der ersten Verschiebung so erfüllt:

- **StockInfo:** Übergabe mit `handoff_commit` auf den fertigen Board-Stand.
  Verschiebungen werden separat von Inhaltsänderungen committet; die OUTBOX
  nennt beide Commits und den Inhalts-Diff gegen den gesicherten Ausgangsstand.
- **PersonalSkills:** Ausgangscommit
  `3e6c8d828cb19e32a373ece540ea30034b041e95`; geändert werden ausschließlich
  `task-verification-workflow/SKILL.md`, `templates/ticket.md` und
  `templates/QUESTIONS.md`. Der exakte Abschlusscommit und die SHA-256-Werte
  dieser drei Dateien stehen vor dem StockInfo-Handoff im Ticket und in der
  OUTBOX. Vorhandene fremde Änderungen bleiben erhalten und werden separat
  ausgewiesen; sie gehören nicht zum eigenen Skill-Diff.
- Claude prüft im PersonalSkills-Repository den benannten Commit und vergleicht
  seine drei Dateiinhalte mit den tatsächlich von beiden Skill-Symlinks
  gelesenen Dateien. Der Nachweis nennt deren aufgelöste Pfade und Prüfsummen.
  Ein Worktree-Stand ohne benannten Commit gilt nicht als gelieferter Skill.
- Der Inhaltsabgleich prüft in beiden Repositorys dieselben sechs Ordner,
  `.agents/` und Dateinamen, Aufnahme/Einplanung/Beginn/Review/Abschluss sowie
  die Ausnahme für unveränderte Archivskripte und fremde bestehende Boards.
  Pfad- und Ankerprüfungen ergänzen diesen inhaltlichen Abgleich.

Vorherige Worktree-Inhalte und getrennte Ausgangsdiffs beider Repositorys
sind unter `/tmp/t68-baseline/`, `/tmp/t68-before-stockinfo.patch` und
`/tmp/t68-before-personalskills.patch` gesichert. Die Sicherung ist Arbeitsmittel;
die endgültige Übergabe stützt sich auf die genannten Commits und Prüfsummen.

**Beobachtbares Ergebnis:** Das Board zeigt den Arbeitsstand durch den
Ablageort. Beide Agenten lesen dieselben dazu passenden Regeln und können
zusätzliche Instanzen eindeutig und ohne fremde Rollenarbeit starten.

Der bisherige Auftrag enthält drei fachliche Änderungen:

1. Bestehende Tickets und Begleitdateien in die vereinbarten Ordner verschieben;
   aktuelle Pfade und Regeln einschließlich Skill und Vorlagen gemeinsam ändern.
2. Die optionale Observer-Rolle samt exaktem Vergleich der Instanzkennung im
   gemeinsamen Workflow beschreiben; keine zusätzliche Freigaberunde.
3. Die beiden Observer-Kurzbefehle einrichten und ihren tatsächlichen
   CLI-Start, Kontextwechsel und Beobachtungsloop prüfen.

**Zuschnitt für den Checkpoint:** Punkt 1 ist unabhängig von 2 und 3
lieferbar. Die Ordnerumstellung allein braucht keinen neuen Observer und
keinen Nachweis zum Verhalten von `/clear`. Vorschlag an den Verifier:
`split` — T-68 liefert die beschlossene Ablage samt Regeln und Skill;
Observer-Rolle, Startbefehle und Live-Prüfungen bilden ein unmittelbar
anschließendes Ticket. Der Auftrag geht dabei nicht verloren. Vor dem
Scope-Entscheid wird weder ein Folgeticket angelegt noch die Kette erweitert.

### Bestand und betroffene Flächen

Inventar nach Claudes Abschluss: **98 Dateien** unter `_tickets/`, davon
79 in `solved/`, fünf in `postponed/`, zwei in `rejected/` und zwölf im Root.
Das Inventar schließt versteckte Dateien ein. Pfad, Größe und SHA-256 stehen
für den Vorher-/Nachher-Abgleich in `/tmp/t68-before-inventory.json`.
Zwölf Arbeitsdatendateien sind separat mit Prüfsummen erfasst; ihre Inhalte
wurden weder ausgegeben noch verändert.

- T-68 zieht als aktive Arbeit nach `30-doing/`.
- T-66 zieht nach `10-backlog/`: Konzept freigegeben, Bau nicht beauftragt.
- T-63 zieht nach `10-backlog/`: Sein aktueller Einstieg sagt ausdrücklich
  „nicht eingeplant“, und die aktive Kette enthält nur T-68. Die fachliche
  Reihenfolge Container vor MCP bleibt bestehen; die Ablage plant keinen Lauf ein.
- Der historische Bericht `codex-verification-2026-08-19-plugin-system-design.md`
  zieht nach `40-done/`; sein Berichtstext bleibt historischer Nachweis.
- Die fünf Agentendokumente ziehen mit den beschlossenen Namen nach `.agents/`.
- Außerhalb des Boards enthält das Inventar 19 versionierte Dateien mit
  Ticketpfaden: die beiden Projekteinstiege, zwei Dashboard-Dateien,
  REST-Vertrag, historische Pläne/Specs und `scripts/sources-profile.sh`.
  Nur erforderliche Verweisänderungen; keine fachliche Überarbeitung der Historie.
- Im PersonalSkills-Repository sind genau der Ticket-Skill und die beiden
  genannten Vorlagen betroffen. Die freigegebene gemeinsame Quelle wird
  einmal geändert; andere Boards bleiben an ihrem dokumentierten Ort.

Bereits vorhandene uncommittete Änderungen werden als Ausgangsbestand
gesichert und erhalten. Fremde Dokumentlöschungen und sonstige Nebenarbeit
sind kein Teil des Übergabe-Diffs. Archivierte Skripte werden nur verschoben;
Bytevergleich statt Reparatur oder Wiederholung ihrer Testläufe.

### Budget und Abgrenzung

Beantragt für die **Ordnerumstellung allein**: höchstens zwei Produkt- oder
aktive Skriptdateien mit reinen Pfadänderungen, 110 Test-/Dokumentationsdateien
einschließlich Tickets, Skill und Vorlagen, **2.500 geänderte Inhaltszeilen**.
Reine Umbenennungen werden mit Git-Rename-Erkennung gesondert ausgewiesen;
die vorhandenen Inhalte zählen nicht nochmals als neu geschriebene Zeilen.
Neue Ticket- und Übergabedokumentation zählt dagegen mit.

Aktuell: keine Produktdatei geändert; nur dieses Ticket um Bestand und
Scope-Vertrag ergänzt. Der erwartete mechanische Diff überschreitet die
800-Zeilen-Schwelle. Das und der unabhängig lieferbare Observer-Umfang sind
die Auslöser des Checkpoints. Noch keine Budgeterweiterung verbraucht.

Nicht-Ziele: Produktverhalten, Datenmigration, Containerprüfung, MCP-Bau,
neues Board-Werkzeug, neue Statusdatei, Änderungen an menschlichen Antworten
oder bisherigen Freigaben. Keine Neufassung historischer Reviewberichte.

### Ausführung und Nachweis nach dem Scope-Entscheid

1. Vorher-Inventar und vorhandene Änderungen sichern; Zielzuordnung vollständig
   festlegen. Noch keine Agenten auf die neue Ablage aktivieren.
2. Dateien verschieben und aktuelle Verweise einschließlich relativer Links
   in den verschobenen Dokumenten anpassen. Leere vereinbarte Ordner erhalten.
3. Workflow, README, STATUS, Aktivierung und Scheduler gemeinsam auf
   `30-doing/` umstellen; Wechsel aus `20-ready/` mit STATUS atomar beschreiben.
4. Skill und Vorlagen zuerst als überprüfbaren Diff vorbereiten, danach die
   freigegebene gemeinsame Quelle ändern und beide Skill-Zugänge vergleichen.
5. Vollständigkeit, eindeutige Ticketzuordnung, Links/Anker einschließlich
   `.agents/`, unveränderte Archivskripte und Arbeitsdaten prüfen. Betroffene
   vorhandene Tests gezielt ausführen; keine Archivskripte starten.
6. Aktuelle Verify-Zeilen mit konkreten Belegen aktualisieren, Scope-Budget
   messen, gemeinsamen Doku-Abgleich dokumentieren und an Claude übergeben.
