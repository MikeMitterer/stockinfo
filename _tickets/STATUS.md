# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `claude_working`
- `ticket`: `T-44-fehlerwege-mit-kennung.md`
- `handoff_commit`: `cc7cafc`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `last_reviewed_commit`: `1f1fbb7`
- `last_reviewed_round`: `2`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md`
- `priority_ticket`: `T-44-fehlerwege-mit-kennung.md`

Erlaubte Phasen: `claude_working` → bei Breitenalarm kurz
`scope_checkpoint` → `ready_for_codex` → `codex_reviewing` →
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

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

> **T-40 Universalisierung Mike, 2026-08-29:** Nach dem letzten Plugin-/Produkt-
> Ticket T-39 wird das in StockInfo geschärfte Implementierungs- und Review-
> Regelwerk projektneutral formuliert und als wiederverwendbarer Workflow für
> andere Projekte bereitgestellt. T-40 ist Meta-Nacharbeit; es darf die Plugin-
> Implementierung T-31 → T-39 nicht unterbrechen.

> **T-42 menschliche MVP-Abnahme Mike, 2026-08-31:** Nach T-39 entwirft
> Claude aus den freigegebenen Tickets eine kurze risikobasierte UI-Matrix.
> Codex prüft zuerst nur das Konzept; nach Freigabe läuft Claude es im Browser,
> korrigiert kleine lokale Befunde und übergibt dieselben Schritte mit leerer
> Human-Spalte an Mike. T-40 ruht bis zu Mikes ausdrücklichem Kommando.

> **Portfolio-Entscheidung Mike, 2026-08-31:** T-42 ist **on hold** — die
> menschliche Abnahme der Matrix wartet, bis **T-43 → T-44 → T-46 → T-47**
> erledigt sind; das ist die neue Kette. **T-45 bleibt bis auf weiteres
> ausgelassen.** T-40 ruht unverändert bis zu Mikes Kommando.

> **T-41 Designfreigabe Mike, 2026-08-30:** Nach T-37 werden vor T-35 drei
> kleine, rollenspezifische Kaskaden für Quote, Daily und FX umgesetzt. Erste
> gültige Antwort gewinnt; Non-Hit/Ausfall fällt weiter; bestehender
> Cache-/Fehlerweg greift erst nach der ganzen Kette. Keine generische
> Abstraktion, Parallelität, Retries oder neue Konfiguration.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

**T-44 Runde 1 — `changes_requested` zu `cc7cafc`.** Die fachliche
Daily-/FX-Unterscheidung ist belastbar; nicht zurückbauen und kein neues Ticket
abspalten. Ein Vertragsfehler bleibt:

1. **`invalid_isin_format` ist kein ausgeliefertes `ErrorDetail`.**
   `normalize_isin()` steckt `ErrorDetail.model_dump()` in
   `HTTPException.detail`. Gemessen über den echten Eintrittspfad:

   ```json
   GET /quote/BTC-EUR
   422 {"detail":{"code":"invalid_isin_format","params":{"isin":"BTC-EUR"}}}
   ```

   `ErrorDetail` sagt ausdrücklich die nicht verschachtelte Form
   `{"code":…, "params":…}` zu; `reasonOf()` kann die jetzige Form ebenfalls
   nicht lesen. OpenAPI veröffentlicht für denselben 422 weiter
   `HTTPValidationError`. Der neue Test schreibt mit
   `response.json()["detail"]["code"]` genau diesen Widerspruch fest.

   **Korrektur:** Die gemeinsame ISIN-Validierung muss top-level
   `ErrorDetail` liefern. Alle Routen, die durch diese gemeinsame Validierung
   mit 422 abbrechen können, müssen denselben Laufzeitkörper im OpenAPI-Vertrag
   deklarieren. Das Orakel prüft am echten `GET /quote/BTC-EUR` die exakten
   Top-level-Schlüssel und den `$ref` auf `ErrorDetail`; kein Parser-Workaround
   im Dashboard.

2. **Scope-Disziplin:** 28 Dateien und 1.154 geänderte Zeilen liegen klar über
   17/550. Die notwendige Signaturfortpflanzung darf bleiben; es gibt deshalb
   weder Rollback noch künstliche Aufteilung. Entferne aber aus den in T-44 neu
   angefassten Produkt- und Testkommentaren Ticket-, Runden- und
   Codex-Prozessgeschichte (`T-44`, `T-42`, „Codex“, „Befund/Runde“), wo sie
   nicht den aktuellen Fachvertrag erklärt. Kommentare beschreiben den
   heutigen Invariant, das Ticket trägt die Historie.

**Harte Grenze für Runde 2:** kein neuer Endpunkt, keine neue Rolle, keine
Kaskaden-/Plugin-API-Architektur, keine neue Datei. Verhaltensänderungen nur an
der gemeinsamen 422-Abbildung und ihrer REST-Deklaration; übrige Änderungen
nur Testkorrektur, generierter Snapshot und Löschen/Neutralisieren der neuen
Prozessprosa. Der Gesamtdiff darf nicht weiter wachsen. Bei erneutem
Breitenalarm sofort `scope_checkpoint`, nicht erst nach der Umsetzung.

**Codex-Nachweis:** `make test` grün (963 Backend, 295 Plugin-API, 45 Beispiel,
291 Dashboard), `npm --prefix dashboard run build`, Ruff und
`git diff --check` grün. Der grüne Stand widerlegt den Befund nicht, weil das
422-Orakel derzeit die falsche Form erwartet.
