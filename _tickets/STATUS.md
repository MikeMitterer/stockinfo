# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `approved`
- `ticket`: `T-22-quellen-konfiguration.md`
- `handoff_commit`: `490314a`
- `review_round`: `3`
- `owner`: `claude`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-22-quellen-konfiguration.md`
- `last_reviewed_commit`: `490314a`
- `last_reviewed_round`: `3`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-22-quellen-konfiguration.md`

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

### T-22 · Runde 3 · freigegeben

Der neue Test stellt die ursprüngliche Abweichung belastbar in einem Prozess
her: Laufzeitstand A wird über `_build_resolver()` gebaut, die Datei danach auf
B geändert, und sowohl `/sources` als auch die bereits gebaute Laufzeit müssen
bei A bleiben. Der dokumentierte Frischlese-Mutant macht genau diesen Test rot.

**Verifikation Codex:** fokussierter Regressionstest 1/1, T-22-Smoke 5/5,
Ruff und `git diff --check` sauber; `make test` mit Backend 637 passed / 29
skipped, Plugin-API 36 und Dashboard 259. DRY-Prüfung des Runde-3-Diffs: nur
der bestehende Regressionstest wurde vertieft, keine neue Produktregel oder
parallele Wissensquelle entstand.

**Ergebnis:** `approved`. Bitte gemäß `priority_chain` auf T-27a wechseln; T-22
nicht nach `solved/` verschieben.


## OUTBOX → Codex

_Keine neue Übergabe._
