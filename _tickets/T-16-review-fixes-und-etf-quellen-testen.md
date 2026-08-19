# T-16 · Review-Fixes und die zweite ETF-Quelle am laufenden System prüfen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | in-review | 45 min | Verifikation am laufenden System, kein Code | — |

**Löst:** Vier Commits (`6ee6bbe`…`809c48a`) haben sechs Review-Befunde behoben
und ETF-Metadaten auf zwei Quellen aufgeteilt. Die Unit-Tests decken die Logik
ab, aber die Hälfte der Befunde lebt an Stellen, die kein Test erreicht: ein
echtes Papier über die HTTP-API anlegen, der Knopf in der Zeile, der Container
mit seiner Konfigurationsdatei. Genau dort saßen die Fehler.

<!--
  Status: in-review — Code ist in master, die Mensch-Spalte fehlt.
  Die AI-Spalte ist bewusst zurückhaltend: Was mit einem gefälschten
  Quote-Provider lief, steht als ◑, nicht als ✅.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `curl` auf ein Krypto-Papier, leere DB (Block unten) | 200 statt 500 — früher `Incorrect number of bindings supplied` | ◑ [^1] | |
| 2 | Assets → US-ETF aufnehmen (`US9229087690`) | Anbieter steht da („Vanguard"), Quelle sagt `yfinance`, TER bleibt leer | ◑ [^2] | |
| 3 | dieselbe Zeile → Detailbereich → TER von Hand eintragen, dann Refresh | der eingetragene Wert bleibt stehen und wird nicht verdeckt | ➖ [^3] | |
| 4 | Assets → kanadisches Papier (`CA46434V6817`, Symbol `XIC.TO`) | Anbieter „BlackRock Asset Management Canada Ltd" | ◑ [^2] | |
| 5 | Assets → europäischer ETF (`IE00B4L5Y983`) | unverändert: TER, Replikation, Domizil da, Quelle `yfinance+justetf` | ◑ [^2] | |
| 6 | Refresh-Knopf an einer **ETF-Zeile ohne ISIN-Spalte**, danach Detailbereich | TER/Anbieter werden tatsächlich aktualisiert statt still zu bleiben | ➖ [^4] | |
| 7 | Ein Papier zweimal abrufen, dazwischen TTL abwarten (oder `CACHE_TTL_HOURS=0`) | Börse und Währung bleiben gleich — kein Sprung von `.DE`/EUR nach `.L`/GBP | ◑ [^5] | |
| 8 | „Alles aktualisieren" in der Kopfzeile drücken | Balken läuft an der **Oberkante der Seite**, über der Kopfzeile — nicht darunter | ◑ [^6] | |
| 9 | `make up` (Container), danach `docker logs stockinfo` | Container startet; **kein** `ValidationError` zu `strict_exchange` | ➖ [^7] | |
| 10 | Ein ETF, dessen Kennzahlen gepflegt sind → warten bis `METADATA_TTL_DAYS` greift | justETF wird erneut gefragt, statt nach dem ersten Kontakt zu verstummen | ➖ [^8] | |
| 11 | `make test` | Backend 244, Dashboard 230, `ruff` sauber | ✅ [^9] | |

```bash
# #1 — Krypto-Papier auf frischer DB: früher 500, jetzt 200
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote/by-symbol/BTC-USD"

# #2 — US-ETF: Anbieter da, Quelle yfinance, ter leer
curl -s "http://localhost:8000/quote/US9229087690" | python3 -m json.tool

# #4 — kanadischer ETF
curl -s "http://localhost:8000/quote/by-symbol/XIC.TO" | python3 -m json.tool

# #5 — europäischer ETF, muss unverändert vollständig sein
curl -s "http://localhost:8000/quote/IE00B4L5Y983" | python3 -m json.tool

# #7 — zweimal hintereinander, Symbol und Währung vergleichen
curl -s "http://localhost:8000/quote/IE00BCRY6557" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['symbol'], d['currency'], d['exchange'])"

# #9 — Container
make build && make up && sleep 3 && docker logs stockinfo 2>&1 | tail -20

# #11 — beide Suiten
make test
```

---

## Details

**Was die vier Commits geändert haben**

| Commit | Inhalt |
|---|---|
| `6ee6bbe` | `make test` neu; pauschales `export` im Makefile entfernt; Hilfe zu `PLATFORM=all` korrigiert |
| `5c094f8` | Fortschrittsbalken an die Seitenoberkante; totes `$header-h` entfernt |
| `5ec9c37` | Fünf Review-Befunde: Insert-Absturz, wandernde Börse im Lesepfad, Metadaten-Zeitstempel, Symbol-Refresh, Gattungswahl im Resolver |
| `809c48a` | `is_responsible` trennt Zuständigkeit vom Ergebnis; `YFinanceEtfEnricher` + `CompositeEtfEnricher`; `EtfDetails.source` |

**Offene Kante, bewusst so gelassen**

Für nicht-europäische ETFs kostet die Anreicherung einen zusätzlichen
Yahoo-Aufruf (`.info`), zusätzlich zu dem, den `YFinanceProvider.fetch_quote`
ohnehin holt. Er läuft nur, wenn `METADATA_TTL_DAYS` abgelaufen ist — also
selten. Vermeidbar wäre er, indem `RawQuote` den `fundFamily` mitbringt; das
vermischt aber Kurs- und Metadatenpfad. Wenn #2 und #4 spürbar träge sind, ist
das der Hebel.

**Nicht abgedeckt**

`is_responsible` entscheidet allein über das ISIN-Präfix. Ein japanisches oder
australisches Papier fällt damit ebenfalls an Yahoo — gewollt, aber gegen echte
Papiere von dort ungetestet.

[^1]: Auf Repository-Ebene reproduziert und gefixt
    (`test_erster_insert_mit_unvollstaendigen_metadaten`); der Fehler war exakt
    `Incorrect number of bindings supplied. The current statement uses 17, and
    there are 8 supplied.` **Nicht** über die laufende HTTP-Route geprüft.
[^2]: Mit der echten Container-Verdrahtung (`_build_etf_enricher`) und echten
    Yahoo-Antworten gemessen: VTI → Vanguard/`yfinance`/ter leer, XIC.TO →
    BlackRock Asset Management Canada Ltd, EUNL.DE → iShares/`yfinance+justetf`/
    ter 0.2. Der Kursteil war dabei gefälscht, die Papiere kamen also nicht über
    die HTTP-API herein.
[^3]: Nur aus `apply_overrides` abgeleitet („füllt nur Lücken"), nicht in der
    Oberfläche durchgespielt. Der Grund, warum TER aus Yahoo bewusst *nicht*
    übernommen wird — ein gelieferter Wert verdeckt einen eingetragenen.
[^4]: Unit-getestet (`test_refresh_per_symbol_reicht_die_gespeicherte_zeile_durch`),
    aber nie am Knopf in der Oberfläche.
[^5]: Mit einem Stub reproduziert, der bei jeder Auflösung eine andere Börse
    liefert (`_WanderndeAufloesung`). Gegen echtes Yahoo nicht nachstellbar, weil
    der Sprung dort nur gelegentlich auftritt.
[^6]: Im Browser gemessen — Balken `y=0..3`, Kopfzeile `y=0..56`, z-index 25
    gegen 10. Die Klasse `active` habe ich dabei von Hand gesetzt; ein echter
    Lauf von „Alles aktualisieren" stand nicht dahinter.
[^7]: Nur der Weg über Make ist geprüft (`make test` läuft jetzt). Der Container
    bekommt seine Konfiguration über `--env-file` und übergibt Werte wörtlich —
    der Trailing-Whitespace, der über Make stolperte, kann dort weiterhin
    zuschlagen. Das ist der eigentliche Grund für diese Zeile.
[^8]: Die TTL lässt sich in der Zeit nicht abkürzen, ohne den Zeitstempel in der
    DB von Hand zu setzen. Logik ist unit-getestet
    (`test_unvollstaendige_antwort_setzt_den_metadaten_zeitstempel_nicht_hoch`).
[^9]: `make test` → 244 passed (Backend) und 230 passed (Dashboard),
    `ruff check app tests` → All checks passed. Working Tree sauber, alles in
    `master`.

---

## Auflösung

_(offen — trägt der Mensch nach)_
