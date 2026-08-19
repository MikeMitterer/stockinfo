# T-21 · Identität auf MIC + Ticker umstellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | Schema-Migration, Symbolerzeugung | — |

**Löst:** Der Identifikator eines Papiers ist heute das **Yahoo-Symbol**
(`EUNL.DE`) — in der Datenbank, in der API, im Dashboard. Damit ist yfinance
nicht ersetzbar, sondern nur ergänzbar. Jede zweite Kursquelle müsste Yahoos
Suffix-Schreibweise nachbilden.

**Der Brocken der Serie.** Alles andere ist klein dagegen.

> **Verschärft nach Codex-Review vom 2026-08-19.** Die erste Fassung wollte
> `symbol` „einfach behalten". Das genügt nicht: Die Spalte ist `NOT NULL` und
> global eindeutig — damit bliebe ein gültiges Yahoo-Symbol Pflicht für jedes
> Instrument, auch für eines, das nur über EODHD verwaltet wird. Siehe
> „Was `symbol` heute erzwingt".

**Hängt an:** nichts. **Blockiert:** T-23 (ein Plugin, das Yahoo-Symbole erwarten
muss, ist kein Plugin).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | bestehende Datenbank, Migration laufen lassen | jedes Instrument hat `ticker` und `exchange_mic`, **kein Datenverlust** | | |
| 2 | Stichprobe nach der Migration | `EUNL.DE` → `EUNL`/`XETR`, `XIC.TO` → `XIC`/`XTSE`, `VTI` → `VTI`/`US` | | |
| 3 | `GET /instruments` | `symbol` weiterhin vorhanden und unverändert (Profil-Links hängen daran) | | |
| 4 | Dashboard, Assets-Tabelle | unverändert; Yahoo- und extraETF-Links funktionieren | | |
| 5 | neues Papier aufnehmen | `ticker`/`exchange_mic` werden gefüllt, `symbol` daraus erzeugt | | |
| 6 | `make test` | Backend grün, Dashboard grün | | |

---

## Details

### Warum es geht — die Rückrechnung ist eindeutig

Gemessen am 2026-08-19 über die vollständige Börsentabelle:

```
Börsen gesamt: 33
Suffixe doppelt vergeben: keine — Zuordnung ist eindeutig

EUNL.DE  -> ticker=EUNL  suffix=.DE  mic=XETR
XIC.TO   -> ticker=XIC   suffix=.TO  mic=XTSE
VTI      -> ticker=VTI   suffix=''   mic=US
```

Kein Suffix ist doppelt belegt. Jedes gespeicherte Symbol lässt sich automatisch
zerlegen — keine Handarbeit, kein Datenverlust.

### Was `symbol` heute erzwingt

```
app/db.py:21    symbol TEXT NOT NULL
app/db.py:172   CREATE UNIQUE INDEX idx_instruments_symbol
```

Pflichtfeld **und** global eindeutig. Bleibt das so, braucht auch ein Instrument,
das ausschließlich über EODHD oder Twelve Data verwaltet wird, ein gültiges,
eindeutiges **Yahoo**-Symbol. Yahoo wäre dann weiterhin Teil der Identität — das
Ticket verfehlte sein eigenes Ziel.

**Weg:** `symbol` wird `NULL`-fähig und verliert den Eindeutigkeits-Index. Die
kanonische Identität ist `(ticker, exchange_mic)`; das Yahoo-Symbol ist ein
**abgeleiteter Alias** für die Profil-Links. Die bestehenden `/by-symbol/`-Pfade
bleiben als Kompatibilitätsschicht und werden als solche dokumentiert.

Sind absehbar mehrere Anbieter-Aliase nötig, gehören sie in eine eigene Tabelle
statt als Spalten in die Instrumentenzeile.

### `US` ist kein MIC

`EXCHANGES` führt `US` als Sammelcode für NYSE/NASDAQ (OpenFIGI `exchCode=US`).
Das ist **kein** ISO-10383-MIC. Ein Feld namens `exchange_mic`, das mal echte
MICs und mal diesen internen Code enthält, ist falsch benannt und wird beim
ersten Anbieter, der echte MICs erwartet, zum Problem.

**Zu entscheiden:** entweder auf echte MICs abbilden (`XNYS`, `XNAS`) und den
Sammelcode nur intern führen, oder das Feld neutral benennen (`exchange_code`)
und die Kodierung ausdrücklich modellieren. Nicht: beides unter einem Namen.

### Was sich sonst ändert

* `instruments` bekommt `ticker` und `exchange_mic`
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
