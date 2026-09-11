---
schema_version: 1
id: SI-T-66
project: stockinfo
kind: case
discovery_phase: human_feedback
affected_work:
- review
- documentation
subject_author: codex
discovered_by: mike
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CODEX-LESSONS.md
  heading: T-66 · Fachbefund übernommen, Gewichtung nicht eigenständig geprüft
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: 13fe30eeadb5df008df41a815663ecf84b26726465e892a2adc0ed9a31d5d563
  section_sha256: 2d2e27b41e5f6dd5b80caa30a1520952dcb0db51ee53cda2134126f2ccecab2a
  captured_at: '2026-09-11'
---

# SI-T-66 · Fachbefund übernommen, Gewichtung nicht eigenständig geprüft

**Implementer-Regel:** Auch beim Übernehmen eines Reviews Befund und Architekturfolgerung getrennt bewerten.

**Verifier-Prüfung:** Die behauptete Schwere am tatsächlichen Aufrufweg prüfen; SI-R-01 beschreibt denselben Vorfall.

## Originalbelege und Einordnung

Einzelfall-Lehre auf ausdrücklichen Auftrag von Mike, 2026-09-08: Codex
bestätigte Claudes korrekte Aussage zur HTTP-Middleware und übernahm daraus
vorschnell die SSE-Empfehlung (`26590c8`). Die Prüfung der konkreten UI-/REST-
Wirkung fehlte. Die Korrektur erfolgte in `e4b793e`, bestätigt in `e5e0b20`.
Bei der Review-Übernahme sind **Befund und Architekturfolgerung getrennt** zu
prüfen; ein zutreffender Codeverweis beweist nicht die behauptete Schwere.
Die gemeinsame Analyse und Gegenprüfung stehen einmalig in
[R-01 der Review-Lehren](../CLAUDE-LESSONS.md#r-01--integrationsaufwand-verdrängt-die-fachliche-architekturentscheidung).
Keine zweite unabhängige Episode wird behauptet.
