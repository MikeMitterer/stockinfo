# Der REST-Core von StockInfo — was zugesagt ist

**Vertragsversion 4.4.0** · Stand 2026-09-26

`GET /fields` liefert den Feldvertrag und das aktuelle Detailschema.
`GET /instrument-types` liefert die Typen der konfigurierten Plugins.
Instrumente werden über `identity` beschrieben und über `listing_id`
dauerhaft referenziert. Das allgemeine Generation-Protokoll ist noch nicht
verfügbar; der Stand und bekannte Vertragsabweichungen stehen unten.

Die maschinenlesbaren Zusagen stehen in
[`contract/core-contract.json`](../contract/core-contract.json).
Die Fixtures werden gegen dieses Artefakt geprüft. Ein dort beschriebener,
unter `planned` geführter Ablauf ist noch keine verfügbare Laufzeitfunktion.

## Übersicht

- [Warum es das gibt](#warum-es-das-gibt)
- [Börsenentscheidung bei der Aufnahme](#börsenentscheidung-bei-der-aufnahme)
- [Was der Core umfasst](#was-der-core-umfasst)
- [Die Begriffe, die sich sonst niemand erschließt](#die-begriffe-die-sich-sonst-niemand-erschließt)
- [Identität: `listing_id` für Maschinen, `symbol` für Menschen](#identität-listing_id-für-maschinen-symbol-für-menschen)
- [Die Generation: woran ein Konsument einen Datensatzwechsel erkennt](#die-generation-woran-ein-konsument-einen-datensatzwechsel-erkennt)
- [Was additiv ist und was ein Bruch wäre](#was-additiv-ist-und-was-ein-bruch-wäre)
- [Entschieden, aber noch nicht zugesagt](#entschieden-aber-noch-nicht-zugesagt)
- [Der Vertrag ist abfragbar, nicht nur dokumentiert](#der-vertrag-ist-abfragbar-nicht-nur-dokumentiert)
- [Asset-Typen aus der Plugin-Konfiguration](#asset-typen-aus-der-plugin-konfiguration)
- [Wie man den Vertrag prüft](#wie-man-den-vertrag-prüft)

## Warum es das gibt

StockInfo und sein Konsument StockPortfolio haben getrennte Releases.
Der Vertrag beschreibt die gemeinsamen Datenformen und macht Änderungen
zwischen diesen Anwendungen prüfbar.

[↑ Übersicht](#übersicht)

## Börsenentscheidung bei der Aufnahme

`POST /instruments/intake` nimmt eine `identifier` entgegen. Mit
`check_exchange: true` prüft der Core ein neues Listing vor dem Speichern
gegen die konfigurierte bevorzugte Börse. Weicht der MIC ab, liefert er
`202` mit `status: confirmation_required`, `identity`, `name`, `exchange`,
`currency` und `preferred` (`mic`, `name`, `currency`). Die tatsächliche
Währung stammt aus dem Kurs; die bevorzugte Währung aus dem Börsenkatalog.
Zu diesem Zeitpunkt ist das Instrument noch nicht gespeichert.

Das Dashboard erklärt den Vergleich nach Submit als Fließtext und hebt die
ursprüngliche Eingabe, beide Börsennamen und die Kurswährung fett hervor.
Die Alternative steht nach einer Leerzeile. Du entscheidest mit „Übernehmen“
oder „Abbrechen“. Abbruch benötigt keinen weiteren Request. Bestätigung sendet
dieselbe Eingabe mit `check_exchange: true` und der angezeigten `identity`
als `confirmed_listing`. Eine geänderte Auflösung erfordert eine neue
Bestätigung, solange ihre Börse weiterhin von der bevorzugten abweicht. Erfolgreiche Aufnahme liefert `201`, ein vorhandenes Listing
`200`, jeweils mit `InstrumentSummary`.

Gleiche Börse, Paare, reine ISIN-Instrumente und vorhandene Listings benötigen
keine Rückfrage. Eine unbekannte Präferenz erzeugt keinen geratenen Vergleich.
Ohne `check_exchange` wird direkt aufgenommen. Nach einer bestätigten Aufnahme
gibt es keine dauerhafte Warnung und keine Rückfrage beim Lesen oder Refresh.
Die Anfragefelder und die 202-Antwort gehören zu Core-Version `4.3.0`.

[↑ Übersicht](#übersicht)

## Was der Core umfasst

Fünf öffentliche Modelle, jedes mit eigener Pflichtfeldmenge:

| Modell | Endpunkte |
|---|---|
| `quote` | `/quote`, `/quote/{isin}` |
| `instrument` | `/instruments`, `POST /instruments/intake` |
| `daily` | `/quote/{isin}/daily`, `/quote/by-symbol/{symbol}/daily` |
| `history` | `/quote/{isin}/history`, `/quote/by-symbol/{symbol}/history` |
| `fx` | `/fx` |

`GET /fields` und `GET /instrument-types` sind ebenfalls im Artefakt und im
OpenAPI-Schnappschuss erfasst. Diagnoseendpunkte (`/env`, `/analyze`, `/ready`),
`/exchanges` und die übrigen Schreibwege des Dashboards gehören nicht zu
diesem versionierten Core.

`POST /instruments/intake` ist der Aufnahmeweg des Dashboards. Der Core
klassifiziert und löst die Eingabe auf; ein Konsument braucht dafür keine
eigene Erkennungslogik. Auch eine Kursabfrage kann ein Instrument speichern.

[↑ Übersicht](#übersicht)

## Die Begriffe, die sich sonst niemand erschließt

**`quote_time` gegen `fetched_at`.** Das erste ist der Zeitpunkt, zu dem der
Kurs an der Börse galt; das zweite, wann StockInfo ihn geholt hat. Ein am
Montagmorgen frisch beschaffter Kurs vom Freitagabend hat ein junges
`fetched_at` und ein altes `quote_time`. Wer Aktualität anzeigen will, braucht
beide.

**`cached` gegen `stale`.** `cached` heißt nur: Diese Antwort kam ohne
Anbieteraufruf zustande. Über die Güte sagt das nichts — ein Kurs von vor zehn
Minuten ist gut. `stale` heißt: Die frische Beschaffung ist **fehlgeschlagen**,
und der zuletzt bekannte Wert wird trotzdem ausgeliefert, älter als die TTL.
`stale=true` zieht `cached=true` nach sich, umgekehrt gilt es nicht.

**Bekannte Abweichung bei Tageskursen:** Das Vertragsartefakt beschreibt
`daily.close` als unbereinigt. Die Yahoo-Anbindung ruft jedoch
`history(..., auto_adjust=True)` auf und liefert um Dividenden und Splits
bereinigte Kurse. Der Daily-Adapter reicht diese Werte weiter; die REST-Antwort
enthält kein `adjusted`-Feld. Konsumenten dürfen daher derzeit keine
durchgehend unbereinigte Reihe voraussetzen.

**Währung ist Pflicht, nicht Zierde.** Ein Preis ohne Währung ist für eine
Depotrechnung wertlos, und die naheliegende Vermutung — „wird schon Euro sein" —
ist bei einem Londoner Listing in Pence falsch. Liefert eine Quelle einen Preis
ohne Währung, kann diese Antwort nicht als Kurs verwendet werden. Liefert
auch keine weitere Quelle einen gültigen Kurs und gibt es keinen nutzbaren
Cachewert, antwortet die API mit `502`.

**Bekannte Abweichung bei Pence-Kursen:** Das REST-Artefakt erlaubt `GBp`
(Pence), der Plugin-Vertrag verlangt dagegen ISO-Währungscodes und lehnt
Untereinheiten ab. Die Yahoo-Kursquelle reicht einen solchen Wert nicht als
gültigen Treffer weiter und rechnet ihn derzeit auch nicht in `GBP` um.
Ein in Pence notiertes Instrument kann deshalb auf eine andere Quelle oder
den Cache zurückfallen; ohne beides schlägt der Abruf fehl.

[↑ Übersicht](#übersicht)

## Identität: `listing_id` für Maschinen, `symbol` für Menschen

`identity` ist ein Pflichtobjekt in Quote- und Instrumentantworten.
`identity.kind` bestimmt seine Felder:

| `kind` | Felder | Beispiel |
|---|---|---|
| `listed` | `ticker`, `mic`, optional `isin` | Aktie oder ETF an einem Handelsplatz |
| `pair` | `base`, `quote_currency` | natives Kryptopaar wie BTC/EUR |
| `isin_only` | `isin` | außerbörsliche Anleihe |

`mic` ist die eindeutige Handelsplatzkennung nach ISO 10383.
Ticker, MIC und ISIN stehen innerhalb von `identity`, nicht daneben.
`symbol` bleibt ein Pflichtfeld für die Anzeige, ist aber **nicht garantiert
eindeutig**. Mehrere Listings können denselben Namen tragen.

- **`listing_id`** — eine opake UUID, bei Anlage einmal erzeugt und **nicht**
  aus `ticker`, `mic`, ISIN oder dem lokalen Schlüssel abgeleitet. Jede Zeile
  bekommt eine, unabhängig von ihrer Identitätsform. Sie überlebt manuelle Zuordnung,
  Metadatenänderungen, Sicherung und Wiederherstellung. Konsumenten zerlegen
  sie nie.
- **`409 Conflict`** bei mehrdeutigem Symbol, mit Kandidatenliste im Rumpf —
  statt still das Falsche zu treffen.

**Ein aktives Listing je ISIN.** `isin TEXT UNIQUE` ist eine Grenze, kein
Zufall: Ein Profil wählt genau ein Listing. Mehrere gleichzeitige Listings
derselben ISIN wären eine eigene Schema- und Konsumenten-Erweiterung.

### Zwei Fälle unter einem `409` — unterschieden wird über `code`

Beide Antworten enthalten `code` und `params`. Die Antwort auf ein
mehrdeutiges Symbol ergänzt `detail` und `candidates`:

| `code` | Bedeutung | Gilt an |
|---|---|---|
| `symbol_ambiguous` | Mehrere Listings tragen diesen Anzeigenamen. Rumpf: `detail`, `code`, `params`, `candidates` — jeder Kandidat mit `listing_id`, `symbol`, `mic`, `exchange`, `isin`. | jedem Endpunkt, der ein `symbol` entgegennimmt — lesend wie verändernd |
| `identity_conflict` | Zwei gewachsene Zeilen beanspruchen dieselbe kanonische Identität — `AAPL/XNAS` ohne ISIN neben `AAPL/XNYS` mit ihr, und dieselbe ISIN wandert nach XNAS. Rumpf: `code`, `params` mit `ticker`, `mic`, `isin` (sofern bekannt). | jedem Endpunkt, der speichert |

**Keiner der beiden ist ein Eingabefehler**, und deshalb ist keiner ein `400`:
Beim mehrdeutigen Symbol reicht der Anzeigename nicht zur Auswahl eines
Listings; beim Identitätskonflikt beanspruchen zwei gespeicherte Zeilen
dieselbe Identität.

`symbol_ambiguous` trägt die Kandidaten mit, weil ein `409` ohne sie eine
Sackgasse wäre — mit ihnen hat der Aufrufer je Kandidat eine `listing_id`, und
die ist eindeutig. **Verändert wird dabei nichts.**

`identity_conflict` sagt, was der Fall ist — er löst ihn nicht. Die
Zusammenführung zweier Zeilen ist eine eigene Datenoperation und findet
nicht nebenbei in einer Kursabfrage statt.

[↑ Übersicht](#übersicht)

## Die Generation: woran ein Konsument einen Datensatzwechsel erkennt

**Verfügbar:** `GET /fields` liefert `generation_id` aus der Datenbank.
Die UUID bleibt über Neustarts erhalten und wird mit der Datenbank gesichert.
`GET /instrument-types` sendet dieselbe UUID im Header `StockInfo-Generation`
und setzt `Cache-Control: no-store`. Sie ist keine Typkatalogversion und
ändert sich nicht automatisch bei jedem Wechsel der Quellenkonfiguration.

**Noch nicht verfügbar:** `GET /generation`, ein Generation-Header auf jeder
Antwort und dessen CORS-Freigabe für Browser anderer Origins. Das Artefakt
beschreibt diese Teile unter `planned.generation_runtime`. Seine allgemeinen
Generation-Fixtures zeigen den vorgesehenen Vertrag, keine heutigen
Antworten der laufenden App.

Der geplante Ablauf verwendet folgende Route:

```http
GET /generation
Cache-Control: no-store

{ "generation_id": "550e8400-e29b-41d4-a716-446655440000" }
```

und auf jeder Antwort — auch auf `404`, `409`, `422`, `502` — diesen Header:

```http
StockInfo-Generation: 550e8400-e29b-41d4-a716-446655440000
```

Die Fehlerfälle sind kein Detail: Nach einem Profilwechsel kann ein bisher
bekanntes Papier fehlen. Ohne Header auf der `404` zeigt der Konsument seinen
alten Cache weiter.

**Im geplanten Ablauf bestätigt `/generation` den aktuellen Stand.** Zwei Anfragen
können sich über einen Profilwechsel hinweg überschneiden, und eine verspätete
Antwort aus A trifft nach einer schnellen aus B ein. UUIDs tragen keine
Reihenfolge — wer dem Header blind folgt, springt von B zurück auf A. Weicht
der Header ab, wird die Antwort deshalb verworfen, `/generation` bestätigt den
Stand, und erst danach wird umgeschaltet.

**Die CORS-Freigabe des Headers fehlt derzeit.** Ohne `Access-Control-Expose-Headers` kann
Browser-JavaScript den Antwort-Header nicht lesen. StockPortfolio läuft
cross-origin; der Header wäre dort unsichtbar — gesetzt, aber wirkungslos.

[↑ Übersicht](#übersicht)

## Was additiv ist und was ein Bruch wäre

| additiv (Minor) | Bruch (Major) |
|---|---|
| ein neues optionales Feld | ein Pflichtfeld entfernen oder umbenennen |
| ein neuer Eintrag in `details` | die Art eines Feldes ändern |
| ein neuer Endpunkt | ein optionales Feld zum Pflichtfeld machen |
| ein neuer Wert in `source` | die Bedeutung eines Feldes ändern |
| | einen Statuscode für einen bestehenden Fall austauschen |

**Regel für den Konsumenten:** Unbekannte Felder werden ignoriert, nicht als
Fehler behandelt. Nur so bleibt eine additive Erweiterung wirklich additiv.

[↑ Übersicht](#übersicht)

## Entschieden, aber noch nicht zugesagt

Unter `planned` ist das allgemeine Generation-Protokoll aufgeführt. Die oben
genannten Laufzeitteile stehen noch aus; die dort ebenfalls genannte
persistierte UUID ist für das Detailschema bereits vorhanden.
Der `details`-Container ist implementiert:
Quote- und Instrumentantworten liefern Werte, Einheiten, Währungen und
Herkunft; `/fields` liefert die zugehörigen Felddefinitionen. Manuelle Werte
werden mit `PATCH /instruments/by-id/{listing_id}/details` gepflegt.
Die [Detailfeld-Anleitung](plugin-authors.md#open-detail-fields) beschreibt
Quellenvorrang, Validierung und das Entfernen manueller Werte.

[↑ Übersicht](#übersicht)

## Der Vertrag ist abfragbar, nicht nur dokumentiert

Ein Dokument, das niemand zur Laufzeit lesen kann, hilft einem Konsumenten
nicht — er müsste raten, ob seine gecachte Feldliste noch stimmt. `GET /fields`
liefert deshalb dieselbe Auskunft im Betrieb.

`meaning` enthält in `core` und `plugin_contract` eine englische
Feldbeschreibung. Diese Sprache ist fest: `Accept-Language` und die
Dashboard-Sprache ändern sie nicht. Die Texte erläutern den Vertrag;
Programme verwenden die Feldnamen, Typen und Pflichtangaben.

Gekürzter Auszug; `core` und `endpoints` enthalten hier jeweils nur einen Eintrag:

```json
{
  "core_version": "4.4.0",
  "core": { "quote": [ {"name": "price", "kind": "number", "required": true, "meaning": "Latest known price in the trading currency. Never guessed or converted."} ] },
  "endpoints": { "quote": [ {"path": "/quote/{isin}", "method": "GET", "query": []} ] },
  "generation_id": "550e8400-e29b-41d4-a716-446655440000",
  "details_version": 0,
  "details": []
}
```

Der Core kommt aus **derselben Datei**, gegen die die Fixtures geprüft werden.
Der Plugin-Vertrag wird aus den Plugin-Typen abgeleitet. Detailschema,
`details_version` und `generation_id` stammen aus der Datenbank; das beim
Start aus den konfigurierten Plugins ermittelte Detailschema wird dort gespeichert.

Zwei Nummern, zwei Ebenen: `core_version` folgt SemVer über den geschlossenen
Core, `details_version` zählt Änderungen am Detailschema. Zwischenspeichern
sollte ein Konsument unter `(generation_id, core_version, details_version)`.
Zum Erkennen einer Änderung muss er `/fields` erneut abrufen.

[↑ Übersicht](#übersicht)

## Asset-Typen aus der Plugin-Konfiguration

`GET /instrument-types` liefert die Typkennungen für dynamische Filter.
Grundlage sind `SUPPORTED_TYPES` der geladenen Plugin-Klassen in den laufenden
Ketten `resolvers`, `etf_meta`, `quotes` und `daily`. Nur die jeweilige
Rollenklasse zählt; eine reine FX-Kette liefert keine Asset-Typen.
Der Instrumentenbestand spielt keine Rolle. Es gibt keine feste Ersatzliste.

```json
{
  "instrument_types": ["future-type", "stock"],
  "complete": true,
  "sources": [
    {"name": "catalog-quote", "role": "quotes", "instrument_types": ["future-type", "stock"], "status": "available"}
  ]
}
```

Die Gesamtmenge und die Typen je Quelle sind sortiert und duplikatfrei.
`sources` enthält einen Eintrag je konfigurierter Position, in der oben
genannten Rollenfolge und innerhalb der Rolle in Kettenreihenfolge.
Neue Kennungen sind normale Strings und brauchen keine neue Client-Version.

| Status je Quelle/Rolle | Bedeutung | Beitrag zur Typmenge |
|---|---|---|
| `available` | Deklaration lesbar, lokale Betriebsdiagnose positiv | Deklarierte Typen |
| `unavailable` | Deklaration lesbar, aber Quelle derzeit nicht einsatzbereit | Deklarierte Typen bleiben erhalten |
| `unknown_source` | Konfigurierter Name ist nicht geladen oder wurde entfernt | Kein Beitrag |
| `unsupported_role` | Quelle implementiert die ausgewählte Rolle nicht | Kein Beitrag |
| `invalid_declaration` | Typdeklaration fehlt oder ist ungültig | Kein Beitrag |

`complete` ist nur dann `true`, wenn alle ausgewählten Asset-Rollen lesbare
Deklarationen haben. Eine leere Konfiguration liefert HTTP 200 mit
`instrument_types: []`, `sources: []`, `complete: true`. Fehlende oder ungültige
Deklarationen liefern ebenfalls HTTP 200, aber `complete: false`; vorhandene
gültige Typen bleiben enthalten. Ein Betriebsproblem allein macht den Katalog
nicht unvollständig. Gründe zur Betriebsdiagnose stehen unter `/sources`.

Die Auskunft löst keine Kurs-, Resolver- oder Metadatenabfragen aus.
`available` bestätigt keine Erreichbarkeit eines externen Dienstes und keine
Unterstützung jedes einzelnen Instruments. Änderungen an `sources.yaml` oder
Plugin-Dateien werden nach Neustart sichtbar. Der Endpunkt sendet
`Cache-Control: no-store` und `StockInfo-Generation`; die Generation stammt aus
derselben Datenbank wie `generation_id` von `GET /fields` und ist keine Katalogversion.
Clients laden die Auskunft beim Öffnen ihrer Filter neu. Während einer
gesperrten Migration gilt wie für andere Fachendpunkte der HTTP-503-Riegel.

Beispiele für Offline-Konsumententests liegen unter
[`contract/fixtures/instrument-types-200.json`](../contract/fixtures/instrument-types-200.json),
[`…-200-empty.json`](../contract/fixtures/instrument-types-200-empty.json) und
[`…-200-incomplete.json`](../contract/fixtures/instrument-types-200-incomplete.json).

[↑ Übersicht](#übersicht)

## Wie man den Vertrag prüft

Ohne Cross-Repo-CI, in drei Stufen:

1. **StockInfo** prüft Artefakt und Fixtures statisch gegeneinander
   (`tests/test_contract.py`) und die App gegen einen
   OpenAPI-Schnappschuss (`tests/test_contract_openapi.py`) — der schlägt an,
   sobald sich ein erfasstes Modell, ein Core-Pfad, `/fields` oder
   `/instrument-types` gegenüber dem gespeicherten Stand ändert.
2. **StockPortfolio** prüft seine Mapper gegen dieselben veröffentlichten
   Fixtures unter [`contract/fixtures/`](../contract/fixtures).
3. **Vor Releases** ein kleiner Lauf: eine bestehende Position gegen eine
   frische Profil-Datenbank.

Kein Repo klont das andere.

[↑ Übersicht](#übersicht)
