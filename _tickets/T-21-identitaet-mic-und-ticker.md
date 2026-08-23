# T-21 · Identität auf MIC + Ticker umstellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | Teil 1 in-review | 1 Tag | Schema-Migration, Symbolerzeugung | — |

**Löst:** Der Identifikator eines Papiers ist heute das **Yahoo-Symbol**
(`EUNL.DE`) — in der Datenbank, in der API, im Dashboard. Damit ist yfinance
nicht ersetzbar, sondern nur ergänzbar. Jede zweite Kursquelle müsste Yahoos
Suffix-Schreibweise nachbilden.

**Der Brocken der Serie.** Alles andere ist klein dagegen.

> **Stand nach Codex-Runde 4.** Zwei frühere Fassungen sind überholt: `symbol`
> wird **nicht** `NULL`-fähig (es bleibt am REST-Rand zugesagt), verliert aber
> seinen **globalen Eindeutigkeits-Index** — der gehört auf `(ticker, mic)`.

**Hängt an: T-24** — erst muss feststehen, was die API zusagt und wie eindeutig
adressiert wird. **Blockiert:** T-23 (ein Plugin, das Yahoo-Symbole erwarten
muss, ist kein Plugin).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Drei Übergaben statt einer** *(Claude, 2026-08-22)* — ein Tag Arbeit ist für
> einen Diff-Review zu viel am Stück. Die Schnitte liegen dort, wo das Ticket
> selbst schon trennt:
>
> | | Umfang | Zeilen | Commit |
> |---|---|---|---|
> | **Teil 1** | Schema, Migration, Meldung offener Fälle, Index-Umzug | `#1`, `#2`, `#3b` | Runde 5 |
> | **Teil 2** | Erzeugung neuer Papiere, Yahoo-Normalisierung, `ExchangeDef` aufräumen | `#5` | offen |
> | **Teil 3** | API und Dashboard, offene Zuordnungen sichtbar und von Hand setzbar, Vertragsversion | `#2b`, `#2c`, `#3`, `#4` | offen |
>
> `#6` (`make test`) läuft in jeder Übergabe mit.

> **Verify `#2` verlangt für `AAPL` mehr, als die Migration wissen kann**
> *(Claude, 2026-08-22)*
>
> Die Zeile erwartet `AAPL` → `AAPL`/**`XNAS`** direkt nach der Migration. Das
> Ticket sagt zwei Absätze weiter aber selbst: Für suffixlose Symbole liefert
> die Börsentabelle nur den Sammelcode `US`, und „welcher echte MIC gilt,
> **steht dort nicht** — das muss aus dem aufgelösten Listing kommen".
>
> Beides zusammen geht nicht. Die Migration läuft beim Start und offline; sie
> müsste OpenFIGI fragen, um `XNYS` von `XNAS` zu unterscheiden — ein Start,
> der Netz braucht und in ein Rate-Limit laufen kann, und das für jede
> bestehende Zeile.
>
> **Umgesetzt ist deshalb:** Ein suffixloses Symbol wird **nicht geraten**. Die
> Zeile bekommt `identity_status = legacy_unresolved` und erscheint in der
> Liste offener Zuordnungen; den echten MIC trägt der nächste erfolgreiche
> Auflösungslauf nach (Teil 2) oder ein Mensch von Hand (Teil 3). Das ist genau
> die Regel, die das Ticket für nicht zerlegbare Symbole ohnehin aufstellt —
> `AAPL` ist einer dieser Fälle, nicht die Ausnahme davon.
>
> Verify `#2` prüft entsprechend `EUNL.DE` → `EUNL`/`XETR` und `XIC.TO` →
> `XIC`/`XTSE` **nach der Migration**, `AAPL` dagegen als offenen Fall.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | bestehende Datenbank, Migration laufen lassen | zerlegbare Instrumente haben `ticker` und `mic`; **nicht** zerlegbare werden gemeldet, nicht geraten | ✅ [^a] | |
| 1b | dieselbe Migration auf einer **Kopie des echten Bestands** | keine Zeile und kein Kurspunkt geht verloren, auch beim zweiten Start nicht | ✅ [^g] | |
| 2 | Stichprobe nach der Migration | `EUNL.DE` → `EUNL`/`XETR`, `XIC.TO` → `XIC`/`XTSE`; `AAPL` bleibt **offen** statt geraten (siehe Kasten oben) | ✅ [^b] | |
| 2b | Instrument mit Fremdsymbol (`BRK-B`, aus dem Yahoo-Fallback) | erscheint in einer Liste offener Zuordnungen, mit Grund | ◑ [^c] | |
| 2c | derselbe Fall, manuelle Zuordnung | lässt sich von Hand auf `(ticker, mic)` setzen | ➖ Teil 3 | |
| 3 | `GET /instruments` | `symbol` weiterhin vorhanden und unverändert (Profil-Links hängen daran) | ✅ [^d] | |
| 3b | Datenbank-Schema | Eindeutigkeit liegt auf `(ticker, mic)`; `symbol` ist **nicht mehr** global unique | ✅ [^e] | |
| 4 | Dashboard, Assets-Tabelle | unverändert; Yahoo- und extraETF-Links funktionieren | | |
| 5 | neues Papier aufnehmen | `ticker`/`mic` werden gefüllt, `symbol` daraus erzeugt | ➖ Teil 2 | |
| 6 | `make test` | Backend, Plugin-API und Dashboard grün | ✅ [^f] | |

[^a]: `tests/test_identity_migration.py`, **vierzehn** Tests gegen eine
    nachgestellte Alt-Datenbank mit vier bezeichnenden Fällen. Zerlegt werden `EUNL.DE` und
    `XIC.TO`; `AAPL` (suffixlos) und `BRK-B` (fremde Schreibweise) bleiben
    offen. Die Migration läuft zweimal — sie muss idempotent sein.
[^b]: `test_bekannte_suffixe_werden_zerlegt` und die beiden Gegenproben
    `test_suffixloses_symbol_wird_nicht_geraten` /
    `test_fremde_schreibweise_wird_nicht_geraten`. Dazu
    `tests/test_exchanges.py` mit der Rückrechnung selbst — einschließlich
    `test_kein_suffix_ist_doppelt_vergeben`: Käme eine Börse mit belegtem
    Suffix dazu, wäre `split_symbol` stillschweigend mehrdeutig, und dieser
    Test schlägt an, statt dass die Migration falsch zuordnet.
[^c]: **Nur als Protokollmeldung.** `test_die_offenen_faelle_werden_gemeldet`
    belegt, dass die Migration `identity_unresolved` mit Anzahl und Symbolen
    schreibt. Eine abfragbare *Liste* offener Zuordnungen ist Teil 3 — dort
    steht auch der Grund je Fall.
[^d]: Der Index auf `symbol` ist weg, die Spalte nicht: `symbol TEXT NOT NULL`
    steht unverändert im Schema, und die 370 Tests der Suite fahren die
    bestehenden Symbol-Endpunkte weiter durch.
[^e]: `test_die_eindeutigkeit_liegt_auf_ticker_und_mic` prüft beides:
    `idx_instruments_symbol` ist verschwunden, `idx_instruments_ticker_mic`
    ist eindeutig. Zwei weitere Tests halten die Folgen fest — mehrere offene
    Zeilen dürfen nebeneinander stehen (SQLite zählt `NULL` als eigenen Wert),
    ein echter Konflikt fällt weiterhin auf.
[^f]: `.venv/bin/pytest tests/ -q` → `370 passed, 29 skipped`;
    `make test-plugin-api` → 36; Ruff sauber.
[^g]: `./_tickets/T-21-smoke.sh --run` gegen eine **Sicherung** von
    `data/stockinfo.db` (sechs gewachsene Papiere, 48 Kurspunkte) — das
    Original wird nur gelesen. Die Sicherung entsteht über die
    SQLite-Backup-API, nicht per `cp`: Die App läuft im WAL-Modus, und eine
    Dateikopie ließe committete Einträge aus — der Lauf liefe dann an genau
    den neuesten Fällen vorbei (Codex, Runde 2). Neun Checks grün: 6 Instrumente vorher und
    nachher, 48 Kurspunkte vorher und nachher, sechs eindeutige `listing_id`,
    vier zerlegt (`VGWL.DE`, `EUNL.DE`, `APC.DE`, `BRYN.DE` → `XETR`), zwei
    offen (`GOLD.SG` — das Suffix `.SG` steht nicht in der Tabelle — und
    `VTI`, suffixlos), Indizes umgezogen **und eindeutig**. Das Script
    migriert **zweimal**; genau dort hat die Alt-Bereinigung in Runde 1
    Listings gelöscht.

    Die Prüfungen rechnen nach statt zu behaupten, und zwar in der
    **Gegenrichtung**: Was dieser Lauf zugeordnet hat, muss sich aus
    `(ticker, mic)` wieder zu `symbol` zusammensetzen; offene Zeilen tragen
    weder Ticker noch MIC; bereits bestehende Zuordnungen bleiben unverändert
    (`#2c`) und dürfen keinen Sammelcode tragen (`#2d`). Ein Lauf, der nichts
    zugeordnet hat, gilt als **nicht geprüft**. Ein leerer Bestand lässt den Lauf **fehlschlagen** —
    vorher hätte er dort grün gemeldet, ohne einen einzigen Fall geprüft zu
    haben (Codex, Runde 2). Gegenproben: leere Datenbank → Exit 1; ein
    committeter Eintrag im WAL → wird mitgesichert und mitgezählt (7 statt 6).

    **Das Oracle rechnet vorwärts** (Codex, Runde 3): Die Migration zerlegt
    `symbol` → `(ticker, mic)`, die Prüfung setzt `(ticker, mic)` → `symbol`
    zusammen. Mit derselben Funktion zu prüfen hieße, sich selbst recht zu
    geben — und es verwarf einen gültigen Zielzustand: Ein von Hand
    zugeordnetes `VTI` → `VTI/XNAS` behält sein suffixloses `symbol`.
    Nachvalidiert wird deshalb nur, was **dieser Lauf** zugeordnet hat; `#2c`
    hält zusätzlich fest, dass bestehende Zuordnungen unverändert bleiben.
    Gegenprobe mit `WALONLY/XNAS` im WAL: angenommen.

---

## Details

### Warum es geht — die Rückrechnung ist eindeutig

Gemessen am 2026-08-19 über die vollständige Börsentabelle:

```
Börsen gesamt: 33
Suffixe doppelt vergeben: keine — Zuordnung ist eindeutig

EUNL.DE  -> ticker=EUNL  suffix=.DE  mic=XETR
XIC.TO   -> ticker=XIC   suffix=.TO  mic=XTSE
VTI      -> ticker=VTI   suffix=''   → Sammelcode US, **kein** MIC
```

Die letzte Zeile zeigt zugleich die Grenze der Messung: Für suffixlose Symbole
liefert die Tabelle nur den Sammelcode `US`. Welcher echte MIC gilt (`XNYS`
gegen `XNAS`), steht dort nicht — das muss aus dem aufgelösten Listing kommen.

Kein Suffix ist doppelt belegt. **Für Symbole, die aus der eigenen Regel
stammen**, ist die Zerlegung damit eindeutig.

Das gilt aber nicht für alle: Was der Yahoo-Fallback geliefert hat, folgt der
Konvention nicht zwingend (siehe unten). Diese Fälle werden **gemeldet**, nicht
geraten — „jedes Symbol lässt sich zerlegen" wäre eine Behauptung, die der
nächste Bestand widerlegt.

### Was `symbol` heute erzwingt

```
app/db.py:21    symbol TEXT NOT NULL
app/db.py:172   CREATE UNIQUE INDEX idx_instruments_symbol
```

Pflichtfeld **und** global eindeutig. Bleibt das so, braucht auch ein Instrument,
das ausschließlich über EODHD oder Twelve Data verwaltet wird, ein gültiges,
eindeutiges **Yahoo**-Symbol. Yahoo wäre dann weiterhin Teil der Identität — das
Ticket verfehlte sein eigenes Ziel.

**Weg (revidiert nach Codex-Runde 3):** `symbol` **bleibt verpflichtend** — die
erste Fassung wollte es `NULL`-fähig machen.

Der Grund ist **nicht** StockPortfolio: Das gehört demselben Autor, ist nicht
öffentlich und wäre in einem Zug mitzuändern. Der Grund ist, dass StockInfo
selbst verteilt wird — GitHub, Docker Hub, Unraid-Template. Wer die API direkt
nutzt, bekäme den Bruch ab, und man erfährt es nicht.

Was an `symbol` hängt, zeigt der Testkonsument stellvertretend:

```text
src/api/types.ts:17        symbol: string                      // nicht nullable
src/types/portfolio.ts:29  symbol: string                      // Pflicht je Position
src/api/mappers.ts:56      return entry.isin ?? entry.symbol   // Cache-Schlüssel
```

Die dritte Stelle bräche **still**: Der Cache-Schlüssel wäre `undefined`.

Stattdessen **additiv**: `ticker` und `mic` kommen dazu und werden die
kanonische Identität; `symbol` bleibt als stabiler Listing-Bezeichner erhalten
und wird nach derselben Regel erzeugt wie bisher. Das ist kein Anbieter-Alias —
das Format gehört der App (`resolver.py:130` bildet es aus der eigenen
`EXCHANGES`-Tabelle), nicht Yahoo.

**Der Eindeutigkeits-Index zieht mit um — aber nicht ersatzlos.** `symbol`
bleibt Pflichtfeld und verliert den globalen Unique-Index; an seine Stelle tritt
`(ticker, mic)` **und** eine `listing_id` als Schlüssel für Maschinen. Den Index
nur zu entfernen wäre ein stiller Bruch: `get_instrument_by_symbol` nimmt per
`ORDER BY id LIMIT 1` die ältere Zeile, und `DELETE /instruments/by-symbol/…`
träfe dann das falsche Instrument. Die Regeln dafür stehen in **T-24**.

Sind später mehrere Anbieter-Aliase nötig, gehören sie in eine eigene Tabelle
statt als Spalten in die Instrumentenzeile.

### Der eine Pfad, der die Migration bricht

`resolver.py:170` übernimmt im Yahoo-Fallback `top["symbol"]` — den String, den
Yahoos Suche liefert. Der folgt der eigenen Konvention **nicht** zwingend
(`BRK-B` mit Bindestrich). Solche Symbole sind später nicht sicher in `ticker` +
`mic` zu zerlegen.

**Entschieden (Codex, 2026-08-20): normalisieren, wenn eindeutig — sonst
ablehnen und sichtbar machen. Niemals raten.**

Der Yahoo-Adapter kennt Yahoos Eigenheiten, also gehört das Wissen dorthin:

1. Yahoos Börsencode über eine **explizite** Tabelle auf einen echten MIC abbilden
2. den Ticker nur für **bekannte, umkehrbare** Fälle in die kanonische Form bringen
3. das ursprüngliche Yahoo-Symbol als Provider-Alias behalten
4. `Resolved` erst liefern, wenn echter MIC **und** kanonischer Ticker feststehen

`BRK-B` darf **nicht** per Bindestrich-zu-Punkt-Regel zu `BRK.B` geraten werden —
diese Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
etwas anderes. Bleibt ein Treffer mehrdeutig: mit Grund in `/sources` und Log
sichtbar machen, nicht als `(ticker, mic)` speichern, `Unavailable` zurückgeben
und einen Weg zur Zuordnung von Hand anbieten.

„Übernehmen und als nicht zerlegbar markieren" wäre die schlechtere Variante:
Sie macht die gerade eingeführte kanonische Identität wieder optional und
belastet jedes spätere Quote- oder Daily-Plugin erneut mit einem Yahoo-Sonderfall.

### `US` ist kein MIC

`EXCHANGES` führt `US` als Sammelcode für NYSE/NASDAQ (OpenFIGI `exchCode=US`).
Das ist **kein** ISO-10383-MIC. Ein Feld, das mal echte MICs und mal diesen
internen Code enthält, wird beim ersten Anbieter, der echte MICs erwartet, zum
Problem.

**Entschieden (Codex, 2026-08-20):** Das kanonische Feld heißt `mic` und enthält
**ausschließlich echte MICs** (`XNYS`, `XNAS`). Der Sammelcode `US` bleibt als
interner OpenFIGI-Suchcode erhalten, taucht aber nie im kanonischen Feld auf.
Niemals raten, und niemals beide Codearten unter einem Namen führen.

Das betrifft auch T-18: Die Kaskade über die Heimatbörse muss auf echte MICs
abbilden, nicht auf den Sammelcode.

### Was sich sonst ändert

* `instruments` bekommt `ticker` und `mic` (nicht `exchange_mic` — der Name trüge sonst wieder zwei Codearten)
* Migration zerlegt bestehende Symbole über die Suffix-Tabelle
* Wer Kurse holt, setzt sein Format selbst zusammen — Yahoo `{ticker}{suffix}`,
  EODHD `{ticker}.{code}`, Twelve Data `symbol` + `mic_code`
* `ExchangeDef` verliert seine OpenFIGI-Spalten (`figi_id_type`, `figi_value`);
  dieses Wissen zieht zum OpenFIGI-Provider

### Warum das die Anbieterfrage löst

Recherchiert am 2026-08-19: **Kein kommerzieller Dienst verlangt ein eigenes
Identitätssystem.** Alle arbeiten mit Ticker plus Börse, nur die Schreibweise
unterscheidet sich — EODHD hängt `.XETRA` an, Twelve Data nimmt den MIC nach
ISO 10383 als eigenen Parameter. Und MIC ist bereits der Schlüssel der
`EXCHANGES`-Tabelle.

Quellen: [EODHD Exchanges API](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours),
[Twelve Data Docs](https://twelvedata.com/docs)

### Der Zwischenzustand — sonst ist „melden statt raten" nicht umsetzbar

Wären `ticker` und `mic` sofort `NOT NULL`, könnte die Migration eine nicht
zerlegbare Zeile weder stehen lassen noch melden: Sie müsste raten, den Start
blockieren oder Daten löschen. Genau die drei Auswege, die dieses Ticket
ausschließt.

**Also braucht es einen ausdrücklichen Zwischenzustand:**

- die neuen Spalten sind zunächst `NULL`-fähig
- eine Kennzeichnung wie `identity_status = legacy_unresolved` markiert offene
  Fälle — alternativ eine eigene Tabelle offener Zuordnungen
- der Altdatensatz bleibt in dieser Zeit **lesbar und nutzbar**
- erst nach erfolgreicher Zuordnung wird `(ticker, mic)` für diesen Datensatz
  zur Pflicht

Ohne diesen Zustand ist „später von Hand zuordnen" ein Versprechen, das die
Migration technisch nicht halten kann.

### Risiko

Die Migration ist die einzige der Serie, die bestehende Daten anfasst. Vor dem
Lauf eine Kopie der Datenbank, und die Zerlegung vorher als Trockenlauf über die
echten Daten prüfen — ein Symbol, das die Tabelle nicht kennt, muss auffallen
statt still `NULL` zu werden.

**Die Eindeutigkeit der Suffixe gilt für den Bestand, nicht für die Zukunft.**
Gemessen wurde die heutige `EXCHANGES`-Tabelle. Nicht abgedeckt sind neue oder
unbekannte Suffixe, suffixlose Nicht-US-Symbole, von Hand eingetragene Symbole
und Ticker, in denen ein Punkt zum Namen gehört (`BRK.A`). Die Migration muss
solche Fälle **melden** statt zu raten — und danach braucht es einen Weg, sie
von Hand zuzuordnen.

---

## Auflösung

_(offen)_
