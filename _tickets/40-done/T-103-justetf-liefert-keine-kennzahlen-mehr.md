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
`codex`. Von Codex in Runde 1 freigegeben (`07f5684`), nach `master`
gemergt (`8668849`). Am 2026-10-15 von Mike abgenommen („T-103 und T-104
sind somit abgenommen“) und nach `40-done/` verschoben. Offen außerhalb des
Tickets: Rückkehr des Pins auf Upstream nach Merge von
druzsan/justetf-scraping#59 und ein neues Image für Unraid.

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

Stand `558add9`, Claude, 2026-10-15 (Runde 1).

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `.venv/bin/pytest -q tests/test_plugin_justetf_integration.py` | beide Tests grün | ✅ alter Pin: 2 failed; neuer Pin (nach `pip install --force-reinstall --no-deps`): 2 passed |
| 2 | Direktaufruf für `IE00B4L5Y983` | TER, Fondsgröße, Anbieter, Replikation, Volatilität gefüllt | ✅ `ter 0.2`, `fund_size_eur 133518.0`, `fund_provider 'iShares'`, `replication 'Physical(Optimized sampling)'`, `volatility_1y 10.48`, `fund_domicile 'Ireland'`, `fund_currency 'USD'`, `distribution_policy 'Accumulating'`, `currency_hedged False` |
| 3 | `make test` | grün | ✅ Exit 0 auf `558add9`: docs-check ohne Probleme, Backend 1321 passed (inkl. Online-Tests), Plugin-API 324, Beispiel 50, Dashboard 399. `make check` Exit 0, Ruff grün |
| 4 | Instrument mit gespeicherten Kennzahlen aktualisieren, während justETF nichts liefert | gespeicherte Werte bleiben erhalten (oder das Ticket nennt das beschlossene Verhalten) | ✅ `tests/test_quote_cache.py::test_justetf_ohne_kennzahlen_leert_den_gespeicherten_stand_nicht`: echte Kette (`wire_real_chain` mit echtem `JustEtfProvider`, ersetzt nur `get_etf_overview`), `refresh_one` → `ter 0.2` in Antwort und Datenbank, `provider 'Vanguard'`. Am alten Provider rot (`assert None == 0.2`, `metadata_complete=True`) |
| 5 | Neuer Pin in einer bestehenden venv (Prüfpunkt aus dem Scope-Checkpoint) | `make setup` installiert ihn | ✅ alter Pin von Hand in `.venv` installiert, `make setup` Exit 0, danach `freeze` = Fork-Commit, Online-Tests 2 passed; zweiter Vergleich „aktuell“, keine Neuinstallation. Vorher: `pip install -r` und `pip install --upgrade -r` behielten beide den alten Commit (Scratch-venv) |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] justETF liefert für einen bekannten UCITS-Fonds wieder Kennzahlen.
- [x] Die justETF-Online-Tests und `make test` sind grün.
- [x] Das Verhalten bei leerer justETF-Antwort ist geklärt und belegt.

### Abgrenzung

- Andere Quellen (yfinance, OpenFIGI) gehören nicht dazu.
- Kein Wechsel auf eine andere Datenquelle ohne eigene Entscheidung.

## Review-Verlauf (neueste Runde zuerst)

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: `approved` für `558add9`.** Der Fork-Commit
[`1e804a8`](https://github.com/MikeMitterer/justetf-scraping/commit/1e804a89ecc37df4d4cf63f507695a7dcc28aa28)
ist der Kopf von [Upstream-PR #59](https://github.com/druzsan/justetf-scraping/pull/59).
Der PR ändert den Parser auf `data-testid="etf-basics_data_table"` und
enthält einen Test für die versetzte Tabelle. StockInfo pinnt exakt diesen
Commit. Der installierte Stand aus `pip freeze` stimmt mit dem Pin überein.

| Verify | Unabhängiger Befund |
|---|---|
| #1 | Beide justETF-Online-Tests mit Netzwerkzugriff grün (2 passed). Ein erster Lauf in der Sandbox scheiterte an DNS, bevor justETF antworten konnte. |
| #2 | Der Fork-Test prüft TER, Fondsgröße, Anbieter, Replikation, Volatilität, Domizil, Fondswährung, Ertragsverwendung und `currency_hedged=False`; die Online-Tests bestätigen gelieferte deklarierte Felder und einen Betrag mit Währung. Die konkreten Live-Zahlen aus Claudes Direktaufruf habe ich nicht erneut gemessen. |
| #3 | `make test` unabhängig mit Exit 0. `git diff --check` ohne Befund; nach `558add9` wurden nur Ticket und STATUS geändert. |
| #4 | Provider-Test mit leerer Übersicht und Refresh-Test über `CachedQuoteService` → `QuoteService` → `JustEtfProvider` grün. Der Refresh-Test liest TER und Anbieter nachher aus Antwort und temporärer Datenbank. Die Quelle und Kurs-/Resolver-Grenzen sind ersetzt; der Composite wird darin nicht verdrahtet. Für europäische ISINs ist die Yahoo-ETF-Quelle laut `is_responsible` unzuständig. |
| #5 | `make setup` vergleicht Git-Pins aus `requirements.txt` mit `pip freeze` und installiert einen abweichenden Pin gezielt neu. Den von Claude belegten Wechsel alt → neu habe ich nicht nochmals in Mikes `.venv` vorgenommen; Pin, Vergleichszeile und aktueller Installationsstand sind unabhängig geprüft. |

**Scope:** Die zusätzlichen sieben Makefile-Zeilen sichern mechanisch, dass
der beschlossene Fork-Pin in der bestehenden Entwicklungsumgebung tatsächlich
wirkt. Ich werte sie als die im Workflow erlaubte eindeutige Restanpassung
nach der einmaligen Umfangserweiterung im Checkpoint. Die zusätzlichen
Testdateien belegen den bereits vereinbarten Datenverlustfall über den
öffentlichen Refresh-Einstieg und nutzen die vorhandene Verdrahtung. Es
entsteht kein unabhängiges Produktergebnis. Der Coder hätte die Überschreitung
vor dem Edit melden müssen; diese Prozessabweichung ist hier festgehalten.

**Code-Standards:** Gelesen:
`/Users/macminipro/.codex/skills/code-standards/SKILL.md`,
`references/architecture.md`, `references/python.md`, `references/quality.md`
und `makefile-conventions/SKILL.md`. Die berührten Python-Dateien wurden per
AST nach `Name`, Argumenten, Funktions- und Klassennamen inventarisiert;
die neuen Bezeichner sind englisch. Ergebnis je Gruppe:

| Gruppe | Ergebnis |
|---|---|
| Projektstruktur | ➖ keine Strukturänderung |
| Architektur, DRY, Namen | ✅ Schutzregel einmal im Provider; die Feldmenge leitet sich aus `EtfDetails` ab; Testverdrahtung nutzt `wire_real_chain` |
| Shell/Makefile | ✅ `PIN` groß, `read -r`, Pin zitiert; Git-Pins werden aus `requirements.txt` gelesen |
| Python | ✅ Typen, abgefangener Quellfehler und `structlog`-Kennung vorhanden |
| Qualität | ✅ Provider- und Refresh-Test treffen den leeren Antwortfall; Online- und Gesamtlauf grün |
| Persistenz | ➖ kein Produkt-Datenbankcode geändert; temporäre Testdatenbank durch `tmp_path` |
| Frontend, CLI | ➖ nicht berührt |

**DRY-Prüfguard:** `get_etf_overview`, Kennzahlenschutz, Git-Pin-Vergleich
und `wire_real_chain` im Projekt einschließlich `.libs/ProjectTools` gesucht.
Keine zweite Implementierung der neuen Schutzregel oder zweite Pin-Liste
gefunden. Die zwei Tests haben unterschiedliche Orakel (Provider-Antwort und
gespeicherter Refresh-Stand).

**Doku-Abgleich:** `README.md`, `README.de.md`, `docker/README.md` und
`unraid/README.md` geprüft. Sie nennen die Bibliothek ohne Herkunft oder
Commit und beschreiben `make setup` weiterhin zutreffend als Einrichtung
der Entwicklungsumgebung. Für das aktuelle Verhalten ist dort keine
Anpassung nötig. Der Fork-Pin und die Rückkehrbedingung stehen in
`requirements.txt`; Betrieb mit neuem Image und Rückkehr nach Upstream-Merge
bleiben gesonderte Schritte. Keine menschliche Abnahme und kein Push.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `558add9` auf `t-103-justetf-kennzahlen`. Produkt-Commits
`86d0e15` (Pin) und `558add9` (Schutz, Tests, `make setup`). Fork-Commit
`1e804a8` mit PR druzsan/justetf-scraping#59.

**Umfang geplant / tatsächlich:**

| Größe | Vertrag + Checkpoint | Tatsächlich | Abweichung |
|---|---|---|---|
| Fachliche Änderungen | 3 | 4 | `make setup` übernimmt geänderte Git-Pins; Codex' Prüfpunkt „wirksame Installation in bestehender Umgebung“ verlangt es, im Checkpoint stand „keine Änderung geplant“ |
| Produktdateien StockInfo | 2 | 3 (`requirements.txt`, `app/providers/justetf_provider.py`, `Makefile`) | `Makefile` wie oben |
| Testdateien StockInfo | 1 | 3 (`tests/test_providers.py`, `tests/test_quote_cache.py`, `tests/boundaries.py`) | Akzeptanztest über die echte Kette statt nur Provider-Test; `wire_real_chain` nimmt dafür optional eine ETF-Quelle, statt die Verdrahtung ein zweites Mal zu bauen |
| Diff StockInfo ohne `_tickets/` | ≈ 60 | 112 (+106/−6) | Makefile 7, Akzeptanztest 30, Kommentare |

**Akzeptanzfälle (rot → grün):**

| Fall | Test | Rot am alten Stand |
|---|---|---|
| Übersicht nur mit Name ist keine Antwort | `test_providers.py::test_justetf_ohne_kennzahlen_gilt_als_keine_antwort` | `assert EtfDetails(… name='iShares …', ter=None …) is None` |
| Refresh hält TER und Anbieter in Antwort und DB | `test_quote_cache.py::test_justetf_ohne_kennzahlen_leert_den_gespeicherten_stand_nicht` | `assert None == 0.2`, Antwort mit `metadata_complete=True` |
| Fork: Stammdaten aus der Basistabelle | `test_etf_profile.py::test_basic_data_from_basics_table` (Fork) | `assert None == 133518.0` |

**Negative Mutanten** (einzeln, Datei danach per `diff` als wiederhergestellt
geprüft):

| Mutant | Ergebnis |
|---|---|
| `name` zählt als Kennzahl | beide neuen Tests rot |
| Prüfung `_has_metrics` ausgeschaltet | beide neuen Tests rot |
| keine Kennzahl zählt | 10 bestehende Provider-Tests rot |

Ein erster Mutantenlauf war ungültig: `cp` ist hier auf `cp -i` gesetzt, die
Wiederherstellung griff nicht, die Mutanten stapelten sich. Die Datei wurde
aus der Sicherung wiederhergestellt und gegengeprüft; die Tabelle oben
stammt aus dem Wiederholungslauf mit `command cp -f`.

**Angepasster Bestandstest:** `test_unbekannte_ausschuettungspolitik_bleibt_unbekannt`
fütterte eine Übersicht nur mit `distribution_policy` — nach der neuen Regel
keine Antwort. Die Übersicht trägt jetzt zusätzlich `ter: 0.2`; die
Zusicherung (`accumulating is None`) ist unverändert.

**Code-Standards** (gelesen: `~/.claude/skills/code-standards/SKILL.md`,
`references/python.md`, `references/quality.md`, `references/shell.md`):

| Referenz | Ergebnis |
|---|---|
| Projektstruktur | ➖ nicht berührt |
| Architektur (DRY, Namen) | ✅ neue Bezeichner englisch (`_NOT_METRICS`, `_has_metrics`, `details`, `etf_source`, `PIN`); Kennzahlen aus `fields(EtfDetails)` abgeleitet statt als zweite Liste; Kettenverdrahtung über `wire_real_chain`, Fakes aus `tests/test_quote_service.py` importiert |
| Shell (Makefile-Rezept) | ✅ Variable groß (`PIN`), `read -r`, Pin in Anführungszeichen |
| Python | ✅ Typen, Docstrings, Logmeldung `justetf_no_metrics` als stabile Kennung |
| Qualität (Tests) | ✅ Akzeptanztest am öffentlichen Eintritt `refresh_one`, rot/grün und Mutanten oben |
| Persistenz | ➖ nicht berührt (vorhandener Schutz über `metadata_complete`) |
| Frontend, CLI | ➖ nicht berührt |

**DRY:** Die Schutzregel steht einmal in `JustEtfProvider`; der Composite
und `_enrich_etf` behandeln `None` wie bisher. Der Plugin-Weg
(`justetf_metadata.py`) hatte den Schutz schon über `as_readings(...) or
None` und bleibt unverändert. Die Pin-Prüfung in `make setup` liest die
Pins aus `requirements.txt`, keine zweite Liste.

**Doku-Abgleich:** `README.md`, `README.de.md`, `docker/README.md`,
`unraid/README.md` nennen `justetf-scraping` nur als Bibliothek ohne Quelle
oder Version und beschreiben `make setup` als Einrichtung der venv; beides
bleibt richtig, keine Änderung. Das Verhalten bei leerer Quellenantwort
steht in keiner Anleitung. `requirements.txt` erklärt den Fork-Pin.

**Offen außerhalb:** Rückkehr auf Upstream nach Merge von #59; neues
Docker-Image für Unraid (eigener Auftrag).

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
