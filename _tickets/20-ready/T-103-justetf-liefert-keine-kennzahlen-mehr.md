# T-103 · justETF liefert keine Kennzahlen mehr

**Warum dieses Ticket:** Die Online-Tests in
`tests/test_plugin_justetf_integration.py` sind rot, und der Grund betrifft
die laufende App, nicht nur die Tests. Die Bibliothek `justetf-scraping`
erreicht justETF noch, liest aber bis auf den Namen keine Kennzahl mehr aus.
StockInfo bekommt für europäische ETFs damit weder TER noch Fondsgröße,
Anbieter, Replikation, Volatilität, Domizil, Fondswährung oder
Ertragsverwendung.

**Beispiel:** `justetf_scraping.get_etf_overview("IE00B4L5Y983",
include_gettex=False)` liefert am 2026-10-15 `name` „iShares Core MSCI World
UCITS ETF USD (Acc)“, Bestände, Länder und Sektoren, aber `ter`,
`fund_size_eur`, `fund_provider`, `replication`, `volatility_1y`,
`fund_domicile`, `fund_currency` und `distribution_policy` als `None`.
`currency_hedged` steht auf `True`, obwohl der Fonds nicht währungsgesichert
ist. `JustEtfProvider.fetch_etf` baut daraus `EtfDetails` ohne Kennzahlen,
`as_readings` liefert nichts, und das Plugin meldet `None`: „justETF kennt
das Papier nicht“.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 in `10-backlog/` angelegt,
gefunden beim Gesamtlauf von `make test` in T-102. Auf Mikes Auftrag
(„Nimm T-103 in die Kette nach T-102“) in `20-ready/` und in
`priority_chain` nach T-102. Nicht aktiviert, keine Umsetzung; Start nach
der technischen Freigabe von T-102. `make check` ist nicht betroffen, weil es die
`integration`-Tests auslässt.

## Befund

| Prüfung | Ergebnis am 2026-10-15 |
|---|---|
| `.venv/bin/pytest -q tests/test_plugin_justetf_integration.py` | 2 failed: `test_ein_bekannter_ucits_fonds_liefert_deklarierte_felder` („justETF kennt diesen Fonds — eine leere Antwort wäre neu“, `readings` ist `None`), `test_ein_betrag_traegt_seine_waehrung` (keine Beträge) |
| Direktaufruf der Bibliothek (siehe Beispiel) | Seite geladen, Kennzahlen `None`, `currency_hedged` falsch |
| Gepinnte Fassung | `requirements.txt`: `justetf-scraping @ git+https://github.com/druzsan/justetf-scraping.git@b52934a…` (Paketversion 0.1.0) |
| Upstream | `git ls-remote` zeigt `HEAD` auf `53cca6a…`; ob diese Fassung den Fehler behebt, ist nicht geprüft |

Wahrscheinliche Ursache: justETF hat den Aufbau der Profilseite geändert,
und die gepinnte Fassung der Bibliothek findet die Felder nicht mehr. Nicht
belegt ist, seit wann.

**Folgen im Betrieb:** Bei jeder Metadaten-Aktualisierung (alle
`METADATA_TTL_DAYS` und bei manueller Aktualisierung) kommt von justETF
nichts. Zu klären ist, ob bereits gespeicherte Werte dabei erhalten bleiben
oder überschrieben werden, und wie der Cache „justETF kennt das Papier
nicht“ behandelt.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | offen | Ursache klären, Bibliothek aktualisieren oder Abruf anpassen | — |

1. Prüfen, ob Upstream `53cca6a` die Felder wieder liest; wenn ja, Pin in
   `requirements.txt` anheben.
2. Wenn nicht: Fehler upstream melden und entscheiden, ob StockInfo den
   Abruf selbst anpasst oder justETF bis zur Korrektur ohne Kennzahlen läuft.
3. Klären, was mit gespeicherten Kennzahlen passiert, solange justETF nichts
   liefert, und ob „nichts gelesen“ von „Papier unbekannt“ unterschieden
   werden muss (`fetch` gibt in beiden Fällen `None`).
4. `currency_hedged` prüfen: Wird der falsche Wert irgendwo übernommen?

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `.venv/bin/pytest -q tests/test_plugin_justetf_integration.py` | beide Tests grün | ➖ |
| 2 | Direktaufruf für `IE00B4L5Y983` | TER, Fondsgröße, Anbieter, Replikation, Volatilität gefüllt | ➖ |
| 3 | `make test` | grün | ➖ |
| 4 | Instrument mit gespeicherten Kennzahlen aktualisieren, während justETF nichts liefert | gespeicherte Werte bleiben erhalten (oder das Ticket nennt das beschlossene Verhalten) | ➖ |

### Akzeptanzkriterien

- [ ] justETF liefert für einen bekannten UCITS-Fonds wieder Kennzahlen.
- [ ] Die justETF-Online-Tests und `make test` sind grün.
- [ ] Das Verhalten bei leerer justETF-Antwort ist geklärt und belegt.

### Abgrenzung

- Andere Quellen (yfinance, OpenFIGI) gehören nicht dazu.
- Kein Wechsel auf eine andere Datenquelle ohne eigene Entscheidung.
