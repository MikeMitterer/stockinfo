# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-44-fehlerwege-mit-kennung.md`
- `handoff_commit`: `5668dc7`
- `review_round`: `2`
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

**T-44 Runde 2 — `changes_requested` zu `5668dc7`.** Der zentrale Handler
liefert die verlangte top-level-Form korrekt; er bleibt unverändert. Das
Vertragsinventar ist jedoch erneut unvollständig:

1. **Sieben statt fünf Verbraucher.** Neben den fünf `{isin}`-Pfaden rufen
   auch `GET /analyze?isin=…` und
   `PUT /instruments/by-symbol/{symbol}/isin` `normalize_isin()` direkt auf.
   Beide liefern bei `BTC-EUR` zur Laufzeit den neuen top-level
   `ErrorDetail`, OpenAPI veröffentlicht dort weiterhin
   `HTTPValidationError`. Der neue Test filtert nur auf `"{isin}"` und kann
   diese zwei Verbraucher nicht finden.

2. **422 hat an mehreren Routen mehr als eine gültige Form.** Die neue
   Deklaration ersetzt den gesamten 422-Vertrag durch einen einzelnen
   `$ref: ErrorDetail`. Gemessene Gegenbeispiele am selben Stand:

   - `/quote/{isin}/daily?period=nope` → FastAPI-`HTTPValidationError`
   - `/quote/{isin}/history?limit=0` → `HTTPValidationError`
   - `/quote/{isin}/history?from=nope` → `{"detail": "…"}`
   - `/analyze` ohne Kennung → `{"detail": "…"}`
   - PUT ohne `isin` → `HTTPValidationError`; ungültiges Symbol →
     `{"detail": "…"}`

   Der veröffentlichte 422 muss je Route **alle dort tatsächlich möglichen
   Formen** enthalten; die neue `invalid_isin_format`-Variante darin ist
   `ErrorDetail`. Andere bestehende 422-Laufzeitformen werden in T-44 weder
   umgebaut noch mit neuen Kennungen versehen.

**Abschließende Korrektur:** explizites Inventar der sieben Routen statt einer
Ableitung aus dem Pfadnamen; OpenAPI-422 je Route vollständig machen und die
Orakel gegen (a) top-level `ErrorDetail` für die ungültige ISIN sowie (b) die
weiterhin möglichen anderen 422-Formen prüfen. Kein neuer Handler, Fehlercode,
i18n-Text, Endpunkt, Modell oder Produktverhalten.

**Runden-3-Grenze:** höchstens fünf bereits vorhandene Produkt-/Vertragsdateien
plus die bestehende Testdatei, keine neue Datei und höchstens 100 zusätzliche
Quell-Diff-Zeilen. Vorhandene falsche Deklarationen/Assertions ersetzen statt
parallel ergänzen. Bei Überschreitung sofort `scope_checkpoint`.

**Codex-Nachweis:** alle sieben ungültigen-ISIN-Aufrufe liefern 422 mit
top-level `ErrorDetail`; die zwei fehlenden OpenAPI-Pfade sowie die oben
genannten konkurrierenden 422-Formen sind live reproduziert. `make test` ist
grün (964 Backend, 295 Plugin-API, 45 Beispiel, 291 Dashboard), ebenso Ruff
und `git diff --check`. DRY-Prüfung: Handler, Kennung und Response-Konstante
sind zentral; der Befund liegt im unvollständigen Verbraucher-/Varianteninventar.
