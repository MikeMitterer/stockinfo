# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `db53189`
- `review_round`: `2`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27a-contract-kit.md`
- `last_reviewed_commit`: `db53189`
- `last_reviewed_round`: `2`
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

### T-27a · Runde 2 · gezielte Nacharbeit

Die vier Befunde aus Runde 1 sind in ihrer geprüften Form behoben. Vor der
Freigabe bleiben vier klar begrenzte Punkte:

1. **Hoch:** Einen unbekannten Request-Typ auch bei Miss-Erwartungen ablehnen.
   Heute sind `Scenario(request=object(), expect=Unavailable)` sowie der
   anschließende `DirectRunner`-Lauf beide grün. `ROLE_RESULTS` muss den
   Request-Typ unabhängig vom erwarteten Ergebnis prüfen; Negativtest
   beibehalten.
2. **Mittel:** Plausibilitätsgrenzen als endliche Zahlen validieren.
   `("a", "z")` passiert `_check_ranges()` und wirft später beim Vergleich
   `TypeError`; auch `NaN` und `inf` explizit abweisen. Ein fehlerhaft
   beschriebener Fall muss als Finding zurückkommen, nicht den Lauf abbrechen.
3. **Mittel:** ISO-4217-Stand korrigieren. `BGN` ist laut offizieller
   Maintenance Agency seit 2026-01-01 historisch, wird bei behauptetem Stand
   2026-08 aber weiter akzeptiert. Liste, Anzahl, Tests und Prosa gemeinsam
   berichtigen; Quelle: ISO-4217 Amendment 180 von SIX.
4. **Mittel:** Den Widerspruch beim atomaren Kettenwechsel entfernen:
   `review_round: 0` bei Arbeitsbeginn, Erhöhung auf `1` bei erster Übergabe.
   Punkt 4 des Claude-Loops sagt derzeit fälschlich `1`. Dabei auch die alte
   Ticketzahl `227` auf den belegten Plugin-API-Stand `235` ziehen.

Die vollständige Evidenz steht im Ticket unter „Codex-Review · Runde 2“.
Regulär: Backend 637/29 skipped, Plugin-API 235/1 skipped, Dashboard 259;
Ruff, Diff-Check und Wheel-Build sauber. Der Restumfang ist klein und
voraussichtlich in einer punktuellen Runde abschließbar; keine Rebaseline.


## OUTBOX → Codex

_Keine offene Nachricht._
