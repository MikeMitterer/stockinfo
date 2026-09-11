---
schema_version: 1
id: SI-P-03
project: stockinfo
kind: case
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
  heading: P-03 · Prüfwerkzeuge räumen fremde Ressourcen mit auf
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 932b9cb6cc3353e39175814fa3645d69dbe8e1ea3c9ce6758dee3e228de43b50
  captured_at: '2026-09-11'
---

# SI-P-03 · Prüfwerkzeuge räumen fremde Ressourcen mit auf

**Implementer-Regel:** Eigene Prozesse und temporäre Ressourcen festhalten; nur diese aufräumen.

**Verifier-Prüfung:** Cleanup-Ziele mit den nachweislich selbst gestarteten Ressourcen vergleichen.

## Originalbelege und Einordnung

**Erkennungsregel:** Cleanup bestimmt sein Ziel anhand eines globalen Merkmals
wie Port, Prozessname oder Pfadmuster statt anhand einer vom Lauf erzeugten und
gespeicherten Identität.

**Prüffrage:** Gehört jede beendete oder gelöschte Ressource nachweislich
diesem Lauf? Bei Prozess-Cleanup nur eigene PID beziehungsweise eigene
Prozessgruppe verwenden und Konflikte vor dem Start abbrechen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: `_tickets/40-done/T-17-smoke.sh`
beendete nach dem Lauf alle Prozesse auf Port 8766; ein bereits laufender
fremder Server konnte zusätzlich den Health-Check bestehen und danach beendet
werden.
