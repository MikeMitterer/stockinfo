---
schema_version: 1
id: SI-P-09
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
  heading: P-09 · Eine Testanforderung wächst zum unbeauftragten Subsystem
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: bc5e01dd241f8c7c391cd33aa4b31b41305087e992f7d44fd44b05f52fc4f041
  captured_at: '2026-09-11'
---

# SI-P-09 · Eine Testanforderung wächst zum unbeauftragten Subsystem

**Implementer-Regel:** Die kleinste vollständige Lösung des tatsächlichen Auftrags bauen.

**Verifier-Prüfung:** Vor Detailverbesserungen Umfang und Zusatzmechanik am Nutzerauftrag prüfen.

## Originalbelege und Einordnung

**Erkennungsregel:** Eine einfache Forderung nach Unit- und Integrationstests
wird ohne Produktentscheidung um dauerhafte Test-Infrastruktur erweitert —
etwa Record/Replay, Cassettes oder vollständige Datenverkehrsmitschnitte,
eigene Transportabstraktionen, Socket-Sperren, Bereinigungs- und
Serialisierungsformate, Freshness-Tore, CLIs oder pytest-Plugins. Die einzelnen
Bausteine können technisch begründbar sein; zusammen lösen sie eine neue
Anforderung, die niemand gestellt hat.

**Prüffrage:** Welcher wörtliche Auftrag verlangt das zusätzliche Subsystem?
Wenn die Antwort nur „offline wäre robuster“, „für CI wäre es bequemer“ oder
eine Ableitung aus einer allgemeinen Qualitätsregel ist, gilt die schlanke
Variante: normale Unit-Tests und echte Online-Integrationstests über die
bereits vorhandenen APIs. Eine Ausnahme darf weder Claude noch Codex aus
vermuteten Betriebsbedingungen ableiten; sie braucht Mikes ausdrückliche,
datierte Freigabe im Ticket.

**Beleg und ausdrückliche Produktkorrektur:** T-27b, Entwurfsstände
`a1ac605` bis `af72b5a`, 2026-08-28. Aus dem Ziel, ein echtes API-Plugin zu
prüfen, entstanden über drei Reviewrunden vier neue Testkit-Module,
Aufzeichnungsformat und Signaturen, Scrubbing, Socket-Guard, pytest-Entry-Point,
Freshness-Policy und Release-CLI. Unmittelbar vor Mikes Eingriff lag davon
bereits ein uncommitteter Produktstand mit `testing/http.py`,
`testing/recordings.py`, `testing/freshness.py` und `testing/pytest_plugin.py`
vor. Mike strich die Grundannahme ausdrücklich: Unit-Tests plus
Integrationstests gegen den echten Dienst, unter Verwendung der APIs, die für
die jeweilige Programmiersprache beziehungsweise Bibliothek bereits zur
Verfügung stehen. Claude verwarf den begonnenen Offline-Code in `ebf8a14`;
die Neufassung steht in `8698aa0`.

**Reviewer-Mitverantwortung:** Codex hat den Ausbau drei Runden lang
detailgenau verbessert und schließlich zur Umsetzung freigegeben. Das ist
nicht nur ein Implementiererfehler, sondern ein fehlender YAGNI-Riegel im
Review: Lokale technische Korrektheit darf die unbeauftragte Grundannahme nicht
legitimieren.
