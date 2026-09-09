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

Der Observer erhält einen eigenen Chat und Loop. Seine Einführung ist in
[T-69](../20-ready/T-69-observer-instanzen-und-loop.md) vorbereitet; die
[Observer-Aktivierung](#observer-aktivierung--vorbereitet-für-t-69) unten ist
noch keine Freigabe zum Start.

## Übersicht

- [Trigger für den Codex-In-Context-Scheduler](#trigger-für-den-codex-in-context-scheduler)
- [Prompt für den periodischen Claude-Loop](#prompt-für-den-periodischen-claude-loop)
- [Observer-Aktivierung · vorbereitet für T-69](#observer-aktivierung--vorbereitet-für-t-69)

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
`AGENT-WORKFLOW.md`, den Skill `code-standards` gemäß dessen
Standard-Riegel und die nötigen Review-Muster — unabhängig von ihrer Rolle.
Damit kosten Leerdurchläufe nur den Zustandscheck; die ausführlichen Regeln
bleiben trotzdem versioniert und überstehen Exit sowie Compaction.

[↑ Übersicht](#übersicht)

## Prompt für den periodischen Claude-Loop

Im bestehenden Claude-Arbeitschat des Projekts starten. Der Prompt verweist
auf einen einzelnen Durchlauf; er legt bei einem Tick keinen neuen Loop an.
Die Instanzkennung ist standardmäßig `claude`. Ein ausdrücklich vergebener
anderer Name bleibt erhalten und wird nicht durch den Standard ersetzt.

Vor dem Start die geplanten Jobs auflisten lassen. Läuft bereits derselbe
Board-Loop, keinen zweiten anlegen. Zum Ersetzen den bisherigen Job gezielt
löschen. Claude bestätigt beim Anlegen den Takt und die Job-ID.

```text
/loop 5m Lies _tickets/.agents/AGENT-ACTIVATION.md und führe einmal den Abschnitt „Claude-Durchlauf“ aus.
```

### Claude-Durchlauf

1. Lies zuerst nur den maschinenlesbaren Zustand aus `_tickets/STATUS.md`:
   Rollen, `owner`, `phase`, Ticket, Prioritätskette und Übergabetupel samt
   letztem Review. Vergleiche vollständige Instanzkennungen. Fehlt die eigene
   eindeutige Zuordnung oder widersprechen sich Rolle, Owner und Phase,
   melde den Konflikt und ändere nichts. Ist eine andere Instanz am Zug,
   endet dieser Durchlauf mit einer kurzen Statuszeile.
2. Prüfe bei eigenem Owner, ob ein Auftrag zur Rolle passt: als Verifier eine
   neue Review-Übergabe oder ein `scope_checkpoint`; als Coder die Arbeitsphase,
   `changes_requested` oder `approved`. Die Zuordnung der Phasen steht in
   `STATUS.md`. Eine Freigabe verarbeiten, nicht die Implementierung neu beginnen.
   Bereits abgeschlossene Reviews nicht wiederholen; dafür den letzten
   Review-Stand aus STATUS und den zugehörigen Nachweis im Ticket beachten.
3. Prüfe die [Ticketpfade](AGENT-WORKFLOW.md#ticketpfade-und-arbeitsbeginn):
   `_tickets/30-doing/<ticket>` muss existieren, `ticket` muss
   `priority_ticket` entsprechen und in `priority_chain` stehen.
   Andernfalls `portfolio_mismatch` melden und stoppen.
4. Beachte `CLAUDE.md` und lies das Ticket sowie den vollständigen
   [gemeinsamen Workflow](AGENT-WORKFLOW.md). Lade `code-standards`
   samt passenden Referenzen nach dessen Standard-Riegel und die zur
   Autorenschaft passende Mustersammlung. Führe ausschließlich den für deine
   Rolle fälligen Schritt aus. Übergabe, Rückgabe, Rundenlimit, Selbstheilung
   und Fortsetzung der Prioritätskette richten sich nach diesem Workflow.
5. Bei echtem menschlichem Entscheidungsbedarf den Arbeitsstand erhalten,
   nach Workflow an Mike übergeben und den eigenen Loop löschen. Melde sonst
   nur Übergabe, Scope-Checkpoint, Blocker oder Entscheidungsbedarf;
   Leerdurchläufe bleiben einzeilig. Ein Rollenwechsel setzt keine Runde
   zurück und erzeugt keine neue Freigabe.

### Claude-Loop beenden und fortsetzen

Zum Auflisten oder Löschen Claude im selben Chat anweisen, beispielsweise
„Liste meine geplanten Jobs auf“ und anschließend „Lösche Job …“ mit der
bestätigten ID. Dafür stehen `CronList` und `CronDelete` zur Verfügung.
Nur den eigenen Board-Job löschen.

`/loop 5m <Prompt>` ist die dokumentierte Syntax. Der Job läuft zwischen
Chat-Turns; ein beschäftigter Chat und der zeitliche Versatz des Schedulers
können einen Durchlauf verzögern. Fünf Minuten sind kein garantierter
Ausführungszeitpunkt. Ein gestarteter Job ist außerdem noch kein Nachweis,
dass Rollenwahl und fachlicher Durchlauf funktionieren.

Ein neuer Chat, auch nach `/clear`, führt den bisherigen Loop nicht fort.
Beim Fortsetzen der alten Sitzung über `--resume` oder `--continue` können
nicht abgelaufene Jobs wiederhergestellt werden. Deshalb vor einem Neustart
Kennung, Rollen und vorhandene Jobs prüfen. Wiederkehrende Jobs laufen laut
aktueller Dokumentation nach sieben Tagen ab.

Quelle: [Claude Code — geplante Aufgaben](https://code.claude.com/docs/en/scheduled-tasks).
Syntax und Laufzeitbeschreibung sind an der Dokumentation geprüft;
ein Live-Test des Board-Loops steht noch aus. Die Prüfung nach `/clear`
einschließlich Instanzkennung bleibt Teil von T-69.

[↑ Übersicht](#übersicht)

## Observer-Aktivierung · vorbereitet für T-69

**Erst nach Einführung der Rolle über T-69 verwenden.** Der Observer braucht
eine eigene Instanzkennung und einen eigenen Chat. Der Startauftrag benennt
die Kennung; der aktuelle Auftrag steht im Feld `observer` in `STATUS.md`.
Der Observer wartet nicht auf `owner` und übernimmt keine Coder-/Verifier-Arbeit.

Vorlage für den separaten Claude-Observer-Chat nach der Einführung:

```text
/loop 5m Deine Instanzkennung ist claude-observer. Lies _tickets/.agents/AGENT-ACTIVATION.md und führe einmal den Abschnitt „Observer-Durchlauf“ aus.
```

Es gelten dieselben Regeln für Job-ID, doppelte Jobs, Stoppen und Wiederanlauf
wie beim Claude-Arbeitsloop. Die Startskripte `claude-observer` und
`codex-observer` sind noch nicht eingerichtet.

Für Codex wird der vorhandene In-Context-Scheduler um einen eigenen
Observer-Auftrag ergänzt. Der aktuelle Vertrag unterstützt diese Rolle noch
nicht. Einen Claude-`/loop`-Befehl nicht in Codex übernehmen. Vor Einführung
des Kurzbefehls muss außerdem geprüft sein, ob die gestartete Codex-Laufzeit
den erforderlichen Scheduler bereitstellt; sonst einen passenden Startweg
festlegen und dokumentieren.

### Observer-Durchlauf

Der vorgesehene Ablauf und die Grenzen stehen bis zur Einführung in
[T-69](../20-ready/T-69-observer-instanzen-und-loop.md#eigener-observer-loop).
Bei Einführung werden sie in den gemeinsamen Workflow übernommen und hier
verlinkt. Dieser Abschnitt aktiviert die Rolle nicht vorzeitig. Solange der
gemeinsame Workflow den Observer nicht unterstützt, keine Beobachtung starten.
Nach Einführung gilt vor jedem Durchlauf: nur bei exakt passender
`observer`-Kennung beobachten, andernfalls den eigenen Loop beenden.

[↑ Übersicht](#übersicht)
