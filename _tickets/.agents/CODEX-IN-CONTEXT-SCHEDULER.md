# Codex-In-Context-Scheduler

Dies ist ausschließlich der kurze Laufzeitvertrag für den internen Scheduler
des bestehenden Codex-Arbeits-Chats. Das fachliche Review-Verfahren steht in
`CODEX-REVIEW-AUTOMATION.md`.

## Vertrag

**Der Scheduler folgt seit Mikes Auftrag vom 2026-09-07 der aktuellen Rolle.**
Bei `reviewer: codex` gelten die Review-Trigger unten. Bei `implementer: codex`
weckt er denselben Arbeits-Chat für `codex_working`, `changes_requested` und
`approved`, ausschließlich mit `owner: codex`, gültigem Prioritätsticket und
konsistenter Rollenverteilung. `coder_handoff` enthält Phase und Übergabetupel;
dieselbe unveränderte Kombination wird innerhalb eines Laufs nur einmal
signalisiert. Nach Wiederanlauf liest Codex den dauerhaften Arbeitsstand und
setzt ihn fort; `approved` ist kein Auftrag zur erneuten Implementierung,
sondern zur Verarbeitung der Freigabe und zum nächsten Kettenglied.

Der Timer selbst implementiert und reviewed nichts. Vor der fachlichen Arbeit
liest der Chat den Zustand erneut. Während einer laufenden Implementierung
ist ein Heartbeat kein paralleler Arbeitsauftrag. Bei Owner Claude bleibt
Codex still. Fehlende oder widersprüchliche Rollenfelder sind ein Zustandsfehler.
Ein Rollenwechsel startet keinen Scheduler automatisch.

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
  Neben dem Review-Tupel sind `workstream`, `priority_chain` und
  `priority_ticket` Teil dieses Zustands.
- **Jeder** Tick sendet unabhängig von der Phase einen knappen internen
  `scheduler_heartbeat` mit Zeitstempel, Phase und Zustands-Tupel über
  `notify(...)` und ruft danach `yield_control()` auf. Erst dieses Signal
  beweist, dass die Zelle den Chat weiterhin wecken kann. Der Heartbeat erzeugt
  keine Nachricht an Mike und keine Dateiänderung.
- Für die Verifier-Rolle gilt: Ist `phase` weder `ready_for_codex` noch
  `scope_checkpoint`, endet die fachliche Verarbeitung nach dem Heartbeat still.
- Vor jedem fachlichen Auftrag (auch `coder_handoff`) muss `ticket` eine vorhandene Datei direkt
  im Board-Root bezeichnen. Tickets in `postponed/`, `rejected/` oder
  `solved/` lösen keinen Auftrag aus; bei veralteter Priorität einmalig
  `portfolio_mismatch` melden. Diese Dateiprüfung erfolgt nur bei einem
  ansonsten fälligen Auftrag, nicht bei jedem Leerdurchlauf.
- Ist `phase` `scope_checkpoint`, müssen `owner: codex`, ein gesetzter
  `handoff_commit`, `ticket == priority_ticket` und die Mitgliedschaft in
  `priority_chain` gelten. Ein neues Tupel aus `phase`, `ticket`,
  `handoff_commit` und `review_round` weckt denselben Chat mit
  `scope_handoff`. Codex führt dann ausschließlich den Scope-Checkpoint aus
  `CODEX-REVIEW-AUTOMATION.md` aus — kein vollständiges Review.
- Ist `phase` `ready_for_codex`, müssen vor einem Review **alle** folgenden
  Bedingungen gelten: `owner` ist `codex`, `handoff_commit` ist gesetzt,
  `ticket` entspricht exakt `priority_ticket`, und `priority_ticket` kommt in
  `priority_chain` vor. Erst wenn sich zusätzlich das Tupel aus `ticket`,
  `handoff_commit` und `review_round` vom letzten Review unterscheidet, wird
  derselbe Chat mit einem eindeutigen `review_handoff` per `notify(...)`
  geweckt und führt `CODEX-REVIEW-AUTOMATION.md` aus.
- Verletzt ein `ready_for_codex`-Zustand diesen Prioritätsriegel, findet
  **kein Review** statt. Die Zelle sendet einmalig `portfolio_mismatch` mit
  Ticket, erwartetem `priority_ticket` und Kette. Derselbe unveränderte
  Fehlzustand wird nicht alle fünf Minuten erneut gemeldet. So kann ein
  technisch lebender Scheduler nicht mehr dauerhaft das falsche Arbeitspaket
  optimieren.
- Die Deduplizierung darf nicht nur im Arbeitsspeicher der Zelle leben. Beim
  Start und nach jedem Wiederanlauf werden `last_reviewed_ticket`,
  `last_reviewed_commit` und `last_reviewed_round` aus `STATUS.md` als
  persistente Vergleichsbasis verwendet.
- Bei einem Lesefehler oder ungültigen Zustandsformat wird Mike einmalig mit
  dem konkreten Fehler informiert. Derselbe unveränderte Fehler wird nicht bei
  jedem Heartbeat wiederholt; nach einer Erholung darf ein neuer Fehler wieder
  gemeldet werden.

## Gesundheits- und Wiederanlaufregeln

- **Der steuernde Codex-Turn bleibt offen.** `notify(...)` und
  `yield_control()` geben nur innerhalb eines noch aktiven Turns wieder
  Kontrolle an Codex. Nach einer Final-Antwort startet ein späterer
  `review_handoff` keinen neuen Assistenten-Turn; er wird erst mit der nächsten
  Benutzernachricht zugestellt. Wer den Scheduler als laufende Überwachung
  startet, wartet deshalb nach dem Yield mit `functions.wait` auf derselben
  Cell-ID weiter und sendet bis zum Ende der Überwachung **keine**
  Final-Antwort.
- `scheduler_started` belegt nur den Start. Erst ein regulärer Heartbeat und
  anschließend das fortgesetzte Warten der steuernden Unterhaltung belegen
  die funktionsfähige Überwachung. Eine nach dem Start beendete Unterhaltung
  ist kein laufender Scheduler, auch wenn die Zelle später noch als
  `Script running` erscheint.
- Ein Scheduler ist gesund, wenn seit höchstens fünf Minuten und einer kleinen
  Laufzeittoleranz ein `scheduler_heartbeat` eingetroffen ist. `Script running`
  ohne Heartbeat ist ausdrücklich ein Defekt.
- Liefert die Scheduler-Zelle ein Completion-, Fehler- oder Abbruchresultat,
  wird sie sofort einmal neu gestartet. Der alte Cell-Identifier darf danach
  nicht weiterverwendet werden.
- Bleibt der erwartete Heartbeat aus und der Chat erhält wieder Kontrolle, wird
  die alte Zelle beendet und einmal neu gestartet. Mike wird nur informiert,
  wenn auch dieser Wiederanlauf kein `scheduler_started` liefert.
- Ein Heartbeat oder Wiederanlauf darf niemals selbst ein Review oder einen
  Scope-Entscheid auslösen. Ausschlaggebend bleibt ausschließlich ein neues,
  valides `ready_for_codex`- beziehungsweise `scope_checkpoint`-Tupel; ein
  vollständiges Review startet weiterhin nur bei `ready_for_codex`.
- `max_review_rounds` allein stoppt den Scheduler nicht und wechselt keinen
  Owner. Bei tatsächlicher Arbeit gilt die gemeinsame
  [Rundenlimit-Regel](CODEX-REVIEW-AUTOMATION.md#rundenlimit-rest-offenlegen-und-abschließen):
  Rest und Ursache im Ticket offenlegen, Selbstheilung nutzen, Blocker vor
  Folgearbeit beheben und gezielt nachprüfen. Der Timer entscheidet darüber
  nicht selbst und setzt keine Runde zurück.
- Ein neues Ticket darf nicht aus der Nummernfolge oder aus einer während des
  Reviews entdeckten Nebenarbeit abgeleitet werden. Maßgeblich ist allein
  `priority_ticket`. Nach dem letzten Element einer Kette bleibt der Scheduler
  still, bis die Portfolio-Einordnung in `STATUS.md` ausdrücklich geändert
  wurde.
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
