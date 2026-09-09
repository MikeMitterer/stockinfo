# Agenten aktivieren · laufzeitspezifische Syntax

**Die Rolle steht ausschließlich in [STATUS.md](../STATUS.md).** Der fachliche
Vertrag spricht von Coder und Verifier. Diese Datei nennt konkrete Laufzeiten,
weil deren Startmechanismen verschieden sind. Ein `/loop`-Befehl wird im
entsprechenden Chat eingegeben; er ist kein Terminalbefehl.

| Laufzeit | Aktivierung | Rollenwahl |
|---|---|---|
| Codex | In-Context-Scheduler des bestehenden Chats | Aus `implementer`, `reviewer` und `owner` |
| Claude | `/loop` im bestehenden Arbeits-Chat | Aus denselben Rollenfeldern |

Eine Anweisung in einem Agentenchat steuert nicht automatisch eine andere
Laufzeit. Die Änderung der Rollenfelder startet weder einen Timer noch eine
zweite Instanz. Konkrete Fähigkeiten und Grenzen bleiben im jeweiligen
Laufzeitvertrag; es gibt keinen zweiten fachlichen Workflow je Laufzeit.

## Trigger für den Codex-In-Context-Scheduler

**Beide Laufzeiten folgen der aktuellen Rolle.** Der Codex-Scheduler nimmt
seit Mikes Auftrag vom 2026-09-07 auch fällige Coder-Arbeit im bestehenden
Arbeits-Chat auf. Der Claude-Loop unten unterstützt ebenfalls beide Rollen.

Der Scheduler enthält keine Kopie des Review-Verfahrens. Sein vollständiger
Auftrag ist:

```text
Führe _tickets/.agents/CODEX-IN-CONTEXT-SCHEDULER.md aus.
```

Erst bei einem fälligen Auftrag lädt die Instanz den fachlichen Vertrag aus
`AGENT-WORKFLOW.md` und die nötigen Review-Muster.
Damit kosten Leerdurchläufe nur den Zustandscheck; die ausführlichen Regeln
bleiben trotzdem versioniert und überstehen Exit sowie Compaction.

## Prompt für den periodischen Claude-Loop

Claude prüft im selben Takt, ob ein Auftrag für seine aktuelle Rolle vorliegt.
Als Verifier wartet die Instanz auf eine Übergabe, als Coder auf den
jeweils fälligen Arbeitsschritt. Als `/loop` **im laufenden Arbeits-Chat**
starten, damit derselbe Branch und dasselbe `STATUS.md` gesehen werden. Beim
Ausstieg wird der Loop gelöscht; dieser Abschnitt hält ihn wiederherstellbar.

**Im laufenden Claude-Chat einfügen — den gesamten folgenden Block kopieren:**

```text
/loop 5m Du bist die Claude-Instanz im StockInfo-Board. Deine Rolle ist nicht fest vorgegeben.

1. Lies zuerst nur den maschinenlesbaren Zustand in _tickets/STATUS.md: implementer, reviewer, owner, phase, ticket, priority_ticket, priority_chain und das Übergabetupel. Fehlt eine eindeutige Zuordnung oder widersprechen sich Rolle, Owner und Phase, melde den Konflikt und ändere nichts. Ist owner nicht claude, beende den Durchlauf mit einer Statuszeile.
2. Beachte CLAUDE.md. Lies bei tatsächlicher Arbeit _tickets/.agents/AGENT-WORKFLOW.md, die zur Autorenschaft passende Mustersammlung (_tickets/.agents/CODEX-LESSONS.md für Codex-Arbeit, _tickets/.agents/CLAUDE-LESSONS.md für Claude-Arbeit; bei gemischter Autorenschaft beide) und das aktive Ticket. ticket muss als Datei direkt im Board-Root liegen, priority_ticket entsprechen und in priority_chain stehen; sonst portfolio_mismatch melden und stoppen.
3. Wenn reviewer claude ist, bearbeite ausschließlich eine neue ready_for_claude-Übergabe oder einen an dich gerichteten scope_checkpoint. Setze beim Review claude_reviewing und führe den vollständigen Reviewvertrag aus. Nach approved oder changes_requested geht owner an den implementer zurück. Keine Implementierung aus einer Verifier-Zuordnung ableiten.
4. Wenn implementer claude ist, führe nur den für den Coder vorgesehenen Schritt aus. Scope-, Testinfrastruktur-, Vertical-Acceptance-, DRY- und Konvergenzregeln gelten unverändert. Bei Übergabe den vollständigen Bericht vor Phase und Owner schreiben; Empfänger ist der aktuell zugeordnete Verifier. Nach Freigabe nur entlang der bestehenden Prioritätskette fortsetzen.
   Beachte max_review_rounds nach dem gemeinsamen Reviewvertrag: Am Limit Rest und Ursache im Ticket dokumentieren, Selbstheilung nutzen und Blocker gezielt am aktuellen Ticket lösen. Keine automatische Übergabe an Mike allein wegen der Rundenzahl; mit offenem Blocker keine Folgearbeit und kein solved.
5. Bei menschlichem Entscheidungsbedarf Arbeit erhalten, owner mike setzen und den Loop stoppen. Melde nur Übergabe, Scope-Checkpoint, Blocker oder Entscheidungsbedarf; Leerdurchläufe bleiben einzeilig. Ein Rollenwechsel setzt keine Review-Runde zurück und erzeugt keine neue Freigabe.
```

Beide Loops teilen sich denselben Zustandsfilter: Genau einer von beiden ist
über `owner` je Runde am Zug, der andere beendet seinen Lauf einzeilig. Läuft
nur ein Agent, bleibt der andere Takt wirkungslos, aber ungefährlich.
