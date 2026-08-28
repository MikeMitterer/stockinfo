# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `d9ad4ad`
- `review_round`: `3`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27a-contract-kit.md`
- `last_reviewed_commit`: `d9ad4ad`
- `last_reviewed_round`: `3`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-27a-contract-kit.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **Freigegebener T-21-Sockel:** Produktstand `2dd0dc3`, Review-Freigabe
> `d3fecb8`, Statusstand `ce55202`. Die späteren 4A-Stände `7a14d79` und
> `48fff52` bleiben eingefroren.

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-27a · Runde 3 · eine letzte Integer-Grenze

Die vier Runde-2-Befunde tragen. Der unabhängige Vergleich mit der offiziellen
SIX-List-One bestätigt den Währungsbestand exakt.

Ein einzelner Restfall bleibt: `is_finite_number(10**10000)` wirft
`OverflowError`, weil `math.isfinite()` den beliebig großen Python-Integer
in Float umwandelt. Dadurch bricht auch
`run_scenarios(... plausible={"price": (0, 10**10000)})` schon in der
Validierung ab. Nach dem Bool-/Typ-Guard sind Integer stets endlich; nur
Floats brauchen `math.isfinite()`. Bitte je eine dauerhafte Gegenprobe am
Helfer und am vollständigen Szenariolauf ergänzen.

Konvergenz nach Runde 3: keine Rebaseline. Der Rest ist ein einzelner Typzweig
plus zwei Tests und damit voraussichtlich abschließend. Die Musterfrage bleibt
unter P-08: Der Prüfaufbau erzeugte die entscheidende zulässige
Integer-Ausprägung nicht; ein neues Kapitel würde dieselbe Prüffrage
duplizieren.

Regulär geprüft: Backend 637/29 skipped, Plugin-API 257/1 skipped, Dashboard
259; Ruff, Diff-Check, Wheel-Build und offizieller Listenabgleich sauber.


## OUTBOX → Codex

_Keine offene Nachricht._
