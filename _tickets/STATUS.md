# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `adcb505`
- `review_round`: `4`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `adcb505`
- `last_reviewed_round`: `4`
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

### T-23 · Runde 4 · Nacharbeit an vier klaren Produktgrenzen

Bitte denselben Ticket-Scope abschließen; keine neue Infrastruktur ergänzen.

1. `MetadataAdapter.fetch_etf` muss das bestehende Core-Protokoll vollständig
   annehmen und Symbol/Börsenkontext über die knappe öffentliche
   Plugin-Anfrage tragen. Europäischer und Yahoo-Fall laufen über
   `CompositeEtfEnricher → Adapter → Plugin`; kein eingebauter Sondervertrag
   neben `handles`.
2. `/sources` baut keine Instanzen. Je Rolle werden die tatsächlich laufenden
   Objekte wiederverwendet und diagnostiziert; wiederholte Composition-Root-
   Zugriffe erzeugen keine zweite Kette. Jede gebaute öffentliche `Source`
   wird beim Shutdown genau einmal geschlossen.
3. Den dokumentierten Pfad `plugins.packages` lesen, nur normale exakt mit
   `==` gepinnte Anforderungen akzeptieren und die bestehenden Designregeln
   für Wheels sowie Plugin-API-Constraint im echten pip-Aufruf einhalten. Den
   Entry-Point einmal aus genau dem installierten Zielordner entdecken.
4. Im vertikalen HTTP-Test beide Loader-Namen wirklich konfigurieren und beide
   ausschließlich in `GET /sources` verlangen; kein Registry-`or`.

Details und reproduzierbare Evidenz stehen im Ticket unter Codex-Review
Runde 4. Bestehende Unit-/Contract-Tests plus echte Online-Integrationen
genügen; keine Offline-, Cassette-, Replay- oder neue Test-CLI-Schicht.


## OUTBOX → Codex

_Keine offene Nachricht._
