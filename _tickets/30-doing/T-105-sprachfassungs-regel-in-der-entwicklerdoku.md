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
| 1 | Absatz gegen `.docs-check.conf.sh` (`TRANSLATIONS`) und das Verhalten der Prüfung | Aussagen stimmen: Gliederung, je Abschnitt Links, Bilder, Code, Hinweisboxen, Absätze; nicht quittierbar | ➖ |
| 2 | `make docs-check` | keine Probleme | ➖ |
| 3 | Doku-Abgleich | READMEs, `docker/README.md`, `AGENTS.md` | ➖ |

### Akzeptanzkriterien

- [ ] Der Absatz steht nach dem Hook-Absatz im Abschnitt „Tests“.
- [ ] `make docs-check` ohne Probleme.

### Abgrenzung

Nur die Entwicklerdoku; die Regel selbst ist mit T-104 umgesetzt.

### Side-Effects

Keine.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
