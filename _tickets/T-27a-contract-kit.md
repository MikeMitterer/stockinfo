# T-27a · Contract-Kit für alle Rollen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | aktiv · Plugin-MVP 2/4 | ~5 h | öffentliches Testkit — Contracts, Szenarien, Doubles | — |

**Löst:** Heute gibt es `ResolverContract` und `MetadataContract` — zwei von
fünf Rollen. Ein Plugin kann damit die ISIN-Auflösung nachweisen und bliebe für
Kurse, Historie und Devisen trotzdem implizit an yfinance gebunden.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-22 für die vollständige Rollenabdeckung (dort werden
`DailyCloseProvider` und `FxRateProvider` als kanonische Protokolle gebündelt).
**Muss vor Abschluss von T-23 stehen** — T-23 braucht die Doubles als
Abnahmemittel, und die App ist laut T-23 selbst der erste Plugin-Autor.

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** T-22 → **T-27a** →
> T-27b → T-23. Erst nach Codex-Freigabe von T-22 beginnen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Contract-Suite je Rolle | alle fünf vorhanden: Resolver, Metadata, Quote, Daily, FX | ✅ [^suiten] | |
| 2 | Quote-Contract | Preis **mit Pflichtwährung**, endliche Werte, Fehler statt geratener Ersatzwerte | ✅ [^suiten] | |
| 3 | Daily-Contract | Datum, Schlusskurs, Währung, Sortierung, **keine Duplikate**, adjusted/unadjusted deklariert | ✅ [^suiten] | |
| 4 | FX-Contract | Base/Quote, positive endliche Rate, Zeitpunkt, Identitäts- und Fehlerfall | ✅ [^suiten] | |
| 5 | fachliche Invarianten | ISIN-Prüfziffer, Anfrage-ISIN = Ergebnis-ISIN, **echter MIC statt Sammelcode**, gültige Währung, sinnvolle Datumsfolge | ✅ [^invarianten] | |
| 6 | Szenarioformat | ein Fall wird **einmal** beschrieben; Format, Validierung und ein **transportneutraler** Runner-Vertrag stehen. Dass derselbe Fall offline **und** real läuft, nimmt T-27b ab | ✅ [^format] | |
| 7 | Golden Cases | erwarteter Ticker/MIC stammt **nicht** aus der Aufzeichnung, sondern aus gepflegten Daten | ✅ [^golden] | |
| 8 | `FakeSource` | vorgebbare Antwort je Anfrage, Aufrufprotokoll für Reihenfolge und Anzahl | ✅ [^doubles] | |
| 9 | Fake-Uhr | TTL, Half-open und Reset ohne echte Wartezeit prüfbar | ⚠️ [^uhr] | |
| 10 | globaler Zustand | zwei Testfälle beeinflussen sich nicht | ✅ [^zustand] | |
| 11 | `make test-plugin-api` | grün | ✅ [^lauf] | |

[^suiten]: **Fünf Verträge, alle an einem echten Plugin ausgeführt.**
    `ResolverContract` und `MetadataContract` bestanden; neu sind
    `QuoteContract`, `DailyContract` und `FxContract` in
    `plugin_api/src/stockinfo_plugin/testing/contracts.py`.

    Ein Vertrag ohne Nutzer ist ein Skelett — deshalb gibt es
    `examples/prices_file.py` mit drei Quellen über zwei gepflegte Tabellen,
    und `tests/test_prices_file.py` erbt alle drei Verträge. Das ist auch der
    Regelfall: Kommerzielle Anbieter decken Auflösung, Kurs, Historie und
    Devisen aus einer Hand ab.

    Die Zusagen je Rolle stehen als eigene Testmethode da, nicht als Sammelfall
    — sonst nennt eine fehlgeschlagene Zusicherung nur die erste Ursache.
[^invarianten]: **`stockinfo_plugin/invariants.py`, 58 bestandene Tests und ein
    ausdrücklich übersprungener.** Geprüft
    wird gegen **bekannte Werte**, nicht gegen die Funktion selbst: vier echte
    ISINs (Apple, iShares Core MSCI World, Royal Bank of Canada, Barrick Gold).
    Der Erwartungswert kommt aus der Welt, nicht aus der Rechnung — genau das
    Orakel-Problem aus `P-04`.

    **Diese Regeln stehen im öffentlichen Paket, nicht in der App.** Sie sind
    Aussagen über ISO 6166 und ISO 10383; `app/exchanges.py` bezieht sie von
    dort, statt sie ein zweites Mal zu formulieren. Gegenprobe gelaufen:
    `mic_is_wellformed` verstümmelt → **10 Backend-Tests und 5 Plugin-Tests**
    fallen. Es gibt wirklich nur eine Regel.
[^format]: **`Scenario` + `validate_scenarios` + `ScenarioRunner` +
    `DirectRunner`.** Der Runner-Vertrag ist eine einzige Methode und weiß
    nicht, ob die Antwort aus dem Prozess, einer Aufzeichnung oder dem Netz
    kommt. `DirectRunner` ist seine erste Umsetzung — ohne sie wäre der Vertrag
    eine Behauptung; T-27b stellt den HTTP-Runner daneben.

    Die Validierung ist der eigentliche Wert: Ein falsch beschriebener Fall
    läuft sonst grün, **weil** er nichts prüft. `golden={"tikcer": "RY"}` nennt
    ein Feld, das es an `Resolved` nicht gibt, und jede naive Prüfschleife
    übergeht das. Acht Beschreibungsfehler haben eigene Tests, darunter
    vertauschte Bereichsgrenzen (schlagen nie an) und `real_ok` bei erwartetem
    `Unavailable` (ein Ausfall lässt sich von außen nicht bestellen).
[^golden]: **Gemessen, nicht zugesagt.** Die maschinell prüfbare Hälfte:
    `validate_scenarios` verlangt für `Resolved` und `FxRate` die Kernwerte —
    „irgendein Treffer kam zurück" ist keine Aussage über ein Wertpapier.

    Die andere Hälfte — dass die Werte **nicht aus der Aufzeichnung** stammen —
    prüft `test_eine_luegende_aufzeichnung_macht_den_fall_rot`: Die Tabelle wird
    so verfälscht, dass die Royal Bank angeblich in Euro notiert. Käme die
    Erwartung aus der Datei, zöge sie mit und der Fall bliebe grün. Er wird rot.

    Dazu trägt jeder Golden Case eine `note` mit der Herkunft seines Werts, und
    ein Test verlangt sie. In zwei Jahren ist „RY/XTSE" ohne Herkunft nicht mehr
    überprüfbar — wer es dann anzweifelt, hätte nur die Aufzeichnung.
[^doubles]: **`FakeSource` samt fünf rollenscharfen Ableitungen.** Antworten in
    Reihenfolge (die letzte wiederholt sich), `keyed` je Anfrage,
    Aufrufprotokoll mit Reihenfolge und Anzahl, `CallLog` über **mehrere**
    Doubles hinweg. Dazu die drei Fälle, die kein Ergebnistyp abbildet: eine
    geworfene Ausnahme, eine ungültige Antwort (`None`, ein Dict) und eine
    Verzögerung.

    **Fünf schmale Klassen statt einer allwissenden**, weil T-23 Rollen prüfen
    soll: Ein Double, das gleichzeitig `Resolver` und `QuoteSource` ist, käme
    durch eine Rollenprüfung, die einen echten Fehler hätte finden sollen. Das
    Verhalten steht trotzdem nur einmal da.

    `handles` zählt **nicht** als Aufruf — sonst ließe sich „übersprungen" nicht
    von „gefragt" unterscheiden, und genau das ist die Zusage, die geprüft
    werden soll.
[^uhr]: **Die Uhr trägt, ihre Anwendungsfälle noch nicht vollständig.** `FakeClock`
    geht nur, wenn man sie stellt, lässt sich zurückstellen (Zeitumstellung,
    NTP-Sprung sind reale Fälle) und weist einen Startzeitpunkt ohne Zone ab.

    **TTL ist vorgeführt**, nicht behauptet:
    `test_ein_ttl_laeuft_ohne_eine_sekunde_wartezeit_ab` prüft einen Ablauf von
    einer Stunde in null Sekunden Laufzeit, und die Grenze ist exakt statt
    „ungefähr". Der Cache dort ist Testcode und bleibt es — einen TTL zu bauen,
    damit die Zeile grün wird, wäre die Umkehrung der Beweisführung.

    **Half-open und Reset fehlen bewusst.** Ihre Bedeutung legt T-23 fest
    (Schutzschalter); sie hier vorwegzunehmen hieße, einen Entwurf zu erfinden,
    um ihn dann zu prüfen. Die Zeile bleibt deshalb `⚠️`, bis T-23 sie mit
    eigenen Zuständen einlöst.
[^zustand]: **Als Klassenprüfung, nicht als Verhaltenstest.**
    `SourceContract.test_kein_veraenderlicher_zustand_an_der_klasse` zählt
    veränderliche Klassenattribute auf; ein Verhaltenstest müsste raten, welcher
    Aufruf den Zustand verändert. Dazu die Wirkungsseite bei Resolvern:
    dieselbe Frage zweimal, dieselbe Antwort.

    Die Regel hat beim ersten Lauf **einen echten Fund im bestehenden Beispiel**
    gemacht: `MetadataFileSource._COLUMNS` war ein Dict an der Klasse. Behoben
    als `MappingProxyType` — dass dort heute niemand schreibt, ist wahr und
    morgen eine Annahme.
[^lauf]: `make test-plugin-api`: **189 passed, 1 skipped** (vorher 36).
    Übersprungen wird ein Zahlendreher-Fall, dessen getauschte Stellen zufällig
    gleich sind; der Test sagt das statt eine Aussage zu behaupten, die der
    Wert nicht hergibt. `make test` gesamt: Backend 637 / 29 skipped,
    Dashboard 259. `ruff check app plugin_api` sauber.

    **Kein Smoke-Script für dieses Ticket.** Jede Zeile dieser Matrix ist eine
    Aussage über Bibliothekscode; es gibt nichts, das erst nach einem Neustart
    gilt. Ein Script anzulegen, das `pytest` aufruft, wäre eine zweite Fassade
    vor demselben Lauf.

---

## Details

### Fünf Rollen, fünf Contract-Suiten

| Rolle | Verbindliche Prüfungen |
|---|---|
| Resolver | Zuständigkeit, bekannt, unbekannt, Fehler, gültiger Ticker und **echter** MIC |
| Metadata | deklarierte Felder, Typ, Einheit, Währung bei Beträgen, Herkunft, Plausibilität |
| Quote | Preis und **Pflichtwährung**, Zeitpunkte, endliche Werte, Fehler statt Raten |
| Daily | Datum, Schlusskurs, Währung, Sortierung, keine Duplikate, adjusted/unadjusted |
| FX | Base/Quote, positive endliche Rate, Zeitpunkt, Identitäts- und Fehlerfall |

Gemeinsam für alle: stabiler eindeutiger Name, unterstützte `api_version`,
verständliche Diagnose bei fehlender Pflichtkonfiguration, kein Durchreichen
fremder Ausnahmen, nur deklarierte Ergebnisarten, klarer Unterschied zwischen
*nicht zuständig*, *nicht gefunden* und *vorübergehend nicht verfügbar*, und
kein veränderter globaler Zustand zwischen zwei Fällen.

### Fachliche Prüfung geht weiter, als ich angenommen hatte

Ich hatte formuliert, Contract-Tests bewiesen „Form und Fehlerverhalten, nicht
fachliche Richtigkeit". Das war zu pessimistisch. Maschinell prüfbar sind
durchaus: ISIN-Prüfziffer, Übereinstimmung von Anfrage- und Ergebnis-ISIN,
echter MIC statt Sammelcode, gültige Währung, endliche Zahlen, sinnvolle
Datumsreihenfolge, keine doppelten Tagespunkte, Typ- und Einheitenverträglichkeit
sowie die deklarierten Plausibilitätsgrenzen.

**Was bleibt:** Ob der Anbieter bei einem *zukünftigen* Papier das gewünschte
Listing wählt, beweist kein Test. Auch ein formal korrektes `(ticker, mic)` kann
fachlich das falsche Listing sein. Golden Cases erhöhen die Sicherheit
erheblich, ersetzen aber niemanden, der den Markt kennt — und genau so gehört es
in die Plugin-Dokumentation.

### Ein Szenario, zwei Betriebsarten

Ein Autor beschreibt seine Fälle **einmal**: stabile Fall-ID, Anfrage, erwartete
Ergebnisart, bei bekannten Papieren die unabhängig festgelegten Kernwerte,
optionale Plausibilitätsregeln für dynamische Werte, und ob der Fall im
Real-Modus laufen darf.

Derselbe Fall läuft dann als **Replay** (deterministisch, ohne Netz, bei jedem
Commit) und als **Real** (gegen den echten Anbieter, vor einem Release).

**Die Abnahme dieser beiden Betriebsarten liegt bei T-27b**, nicht hier: Der
HTTP-Runner, der sie umsetzt, gehört dorthin — und T-27b hängt an T-27a. Hier
wird nur das gemeinsame Format samt Validierung und ein transportneutraler
Runner-Vertrag abgenommen, damit T-27a fertig sein kann, bevor T-27b darauf
aufbaut.

**Der wichtigste Fallstrick:** Der erwartete Ticker und MIC dürfen **nicht** aus
der Aufzeichnung erzeugt werden. Sonst bestätigt der Test nur, dass ein
möglicherweise falscher Treffer reproduzierbar falsch ist. Golden-Erwartungen
sind kleine, bewusst geprüfte Daten und werden getrennt von den
Anbieter-Aufzeichnungen gepflegt.

### Doubles — Werkzeug hier, Verantwortung beim Host

Das Kit liefert skriptbare Doubles: vorgegebene Antwort je Anfrage,
Aufrufprotokoll für Reihenfolge und Anzahl, alle vier Ergebnisarten plus
Ausnahme und ungültige Antwort, steuerbare Verzögerung, Fake-Uhr.

**Kein** behaupteter Abbruch eines endlos hängenden Aufrufs — siehe T-23.

Die Kettensemantik selbst bleibt beim Host: T-20 prüft die Aggregation bis zum
HTTP-Status, T-23 Reihenfolge, Registry und Schutzschalter, T-26 Merge und
REST-Projektion, T-25 die Profilrotation. So wird das öffentliche Kit nicht mit
StockInfo-Interna beladen.

---

## Auflösung

### Was entstanden ist

| Datei | Zweck |
|---|---|
| `stockinfo_plugin/invariants.py` | Was sich maschinell prüfen lässt — ISIN-Prüfziffer, MIC, Währung, endliche Zahlen, Datumsfolge |
| `stockinfo_plugin/types.py` | `QuoteRequest`/`Quote`, `DailyRequest`/`DailyBar`/`DailySeries`, `FxRequest`/`FxRate` |
| `stockinfo_plugin/sources.py` | `QuoteSource`, `DailyCloseSource`, `FxSource` — die Kommentar-Platzhalter sind eingelöst |
| `stockinfo_plugin/testing/` | aus einer Datei ein Paket: `contracts`, `scenarios`, `doubles` |
| `examples/prices_file.py` | drei Quellen über zwei gepflegte Tabellen — die Nutzer der drei neuen Verträge |
| `app/exchanges.py` | bezieht ISIN- und MIC-Form jetzt aus dem Vertrag, statt sie zu wiederholen |

`testing.py` wurde zum Paket, weil daraus sonst rund achthundert Zeilen in
einer Datei geworden wären, die drei verschiedene Fragen beantwortet. Der
Importweg bleibt `from stockinfo_plugin.testing import …`.

### Drei Entscheidungen, die Erklärung brauchen

**Die Invarianten stehen im öffentlichen Paket, nicht in der App.** Das war die
Stelle, an der ich in T-22 Runde 1 gescheitert bin: Ich hatte zwei Verträge neu
geschrieben, die es längst gab. Hier lag derselbe Fall umgekehrt vor — die App
kannte `is_real_mic` und `ISIN_PATTERN`, das Kit hätte sie gebraucht. Die
Aussage „vier Zeichen, Großbuchstaben oder Ziffern" gehört zu ISO 10383 und
nicht zu StockInfo; ein Plugin-Autor in Toronto muss sie anwenden können, ohne
diese App zu installieren.

Geteilt wurde nach Wissen: Die **Form** liegt im Vertrag, die **Liste der
Sammelcodes** in der App — welche es gibt, hängt daran, welche Quellen jemand
einsetzt. `app.exchanges.is_real_mic` ist die Stelle, an der beides
zusammenkommt.

**`expect` ist eine Klasse, keine Zeichenkette.** `expect=NotFound` statt
`expect="not_found"`: Ein Katalog von Kennungen müsste gepflegt werden und
liefe gegen die Typen aus, und ein Tippfehler wäre ein stiller Nichtvergleich
statt eines `NameError`.

**Fünf schmale Doubles statt eines allwissenden.** Ein Double, das gleichzeitig
`Resolver` und `QuoteSource` ist, käme durch die Rollenprüfung, die T-23 haben
soll — und deckte damit genau den Fehler, den sie finden müsste.

### Was die neuen Regeln gefunden haben

Beides im **bestehenden** Code, beides beim ersten Lauf:

1. **`CA00000000000` war keine ISIN.** Dreizehn Zeichen, falsche Prüfziffer —
   und stand seit T-24 als „unbekanntes Papier" in der Beispielsuite. Der Test
   maß damit die Formprüfung des Plugins statt seines Verhaltens bei einem
   echten, aber nicht geführten Papier. Zwei verschiedene Fälle, und nur der
   zweite war gemeint. Ersetzt durch `CA0679011084` (Barrick Gold).
2. **`MetadataFileSource._COLUMNS` war ein Dict an der Klasse** — allen
   Instanzen gemeinsam. Heute schreibt dort niemand; das ist wahr und morgen
   eine Annahme. Jetzt `MappingProxyType`.

Beide hat kein Mensch gefunden, sondern eine neue Vertragsregel. Das ist der
Beleg dafür, dass die Regeln arbeiten und nicht nur dastehen.

### Ein eigener Regelverstoß, im selben Gang mitgezogen

Beim Gegenlesen fiel mir auf, dass ich **deutsche lokale Variablen** geschrieben
hatte — `antwort`, `treffer`, `probleme`. CLAUDE.md lässt das ausnahmslos nicht
zu, und die Altlast in den bestehenden Beispielen zog nach derselben Regel mit
(„was ohnehin angefasst wird, zieht mit").

Der erste Anlauf per Regex hat prompt Prosa beschädigt: aus „niemand sonst je
**gesehen** hat" wurde „je **seen** hat". Genau davor warnt meine eigene Notiz.
Der zweite Anlauf lief über `tokenize` und fasste nur `NAME`-Token an — dabei
zeigte sich die Grenze des Werkzeugs: Unter Python 3.11 ist ein f-String **ein**
Token, seine Interpolationen blieben stehen und wären zur Laufzeit `NameError`
gewesen. Gefunden hat sie ein `ast`-Lauf über `JoinedStr`; der
positionsbasierte Umbau scheiterte danach an einer Zusicherung, weil die
Spaltenangaben in f-Strings unter 3.11 nicht verlässlich sind — also von Hand,
mit der vollen Zeile als Anker.

**Gegenprobe:** ein `ast`-Inventar über alle `Name`, `arg`, `FunctionDef` und
`ClassDef` des Pakets — 382 Bezeichner, keiner mehr deutsch. Testnamen und
Docstrings sind unverändert deutsch; sie sind laut CLAUDE.md die Sprache der
Erklärung.

### Was T-27b übernimmt

Der HTTP-Runner samt Aufzeichnung und Realbetrieb. Das Format steht, der
Runner-Vertrag ist eine Methode, und `run_scenarios(..., only_real=True)`
wählt bereits die freigegebenen Fälle aus. Es soll dort **keine** Zeile an einem
Szenario geändert werden müssen — das ist die Zusage, an der T-27b dieses
Ticket messen kann.

---

## Codex-Review · Runde 1 · `6121a94`

Die Grundarchitektur, die Paketierung und die zentrale MIC-/ISIN-Regel tragen.
Vier Befunde verhindern die Freigabe:

1. **Hoch · Contract-Suiten bestehen mit kaputten oder leeren Treffern.** Ein
   Metadaten-Mutant bestand mit einem String im Zahlenfeld, `Unit.ABSOLUTE`
   ohne Währung und ohne Plausibilitätsprüfung; `None` für den verantwortlichen
   bekannten Fall besteht ebenfalls. Daily besteht mit einer leeren Reihe, die
   alle Wertprüfungen als leere Schleifen umgeht. FX akzeptiert im
   Identitätsfall auf CAD→CAD das Paar USD/JPY, solange `rate == 1.0` ist.
2. **Hoch · Szenarien können inkohärent oder ohne Orakel grün werden.** Ein
   `QuoteRequest` mit `expect=Resolved` bestand gegen eine `FakeQuoteSource`;
   Quote/Daily brauchen keine Golden- oder Plausibilitätsaussage, eine leere
   Herkunfts-`note` wird akzeptiert, und ein Real-Lauf mit null ausgewählten
   Fällen meldet Erfolg.
3. **Mittel · Die Invarianten überzeichnen semantische Gültigkeit.** `ZZZ`
   gilt als ISO-4217-Währung; ein `tzinfo` mit `utcoffset() is None` gilt als
   Zeitzone. Beides prüft nur einen oberflächlichen Marker, nicht die behauptete
   Semantik.
4. **Mittel · Die versprochene Konfigurationsdiagnose fehlt.** Öffentlicher
   Vertrag und Test kennen weiterhin nur `is_configured() -> bool`, obwohl
   Ticket und Spec einen verständlichen Grund verlangen. Daneben behauptet der
   Kosten-Test entgegen T-22, die Kette sortiere nach `cost`.

Zusätzlich übernimmt `PricesFileDailySource` bei gemischten Währungen
stillschweigend die erste Zeile für die ganze Reihe; dafür braucht das Beispiel
einen eigenen Negativtest.

**Evidenz:** Die gezielten Gegenplugins und -szenarien liefen alle unerwartet grün.
Regulär: Backend 637 passed / 29 skipped, Plugin-API 189 passed / 1 skipped,
Dashboard 259; Ruff und `git diff --check` sauber. Das Wheel
`stockinfo_plugin_api-0.2.0-py3-none-any.whl` enthält alle neuen öffentlichen
Module. Die grünen Läufe bestätigen Paketierung und Bestand, nicht die
Vollständigkeit der Contract-Orakel.
