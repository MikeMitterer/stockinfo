# T-33 · Zwei Zeilen, ein Listing — Zusammenführung entscheiden

- **Status:** offen (Entscheidung ausstehend)
- **Angelegt:** 2026-08-26, aus T-21 Teil 3, Übergabe 3, Codex-Runde 43
- **Repo:** StockInfo
- **Hängt an:** T-21 Teil 3 (der `409` ist dort gebaut, die Auflösung nicht)
- **Gehört in:** T-28, das finale Plugin-Gate

## Verify-Matrix

| # | Where | Look for | AI | Human |
|---|---|---|---|---|
| 1 | Entscheidung | Mike hat entschieden, **welche `listing_id` überlebt**, wenn zwei Zeilen dasselbe Listing meinen — die ältere, die mit den meisten Kurspunkten, oder eine neu vergebene | ➖ [^a] | |
| 2 | Entscheidung | Mike hat entschieden, was mit den Kurspunkten der unterlegenen Zeile geschieht: verschieben, archivieren oder getrennt halten | ➖ [^a] | |
| 3 | Aufruferseite | wer die Zusammenführung auslöst — der Benutzer im UI, ein Wartungsendpunkt oder der Abruf selbst. Der Kursabruf darf sie **nicht** nebenbei tun; genau das trennt `409` von `200` | | |
| 4 | `app/repository.py` | die Zusammenführung läuft in **einer** Transaktion; ein Abbruch lässt keinen halben Zustand zurück | | |
| 5 | echte Kette | nach der Zusammenführung gibt es genau eine aktive Zeile, `one_active_listing_per_isin` gilt wieder, und der `409` aus T-21 tritt für denselben Fall nicht mehr auf | | |
| 6 | Konsumentensicht | eine verschwundene `listing_id` ist ein Datensatzwechsel — der Konsument muss ihn erkennen können, nicht raten (siehe `generation` im Core-Vertrag) | | |

[^a]: **Nicht entschieden.** Codex hat den Schnitt in Runde 43 ausdrücklich
    vorgeschlagen, damit T-21 nicht an einer Datenentscheidung hängt, die mit
    Identität und Vertrag nichts zu tun hat.

## Worum es geht

Zwei Zeilen können dasselbe Listing meinen, ohne dass jemand etwas falsch
gemacht hat. Der gemessene Fall aus T-21:

* `AAPL/XNAS` liegt ohne ISIN im Bestand — angelegt, bevor die Quelle eine
  ISIN meldete.
* `AAPL/XNYS` liegt mit `US0378331005` daneben.
* Ein Kursabruf für `AAPL.XNAS` bekommt von der Quelle dieselbe ISIN
  mitgeliefert. Die ISIN-Suche findet die XNYS-Zeile, deren Aktualisierung
  läuft in den eindeutigen `(ticker, mic)`-Index.

Nach `one_active_listing_per_isin` beschreiben beide dasselbe Papier. Sie
zusammenzuführen ist aber **keine** Nebenwirkung eines Kursabrufs: Es
entscheidet, welche Identität überlebt und was mit der Historie der anderen
geschieht. Beides ist für einen Konsumenten sichtbar und nicht rückgängig zu
machen.

## Was T-21 dazu schon getan hat

**Den Fall benannt und ehrlich beantwortet, nicht gelöst.** Seit Runde 44
tritt er als typisierter `409` mit `code: identity_conflict` aus, an allen
drei speichernden Vertragsendpunkten (`POST /instruments/intake`, `GET
/quote`, `GET /quote/{isin}`). Davor war es ein `500`.

Der `409` sagt, was der Fall ist. Er sagt nicht, was zu tun ist — das ist
dieses Ticket.

## Warum das nicht in T-21 gehört

T-21 zieht eine Identitätsgrenze: `ticker` und `mic` sind Pflicht, `symbol`
ist kein Bezeichner mehr. Diese Grenze ist gezogen, sobald der Konflikt
sichtbar und typisiert ist.

Was danach mit zwei kollidierenden Zeilen geschieht, ist eine Frage an die
**Daten**, nicht an den Vertrag — und sie hängt an der noch offenen
`listing_id`- und Historienpolitik aus T-29 (Alias-Lebenszyklus, zwei
Backup-Arten). Sie in T-21 zu beantworten hieße, dieselbe Entscheidung zweimal
zu treffen.

## Die Auswege, wie sie beim Fund aussahen

1. **Die ältere Zeile gewinnt.** Einfach zu erklären, aber sie ist nicht
   zwangsläufig die mit der Historie — die kann an der jüngeren hängen.
2. **Die Zeile mit den meisten Kurspunkten gewinnt.** Verliert am wenigsten
   Daten, aber die `listing_id` eines Konsumenten kann dabei verschwinden,
   ohne dass er es merkt.
3. **Beide bleiben, eine wird inaktiv.** Kostet keine Daten und ist
   umkehrbar — verlangt aber einen Zustand „inaktives Listing", den es heute
   nicht gibt, und der Bestand ist danach nicht mehr selbsterklärend.

Keiner der drei ist offensichtlich richtig. Die Entscheidung gehört Mike.
