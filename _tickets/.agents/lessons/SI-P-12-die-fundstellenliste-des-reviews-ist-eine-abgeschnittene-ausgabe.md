---
schema_version: 1
id: SI-P-12
project: stockinfo
kind: case
discovery_phase: verification
affected_work:
- review
subject_author: claude
discovered_by: claude
recorded_by: claude
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-12 · Die Fundstellenliste des Reviews ist eine abgeschnittene Ausgabe
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 86de205c2a8d57f77b0c46b44b5ecd0c362775c78ad21a1ee9e8788ed2129a56
  captured_at: '2026-09-11'
---

# SI-P-12 · Die Fundstellenliste des Reviews ist eine abgeschnittene Ausgabe

**Implementer-Regel:** Treffer vollständig zählen und begrenzte Ausgaben als solche kennzeichnen.

**Verifier-Prüfung:** Gezählte Fundstellen mit dem vollständigen Inventar vergleichen.

## Originalbelege und Einordnung

**Rolle: Claude als Verifier.** Der Befund betrifft nicht die Umsetzung,
sondern den Reviewbericht selbst.

**Erkennungsregel:** Ein Finding nennt Fundstellen und liest sich als
Inventar — „in den geänderten Dateien … weiter außerhalb liegen …“. Erzeugt
wurde die Liste aber mit einer begrenzten Ausgabe: `head`, `-m`, `| head -20`,
`--max-count`, ein Werkzeug mit eigener Trefferkappe. Der Coder arbeitet die
Liste vollständig ab, und die nächste Runde findet den Rest — der die ganze
Zeit da war.

**Prüffrage:** Wurde die Zahl der Treffer **gezählt**, bevor die Liste in den
Bericht kam? Jede Suche, deren Ergebnis eine Fundstellenliste wird, läuft
ohne Ausgabebegrenzung und mit `-c` oder `wc -l` als Gegenprobe. Steht in der
Pipe ein `head`, gehört in den Bericht die Gesamtzahl und das Wort
„gekürzt“ — sonst ist die Liste eine Behauptung über Vollständigkeit.

**Beleg:** T-21 Runde 1, Prüfstand `1166745`. Der Befund B1 zählte die
verbliebenen Sammelcode-Stellen auf; die zugrunde liegende Suche lief als
`git grep … | head -20`. Genannt wurden **11 Dateien**, den entfernten Begriff
trugen **18**. Codex korrigierte in Runde 2 genau die genannten und begründete
seine Auslassungen sauber; die nie genannten `test_migration_plan.py`,
`test_openfigi_lookup.py`, `test_plugin_openfigi.py`,
`test_plugin_openfigi_integration.py`, `test_repository.py`,
`test_yaml_profile.py` und `test_resolver_identity.py:67` blieben stehen,
ohne dass ihm etwas vorzuwerfen wäre. Befund von Claude über eigene Arbeit,
2026-09-09.

**Wie der Fall ausgegangen ist:** Auf Mikes Anweisung hat der Verifier die
restlichen 20 Fundstellen selbst korrigiert, statt sie an den Coder zu geben.
Daraus ist die Regel
[Der bereits benannte Rest wird nicht zur nächsten Runde](../AGENT-WORKFLOW.md#der-bereits-benannte-rest-wird-nicht-zur-nächsten-runde)
geworden. Sie ändert nichts an P-12: Die Liste muss trotzdem vollständig sein,
denn wer sie selbst abarbeitet, arbeitet genau sie ab.

**Der Zusammenhang zu den Projektregeln:** In `AGENTS.md` steht „Die Gegenprobe ist ein
Inventar, keine Textsuche“ für Bezeichner. Dieselbe Regel gilt für
Fundstellen im Review. Eine gekappte Ausgabe ist noch schlechter als eine
schlecht geratene Suche: Sie sieht vollständig aus, weil sie mit einem
korrekten Kommando entstanden ist.
