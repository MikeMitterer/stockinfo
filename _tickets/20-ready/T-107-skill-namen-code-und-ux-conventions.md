# T-107 · Skill-Namen code-conventions und ux-conventions

**Warum dieses Ticket:** Die Skills `code-standards` und `ux-standards`
heißen jetzt `code-conventions` und `ux-conventions`. StockInfos
Projektregeln und lokale Board-Dateien nennen noch die alten Namen; ein
Agent, der danach sucht, findet den Skill nicht.

**Beispiel:** `AGENT-WORKFLOW.md` sagt „Vor fachlicher Arbeit laden Coder
und Verifier den Skill `code-standards`“. Den gibt es nicht mehr. Danach
steht dort `code-conventions`.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 in `20-ready/` angelegt
(Hinweis der StockPortfolio-Sitzung `stockportfolio-97`, von Mike
bestätigt: „Ja, das ist auch von mir“). Aktiviert wird es nach T-106.
Geprüft: Das gemeinsame Paket `agent-workflow` (`e627c21…`) nennt keinen
der alten Namen; alle Treffer stehen in StockInfos eigenen Dateien.
Vorbild: StockPortfolio `d690e5f`.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `git grep 'code-standards\|ux-standards'`
findet außerhalb von Lessons und erledigten Tickets nichts mehr.

**Fachliche Änderung:** eine — reine Umbenennung, keine neue Regel.

**Fundstellen (8):**

| Datei | Zeilen |
|---|---|
| `AGENTS.md` | 48, 131 |
| `_tickets/.agents/AGENT-ACTIVATION.md` | 49, 92 |
| `_tickets/.agents/AGENT-WORKFLOW.md` | 19, 637 (`ux-standards`), 766 |
| `_tickets/.agents/CODEX-IN-CONTEXT-SCHEDULER.md` | 36 |

**Diff-Budget:** unter 20 Zeilen.

**Nicht-Ziele:** Lessons unter `_tickets/.agents/lessons/` und Tickets in
`40-done/` bleiben als Verlauf unverändert; `STATUS.md`-Archiv ebenso.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `git grep -n 'code-standards\|ux-standards' -- AGENTS.md _tickets/.agents ':(exclude)_tickets/.agents/lessons'` | kein Treffer | ➖ |
| 2 | Neue Namen existieren (`~/.claude/skills/code-conventions`, `ux-conventions`) | vorhanden | ➖ |
| 3 | `make docs-check` | keine Probleme (AGENTS.md wird auf Links geprüft) | ➖ |

### Akzeptanzkriterien

- [ ] Alle acht Fundstellen umbenannt, sonst nichts geändert.
- [ ] `make docs-check` ohne Probleme.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
