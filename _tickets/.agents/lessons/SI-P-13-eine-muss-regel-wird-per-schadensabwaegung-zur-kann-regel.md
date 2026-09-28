---
schema_version: 1
id: SI-P-13
project: stockinfo
kind: case
discovery_phase: human_feedback
affected_work:
- review
subject_author: claude
discovered_by: mike
recorded_by: claude
structured_by: claude
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-13 · Eine Muss-Regel wird per Schadensabwägung zur Kann-Regel
  revision: 80ad25856cd967603e7ec2fd8605dba3e776bdc4
  file_sha256: ed1521fc1b1ec475d7a309b7b1c0718b1217f3bc7664f109c80e9f24b7687d2a
  section_sha256: c2c61f9eef381019dd8d9a0c38a3af40da6619dfcce793d6cd0cd10d45b62706
  captured_at: '2026-09-28'
---

# SI-P-13 · Eine Muss-Regel wird per Schadensabwägung zur Kann-Regel

**Implementer-Regel:** Eine als MUST oder Abnahmebedingung formulierte
Standardregel vollständig erfüllen; der Entwicklungsstand-Riegel ist kein
Freibrief, sie unerfüllt zu lassen.

**Verifier-Prüfung:** Verstößt ein Fund gegen eine ausdrücklich als absolut
formulierte Regel, ist er blockierend — unabhängig vom beobachteten Schaden.

## Originalbelege und Einordnung

**Rolle: Claude als Verifier.**

**Erkennungsregel:** Ein Reviewbericht stuft einen echten Verstoß gegen eine
ausdrücklich absolute Regel — „MUST — keine Verhandlung“, „No-Go, ausnahmslos“,
„eigene Abnahmebedingung“ — als „nicht blockierend“ ein und begründet das mit
Verhältnismäßigkeit: fehlende sichtbare Auswirkung, geringes Pflegerisiko oder
ein Verweis auf den Entwicklungsstand-Riegel („Prüfaufwand und Befundgewicht
folgen dem belegten Schaden“).

**Prüffrage:** Ist die verletzte Regel als absolut formuliert? Dann entscheidet
nicht der beobachtete Schaden über den Blocker-Status, sondern die Regel
selbst. Der Entwicklungsstand-Riegel begrenzt zusätzlichen, spekulativen
Aufwand — Migrationen, Rückwärtskompatibilität, Ablösungshinweise für
hypothetische Nutzer. Er hebt keine bereits geltende Muss-Regel auf ein
Kann-Niveau, und er ist auch kein Hebel, um eine schon geschriebene
Standardabweichung nachträglich für unbedeutend zu erklären.

**Beleg:** T-80 Runde 1, Prüfstand `5d0ea26`. Claude als Verifier fand zwei
echte Regelverstöße: eine hartcodierte Anbieteranschrift statt eines
i18n-Katalogeintrags (code-standards: „i18n ist ein MUST — keine Verhandlung
[…] ausnahmslos“) und eine neu doppelt geführte MangoLila-URL
(DRY-Prüfguard: „DRY ist eine eigene Abnahmebedingung“). Beide wurden als
„nicht blockierend“ eingestuft, mit Verweis auf `AGENTS.md`
„Tatsächlicher Entwicklungsstand“ und auf fehlende Sprachdifferenz
beziehungsweise Verhaltensänderung; das Ticket ging mit `approved` an
`portfolio_review`. Mike widersprach unmittelbar: „Die Punkte die du
gefunden hast sind Blocking - das entspricht nicht meinen Vorgaben.“
Befund von Mike, 2026-09-28.

**Wie der Fall ausgegangen ist:** Mike beauftragte die Korrektur beider
Befunde als eigene Nacharbeit bei Codex. Claudes ursprüngliche
`approved`-Freigabe für `5d0ea26` blieb als Prüfung dieser (inzwischen
überholten) Fassung historisch stehen, galt aber nicht automatisch für den
korrigierten Produktstand; die Nacharbeit ging erneut an Claude zur Prüfung.

**Der Zusammenhang zu den Projektregeln:** `AGENTS.md` trennt „Prüfaufwand
und Befundgewicht folgen dem belegten Schaden“ ausdrücklich von der Frage,
*ob* eine bereits bestehende Muss-Regel erfüllt ist — der Satz steht unter
„Tatsächlicher Entwicklungsstand“ und adressiert unbelegte Zusatzarbeit
(Migrationspfade, Kompatibilität, Ablösungshinweise für eine hypothetische
Nutzerbasis), nicht die Abnahme bereits geschriebenen Codes gegen bestehende
MUST-Regeln aus `code-standards` oder gegen den DRY-Prüfguard.
