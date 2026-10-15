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
`priority_chain` nach T-102. Nach der Freigabe von T-102 aktiviert
(2026-10-15) auf `t-103-justetf-kennzahlen`, Coder `claude`, Verifier
`codex`. Zuerst Ursache klären, dann Scope-Vertrag, dann Umsetzung. `make check` ist nicht betroffen, weil es die
`integration`-Tests auslässt.

## Befund

| Prüfung | Ergebnis am 2026-10-15 |
|---|---|
| `.venv/bin/pytest -q tests/test_plugin_justetf_integration.py` | 2 failed: `test_ein_bekannter_ucits_fonds_liefert_deklarierte_felder` („justETF kennt diesen Fonds — eine leere Antwort wäre neu“, `readings` ist `None`), `test_ein_betrag_traegt_seine_waehrung` (keine Beträge) |
| Direktaufruf der Bibliothek (siehe Beispiel) | Seite geladen, Kennzahlen `None`, `currency_hedged` falsch |
| Gepinnte Fassung | `requirements.txt`: `justetf-scraping @ git+https://github.com/druzsan/justetf-scraping.git@b52934a…` (Paketversion 0.1.0) |
| Upstream | `git ls-remote` zeigt `HEAD` auf `53cca6a…`; ob diese Fassung den Fehler behebt, ist nicht geprüft |

**Ursache (geklärt 2026-10-15):** `justetf_scraping/etf_profile.py` liest
die Stammdaten aus `soup.find_all("table")[1]`, also aus der zweiten
Tabelle der Seite. justETF liefert die Stammdaten heute in der **ersten**
Tabelle (`data-testid="etf-basics_data_table"`); an zweiter Stelle steht
jetzt „Fund Structure / UCITS compliance / Administrator“. Alle
Zeilenbeschriftungen, die die Bibliothek erwartet („Fund size“, „Total
expense ratio“, „Replication“, „Fund currency“, „Currency risk“,
„Volatility 1 year (in EUR)“, „Distribution policy“, „Fund domicile“,
„Fund Provider“ …), stehen unverändert in dieser ersten Tabelle; für
IE00B4L5Y983 etwa „EUR 133,518 m“, „0.20% p.a.“, „Currency unhedged“,
„10.48%“. `currency_hedged` wird `True`, weil die Bibliothek
`"Currency risk"` fehlt und `"" != "currency unhedged"` gilt.

Die Upstream-Fassung `53cca6a` (in einer eigenen venv im Scratchpad
installiert) hat denselben Fehler; ein Pin-Update hilft nicht. Upstream
`druzsan/justetf-scraping`: letzter Commit 2026-08-01, 16 offene Issues/PRs,
dieser Fehler ist dort nicht gemeldet. Seit wann justETF die Seite so
ausliefert, ist nicht belegt.

**Entscheidung Mike, 2026-10-15:** „Fork + Upstream-PR“. Fork unter
`MikeMitterer/justetf-scraping`, Fix mit Test, PR an `druzsan`; StockInfo
pinnt bis zum Merge auf den Fork-Commit.

## Scope-Vertrag

**Beobachtbares Ergebnis:** Für IE00B4L5Y983 liefert StockInfos
justETF-Plugin wieder TER, Fondsgröße, Anbieter, Replikation, Volatilität,
Domizil, Fondswährung und Ertragsverwendung; die beiden Online-Tests und
`make test` sind grün.

**Fachliche Änderungen (zwei):**

1. Im Fork: Stammdaten aus der Tabelle `etf-basics_data_table` lesen statt
   aus der zweiten Tabelle, mit Test; PR an Upstream.
2. In StockInfo: `requirements.txt` pinnt auf den Fork-Commit, mit
   Kommentar, wann der Pin zurück auf Upstream geht.

**Erwartete Dateien:** Fork: `etf_profile.py` und ein Test (2). StockInfo:
`requirements.txt` (1), Ticket. Keine Doku-Datei: die READMEs nennen die
Bibliothek ohne Quelle oder Version; geprüft im Doku-Abgleich.

**Diff-Budget:** StockInfo unter 20 Zeilen ohne `_tickets/`; Fork unter
100 Zeilen.

**Nicht-Ziele:** keine eigene Auswertung in StockInfo; Klärung von
Verify #4 (Verhalten bei leerer Antwort) nur als Befund, ohne Code, falls
dafür eine neue Entscheidung nötig ist; kein Push von StockInfo.

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

Stand `86d0e15`, Claude, 2026-10-15.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `.venv/bin/pytest -q tests/test_plugin_justetf_integration.py` | beide Tests grün | ✅ alter Pin: 2 failed; neuer Pin (nach `pip install --force-reinstall --no-deps`): 2 passed |
| 2 | Direktaufruf für `IE00B4L5Y983` | TER, Fondsgröße, Anbieter, Replikation, Volatilität gefüllt | ✅ `ter 0.2`, `fund_size_eur 133518.0`, `fund_provider 'iShares'`, `replication 'Physical(Optimized sampling)'`, `volatility_1y 10.48`, `fund_domicile 'Ireland'`, `fund_currency 'USD'`, `distribution_policy 'Accumulating'`, `currency_hedged False` |
| 3 | `make test` | grün | ✅ Exit 0: docs-check ohne Probleme, Backend 1319 passed (inkl. Online-Tests), Plugin-API 324, Beispiel 50, Dashboard 399 |
| 4 | Instrument mit gespeicherten Kennzahlen aktualisieren, während justETF nichts liefert | gespeicherte Werte bleiben erhalten (oder das Ticket nennt das beschlossene Verhalten) | ⚠️ **nicht erfüllt, am Code belegt**: siehe [Scope-Checkpoint](#scope-checkpoint-runde-0--claude-2026-10-15) |

### Akzeptanzkriterien

- [ ] justETF liefert für einen bekannten UCITS-Fonds wieder Kennzahlen.
- [ ] Die justETF-Online-Tests und `make test` sind grün.
- [ ] Das Verhalten bei leerer justETF-Antwort ist geklärt und belegt.

### Abgrenzung

- Andere Quellen (yfinance, OpenFIGI) gehören nicht dazu.
- Kein Wechsel auf eine andere Datenquelle ohne eigene Entscheidung.

## Review-Verlauf (neueste Runde zuerst)

### Scope-Checkpoint Runde 0 · Codex, 2026-10-15

**Entscheidung: `continue` für `86d0e15`.** Die Ergänzung in
`JustEtfProvider.fetch_etf` und der gezielte Unit-Test gehören zu Verify #4:
Eine leere justETF-Antwort darf gespeicherte Kennzahlen nicht löschen. Die
Änderung bleibt in der vorhandenen Provider-Schicht und erweitert weder API
noch Schema oder Abhängigkeiten. Claude kann die Erweiterung umsetzen und
danach die vollständige Prüffassung übergeben.

Im Review sind die Erhaltung gespeicherter Werte bei leerer Antwort, die
Übernahme echter Kennzahlen und die wirksame Installation des neuen Pins in
einer bestehenden Entwicklungsumgebung zu prüfen. Dies ist eine
Umfangsentscheidung, keine technische oder menschliche Abnahme.

### Scope-Checkpoint Runde 0 · Claude, 2026-10-15

**Prüfstand:** `86d0e15`. Kein Code-Review erbeten, nur die Breite.

**Bis hier (im Vertrag):**

- Fork `MikeMitterer/justetf-scraping`, Branch `fix/basic-data-table`,
  Commit `1e804a8` auf Upstream `53cca6a`: Tabelle per
  `data-testid="etf-basics_data_table"` statt `find_all("table")[1]`
  (−3/+2 Zeilen), Test `test_basic_data_from_basics_table` mit dem heutigen
  Seitenaufbau, am alten Code rot (`assert None == 133518.0`), danach 18
  passed. PR [druzsan/justetf-scraping#59](https://github.com/druzsan/justetf-scraping/pull/59).
  Zwischen `b52934a` (alter Pin) und `53cca6a` ändert sich nur `uv.lock`.
- StockInfo `requirements.txt`: Pin auf den Fork-Commit mit Kommentar,
  wann er zurück auf Upstream geht (+5/−1).

**Befund zu Verify #4 (Auslöser):** Während der Störung hat
`JustEtfProvider.fetch_etf` (`app/providers/justetf_provider.py:175–197`)
`EtfDetails` mit Namen, aber ohne Kennzahlen zurückgegeben, weil
`get_etf_overview` ein nicht leeres Dict liefert. `CompositeEtfEnricher`
(`app/providers/composite_etf.py:99–107`) übernimmt jede Antwort, die nicht
`None` ist, und `QuoteService._enrich_etf`
(`app/services/quote_service.py:871–888`) wertet sie als „Quelle hat
geantwortet“ (`True`): TER, Fondsgröße, Anbieter, Replikation, Domizil,
Volatilität und Ertragsverwendung werden mit `None` überschrieben, und der
Stand gilt danach `METADATA_TTL_DAYS` lang als frisch. Der Plugin-Weg
(`app/plugins/justetf_metadata.py:180–184`) gibt in diesem Fall `None` und
schützt den Stand. Eigene Werte aus dem Detailbereich sind getrennt
gespeichert und nicht betroffen. Die Arbeitsdatenbank wurde dafür nicht
geöffnet.

**Geplante Erweiterung:** `JustEtfProvider.fetch_etf` gibt `None` zurück,
wenn die Übersicht keine der Kennzahlen enthält, die StockInfo übernimmt
(nur Name oder gar nichts). Dann gilt „nicht erreichbar“, und der
gespeicherte Stand bleibt, wie der Composite es zusagt. Dazu ein
Unit-Test mit gefälschter Übersicht, der am heutigen Code rot ist.

| Größe | Vertrag | Mit Erweiterung |
|---|---|---|
| Fachliche Änderungen | 2 | 3 |
| Produktdateien StockInfo | 1 (`requirements.txt`) | 2 (+ `app/providers/justetf_provider.py`) |
| Testdateien StockInfo | 0 | 1 |
| Diff StockInfo ohne `_tickets/` | < 20 | ≈ 60 |

Auslöser des Checkpoints: `app/providers/` ist eine im Vertrag nicht
angekündigte Produktschicht.

**Außerdem zu wissen:**

- `make setup` (`pip install -q -r requirements-dev.txt`) übernimmt den
  neuen Pin in einer bestehenden venv nicht, weil die Paketversion bei
  beiden Commits `0.1.0` ist. Mikes venv ist von Hand aktualisiert; das
  Docker-Image installiert neu, weil sich `requirements.txt` ändert. Keine
  Änderung geplant.
- Gespeicherte Kennzahlen, die in der Störung geleert wurden, kommen mit
  der nächsten Metadaten-Aktualisierung nach dem Fix zurück (spätestens
  nach `METADATA_TTL_DAYS`, sofort mit einer Einzelaktualisierung). Auf
  Unraid erst mit einem neuen Image; Build und Push sind nicht Teil dieses
  Tickets.

Erbeten: `continue` (mit Erweiterung), `reduce` (ohne, Verify #4 bleibt
Befund für ein eigenes Ticket) oder `split`.
