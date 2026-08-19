# T-15 · ETF-Extras vollständig nachtragen, im Detailbereich

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) + ux-foundation | in-review | — (gemerged) | Kennzahlen-Pflege, Detailbereich, Scan-Befunde | — |

**Löst:** T-09 machte drei Kennzahlen von Hand pflegbar — TER, Volatilität,
Thesaurierung. Die übrigen fünf, die justETF ebenfalls liefert, blieben leer,
sobald die Quelle nichts hergab: Anbieter, Replikationsart, Fondsvolumen,
Fondsdomizil, Fondswährung. In der Tabellenzelle war für acht Felder kein
Platz; die Pflege zieht deshalb in einen aufklappbaren Detailbereich um.

<!--
  Repo:   StockInfo (app/ + dashboard/), dazu ux-foundation (UxCaret, UxInfoHint).
  Status: in-review — Code ist in master (Merge 1c2fe50), die Mensch-Spalte fehlt.
  Herkunft: Dieses Ticket ist **nachgetragen**. Die Einheit lief über Spec und
  Plan unter docs/superpowers/, nicht über das Board — deshalb stand sie hier
  nie. Der Arbeits-Ledger und die Übergabe sind gelöscht (ed089e2).
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Assets → Klick auf Symbol oder Name | Zeile klappt auf, **acht** Kennzahlen stehen darin | ✅ [^1] | |
| 2 | dieselbe Zeile, Pfeil vorne | zeigt zu nach unten, offen nach oben — und bleibt in beiden Zuständen mittig in der Zeile | ✅ [^2] | |
| 3 | Fenster unter 768 px → Kartenliste, „mehr" | derselbe Detailbereich wie am Schreibtisch, einspaltig | ✅ [^3] | |
| 4 | ein Feld, das die Quelle liefert (z.B. TER bei EUNL.DE) | Wert ist **sichtbar**, aber nicht bearbeitbar; ein eigener Wert lässt sich trotzdem entfernen | ✅ [^4] | |
| 5 | ein Feld, das die Quelle **nicht** liefert (z.B. Fondsdomizil bei GOLD.SG) | Auswahlliste mit freier Eingabe; der eingetragene Wert erscheint sofort in der Tabelle | ✅ [^5] | |
| 6 | Detailbereich, alle acht Felder | **nur** die pflegbaren tragen eine getönte Fläche — die gesperrten nicht | ✅ [^6] | |
| 7 | Fußzeile des Detailbereichs | „Quelle: yfinance+justetf", darunter „Stand der Quelle", dahinter ein (i) mit der Erklärung | ✅ [^7] | |
| 8 | Auswahlliste öffnen, **einmal** Escape | die Liste geht zu, der Detailbereich bleibt offen; zweites Escape schließt ihn | ✅ [^8] | |
| 9 | Aktie aufklappen (APC.DE) | erklärt, dass justETF nur ETFs kennt — nicht „abgefragt, nichts geliefert" | ✅ [^9] | |
| 10 | Instrument mit Duplikat in einer Alt-DB | von Hand gepflegte Werte und das Daily-Wasserzeichen überleben die Migration | ➖ [^10] | |
| 11 | justETF nicht erreichbar, dann Refresh | gespeicherte ETF-Kennzahlen bleiben stehen statt auf leer zu fallen | ➖ [^11] | |
| 12 | `curl` gegen die API (Block unten) | unbrauchbares Symbol → 422, verdrehtes Zeitfenster → 422, unbekannte **ISIN** → 404 statt 502; unbekanntes **Symbol** bleibt 502 | ✅ [^12] | |
| 13 | `/ready` bei umbenannter DB-Datei | meldet 503; `/health` bleibt 200 | ➖ [^13] | |
| 14 | `make test`, `vue-tsc -b`, `vite build` | Backend 209, Frontend 230, Typen sauber, Build läuft | ✅ [^14] | |

```bash
# #14 — Backend
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo" && .venv/bin/python -m pytest -q

# #14 — Frontend
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo/dashboard" && npx vitest run && npx vue-tsc -b && npx vite build

# #12 — Symbol ohne erlaubtes Format → 422
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote?symbol=../etc/passwd"

# #12 — verdrehtes Zeitfenster → 422
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://localhost:8000/quote/IE00B4L5Y983/history?from=2026-08-01T00:00:00%2B00:00&to=2026-01-01T00:00:00%2B00:00"

# #12 — unbekannte ISIN in der Daily-Route → 404 (früher 502)
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote/XX0000000000/daily"

# #12 — unbekanntes Symbol bleibt 502: dort ist "unbekannt" nicht von
#       "Provider antwortet nicht" zu unterscheiden
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote/by-symbol/XXTEST/daily"

# #13 — Readiness gegen Liveness
curl -s -o /dev/null -w "ready: %{http_code}\n"  "http://localhost:8000/ready"
curl -s -o /dev/null -w "health: %{http_code}\n" "http://localhost:8000/health"
```

[^1]: Live an EUNL.DE und GOLD.SG gesehen; acht `MetricEditor` im Detailbereich,
    mehrspaltig ab `md`, dreispaltig ab `lg`.
[^2]: Gemessen, weil der Augenschein hier trügt: Der Versatz zur Zeilenmitte
    beträgt 0,4 px — geschlossen **wie** geöffnet. Vorher war es ein Zeichen
    (U+2304), das tief im Em-Quadrat sitzt und beim Drehen nach oben kippte;
    jetzt ein SVG, dessen Form symmetrisch um die Kastenmitte liegt.
[^3]: Fenster verkleinert, Karte „EUNL.DE" auf- und zugeklappt; kein
    waagrechter Überhang (`scrollWidth − clientWidth` = 0).
[^4]: Der Fall war einmal kaputt — die Bedingung für die Bearbeitbarkeit
    umschloss auch die Anzeige, wodurch ein vollständig versorgtes Papier acht
    leere Zeilen zeigte.
[^5]: An GOLD.SG gesehen (Anbieter „Vanguard", Fondsdomizil „Irland").
[^6]: Gemessen: bei EUNL.DE (Quelle liefert alles) null hervorgehobene Felder,
    bei GOLD.SG sieben von acht — „Vola 1J" kommt dort aus der Quelle.
[^7]: Das (i) ist eine Form, kein Zeichen, und sitzt 6,4 px hinter dem
    Zeitstempel. Die zwei Pixel optische Korrektur nach oben sind mit Augen
    bestimmt: `vertical-align: middle` richtet an der halben x-Höhe aus, die
    Zeile besteht aber aus Ziffern auf Versalhöhe.
[^8]: Mit **echten** Tastenanschlägen geprüft, nicht mit synthetischen Events —
    Naive reagiert auf letztere nicht. Erstes Escape: Liste zu, Detailbereich
    offen. Zweites: beides zu. Der Wächter dafür sitzt in der Capture-Phase,
    weil Naive seine Liste in der Ziel-Phase schließt und die Klasse beim
    Bubble längst weg ist.
[^9]: Vorher stand dort „Quelle wurde abgefragt, hat nichts geliefert" — sie
    wurde nie abgefragt.
[^10]: ➖ **Nicht an einer echten Alt-Datenbank nachgestellt.** Belegt sind vier
    Migrationstests samt Gegenprobe: Ohne die Merge-Aufrufe fallen genau diese
    vier. Wer eine echte Alt-DB mit Duplikat zur Hand hat, sollte es einmal
    laufen lassen.
[^11]: ➖ **Nur über Tests.** Der Fehler selbst ist am 2026-08-18 real
    aufgetreten (ein Refresh über den Pfad ohne ISIN löschte TER,
    Replikationsart, Fondsvolumen und Thesaurierung von EUNL.DE); die
    **Behebung** ist nicht live nachgestellt worden.
[^12]: Live gegen `:8000` ausgeführt — und dabei fiel ein Fehler auf: Der
    Symbol-Pfad antwortete mit 502, wo Test und Ticket 404 behaupteten. Der
    Test war grün, weil das Double `InstrumentNotFoundError` warf; die echte
    Route kann das gar nicht. Auf dem Symbol-Pfad gibt es keine Auflösung, die
    scheitern könnte — `fetch_quote` liefert `None`, ob Yahoo das Symbol nicht
    kennt oder gerade nicht antwortet. 502 ist dort richtig, 404 wäre geraten.
    Der unerreichbare Zweig ist entfernt, der Test auf das echte Verhalten
    umgestellt. Gemessen: `../etc/passwd` → 422, verdrehtes Fenster → 422,
    `XX0000000000/daily` → **404**, `by-symbol/XXTEST/daily` → **502**.
[^13]: ➖ nur über Tests. Für den Handtest die SQLite-Datei umbenennen, `/ready`
    abfragen, zurückbenennen.
[^14]: Backend 209 (vorher 167), Frontend 230 in 43 Dateien, `ruff` über `app`
    und `tests` sauber, `vue-tsc -b` und `vite build` fehlerfrei — zuletzt auf
    `master` nach dem Merge gelaufen.

---

## Was gebaut wurde

**Acht Kennzahlen statt drei.** Anbieter, Replikationsart, Fondsvolumen,
Fondsdomizil und Fondswährung kommen dazu. Die Vorrang-Regel bleibt: Was die
Quelle liefert, gewinnt; von Hand ergänzt wird nur, was sie offen lässt. Ein
eigener Wert bleibt gespeichert, auch wenn die Quelle ihn gerade verdeckt, und
greift wieder, sobald sie nichts mehr liefert.

**Der Detailbereich.** Gepflegt wird in einer aufklappbaren Zeile, nicht mehr
in der Tabellenzelle — acht Felder passen dort nicht. Er erklärt sich auch im
Normalfall und nennt Herkunft und Stand der Daten; wo die Quelle übersprungen
wurde, sagt er den **tatsächlichen** Grund (kein ETF / keine ISIN / ISIN außerhalb
Europas / abgefragt und leer), in der Reihenfolge, in der das Backend prüft.

**Ins Fundament ausgelagert.** `UxCaret` ersetzt fünf handgezeichnete Pfeile in
zwei Apps, `UxInfoHint` kennt neben dem Fragezeichen ein (i). Beides liegt in
`@mmit/ux-foundation`; Ticket dort: T-16.

**„Schublade" heißt „Detailbereich".** Das alte Wort war eine Fehlbenennung:
„drawer" ist in der UI-Sprache für das Seitenpanel belegt, das von der Kante
hereinfährt — dieser Bereich klappt in der Zeile auf. Umbenannt wurde von Hand,
weil das Deutsche dabei den Fall wechselt.

**Befunde eines Codex-Scans**, im selben Zug behoben: zwei Datenverlust-Fehler
(Duplikat-Migration, Provider-Ausfall), geratene Ausschüttungspolitik,
nicht-endliche Kurse, ein blinder Healthcheck sowie Symbol-, Datums- und
Statuscode-Validierung.

## Auflösung

Gemerged als `1c2fe50` (`--no-ff`, 55 Commits). Die tragenden:

| Commit | Was |
|---|---|
| `75f4b46` | Detailbereich nennt den richtigen Grund für die leere Quelle |
| `3df83fd` | nennt die Quelle der Kennzahlen |
| `b95d898` | Escape schließt erst die Auswahlliste, dann den Detailbereich |
| `a1cdefa` | Pfeil mittig und größer — Form statt Zeichen |
| `d913827` | Pfeil und Erklärzeichen kommen aus dem Fundament |
| `b6893d8` | Fläche nur an den Feldern, die sich ändern lassen |
| `41a35d4` | „Schublade" → „Detailbereich" |
| `07848d3` | Metadaten überleben Duplikat-Merge und Provider-Ausfall |
| `91ed077` | unbrauchbare Zahlen, geratene Aussagen, blinder Healthcheck |
| `62a0444` | Symbole, Zeitgrenzen und Statuscodes prüfen |
| `3bf1f66` | Betriebsmodell und Readiness im README |

## Was bewusst offen bleibt

Aus dem Codex-Scan **nicht** angegangen, auf Zuruf zurückgestellt:

- **SEC-01** — kein Zugriffsschutz. Die App hat keine Authentifizierung und
  bindet an `0.0.0.0`; entschieden wurde, das im README zu dokumentieren statt
  Auth einzubauen. Der Abschnitt „Security model" nennt die betroffenen
  Endpunkte und die drei tragfähigen Betriebsarten.
- **SEC-03** — Security-Header und erlaubte URL-Schemata.
- **SUPPLY-01** — Base-Images auf Digest pinnen, hashbasierter Python-Lock.
- **MAINT-01** — `quote_cache.py`, `repository.py` und `InstrumentsTable.vue`
  bündeln je mehrere Themen. Ein eigener Umbau, kein Nebenher.

## Berührte Repos

| Repo | Was |
|---|---|
| `StockInfo/app` | acht Override-Felder, Merge-Regeln der Migration, `metadata_complete`, Metadaten-TTL, Validierung, `/ready` |
| `StockInfo/dashboard` | Detailbereich, `MetricEditor`, Kartenliste, Escape, Umbenennung |
| `ux-foundation` | `UxCaret`, `(i)`-Fassung von `UxInfoHint` — dort T-16 |
| `StockPortfolio` | drei handgezeichnete Pfeile auf `UxCaret` umgestellt |
