---
schema_version: 1
id: SI-P-11
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
  heading: P-11 · Die Übergabe steht in der Mailbox, bevor es sie gibt
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 6913ceebe0a633dbc5e2defcb80c57e257df29900d317e16196e83ea29f8f111
  captured_at: '2026-09-11'
---

# SI-P-11 · Die Übergabe steht in der Mailbox, bevor es sie gibt

**Implementer-Regel:** Erst den fertigen Produktcommit erstellen, dann nach lokalem Workflow übergeben.

**Verifier-Prüfung:** Übergabereferenz auflösen und ihre Reihenfolge mit Mailbox und Produktänderungen vergleichen.

## Originalbelege und Einordnung

**Erkennungsregel:** `phase: ready_for_codex` und `owner: codex` stehen in
`STATUS.md`, während die Datei **uncommitted** im Arbeitsverzeichnis liegt
oder ein `handoff_commit` nennt, hinter dem noch Produktcommits folgen. Die
Mailbox ist damit für einen Zeitraum in einem Zustand, den sie nicht halten
kann: Sie sagt „übergeben" über einen Stand, den es im Repository so nicht
gibt.

**Der Unterschied zu P-06** ist die Richtung. Dort entsteht Produktcode
**nach** einer gültigen Übergabe. Hier ist die Übergabe von Anfang an
ungültig — sie wurde ausgesprochen, bevor der Stand fertig war, und der
Nachtrag kam später. Beide Male ist das Ergebnis dasselbe: Der Prüfer weiß
nicht, was er prüfen soll. Nur ist es hier kein Verstoß gegen den Riegel,
sondern eine Reihenfolge, die ihn gar nicht erst herstellt.

**Warum es so leicht passiert:** Die Mailbox wird beim Schreiben der Übergabe
gefüllt — Befundtabelle, Matrixzuordnung, Läufe —, und `phase`/`owner` sind
zwei Zeilen im selben Dokument. Es fühlt sich wie *ein* Vorgang an. Der
Zeitpunkt der Wirkung ist aber ein anderer als der des Schreibens: Wirksam
wird die Übergabe, sobald ein anderer Agent die Datei liest, und der wartet
nicht darauf, dass man fertig wird.

**Prüffrage — die Übergabe ist genau ein Commit, und er ist der letzte.** Vor
dem Setzen von `phase`/`owner`:

1. `git status --short` — ist alles außer `STATUS.md` committed?
2. `git log <handoff_commit>..HEAD --name-only` — steht dort noch Produktcode?
3. Zeigt `handoff_commit` auf **den letzten** Produktcommit, nicht auf einen
   Zwischenstand?

Erst wenn alle drei stimmen, werden `phase` und `owner` gesetzt — und
unmittelbar danach als **eigener** Commit gesichert, ohne etwas anderes
darin.

**Beleg:** T-31 Runde 6, 2026-08-29: Ich schrieb die vollständige OUTBOX samt
`phase: ready_for_codex`, `owner: codex` und `handoff_commit: 5b3c406` in die
Datei — und committete sie nicht. Beim Zusammenstellen der Matrixzuordnung
fand ich anschließend eine Testlücke bei `identity_form`, schloss sie mit
`6635c0e` und zog `handoff_commit` erst danach nach. Codex hat in genau dieses
Fenster gesehen: eine angekündigte Übergabe, uncommitted, auf einen Stand
zeigend, hinter dem noch ein Produktcommit lag. Zurückgewiesen ohne Review —
richtigerweise, denn der Riegel verbietet, den gemeinten Stand zu raten.

**Neuer Beleg:** T-51 Runde 1, Statuscommit `4158941`: `handoff_commit` zeigte
auf `c956bf7`, den nachgelagerten Ticket-Evidenzcommit, statt auf den letzten
Produktcommit `7b8d3bc`. Weil dazwischen ausschließlich Ticketdateien lagen,
war der Fachstand noch eindeutig und Codex konnte die Mailbox vor dem Review
normalisieren; die Prüffrage 3 hätte den Fehler vor der Übergabe verhindert.

**Die Lehre steckt in der Ursache, nicht in der Regel:** Das Schreiben der
Übergabe ist selbst noch Arbeit, die Befunde erzeugt. Wer die Mailbox
umschaltet, *während* er sie schreibt, hat die Übergabe für die Dauer dieser
Arbeit versprochen.



---
