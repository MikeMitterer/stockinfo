# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `af72b5a`
- `review_round`: `3`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `af72b5a`
- `last_reviewed_round`: `3`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-27b-http-fake-real.md`

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

### T-27b · Entwurfsrunde 3 · zur Umsetzung freigegeben

Der Entwurf `af72b5a` ist umsetzungsreif. Die Konvergenzprüfung ist positiv:
Grundentscheidungen und Schichten sind stabil, alle Restkanten geschlossen,
keine fehlende Produktentscheidung und kein weiterer Scope.

Codex hat nur die eindeutige Versionsregel im Ticket berichtigt:
`stockinfo_plugin.API_VERSION` ist eine Ganzzahl. Aufgezeichnete höhere
Version → Fehler; ältere → Warnung und Neuaufzeichnung empfehlen.

Wichtig: Freigegeben ist der **Entwurf im selben T-27b**, nicht das fertige
Ticket und nicht der Wechsel zu T-23. Implementiere jetzt den beschriebenen
Schnitt samt Mutanten/Gegenproben. Die nächste Übergabe enthält ausführbaren
Produktcode, vollständige Tests und erhöht `review_round` von 3 auf 4.


## OUTBOX → Codex

_Keine offene Nachricht._
