# T-28 · Abnahme durch Mike — grobe Tests am Ende

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo | sammelt | zu schätzen | Abnahme aus Nutzersicht, keine Detailprüfung | — |

**Löst:** Die Frage „ist das Ganze benutzbar geworden?" — einmal, am Ende, statt
Ticket für Ticket. Die `Human`-Spalte der Einzeltickets bleibt bis dahin leer.

**Hängt an:** allen Tickets der Plugin-Reihe. Wird abgearbeitet, wenn T-17 bis
T-27b durch sind.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Wie dieses Ticket zu lesen ist

Die Zeilen sind **grob**. Sie fragen nach dem, was jemand an der Oberfläche
sieht — nicht nach einzelnen Feldern, Zeitstempeln oder Codepfaden. Jede Zeile
soll sich in ein bis zwei Minuten am laufenden Stack beantworten lassen
(`make dev-up`, Backend `:8000`, Dashboard `:5173`), ohne dass jemand ein
Ticket nachlesen muss.

Die feine Prüfung ist an anderer Stelle schon passiert: Unit-Tests, die
Prüf-Scripts `T-NN-smoke.sh` und Codex' Review. Hier geht es um die Frage, ob
das Ergebnis im Alltag trägt.

Die `AI`-Spalte steht bewusst auf ➖ — diese Zeilen gehören dem Menschen. Wo
das Verhalten maschinell belegt ist, nennt die Fußnote das Ticket.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Ein europäisches Papier per ISIN aufnehmen (z.B. `IE00B4L5Y983`) | kommt an der erwarteten Börse in EUR herein, Kennzahlen sind gefüllt | ➖ [^t17] | |
| 2 | Dasselbe Papier später erneut ansehen | TER, Anbieter und Domizil stehen noch da — nichts ist über Nacht leer geworden | ➖ [^t17] | |
| 3 | Ein Papier aufnehmen, dessen ISIN nirgends auflösbar ist | die App sagt das verständlich, statt eine kaputte Zeile anzulegen | ➖ [^t17] | |
| 4 | Die Liste durchsehen, nachdem länger nichts angefasst wurde | keine Zeile trägt ein Symbol oder eine ISIN, die nicht zum Papier gehört | ➖ [^t17] | |

_(wächst mit jedem abgeschlossenen Ticket — je Ticket ein bis drei Zeilen,
nicht mehr)_

[^t17]: T-17 — Fehler im Antwortpfad. Maschineller Nachweis:
    `./_tickets/T-17-smoke.sh --run` (acht Checks) und
    `./_tickets/T-16-smoke.sh --run` (`#5c`), dazu zwölf Unit-Tests.

---

## Details

### Warum gesammelt statt einzeln

Eine Abnahme je Ticket würde denselben Handgriff zehnmal verlangen — ein Papier
aufnehmen, ansehen, aktualisieren — und jedes Mal in einer Zwischenversion, die
niemand behält. Am Ende zählt der Zustand, der bleibt.

Der Preis ist, dass ein Fehler länger unentdeckt bleiben kann. Dagegen stehen
die Prüf-Scripts und Codex' unabhängige Prüfung je Commit; sie fangen das ab,
was maschinell zu sehen ist. Was sie nicht beantworten, ist die Frage, ob sich
das Ergebnis richtig anfühlt — und die stellt sich sinnvoll nur einmal, am
fertigen Stand.

### Wann dieses Ticket dran ist

Wenn die Plugin-Reihe durch ist und der Stand auf `master` liegt. Vorher wächst
hier nur die Liste.

---

## Auflösung

_(offen)_
