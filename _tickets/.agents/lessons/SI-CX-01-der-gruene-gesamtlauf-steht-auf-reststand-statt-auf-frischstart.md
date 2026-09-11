---
schema_version: 1
id: SI-CX-01
project: stockinfo
kind: case
discovery_phase: verification
affected_work:
- tests
- handoff
subject_author: codex
discovered_by: claude
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CODEX-LESSONS.md
  heading: CX-01 · Der grüne Gesamtlauf steht auf Reststand statt auf Frischstart
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: 13fe30eeadb5df008df41a815663ecf84b26726465e892a2adc0ed9a31d5d563
  section_sha256: e79e0d58c9cb1da6e9b5bb80b741fb25e625228173155982cfe45aa10faf43e3
  captured_at: '2026-09-11'
---

# SI-CX-01 · Der grüne Gesamtlauf steht auf Reststand statt auf Frischstart

**Implementer-Regel:** Initialisierung und Speicherung auch mit nachweislich leerem Testspeicher prüfen.

**Verifier-Prüfung:** Frischen Ausgangszustand unabhängig herstellen und mit dem gemeldeten Ergebnis vergleichen.

## Originalbelege und Einordnung

**Erkennungsregel:** Die Übergabe nennt eine vollständige grüne Suite und ein
kopierbares Kommando mit eigenem Datenpfad. Der Pfad wird im Kommando nur
*genannt*, nicht *erzeugt* — er existiert aus einem früheren Lauf bereits
angelegt und initialisiert.

**Prüffrage:** Existiert der im Beleg genannte Zustand vor dem Lauf schon? Das
dokumentierte Kommando einmal auf einem nachweislich leeren Pfad wiederholen und
die Zahlen vergleichen. Bei Tickets, die Schema, Migration, Loader oder
Startzustand berühren, ist das der Frischstart aus dem
Vertical-Acceptance-Riegel und nicht optional.

**Beleg (ausdrücklich falsche Vollständigkeitsbehauptung):** T-26 Runde 1,
Prüfstand `fe323ff`. Verify `#11` und die OUTBOX melden „1065 Backend
erfolgreich" mit dem Kommando
`env DATABASE_PATH=/tmp/stockinfo-t26-suite/stockinfo.db make test`. Diese Datei
lag zum Zeitpunkt des Belegs bereits vollständig initialisiert vor
(`detail_values`, `detail_overrides`, Zeitstempel 14:51). Auf einem frischen
Pfad ergibt dasselbe Kommando `7 failed, 1058 passed`: `GET /fields` liest seit
diesem Diff `meta`, ohne dass `init_db` gelaufen sein muss
(`sqlite3.OperationalError: no such table: meta`, `app/routers/fields.py:47`).
Gegenprobe mit initialisierter Datenbank: dieselben 36 Tests grün. Befund von
Claude als Verifier, 2026-09-07.
