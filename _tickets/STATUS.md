# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `617b407`
- `review_round`: `2`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `617b407`
- `last_reviewed_round`: `2`
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

### T-27b · Entwurfsrunde 2 · vier Restkanten

Die sechs Runde-1-Befunde sind im Grundsatz gelöst. Vor Produktcode bleiben:

1. **Hoch:** `scenario_signature` muss auch qualifizierten Typ und alle
   kanonischen Felder von `Scenario.request` enthalten. Gegenprobe: nur das
   Request-Feld ändern, während die fehlerhafte HTTP-Emission gleich bleibt.
2. **Hoch:** `only: real` an Replay-Aufnahmen entfernen. T-27a führt offline
   alle Fälle aus und filtert nur real über `real_ok`; eine nur real benutzte
   Replay-Datei gibt es nicht. Unbenutzt ist immer ein Fehler.
3. **Mittel:** `--real` darf `last_real_ok` nur bei vorhandener Aufnahme mit
   passender Szenario-Signatur aktualisieren. Suite-weite Veröffentlichung
   gegen Prozessabbruch absichern; mehrere einzelne `os.replace` sind
   gemeinsam nicht atomar.
4. **Mittel:** Quelle der `RecordingPolicy` für den konkreten CLI-Befehl und
   die von Verify #5 verlangten Versionsfelder samt Vergleichsregeln festlegen.

Beim Socket-Opt-in einen kanonischen Weg wählen: Die Replay-/Scenario-Fixture
hängt zwingend am Guard; ein Marker löst genau diesen aus. So kann die
Referenzsuite ihn nicht vergessen, fremde Tests bleiben ohne Opt-in unberührt.

Vollständige Begründung und Gegenproben stehen im Ticket. Keine Rebaseline;
vier Zustandskanten im vorhandenen Entwurf.


## OUTBOX → Codex

_Keine offene Nachricht._
