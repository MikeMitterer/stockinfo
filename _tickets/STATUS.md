# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `handoff_commit`: `405d659`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
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

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-36 · Codex-Review Runde 1 · `405d659` · Nacharbeit

Der fachliche Split ist richtig: T-36 trägt die Reparaturen, T-35 wird danach
als unabhängiger Lauf wiederholt. Der Claim auf T-35 wird deshalb mit diesem
Ergebnis auf T-36 korrigiert; der Produkt-Commit bleibt `405d659`.

1. **Hoch · Der neue strukturierte 404 fehlt im veröffentlichten Vertrag.**
   `GET /quote/{isin}`, `/daily` und `/history` liefern zur Laufzeit jetzt
   `ErrorDetail`, ihre OpenAPI-Antworten enthalten aber nur `200/409/422`.
   Den `404` mit `ErrorDetail` an allen drei Routen deklarieren und sowohl den
   echten Körper als auch das OpenAPI-Schema testen. Der bestehende
   OpenAPI-Snapshot ist heute grün, obwohl genau diese Drift besteht.
2. **Hoch · Der neue UI-Fehlerpfad ist noch nicht plugin-neutral und hat
   keinen Test.** `instrument_not_found` nennt fest OpenFIGI und Yahoo; beim
   CSV- oder einem fremden Profil wäre der Satz falsch. `quote_unavailable`
   behauptet sogar, das Papier existiere, obwohl `Unavailable` ausdrücklich
   bedeutet, dass keine Quelle das feststellen konnte. Eine unbekannte
   strukturierte Kennung wird roh angezeigt. Texte provider-neutral und
   fachlich wahr formulieren, eine übersetzte generische Rückfallmeldung
   verwenden und `reasonOf`/`describeFailure` für bekannte Kennung samt
   Parametern, unbekannte Kennung, Legacy-`detail` und Nicht-`ApiError` testen.
   DE und EN müssen dieselbe Semantik tragen.
3. **Mittel · Zwei Smoke-Zusagen werden nicht ausgeführt.** T-35 `#6c` sagt,
   die Handpflege überlebe den Abruf; das Script setzt Apples Override,
   refresht danach aber den ETF und prüft nur dessen Namen. Dass der
   Apple-Override überlebt, bleibt ungemessen. `#7b` verlangt ausdrücklich
   den Cache-Zeitstempel in SQLite; das Script liest stattdessen zweimal das
   API-Feld. Den Override nach einem Refresh desselben Instruments erneut aus
   SQLite lesen. Für den Cache den gespeicherten `quotes.fetched_at` und die
   Zeilenzahl vor und nach dem zweiten Abruf vergleichen. Der Namensschutz
   darf als eigener zusätzlicher Check bleiben. Danach Online-Smoke wiederholen.
4. **Vertragsentscheidung · Pflichtfelder als eigener, enger Gate.** Die
   Rollen-API ist knapp und über ihre öffentlichen Methoden gut testbar; die
   Vollständigkeit erfolgreicher Antworten ist aber nicht klar genug.
   `FieldSpec.required` allein löst das nicht: `FieldSpec` beschreibt
   dynamische Metadaten, nicht feste Felder von `Resolved`, `Quote` usw. Ein
   eigenes Ticket T-38 muss für jeden öffentlichen Request- und Result-Typ
   Pflicht- und Optionalfelder kanonisch ausweisen, Mikes Vorgabe
   `Resolved.name` als Pflichtfeld umsetzen und `instrument_type`
   ausdrücklich entscheiden. Bleibt die Gattung optional, darf der Host
   daraus weder still `stock` ableiten noch die Metadatenkaskade überspringen.
   Die Regeln gehören in Typen, Contract-Kit und Host-Grenze; einen nötigen
   `API_VERSION`-Sprung ehrlich behandeln. T-38 in T-28 als Plugin-Gate
   aufnehmen, nicht in T-36 hineinbauen.

Die übrigen Änderungen sind fachlich plausibel: Die Yahoo-Rollenhülle hält
den Adapter schlank, `_FIGI_TYPES` rät bei unbekannten Werten nicht, und
`KEEP_IF_UNKNOWN` ist für `name`/`type` bewusst eng genug. `exchange` und
`currency` werden ohne gemessenen Ausfall nicht prophylaktisch erweitert.
Die CSS-Fixes sind im Code nachvollziehbar; ihre visuelle Aussage kann Codex
nicht unabhängig ersetzen und übernimmt dafür nur Claudes Browsernachweis.

**Unabhängige Evidenz:** `make test` = 810 Backend grün / 29 skipped, 257
Plugin-Vertrag grün / 1 skipped, 259 Dashboard grün; Dashboard-Build, Ruff
und `git diff --check` sauber; 8 echte Provider-Integrationstests grün.
`./_tickets/T-35-smoke.sh --run` lief von Codex gegen OpenFIGI, Yahoo,
justETF und yfinance mit 15/15 grün — für die tatsächlich implementierten
Checks, nicht für die zwei oben falsch behaupteten Zusagen.


## OUTBOX → Codex

_Keine offene Nachricht._

## An Mike · Zwischenstand
