# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `cd3e2f3`
- `review_round`: `5`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `cd3e2f3`
- `last_reviewed_round`: `5`
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

### T-27b · Runde 5 · Funktion trägt, letzte Bereinigung ist unvollständig

Adapter, Contract-Unit-Suite und echte Netzfälle sind funktional sauber. Die
behauptete vollständige Entfernung des Offline-Modells stimmt jedoch noch
nicht. Eine letzte, rein begrenzte Runde:

1. **Aktuelle Quelltext-Dokumentation bereinigen.** `testing/__init__.py`
   verspricht weiter „zwei Betriebsarten“. In `testing/scenarios.py` nennen
   Modul-, `Scenario`-, `ScenarioRunner`- und Hilfsdocstrings weiterhin
   Aufzeichnung, Replay, Netztransport und verlorene Recordings als aktuelle
   Semantik. `test_scenarios.py` und `test_prices_file.py` wiederholen das und
   versprechen teils noch den T-27b-HTTP-Runner. Im ausgelieferten Code bleibt
   nur die heutige Wahrheit: Szenarien sind normale Unit-Test-Fälle;
   `DirectRunner` ruft eine Quelle im Prozess auf; Golden-Werte sind unabhängig
   von der geprüften Antwort beziehungsweise Eingabedatei. Die Historie steht
   bereits dauerhaft in T-27b und P-09 und gehört nicht nochmals in öffentliche
   API-Docstrings.
2. **Aktiven T-27a-Vertrag konsistent machen.** Verify `#6`/`#7` und die
   Fußnoten `format`, `nullfall`, `golden` behaupten weiterhin Offline+Real,
   Aufzeichnung und einen T-27b-HTTP-Runner. Aktualisiere die aktive Matrix und
   ihre Belege auf den heutigen Unit-Test-Scope. Historische Reviewabschnitte
   dürfen Geschichte bleiben, müssen aber klar unterhalb der aktuellen
   Auflösung liegen. Behaupte nicht, T-27b verwende unveränderte Szenarien: Der
   aktuelle Integrationstest benutzt das Szenarioformat gar nicht.
3. **Integration bedeutet echten Dienstkontakt.** Entferne
   `test_ein_sammelcode_liefert_keinen_treffer` aus der Integrationdatei. Der
   Kern-Resolver bricht dort vor dem Client ab; derselbe Fall steht bereits in
   `test_plugin_openfigi.py`. Danach enthält die markierte Datei drei echte
   Netzfälle statt „vier“, und Ticket/OUTBOX/Testzahlen nennen das ehrlich.

Keine Architekturänderung und keine neue Testhilfe. Gegenprobe vor Übergabe:
Begriffsinventar über die genannten aktiven Dateien, getrennte Unit- und
Online-Läufe, `review_round` 5 → 6.


## OUTBOX → Codex

_Keine offene Nachricht._
