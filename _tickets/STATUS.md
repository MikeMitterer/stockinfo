# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-22-quellen-konfiguration.md`
- `handoff_commit`: `20af8fa`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-22-quellen-konfiguration.md`
- `last_reviewed_commit`: `20af8fa`
- `last_reviewed_round`: `1`
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

### T-22 · Runde 1 · Änderungen angefordert

Die Richtung trägt, aber vier reproduzierte Befunde verhindern die Freigabe.
Die vollständige Beschreibung samt Evidenz steht im Ticket unter
`Codex-Review · Runde 1 · 20af8fa`.

1. **Hoch:** Ohne `sources.yaml` geht ein vorhandener
   `Settings.openfigi_api_key` verloren; der gebaute Client erhält `None`.
   Secret-Verweise und Vorgaben müssen dieselbe kanonische
   Umgebungskonfiguration verwenden.
2. **Hoch:** `/sources` kann eine andere Kette melden als die laufenden,
   gecachten Services; eine Quelle in einer unpassenden Rolle erscheint zudem
   als `configured: true`, obwohl sie aus der echten Kette fällt. Laufzeit und
   Diagnose brauchen dieselbe Config- und Rollenentscheidung.
3. **Mittel:** Die neuen `DailyCloseProvider`/`FxProvider` sind unbenutzt,
   während die alten Protokolle in `daily_sync`/`fx_service` weiter die
   Verbraucher typisieren. Pro Rolle eine einzige Source of Truth herstellen.
4. **Mittel:** `T-22-smoke.sh` kann nach einem vor `report()` abgebrochenen
   Check mit weniger als fünf Ergebnissen grün enden. Einen kontrollierten
   Teilabbruch rot prüfen und exakt fünf Checks als Erfolg verlangen.

Verifikation Codex: T-22-Smoke **5/5**, `make test` **633 + 36 + 259**,
`ruff` sauber. Die Befunde liegen in nicht abgedeckten Gegenpfaden. Bitte jeden
Befund mit einer unabhängigen Gegenprobe schließen, dann Runde 2 übergeben.

## OUTBOX → Codex

_Keine offene Nachricht._
