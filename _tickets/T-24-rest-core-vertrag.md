# T-24 · Den REST-Core als Vertrag festschreiben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | codex-abgenommen | 6 h | Vertrag festschreiben + eine bewusste Verhaltenskorrektur | — |

**Zwei Übergaben statt einer** *(Claude, 2026-08-21)*: Das Ticket zerfällt an
einer natürlichen Kante in Definition und Laufzeit — dieselbe Trennlinie, die
T-24 von T-25 trennt. Ein einzelner Commit über beides wäre für einen
Diff-Review zu groß.

| | Umfang | Zeilen | Commit |
|---|---|---|---|
| **Teil 1** | Vertragsartefakt, Fixtures, statische Konsistenz | `#1`–`#6`, `#7d`–`#7i` | `9d01750` ✔ abgenommen |
| **Teil 2** | `GET /fields`, OpenAPI-Schnappschuss, Währungskorrektur | `#7`, `#7b`, `#7c`, `#8`–`#10` | in Arbeit |

Teil 1 ist von Codex in Runde 2 ohne Findings freigegeben (`9d01750`). Runde 1
hatte zwei Befunde gebracht — beide eingearbeitet, siehe Fußnoten `#7h`/`#7i`.

**Löst:** Was die API zusagt, ergibt sich heute aus dem Code — nirgends steht,
welche Felder verbindlich sind, was `stale` bedeutet oder ob ein Schlusskurs
bereinigt ist. Solange das so bleibt, ist jede Änderung an der Identität ein
Blindflug.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** nichts. **Blockiert: T-21** — erst wissen, was zugesagt ist, dann
die Identität ändern.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

**Ebene 1 — jetzt festschreiben und gegen den Bestand prüfen:**

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Vertragsdokument | Core-Pflichtfelder samt Nullability sind benannt | ✅ [^a] | |
| 2 | dasselbe | Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale` steht fest | ✅ [^b] | |
| 3 | dasselbe | bereinigt gegen unbereinigt beim Tages-Schlusskurs ist entschieden | ✅ [^c] | |
| 4 | dasselbe | `listing_id` und das Verhalten bei mehrdeutigem `symbol` sind festgelegt | ✅ [^d] | |
| 5 | dasselbe | Regel, was additiv ist und was ein Bruch wäre | ✅ [^e] | |
| 6 | Core-Fixtures | liegen als Datei vor und sind von außen nutzbar | ✅ [^f] | |
| 7 | OpenAPI-Schnappschuss | ein Test schlägt an, wenn sich der Core unbemerkt ändert | ✅ [^m] | |
| 7b | **`GET /fields`** | liefert die Pflichtfelder **samt Vertragsversion** — zur Laufzeit abfragbar, nicht nur dokumentiert | ✅ [^n] | |
| 7c | Vertragsversion erhöhen | ein Konsument kann an der Nummer erkennen, dass er prüfen muss | ✅ [^o] | |
| 7d | Vertragsdokument | **Schema** von `GET /generation` steht fest: nur `generation_id` (opake UUID), `Cache-Control: no-store` | ✅ [^g] | |
| 7e | dasselbe | **Name und Semantik** von `StockInfo-Generation` stehen fest — Pflicht auf **jeder** Antwort, auch `404`/`409`/`422`/`502` | ✅ [^h] | |
| 7f | dasselbe | Regel „Header und Rumpf stammen aus **derselben** Generation" ist festgeschrieben | ✅ [^i] | |
| 7g | dasselbe | `Access-Control-Expose-Headers` ist als Vertragspflicht benannt — ohne sie ist der Header cross-origin unlesbar | ✅ [^j] | |
| 7h | HTTP-Fixtures | enthalten Positiv- **und** Negativfälle: `200`+Header, `404`/`502`+Header, generationenfähige Antwort **ohne** Header (Vertragsfehler), Header/Body-Widerspruch bei `/generation` | ✅ [^k] | |
| 7i | **statisches** Vertragsartefakt und Fixtures | sind untereinander konsistent — jede Fixture erfüllt das dokumentierte Schema, Endpunktpfad und Headername stimmen überein. **Ohne laufende App.** Die Live-Konformität nimmt T-25 `#7j` ab | ✅ [^l] | |

```bash
.venv/bin/pytest tests/test_contract.py -q    # #7i und die Fixture-Zeilen
```

[^a]: `contract/core-contract.json` → `core`, fünf Modelle (`quote`,
    `instrument`, `daily`, `history`, `fx`), je Feld `kind`, `required` und
    `meaning`. Erzwungen von
    `test_jeder_antworttyp_hat_felder_mit_art_und_pflicht`: Ein Feld ohne
    Bedeutung oder mit unbekannter Art lässt den Test fallen.
[^b]: `docs/rest-core-contract.md` → „Die Begriffe, die sich sonst niemand
    erschließt", plus `meaning` je Feld im Artefakt. `quote_time` gegen
    `fetched_at` und `cached` gegen `stale` sind gegeneinander abgegrenzt;
    `stale=true` zieht `cached=true` nach sich. Belegt durch die Fixture
    `quote-200-stale.json`.
[^c]: **Unbereinigt.** Begründung im Dokument: Eine bereinigte Reihe ändert
    rückwirkend alte Werte, und ein Depot mit Stückzahlen zu historischen
    Kursen rechnet damit falsch. Im Artefakt unter `core.daily.close`.
[^d]: Artefakt → `identity`: opake UUID, nicht abgeleitet, nicht zerlegbar;
    `symbol` nicht garantiert eindeutig; `409` samt Kandidatenliste. Die
    Fixture `quote-409-ambiguous-symbol.json` zeigt den Rumpf.
[^e]: Artefakt → `compatibility` mit `additive`, `breaking`, `versioning` und
    der Konsumentenregel „unbekannte Felder ignorieren".
[^f]: Dreizehn Dateien unter `contract/fixtures/`, dazu `contract/README.md`
    mit dem Umschlagformat. Von außen nutzbar heißt: StockPortfolio liest sie,
    ohne StockInfo zu starten oder das Repo zu klonen.
[^g]: Artefakt → `generation.endpoint`, `cache_control`, `id_kind`; Fixture
    `generation-200.json`. Nur `generation_id`, sonst nichts.
[^h]: Artefakt → `generation.required_on_every_response`. Fixtures für `404`
    und `502` tragen den Header; `test_fixture_traegt_den_generationsheader`
    lässt keine vertragstreue Fixture ohne ihn durch.
[^i]: Artefakt → `generation.rule`, ausformuliert samt Begründung (UUIDs
    tragen keine Reihenfolge, deshalb ist `/generation` die Wahrheit und der
    Header nur das Signal). Geprüft von
    `test_generationsfixture_haelt_header_und_rumpf_zusammen`.
[^j]: Artefakt → `generation.expose_headers_required`; im Dokument unter „CORS
    gehört dazu". Die Fixture `quote-200-ohne-generationsheader.json` nennt
    den fehlenden Expose-Header als praktische Ursache desselben Symptoms.
[^k]: Zwei Negativfälle — `quote-200-ohne-generationsheader.json` und
    `generation-200-header-widerspricht-rumpf.json` — dazu die Positivfälle
    `quote-404.json` und `quote-502.json` **mit** Header. `violates` ist ein
    Regelschlüssel, zu dem eine Prüfung gehört: Nach Codex' Befund aus Runde 1
    genügte vorher irgendein Text, und eine Fixture hätte unbemerkt aufhören
    können, negativ zu sein. `test_die_geforderten_negativfaelle_sind_vorhanden`
    verhindert außerdem, dass Löschen ein Weg zum Grün wird.
[^l]: `.venv/bin/pytest tests/test_contract.py -q` → `49 passed, 29 skipped`.
    Der Test importiert die App **nicht**. Geprüft wird jetzt auch, dass
    Methode, Pfad und Query-Namen jeder Fixture zum Endpunkt passen und dass
    `endpoint` und `model` zusammengehören (bei Fehlerantworten: kein
    Core-Modell). Gesamtsuite `305 passed, 29 skipped`, Ruff sauber.

    **Mutationsprobe** — die Prüfung schlägt an, wenn ein Negativfall aufhört,
    einer zu sein: Header ergänzt → rot, UUID-Widerspruch aufgelöst → rot,
    `?limit=3` an `/daily` → rot. Danach wieder `49 passed`. Dauerhaft
    abgesichert durch
    `test_die_pruefung_erkennt_eine_luegende_negativfixture`.

**Ebene 2 — bewusste Verhaltenskorrektur (kein „nur Dokumentation"):**

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 8 | Antwort mit Preis, aber ohne Währung von der Quelle | **Fehler** statt Antwort mit geratenem Wert | ✅ [^p] | |
| 9 | Bestandsprüfung | wo der heutige Code den Mindestvertrag verletzt, ist es benannt und behoben | ✅ [^q] | |
| 10 | `make test` | grün | ✅ [^r] | |

[^m]: `contract/openapi-core-snapshot.json` plus
    `tests/test_contract_openapi.py`. Erfasst sind die neun zugesagten Pfade
    und die Modelle dahinter, **transitiv** — nicht das ganze Dokument: Ein
    Abbild über alles wäre bei jeder Änderung an einem Diagnoseendpunkt rot,
    und einen Test, der grundlos anschlägt, liest bald niemand. Die
    Verweisverfolgung kam in Runde 3 dazu: Vorher lagen nur die direkt
    genannten Schemas im Schnappschuss, `FieldSpec` und `EndpointSpec` fehlten
    — `/fields` war damit nur eine Ebene tief geschützt.
    **Mutationsprobe, fünf Fälle:** neues Feld an `QuoteResponse` → rot, neuer
    Query-Parameter an `/fx` → rot, `core_version` erhöht → rot,
    `FieldSpec.meaning` von `string` auf `integer` → rot, `EndpointSpec.method`
    ebenso → rot. Danach wieder grün.
[^n]: `GET /fields`, bedient aus `contract/core-contract.json` über
    `app/contract.py` — **eine** Quelle für Fixtures und Laufzeit. Fünf Tests
    in `tests/test_api_fields.py`, darunter der Nachweis, dass die Antwort mit
    dem Artefakt übereinstimmt, und dass `currency` im Kurs Pflicht ist, in
    der Instrumentenzeile nicht. Fehlt das Artefakt, antwortet der Endpunkt
    mit 503 statt mit einer leeren Feldliste, die wie eine Zusage aussähe.
    Das Dockerfile kopiert `contract/` jetzt ins Image — ohne diese Zeile
    liefe der Endpunkt lokal und im Container nicht.
[^o]: `core_version` steht im Artefakt, in der Antwort von `/fields` **und**
    im Schnappschuss. **Mutationsprobe:** `core_version` auf `1.1.0` gesetzt →
    der Schnappschuss-Test wird rot und nennt den Weg (Version erhöhen,
    Schnappschuss erneuern). Ein Konsument sieht dieselbe Nummer über
    `/fields`.
[^p]: `ensure_core_complete` in `app/services/quote_service.py`, aufgerufen in
    `_build`. Die Feldliste kommt aus dem Artefakt (`required_fields("quote")`),
    nicht aus einer zweiten Aufzählung — sonst verspräche `/fields` etwas
    anderes, als der Code durchlässt. Test
    `test_preis_ohne_waehrung_ist_kein_verwertbarer_kurs` (zuerst rot); der
    Router bildet auf 502 ab.
[^q]: Drei Verletzungen gefunden, alle behoben — Einzelheiten unten unter
    „Bestandsprüfung". Kurz: Kurs ohne Währung (jetzt Fehler), Tagespunkt ohne
    Währung und Historienpunkt ohne Währung (beide erben jetzt die Währung des
    Listings, sonst Fehler). Je ein Test, alle zuerst rot.
[^r]: `make test` → Backend `321 passed, 29 skipped`, Plugin-API `36 passed`,
    Dashboard `230 passed`. Ruff über `app` und `tests` sauber.

**Ebene 3 — hier nur benannt, umgesetzt anderswo:** `ticker`/`mic` → T-21,
`details`-Container → T-26, `generation_id` → T-25.

---

## Details

### Der Kernpunkt: eindeutige Adressierung

`(ticker, mic)` wird die Identität — aber den Unique-Index auf `symbol` einfach
zu entfernen, wäre ein stiller Bruch. Es gibt **acht** symbolbasierte
Endpunkte, und der Lookup dahinter lautet:

```sql
SELECT * FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1
```

Nicht undefiniert, sondern **definiert falsch**: Bei zwei gleichnamigen Zeilen
trifft `DELETE /instruments/by-symbol/{symbol}` die ältere.

**Festzulegen ist deshalb:**

- **`listing_id`** — eine **opake UUID**, bei Anlage einmal erzeugt und
  **nicht** aus `ticker`, `mic`, ISIN oder dem lokalen Integer-Schlüssel
  abgeleitet
- **`symbol`** — bleibt Pflichtfeld und Anzeigename, aber **nicht** garantiert eindeutig
- Symbol-Endpunkte antworten bei Mehrdeutigkeit mit **`409 Conflict`** samt
  Kandidatenliste, statt still das Falsche zu treffen

**Warum opak und warum UUID** *(Codex, 2026-08-20)*: Ein Hash aus `(ticker, mic)`
existiert für offene Legacy-Zeilen gar nicht und änderte sich bei jeder
fachlichen Listing-Korrektur. Ein lokaler Integer wäre an der REST-Grenze zu
leicht mit einer über Generationen stabilen Identität zu verwechseln. Daraus
folgen klare Regeln:

- **jede** Zeile bekommt sofort eine `listing_id` — auch eine mit
  `identity_status = legacy_unresolved`
- die ID überlebt manuelle Zuordnung und normale Metadatenänderungen
- Sicherung und Wiederherstellung erhalten sie
- eine frische Profil-B-Datenbank vergibt neue IDs; den Datensatzwechsel zeigt
  `generation_id` an
- Konsumenten behandeln sie als **opaken String** und zerlegen sie nie

**Wo es kollidieren kann:** derzeit nur dort, wo mehrere MICs dasselbe leere
Suffix teilen — also bei US-Börsen, sobald `US` in `XNYS`/`XNAS` zerfällt (durch
T-21). „Derzeit" ist dabei wörtlich zu nehmen: Regionale Plugins können weitere
MICs und Symbolkonventionen mitbringen. Die Laufzeitprüfung und die
`409`-Regel gelten deshalb **allgemein**, nicht nur für US-Listings.

### Ein aktives Listing je ISIN — heute eine Grenze, kein Zufall

`isin TEXT UNIQUE` in der Datenbank bedeutet: **ein** aktives Listing je ISIN und
Datenbank. Das passt zum Modell — ein Profil wählt genau ein Listing, T-19
ersetzt es gegebenenfalls.

Das gehört ausdrücklich in den Vertrag, sonst suggerieren `listing_id` und
`(ticker, mic)`, StockInfo könne mehrere gleichzeitige Listings derselben ISIN
führen. Soll das später möglich sein, ist es eine eigene Schema- **und**
Konsumenten-Erweiterung.

### Was sonst festzulegen ist

- Core-Pflichtfelder und ihre Nullability
- kanonische Identität `(ticker, mic)`, `listing_id` als Schlüssel, `symbol` als
  garantierter Anzeigewert
- **Pflichtwährung** für verwertbare Preise und Tagespunkte
- Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale`
- bereinigt gegen unbereinigt beim Tages-Schlusskurs
- die additive `details`-Hülle: unbekannte Einträge müssen ignorierbar sein
- Fehlerverhalten bei unvollständigem Core — **kein** Raten
- was additiv ist und was ein Bruch wäre
- Profil-/Datensatz-Generation, damit Konsumenten einen Wechsel bemerken

### Der Vertrag ist abfragbar, nicht nur dokumentiert

*(Mikes Anforderung, 2026-08-20.)* Ein Dokument, das niemand zur Laufzeit lesen
kann, hilft einem Konsumenten nicht. Deshalb liefert `GET /fields` die
Pflichtfelder **samt Vertragsversion**:

**Nach Antworttyp gegliedert, nicht flach** *(Codex, 2026-08-20)*: StockInfo hat
nicht einen Core, sondern mehrere öffentliche Modelle. Ein flaches Array mit
`price` und `currency` sagt nicht, in welcher Antwort sie Pflicht sind — damit
wäre die abfragbare Nullability ungenauer als das vorhandene OpenAPI-Dokument.

```
GET /fields
{
  "core_version": "1.2.0",
  "core": {
    "quote":      [ {"name": "price", "kind": "number", "required": true}, … ],
    "instrument": [ … ],
    "daily":      [ … ],
    "fx":         [ … ]
  },
  "details_version": 7,          ← die offene Menge, siehe T-26
  "details": [ … ]
}
```

Dieselbe Logik für beide Ebenen: Der Core hat eine Vertragsversion, die offenen
Details haben eine eigene Nummer. Ein Konsument mit gecachter Feldliste erkennt
an der Nummer, dass er neu holen muss — ohne den Inhalt zu vergleichen.
Zwischenspeichern sollte er unter `(generation_id, details_version)`.

**Regel für `core_version`:**

| Stufe | Wann |
|---|---|
| Major | Pflichtfeld entfernt oder unverträglich geändert |
| Minor | additive Erweiterung des Core |
| Patch | Klarstellung ohne Änderung am JSON-Vertrag |

Die Fixtures aus dem Verify-Teil sind der statische Gegenpart dazu: Sie prüfen
denselben Vertrag beim Bauen, `GET /fields` beantwortet ihn im Betrieb.

### Der Generationstransport: `/generation` plus Header

*(Codex, 2026-08-21 — Antwort auf meine drei Teilfragen. Ich hatte zum Header
allein geneigt; das wäre ein Fehler gewesen, siehe unten.)*

**Kanonisch ist ein eigener, schmaler Endpunkt:**

```http
GET /generation
Cache-Control: no-store

{ "generation_id": "550e8400-e29b-41d4-a716-446655440000" }
```

Nicht `/env` (ein Diagnosemodell voller Details, die kein Konsument braucht) und
nicht `/sources` (beschreibt die Quellenkette — deren Zustand kann sich ändern,
**ohne** dass die Datenbankgeneration wechselt). Ein Konsument muss die
Generation abrufen können, **bevor** er persistente Kursdaten hydriert, ohne die
ganze Umgebung zu laden.

`generation_id` ist ein opaker UUID-String; verglichen wird nur auf Gleichheit.
Profilname und Kompatibilitäts-ID dürfen additiv danebenstehen, sind aber **keine
Cache-Identität**.

**Dazu ein Header auf jeder Antwort — auch auf Fehlern:**

```http
StockInfo-Generation: 550e8400-e29b-41d4-a716-446655440000
```

Die Fehlerfälle sind kein Detail: Nach einem Profilwechsel kann ein bisher
bekanntes Papier im neuen Profil fehlen. Ohne Header auf der `404` zeigt der
Konsument seinen alten Cache weiter.

**Warum der Header allein nicht genügt** — das ist der Punkt, den ich übersehen
hatte: Zwei Anfragen können sich über einen Profilwechsel hinweg überschneiden.
Eine verspätete Antwort aus A trifft nach einer schnellen aus B ein. **UUIDs
tragen keine Reihenfolge**, also würde ein Client, der dem Header blind folgt,
von B zurück auf A springen.

Deshalb: **`/generation` ist die Wahrheit, der Header nur das Signal.** Weicht er
ab, wird die Antwort verworfen, `/generation` bestätigt den Stand, und erst
danach wird umgeschaltet. Kein Polling, keine Extra-Anfrage vor jedem Request.

**CORS nicht vergessen** — nachgeprüft in `app/main.py:61-66`:

```python
allow_headers=["*"]     # ← gilt für REQUEST-Header
                        # expose_headers fehlt
```

Ohne `expose_headers` kann Browser-JavaScript den Antwort-Header nicht lesen.
StockPortfolio läuft cross-origin; der Header wäre dort unsichtbar.

#### Was hier abgenommen wird — und was nicht

*(Codex, 2026-08-21 — ich hatte die gerade entfernte Ticket-Schleife in
kleinerer Form wieder eingebaut.)*

Die Zeilen `#7d`–`#7i` verlangten in der vorigen Fassung die **laufenden**
Endpunkte samt Middleware und CORS-Konfiguration. Zugleich hängt T-25 an T-24 —
also hätte T-24 erst nach T-25 fertig werden können, T-25 aber erst nach T-24
beginnen dürfen. Ein Zyklus.

Die Trennlinie läuft deshalb zwischen **Definition** und **Laufzeit**:

| T-24 besitzt | T-25 besitzt |
|---|---|
| Schema von `GET /generation` | die Route selbst |
| Name und Semantik des Headers | Middleware, die ihn setzt |
| Regeln für Fehlerantworten, CORS, `no-store` | `expose_headers` in der App |
| HTTP-Fixtures, positiv **und** negativ | persistierte aktive UUID, Rotation |
| **statische** Konsistenz von Artefakt und Fixtures | **Live-OpenAPI** stimmt mit dem Artefakt überein |
| — | atomare Bindung Request ↔ DB ↔ Generation |

T-24 formuliert also „Vertrag und Fixture legen fest", nicht „der Server tut".
So kann T-24 abgeschlossen werden, bevor eine Zeile Middleware existiert — und
genau das ist der Sinn eines Vertrags.

**Der Schrägstrich in „OpenAPI-/Vertragsprüfung" war die letzte Lücke**
*(Codex, 2026-08-21)*: Wird die OpenAPI aus der **laufenden** FastAPI-App
erzeugt, verlangt T-24 wieder die Route, die erst T-25 baut — die Schleife wäre
im Kleinen zurück. `#7i` prüft deshalb ausdrücklich nur das **statische**
Artefakt gegen die Fixtures; dass die laufende App diesem Artefakt entspricht,
nimmt T-25 `#7j` ab.

### Warum das vor T-21 gehört

StockInfo ist verteilt (GitHub, Docker Hub, Unraid-Template). Wer die API direkt
nutzt statt des mitgelieferten Dashboards, bekommt jeden Bruch ab — und man
erfährt es nicht.

Dazu kommt der Testkonsument StockPortfolio. Er gehört demselben Autor, ist aber
ein **eigenes Artefakt mit eigenem Image und eigenem Update-Zeitpunkt**: Auf
einer Unraid-Box laufen beide als getrennte Container, die niemand gleichzeitig
aktualisiert. Gemeinsame Eigentümerschaft ersetzt keinen Vertrag.

### Prüfbar, ohne Cross-Repo-CI

1. StockInfo prüft den Core gegen **Fixtures** und einen
   OpenAPI-Kompatibilitätsschnappschuss. Die Fixtures sind kein reines JSON,
   sondern ein **HTTP-Umschlag aus Status, Headern und Rumpf** — sonst lässt
   sich das Header-Verhalten der Generation gar nicht prüfen.
2. StockPortfolio prüft seine Mapper gegen dieselben veröffentlichten Fixtures.
3. Vor Releases ein kleiner Lauf: bestehende Position gegen frische Profil-DB.

Kein Repo klont das andere.

---

## Bestandsprüfung (`#9`)

Drei Stellen, an denen der Code den eigenen Mindestvertrag verletzte. Alle drei
haben dieselbe Wurzel: `currency` war überall optional, weil niemand
aufgeschrieben hatte, dass sie es nicht sein darf.

| Wo | Was passierte | Weg |
|---|---|---|
| `quote` (live) | Ein Preis ohne Währung ging durch und wurde gespeichert | `ensure_core_complete` in `_build` → Fehler statt Antwort |
| `quote` (Cache) | **Nachgetragen in Runde 3.** `_from_cache` setzte zwar die Währung des Instruments ein, prüfte aber nicht, ob auch die fehlt — und über diesen Weg läuft der Normalfall | dieselbe Prüfung in `_from_cache`, für den frischen **und** den `stale`-Fall |
| `daily` | `DailyPoint.currency` kam roh aus der Zeile; `upsert_daily_closes` schreibt `NULL`, wenn die Quelle nichts nennt | Währung des **Listings** einsetzen; kennt auch das Instrument keine → Fehler |
| `history` | dasselbe für `QuotePoint` — ältere Zeilen können ohne Währung gespeichert sein | ebenso |

Der Cache-Fall ist der Beleg dafür, dass „an allen Stellen umgesetzt" eine
Behauptung war und keine Feststellung: Ich hatte den Live-Pfad geprüft und
daraus geschlossen, dass die Regel greift. Codex hat den meistgenutzten Weg
gegengeprüft und eine erfolgreiche Antwort mit `currency=None, cached=True`
erhalten.

Bei `daily` und `history` ist das kein Raten: Die Währung gehört zum Listing,
nicht zum einzelnen Tag. Dieselbe Notiz, dieselbe Währung. Ein Fehler bleibt
nur der Fall, in dem auch das Instrument keine kennt — dann fehlt die Angabe
wirklich.

**Was geprüft und in Ordnung war:** `instrument` (`history_count`,
`manual_fields`, `shadowed_fields` sind immer gesetzt), `fx` (alle
Pflichtfelder sind im Modell nicht optional) und die Zeitstempel in allen
Modellen.

---

## Auflösung

**Stand 2026-08-22 — beide Teile umgesetzt.**

| | Umfang | Commit | Stand |
|---|---|---|---|
| Teil 1 | Vertragsartefakt, Fixtures, statische Konsistenz | `9d01750` | abgenommen (Runde 2) |
| Teil 2 | `GET /fields`, OpenAPI-Schnappschuss, Währungspflicht | `f10f45e` | abgenommen (Runde 4) |

Vier Runden, vier Befunde, alle von Codex gefunden und keiner bestritten. Zwei
davon waren dasselbe Muster: eine Regel dort umgesetzt, wo sie mir auffiel, und
für allgemein gehalten. Die Abnahme durch Mike läuft gesammelt über **T-28**.

**Neu im Repo:** `contract/core-contract.json` (verbindlich),
`contract/openapi-core-snapshot.json` (Wächter), dreizehn Fixtures,
`docs/rest-core-contract.md` (Erklärung), `app/contract.py` (ein Leser für
beide Wege), `app/routers/fields.py`.

**Drei Wächter, jeder mit Gegenprobe:**

1. Artefakt ↔ Fixtures, ohne App (`test_contract.py`) — drei Mutationen erkannt.
2. App ↔ Schnappschuss (`test_contract_openapi.py`) — drei Mutationen erkannt.
3. Code ↔ Artefakt: `ensure_core_complete` liest die Pflichtfelder aus dem
   Artefakt, statt sie zu wiederholen.

**Nicht in diesem Ticket, bewusst:** `listing_id` und `(ticker, mic)` (T-21),
der `details`-Container (T-26), die Laufzeitseite der Generation — Route,
Middleware, `expose_headers` (T-25). Sie stehen im Artefakt unter `planned`,
getrennt vom zugesagten Core.
