# Codex-In-Context-Scheduler

Dies ist ausschließlich der kurze Laufzeitvertrag für den internen Scheduler
des bestehenden Codex-Review-Chats. Das fachliche Review-Verfahren steht in
`CODEX-REVIEW-AUTOMATION.md`.

## Vertrag

- Mechanismus: interner In-Context-Scheduler dieses Chats; kein `/goal`, kein
  ChatGPT-Scheduled-Task und keine Desktop-App-Automation.
- Laufzeit: eine dauerhaft laufende `functions.exec`-Zelle. Der beim Start
  zurückgegebene Cell-Identifier wird im Chat festgehalten. Eine Zelle gilt
  **nicht** allein deshalb als gesund, weil sie weiterhin `Script running`
  meldet.
- Startprüfung: unmittelbar nach dem Start sendet die Zelle ein internes
  `scheduler_started` per `notify(...)` und gibt die Kontrolle mit
  `yield_control()` an den Chat zurück. Fehlt dieses Signal, wird die Zelle
  beendet und einmal neu gestartet.
- Takt: exakt alle fünf Minuten, der erste reguläre Tick fünf Minuten nach dem
  Start. Der nächste Termin wird aus dem vorher geplanten Termin berechnet
  (`next_tick += 300000`) und nicht aus dem Ende des letzten Durchlaufs. Nach
  einer Verzögerung werden verpasste Termine übersprungen; es gibt weder Drift
  noch eine Folge sofortiger Nachhol-Ticks.
- Projekt: aktueller lokaler Checkout von StockInfo; kein anderer Worktree.
- Pro Tick: ausschließlich den maschinenlesbaren Zustand in `STATUS.md` lesen.
- **Jeder** Tick sendet unabhängig von der Phase einen knappen internen
  `scheduler_heartbeat` mit Zeitstempel, Phase und Zustands-Tupel über
  `notify(...)` und ruft danach `yield_control()` auf. Erst dieses Signal
  beweist, dass die Zelle den Chat weiterhin wecken kann. Der Heartbeat erzeugt
  keine Nachricht an Mike und keine Dateiänderung.
- Ist `phase` nicht `ready_for_codex`, endet die fachliche Verarbeitung nach
  dem Heartbeat still.
- Ist `phase` `ready_for_codex` und unterscheidet sich das Tupel aus `ticket`,
  `handoff_commit` und `review_round` vom letzten Review, wird derselbe Chat
  zusätzlich mit einem eindeutigen `review_handoff` per `notify(...)` geweckt
  und führt `CODEX-REVIEW-AUTOMATION.md` aus.
- Die Deduplizierung darf nicht nur im Arbeitsspeicher der Zelle leben. Beim
  Start und nach jedem Wiederanlauf werden `last_reviewed_ticket`,
  `last_reviewed_commit` und `last_reviewed_round` aus `STATUS.md` als
  persistente Vergleichsbasis verwendet.
- Bei einem Lesefehler oder ungültigen Zustandsformat wird Mike einmalig mit
  dem konkreten Fehler informiert. Derselbe unveränderte Fehler wird nicht bei
  jedem Heartbeat wiederholt; nach einer Erholung darf ein neuer Fehler wieder
  gemeldet werden.

## Gesundheits- und Wiederanlaufregeln

- Ein Scheduler ist gesund, wenn seit höchstens fünf Minuten und einer kleinen
  Laufzeittoleranz ein `scheduler_heartbeat` eingetroffen ist. `Script running`
  ohne Heartbeat ist ausdrücklich ein Defekt.
- Liefert die Scheduler-Zelle ein Completion-, Fehler- oder Abbruchresultat,
  wird sie sofort einmal neu gestartet. Der alte Cell-Identifier darf danach
  nicht weiterverwendet werden.
- Bleibt der erwartete Heartbeat aus und der Chat erhält wieder Kontrolle, wird
  die alte Zelle beendet und einmal neu gestartet. Mike wird nur informiert,
  wenn auch dieser Wiederanlauf kein `scheduler_started` liefert.
- Ein Heartbeat oder Wiederanlauf darf niemals selbst ein Review auslösen.
  Ausschlaggebend bleibt ausschließlich ein neues, valides
  `ready_for_codex`-Tupel.
- Bevor eine Ersatz-Zelle gestartet wird, wird eine noch bekannte alte Zelle
  beendet. Es dürfen nicht zwei Scheduler gleichzeitig dasselbe Tupel
  verarbeiten.

## Wiederanlauf nach Exit oder Compaction

Der Vertrag überlebt in dieser Datei; der laufende Timer selbst überlebt nur
seine aktuelle Chat-Laufzeit. Nach Exit oder Compaction wird deshalb stets eine
neue Zelle nach den Startprüfungs- und Deduplizierungsregeln oben erzeugt. Dazu
genügt der Auftrag:

```text
Starte den In-Context-Scheduler aus
_tickets/CODEX-IN-CONTEXT-SCHEDULER.md.
```
