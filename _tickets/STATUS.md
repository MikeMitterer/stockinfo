# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `portfolio_review`
- `ticket`: `T-28-abnahme-durch-mike.md`
- `handoff_commit`: `a9e49f9`
- `review_round`: `6`
- `owner`: `mike`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
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

_Keine offene Nachricht._


## OUTBOX → Codex

_Keine offene Nachricht._


## An Mike · Portfolio-Riegel

**Der Plugin-MVP steht.** T-22 → T-27a → T-27b → T-23 ist vollständig
freigegeben, letzter Produktstand `a9e49f9`. Der Lauf Registry → Core → REST
ist über **beide** Ladewege belegt: eine `*.py` im Datenvolume und ein echter
Entry-Point aus einer installierten Distribution. `795 passed, 29 skipped`
ohne Netz, dazu 8 Integrationstests gegen Yahoo, justETF und OpenFIGI.

Nach dem letzten Kettenglied wird nichts Neues begonnen — deshalb steht hier
jetzt `portfolio_review` und `owner: mike`. Es fehlt **eine Entscheidung von
dir**, keine Arbeit von uns.

**Was zu entscheiden ist:** Welche der neun offenen Positionen sind Gate (vor
T-28 erforderlich) und welche Follow-up? Das Inventar dazu steht in
`T-28-abnahme-durch-mike.md` unter „Inventar der offenen Tickets" — mit dem,
was jede Position für die Abnahme bedeutet. Die Empfehlung ist laut T-28
Codex' Aufgabe; die Spalte dort ist ein Vorschlag, kein Beschluss.

Drei Punkte brauchen dich unabhängig von der Einordnung:

1. **T-34 gibt es nicht.** Der Bereich „T-29 bis T-34" nennt ein Ticket, das
   weder im Board-Root noch unter `solved/` existiert. Vertipper oder nie
   angelegt?
2. **T-31 und T-33** stehen selbst auf „Entscheidung ausstehend" und sind
   ohne deine Antwort nicht umsetzbar — unabhängig davon, wie sie eingeordnet
   werden.
3. **Die ⚠️-Einschränkung aus Codex' Runde 6:** Der Installationsweg nach
   `data/plugin-env/<hash>` ist maschinell belegt, aber nie an einem echten
   `docker pull` auf demselben Volume gemessen. Genau dafür liegt der Ordner
   unter `/data`. Eine Verify-Zeile in T-28 wäre in zwei Minuten geprüft.

Das Verschieben nach `solved/` und die `Human`-Spalte bleiben wie immer bei
dir.
