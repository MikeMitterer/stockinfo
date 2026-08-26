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
(`vue-tsc` prüft Typen, kein Inventar — es findet einen deutschen Namen nie.) Genau daran ist die zu kurze Liste in
T-21 Runde 37 gescheitert.

Vollständige Konventionen samt Namensschema je Sprache: Skill `code-standards`.

## Vor Arbeitsbeginn

- `_tickets/STATUS.md` — die Mailbox zwischen Claude und Codex. `owner` sagt,
  wer am Zug ist: **Für den, der dort nicht steht, ist die Commit-Linie
  eingefroren** — außer für Review- und Statusdateien. Claude wartet also bei
  `owner: codex`, Codex bei `owner: claude`.
- `_tickets/CLAUDE-REVIEW-PATTERNS.md` — Claudes wiederkehrende Fehlermuster,
  gepflegt von beiden Seiten. Claude liest sie vor einer Übergabe, Codex vor
  einem Review — nicht erst nach dem Befund.
- `_tickets/CODEX-REVIEW-AUTOMATION.md` — Phasen, Validierungen und der
  Ablauf einer Übergabe.

> **Diese Datei gilt für beide Agenten.** `AGENTS.md` daneben ist Codex'
> üblicher Einstieg und **verweist** hierher, statt die Regeln zu kopieren —
> zwei Kopien liefen beim ersten Nachtrag auseinander. Wo eine Zeile
> rollenabhängig ist, nennt sie die Rolle ausdrücklich.
