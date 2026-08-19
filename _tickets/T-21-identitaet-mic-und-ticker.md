# T-21 · Identität auf MIC + Ticker umstellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | Schema-Migration, Symbolerzeugung | — |

**Löst:** Der Identifikator eines Papiers ist heute das **Yahoo-Symbol**
(`EUNL.DE`) — in der Datenbank, in der API, im Dashboard. Damit ist yfinance
nicht ersetzbar, sondern nur ergänzbar. Jede zweite Kursquelle müsste Yahoos
Suffix-Schreibweise nachbilden.

**Der Brocken der Serie.** Alles andere ist klein dagegen.

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

### Was sich ändert

* `instruments` bekommt `ticker` und `exchange_mic`; `symbol` **bleibt** als
  Yahoo-Symbol erhalten, ist aber nicht mehr der Identifikator (die Profil-Links
  `yahoo_url` und `extraetf_*_url` brauchen es weiter)
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

---

## Auflösung

_(offen)_
