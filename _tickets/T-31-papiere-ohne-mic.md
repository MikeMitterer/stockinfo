# T-31 · Papiere ohne echten MIC — Krypto, Index, Anleihe

- **Status:** offen (entschieden 2026-08-28)
- **Angelegt:** 2026-08-25, beim Bau von T-21 Teil 3, Übergabe 2A
- **Entschieden:** 2026-08-28, Mike im Gespräch mit Claude — Details unten
- **Repo:** StockInfo
- **Abhängt von:** T-21 Teil 3 (Entscheidung 2)
- **Verzahnt mit:** T-38 (Pflichtfelder/`instrument_type` — **ein** gemeinsamer
  `API_VERSION`-Sprung statt zwei) und T-37 (der YAML-Fallback bekommt einen
  zweiten Einsatzort, siehe dort)

## Verify-Matrix

| # | Where | Look for | AI | Human |
|---|---|---|---|---|
| 1 | Entscheidung | Mike hat entschieden: Krypto und Anleihen kommen in den MVP, mit eigener Identitätsform und eigenem Typ; Indizes bleiben draußen | ✅ [^a] | |
| 2 | `app/db.py` | die Identität ist eine getaggte Union: `kind` ∈ `listed`/`pair`/`isin_only`, ein `CHECK` je `kind` erzwingt genau die passende Feldbelegung — halbe Identitäten bleiben unmöglich | | |
| 3 | `app/exchanges.py`, Contract-Kit | `canonical_identity` wird zur Weiche über die Union; `is_real_mic` und `is_canonical_ticker` bleiben unverändert die `listed`-Hälfte. Im Vertrag: discriminated union über `kind` | | |
| 4 | Typ-Katalog | `stock`/`etf`/`etc`/`crypto`/`bond` kanonisch (Ort: T-38); `QUOTE_TYPE_MAP` erweitert um `CRYPTOCURRENCY → crypto`, `BOND → bond` — Erkennen, nicht Raten | | |
| 5 | Aufnahmeweg | die Paar-Identität entsteht aus dem **Gattungs-Befund der Quelle**, nie aus der Symbolform; Eintritt per Symbol (`isin = NULL`), die By-Symbol-Routen tragen ihn | | |
| 6 | Aufnahmeweg | eine **nicht** aufgenommene Gattung (Index) wird mit eigener Kennung `unsupported_instrument_type` abgelehnt — nicht mit dem Zufallsbefund der Symbolform; i18n DE/EN | | |
| 7 | Kursweg | für ein Paar muss die Währung des gelieferten Kurses `quote_currency` entsprechen; eine Abweichung ist ein Datenfehler und wird abgelehnt, nicht still konvertiert | | |
| 8 | Metadatenkaskade | sie läuft nur für Typen, deren Metadaten es geben kann — kein justETF-Abruf für eine Coin, keine TER-Frage an eine Anleihe | | |
| 9 | Tests | `BTC-EUR` prüft das **entschiedene** Verhalten (Annahme als `pair`), ein Index den Ablehnungsgrund, eine Anleihe die `isin_only`-Form samt `quote_unavailable` ohne liefernde Quelle | | |

[^a]: Entschieden am 2026-08-28; die einzelnen Punkte stehen unter
    **Die Entscheidung**. Die Human-Spalte bleibt für Mikes Bestätigung des
    fortgeschriebenen Tickets.

## Die Entscheidung (Mike, 2026-08-28)

1. **Option 3 aus der Fundliste** — eine eigene Identitätsform für Gattungen
   ohne Handelsplatz. Krypto und Anleihen sollen **schon im MVP** erfassbar
   sein.
2. **Jede Gattung bekommt einen eigenen Typ.** Kanonischer Katalog:
   `stock`, `etf`, `etc`, `crypto`, `bond`. ETC ist als gängiger Typ bestätigt;
   ETN kann später ergänzt werden, wenn gebraucht.
3. **Kein Migrationspfad.** Die bestehende Entwicklungsdatenbank wird verworfen;
   das neue Schema wird direkt angelegt.
4. **Indizes bleiben draußen** — sie waren Teil des Fundes, sind aber nicht
   Teil der Entscheidung. Sie werden ehrlich abgelehnt
   (`unsupported_instrument_type`), bis eine eigene Entscheidung sie aufnimmt.
5. **Anleihen werden ausschließlich über Quellen bepreist.** Die Handpflege
   (`instrument_overrides`) bleibt Metadaten — ein Preis ist ein Messpunkt mit
   Herkunft (`price NOT NULL`, `quote_time`, `fetched_at`), kein pflegbares
   Attribut. Kein Preis heißt kein Quote-Datensatz, nicht ein Quote mit Lücke.
6. **Der YAML-Fallback wird zum Kettenglied des Online-Profils** (Mikes
   Vorschlag): Das Online-Profil hängt das ohnehin in T-37 gebaute YAML-Plugin
   ans **Ende** seiner Kette. Eine Anleihe fällt durch die Online-Quellen
   durch und landet bei der Datei — im laufenden Online-Profil, ohne
   Profilwechsel. Es bleiben zwei Profile: reines YAML oder die Online-Kette
   mit demselben YAML-Plugin an letzter Stelle.

**Offen als eigene Entscheidungszeile:** eine *manuelle Quelle* — ein
Eingabeweg im Dashboard, der einen vollwertigen Quote schreibt (`price`,
`quote_time`, `provider: manual`). Wenn gewollt, ist das ein eigenes kleines
Feature und **keine** Override-Spalte. Für den MVP zurückgestellt; der
YAML-Fallback deckt den Bedarf.

## Der Entwurf: Identität als getaggte Union

Die T-21-Lehre bleibt: kein Wert, der etwas anderes vorgibt zu sein. Statt
eines Sentinel-MIC bekommt die Identität einen expliziten Diskriminator:

```
kind = 'listed'     → ticker + mic          (Aktie, ETF, ETC, börsengehandelte Anleihe)
kind = 'pair'       → base + quote_currency (natives Krypto: BTC/EUR)
kind = 'isin_only'  → isin                  (OTC-Anleihe: die ISIN ist die Identität)
```

- **SQLite:** `ticker`/`mic` werden wieder nullable; der `CHECK` verlangt je
  `kind` die Identitätsfelder dieser Form und schließt alle Identitätsfelder
  der beiden anderen Formen aus. „Vollständig" ist damit je Gattung
  definiert, halbe oder doppelte Identitäten bleiben unmöglich.
- **Pydantic/Contract-Kit:** discriminated union über `kind`. Ein Plugin sagt
  ausdrücklich, welche Identitätsform es liefert, statt dass der Host aus
  Feldkombinationen rät.
- **Fähigkeitsdeklaration:** ein Plugin deklariert, welche `kind`s und
  Typen es bedient. Der Host überspringt Quellen, die eine Gattung nicht
  bedienen, und antwortet für den Rest ehrlich mit `quote_unavailable` —
  statt dass ein YAML-Plugin OpenFIGI-Fragen bekommt oder Yahoo eine
  `isin_only`-Anleihe. **Ort:** T-38, wo Pflichtfelder und `instrument_type`
  ohnehin kanonisiert werden; zusammen ergibt das einen einzigen
  `API_VERSION`-Sprung.
- **Symbolformat:** `{base}-{quote}` ist das Paar-Symbol (`BTC-EUR`). Der
  Bindestrich, den `is_canonical_ticker` bei `listed`-Tickers zu Recht
  verbietet, ist hier das Trennzeichen der *anderen* Form. Die Zerlegung
  läuft über `kind`, nie über die Symbolform allein.

## Krypto: der Weg durch die App

Zwei Arten, „Krypto zu halten" — nur eine braucht die neue Form:

| | Krypto-**ETP** (21Shares & Co.) | **natives** Krypto (die Coin) |
|---|---|---|
| ISIN / MIC | vorhanden | gibt es nicht |
| Identität | `listed` — braucht nur den Typ | `pair` — der Gegenstand dieses Tickets |

Der Kern des Paars: `BTC` allein hat keinen Preis. Einen Preis gibt es nur
relativ zu einer Währung, und `BTC-EUR` ≠ `BTC-USD`. Die Rolle, die bei der
Aktie der Handelsplatz spielt („wo gilt dieser Preis?"), spielt beim Paar die
Quote-Währung. `BTC-EUR` neben `BTC-USD` sind zwei Instrumente — so legitim
wie zwei Listings derselben Aktie.

1. **Erfassen** per Symbol (`BTC-EUR`), nicht per ISIN — die gibt es nicht.
   `isin` ist im Schema bereits nullable, die By-Symbol-Routen existieren.
2. **Auflösen:** Quellen ohne `pair`-Fähigkeit werden übersprungen; yfinance
   kennt `BTC-EUR` nativ und meldet `quoteType: CRYPTOCURRENCY`. Aus dem
   Gattungs-Befund — nicht aus dem Bindestrich — entsteht die Paar-Identität.
3. **Speichern:** normale Instrumenten-Zeile mit `kind='pair'`, `base`,
   `quote_currency`, `type='crypto'`, `isin=NULL`.
4. **Kurse:** ab hier nichts Besonderes — `quotes`-Zeilen, Cache, Refresh wie
   bei jedem Papier. Zusatzregel: Kurswährung muss `quote_currency`
   entsprechen (Matrix `#7`).
5. **Metadaten:** TER, Fondsvolumen, Domizil sind Fonds-Begriffe; für
   `type='crypto'` läuft die Kaskade gar nicht erst los (Matrix `#8`).

Krypto ist damit in **beiden** Profilen zu Hause: online über yfinance, im
YAML-Profil über einen Dateieintrag. Anders als die Anleihe braucht es keinen
Fallback — es ist die Gattung mit der besten Quellenlage.

## Anleihe: erfassbar sofort, bepreist über Quellen

1. **Erfassen** funktioniert mit `isin_only` sofort — Instrument, Name, Typ,
   Metadaten (inkl. Handpflege) sind da. OpenFIGI kennt Anleihen-ISINs und
   kann Metadaten liefern; einen Preis liefern die Online-Quellen nicht.
2. **Ohne liefernde Quelle** zeigt `/quote/{isin}` den strukturierten
   `quote_unavailable`-Zustand — die wahre Aussage „keine Quelle konnte einen
   Preis feststellen". Die provider-neutralen Fehlertexte aus T-36 Finding 2
   tragen genau diesen Fall.
3. **Der Weg zum Preis ist der YAML-Fallback** — als Kettenende des
   Online-Profils (Entscheidung 6) oder im reinen YAML-Profil. Er *ist* die
   Handpflege für Preise, nur in ehrlicher Form: jede Zeile mit Zeitpunkt und
   Herkunft, wiederholbarer Refresh, keine zweite Preis-Wahrheit neben
   `quotes`.

## Der YAML-Fallback als Kettenglied — drei Bedingungen

Damit Entscheidung 6 sauber bleibt:

1. **Eigene Quelle, kein Seitenblick im Adapter.** Die Yahoo-Hülle bleibt
   schlank; das YAML-Plugin steht als eigenes Kettenglied in der
   Profilkonfiguration.
2. **Konfiguriert, nicht entdeckt.** Das Profil nennt den Dateipfad; fehlt
   die Datei, meldet die Quelle das dreiwertige „konnte nicht feststellen"
   (T-20) und die Kette läuft weiter. Kein Verzeichnis-Scannen.
3. **Fallback, nicht Override.** YAML steht **zuletzt**: Ein Papier, das
   online und in der Datei steht, bekommt den Online-Kurs; YAML greift
   nur, wo keine Online-Quelle liefert. Die umgekehrte Semantik wäre ein
   eigenes Feature — nicht im MVP.

Eine Implementierung, zwei Verwendungen — siehe die Notiz in T-37.

## Der Umbauschnitt *(Entwurf, 2026-08-29 — noch nicht umgesetzt)*

Ausgewiesen, nicht vorweggenommen: T-38 bleibt das eigene, unmittelbar
folgende Kettenglied. Was hier steht, ist der Schnitt durch **dieses** Ticket
und die Stelle, an der er den Vertrag mit T-38 und T-37 teilt — damit der
`API_VERSION`-Sprung einer bleibt und nicht dreimal passiert.

### Der Fund, der in keinem der drei Tickets steht

Dieses Ticket beschreibt die Union an `Resolved`. Der Vertrag hat aber fünf
Rollen, und die beiden Kursrollen tragen die Identität ebenfalls — heute als
Pflichtfelder:

```python
class QuoteRequest:  ticker: str; mic: str; isin: str | None = None
class DailyRequest:  ticker: str; mic: str; start: ...; end: ...
```

Ein `BTC-EUR` ließe sich damit **auflösen, aber nicht bepreisen**. Eine Coin
hat keinen MIC — der Grund, aus dem dieses Ticket existiert —, und für die
`isin_only`-Anleihe gilt dasselbe. Wer die Union nur an `Resolved` einbaut,
nimmt die Gattung auf und schneidet ihr den Weg zum Kurs ab. Der
YAML-Fallback aus T-37 wäre die erste Quelle, die daran scheitert, und die
Anleihe ist der Fall, für den er gebaut wird.

Es ist keine Ausweitung, sondern der Umfang, den Matrix `#7` bereits
voraussetzt: Die Prüfung „Kurswährung muss `quote_currency` entsprechen" kann
es nur geben, wenn die Kursanfrage weiß, dass sie ein Paar betrifft.

**`Identity` ersetzt darum `ticker`/`mic` in `Resolved`, `QuoteRequest` und
`DailyRequest`.** `FxRequest` und die Metadatentypen bleiben unberührt.

### Stufe 1 · Der Vertrag — hier und nur hier springt `API_VERSION`

```python
API_VERSION = 2

@dataclass(frozen=True)
class ListedIdentity:    kind: Literal["listed"];    ticker: str; mic: str; isin: str | None = None
@dataclass(frozen=True)
class PairIdentity:      kind: Literal["pair"];      base: str;   quote_currency: str
@dataclass(frozen=True)
class IsinOnlyIdentity:  kind: Literal["isin_only"]; isin: str

Identity = ListedIdentity | PairIdentity | IsinOnlyIdentity
```

Die drei Dataclasses tragen sie als **ausdrückliches Feld**, nicht als
aufgelöste Einzelfelder:

```python
class Resolved:      identity: Identity; name: ...; instrument_type: ...
class QuoteRequest:  identity: Identity
class DailyRequest:  identity: Identity; start: ...; end: ...
```

`QuoteRequest.isin` entfällt damit: Die ISIN steckt in `ListedIdentity` und
`IsinOnlyIdentity`, und ein zweites Feld daneben wäre eine zweite Wahrheit
über dieselbe Sache.

**Keine `ticker`/`mic`-Properties als Bequemlichkeit.** Sie müssten für ein
Paar etwas erfinden, und das ist genau der Sentinel-Wert, den T-21 ausgetrieben
hat. Aufrufer verzweigen über `kind`.

#### Der Versionscheck greift heute nicht — und das ist derselbe Mechanismus

*(Befund Codex, Runde 1. Er korrigiert eine Begründung, die ich selbst
gegeben habe, und der Widerspruch ist lehrreich genug für einen Absatz.)*

`app/plugin_loader.py` vergleicht hart (`if version != API_VERSION`), und das
sah nach einer wirksamen Schranke aus. Sie ist keine. Drei Dinge greifen
ineinander:

1. `Source.api_version: int = API_VERSION` ist ein **Klassenattribut mit
   Vorgabewert**. Wer nicht deklariert, erbt den jeweils aktuellen Wert.
2. `_check()` liest ihn mit `getattr()` — der geerbte Wert ist von einem
   selbst gesetzten nicht zu unterscheiden.
3. `app/plugin_env.py` schreibt beim Installieren eine Schranke
   `stockinfo-plugin-api==<Version der App>` (`_contract_constraint`). Ein
   beigesteuertes Plugin bekommt damit **zwangsweise** das Contract-Paket der
   App, nicht das, gegen das es gebaut wurde.

Ein unverändertes Altplugin ohne eigene Deklaration erbt nach dem Upgrade
also `2` und passiert den Check. Die Schranke prüft nichts.

**Genau das war mein Argument für den Sprung — und es war falsch herum.** Ich
habe „die eingebauten Plugins erben den neuen Wert, kostet also nichts" als
Vorteil verkauft. Dieselbe Vererbung ist der Grund, warum die Prüfung
danebengreift. Billig und wirkungslos waren hier eine Sache.

**Die Korrektur:** Eine konkrete `Source` muss `api_version` **selbst**
deklarieren. Der Loader weist eine fehlende oder falsche **eigene**
Deklaration ab: Die **konkrete**, als Entry-Point oder Datei geladene
`source_class` muss `api_version` in ihrem **eigenen** `__dict__` tragen.
Geerbt genügt nicht — auch nicht von einer Zwischenklasse. *(Präzisierung
Codex, Runde 2: Mein erster Text verlangte „selbst deklarieren", beschrieb
den Check dann aber als Lauf entlang der MRO. Das hätte die Deklaration
einer gemeinsamen Basisklasse durchgehen lassen und damit dieselbe Vererbung
wieder eingeführt, die der Check ausschließen soll. Ein Blick, keine Suche.)*
Der Test prüft genau das. Die eingebauten
Plugins, die Beispiele, die Test-Doubles und das Contract-Kit ziehen mit und
deklarieren ausdrücklich.

Damit kostet der Sprung nicht mehr eine Zeile, sondern eine je Quelle. Er ist
dafür das, was er zu sein vorgab.

#### Die Fähigkeitsdeklaration — grober Vorfilter, mehr nicht

```python
SUPPORTED_KINDS: frozenset[str] = frozenset({"listed"})
SUPPORTED_TYPES: frozenset[str] = frozenset()   # leer = nichts zugesagt
```

Die Vorgabe `{"listed"}` bleibt: Ein Plugin, das gegen Vertrag 1 gebaut
wurde, konnte nur Listings, und die Vorgabe sagt damit die Wahrheit über
einen Autor, der nichts erklärt.

**Kein neues Subsystem.** Die beiden Mengen sind ein *grober Vorfilter*; die
eigentliche Entscheidung bleibt das vorhandene `handles(request)` **je
Rolle**. Zwei Ebenen, jede dort, wo das Wissen sitzt; die untere ist bereits
gebaut und wird nicht ersetzt.

**Die Aufrufstelle ist je Rolle verschieden, und beim Resolver gibt es sie
gar nicht.** *(Präzisierung Codex, Runde 2 — mein erster Text beschrieb den
Vorfilter, als kenne der Host die Gattung schon vor der Frage.)* Er kennt sie
nicht: `ResolveRequest` trägt ISIN, Symbol, Vorzugsbörse und Währung — weder
`kind` noch `instrument_type`. Beides ist das **Ergebnis** der Auflösung.

| Rolle | wann der Host filtert |
|---|---|
| `resolvers` | **gar nicht vorher.** Es bleibt bei `handles(request)`. Die **Antwort** wird gegen die deklarierten Fähigkeiten geprüft: Liefert eine Quelle eine `kind` oder Gattung, die sie nicht deklariert hat, ist das ein Befund und kein stiller Treffer |
| `quotes`, `daily`, `etf_meta` | **nach** der Auflösung. Dort sind Identität und Gattung bekannt und stehen in der gespeicherten Zeile; der Vorfilter überspringt eine Quelle, bevor sie eine Anfrage kostet |

**Nie aus der Symbolform geraten.** Der Bindestrich in `BTC-EUR` ist kein
Beleg für ein Paar, und eine ISIN mit `DE` ist kein Beleg für eine Anleihe.
Die Gattung stammt aus dem Befund der Quelle — das ist Matrix `#5`, und die
Vorfilter-Regel darf sie nicht hintenherum aushebeln.

**`SUPPORTED_TYPES` bekommt keinen `None`-Wert mehr.** `None` hätte „alle
heutigen und künftigen Typen" bedeutet — eine Zusage, die ein Autor nie
gegeben hat und die bei jedem neuen Katalogeintrag stillschweigend wächst.
Das ist dieselbe stille Annahme, gegen die T-38 geschrieben wurde. Eine leere
Menge sagt stattdessen „nichts zugesagt", und die eingebauten Quellen
deklarieren ihre Typen ausdrücklich.

### Stufe 2 · Datenbank

**Die `CHECK`-Klausel muss die Belegung ausschließen, nicht nur verlangen.**
*(Befund Codex, Runde 1.)* Mein erster Entwurf prüfte je Form nur, was da
sein **muss**. Eine `listed`-Zeile hätte dann zusätzlich `base` und
`quote_currency` tragen dürfen, eine `pair`-Zeile obendrein einen `ticker` —
und genau eine solche halbe Doppelidentität ist der Zustand, den dieses
Ticket unmöglich machen soll. Jede Form nennt darum auch, was sie **nicht**
haben darf:

```sql
kind           TEXT NOT NULL DEFAULT 'listed',
base           TEXT,
quote_currency TEXT,
ticker         TEXT,          -- wieder nullable
mic            TEXT,          -- wieder nullable
CHECK (
  (kind = 'listed'    AND ticker IS NOT NULL AND mic IS NOT NULL
                      AND base IS NULL AND quote_currency IS NULL) OR
  (kind = 'pair'      AND base IS NOT NULL AND quote_currency IS NOT NULL
                      AND ticker IS NULL AND mic IS NULL AND isin IS NULL) OR
  (kind = 'isin_only' AND isin IS NOT NULL
                      AND ticker IS NULL AND mic IS NULL
                      AND base IS NULL AND quote_currency IS NULL)
)
```

**Die Eindeutigkeit — drei partielle Indizes reichen nicht.** Sie liegt heute
auf `UNIQUE(ticker, mic)`, das für zwei der drei Formen leerliefe. Je Form
kommt darum ein partieller Index (`WHERE kind = …`). Das ersetzt aber zwei
bestehende Zusagen **nicht**, und beide bleiben ausdrücklich erhalten:

- **`isin` bleibt global eindeutig**, über alle `kind` hinweg. Heute steht das
  als Spalten-`UNIQUE` plus `idx_instruments_isin` im Schema. Ein partieller
  Index nur für `isin_only` ließe dieselbe ISIN einmal als `listed` und einmal
  als `isin_only` zu — zwei Zeilen für dasselbe Papier, in zwei
  Identitätsformen. Beim Tabellen-Neuaufbau muss die globale Zusage
  mitgeschrieben werden; sie fällt sonst still weg.
- **`listing_id` bleibt global eindeutig** (`idx_instruments_listing_id`). Sie
  ist die opake Kennung eines Listings und von `kind` unabhängig.

### Stufe 3 · Die App-Grenze

| Ort | Änderung |
|---|---|
| `app/providers/base.py` | `ResolvedInstrument` bekommt `kind`, `base`, `quote_currency`; `QUOTE_TYPE_MAP` += `CRYPTOCURRENCY → crypto`, `BOND → bond` (Matrix `#4`) |
| `app/exchanges.py` | `canonical_identity` wird Weiche über die Union; `is_real_mic` und `is_canonical_ticker` bleiben unverändert die `listed`-Hälfte (Matrix `#3`) |
| `app/exchanges.py` | `REASON_UNSUPPORTED_INSTRUMENT_TYPE` samt Eintrag in `REJECTION_REASONS` (Matrix `#6`) |
| `dashboard/src/i18n/{de,en}.ts` | derselbe Schlüssel in beiden Sprachen |
| `app/plugin_adapters.py` | `ResolverAdapter` übersetzt über `kind` (Matrix `#5`) |
| `app/services/quote_service.py` | für `kind='pair'`: Kurswährung ≠ `quote_currency` ⇒ Ablehnung, keine stille Umrechnung (Matrix `#7`) |
| Metadatenkaskade | läuft nur für `etf`/`etc` — kein justETF für eine Coin, keine TER-Frage an eine Anleihe (Matrix `#8`) |

`app/resolver.py` und die eingebauten Plugins ziehen mit.

#### Die Union endet nicht am Repository — sie muss bis nach draußen

*(Befund Codex, Runde 1.)* Mein erster Entwurf hörte bei Vertrag, Datenbank
und Adapter auf. Das hätte ein System ergeben, das eine Anleihe **speichern**
und nicht **ausliefern** kann. Gemessen an `app/models.py`:

```python
class QuoteResponse:      ticker: str;  mic: str          # Pflicht, nicht nullable
class InstrumentSummary:  ticker: str;  mic: str;  listing_id: str
```

Beide sind seit `core_version 2.0.0` ausdrücklich als Pflicht **zugesagt**,
und `QuoteService._build` lässt eine Antwort ohne Identität schon vorher
scheitern. Ein `BTC-EUR` und eine `isin_only`-Anleihe fielen dort also um —
und der einzige Weg, sie doch durchzubekommen, wäre ein erfundener Ticker
oder MIC. Das ist der Sentinel-Wert, den T-21 ausgetrieben hat, nur am
anderen Ende der App.

Die Union muss darum durch die ganze Kette getragen werden:

| Schicht | was zu tun ist |
|---|---|
| `app/repository.py`, Quote-Cache | lesen und schreiben über `kind`; die Identitätsspalten je Form, keine Sammelabfrage auf `(ticker, mic)` |
| `app/models.py` | `QuoteResponse` und `InstrumentSummary` tragen **genau ein** Feld `identity` mit der diskriminierten Union — siehe unten |
| REST/OpenAPI | `contract/openapi-core-snapshot.json` und die Fixtures ziehen nach; die Änderung ist am veröffentlichten Schema sichtbar, nicht nur im Artefakt |
| `dashboard/src/types.ts` und Darstellung | dieselbe Union; eine Coin zeigt Paar statt Börse, eine `isin_only`-Anleihe ihre ISIN. Kein leeres Feld, das wie ein Fehler aussieht |

**Ein Feld, nicht drei danebengelegte.** *(Präzisierung Codex, Runde 2.)*
Mein erster Text ließ `ticker`/`mic` als Top-Level-Felder stehen, „wo sie
wahr sind", und für die anderen Formen ungesetzt. Das ist dieselbe zweite
Wahrheit, die ich bei `QuoteRequest.isin` gerade entferne — nur an der
öffentlichen Grenze, wo sie mehr kostet: Ein Konsument müsste raten, ob ein
leeres `mic` „gibt es nicht" oder „wurde nicht ermittelt" heißt, und genau
diese Unterscheidung ist der Grund für die Union.

`QuoteResponse` und `InstrumentSummary` tragen darum **ein** Feld `identity`
und **keine** parallelen optionalen `ticker`/`mic`/`isin` daneben. Die
Datenbank behält ihre flachen Spalten — dort sind sie durch den `CHECK`
gebunden und nicht mehrdeutig; die öffentliche Form behält sie nicht.

`listing_id` bleibt Top-Level auf `InstrumentSummary`: Sie ist nicht Teil
der Identität, sondern der opake Schlüssel der gespeicherten Zeile.

**Der Preis, ehrlich benannt:** `isin` wandert damit aus der Wurzel von
`QuoteResponse` in `identity`. Das bricht jeden Konsumenten, der heute
`response.isin` liest — das Dashboard eingeschlossen. Es ist der Grund, aus
dem `core_version` ohnehin auf Major geht, und es ist besser jetzt als nach
dem ersten fremden Konsumenten.

**Die Nahtstelle zu T-38 ist hier und sie ist scharf:** Dass `QuoteResponse`
die Identität *als Union* führt, ist T-31. Dass `name` und `type` darin
**Pflicht** werden und `GET /fields` das ausweist, ist T-38. Die
`core_version` steigt einmal, in T-38 — hier wird sie vorbereitet, nicht
gesetzt.

### Was dieses Ticket **nicht** tut

Die Pflichtfelder (`Resolved.name`, `Resolved.instrument_type`), die
Auskunft in `GET /fields` und der `core_version`-Major sind **T-38** und
bleiben dort. Sie landen im selben `API_VERSION`, weil zwischen beiden
Kettengliedern kein Release liegt — nicht, weil die Tickets verschmelzen.

Der YAML-Fallback ist **T-37**. Er steht hinter beiden, weil das abgestimmte
Beispiel `_tickets/T-37-single-file-sample.yaml` `kind:` und die Gattungen
`crypto`/`bond` bereits ausspricht — er ist der erste Konsument dieses
Vertrags, nicht seine Vorbedingung.

### Entscheidungen Mike, 2026-08-29

1. **Die bestehende `data/stockinfo.db` wird verworfen.** Kein Umzugspfad für
   die Union; das Projekt ist in Entwicklung, die sechs Zeilen sind
   Wegwerfdaten. Das neue Schema wird direkt angelegt. Die `CHECK`-Klauseln
   entfallen dadurch nicht — nur der Umzugsschritt.
2. **Der Smoke-Profilname wird `yaml`** statt `csv` (Umsetzung in T-37).
3. **Beide Versionssprünge werden gemacht**, `API_VERSION` 1→2 und
   `core_version` 2.1.0→3.0.0. Abgewogen gegen Mikes Einwand „wir sind in der
   Entwicklungsphase, und `plugin_api` steht ohnehin auf `0.2.0`" — ein
   berechtigter Einwand, denn `0.x` sagt die Unreife bereits. Der Unterschied:
   `0.2.0` sagt *„rechne mit Brüchen"*, `API_VERSION` sagt *„dieses Plugin
   kann hier nicht laufen"*. Das ist kein Reifegrad, sondern ein
   Dialekt-Token, und nur das zweite lässt sich prüfen.

   **Die Begründung, die ich dabei gegeben habe, war falsch.** Ich habe
   argumentiert, der Sprung koste eine Zeile, weil die eingebauten Plugins
   `api_version` erben. Codex hat in Runde 1 gezeigt, dass genau diese
   Vererbung die Prüfung wirkungslos macht (siehe *Der Versionscheck greift
   heute nicht*). Der Sprung kostet mit der Korrektur **eine Deklaration je
   Quelle** statt einer Zeile insgesamt. Die Entscheidung bleibt trotzdem
   stehen: Nicht weil er billig ist, sondern weil er ohne die Korrektur eine
   Zusage ohne Deckung wäre — und eine Zahl, die etwas anderes vorgibt zu
   sein, ist genau das, was dieses Ticket austreibt.

### Naming-Mitzieher — gemessen, nicht geraten

AST-Inventar über die Dateien, die dieses Ticket ohnehin anfasst. Vier
deutsche Bezeichner, jeder an der Fundstelle bestätigt:

| Datei | heute | wird |
|---|---|---|
| `app/contract.py:68` | `feld` | `field` |
| `app/routers/fields.py:35-46` | `vertrag` | `contract` |
| `app/plugin_adapters.py:352` | `herkunft` | `provenance` |
| `app/sources_config.py:209` | `taugliche` | `usable` |

Die TypeScript- und Bash-Seite wird bei der Umsetzung neu inventarisiert —
welche Dateien dort fallen, steht erst dann fest.

## Worum es geht *(Fundlage, 2026-08-25)*

T-21 Teil 3 verlangt seit Entscheidung 2 eine **vollständige kanonische
Identität**: kanonischer Ticker **und** echter MIC nach ISO 10383. Seit
Übergabe 2A steht das im Schema (`ticker`/`mic` als `NOT NULL`), und
`canonical_identity` lehnt alles andere ab.

Damit lässt sich **`BTC-USD` nicht mehr speichern**. Eine Kryptowährung wird
an keinem Handelsplatz im Sinne von ISO 10383 gehandelt; es gibt schlicht
keinen MIC, der wahr wäre. Dasselbe gilt für Indizes und einen Teil der
Anleihen.

**Das ist keine Nachlässigkeit im Entwurf, sondern eine Folge, die niemand
ausgesprochen hat.** Die gemessene Auswirkungstabelle in der Spec führt nur
Aktien und ETFs auf; die Gattungen ohne Handelsplatz kamen darin nicht vor.

Im realen Bestand gab es am 2026-08-25 **keine** solche Zeile — sechs
Instrumente, fünf mit Börsensuffix, dazu `VTI`. `QUOTE_TYPE_MAP` kannte nur
`ETF`, `MUTUALFUND` und `EQUITY`.

## Die Auswege, wie sie beim Fund aussahen

1. **Streng bleiben.** Was keinen echten MIC hat, gehört nicht in den
   Bestand.
2. **Ein Katalogeintrag für „kein Handelsplatz".** Ein MIC-Wert, der keine
   Börse bezeichnet — dieselbe Sorte magischer Wert, die T-21 gerade
   austreibt.
3. **Eine eigene Identitätsform für Gattungen ohne Handelsplatz.**

**Gewählt: Nr. 3** — mit dem Zuschnitt und den Grenzen unter
**Die Entscheidung**.
