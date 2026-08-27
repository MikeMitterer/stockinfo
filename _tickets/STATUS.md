# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-22-quellen-konfiguration.md`
- `handoff_commit`: `—`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `7a14d79`
- `last_reviewed_round`: `51`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-22-quellen-konfiguration.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

Der Scheduler verarbeitet nur ein neues, valides Tupel aus Ticket, Commit und
Runde. Bei `ready_for_codex` muss `ticket` zusätzlich exakt
`priority_ticket` entsprechen und in `priority_chain` stehen.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** Das bisherige Vorgehen hat den
> Plugin-Host aus den Augen verloren. T-21 wird nach der freigegebenen
> Übergabe 3 eingefroren. Als Nächstes gilt ausschließlich die Kette
> **T-22 → T-27a → T-27b → T-23**. Ziel ist ein nachgewiesener Lauf eines
> Datei- und eines Entry-Point-Plugins über **Registry → Core → REST**.

> **Freigegebener T-21-Sockel:** Produktstand `2dd0dc3`, Review-Freigabe
> `d3fecb8`, anschließender Statusstand `ce55202`. Die späteren 4A-Stände
> `7a14d79` und `48fff52` sind eingefroren; Runde 52 wurde bewusst nicht mehr
> geprüft. 4A/4B werden erst nach dem Plugin-MVP wieder eingeordnet.

> **Sauberer Branch für T-22:** Nicht auf dem aktuellen 4A-Produktstand
> weiterbauen. Vom freigegebenen Sockel `ce55202` den Branch
> `t-22-quellen-konfiguration` erstellen. Danach zuerst den reinen
> Prozess-Commit `27d6195` und anschließend den Tip von
> `t-21d-offene-zuordnungen` mit dieser Rebaseline cherry-picken. Vor dem
> ersten Produktedit prüfen, dass `git log -1` die Rebaseline zeigt und
> `git diff --check` sauber ist.

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als zwingendes Gate oder ausdrückliches Follow-up klassifiziert.
> Sie blockieren den ersten Plugin-MVP nicht automatisch. Nach Freigabe von
> T-23 gilt `phase: portfolio_review`, `owner: mike`; kein Ticket wird dann
> selbständig gestartet.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.
- T-17, T-18, T-20 und T-24 sind bereits Codex-abgenommen und bleiben bis zur
  gesammelten menschlichen Abnahme im Board-Root.

## INBOX → Claude

### Kurskorrektur · jetzt T-22 beginnen

Mike hat die Rebaseline bestätigt. Runde 52 von T-21 wird nicht mehr geprüft;
Übergabe 4A/4B ist eingefroren. Richte zuerst den oben beschriebenen sauberen
T-22-Branch vom freigegebenen T-21-Sockel ein und implementiere dann T-22.

Halte die Kette strikt ein: **T-22 → T-27a → T-27b → T-23**. Eine während
der Arbeit gefundene Nebenbaustelle wird dokumentiert, aber nicht eigenmächtig
vorgezogen. T-22 geht wie gewohnt als ein überprüfbarer Handoff an Codex.

## OUTBOX → Codex

_Keine offene Nachricht. T-21 Runde 52 wurde durch Mikes Rebaseline
zurückgezogen und ist kein Review-Handoff mehr._
