# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`
- `handoff_commit`: `a9e49f9`
- `review_round`: `6`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`

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

_Keine offene Nachricht._


## OUTBOX → Codex

_Keine offene Nachricht._


## An Mike · Zwischenstand

**T-34 ist nicht verloren, sie war gestrandet.** Angelegt am 2026-08-27 in
`3175fb2` auf dem eingefrorenen Branch `t-21d-offene-zuordnungen` — dem
Branch mit T-21 Übergabe 4A/4B. Die Board-Änderung wurde danach zweimal
gemacht: einmal dort, einmal auf der laufenden Linie. Mitgekommen ist der
**Verweis**, nicht die **Datei**. Zurückgeholt, wieder im Board-Root, in T-28
als Gate eingeordnet; Codex' Satz „T-34 ist ein Vertipper" ist dort mit
Beleg korrigiert.

**Der Portfolio-Riegel ist ausgesetzt**, auf deine Anweisung: erst die
UI-Tests. `T-35-ui-abnahme-am-laufenden-stack.md` steht mit dem Prüfplan
bereit; der Lauf läuft gegen die yfinance/justETF/OpenFIGI-Kette und eine
**eigene** Datenbank — nicht gegen `data/stockinfo.db` mit deinen echten
Papieren.
