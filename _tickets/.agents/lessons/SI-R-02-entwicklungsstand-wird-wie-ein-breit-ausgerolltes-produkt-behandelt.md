---
schema_version: 1
id: SI-R-02
project: stockinfo
kind: case
discovery_phase: human_feedback
affected_work:
- implementation
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
  heading: R-02 · Entwicklungsstand wird wie ein breit ausgerolltes Produkt behandelt
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: 13fe30eeadb5df008df41a815663ecf84b26726465e892a2adc0ed9a31d5d563
  section_sha256: a4ecbb7a9fe49c0765d39ff14ffc0b3146009013b8e2c905503d7d769ce8d6c9
  captured_at: '2026-09-11'
---

# SI-R-02 · Entwicklungsstand wird wie ein breit ausgerolltes Produkt behandelt

**Implementer-Regel:** Zusatzaufwand am tatsächlichen Betriebsstand und betroffenen Verbraucher ausrichten.

**Verifier-Prüfung:** Für Migration oder zusätzliche Absicherung den belegten Bedarf benennen.

## Originalbelege und Einordnung

Die verbindliche Vorgabe steht im
[Projekteinstieg](../../../AGENTS.md#tatsächlicher-entwicklungsstand).
Dieser Eintrag hält Anlass und Erkennung des Fehlmusters fest.

**Erkennungsregel:** Eine Änderung wird mit Rückwärtskompatibilität,
Migrationspfaden, Ablösungshinweisen oder zusätzlicher Reviewarbeit belastet,
weil hypothetisch viele Nutzer oder unbekannte Altinstallationen betroffen
sein könnten. Eine Veröffentlichung auf Unraid wird dabei ohne Beleg mit
breiter Nutzung gleichgesetzt. So entsteht Aufwand ohne konkreten Nutzen.

**Prüffrage:** Welcher reale Nutzer, Datenbestand oder Verbraucher braucht diese
Maßnahme heute, und welchen konkreten Nachteil verhindert sie? Ohne belegbare
Antwort entfällt die zusätzliche Maßnahme; die eigentliche Änderung wird fertig.

**Anlass:** T-21, Codex als Implementer, `1166745`: Ablösungsnotiz zur früheren
US-Sonderregel; anschließend Übergangssprache im Entwurf (`f0fb8c8`). Mike
weist beides zurück; entfernt in `4bacaf2`. Mike benennt das übergeordnete
Problem ausdrücklich als wiederkehrend: „Der aktuelle Stand ist ein
Entwicklungsstand“ und „Wir schießen mit Kanonen auf Spatzen“. Diese Vorgabe
wird auf seinen Auftrag festgehalten; es werden keine weiteren Vorfälle erfunden.
