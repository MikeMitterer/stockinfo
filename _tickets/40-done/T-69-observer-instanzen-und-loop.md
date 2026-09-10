# T-69 · Observer-Instanzen eindeutig starten und beobachten lassen

Zusätzliche Agenten sollen den Ticketablauf beobachten können, ohne die
Arbeit des Coders oder Verifiers zu übernehmen. Die Befehle
`codex-observer` und `claude-observer` sollen im jeweiligen Projekt starten
und die eigene Kennung auch beim Wiedereinstieg eindeutig machen.

**Abgeschlossen am 2026-09-10 durch Mike.** Die Rolle ist im Board vollständig
eingerichtet: `STATUS.md` führt das Feld `observer`, der gemeinsame Workflow
den fachlichen Vertrag, die Aktivierung Startweg und Durchlauf, der
Codex-Scheduler seinen eigenen Observer-Auftrag. Die Startbefehle sind
installiert. Was eingerichtet wurde, steht unter
[Eingerichtete Rolle](#eingerichtete-rolle--2026-09-10).

**Nicht praktisch geprüft.** Es wurde kein Observer zugeordnet und keiner
gestartet. Kennung nach `/clear`, durchgereichte Argumente, Exit-Code,
Arbeitsverzeichnis und ein laufender Beobachtungstakt sind unbelegt; die
Prüfmatrix weist das aus. Mike schließt das Ticket in diesem Zustand ab —
der erste echte Lauf ist die Probe.

Dieser Auftrag war der Observer-Teil aus T-68. Claude hat die getrennte
Lieferung mit `6177c76` beschlossen.

**Wenn du den Observer einsetzen willst:** `observer` in `STATUS.md` von
`unassigned` auf `claude-observer` beziehungsweise `codex-observer` setzen und
den gleichnamigen Befehl im Projektverzeichnis starten. Ohne passende
Zuordnung meldet der Agent den Konflikt und beginnt nichts.

## Übersicht

- [Vereinbarter Observer-Auftrag](#vereinbarter-observer-auftrag)
- [Lieferung und Grenzen](#lieferung-und-grenzen)
- [Eingerichtete Rolle · 2026-09-10](#eingerichtete-rolle--2026-09-10)
- [Prüfung](#prüfung)

## Vereinbarter Observer-Auftrag

Mike fragt nach einer dritten Rolle. Vorschlag: Ein optionaler Observer
beobachtet den Ablauf, den Ticketstand, den Doku-Abgleich und wiederkehrende
Probleme über mehrere Tickets hinweg. Coder und Verifier bleiben für Umsetzung
und technische Abnahme zuständig. Ein fehlender Observer hält keine Arbeit auf.

- Die Zuordnung erfolgt über ein optionales Feld `observer` in `STATUS.md`.
  Die dritte Instanz braucht eine eindeutige Kennung, auch wenn sie dasselbe
  Agentenprodukt wie Coder oder Verifier verwendet. Das gilt dann für alle
  Rollenfelder und die Aktivierungsanweisungen.
- Der Observer darf unabhängig vom aktuellen `owner` lesen. Er ändert weder
  Produktdateien noch Owner, Phase, Prioritäten, Freigaben oder Review-Zähler.
  Es gibt keine zusätzliche obligatorische Abnahmerunde.
- Beobachtungen nennen Ticket beziehungsweise geprüften Stand, Beleg,
  Auswirkung und einen konkreten Vorschlag. Zunächst berichtet der Observer
  auf Auftrag im eigenen Chat. Daraus werden bei Bedarf Ticketergänzungen
  durch die zuständige Instanz oder auf Mikes ausdrücklichen Auftrag.
  Kein paralleles Schreiben in die laufende Mailbox und kein zweites Board.
- Einen möglichen fachlichen Fehler meldet er als Hinweis an Mike; über
  einen technischen Befund und nötige Nacharbeit entscheidet der Verifier.
  Der Observer erteilt selbst keine Freigabe und startet keine Folgearbeit.
- Der Observer erhält einen eigenen Scheduler beziehungsweise Loop im eigenen
  Chat. Die frühere Beschränkung auf einzelne manuelle Aufträge entfällt.
  Start, Zustandsprüfung und Meldeweg sind unten beschrieben.

Dieser Abschnitt hält die Vereinbarung vom 2026-09-09 fest; der umgesetzte
Stand steht unter [Eingerichtete Rolle](#eingerichtete-rolle--2026-09-10).
Die Regeln liegen wie vereinbart im gemeinsamen Workflow, in der Aktivierung
und im Codex-Scheduler — keine eigene Workflow-Kopie für den Observer.
Der inhaltliche Schwerpunkt der Beobachtung bleibt offen und ergibt sich aus
dem ersten echten Lauf.

### Instanznamen · Vorgabe von Mike

Die Standardnamen bleiben `codex` und `claude`. Zusätzliche Instanzen
erhalten einen eindeutigen Zusatz, zum Beispiel `codex-observer` oder
`claude-observer`. Die zuvor vorgeschlagene Pflichtnummerierung entfällt.
Ein Name darf im selben Board nicht gleichzeitig zwei aktiven Instanzen
zugeordnet sein. Die Rolle steht weiterhin in `STATUS.md`; auch ein
Namenszusatz erteilt keine Berechtigung und ersetzt keine Rollenübergabe.

Der Startauftrag nennt bei zusätzlichen Instanzen die eigene Kennung
ausdrücklich. `owner` und Nachrichtenempfänger verwenden die vollständigen
Kennungen. Startprompts vergleichen sie exakt und behandeln nicht jede
Codex-Instanz als `codex` beziehungsweise jede Claude-Instanz als `claude`.

`/clear` beginnt in Codex CLI und Claude Code einen neuen Chat mit frischem
Kontext. Eine nur im Gespräch mitgeteilte Identität ist danach nicht
zuverlässig verfügbar. Die Zuordnung in `STATUS.md` bleibt bestehen, sagt
einem neuen Chat aber nicht, welche von mehreren Instanzen er selbst ist.
Bei mehreren Instanzen desselben Produkts darf er das nicht erraten oder
ohne Prüfung den Standardnamen übernehmen.

Einfacher Wiedereinstieg: Nach `/clear` ausdrücklich angeben:
„Du bist `codex-observer`. Lies deine Rolle und den Arbeitsstand aus
`_tickets/STATUS.md`.“ Die Kennung kann damit nach dem Kontextwechsel
weiterverwendet werden. Eine automatische Wiederherstellung würde eine
instanzbezogene Startkonfiguration benötigen, die den Namen erneut mitgibt;
eine von allen Chats gelesene Projektdatei allein reicht dafür nicht.
Ein solcher Mechanismus ist bislang weder umgesetzt noch geprüft.

Mike fragt nach der Übergabe über ein Kommandozeilenargument. Die lokale
CLI-Hilfe wurde geprüft: Codex 0.153.4 unterstützt `-c`, Claude Code 2.1.236
unterstützt `--name` und `--append-system-prompt`. Für die Instanzkennung
kommen folgende Aufrufe infrage:

```bash
codex -c 'developer_instructions="Deine Instanzkennung ist codex-observer. Lies deine Rolle aus _tickets/STATUS.md."'

claude --name claude-observer \
  --append-system-prompt 'Deine Instanzkennung ist claude-observer. Lies deine Rolle aus _tickets/STATUS.md.'
```

Claudes `--name` setzt den Anzeigenamen; die zusätzliche Anweisung macht die
Kennung für die Rollenwahl verfügbar. Codex bietet in der geprüften CLI-Hilfe
kein entsprechendes `--name`; `developer_instructions` ist ein dokumentierter
Konfigurationswert. Beim späteren Einrichten vorhandene zusätzliche
Anweisungen erhalten: `-c` überschreibt den jeweiligen Konfigurationswert.
Diese Aufrufe wurden nicht gestartet. Die Wiederherstellung der Kennung nach
`/clear` muss vor einer Zusage in beiden verwendeten CLIs praktisch geprüft
werden; die Hilfe allein belegt diesen Ablauf nicht.

Referenzen: [Codex-Konfiguration](https://developers.openai.com/codex/config-reference),
[Claude-CLI](https://code.claude.com/docs/en/cli-reference).

Quellen für das Verhalten von `/clear`:
[Codex CLI](https://developers.openai.com/codex/cli/slash-commands),
[Claude Code](https://code.claude.com/docs/en/commands).
Die bestehende Arbeitskette wird während ihrer Ausführung nicht umbenannt.

### Kurzbefehle für Bash und Zsh

Mike bestätigt den Start mit Instanzkennung und möchte die Einrichtung im
Ticket vormerken. Gewünschte Aufrufe aus dem jeweiligen Projektverzeichnis:

```bash
claude-observer
codex-observer
```

Technischer Vorschlag: Zwei kleine ausführbare Startskripte in einem
persönlichen Verzeichnis im `PATH`, zum Beispiel `~/.local/bin/`. Damit
funktionieren dieselben Befehle in Bash und Zsh. Die Skripte verwenden die
oben beschriebenen CLI-Argumente und starten die jeweilige CLI mit `exec`.
Zusätzliche Argumente werden mit `"$@"` unverändert weitergereicht.
Das aktuelle Projektverzeichnis bleibt erhalten; kein fest eingebauter
StockInfo-Pfad. Die Standardbefehle `claude` und `codex` bleiben unverändert.

Die Kennung wird beim Start mitgegeben; die Rolle wird weiter aus der
`STATUS.md` des Projekts gelesen. Der Aufruf trägt den Observer nicht selbst
ins Board ein und ändert keine laufende Rollenverteilung. Bereits vorhandene
zusätzliche CLI-Anweisungen müssen beim Einrichten erhalten bleiben.

Die Startanleitung steht in `.agents/AGENT-ACTIVATION.md`; der Ticket-Skill
erklärt die Zuordnung über die Instanzkennung. Der Vorschlag von zwei eigenen
Startskripten ist überholt: Es gibt ein gemeinsames Basis-Script mit acht
Symlinks, geliefert vom Ticket-Skill. Shell-Startdateien wurden nicht geändert.

### Eigener Observer-Loop

Der Observer läuft in einer eigenen Instanz mit eigenem Takt. Er wartet nicht
darauf, `owner` zu werden. Vor jedem Durchlauf prüft er, ob seine vollständige
Kennung weiterhin im Feld `observer` steht. Fehlt die Zuordnung, ist sie
widersprüchlich oder wurde sie geändert, beendet er die Beobachtung.
Er übernimmt dabei keine andere Rolle.

Als Startwert wird ein Abstand von fünf Minuten vorgeschlagen. Zuerst prüft
er knapp, ob sich seit dem letzten Durchlauf relevante Dateien, der
Arbeitsstand oder eine vereinbarte Frist geändert haben. Nur dann liest er
die betroffenen Inhalte genauer. Ein unveränderter Stand führt nicht zu
einem neuen vollständigen Review. Meldungen im eigenen Chat beschränken sich
auf neue Beobachtungen oder eine geänderte Bedeutung bereits gemeldeter Punkte.
Bloßes Verstreichen eines Takts belegt keinen Stillstand.

`claude-observer` beziehungsweise `codex-observer` sollen nach erfolgreicher
Zuordnungsprüfung die passende Beobachtung starten. Der jeweilige
Startmechanismus wird in `../.agents/AGENT-ACTIVATION.md` dokumentiert und praktisch
geprüft. Die fachlichen Observer-Regeln stehen einmal im gemeinsamen Workflow.
Es wird kein zweiter Coder-/Verifier-Ablauf kopiert.

Stoppen, `/clear` und Wiederanlauf gehören zur Prüfung: Es darf kein alter
Loop unter verlorener Kennung weiterarbeiten und kein doppelter Loop entstehen.
Falls die Laufzeit nach `/clear` einen erneuten Start verlangt, wird dieser
ausdrücklich dokumentiert. Ein beendeter Observer blockiert weder Umsetzung
noch Freigabe. Der Ablauf steht jetzt als
[Observer-Durchlauf](../.agents/AGENT-ACTIVATION.md#observer-durchlauf) in der
Aktivierung; gelaufen ist er noch nicht.

[↑ Übersicht](#übersicht)

## Lieferung und Grenzen

Die gemeinsamen Rollenregeln gehören in den Workflow, die konkrete
Startsyntax in die Aktivierung und die allgemeine Zuordnung in den Ticket-Skill.
Keine zweite Workflow-Kopie. Codex CLI und der Scheduler dieses App-Chats
werden nur gleichgesetzt, wenn die tatsächliche Ausstattung das belegt.

Startskripte in einem persönlichen PATH-Verzeichnis werden zuerst als
prüfbarer Diff vorbereitet. Bestehende CLI-Zusatzanweisungen, Standardbefehle,
Arbeitsverzeichnis, Argumente und Exit-Code bleiben erhalten. Keine Observer-
Zuordnung in einem realen Board ohne ausdrücklichen Auftrag eintragen.

[↑ Übersicht](#übersicht)

## Eingerichtete Rolle · 2026-09-10

Vier Lücken standen einem Einsatz im Weg. Sie sind geschlossen.

| Datei | Was fehlte | Was jetzt drinsteht |
|---|---|---|
| `.agents/AGENT-ACTIVATION.md` | „Erst nach Einführung der Rolle über T-69 verwenden“ — ein gestarteter Observer wäre daran stehengeblieben | Abschnitt „Observer-Aktivierung“ ohne Sperre; gestartet wird nach `observer`-Zuordnung |
| `.agents/AGENT-ACTIVATION.md` | „Solange der gemeinsame Workflow den Observer nicht unterstützt, keine Beobachtung starten“ — die Bedingung war erfüllt, der Satz sperrte weiter | entfallen; der Workflow trägt den Vertrag seit dem Board-Abgleich |
| `.agents/AGENT-ACTIVATION.md` | Abschnitt „Observer-Durchlauf“ ohne ausführbaren Inhalt, obwohl der Loop-Prompt genau ihn aufruft | fünf nummerierte Schritte: Zuordnung, Änderungserkennung, genaues Lesen, Bericht, Schreibverbot |
| `.agents/CODEX-IN-CONTEXT-SCHEDULER.md` | kein Observer-Trigger; `codex-observer` bekommt vom Startbefehl aber genau diesen Scheduler genannt | Abschnitt „Observer-Auftrag“: eigene Zelle, Zuordnungsprüfung je Tick, kein Review-/Coder-Trigger, kein Schreiben |

Dazu die überholte Angabe zu den Startbefehlen: Beschrieben waren
`agent-session` und sechs Symlinks, installiert sind `agent-session.sh`, die
Farbdatei `.agent-session.conf.sh` und acht Symlinks samt `codex-neutral`
und `claude-neutral`.

Die Rollenpflicht des Observers an den Mustersammlungen steht bewusst nur im
gemeinsamen Workflow. Die Köpfe von `CLAUDE-LESSONS.md` und `CODEX-LESSONS.md`
nennen weiterhin nur Coder und Verifier als Leser; eine zweite Regelkopie
wurde vermieden.

Doku-Abgleich: `.agents/AGENT-ACTIVATION.md`, `.agents/CODEX-IN-CONTEXT-SCHEDULER.md`
und der Observer-Abschnitt in `.agents/AGENT-WORKFLOW.md` angepasst.
`STATUS.md` führt das Feld bereits seit dem Board-Abgleich. 293 lokale
Markdown-Links samt Ankern geprüft, keine Befunde.

[↑ Übersicht](#übersicht)

## Prüfung

Die Prüfpunkte stammen unverändert im Umfang aus T-68 #7–10; hier #1–4.
**Keiner davon ist durch einen Lauf belegt.** Mike hat das Ticket am
2026-09-10 in diesem Zustand abgeschlossen; die Punkte sind damit nicht
erfüllt, sondern bewusst offen geblieben.

| # | Erwartetes Ergebnis | AI |
|---|---|:--:|
| 1 | `claude-observer` und `codex-observer` sind in Bash und Zsh aufrufbar; Projektverzeichnis, zusätzliche Argumente und Exit-Code bleiben erhalten; Standardbefehle sind unverändert | ◑ [^t69-1] |
| 2 | Beide Observer-Starts erhalten die richtige Kennung und lesen ihre Rolle aus STATUS; ein paralleler Standardagent behält seine eigene Kennung; der Start verändert keine Rollenzuordnung | ➖ [^t69-2] |
| 3 | Nach `/clear` ist die Kennung in beiden verwendeten CLIs erneut verfügbar und die aktuelle Rolle wird neu gelesen; andernfalls vor Einführung einen geprüften Wiedereinstieg einrichten und dokumentieren | ➖ [^t69-3] |
| 4 | Der Observer-Loop liest unabhängig vom Owner, arbeitet nur bei passender Observer-Zuordnung und meldet unveränderte Beobachtungen nicht wiederholt; Stoppen, Rollenwechsel, `/clear` und Wiederanlauf erzeugen weder fremde Rollenarbeit noch doppelte Loops | ➖ [^t69-4] |

[^t69-1]: Nur Bestand und Auffindbarkeit: `command -v claude-observer codex-observer agent-session.sh` liefert in Bash- und Zsh-Login-Shell die acht Symlinks auf `~/.local/bin/agent-session.sh`. Arbeitsverzeichnis, durchgereichte Argumente und Exit-Code wurden nicht gemessen.
[^t69-2]: Kein Start. Gelesen wurde nur der Quelltext von `agent-session.sh`: Er setzt `IDENTITY="${CLI}-observer"`, gibt den Rollenauftrag samt Zuordnungsprüfung als Prompt mit und schreibt selbst nichts ins Board. Eine Codelesung ist kein Lauf.
[^t69-3]: Kein `/clear`-Versuch in einer der beiden CLIs.
[^t69-4]: Der Vertrag steht jetzt im Workflow, der Ablauf in der Aktivierung und der Codex-Trigger im Scheduler. Ein Beobachtungstakt lief nie; Stoppen, Rollenwechsel und Wiederanlauf sind unbelegt.

[↑ Übersicht](#übersicht)
