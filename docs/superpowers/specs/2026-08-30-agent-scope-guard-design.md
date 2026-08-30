# Agent Scope Guard — Design

**Datum:** 2026-08-30
**Status:** von Mike bestätigt; im StockInfo-Workflow umgesetzt

## Ziel

Wiederkehrende Scope-Ausweitungen werden gestoppt, bevor ein großer Diff
entsteht. Claude bleibt Implementierer, Codex entscheidet bei einer
Überschreitung, ob eine rein mechanische Ausbreitung weiterlaufen darf.
Mike wird nur bei einer neuen Produktentscheidung beteiligt.

Der Guard ersetzt weder Ticket-Review noch Tests. Er ist ein kurzer
Zwischenentscheid über den Arbeitsumfang.

## Scope-Vertrag vor dem ersten Produktedit

Jedes Implementierungsticket enthält vor Arbeitsbeginn einen Abschnitt
`Scope-Vertrag` mit:

- einem beobachtbaren Ergebnis;
- höchstens drei fachlichen Änderungen;
- den erwarteten Produktschichten und Produktdateien;
- den erwarteten Test- und Dokumentationsanpassungen;
- ausdrücklichen Nicht-Zielen;
- einer Schätzung für Dateizahl und gesamte Diff-Zeilen.

Tests und Dokumentation werden getrennt von Produktdateien geschätzt. Eine
große mechanische Fixture-Anpassung bleibt dadurch sichtbar, ohne automatisch
als neue Produktarchitektur zu gelten.

## Auslöser

Claude stoppt vor weiterer Produktarbeit, sobald mindestens eines zutrifft:

1. Eine nicht angekündigte Produktschicht wird berührt.
2. Ein neuer öffentlicher Typ, Endpunkt, Vertrag, ein Schema, eine Abhängigkeit
   oder eine neue Abstraktion wird benötigt, ohne im Scope-Vertrag zu stehen.
3. Die geschätzte Dateizahl wird um mehr als 25 Prozent überschritten.
4. Der gesamte Ticket-Diff wächst ohne Vorabfreigabe über 800 Zeilen.
5. Produktkommentare oder Test-Docstrings beginnen, Prozesshistorie statt der
   aktuellen Invariante zu tragen.

Die quantitativen Grenzen sind ein Unterbrecher, kein Qualitätsurteil. Eine
legitime mechanische Ausbreitung kann nach dem Checkpoint weiterlaufen.

## Checkpoint-Protokoll

Claude friert einen stabilen Commit ein und setzt:

- `phase: scope_checkpoint`;
- `owner: codex`;
- `handoff_commit` auf den eingefrorenen Stand;
- eine kurze OUTBOX mit geplantem und tatsächlichem Umfang sowie dem konkreten
  Grund der Überschreitung.

Der Checkpoint ist kein Code-Review. Codex prüft nur Ticketziel, Diff-Statistik
und die neu berührten Flächen. Es werden keine neuen Qualitätsanforderungen
erfunden und keine vollständigen Tests verlangt.

Codex antwortet mit genau einer Entscheidung:

- `continue`: rein mechanische Ausbreitung innerhalb des vereinbarten
  Ergebnisses;
- `reduce`: Änderungen ohne notwendigen Beitrag zum Ergebnis entfernen;
- `split`: ein unabhängig lieferbares Ergebnis wird ein eigenes Ticket;
- `mike`: eine neue Produktentscheidung ist erforderlich.

Bei `continue`, `reduce` oder `split` geht der Zustand zurück auf
`claude_working`, `owner: claude`. Nur `mike` wechselt zu `blocked`,
`owner: mike`.

Codex darf das Budget eines Tickets einmal erweitern. Eine zweite
Überschreitung führt standardmäßig zu `reduce` oder `split`; nur eine eindeutig
mechanische Restanpassung darf nochmals weiterlaufen.

## Übergabe

Die normale Review-Übergabe enthält zusätzlich eine kleine Soll/Ist-Tabelle:

| Wert | geplant | tatsächlich |
|---|---:|---:|
| fachliche Änderungen | | |
| Produktdateien | | |
| Test-/Dokumentationsdateien | | |
| Diff-Zeilen | | |

Jede Abweichung wird in einem Satz begründet. Eine grüne Gesamtsuite ersetzt
diese Umfangskontrolle nicht.

## Kommentardisziplin

Produktkommentare und Test-Docstrings erklären nur die aktuelle Invariante und
den fachlichen Grund, soweit der Code ihn nicht selbst ausdrückt. Nicht in den
Code gehören:

- Review-Runden, Commit-IDs oder Ticketchroniken;
- Gesprächszitate und Datumsfolgen;
- frühere Implementierungsvarianten als längere Erzählung;
- Rechtfertigungen für jeden einzelnen Testaufbau.

Diese Historie bleibt im Ticket, in der Spec und in Git. Der Guard soll nicht
nur die Dateizahl, sondern auch den narrativen Diff begrenzen.

## Einführung

T-38 wird nicht rückwirkend durch einen Scope-Checkpoint unterbrochen, weil
sein Produktstand bereits vollständig übergeben ist. Das normale Review darf
nur konkrete Restbefunde zurückgeben.

Der Guard gilt verbindlich ab T-37 und wird in
`_tickets/CODEX-REVIEW-AUTOMATION.md`, im Claude-Loop-Prompt und in der
Ticketvorlage verankert. T-40 formuliert ihn später projektneutral; bis dahin
bleibt diese Fassung bewusst StockInfo-spezifisch.
