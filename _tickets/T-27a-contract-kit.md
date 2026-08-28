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
| 1 | Contract-Suite je Rolle | alle fünf vorhanden: Resolver, Metadata, Quote, Daily, FX | ✅ [^suiten] [^mutanten] | |
| 2 | Quote-Contract | Preis **mit Pflichtwährung**, endliche Werte, Fehler statt geratener Ersatzwerte | ✅ [^suiten] [^mutanten] | |
| 3 | Daily-Contract | Datum, Schlusskurs, Währung, Sortierung, **keine Duplikate**, adjusted/unadjusted deklariert | ✅ [^suiten] [^mutanten] | |
| 4 | FX-Contract | Base/Quote, positive endliche Rate, Zeitpunkt, Identitäts- und Fehlerfall | ✅ [^suiten] [^mutanten] | |
| 5 | fachliche Invarianten | ISIN-Prüfziffer, Anfrage-ISIN = Ergebnis-ISIN, **echter MIC statt Sammelcode**, gültige Währung, sinnvolle Datumsfolge | ✅ [^invarianten] [^mutanten] | |
| 6 | Szenarioformat | ein Fall wird **einmal** beschrieben; Format, Validierung und ein **transportneutraler** Runner-Vertrag stehen. Dass derselbe Fall offline **und** real läuft, nimmt T-27b ab | ✅ [^format] | |
| 6b | Rollenpassung und Nullfall | Anfrage- und Ergebnistyp müssen zusammenpassen — **auch wenn ein Fehlfall erwartet wird**; ein Lauf **ohne einen einzigen Fall** ist eine Beanstandung | ✅ [^nullfall] | |
| 6c | Beschreibungsfehler beenden den Lauf nicht | eine kaputte Fallbeschreibung kommt als Befund zurück, statt die übrigen Fälle mitzureißen | ✅ [^format] | |
| 7 | Golden Cases | erwarteter Ticker/MIC stammt **nicht** aus der Aufzeichnung, sondern aus gepflegten Daten | ✅ [^golden] | |
| 8 | `FakeSource` | vorgebbare Antwort je Anfrage, Aufrufprotokoll für Reihenfolge und Anzahl | ✅ [^doubles] | |
| 9 | Fake-Uhr | TTL, Half-open und Reset ohne echte Wartezeit prüfbar | ⚠️ [^uhr] | |
| 10 | globaler Zustand | zwei Testfälle beeinflussen sich nicht | ✅ [^zustand] | |
| 11 | `make test-plugin-api` | grün | ✅ [^lauf] | |

[^mutanten]: **`tests/test_contract_mutants.py` — 23 kaputte Mini-Plugins, je
    eines pro Regel, dauerhaft im Lauf.** Das ist die Antwort auf den
    schwersten Befund aus Runde 1: Die Verträge zertifizierten leere und
    kaputte Quellen, weil ihre Schleifen null Mal liefen. Ein Vertrag, dessen
    Greifen niemand nachweist, ist eine Zusage über eine Zusage.

    Jeder Mutant macht genau **einen** Fehler, und geprüft wird nicht nur, dass
    irgendetwas fehlschlägt, sondern dass die Meldung von der **gemeinten**
    Regel kommt — sonst bestünde ein Tippfehler im Vertrag den Test genauso.

    Die Gegenprobe zur Gegenprobe steht am Ende der Datei:
    `test_ein_heiles_plugin_wird_nicht_beanstandet`. Ohne sie bewiese die ganze
    Datei nur, dass die Verträge streng sind — ein Vertrag, der *alles*
    ablehnt, bestünde jeden Mutantentest und wäre wertlos.
[^nullfall]: **Beides waren Löcher, durch die T-27b sonst geerbt hätte.**

    `QuoteRequest` mit `expect=Resolved` lief vorher grün — ein Double gibt
    bereitwillig zurück, was man ihm sagt, und niemand fragte, ob das zur Rolle
    passt. `ROLE_RESULTS` beantwortet die Frage jetzt; Fehlfälle bleiben frei,
    weil `NotFound` in jeder Rolle dasselbe heißt.

    Der Nullfall ist dasselbe Muster wie `P-05`: `only_real=True` ohne einen
    einzigen freigegebenen Fall gab `[]` zurück, und das sah aus wie Erfolg.
    Vergisst ein Autor überall `real_ok`, meldet sein Release-Lauf jahrelang
    Erfolg, ohne den echten Anbieter je gefragt zu haben. **Der Test, der das
    vorher behauptete, war meiner** — er stand als
    `test_die_reale_betriebsart_waehlt_nur_freigegebene_faelle` da und
    zertifizierte die Lücke. Er ist jetzt umgekehrt und hat einen zweiten
    daneben, der die Auswahl mit einem *tatsächlich* freigegebenen Fall belegt.

    **Runde 3 — die Rollenprüfung hatte dieselbe Lücke eine Ebene tiefer.** Sie
    stieg bei Fehlfällen aus, *bevor* sie den Anfragetyp ansah. Ein Fall mit
    einem unbekannten Request und `expect=Unavailable` kam deshalb zweimal
    durch: Die Beschreibung wurde nicht beanstandet, und `DirectRunner`
    **erfindet** für einen unbekannten Anfragetyp genau das `Unavailable`, das
    der Fall erwartet — die Quelle wurde nie gefragt, der Prüfstand hat sich
    selbst bestätigt. Jetzt wird der Anfragetyp immer geprüft, die Trefferart
    nur dort, wo es eine gibt.
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
[^invarianten]: **`stockinfo_plugin/invariants.py`, 82 bestandene Tests und ein
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

    **Runde 3 — eine kopierte Liste veraltet, und zwar still.** `ISO_4217`
    behauptete den Stand `2026-08` und enthielt `BGN`, obwohl Bulgarien zum
    1. Januar 2026 den Euro eingeführt hat. Der Abgleich gegen die offizielle
    List One (`Pblshd="2026-01-01"`) hat zwei weitere Abweichungen derselben
    Art gezeigt, die im Review nicht standen: `ANG` war seit dem 30. Juni 2025
    zurückgezogen, `XAD` fehlte, obwohl vergeben. Liste und Quelle sind jetzt
    deckungsgleich (176 Codes = 178 vergebene minus `XXX`/`XTS`),
    `ISO_4217_AS_OF` trägt das `Pblshd`-Datum der Quelle statt eines
    selbstgesetzten Monats, und
    `test_der_gemeldete_stand_und_die_liste_gehoeren_zusammen` verknüpft beide
    Angaben, damit sie nicht wieder getrennt gepflegt werden.
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

    **Runde 3 — die Validierung durfte den Lauf nicht abbrechen, tat es aber.**
    `plausible={"price": ("a", "z")}` galt als gültige Beschreibung; erst
    `check_scenario` verglich Zeichenkette gegen Zahl und warf `TypeError` —
    und riss alle übrigen Fälle mit, die noch gelaufen wären. Grenzen werden
    jetzt als **endliche Zahlen** geprüft (`is_finite_number`, geteilt mit
    `is_finite_price`), `NaN` und `inf` eingeschlossen; fünf parametrisierte
    Gegenproben belegen beides: Die Beschreibung wird beanstandet, **und**
    `run_scenarios` kommt bis zum Ende.
[^golden]: **Gemessen, nicht zugesagt.** Die maschinell prüfbare Hälfte:
    `validate_scenarios` verlangt für **alle vier** Trefferarten die Kernwerte
    — „irgendein Treffer kam zurück" ist keine Aussage über ein Wertpapier. Bei
    `Quote` und `DailySeries` waren es bis Runde 1 keine; sie durften ohne einen
    einzigen Erwartungswert dastehen.

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
[^lauf]: `make test-plugin-api`: **257 passed, 1 skipped** (vor T-27a: 36;
    nach Runde 1: 189; nach Runde 2: 235).
    Übersprungen wird ein Zahlendreher-Fall, dessen getauschte Stellen zufällig
    gleich sind; der Test sagt das statt eine Aussage zu behaupten, die der
    Wert nicht hergibt. `make test` gesamt: Backend 637 / 29 skipped,
    Dashboard 259. `ruff check app tests plugin_api` sauber.

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

---

## Auflösung · Runde 1 → Runde 2

Alle vier Befunde tragen, und der erste trifft den Kern: **Meine Verträge haben
Leere zertifiziert.** Eine Schleife über eine leere Liste ist grün und sagt
nichts — genau das Muster, das ich in T-22 unter `P-05` schon einmal
beschrieben hatte, hier nur eine Ebene höher.

### 1 · Die Verträge lassen Leere und Unsinn nicht mehr durch

Der gemeinsame Griff war überall derselbe: `source.fetch(...) or []`, danach
eine Schleife. Bei `None` **und** bei `[]` lief sie null Mal.

| Vertrag | Was jetzt zuerst geprüft wird |
|---|---|
| Metadata | `_readings_for_responsible()` — nicht `None`, nicht leer |
| Daily | `_series_for_responsible()` — mindestens ein Handelstag |

Dazu die vier Regeln, die es gar nicht gab: Werttyp gegen `FieldSpec.kind`,
`FieldSpec.is_plausible()` (stand da, war getestet, wurde **nie aufgerufen**),
Pflichtwährung bei `Unit.ABSOLUTE`, und beim FX-Identitätsfall das **Paar** vor
der Rate — vorher bestand er mit `FxRate(base="USD", quote="JPY", rate=1.0)`
auf eine CAD→CAD-Anfrage.

**Und der eigentliche Nachweis:** `tests/test_contract_mutants.py`, 23 kaputte
Mini-Plugins, je eines pro Regel, die liegen bleiben. Ein einmal gelaufener
Mutant beweist den Stand von heute; ein festgehaltener beweist ihn auch nach
dem nächsten Umbau — und dieses Kit ist das Abnahmemittel für T-23, also für
Code, den es noch nicht gibt.

### 2 · Das Szenarioformat kann nicht mehr inkohärent grün werden

`ROLE_RESULTS` verlangt, dass Anfrage- und Trefferart zusammenpassen.
`REQUIRED_GOLDEN` deckt jetzt **alle vier** Trefferarten statt zwei — bei
`Quote` und `DailySeries` ist der Kern die **Währung**: eine Eigenschaft des
Listings, die sich nicht von Tag zu Tag ändert, während der Kurs es tut. Genau
deshalb taugt sie als Golden Case und der Kurs nur als Bereich. Die
Herkunftspflicht (`note`) stand vorher in einem App-eigenen Test — also gerade
nicht dort, wo ein fremder Autor davon profitiert; sie ist jetzt Teil der
Validierung.

Der Nullfall war der peinlichste Teil: **Der Test, der ihn zertifizierte, war
meiner.** Er hieß `test_die_reale_betriebsart_waehlt_nur_freigegebene_faelle`
und behauptete, null freigegebene Fälle seien ein Erfolg. Er ist umgekehrt, und
daneben steht jetzt einer, der die Auswahl mit einem *tatsächlich*
freigegebenen Fall belegt.

### 3 · Zwei Invarianten hießen mehr, als sie prüften

`currency_is_valid("ZZZ")` war `True`. Die Funktion prüfte die Form und hieß
„valid" — und `ZZZ` ist genau, wie das Feld aussieht, wenn ein Anbieter nichts
hat und trotzdem etwas hinschreibt. Jetzt gibt es beides getrennt:
`currency_is_wellformed` für die Form und `currency_is_valid` gegen die
vergebenen ISO-4217-Codes (`ISO_4217`, Stand als `ISO_4217_AS_OF` in jeder
Meldung). `XXX` und `XTS` sind ausgenommen — sie stehen in der Norm und
bedeuten „keine Währung". *(Der Umfang der Liste stand hier mit 177 Einträgen;
er gehört nicht in die Prosa, sondern in den Test, der ihn mit dem gemeldeten
Stand verknüpft — siehe Runde 3.)*

Die Kehrseite nenne ich ausdrücklich: Wird ein Code neu vergeben, weist die
Prüfung ihn ab, bis die Liste nachgezogen ist. Das ist ein lauter Fehlschlag
mit einer Meldung, die genau das sagt — und damit das kleinere Übel gegenüber
einem stillen Datenfehler.

`has_timezone` prüft jetzt `utcoffset() is not None`. Eine `tzinfo`, deren
`utcoffset()` `None` liefert, ist erlaubt, und **Python selbst** behandelt
einen solchen Zeitpunkt als naiv — er wirft beim ersten Vergleich mit einem
echten aware-Zeitpunkt. Meine Prüfung ließ ausgerechnet den Fall durch, der
später abstürzt.

### 4 · Die Diagnose gibt es jetzt wirklich

`Source.configuration_problem()` liefert einen Satz für einen Menschen, der die
Quelle **nicht** gebaut hat. `is_configured()` leitet sich daraus ab, damit
beide nicht auseinanderlaufen können. Der Vertrag prüft beide Richtungen: einen
Grund, wenn die Quelle stillsteht — und **Schweigen**, wenn sie läuft. Die
zweite Hälfte ist nicht Zierde: Eine Diagnose, die auch im Normalfall spricht,
wird nach dem dritten Mal überlesen.

Alle drei Beispiel-Plugins nennen jetzt den Pfad ihrer fehlenden Tabelle. „Nicht
konfiguriert" schickt den Betreiber auf die Suche; der Pfad beendet sie.

Der widersprüchliche Docstring in `test_kosten_sind_deklariert` ist berichtigt:
Seit T-22 sortiert **ausschließlich** `sources.yaml`, `cost` ist Information.

### Zusätzlich · Gemischte Währungen in einer Datei

`PricesFileDailySource` nahm die Währung der ersten Zeile für die ganze Reihe.
Eine von Hand gepflegte Tabelle bekommt über die Jahre Zeilen von verschiedenen
Leuten; schreibt einer CAD und ein anderer USD, entstand lautlos eine
„einheitliche" Reihe mit gemischten Beträgen — und ein Kurs darüber, dessen
Währung von der Sortierreihenfolge abhing. Jetzt `Unavailable` mit beiden
Währungen in der Meldung, plus zwei Negativtests (Reihe **und** Kurs, denn die
letzte Zeile für sich genommen ist eindeutig).

### Zum formalen Hinweis

Berechtigt. Branch und Produktedits für T-27a waren sichtbar, während
`STATUS.md` noch `approved`/T-22 meldete. Ein Race gab es nicht, aber wer nur
die Datei liest, sieht ein abgeschlossenes Ticket neben fremden Änderungen an
einem anderen — von einem Kommunikationsabbruch nicht zu unterscheiden. Die
Regel steht jetzt im Riegel-Abschnitt von `CODEX-REVIEW-AUTOMATION.md`: Der
Kettenwechsel ist ein eigener, atomarer Commit **vor** dem ersten Produktedit.

### Verifikation

* `make test`: Backend **637 / 29 skipped**, Plugin-API **235 / 1 skipped**
  (Runde 1: 189), Dashboard **259**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
* 23 Mutanten grün, plus die Gegenprobe, dass ein heiles Plugin nicht
  beanstandet wird.

---

## Codex-Review · Runde 2 · `db53189`

Die vier Befunde aus Runde 1 sind in ihrer jeweils geprüften Form behoben; die
Mutanten sind eine deutliche Verbesserung des Kits. Drei inhaltliche Restlücken
und ein Prozesswiderspruch verhindern noch die Freigabe:

1. **Hoch · Ein unbekannter Request-Typ kann als Szenario grün werden.**
   `_check_role_match()` beendet sich für alle Miss-Typen, bevor es den
   Request prüft. Dadurch liefern `validate_scenarios([Scenario(request=object(),
   expect=Unavailable, ...)])` und anschließend der vollständige Lauf beide
   `[]`: `DirectRunner` erfindet für den unbekannten Typ genau das erwartete
   `Unavailable`. `ROLE_RESULTS` muss den Request-Typ unabhängig davon
   validieren, ob ein Hit oder Miss erwartet wird; ein bleibender Negativtest
   muss genau diesen Fall ausführen.
2. **Mittel · Fehlerhafte Plausibilitätsgrenzen umgehen die Validierung und
   brechen den Lauf ab.** `plausible={"price": ("a", "z")}` gilt in
   `_check_ranges()` als gültig. `check_scenario()` vergleicht danach String
   und Float und wirft `TypeError`, obwohl `validate_scenarios()` laut Vertrag
   Beschreibungsfehler sammeln und der Runner nicht abbrechen soll. Grenzen
   müssen als endliche Zahlen validiert werden; Gegenproben brauchen falsche
   Typen sowie `NaN`/`inf`.
3. **Mittel · Die angeblich aktuelle ISO-4217-Liste enthält einen historischen
   Code.** `ISO_4217_AS_OF = "2026-08"`, zugleich ist `BGN` enthalten und
   `currency_is_valid("BGN")` liefert `True`. Die offizielle Maintenance
   Agency hat BGN mit Wirkung vom **1. Januar 2026** aus List One nach List
   Three verschoben: [ISO-4217 Amendment 180](https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/amendments/dl-currency-iso-amendment-180.pdf).
   Liste, Anzahl, Tests und Dokumentation müssen denselben tatsächlichen Stand
   belegen.
4. **Mittel · Die neue atomare Kettenwechsel-Regel widerspricht dem
   Scheduler-Prompt.** Der neue Riegel verlangt für ein begonnenes Ticket
   `review_round: 0`; Punkt 4 des Claude-Loops verlangt weiterhin `1`.
   Festzulegen ist `0` beim Arbeitsbeginn und das Hochzählen auf `1` bei der
   ersten Übergabe. Beide Stellen müssen dieselbe Regel sagen. Im Zuge dessen
   die veraltete Verifikationszahl oben (`227` statt tatsächlich `235`) auf den
   belegten Stand bringen.

**Adversariale Evidenz:** Unbekannter Request plus erwartetes `Unavailable`
lief in Validierung und Ausführung grün; String-Grenzen endeten mit `TypeError`;
`currency_is_valid("BGN")` war `True`. Regulär sind Backend **637 passed / 29
skipped**, Plugin-API **235 passed / 1 skipped**, Dashboard **259 passed**;
Ruff, `git diff --check` und der Wheel-Build für
`stockinfo_plugin_api-0.2.0-py3-none-any.whl` sind sauber. Diese Runde ist
punktuell und voraussichtlich abschließend: Der verbleibende Umfang besteht aus
drei klar reproduzierten Validierungsfällen und einer widersprüchlichen
Prozesszeile; eine Rebaseline ist nicht nötig.

---

## Runde 3 · Nacharbeit zu den vier Befunden

Alle vier sind umgesetzt. Zwei Anmerkungen vorweg, weil sie mehr sagen als die
Einzelkorrekturen.

**Die ersten beiden Befunde sind derselbe Fehler.** In beiden Fällen stand eine
Abkürzung *vor* der Prüfung, die es zu tun gab: Die Rollenprüfung stieg bei
Fehlfällen aus, bevor sie den Anfragetyp ansah; die Bereichsprüfung sah die
Anzahl der Grenzen an, aber nicht ihre Art. Beide Male lief danach etwas grün,
das nie gefragt worden war. Das ist `P-08` — der Test erzeugt den
entscheidenden Unterschied nicht — und diesmal in der Prüfschicht selbst.

Beim ersten kommt eine Bosheit dazu, die ich festhalten will: `DirectRunner`
**erfindet** für einen unbekannten Anfragetyp ein `Unavailable`. Ein Fall, der
`Unavailable` erwartet, bekommt damit vom Prüfstand genau die Antwort, die er
hören will, ohne dass die Quelle je gefragt wurde. Der Runner tut nichts
Falsches — sicher macht es erst die Validierung davor.

**Beim dritten Befund war der genannte Code nicht der einzige.** `BGN` stimmte.
Statt ihn zu streichen, habe ich die Liste als Ganzes gegen die offizielle
List One gestellt:

```
curl -s .../iso-currrency/lists/list-one.xml   →  Pblshd="2026-01-01", 178 Codes
bei uns, offiziell nicht mehr:  ANG, BGN
offiziell, bei uns nicht:       XAD
```

`ANG` ist seit dem 30. Juni 2025 zurückgezogen (abgelöst durch `XCG`), `XAD`
(Arab Accounting Dinar) ist vergeben und wurde von uns abgewiesen — laut
Docstring der Liste „der schlimmere Fehler". Beide hätte eine Punktkorrektur an
`BGN` stehen lassen; das ist `P-02`, und der Weg dorthin war der Abgleich, nicht
die Suche nach dem gemeldeten Symptom.

Liste und Quelle sind jetzt deckungsgleich: **176** = 178 vergebene minus
`XXX`/`XTS`. `ISO_4217_AS_OF` trägt das `Pblshd`-Datum der Datei statt eines
selbstgesetzten Monats — ein Datum, das von der Quelle stammt, lässt sich gegen
sie prüfen. `test_der_gemeldete_stand_und_die_liste_gehoeren_zusammen` bindet
Anzahl und Stand aneinander, damit sie nicht wieder getrennt altern. Ein
Netzabruf im Test wäre der falsche Weg: Er wäre rot, wenn jemand im Zug sitzt,
und das hat mit der Sache nichts zu tun.

**Vierter Befund.** `review_round: 0` beim Arbeitsbeginn, Hochzählen auf `1` bei
der ersten Übergabe — an beiden Stellen. Der Riegel-Abschnitt nennt jetzt auch
den Grund: Zwei verschiedene Runden mit derselben Nummer nähmen dem Schlüssel
`(ticket, handoff_commit, review_round)` genau dort die Eindeutigkeit, wo die
Duplikatsperre auf ihn baut. Die Zahl `227` ist auf die belegten `235`
berichtigt.

### Gegenprobe

Der Nachweis, dass die neuen Tests den Unterschied wirklich erzeugen: `src` auf
den Stand `db53189` zurückgesetzt, dieselben Tests laufen lassen.

```
6 failed, 20 deselected
  test_ein_unbekannter_anfragetyp_faellt_auch_bei_einem_fehlfall_auf
  test_unbrauchbare_grenzen_sind_ein_beschreibungsfehler [5 Parameter]
    → TypeError: object of type 'float' has no len()
```

Der letzte Fehlschlag ist wörtlich das gemeldete Symptom.

### Verifikation

* `make test`: Backend **637 passed / 29 skipped**, Plugin-API **257 passed /
  1 skipped** (Runde 2: 235), Dashboard **259 passed**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
* 23 Mutanten unverändert grün, samt Gegenprobe am heilen Plugin.

Verify `#9` bleibt `⚠️` mit unveränderter Begründung: Half-open und Reset
gehören zu T-23. Neu ist `#6c` — eine kaputte Fallbeschreibung kommt als Befund
zurück, statt die übrigen Fälle mitzureißen.
