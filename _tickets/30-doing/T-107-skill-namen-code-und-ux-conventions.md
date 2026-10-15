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
bestätigt: „Ja, das ist auch von mir“). Nach der Freigabe von T-106 aktiviert (2026-10-15) auf `t-107-skill-namen`, Coder `claude`, Verifier `codex`.
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
| 1 | `git grep -n 'code-standards\|ux-standards' -- AGENTS.md _tickets/.agents ':(exclude)_tickets/.agents/lessons'` | kein Treffer | ✅ 0 Treffer nach `862ac11` (vorher 8) |
| 2 | Neue Namen existieren (`~/.claude/skills/code-conventions`, `ux-conventions`) | vorhanden | ✅ beide vorhanden |
| 3 | `make docs-check` | keine Probleme (AGENTS.md wird auf Links geprüft) | ✅ keine Probleme; Hook beim Commit grün |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] Alle acht Fundstellen umbenannt, sonst nichts geändert (`git diff --stat`: 4 Dateien, +8/−8).
- [x] `make docs-check` ohne Probleme.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: technisch `approved` für `862ac11`.** Der Diff ersetzt genau
acht Verweise in den vier vereinbarten Dateien. Die neuen Skills
`code-conventions` und `ux-conventions` sind installiert. Eine vollständige
Suche in AGENTS.md und den aktuellen `.agents/`-Regeln außerhalb der
Lessons-Einstiege findet keinen alten Skill-Namen mehr. Historische Lessons,
abgeschlossene Tickets und das STATUS-Archiv bleiben unangetastet.

**Nachweise:** `make docs-check` unabhängig mit Exit 0 (18 Dokumente,
25 Pflichtdateien, 12 Abhängigkeiten, eine Sprachfassung);
`git diff --check 862ac11^..862ac11` ohne Befund. Der Diff ist
+8/−8 Zeilen und enthält keine Produktdatei. Die lokale offene Übernahme
der Board-Konventionen bleibt sichtbar und ist kein Teil dieser
Namenskorrektur. Keine menschliche Abnahme und kein Push durch dieses Review.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `862ac11` auf `t-107-skill-namen`. 4 Dateien, +8/−8,
genau die acht Fundstellen aus dem Scope-Vertrag; Ersetzung mit
Wortgrenzen (`\bcode-standards\b`, `\bux-standards\b`). Lessons,
`40-done/` und das STATUS-Archiv unverändert. Code-Standards: ➖ kein
Code. DRY: ➖ nur Verweise.
