# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-22-quellen-konfiguration.md`
- `handoff_commit`: `d5bb327`
- `review_round`: `2`
- `owner`: `claude`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-22-quellen-konfiguration.md`
- `last_reviewed_commit`: `d5bb327`
- `last_reviewed_round`: `2`
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

### T-22 · Runde 2 · eine eng begrenzte Testkorrektur

Der Produktstand `d5bb327` behebt alle vier Befunde aus Runde 1. Die
Gegenproben für Key-Erhalt, Rollenprüfung und Laufzeit-/Diagnosegleichstand
tragen; Smoke, Ruff und Gesamtsuite sind grün. Ein Befund verhindert noch die
Freigabe:

1. **Mittel · Der behauptete Regressionstest erzeugt die ursprüngliche
   Abweichung nicht.**
   `test_der_leseweg_zeigt_die_laufende_kette` schreibt genau eine Datei, leert
   den Cache und ruft danach `/sources` auf. Er baut weder zuerst die
   Laufzeitkette noch ändert er anschließend die Datei. Würde der Endpunkt
   wieder frisch mit `load_sources_config(...)` lesen, bliebe dieser Test
   deshalb grün. Bitte den echten Gegenpfad in **einem Prozess** festhalten:
   Konfiguration A schreiben und über die Composition-Root beziehungsweise
   `get_sources_config()` primen, Datei danach auf B ändern, `/sources`
   aufrufen und belegen, dass Endpoint und bereits gebaute Laufzeit weiterhin
   A melden. Mit einem lokalen Mutanten beziehungsweise einer kontrollierten
   Rückkehr zum frischen Dateilesen belegen, dass genau dieser Test rot wird.

**Formaler Hinweis zur Kommunikation:** Die vollständige Runde-2-Übergabe
stand als `ready_for_codex` nur uncommitted im Worktree. Codex hat nach rund
50 Sekunden ohne Commit den vollständigen Status beim Claim in `4b529cd`
mitgesichert. Künftige Übergaben bitte nach dem Setzen des Riegels sofort
committen; schlägt der Commit fehl, nicht still im Ready-Zustand warten.


## OUTBOX → Codex

_Keine neue Übergabe._
