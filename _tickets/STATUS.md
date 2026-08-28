# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `approved`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `08814ff`
- `review_round`: `6`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `08814ff`
- `last_reviewed_round`: `6`
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

### T-27b · Runde 6 · freigegeben

Codex hat Stand `08814ff` freigegeben. Die Offline-/Replay-Restprosa und der
doppelte netzfreie Integrationstest sind entfernt. Frisch bestätigt: 25
Plugin-Unit-/Contract-Tests, 3 echte OpenFIGI-Tests sowie der vollständige
Projektlauf sind grün; das Wheel enthält keine obsolet gewordene
Testinfrastruktur.

Mikes zusätzliche Anforderung ist ebenfalls verifiziert: Die fachliche
Plugin-Schnittstelle ist auf `handles` und `resolve` begrenzt, und die Tests
arbeiten über den öffentlichen Konstruktor und öffentliche Methoden, ohne
private Plugin-Felder anzufassen.

Als Nächstes T-23 übernehmen. **Vor dem ersten Edit** Ticket, Phase,
`handoff_commit`, Runde, Owner und Priorität atomar auf T-23 umstellen. Die
Regeln aus P-09 gelten weiter: keine Record-/Replay- oder eigene Transport-
Testinfrastruktur ohne ausdrückliche datierte Freigabe von Mike.


## OUTBOX → Codex

_Keine offene Nachricht._
