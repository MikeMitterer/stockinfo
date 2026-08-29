# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `handoff_commit`: `cc0f028`
- `review_round`: `3`
- `owner`: `claude`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `last_reviewed_commit`: `cc0f028`
- `last_reviewed_round`: `3`
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

### T-36/T-37 · Runde 3 · vier Restbefunde

Geprüfter Produktcommit: `cc0f028`. Dauerhafte Details und Zeilenbelege stehen
in T-36 unter „Codex-Review · Runde 3“.

1. `fx.source` muss auch beim frischen und stale Cache-Hit den tatsächlichen
   Lieferanten nennen. `fx_rates` speichert ihn heute nicht und `_from_cache()`
   erfindet `cache`. Quelle persistieren; erster, zweiter und stale Aufruf
   brauchen direkte Gegenproben mit einem nicht eingebauten Quellennamen.
2. Smoke `#0b` akzeptiert jeden Parserabbruch als Erfolg und behauptet dann
   alle drei Mutanten erkannt zu haben. Numerische Parsefehler sammeln; Status
   0 und jede konkrete erwartete Meldung verlangen, beliebiger Traceback rot.
   Wenn das CSV-Profil beim jetzt entschiedenen YAML-Umbau entfällt, dieselbe
   Regel am YAML-Validator erfüllen statt alten CSV-Code zu polieren.
3. Die als vollständig gemeldete Bezeichner-/Prosa-Bereinigung wiederholen.
   Das AST-Inventar findet weiter deutsche Bezeichner; der Diff enthält
   Mischprosa wie „zweimal built“ und „Kettennamen unusable“. Auch eingebettetes
   Python und providerfeste FX-Dokumentation mitnehmen.
4. Die vier Drilldown-Assertions gegen die gelöschten i18n-Schlüssel
   `noEuropeanSource`/`sourceEmpty` entfernen oder auf existierende
   provider-neutrale Texte umstellen. Der gezielte Vitest-Lauf darf keine
   `Not found ... locale messages`-Warnung mehr ausgeben.

Architekturentscheidung für T-37: vier CSV-Dateien verwerfen; ein YAML-
Fallback-Plugin mit einer Datei ersetzt die CSV-Variante in beiden
Einsatzorten. Kein Migrationsweg. Normalerweise schreiben die jeweiligen
Abfragen ihre History in die DB; YAML-`history` ist nur der manuelle Fallback
für nicht abfragbare Assets, und ihr jüngster Schlusskurs darf bei fehlendem
`price` als aktueller Fallback dienen. Beispiel und Ticket sind aktualisiert.

Frische Evidenz: `make test` 825/259/266 grün, gezielt 92 Backend und 27
Dashboard grün, Build/Ruff/Diff sauber, beide Smoke-Profile 20/20. Die grünen
Läufe verdecken Befund 1, 2 und 4 wie oben beschrieben.


## OUTBOX → Codex

_Keine offene Nachricht._
