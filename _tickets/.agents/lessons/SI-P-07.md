---
schema_version: 1
id: SI-P-07
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- implementation
- tests
- handoff
subject_author: claude
discovered_by: unknown
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-07 · Eine neue Zwischenlage wird gebaut statt benannt
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: deca3172be058c2b9fb6aa1b2db1b623a15ecbbb098ceeb19f9de586e54c43e6
  captured_at: '2026-09-11'
---

# SI-P-07 · Eine neue Zwischenlage wird gebaut statt benannt

**Implementer-Regel:** Zwischenzustände und erlaubte Übergänge ausdrücklich benennen.

**Verifier-Prüfung:** An der ausstehenden Operation anhalten und Bereitschaft sowie Folgeaktionen prüfen.

## Originalbelege und Einordnung

**Erkennungsregel:** Ein Zustand wird von mehreren booleschen Feldern
gemeinsam getragen, und eine Lage ist nicht ein Wert, sondern eine
*Kombination*. Dann existieren automatisch Kombinationen, die niemand
entworfen hat — und genau die sind zwischen zwei Zuweisungen sichtbar. Das
Muster tarnt sich als Reihenfolgefehler („die Flags werden in der falschen
Reihenfolge gesetzt"); die Ursache ist, dass es für die Zwischenzeit gar
keinen Namen gibt.

Ein zuverlässiger Geruch: Eine Methode setzt Flags und ruft **danach** etwas
auf, das dauern oder scheitern kann. Zwischen beidem liegt eine Lage, die
kein Feld beschreibt.

**Prüffrage:** Jede Lage einzeln benennen und zählen — gibt es mehr
Kombinationen der Felder als benannte Lagen? Dann für jede Zeile im
Zustandsübergang fragen: *Was antwortet die Diagnose genau hier?* Ein
angehaltener Rückruf beantwortet das ausführbar; ein Test, der nur Anfang und
Ende sieht, kann es nicht.

**Beleg 1:** T-21 2A, Runde 30, Codex: `confirm()` setzte den Riegel zurück
und startete den Scheduler, **bevor** der Umzug begann. Die Lage „Umzug läuft
gerade" hatte keinen Namen; sie war „nicht mehr pending, noch nicht fertig".
Behoben, indem sie einen bekam (`claim`/`release`/`abandon`).

**Beleg 2:** T-21 2A, Runde 32, Codex, Commit `21865c0`: Exakt dieselbe Form
eine Stufe später. `release()` setzte `pending=False`, `startup_failed` entstand
erst im `except` — dazwischen lief `RefreshScheduler.start()`, und `/ready`
meldete `ok`, `/operational` meldete `serving`. Bei einem hängenden Start
unbegrenzt lange. Behoben, indem die Lage einen Namen bekam (`starting`) und
alle Lagen zu **einer** `Enum`-Zustandsgröße zusammengezogen wurden: Ein
`Enum` kann nicht halb umgeschaltet sein.

**Beleg 3:** T-21 2B, Runde 35, Codex, Commit `5b0fa31`: Das UI unterscheidet
`startupFailed`, führt dessen Retry aber über dieselbe `confirm()`-Funktion wie
den noch ausstehenden Umzug. Noch bevor der gemeinsame HTTP-Aufruf beginnt,
setzt sie die Lage auf `confirming`; das Template deutet diese ausschließlich
als Phase 1 und zeigt wieder Vorschau, Backup-Warnung und „Migration läuft".
Ein hängender Schedulerstart hält diese falsche Lage unbegrenzt sichtbar. Der
Server-Endpunkt darf gemeinsam sein; der Browservorgang braucht dennoch eine
eigene oder die bereits vorhandene benannte Lage `starting`.

**Warum die Reparatur aus Beleg 1 den Fall in Beleg 2 nicht verhindert hat:**
Sie war punktuell. Benannt wurde die eine fehlende Lage, nicht die
Darstellung. Solange der Zustand aus Flags besteht, entsteht die nächste
unbenannte Kombination beim nächsten Nachtrag von selbst — und der Nachtrag
erbt auch die Verriegelung des Originals nicht (in Runde 32 umging der neue
Wiederholungsweg den `claim` vollständig). Das ist die Verwandtschaft zu
[P-02](../CLAUDE-LESSONS.md#p-02--punktuelle-korrektur-wird-als-vollständige-regelumsetzung-gemeldet):
Dort steht, dass die Meldung zu vollständig war; hier steht, woran es
technisch lag.
