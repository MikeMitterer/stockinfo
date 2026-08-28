# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `4e23cde`
- `review_round`: `3`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `4e23cde`
- `last_reviewed_round`: `3`
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

### T-23 · Runde 3 · Änderungen erforderlich

Die öffentliche Plugin-API ist knapp und über ihre öffentlichen Methoden gut
testbar; Circuit Breaker, EUR-Fondsvolumen, Quote-Signatur und die acht echten
Online-Fälle sind bestätigt. Offen bleiben fünf konkrete Punkte:

1. `DailyAdapter` kann `AAPL/XNAS` aus dem aliaslosen Symbol `AAPL` nicht
   zurückrechnen und ruft den Provider nicht auf. Ticker/MIC wie beim
   Quote-Pfad bis zum echten Daily-Core-Verbraucher tragen und dort US + Xetra
   prüfen; `hasattr` genügt nicht.
2. `MetadataAdapter` ignoriert Einheit, Währung und Herkunft. Eine Ratio-TER
   `0.0019` kommt als `0.0019 %` statt `0.19 %` und `source=None` an. Bekannte
   Core-Felder korrekt konvertieren; unbekannte bleiben T-26. Den nativen
   yfinance-Metadaten-Sonderweg beziehungsweise `contract_roles` nicht als
   unzugeordneten Übergang stehen lassen.
3. `/sources` konstruiert Plugins erneut. Dadurch kann die Diagnose einem
   anderen Zustand als die laufende Kette entsprechen und Ressourcen
   wegwerfen. Operationalen Snapshot anzeigen. Den öffentlichen `close()`-
   Lifecycle beim Shutdown verwenden oder aus der knappen API entfernen;
   Diagnosegrund sichtbar machen oder die Dokumentationszusage korrigieren.
4. Den in `87c953c` entschiedenen schlanken Installationsweg jetzt umsetzen.
   Ausdrücklich keine Kandidaten-/Preflight-/Offline-Infrastruktur ergänzen.
5. Den vertikalen Test auf echte Core-Aufrufe, das tatsächlich kopierte
   `examples/canada_file.py` und beide Plugin-Namen in `GET /sources`
   vertiefen.

Vollständige Gegenproben und Evidenz stehen im Ticket unter
„Codex-Review · Runde 3“. `make test` ist mit 779/29, 257/1 und 259 grün; die
Online-Suite mit 2 + 3 + 3 ebenfalls. Diese Tests beibehalten.

## OUTBOX → Codex

_Keine offene Nachricht._
