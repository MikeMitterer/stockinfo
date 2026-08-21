# T-24 · Den REST-Core als Vertrag festschreiben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 6 h | Vertrag festschreiben + eine bewusste Verhaltenskorrektur | — |

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
| 1 | Vertragsdokument | Core-Pflichtfelder samt Nullability sind benannt | | |
| 2 | dasselbe | Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale` steht fest | | |
| 3 | dasselbe | bereinigt gegen unbereinigt beim Tages-Schlusskurs ist entschieden | | |
| 4 | dasselbe | `listing_id` und das Verhalten bei mehrdeutigem `symbol` sind festgelegt | | |
| 5 | dasselbe | Regel, was additiv ist und was ein Bruch wäre | | |
| 6 | Core-Fixtures | liegen als Datei vor und sind von außen nutzbar | | |
| 7 | OpenAPI-Schnappschuss | ein Test schlägt an, wenn sich der Core unbemerkt ändert | | |
| 7b | **`GET /fields`** | liefert die Pflichtfelder **samt Vertragsversion** — zur Laufzeit abfragbar, nicht nur dokumentiert | | |
| 7c | Vertragsversion erhöhen | ein Konsument kann an der Nummer erkennen, dass er prüfen muss | | |
| 7d | Vertragsdokument | **Schema** von `GET /generation` steht fest: nur `generation_id` (opake UUID), `Cache-Control: no-store` | | |
| 7e | dasselbe | **Name und Semantik** von `StockInfo-Generation` stehen fest — Pflicht auf **jeder** Antwort, auch `404`/`409`/`422`/`502` | | |
| 7f | dasselbe | Regel „Header und Rumpf stammen aus **derselben** Generation" ist festgeschrieben | | |
| 7g | dasselbe | `Access-Control-Expose-Headers` ist als Vertragspflicht benannt — ohne sie ist der Header cross-origin unlesbar | | |
| 7h | HTTP-Fixtures | enthalten Positiv- **und** Negativfälle: `200`+Header, `404`/`502`+Header, generationenfähige Antwort **ohne** Header (Vertragsfehler), Header/Body-Widerspruch bei `/generation` | | |
| 7i | OpenAPI-/Vertragsprüfung | schlägt an, wenn Endpunkt, Headername oder Schema von dieser Definition abweichen | | |

**Ebene 2 — bewusste Verhaltenskorrektur (kein „nur Dokumentation"):**

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 8 | Antwort mit Preis, aber ohne Währung von der Quelle | **Fehler** statt Antwort mit geratenem Wert | | |
| 9 | Bestandsprüfung | wo der heutige Code den Mindestvertrag verletzt, ist es benannt und behoben | | |
| 10 | `make test` | grün | | |

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
| OpenAPI-/Vertragsprüfung gegen die Definition | atomare Bindung Request ↔ DB ↔ Generation |

T-24 formuliert also „Vertrag und Fixture legen fest", nicht „der Server tut".
So kann T-24 abgeschlossen werden, bevor eine Zeile Middleware existiert — und
genau das ist der Sinn eines Vertrags.

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

## Auflösung

_(offen)_
