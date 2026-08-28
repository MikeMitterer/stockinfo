# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `e35d190`
- `review_round`: `2`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `e35d190`
- `last_reviewed_round`: `2`
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

### T-23 · Runde 2 · Änderungen erforderlich

Der Resolver-/Quote-Vertikallauf ist echt, T-23 aber noch nicht vollständig:

1. `daily` und `fx` liefern `YFinancePlugin` an Core-Protokolle und scheitern
   mit `AttributeError`; justETF und yfinance-Metadaten bleiben native
   Sonderwege. Alle fünf Rollen über den gemeinsamen Plugin-/Adapterweg führen.
2. `handles()` setzt den Circuit Breaker vor jedem fehlgeschlagenen
   `resolve()` zurück. Nur Arbeitsmethoden dürfen Erfolg/Fehler verbuchen.
3. `/sources` meldet ein wegen `configuration_problem()` verworfenes Plugin
   weiterhin als `configured: true` und `usable: true`.
4. justETF liest `fund_size_eur`, der Adapter beschriftet den Betrag aber mit
   `fund_currency`; `IE00B4L5Y983` wird so fälschlich als USD statt EUR
   geliefert.
5. Der aktive installierbare Paketweg aus T-23 fehlt weiterhin; das ohnehin
   installierte Contract-Paket mit eigenem Beispiel-Entry-Point beweist kein
   beigesteuertes Plugin. Schlank umsetzen oder eine ausdrückliche datierte
   Verschiebung durch Mike eintragen. Keine Preflight-/Offline-Infrastruktur.
6. EUR→EUR und der justETF-US-Abbruch sind weiterhin netzfreie
   Integrationstests; nur acht von zehn Fällen berühren einen Dienst. In Unit-
   Tests verschieben. Öffentliche `api_key`-Sicht statt `._client._api_key`.

Außerdem die neue `QuoteProvider`-Signatur in allen Implementierern und
Test-Doubles nachziehen. Vollständige Begründung und Gegenproben stehen im
Ticket unter „Codex-Review · Runde 2“.


## OUTBOX → Codex

_Keine offene Nachricht._
