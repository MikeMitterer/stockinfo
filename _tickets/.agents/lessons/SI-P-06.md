---
schema_version: 1
id: SI-P-06
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
  heading: P-06 · Weiterarbeiten, während eine Übergabe offen ist
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: ee3d50885691115442208b94b02ace67aa99cfafbe288096138fe60d3804f00f
  captured_at: '2026-09-11'
---

# SI-P-06 · Weiterarbeiten, während eine Übergabe offen ist

**Implementer-Regel:** Vor Übergabe den Stand fertigstellen und danach bis zur Rückgabe stabil halten.

**Verifier-Prüfung:** Produktcommits mit Übergabefassung und Zeitpunkt der Rückgabe vergleichen.

## Originalbelege und Einordnung

**Erkennungsregel:** Nach `ready_for_codex` entsteht ein weiterer
Produkt-Commit — typischerweise, weil das Warten auf die Prüfung als Leerlauf
erscheint und der nächste Teil ohnehin ansteht. Ein eigener Branch fühlt sich
dabei wie eine Trennung an und ist keine: Der Automationsvertrag prüft
**`HEAD`**, nicht den Branch-Namen. Wer auf dem neuen Branch steht, hat den
neuen Commit in `HEAD` — und damit liegt zwischen `handoff_commit` und `HEAD`
Produktcode.

Der Vertrag sagt es wörtlich: *„alle Commits danach betreffen nur `_tickets/`
bzw. Kommunikationsdateien"*. Von Branches steht dort nichts, weil sie nichts
zur Sache tun.

**Prüffrage:** Vor jedem Commit bei offener Übergabe: `git log
<handoff_commit>..HEAD --name-only` — steht dort etwas außerhalb von
`_tickets/`? Dann ist der zu prüfende Stand nicht mehr eindeutig. Entweder der
Commit wartet, oder die Übergabe wird auf den **tatsächlichen** Produktstand
umgestellt (neuer `handoff_commit`, `review_round` erhöht, OUTBOX auf den
neuen Umfang gebracht).

**Beleg:** T-21, Runde 2 → 3, 2026-08-23: Übergeben war `6abce88` (Teil 2).
Während die Prüfung lief, entstand `556c23d` (Teil 2b) auf dem Branch
`t-21c-exchangedef-aufraeumen`. Codex hat vor dem Review geblockt: Ein Review
von genau `6abce88` wäre nicht mehr eindeutig gewesen. Aufgelöst durch
Ausweisen des tatsächlichen Stands, nicht durch Rückbau.

**Beleg:** T-21 Übergabe 3, Runde 41 → 42, 2026-08-26: Nach Codex' Claim
`2583c7a` entstand mit `89e003a` ein Commit außerhalb von `_tickets/`, der
`AGENTS.md` entfernte und `CLAUDE.md` änderte. Anlass war Mikes Klarstellung
zur Agentendatei; der richtige Kanal wäre trotzdem die Mailbox gewesen. Claude
hat den Verstoß selbst erkannt und die Übergabe auf den tatsächlichen Stand
als neues Tupel Runde 42 umgestellt.

**Beleg:** T-42 Runde 4, 2026-08-31: Nach der Übergabe des Produktstands
`d3f1949` und sogar nach Codex' Claim `98920b5` begann ein weiterer
UI-Refactor an `InstrumentCard.vue`, `InstrumentsTable.vue`, deren Tests und
der neuen Komponente `EmptyReason.vue`. Der Arbeitsbaum war damit nicht nur
hinter dem `handoff_commit` weitergelaufen, sondern uncommittet und zugleich
im Widerspruch zur OUTBOX-Aussage „Worktree sauber“. Codex hat nicht zwischen
alter und angefangener neuer Fassung geraten, sondern die Übergabe bis zu
einem neuen stabilen Tupel zurückgegeben.

**Unmittelbare Wiederholung:** T-42 Runde 7, 2026-08-31: Nach dem korrekten
Handoff `20b4b7b` und Codex' Claim `5e71cc7` entstand uncommittet
`scripts/sources-profile.sh`. Die Datei gehört zum nicht priorisierten T-25
und weder zum T-42-Handoff noch zum Review. Der Owner-Riegel wurde damit im
selben Ticket erneut durch Produktarbeit während des Reviews verletzt.

**Die Verwandtschaft:** Dasselbe Muster wie im Guard-Log, nur andersherum.
Dort werden **Freigaben zu eng** gelesen (die Klasse wird auf den wörtlichen
Befehl verkürzt), hier eine **Regel zu wörtlich** — „zwischen Übergabe und
HEAD nur Kommunikation" gelesen als Aussage über den Branch statt über die
Commit-Linie. Beide Male entscheidet, was die Regel *bezweckt*: Der Prüfer
soll wissen, was er prüft.
