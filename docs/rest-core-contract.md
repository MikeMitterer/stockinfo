# Der REST-Core von StockInfo — was zugesagt ist

**Vertragsversion 2.0.0** · Stand 2026-08-26 · Tickets
[T-24](../_tickets/solved/T-24-rest-core-vertrag.md) und
[T-21](../_tickets/T-21-identitaet-mic-und-ticker.md)

> **Was 2.0.0 gegenüber 1.0.0 ändert** — ein Major-Sprung, weil beides
> bestehende Konsumenten bricht:
>
> * **`ticker` und `mic` sind zugesagte Pflichtfelder** von `quote` und
>   `instrument`, `listing_id` von `instrument`. Sie sind **nicht nullable**:
>   Ein Papier ohne kanonische Identität kommt seit T-21 gar nicht mehr in den
>   Bestand, und `null` zuzulassen wäre die Zusage, mit einem Zustand zu
>   rechnen, den es nicht geben darf.
> * **`GET /quote?symbol=` verlangt den Handelsplatz.** Ein suffixloses Symbol
>   wie `AAPL` wird mit `400` abgelehnt statt mit einer halben Identität
>   gespeichert. Eine Anfrage, die bisher `200` lieferte, liefert künftig
>   `400`.
> * **Neu im Core: `POST /instruments/intake`** — der eine zugesagte
>   Schreibweg. Er nimmt einen rohen Feldwert entgegen; was er bedeutet,
>   entscheidet der Core.

Dieses Dokument erklärt den Vertrag. **Verbindlich ist die Datei daneben:**
[`contract/core-contract.json`](../contract/core-contract.json). Sie ist
maschinenlesbar, die Fixtures werden gegen sie geprüft, und `GET /fields`
beantwortet sie zur Laufzeit aus derselben Quelle. Wo Text und Artefakt
auseinandergehen, gilt das Artefakt.

## Warum es das gibt

StockInfo wird verteilt — GitHub, Docker Hub, Unraid-Template. Wer die API
direkt nutzt statt des mitgelieferten Dashboards, bekommt jede Änderung ab, und
niemand erfährt davon. Dazu kommt StockPortfolio: derselbe Autor, aber ein
eigenes Artefakt mit eigenem Image und eigenem Update-Zeitpunkt. Auf einer
Unraid-Box laufen beide als getrennte Container, die niemand gleichzeitig
aktualisiert. Gemeinsame Eigentümerschaft ersetzt keinen Vertrag.

## Was der Core umfasst

Fünf öffentliche Modelle, jedes mit eigener Pflichtfeldmenge:

| Modell | Endpunkte |
|---|---|
| `quote` | `/quote`, `/quote/{isin}` |
| `instrument` | `/instruments`, `POST /instruments/intake` |
| `daily` | `/quote/{isin}/daily`, `/quote/by-symbol/{symbol}/daily` |
| `history` | `/quote/{isin}/history`, `/quote/by-symbol/{symbol}/history` |
| `fx` | `/fx` |

Nicht im Core: die Diagnoseendpunkte (`/env`, `/analyze`, `/ready`), die
Schreibvorgänge des Dashboards und `/exchanges`. Sie dürfen sich ändern.

**Eine Ausnahme seit 2.0.0:** `POST /instruments/intake` ist ein
Schreibvorgang und **trotzdem** zugesagt. Er ist der eine Weg, auf dem ein
Papier in den Bestand kommt, und das Dashboard darf ihn nicht selbst
nachbauen — täte es das, klassifizierte es Eingaben nach einer zweiten
Grammatik, die beim ersten Plugin von der des Core abwiche. Die übrigen
Schreibknöpfe der Oberfläche (`PUT`/`DELETE` an Instrumenten, `/refresh`)
bleiben außerhalb.

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

**Der Tages-Schlusskurs ist unbereinigt.** `daily.close` ist der Kurs, wie er an
dem Tag galt — Dividenden und Splits sind nicht eingerechnet. Das ist eine
Entscheidung, keine Auslassung: Eine bereinigte Reihe ändert rückwirkend alte
Werte, und ein Depot, das Stückzahlen zu historischen Kursen hält, rechnet
damit falsch. Wer eine bereinigte Reihe braucht, rechnet sie selbst.

**Währung ist Pflicht, nicht Zierde.** Ein Preis ohne Währung ist für eine
Depotrechnung wertlos, und die naheliegende Vermutung — „wird schon Euro sein" —
ist bei einem Londoner Listing in Pence falsch. Liefert eine Quelle einen Preis
ohne Währung, antwortet die API mit `502`, statt zu raten. Das ist die eine
bewusste Verhaltensänderung dieses Tickets.

**`GBp` ist kein Tippfehler.** Londoner Kurse notieren in Pence, ein Hundertstel
Pfund. Der Wert wird originalgetreu durchgereicht; wer nach `GBP` umrechnen
will, teilt durch 100.

## Identität: `listing_id` für Maschinen, `symbol` für Menschen

`symbol` bleibt Pflichtfeld und Anzeigename — aber es ist **nicht garantiert
eindeutig**. Sobald `US` in `XNYS` und `XNAS` zerfällt (T-21), können zwei
Listings dasselbe Symbol tragen; regionale Plugins bringen weitere Konventionen
mit.

Der heutige Lookup lautet:

```sql
SELECT * FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1
```

Das ist nicht undefiniert, sondern definiert falsch: Bei zwei gleichnamigen
Zeilen trifft `DELETE /instruments/by-symbol/{symbol}` die ältere. Deshalb:

- **`listing_id`** — eine opake UUID, bei Anlage einmal erzeugt und **nicht**
  aus `ticker`, `mic`, ISIN oder dem lokalen Schlüssel abgeleitet. Jede Zeile
  bekommt eine, auch eine unaufgelöste. Sie überlebt manuelle Zuordnung,
  Metadatenänderungen, Sicherung und Wiederherstellung. Konsumenten zerlegen
  sie nie.
- **`409 Conflict`** bei mehrdeutigem Symbol, mit Kandidatenliste im Rumpf —
  statt still das Falsche zu treffen.

**Ein aktives Listing je ISIN.** `isin TEXT UNIQUE` ist eine Grenze, kein
Zufall: Ein Profil wählt genau ein Listing. Mehrere gleichzeitige Listings
derselben ISIN wären eine eigene Schema- und Konsumenten-Erweiterung.

### Zwei Fälle unter einem `409` — unterschieden wird über `code`

Der Status allein sagt seit 2.0.0 nicht mehr, was los ist. Der Rumpf ist in
beiden Fällen ein `ErrorDetail` (`{code, params}`), und erst die Kennung trennt
sie:

| `code` | Bedeutung | Gilt an |
|---|---|---|
| `symbol_ambiguous` | Mehrere Listings tragen diesen Anzeigenamen. Rumpf: `detail`, `code`, `params`, `candidates` — jeder Kandidat mit `listing_id`, `symbol`, `mic`, `exchange`, `isin`. | jedem Endpunkt, der ein `symbol` entgegennimmt — lesend wie verändernd |
| `identity_conflict` | Zwei gewachsene Zeilen beanspruchen dieselbe kanonische Identität — `AAPL/XNAS` ohne ISIN neben `AAPL/XNYS` mit ihr, und dieselbe ISIN wandert nach XNAS. Rumpf: `code`, `params` mit `ticker`, `mic`, `isin` (sofern bekannt). | jedem Endpunkt, der speichert |

**Keiner der beiden ist ein Eingabefehler**, und deshalb ist keiner ein `400`:
Der Aufrufer hat nichts falsch gemacht. Beim mehrdeutigen Symbol hat er einen
Namen genannt, der seit T-21 keiner mehr ist; beim Identitätskonflikt meinen
zwei gewachsene Zeilen dasselbe Listing.

`symbol_ambiguous` trägt die Kandidaten mit, weil ein `409` ohne sie eine
Sackgasse wäre — mit ihnen hat der Aufrufer je Kandidat eine `listing_id`, und
die ist eindeutig. **Verändert wird dabei nichts.** Das ist der Punkt: Der
Löschweg per Symbol entfernte bei zwei gleichnamigen Listings beide samt
Historie, der Kursweg gab still die ältere Notierung aus, und das Nachtragen
einer ISIN schrieb sie an den Handelsplatz, den niemand gemeint hatte. Alle
drei sind seit Runde 45 dieser `409`.

`identity_conflict` sagt, was der Fall ist — er löst ihn nicht. Die
Zusammenführung zweier Zeilen ist eine Datenoperation mit eigener
Entscheidung und liegt in `T-33`. Bis Runde 43 sagte die API gar nichts: Der
Fehler entstand im Repository, wurde nirgends behandelt und trat als
`500 Internal Server Error` aus.

## Die Generation: woran ein Konsument einen Datensatzwechsel erkennt

Wechselt das Quellenprofil oder die Datenbank, sind gespeicherte Kursdaten eines
Konsumenten nicht mehr zuzuordnen. Dafür gibt es zwei Dinge:

```http
GET /generation
Cache-Control: no-store

{ "generation_id": "550e8400-e29b-41d4-a716-446655440000" }
```

und auf **jeder** Antwort — auch auf `404`, `409`, `422`, `502` — den Header:

```http
StockInfo-Generation: 550e8400-e29b-41d4-a716-446655440000
```

Die Fehlerfälle sind kein Detail: Nach einem Profilwechsel kann ein bisher
bekanntes Papier fehlen. Ohne Header auf der `404` zeigt der Konsument seinen
alten Cache weiter.

**`/generation` ist die Wahrheit, der Header nur das Signal.** Zwei Anfragen
können sich über einen Profilwechsel hinweg überschneiden, und eine verspätete
Antwort aus A trifft nach einer schnellen aus B ein. UUIDs tragen keine
Reihenfolge — wer dem Header blind folgt, springt von B zurück auf A. Weicht
der Header ab, wird die Antwort deshalb verworfen, `/generation` bestätigt den
Stand, und erst danach wird umgeschaltet.

**CORS gehört dazu.** Ohne `Access-Control-Expose-Headers` kann
Browser-JavaScript den Antwort-Header nicht lesen. StockPortfolio läuft
cross-origin; der Header wäre dort unsichtbar — gesetzt, aber wirkungslos.

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

## Entschieden, aber noch nicht zugesagt

Der Abschnitt `planned` im Artefakt nennt, was kommt und in welchem Ticket:
der `details`-Container mit T-26, die Laufzeitseite der Generation mit T-25.
Diese Einträge sind **nicht** Teil von `core_version 2.0.0`. Sie stehen da,
damit ein Konsument weiß, was kommt — nicht, damit er sich darauf verlässt.

`listing_id` und `(ticker, mic)` standen bis 1.0.0 hier; mit T-21 sind sie
zugesagt und deshalb aus `planned` verschwunden.

## Der Vertrag ist abfragbar, nicht nur dokumentiert

Ein Dokument, das niemand zur Laufzeit lesen kann, hilft einem Konsumenten
nicht — er müsste raten, ob seine gecachte Feldliste noch stimmt. `GET /fields`
liefert deshalb dieselbe Auskunft im Betrieb:

```json
{
  "core_version": "2.0.0",
  "core": { "quote": [ {"name": "price", "kind": "number", "required": true, "meaning": "…"} ], … },
  "endpoints": { "quote": [ {"path": "/quote/{isin}", "method": "GET", "query": []} ], … },
  "details_version": 0,
  "details": []
}
```

Bedient wird das aus **derselben Datei**, gegen die auch die Fixtures geprüft
werden. Eine zweite Feldliste im Code gäbe es sonst sofort — und der Konsument
bekäme je nach Weg eine andere Zusage.

Zwei Nummern, zwei Ebenen: `core_version` folgt SemVer über den geschlossenen
Core, `details_version` zählt die offene Detailmenge (T-26). Zwischenspeichern
sollte ein Konsument unter `(generation_id, core_version, details_version)`.

## Wie man den Vertrag prüft

Ohne Cross-Repo-CI, in drei Stufen:

1. **StockInfo** prüft Artefakt und Fixtures statisch gegeneinander
   (`tests/test_contract.py`) und die App gegen einen
   OpenAPI-Schnappschuss (`tests/test_contract_openapi.py`) — der schlägt an,
   sobald sich ein Core-Modell, ein Core-Pfad oder `/fields` ändert, ohne dass
   jemand die Vertragsversion angefasst hat.
2. **StockPortfolio** prüft seine Mapper gegen dieselben veröffentlichten
   Fixtures unter [`contract/fixtures/`](../contract/fixtures/).
3. **Vor Releases** ein kleiner Lauf: eine bestehende Position gegen eine
   frische Profil-Datenbank.

Kein Repo klont das andere.
