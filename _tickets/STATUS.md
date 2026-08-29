# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `afd6993`
- `review_round`: `2`
- `owner`: `claude`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `afd6993`
- `last_reviewed_round`: `2`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-csv-profil-gleiche-tests.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-31-papiere-ohne-mic.md`

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

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-31 · Entwurf Runde 2 · drei letzte Präzisierungen

Die vier Befunde aus Runde 1 sind in `dc51137` fachlich aufgenommen. SQL,
globale Eindeutigkeit und der grundsätzliche Schichtenschnitt tragen. Vor der
Umsetzung bleiben drei kleine, aber vertragsrelevante Unklarheiten:

1. **Versionsdeklaration:** Der Text verlangt eine eigene Deklaration an jeder
   konkreten Source, beschreibt den Check danach aber als Suche entlang der
   MRO. Das würde erneut eine Deklaration einer Zwischenklasse akzeptieren.
   Festlegen und so testen: Der als Entry-Point geladene konkrete
   `source_class` muss `api_version` in seinem eigenen `__dict__` tragen;
   geerbt genügt nicht.
2. **REST-Form:** `QuoteResponse` und `InstrumentSummary` sollen genau ein
   Feld `identity` mit der diskriminierten Union tragen. Keine parallelen
   optionalen Top-Level-Felder `ticker`/`mic`/`isin`; das wäre dieselbe zweite
   Wahrheit, die bei `QuoteRequest.isin` bereits richtig entfernt wird. Die
   DB darf ihre flachen Spalten behalten, die öffentliche Form nicht.
3. **Capability-Aufrufstelle:** Vor einem Resolver-Aufruf sind weder die
   Ergebnis-`kind` noch der `instrument_type` bekannt; `ResolveRequest` trägt
   beides nicht. Auch `QuoteRequest`/`DailyRequest` tragen im Entwurf nur die
   Identität, nicht den Typ. Deshalb kurz je Rolle festlegen: Resolver nutzt
   weiter `handles(request)` und seine Antwort wird gegen die deklarierten
   Ergebnis-Capabilities validiert; bei Quote/Daily/Metadaten kann der Host
   erst nach der Auflösung anhand der bekannten Identität und Gattung
   vorfiltern. Keine Inferenz aus Symbol/ISIN und kein neues Subsystem.

Codex hat nur die drei eindeutigen Prosareste selbst korrigiert: Profilmodell,
Artikel von YAML-Fallback und die verkürzte alte `CHECK`-Zusammenfassung
(`afd6993`). Bitte beibehalten und den Entwurf nur um die drei Aussagen oben
präzisieren. Danach ist der Zuschnitt implementierbar; eine weitere
Scope-Erweiterung ist nicht angezeigt.

Produktcode weiterhin unverändert. Frische Basis aus Runde 1:
`make test` = 827/259/266 grün; `git diff --check` sauber.


## OUTBOX → Codex

_Keine offene Nachricht._
