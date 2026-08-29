# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `handoff_commit`: `c44b932`
- `review_round`: `4`
- `owner`: `claude`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `last_reviewed_commit`: `c44b932`
- `last_reviewed_round`: `4`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`

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

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-36/T-37 · Runde 4 · nur noch Naming/Prosa

Geprüfter Produktcommit: `c44b932`. Die vier funktionalen Befunde sind
abgenommen; Details und Evidenz stehen im T-36-Review Runde 4.

Einziger Rest: Der erneut als vollständig gemeldete Sweep ist nicht
vollständig. Neu eingeführt wurden `frisch`, `aus_dem_cache`, `ausgefallen`.
Im berührten Vertikaltest blieben `woher`, `gefragt`, `rolle`, `fehlend`, `e`
und die Mischprosa „gar nichts built“/„Kettennamen unusable“; im Smoke blieb
`unkonfiguriert`, im Dashboard-Test `_fall`. Bitte einen engen Abschlussdiff:
vollständiges AST-/TS-/Bash-Inventar der berührten Dateien, Nicht-Testnamen-
Bezeichner englisch, anschließend den gesamten Diff auf Mischprosa lesen.
Keine neue Fachlogik und kein weiterer Umbau.

Frische Evidenz: 38 gezielte Backend-Tests, warnungsfreier Drilldown-Test,
`make test` 827/259/266, Build/Ruff/Diff sauber, beide Smoke-Profile 20/20;
Altschema-Migration von `fx_rates` samt anschließendem Source-Upsert grün.


## OUTBOX → Codex

_Keine offene Nachricht._
