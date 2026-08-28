# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `approved`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `a9e49f9`
- `review_round`: `6`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-23-plugin-registry.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-23 · Runde 6 · freigegeben

`a9e49f9` ist unabhängig geprüft und freigegeben. T-23 ist das letzte Element
der bestätigten MVP-Kette. Bitte gemäß Portfolio-Riegel **nichts Neues
implementieren**: Zustand auf `portfolio_review`, `owner: mike` umstellen.
T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34 müssen vor T-28 einzeln als
Gate oder Follow-up eingeordnet werden; die Human-Spalte und das Verschieben
nach `solved/` bleiben bei Mike.

Abschlussevidenz und die einzige ⚠️-Einschränkung (kein tatsächlicher
Container-Image-Update-Lauf mit demselben Volume) stehen im Ticket unter
Codex-Review Runde 6.


## OUTBOX → Codex

_Keine offene Nachricht._
