# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `e6ca003`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `e6ca003`
- `last_reviewed_round`: `1`
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

### T-23 · Runde 1 · Nacharbeit

Der vollständige Review steht im Ticket. Fünf begrenzte Punkte:

1. Der Plugin-Vertrag ist noch nicht mit den Core-Verträgen verbunden; die
   eingebauten Registry-Specs bauen weiterhin die alten nativen Klassen. Ein
   Datei- und ein echter Entry-Point müssen jeweils Registry → Core → REST
   durchlaufen.
2. Die neuen justETF-/yfinance-Adapter mit den vorhandenen geerbten
   Contract-Suiten prüfen und deren gefundene Verstöße beheben. Jeder
   Integrationstest berührt wirklich den Online-Dienst; EUR→EUR ist Unit.
3. Konstruktorfehler und `configuration_problem` geladener Quellen am
   Bau-Rand kapseln beziehungsweise aus der Kette halten.
4. Im Half-open-Zustand genau einen parallelen Probeaufruf reservieren.
5. Das duplizierte Inline-CSV-Plugin entfernen und die vorhandenen Beispiele
   verwenden. `#6c`, Kandidatenumgebung, Test-CLI und Socket-Sperre streichen;
   P-09 verbietet diesen Ausbau ohne Mikes ausdrückliche Ausnahme.

Keine neue Testschicht und keine neue Anbieterlogik. Der nächste Handoff zeigt
den vertikalen Lauf statt weiterer Vorarbeit.


## OUTBOX → Codex

_Keine offene Nachricht._
