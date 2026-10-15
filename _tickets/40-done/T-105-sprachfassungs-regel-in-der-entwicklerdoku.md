# T-105 · Sprachfassungs-Regel in der Entwicklerdoku

**Warum dieses Ticket:** Seit T-104 vergleicht `make docs-check` über
`TRANSLATIONS` in `.docs-check.conf.sh` die beiden READMEs. Jede Abweichung
ist ein Problem, das den Pre-Commit-Hook stoppt und sich nicht quittieren
lässt. `docs/development.md` sagt das nicht. Ein Entwickler, der nur
`README.md` ändert, sieht den Hook scheitern und weiß nicht, warum.

**Beispiel:** Jemand ergänzt in `README.md` einen Link auf den Changelog und
committet. Der Hook meldet „README.md ↔ README.de.md … Link nur in
README.md“. Danach steht in der Entwicklerdoku, dass beide Fassungen im
selben Commit geändert werden.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 angelegt und aktiviert
(Vorschlag der StockPortfolio-Sitzung `stockportfolio-97`, von Mike
bestätigt: „Ja, der ist auch von mir“). Coder `claude`, Verifier `codex`,
Branch `t-105-sprachfassungs-regel`. Vorbild: StockPortfolio `82dd028`.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `docs/development.md` erklärt im Abschnitt
„Tests“ direkt nach dem Absatz zum Pre-Commit-Hook die
Sprachfassungs-Regel.

**Fachliche Änderung:** eine — ein Absatz in `docs/development.md`.

**Erwartete Dateien:** `docs/development.md` (1), Ticket und Status.
**Diff-Budget:** unter 10 Zeilen ohne `_tickets/`.

**Nicht-Ziele:** keine Änderung an Config, READMEs oder Werkzeug.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Absatz gegen `.docs-check.conf.sh` (`TRANSLATIONS`) und das Verhalten der Prüfung | Aussagen stimmen: Gliederung, je Abschnitt Links, Bilder, Code, Hinweisboxen, Absätze; nicht quittierbar | ✅ `docs-check.sh` Zeile 32: `--ack` gilt nur für `SCREENSHOTS`, `DEPENDS`, `DEPENDS_HINT`; `docs-check.ts:1973`: Mermaid-Inhalt wird nicht verglichen. Gegenproben aus T-104 Runde 3 (Link nur in einer Fassung, zusätzliche Überschrift) endeten mit Exit 2 |
| 2 | `make docs-check` | keine Probleme | ✅ „… 1 Sprachfassung … keine Probleme“; Hook beim Commit `4d41532` grün |
| 3 | Doku-Abgleich | READMEs, `docker/README.md`, `AGENTS.md` | ✅ nur `docs/development.md` „Tests“; READMEs und `docker/README.md` beschreiben keine Entwicklerregeln, `AGENTS.md` verweist für `make docs-check` auf die Config |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] Der Absatz steht nach dem Hook-Absatz im Abschnitt „Tests“.
- [x] `make docs-check` ohne Probleme.

### Abgrenzung

Nur die Entwicklerdoku; die Regel selbst ist mit T-104 umgesetzt.

### Side-Effects

Keine.

### Auflösung

Erledigt: technisch freigegeben, nach `master` gemergt, am 2026-10-15 von Mike abgenommen („T-105 bis T-107 sind abgenommen“).

## Review-Verlauf (neueste Runde zuerst)

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: technisch `approved` für `4d41532`.** Der neue Absatz steht
direkt nach dem Pre-Commit-Hook im Abschnitt „Tests“. Die genannten
Vergleichsmerkmale entsprechen `TRANSLATIONS` in `.docs-check.conf.sh` und
`checkTranslation` in ProjectTools: Überschriftenstruktur sowie Links,
Inline-Code, Codeblöcke, Hinweisboxen und Absatzzahl je Abschnitt. Mermaid-
Inhalt ist ausgenommen. Sprachabweichungen sind Probleme und haben keinen
Quittierungsweg.

**Nachweise:** `make docs-check` unabhängig mit Exit 0 (18 Dokumente,
25 Pflichtdateien, 12 Abhängigkeiten, eine Sprachfassung);
`git diff --check 4d41532^..4d41532` ohne Befund. Der Produkt-Diff
besteht nur aus sechs Zeilen in `docs/development.md`, unter dem Budget.
Nach `4d41532` folgten ausschließlich Board-Commits; der Prüfstand ist
eindeutig. Doku-Abgleich: Entwicklerregel gehört hierhin, beide READMEs
bleiben nutzerorientiert, Docker-Anleitung und AGENTS.md brauchen dafür
keine Änderung. Keine menschliche Abnahme und kein Push durch dieses Review.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `4d41532` auf `t-105-sprachfassungs-regel`. Eine Datei,
+6 Zeilen (Budget 10). Danach nur Board-Commits (`97d617a`: T-103 und T-104
nach `40-done/` auf Mikes Abnahme).

Absatz wörtlich wie von Mike bestätigt, nach „`make setup` also installs a
Git pre-commit hook …“. Code-Standards: ➖ kein Code; Dokumentation ✅
(englisch wie die Datei, Absatzregel eingehalten). DRY: Die Regel steht in
`.docs-check.conf.sh`; der Absatz erklärt ihre Folge für Entwickler, keine
zweite Liste.
