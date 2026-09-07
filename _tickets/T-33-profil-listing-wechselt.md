# T-33 · Wenn das Profil den Handelsplatz wechselt

- **Status:** offen (Entscheidung ausstehend)
- **Angelegt:** 2026-08-26, aus T-21 Teil 3, Übergabe 3, Codex-Runde 43
- **Neu gerahmt:** 2026-08-27, nach Codex-Runde 44 — der erste Zuschnitt
  verwechselte Wertpapier und Listing
- **Repo:** StockInfo
- **Hängt an:** T-21 Teil 3 (der `409` ist dort gebaut, die Auflösung nicht)
- **Einordnung:** eigenständiges offenes Ticket; keine Gate-Beziehung

## Die Grenze, an der dieses Ticket liegt

Drei Begriffe, die der erste Zuschnitt in einen Topf geworfen hat:

| Begriff | Was er bezeichnet | Kennung |
|---|---|---|
| **Wertpapier** | Die Aktie von Apple | ISIN `US0378331005` |
| **Listing** | Ihre Notierung an **einem** Handelsplatz | `listing_id`, eine je Listing |
| **Aktives Profil-Listing** | Das eine Listing, das dieses Profil je ISIN führt | `one_active_listing_per_isin` |

`AAPL/XNAS` und `AAPL/XNYS` sind damit **zwei Listings desselben
Wertpapiers**, nicht zwei Zeilen desselben Listings. Beide dürfen im Bestand
stehen — `#2f` in T-21 verlangt es sogar.

Daraus folgt die Frage, die dieses Ticket stellt, und ebenso die, die es
**nicht** stellt:

* **Keine Frage ist**, „welche `listing_id` überlebt". Die XNAS-ID bezeichnet
  XNAS, die XNYS-ID bezeichnet XNYS. Eine davon zur anderen zu erklären hieße,
  eine Kennung auf etwas zeigen zu lassen, das sie nicht bezeichnet — und der
  Vertrag sagt ausdrücklich zu, dass sie opak ist und nicht wandert.
* **Die Frage ist**, was geschieht, wenn dasselbe Wertpapier sein aktives
  Profil-Listing wechselt: XNYS war es, XNAS soll es werden.

## Verify-Matrix

| # | Where | Look for | AI | Human |
|---|---|---|---|---|
| 1 | Entscheidung | Mike hat entschieden, was mit dem **bisherigen** Profil-Listing geschieht: deaktiviert stehenbleiben, entfernt werden, oder als eigenständiges Listing ohne Profilbezug weiterleben | ➖ [^a] | |
| 2 | Entscheidung | Mike hat entschieden, was mit dessen **handelsplatzgebundener Historie** geschieht. Sie gehört zu XNYS und wird an XNAS nicht wahrer — sie umzuhängen erzeugt eine Kursreihe, die es so nie gab | ➖ [^a] | |
| 3 | Sichtbarkeit | der Wechsel ist für einen Konsumenten **erkennbar**, nicht bloß geschehen: Sein gespeicherter Stand hängt an einer `listing_id`, die das Profil nicht mehr führt | ➖ [^b] | |
| 4 | Auslöser | wer den Wechsel auslöst — der Benutzer im UI, ein Wartungsendpunkt oder die Auflösung selbst. Der Kursabruf darf ihn **nicht** nebenbei vollziehen; genau das trennt den `409` von einem stillen `200` | | |
| 5 | `app/repository.py` | der Wechsel läuft in **einer** Transaktion; ein Abbruch lässt keinen halben Zustand zurück | | |
| 6 | echte Kette | nach dem Wechsel führt das Profil genau ein aktives Listing für diese ISIN, und der `identity_conflict` aus T-21 tritt für denselben Bestand nicht mehr auf | | |
| 7 | echtes Duplikat | der **andere** Fall ist getrennt behandelt: zwei Zeilen mit derselben `(ticker, mic)`-Identität sind ein Datenfehler, kein Handelsplatzwechsel. Heute verhindert ihn der Eindeutigkeitsindex — das Ticket sagt, was gilt, falls er je fällt | | |

[^a]: **Nicht entschieden.** Codex hat den Schnitt in Runde 43 vorgeschlagen,
    damit T-21 nicht an einer Datenentscheidung hängt, die mit Identität und
    Vertrag nichts zu tun hat.
[^b]: Der Vertrag hat dafür bereits einen Platz — `generation` samt
    `StockInfo-Generation`-Header. Ob ein Listingwechsel dieses Signal
    auslöst oder ein feineres braucht, ist Teil der Entscheidung und hängt an
    T-25.

## Wie der Fall entsteht

Kein konstruierter Sonderfall, sondern gewachsener Bestand:

* `AAPL/XNAS` liegt ohne ISIN im Bestand — angelegt, bevor die Quelle eine
  ISIN meldete.
* `AAPL/XNYS` liegt mit `US0378331005` daneben und ist das aktive
  Profil-Listing.
* Ein Kursabruf für `AAPL.XNAS` bekommt von der Quelle dieselbe ISIN
  mitgeliefert. Die ISIN-Suche findet die XNYS-Zeile, deren Aktualisierung
  läuft in den eindeutigen `(ticker, mic)`-Index.

Was hier passieren *will*, ist ein Wechsel des aktiven Profil-Listings von
XNYS nach XNAS. Er ist für einen Konsumenten sichtbar und nicht rückgängig zu
machen, und er entscheidet über die Historie eines Handelsplatzes — deshalb
passiert er nicht als Nebenwirkung eines Kursabrufs.

## Was T-21 dazu schon getan hat

**Den Fall benannt und ehrlich beantwortet, nicht gelöst.** Seit Runde 44
tritt er als typisierter `409` mit `code: identity_conflict` aus, an jedem
Endpunkt, der speichert. Davor war es ein `500`.

Der `409` sagt, was der Fall ist. Er sagt nicht, was zu tun ist — das ist
dieses Ticket.

## Warum das nicht in T-21 gehört

T-21 zieht eine Identitätsgrenze: `ticker` und `mic` sind Pflicht, `symbol`
ist kein Bezeichner mehr. Diese Grenze ist gezogen, sobald der Konflikt
sichtbar und typisiert ist.

Was danach mit dem bisherigen Profil-Listing geschieht, ist eine Frage an die
**Daten**, nicht an den Vertrag — und sie hängt an der noch offenen
`listing_id`- und Historienpolitik aus T-29 (Alias-Lebenszyklus, zwei
Backup-Arten) sowie am Generationssignal aus T-25. Sie in T-21 zu beantworten
hieße, dieselbe Entscheidung zweimal zu treffen.

> **Nachtrag 2026-09-07:** T-29 ist verworfen und trägt diese Politik nicht mehr.
> Der Alias ist seit T-23/T-31 kein Abrufschlüssel; der Bestandsschutz für
> veröffentlichte Aliase steht in [T-30](T-30-plugin-boersenauskunft.md), der
> portable JSON-Weg ist gestrichen. Die `listing_id`- und Historienfrage dieses
> Tickets hat damit **keinen** Vorgänger mehr, an dem sie hängt — sie ist hier
> zu beantworten oder ausdrücklich einem anderen Ticket zuzuweisen.

## Die Auswege, wie sie beim Fund aussahen

Alle drei betreffen das **bisherige** Profil-Listing. Keiner verschiebt eine
`listing_id`.

1. **Es bleibt, wird aber inaktiv.** Kostet keine Daten, ist umkehrbar, und
   die Historie bleibt an ihrem Handelsplatz. Verlangt einen Zustand
   „inaktives Listing", den es heute nicht gibt — und der Bestand ist danach
   nicht mehr selbsterklärend: `GET /instruments` müsste sagen, was ein
   inaktiver Eintrag bedeutet.
2. **Es wird entfernt, samt seiner Historie.** Der Bestand bleibt
   selbsterklärend, aber die Kurspunkte eines echten Handelsplatzes
   verschwinden — bei `GOLD.SG` waren das 257 Tageskurse, und die Warnung im
   Entwurf steht genau deswegen dort.
3. **Es bleibt als gewöhnliches Listing ohne Profilbezug.** Nichts geht
   verloren, nichts wird neu erfunden — dafür führt das Profil zwei Zeilen
   derselben ISIN, und `one_active_listing_per_isin` müsste ausdrücklich
   sagen, dass „aktiv" eine Eigenschaft des Profils ist und nicht der Zeile.

Keiner der drei ist offensichtlich richtig. Die Entscheidung gehört Mike.
