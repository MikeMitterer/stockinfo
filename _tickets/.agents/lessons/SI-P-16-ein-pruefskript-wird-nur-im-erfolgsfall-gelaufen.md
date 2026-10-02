---
schema_version: 1
id: SI-P-16
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- tests
- handoff
subject_author: claude
discovered_by: codex
recorded_by: claude-observer
structured_by: claude-observer
prevention_roles:
- implementer
- reviewer
evidence:
- ticket: T-97
  round: 1
  reviewed_commit: 780abf3
  result_commit: 734917d
  finding: B1
- ticket: T-97
  round: 1
  reviewed_commit: 780abf3
  result_commit: 734917d
  finding: B3
- ticket: T-97
  round: 2
  reviewed_commit: e2c5f4e
  result_commit: 3cf6348
  finding: B6
- human: "Erstelle dazu noch eine Lesson (Mike, 2026-10-02)"
---

# SI-P-16 · Ein Prüfskript wird nur im Erfolgsfall gelaufen

**Implementer-Regel:** Ein neues oder geändertes Prüfskript (Vergleich,
Grenzwächter, Browserlauf) gilt erst als fertig, wenn **jeder Fehlerfall
einmal absichtlich rot** gelaufen ist und der Prozess dabei mit Exit-Code
≠ 0 endet. Das Ticket nennt je Fehlerfall den eingebauten Fehler und den
beobachteten Exit-Code. Ausnahmen gelten nur für einen geprüften Wert, nie
für einen Feld- oder Funktionsnamen.

**Verifier-Prüfung:** Den grünen Lauf nicht als Beleg für das Skript nehmen.
Für jede Ergebnisart (Befund, falsche Änderung, roter Teilschritt,
fehlgeschlagener Aufruf) einen eigenen Fehler einbauen und den Prozess-Exit
prüfen. Besonders prüfen: Kann ein Ausfall dasselbe Ergebnis erzeugen wie
der erwartete Erfolg?

## Originalbelege und Einordnung

**Erkennungsregel:** Ein Prüfskript läuft im Positivfall grün, und die
Übergabe belegt genau diesen Lauf. Die Fehlerpfade werden nur gelesen oder
per `print` gemeldet, aber nicht bis zum Prozess-Exit erprobt. Typisch sind
drei Formen:

1. Ein Befund wird ausgegeben, das Skript endet trotzdem mit Exit 0.
2. Eine Ausnahme („erwarteter Unterschied“) greift nach Name statt Wert.
3. Ein Ausfall erzeugt zufällig das erwartete Ergebnis, etwa „nichts
   geändert“ nach einem gescheiterten Aufruf.

**Prüffrage:** Welche Fehler soll das Skript melden? Wurde jeder davon
einmal eingebaut und endete der Prozess dann mit Exit ≠ 0? Gibt es einen
Ausfall, der wie der Erfolg aussieht?

**Belege (Befunde von Codex als Verifier, Fassungen von Claude als Coder):**

| Ticket · Runde | Befund | Form |
|---|---|---|
| T-97 · 1, `780abf3` | B1: Befund, falsche Tabellenänderung und rotes W17 nur per `print`, Exit 0 | 1 |
| T-97 · 1, `780abf3` | B3: Jede Änderung an `fund_size`, `volatility`, `quote_time` galt als erwartet, unabhängig vom Wert | 2 |
| T-97 · 2, `e2c5f4e` | B6: Ein Refresh mit HTTP 500 ändert keine Tabelle und entsprach damit der Erwartung „aktualisieren ändert nichts“; Exit 0 | 3 |

Jeder Befund kostete eine Review-Runde. Der Positivlauf auf Mikes
Arbeitsbestand war in allen Runden grün.

**Warum eine eigene Lesson trotz Vorgängern:** Die Bausteine stehen in
[SI-P-05](SI-P-05-ein-abgebrochener-prueflauf-meldet-sich-als-bestanden.md)
(Abbruch als bestanden),
[SI-P-08](SI-P-08-der-test-erzeugt-den-entscheidenden-unterschied-nicht.md)
(Test ohne entscheidenden Unterschied) und
[SI-P-14](SI-P-14-der-grenzwaechter-bestaetigt-eine-handgeschriebene-liste.md)
(Ausnahme nach Merkmal statt Inhalt). Der Coder las sie vor jeder Übergabe;
die Muster traten in T-97 trotzdem dreimal auf, jeweils im Prüfskript statt
im Produktcode. SI-P-16 bündelt sie zu einer Pflicht, die vor der Übergabe
abzuhaken ist. Dass Lessons allein das Muster nicht verhindert haben, ist
als Workflow-Frage an AgentLessons übergeben (Ticket zur Vereinfachung und
Durchsetzung des Agenten-Workflows, 2026-10-02).
