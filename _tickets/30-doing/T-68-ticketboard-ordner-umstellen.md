# T-68 · Ticketordner nach Arbeitsstand ordnen

Geplante, laufende und abgeschlossene Arbeit soll schon im Dateibrowser
unterscheidbar sein. Im bisherigen Root liegen diese Zustände nebeneinander.

**Umgestellt; unabhängige Prüfung steht aus.** Tickets liegen nach
Arbeitsstand in den sechs vereinbarten Ordnern. Die Agentenregeln liegen
unter `.agents/`; beide Agenten verwenden dieselbe aktualisierte Skill-Quelle.
Der vollständige Observer-Auftrag folgt in T-69.

## Übersicht

- [Für dich](#für-dich)
- [Vereinbarte Ordner](#vereinbarte-ordner)
- [Umsetzung](#umsetzung)
- [Ticket-Skill mit umstellen](#ticket-skill-mit-umstellen)
- [Dateinamen der Agentenregeln · Prüfung vom 2026-09-09](#dateinamen-der-agentenregeln--prüfung-vom-2026-09-09)
- [Observer-Auftrag ausgelagert](#observer-auftrag-ausgelagert)
- [Reihenfolge und Grenzen](#reihenfolge-und-grenzen)
- [Prüfung](#prüfung)
- [Stand](#stand)
- [Scope-Vertrag · 2026-09-09](#scope-vertrag--2026-09-09)
- [Liefernachweis PersonalSkills](#liefernachweis-personalskills)
- [Nachweis der gültigen Arbeitsanweisung](#nachweis-der-gültigen-arbeitsanweisung)
- [Übergabeumfang · Runde 1](#übergabeumfang--runde-1)

## Für dich

Aktuell ist kein Handgriff nötig. Codex liefert die Nachweise an Claude;
die technische Freigabe ersetzt keine spätere Abschlussbestätigung.
Die Wartebedingung vor dem Umzug ist mit Mikes „Ja, ist durch“ nach Claudes
T-25-Abschluss erfüllt.

Mike, 2026-09-09:

> Das passt dann so. Aktuell arbeiten andere Instanzen an einigen Tickets. Danach kannst du dann die Struktu umstellen und in STATUS.md usw. die Info nachziehen

Ergänzung von Mike, 2026-09-09: Alte Skripte in `solved/` bleiben inhaltlich
unverändert. Die neuen Regeln gelten auch für das Skill
`task-verification-workflow` und seine Vorlagen.

[↑ Übersicht](#übersicht)

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

[↑ Übersicht](#übersicht)

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

[↑ Übersicht](#übersicht)

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

[↑ Übersicht](#übersicht)

## Dateinamen der Agentenregeln · Prüfung vom 2026-09-09

Mike verlangt auch hier eine klare Trennung: Claude und Codex können jeweils
Coder oder Verifier sein. Ein Agentenname im Dateinamen darf keine feste Rolle
vorgeben. Geprüft wurden die Aufgaben, Einleitungen und Abschnitte der fünf
Agentendateien sowie ihre Verweise in `AGENTS.md` und im Ticket-Skill.

**Umgesetzte Namen:**

| Bisher | Jetzt | Grund |
|---|---|---|
| `../.agents/AGENT-WORKFLOW.md` | `AGENT-WORKFLOW.md` | Gemeinsame Regeln für Implementierung, Übergabe, Review und Abschluss; gilt für beide Agenten und beide Rollen |
| `../.agents/AGENT-ACTIVATION.md` | unverändert | Startanweisungen für die jeweiligen Laufzeiten; Rollen kommen aus STATUS |
| `../.agents/CODEX-IN-CONTEXT-SCHEDULER.md` | unverändert | Tatsächlich Codex-spezifische Laufzeit; bedient abhängig von STATUS beide Rollen |
| `../.agents/CLAUDE-LESSONS.md` | `CLAUDE-LESSONS.md` | Belegte Fehler und Erfahrungen aus Claudes Arbeit, einschließlich Implementierung und Review |
| `../.agents/CODEX-LESSONS.md` | `CODEX-LESSONS.md` | Belegte Fehler und Erfahrungen aus Codex-Arbeit, einschließlich Implementierung und Review |

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

Die Namen sind in Board-Regeln, Aktivierung, Scheduler, Ticket-Skill,
Vorlagen und aktuellen Verweisen nachgeführt.

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
vereinbarte Ausnahme. Die neuen Pfade gelten gemeinsam für Board und Agentenregeln.

[↑ Übersicht](#übersicht)

## Observer-Auftrag ausgelagert

Der vollständige Auftrag samt CLI- und Loop-Prüfungen liegt nach Claudes
Scope-Entscheidung `6177c76` in [T-69](../20-ready/T-69-observer-instanzen-und-loop.md).
Er folgt direkt auf T-68. Die frühere Prüfmatrix #7–10 wird dort als #1–4
geführt; sie ist durch die Ordnerumstellung nicht bestanden.

[↑ Übersicht](#übersicht)

## Reihenfolge und Grenzen

### Aktivierungsanleitung geprüft · 2026-09-09

Auf Mikes Auftrag wurde `../.agents/AGENT-ACTIVATION.md` bereits redaktionell angepasst.
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

Doku-Abgleich: `../.agents/AGENT-ACTIVATION.md` und dieses Ticket angepasst. Bestehende
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

[↑ Übersicht](#übersicht)

## Prüfung

| # | Erwartetes Ergebnis | AI |
|---|---|:--:|
| 1 | Vorherige Ticket- und Begleitdateien vollständig vorhanden; jedes Ticket genau einem Ordner zugeordnet | ✅ [^t68-1] |
| 2 | Aktuelle Ticketlinks und Arbeitsanweisungen verwenden gültige Pfade; keine veraltete Root-Pflicht. Alte Pfadtexte in archivierten Skripten sind von der Anpassung ausgenommen | ✅ [^t68-2] |
| 3 | Status, Prioritätskette und Ordner passen zusammen; Backlog, Iced, Done und Rejected starten keine Arbeit | ✅ [^t68-3] |
| 4 | Noch verwendete Skripte und betroffene vorhandene Prüfungen funktionieren nach dem Umzug; archivierte Skripte aus `solved/` sind inhaltlich unverändert und werden nicht erneut ausgeführt; Arbeitsdaten bleiben unberührt | ⚠️ [^t68-4] |
| 5 | README, Ticket-Skill samt Vorlagen und Agentenregeln erklären denselben Ablauf; bisherige Nachweise und menschliche Antworten bleiben erhalten | ✅ [^t68-5] |
| 6 | Codex und Claude lesen dieselbe aktualisierte Skill-Quelle; andere bestehende Boards werden nicht automatisch umgestellt | ✅ [^t68-6] |

[^t68-1]: Inventar: 98/98 Ausgangsdateien; 77 Tickets ohne Doppelzuordnung.
[^t68-2]: 314 lokale Links samt Ankern geprüft; 0 Befunde. Aktive Pfadregeln auf Doing.
[^t68-3]: Aktives T-68 in Doing; T-69 in Ready und Kette; T-63/T-66 im Backlog.
[^t68-4]: 12 Archivskripte und die 12 ursprünglichen Arbeitsdateien SHA-256-identisch; 3 Proxytests grün; TS-Tokenstrom unverändert. Im späteren Inventar kamen `stockinfo.db-wal` und `stockinfo.db-shm` hinzu. Kein DB-Test oder App-Start wurde für T-68 ausgeführt; die Herkunft der neuen Begleitdateien ist nicht unabhängig zugeordnet. Sie wurden nicht verändert oder entfernt. Deshalb kein vollständiger Gleichheitsclaim für das gesamte Datenverzeichnis.
[^t68-5]: Gemeinsamer Workflow und Projektvorgabe zentral; README/Skill/Startverträge abgeglichen.
[^t68-6]: PersonalSkills eeaad8c; beide Symlinks zeigen auf dieselbe Quelle, Hashvergleich siehe Nachweis.

[↑ Übersicht](#übersicht)

## Stand

Die Ablage ist umgesetzt. Reiner Verschiebe-Commit: `b7c9896` (95 Dateien,
100 % unveränderter Git-Inhalt). Pfadkorrekturen: `3d01098`, `d76ac27`;
die begleitenden Regeländerungen werden im Übergabecommit festgehalten.
T-63 und T-66 liegen im Backlog, T-68 in Doing und T-69 in Ready.
Die Matrix unten beziehungsweise im Abschnitt „Prüfung“ ist die einzige
aktuelle technische Bewertung. Claudes unabhängiges Review steht noch aus.

[↑ Übersicht](#übersicht)

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

**Beobachtbares Ergebnis von T-68:** Das Board zeigt den Arbeitsstand durch
den Ablageort; beide Agenten lesen dieselben passenden Regeln und Vorlagen.
Zusätzliche Instanzen sind Gegenstand von T-69.

### Eingereichter Zuschnitt · Historie des Checkpoints

Der ursprüngliche Auftrag enthielt drei fachliche Änderungen:

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

Beim Checkpoint: keine Produktdatei geändert; nur dieses Ticket um Bestand
und Scope-Vertrag ergänzt. Der erwartete mechanische Diff überschreitet die
800-Zeilen-Schwelle. Das und der unabhängig lieferbare Observer-Umfang sind
die Auslöser des Checkpoints. Damals war noch keine Budgeterweiterung verbraucht; `6177c76` hat sie erteilt.

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

[↑ Übersicht](#übersicht)

## Liefernachweis PersonalSkills

Repository: `/Volumes/DevLocal/DevKI/Production/PersonalSkills`.
Basis: `3e6c8d828cb19e32a373ece540ea30034b041e95`.
Ablageregeln: `94a766d`; Navigation und abschließender Skill-Prüfstand:
`eeaad8c2979b6dd1d5cd470b3a0349cb7dd2be1b`.
Die drei Dateien sind gemeinsam mit dem StockInfo-Handoff zu prüfen.

Beide Zugänge lösen nach `PersonalSkills/task-verification-workflow` auf:
`/Users/macminipro/.codex/skills/task-verification-workflow` und
`/Users/macminipro/.claude/skills/task-verification-workflow`.

| Datei | SHA-256 im Commit | SHA-256 der gemeinsamen Quelle |
|---|---|---|
| `SKILL.md` | `7a164b3369b2669ee1445392ba80b305ae8b03c5979675639a538b808cfe85bb` | `30f936bde19120b32f15f4d6baecbf099db9c26250c4887ac7f2305d2ccef037` |
| `templates/ticket.md` | `1eb99d39652e6101342559266264b017eaca8491446fe0480f9d70a553a8cb32` | `6a3fb39c4d97e5514ae126b330215ad02fc0be7756a486ec05c1fc62353f79a5` |
| `templates/QUESTIONS.md` | `1c1916b25b3ee5ae6c1125553a0bd304ad93d4293b351fa2829ae9fbac995579` | `1c1916b25b3ee5ae6c1125553a0bd304ad93d4293b351fa2829ae9fbac995579` |

Die unterschiedlichen Hashes bei Skill und Ticketvorlage sind vollständig
durch **30 bereits vor T-68 vorhandene, uncommittete Zeilen** erklärt:
26 Zeilen zum widerspruchsfreien Ticketabschluss und vier Kommentarzeilen
in der Vorlage. Dieser Ausgangsdiff bleibt unverändert und gehört nicht
zum eigenen Commit. Die Board-Regeln selbst sind im benannten Commit und
in der von beiden Agenten gelesenen Quelle identisch. Die QUESTIONS-Vorlage
ist vollständig bytegleich. Andere Projektboards wurden nicht verschoben.

Kopierbare Gegenprüfung:

```bash
git -C /Volumes/DevLocal/DevKI/Production/PersonalSkills diff eeaad8c -- task-verification-workflow
git -C /Volumes/DevLocal/DevKI/Production/PersonalSkills show --stat eeaad8c
git show --stat b7c9896
cd dashboard
npm test -- tests/viteProxy.spec.ts
```

Doku-Abgleich: Projekteinstiege, Board-README und STATUS, fünf Agentendokumente,
Ticket-Skill samt zwei Vorlagen, betroffene Archivlinks und aktuelle
Spec-/Vertragsverweise beschreiben dieselbe Ablage. Historische Nachweise
bleiben Historie; die Observer-Prüfungen sind ausdrücklich nach T-69 übertragen.
Die neue Navigation und die geprüften Links betreffen Markdown, kein UI.

[↑ Übersicht](#übersicht)

## Nachweis der gültigen Arbeitsanweisung

Realer Zustandsabgleich: T-68 ist `ticket == priority_ticket` und liegt in
`30-doing/`; T-69 ist das anschließende Kettenglied und liegt in `20-ready/`.
Kein Ticket aus den fünf inaktiven Ordnern wird unter `30-doing/` gefunden.
Das ist ein Datei-/Vertragsnachweis, kein behaupteter Observer-Live-Test.
Die jetzige Scheduler-Zelle wird mit genau dieser Dateischranke neu gestartet.

Die aktuellen Einstiege und Laufzeitverträge enthalten keine alten
Agentenpfade und keinen Riegel „Ticket direkt im Root“. 314 lokale Markdown-
Links samt Ankern in Board, Projekteinstiegen und Dokumentation sind geprüft;
zusätzlich 17 Links/Anker des gemeinsamen Skills und seiner Vorlagen.
Die unversionierte `docs/markdown-styles/README.md` behält ihren fremden
Inhalt; allein ihr T-56-Link wurde im Worktree mitgezogen.

Bereits vorbereitete Änderungen in AGENTS.md, CLAUDE.md, Aktivierung,
Workflow, Scheduler und Board-README gehören zur gemeinsam gelieferten
Regelfassung. Ihre Autorenschaft wird nicht als reine Codex-Arbeit ausgegeben;
beide Erfahrungssammlungen wurden vor der Übergabe vollständig gelesen.
Andere vorbestehende Änderungen bleiben außerhalb der Übergabe erhalten.

[↑ Übersicht](#übersicht)

## Übergabeumfang · Runde 1

Prüfstand der gemeinsamen StockInfo-Regeln: `92d19ab`; die Nachweise dieses
Abschnitts werden zusätzlich als Ticketdokumentation gesichert.
PersonalSkills-Prüfstand: `eeaad8c2979b6dd1d5cd470b3a0349cb7dd2be1b`.

| Wert | geplant | gemessen bis `92d19ab` |
|---|---:|---:|
| Fachliche Änderungen | 1 | 1: Ablage mit Regeln und Verweisen |
| Produkt-/aktive Skriptdateien | 2 | 1: ausschließlich TS-Kommentar |
| Test-/Dokudateien einschließlich Verschiebungen, beide Repos | 110 | 117 |
| Inhalts-Diff-Zeilen, beide Repos | 2.500 | 2.317 |

59 StockInfo-Dateien tragen Inhaltsänderungen, weitere 56 sind reine
Verschiebungen. Dazu kommen drei Skill-Dateien. Die 117 Test-/Dokudateien
liegen 6,4 % über der Schätzung: zusätzliche relative Archivlinks wurden beim
vollständigen Linkabgleich sichtbar. Keine zusätzliche Produktschicht;
unterhalb der 25-%-Schwelle des Scope-Vertrags. Die Ticket- und Mailbox-
Ergänzungen der Übergabe werden vor deren Commit zusätzlich mitgezählt.

Der Codex-Scheduler wurde nach Beenden der alten Zelle als Zelle 363 neu
angelegt. `scheduler_started` am 2026-09-09 um 14:43:46 UTC bestätigt den
Start mit `_tickets/30-doing` als aktivem Verzeichnis. Ein regulärer
Heartbeat ist davon getrennt; erst dieser belegt den fortgesetzten Takt.

[↑ Übersicht](#übersicht)
