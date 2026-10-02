---
schema_version: 1
id: SI-P-15
project: stockinfo
kind: case
discovery_phase: human_feedback
affected_work:
- implementation
- review
subject_author: mixed
discovered_by: mike
recorded_by: claude-observer
structured_by: claude-observer
prevention_roles:
- implementer
- reviewer
evidence:
- ticket: T-93
  round: 1
  reviewed_commit: f5e0619
  result_commit: ecfed38
  finding: B1
- human: "Selbst Node 24 ist kein Problem. Das wäre die aktuell LTS-Version. Was soll das mit Python??? (Mike, 2026-10-02)"
- human: "Trag es ein, Node 24 als Mindestversion (Mike, 2026-10-02)"
- decision_commit: fe0bc49
---

# SI-P-15 · Eine dokumentierte Voraussetzung wird umgangen statt zur Entscheidung gestellt

**Implementer-Regel:** Widerspricht eine dokumentierte Voraussetzung dem
tatsächlichen Bedarf, zuerst die Voraussetzung bewerten: Was schützt sie in
diesem Projekt, und gibt es eine aktuelle Standardversion (etwa die LTS)?
Ein Umweg über eine andere Laufzeit, Sprache oder ein zusätzliches Werkzeug
braucht eine Begründung im Ticket oder Mikes Entscheidung.

**Verifier-Prüfung:** Bei einem Konflikt zwischen Voraussetzung und Code
die Option „Voraussetzung anheben“ ausdrücklich nennen und als Entscheidung
an Mike geben. Keine Lösungsliste vorlegen, die die Voraussetzung
stillschweigend festschreibt.

## Originalbelege und Einordnung

**Erkennungsregel:** Eine Angabe wie „Node.js 20+“ oder „Python 3.11+“ wird
als unverrückbar behandelt. Statt sie zur Entscheidung zu stellen, entsteht
eine Ausweichlösung, häufig über eine Sprach- oder Werkzeuggrenze hinweg.
Der Review-Befund wird dabei als vollständige Liste der Lösungswege gelesen,
und die erste Option wird ohne Rückfrage umgesetzt.

**Prüffrage:** Wer braucht die alte Voraussetzung tatsächlich? Wäre die
Lösung einfacher, wenn die Voraussetzung angehoben würde — und wer
entscheidet das?

**Beleg:** T-93 Runde 1, Prüfstand `f5e0619`, Review `ecfed38`, Befund B1.
`dashboard/e2e/visual-check.mjs` importierte `node:sqlite` (verfügbar ab
Node 22.5, ohne Schalter ab 22.13), `README.md` nannte „Node.js 20+“.

- **Codex als Verifier** forderte, den Kurspunkt-Zähler „mit der bereits
  vorhandenen Python-`sqlite3`-Umgebung oder einem gleichwertig zu Node 20
  passenden Weg“ umzusetzen. Die Frage, ob Node 20 für dieses Projekt
  überhaupt gelten muss, stellte der Befund nicht.
- **Claude als Coder** begann ohne Rückfrage den Python-Weg: Das Node-Skript
  sollte Python aufrufen, um eine Zeile in der Datenbank zu zählen.
- **Mike** auf Nachfrage im Observer-Chat: „Selbst Node 24 ist kein Problem.
  Das wäre die aktuell LTS-Version. Was soll das mit Python???“ und „Trag es
  ein, Node 24 als Mindestversion“. Mike bewertete den Python-Umweg als Hack.
  Die Entscheidung steht in `STATUS.md` (`fe0bc49`).

**Wie es ausgegangen ist:** Node 24 ist Mindestversion; `node:sqlite` bleibt,
der Python-Umbau entfällt. Die Anleitungen ziehen die Version mit.

**Abgrenzung:** Die Ursache liegt nahe an
[SI-R-02](SI-R-02-entwicklungsstand-wird-wie-ein-breit-ausgerolltes-produkt-behandelt.md):
StockInfo wird nur von Mike verwendet, „Node.js 20+“ schützte keinen realen
Nutzer. SI-P-15 beschreibt den eigenen Mechanismus: Eine dokumentierte
Grenze wird nicht hinterfragt, und der Aufwand wandert in eine technische
Ausweichlösung, die die Grenze am Leben hält.
