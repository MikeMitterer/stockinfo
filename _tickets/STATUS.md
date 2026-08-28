# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `a1ac605`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `a1ac605`
- `last_reviewed_round`: `1`
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

### T-27b · Entwurfsrunde 1 · Änderungen vor Produktcode

Die Grundrichtung trägt. Vor Umsetzung sind sechs Punkte im Ticket vollständig
ausgeführt:

1. **Hoch:** Replay-Misses über einen separaten Audit-Kanal hart fehlschlagen
   lassen; `MissingRecording` darf nicht als erwartetes `Unavailable` grün
   werden.
2. **Hoch:** `request_signature` für HTTP-Lookup und echte
   `scenario_signature` über `expect`/`golden`/`plausible` trennen und
   gemeinsam binden.
3. **Hoch:** Keine global wirkende Autouse-Socket-Sperre aus einem automatisch
   geladenen `pytest11`-Plugin. Expliziten, getesteten Opt-in für die
   HTTP-Szenariosuite entwerfen.
4. **Hoch:** Eine vollständige Modusmatrix für offline/`--real`/`--record`/
   Freshness schreiben. Record braucht Netz; Metadaten und Aufnahmen erst nach
   komplett grünem Lauf atomar ändern.
5. **Mittel:** `max_age_days` einmal je Plugin konfigurieren, nicht driftfähig
   je Aufnahme; konkreten Release-Check-Befehl benennen.
6. **Mittel:** Request-Kanonisierung und Scrubbing-Grenze präzisieren; relevante
   Header/Scheme/Port einbeziehen. Frankfurter zwingend mit `providers=ECB`
   auf die rechtlich geprüfte Quelle festpinnen und Antwort prüfen.

Verify #10 braucht beide Richtungen: Offline mit poisoned Live-Transport grün,
weil dieser nie berührt wird; Real gegen unerreichbaren Host rot mit deutbarer,
geheimnisfreier Meldung. Vor Umsetzung außerdem die Time-box konkret setzen.

Primärquellen und vollständige Begründung stehen im Ticket unter
„Codex-Review · Entwurfsrunde 1“. Keine Rebaseline; der Entwurf wird an seinen
bestehenden Grenzen präzisiert.


## OUTBOX → Codex

_Keine offene Nachricht._
