# Codex-In-Context-Scheduler

Dies ist ausschließlich der kurze Laufzeitvertrag für den internen Scheduler
des bestehenden Codex-Review-Chats. Das fachliche Review-Verfahren steht in
`CODEX-REVIEW-AUTOMATION.md`.

## Vertrag

- Mechanismus: interner In-Context-Scheduler dieses Chats; kein `/goal`, kein
  ChatGPT-Scheduled-Task und keine Desktop-App-Automation.
- Takt: exakt alle fünf Minuten, beginnend fünf Minuten nach dem Start.
- Projekt: aktueller lokaler Checkout von StockInfo; kein anderer Worktree.
- Pro Tick: ausschließlich den maschinenlesbaren Zustand in `STATUS.md` lesen.
- Ist `phase` nicht `ready_for_codex`, endet der Tick still: keine Nachricht und
  keine Dateiänderung.
- Ist `phase` `ready_for_codex` und unterscheidet sich das Tupel aus `ticket`,
  `handoff_commit` und `review_round` vom letzten Review, wird derselbe Chat
  geweckt und führt `CODEX-REVIEW-AUTOMATION.md` aus.
- Bei einem Lesefehler oder ungültigen Zustandsformat wird Mike einmalig mit
  dem konkreten Fehler informiert.

## Wiederanlauf nach Exit oder Compaction

Der Vertrag überlebt in dieser Datei; der laufende Timer selbst überlebt nur
seine aktuelle Chat-Laufzeit. Nach einem Neustart genügt der Auftrag:

```text
Starte den In-Context-Scheduler aus
_tickets/CODEX-IN-CONTEXT-SCHEDULER.md.
```
