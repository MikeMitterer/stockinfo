# StockInfo — Projektregeln

## Bezeichner sind englisch. Ausnahmslos.

Funktionen, Klassen, Felder, Parameter und **auch lokale Variablen** — in
Produktivcode **wie in Tests** und in **jeder** Sprache: Python, TypeScript,
Vue, Bash, SQL, Makefile, YAML-Schlüssel. Es gibt keine Sprache und keine
Dateiart, in der die Regel nicht gilt.

Das Namensschema je Sprache ist davon unberührt: Bash-Variablen bleiben GROSS
(`local -r _RETRY_DELAY`), Python `snake_case`, TypeScript `camelCase` — nur
eben englisch.

Deutsch bleibt die Sprache der **Erklärung**: Kommentare, Docstrings, Testnamen
(`def test_werte_ueberleben_das_erneute_lesen`), beschreibende `pytest`-IDs und
Commit-Bodies.

Steht in einer Datei beides, ist das keine gewachsene Konvention, der man folgt,
sondern Altlast: **Was ohnehin angefasst wird, zieht mit.** Das ist keine
Scope-Frage, die es zu klären gilt — die Regel hat sie schon beantwortet.

**Die Gegenprobe ist ein Inventar, keine Textsuche.** `grep` findet nur, was man
vorher erraten hat. Für Python zählt `ast` alle `ast.Name`, `ast.arg`, Funktions-
und Klassennamen auf; für TypeScript leistet das ein Lauf über die
TS-Compiler-API, für Bash die Liste aller Zuweisungen und Funktionsköpfe.
(`vue-tsc` prüft Typen, kein Inventar — es findet einen deutschen Namen nie.)
Genau daran ist die zu kurze Liste in T-21 Runde 37 gescheitert.

Vollständige Konventionen samt Namensschema je Sprache: Skill `code-standards`.

## Vor Arbeitsbeginn

- `_tickets/STATUS.md` — die Mailbox zwischen **Claude und Codex**. Sie sagt
  im maschinenlesbaren Zustand, wer am Zug ist. Steht dort `owner: claude`,
  liegt der Ball bei Claude und die Commit-Linie ist für Codex eingefroren —
  außer für Review- und Statusdateien.
- `_tickets/CLAUDE-REVIEW-PATTERNS.md` — Claudes wiederkehrende Fehlermuster,
  gepflegt von beiden Seiten. Codex liest sie **vor** jedem Review, statt
  dieselbe Klasse Fehler ein zweites Mal einzeln zu finden.
- `_tickets/CODEX-REVIEW-AUTOMATION.md` — Phasen, Validierungen und der
  Ablauf einer Übergabe.

> **Diese Datei ist die Codex-Entsprechung zu `CLAUDE.md`.** Die Regeln oben
> gelten für beide; nur dieser Abschnitt ist rollenabhängig. Wer sie synchron
> hält, ersetzt nicht bloß „Claude" durch „Codex" — beim ersten Mal wurde
> daraus „die Mailbox zwischen Codex und Codex" und ein `owner`-Riegel, der
> das Gegenteil dessen sagte, was er sagen sollte.
