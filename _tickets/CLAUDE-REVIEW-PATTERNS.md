# Claude-Review-Muster

Versioniertes, compaction-festes Gedächtnis für wiederkehrende Fehler in
Claudes Implementierungen und Übergaben. Jeder Codex-Review liest diese Datei
vollständig. Sie ist die spätere Ausgangsbasis für einen eigenen Review-Skill.

Aufgenommen werden nur verallgemeinerbare Muster mit mindestens zwei konkreten
Belegen oder eine ausdrücklich falsche Vollständigkeitsbehauptung. Einzelne
Bugs bleiben im Ticket. Ein Eintrag enthält Erkennungsregel, Prüffrage und
Belege; neue Belege werden am bestehenden Eintrag ergänzt statt ihn zu
duplizieren.

## Übersicht

- [P-01 · Testtiefe wird überzeichnet](#p-01--testtiefe-wird-in-der-übergabe-überzeichnet)
- [P-02 · Regelumsetzung wird zu früh vollständig gemeldet](#p-02--punktuelle-korrektur-wird-als-vollständige-regelumsetzung-gemeldet)
- [P-03 · Prüfwerkzeuge räumen fremde Ressourcen auf](#p-03--prüfwerkzeuge-räumen-fremde-ressourcen-mit-auf)
- [P-04 · Negativtests prüfen nur die Fehlerbeschriftung](#p-04--negativtests-prüfen-nur-die-fehlerbeschriftung)
- [P-05 · Ein abgebrochener Prüflauf meldet sich als bestanden](#p-05--ein-abgebrochener-prüflauf-meldet-sich-als-bestanden)

## P-01 · Testtiefe wird in der Übergabe überzeichnet

**Erkennungsregel:** Die Übergabe behauptet „ganze Kette", „nur externe Grenze
gemockt" oder gleichwertig, während eine eigene Kernkomponente durch Fake,
Stub oder Mock ersetzt ist.

**Prüffrage:** Welche konkrete Objektkette läuft im Test? Jeden Test-Doppel als
externe Grenze oder eigene Komponente klassifizieren und die Behauptung damit
abgleichen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: In
`tests/test_resolver.py` ersetzte `CountingResolver` den eigenen
`YFinanceResolver`, obwohl Übergabe und Docstring behaupteten, allein
`httpx.post` sei gemockt und die ganze Kette werde geprüft.

**Beleg:** T-21 Teil 1, Commit `fce1bab`: Verify `#1` markierte die Migration
einer bestehenden Datenbank mit `✅` als live geprüft. Ticketfußnote und
Übergabe hielten zugleich fest, dass nur eine synthetisch nachgestellte
Alt-Datenbank und kein real gewachsener Bestand geprüft worden war.

[↑ Übersicht](#übersicht)

## P-02 · Punktuelle Korrektur wird als vollständige Regelumsetzung gemeldet

**Erkennungsregel:** Besprochene Beispiele sind korrigiert, aber derselbe Diff
führt neue Verstöße gegen die zugrunde liegende Regel ein oder behält alte
Referenzen darauf.

**Prüffrage:** Nicht nur die genannten Beispiele bestätigen; den vollständigen
hinzugefügten Diff automatisiert und manuell gegen die Regel prüfen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: Die zwei besprochenen
Produktbezeichner waren englisch, gleichzeitig entstanden neue deutsche
Test-Helper, Variablen und strukturierte Log-Felder; ein Docstring verwies
weiter auf `_ist_symbolfaehig`.

**Beleg:** T-24 Teil 2, Commit `d792ce9`: Die Übergabe erklärte die
Währungspflicht als an „allen“ gefundenen Stellen umgesetzt und markierte
`#9` mit ✅. Live-, Daily- und History-Pfade waren korrigiert, aber der
meistgenutzte frische sowie der stale Cache-Pfad baute in
`CachedQuoteService._from_cache` weiterhin eine erfolgreiche `QuoteResponse`
mit `currency=None`, wenn Kurspunkt und Instrument keine Währung hatten.

**Beleg:** T-18 Runde 1, Commit `32e08ea`: Die Übergabe erklärte die neue
`fetch_etf`-Signatur an allen Stellen nachgezogen. Der Composite akzeptierte
`exchange` und `currency` und nutzte sie für `is_responsible`, verwarf beide
aber beim anschließenden `enricher.fetch_etf(...)`-Aufruf. Ein Provider, der
den neuen Kontext auch zum Abruf benötigt, wurde deshalb zuständig gewählt
und danach ohne den Kontext aufgerufen.

**Beleg:** T-20 Runde 1, Commit `5d79a6d`: Der Resolververtrag wurde von
`ResolvedInstrument | None` auf vier Ergebnisarten umgestellt und die
Quote-Kette samt Tests angepasst. Der ebenfalls am `InstrumentResolver`
hängende `QuoteAnalyzer` prüfte weiterhin nur auf `None` und griff bei
`NotFound`, `NotResponsible` und `Unavailable` auf `.symbol` zu; der
Diagnose-Endpunkt endete deshalb für unbekannte Papiere und Quellenausfälle
mit HTTP 500.

**Beleg:** T-21 Teil 1, Commit `fce1bab`: Die Identität und der eindeutige
Index wurden von `symbol` auf `(ticker, mic)` umgestellt, während
`_dedupe_symbols()` weiterhin bei jedem Start ausschließlich nach `symbol`
gruppierte. Dadurch löschte der nächste `init_db()` eines von zwei
kanonisch verschiedenen Listings mit demselben Symbol an verschiedenen MICs.

**Beleg:** T-21 Teil 1 Runde 2, Commit `48cdaf9`: Die Korrektur erklärte, nur
noch „kanonisch gleiche“ Instrumente würden zusammengeführt. Für offene Zeilen
gruppierte sie jedoch weiterhin allein nach `symbol`, obwohl dort gerade keine
kanonische Identität bekannt ist. Eine Gegenprobe mit gleichem Symbol, aber
verschiedenen ISINs und `listing_id` verlor beim nächsten `init_db()` erneut
eine der beiden Zeilen.

**Beleg:** T-21 Teil 1 Runde 3, Commit `7da4aae`: Die Übergabe meldete nach der
dritten Naming-Anmahnung `app/db.py`, das ganze Prüfskript und die gesamte
Migrationstestdatei als durchgesehen; Kommentare und Docstrings sollten deutsch
bleiben. Die mechanische Ersetzung hinterließ jedoch Sätze wie „bleibt
`open_rows` und sichtbar“ und „wurde `before` zusammengeführt“ sowie weiterhin
nichtsprechende Einbuchstaben-Bezeichner im berührten Test- und Smoke-Code.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 1
Runde 4, Commit `d6c4c19`: Die Übergabe erklärte die verbliebenen Kurznamen
`r`, `s`, `z` und `e` für sprechend umbenannt und die beschädigte deutsche
Prosa für geheilt. Im geänderten Smoke-Code blieb dennoch `for r in
newly_resolved`, in `tests/test_identity_migration.py` weiterhin „solche
Zeilen bleiben `open_rows`“. Außerdem beschreiben Script und Ticket das
ersetzte Rückwärts-Oracle weiter als aktuelle Prüfung.

**Beleg:** T-21 Teil 1 Runde 6, Commit `4b7a88a`: Die Korrektur bezeichnete
jede `resolved`-Zeile mit nichtleerem Ticker und MIC als vollständige
kanonische Identität. Der Smoke-Check schloss den verbotenen Collector-Code
`US` korrekt aus, die neue Produktfunktion `_has_valid_identity` prüfte aber
nur auf nichtleere Strings und konservierte `VTI/US` bei jedem Start. Die
angekündigte Neubewertung aller anderen Zustände überschrieb außerdem eine
vollständige manuelle Zuordnung `VTI/XNAS`, sobald nur ihr Status unbekannt
war, mit `NULL/NULL/legacy_unresolved`.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 1
Runde 7, Commit `3148d09`: Die Übergabe erklärte beide Reproduktionen für
nicht mehr herstellbar und `is_real_mic` zur einen, von Migration und Prüfung
benutzten Entscheidung. Die Funktion hielt jedoch jeden unbekannten
nichtleeren String für einen echten MIC und konservierte
`VTI/NOT-A-MIC/resolved`; der Smoke duplizierte nur den Ausschluss bekannter
Collector-Codes und bestand mit diesem Wert 9/9. Im neu hinzugefügten Test
entstand zugleich erneut der deutsche lokale Bezeichner `repariert`, obwohl
die Naming-Regel bereits in Runde 3 und 4 Gegenstand der Korrektur war.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 1
Runde 8, Commit `62dcfd2`: Die Korrektur versprach eine Schreibweisenprüfung
auf „genau vier Zeichen“ und meldete den deutschen Bezeichner als bereinigt.
Der Regex-Anker `$` akzeptierte jedoch `XNAS\n`, sodass Migration und Smoke
den Wert weiter als kanonisch gültig behandelten. Gleichzeitig entstand im
neuen Parametertest der deutsche Parameter `warum` — erneut ein neuer Verstoß
gegen genau die gerade korrigierte Naming-Regel.

[↑ Übersicht](#übersicht)

## P-03 · Prüfwerkzeuge räumen fremde Ressourcen mit auf

**Erkennungsregel:** Cleanup bestimmt sein Ziel anhand eines globalen Merkmals
wie Port, Prozessname oder Pfadmuster statt anhand einer vom Lauf erzeugten und
gespeicherten Identität.

**Prüffrage:** Gehört jede beendete oder gelöschte Ressource nachweislich
diesem Lauf? Bei Prozess-Cleanup nur eigene PID beziehungsweise eigene
Prozessgruppe verwenden und Konflikte vor dem Start abbrechen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: `_tickets/T-17-smoke.sh`
beendete nach dem Lauf alle Prozesse auf Port 8766; ein bereits laufender
fremder Server konnte zusätzlich den Health-Check bestehen und danach beendet
werden.

[↑ Übersicht](#übersicht)

## P-04 · Negativtests prüfen nur die Fehlerbeschriftung

**Erkennungsregel:** Eine absichtlich ungültige Fixture oder ein Negativfall gilt
als geprüft, obwohl der Test nur ein Fehlerkennzeichen wie `violates`, einen
Status oder eine Beschreibung verlangt, nicht aber die bezeichnete Verletzung
selbst reproduziert.

**Prüffrage:** Wird der Test rot, wenn man ausschließlich den eigentlichen
Fehler im Negativfall beseitigt und dessen Beschriftung unverändert lässt? Für
jede erlaubte Fehlerkennung muss eine konkrete, gegensinnige Assertion
existieren.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-24 Teil 1,
Commit `403020b`: Ticketzeile `#7i` war mit `✅` als statische Konsistenz von
Artefakt und Fixtures markiert. In `tests/test_contract.py` genügte bei
nicht-konformen Fixtures jedoch ein nichtleerer `violates`-Text; selbst eine
angeblich widersprüchliche `/generation`-Fixture mit identischen UUIDs in Header
und Body passierte beide einschlägigen Prüfungen (`MUTANT_UNERKANNT`).

**Beleg:** T-21 Teil 1 Runde 2, Commit `48cdaf9`: Das neue
`T-21-smoke.sh` meldete die behaupteten sechs Migrationschecks auch auf einer
vollständig leeren Datenbank als bestanden. `all(...)` auf leeren Mengen und
Vergleiche `0 == 0` ersetzten den Nachweis der konkret behaupteten
Auflösungen; selbst `#3b` prüfte nur Indexnamen statt deren Eindeutigkeit.

**Beleg:** T-21 Teil 1 Runde 3, Commit `7da4aae`: Der reparierte Smoke-Check
verwendete `split_symbol` sowohl in der Migration als auch zur Berechnung des
Erwartungswerts. Damit bestätigte die Produktionsfunktion sich selbst und
verwarf zugleich einen laut Ticket gültigen Zielzustand: Ein bereits manuell
aufgelöstes suffixloses Listing `WALONLY/XNAS` wurde von `#2` als falsch
markiert, weil sein Legacy-Symbol absichtlich nicht rückwärts zerlegbar ist.

**Beleg:** T-21 Teil 1 Runde 4, Commit `d6c4c19`: Das neue Vorwärts-Oracle
setzte `(ticker, mic)` über jeden Eintrag aus `EXCHANGES` zu `symbol` zusammen,
ohne echte MICs vom ausdrücklich verbotenen internen Sammelcode `US` zu
trennen. Eine Gegenprobe ließ die Migration `VTI` als `VTI/US` und `resolved`
erzeugen; `#2` meldete wörtlich `VTI/US→VTI` und das Script bestand mit 8/8.
Auf einem bereits migrierten Bestand bestand derselbe Check außerdem mit „0
neu zerlegt“ und prüfte damit keine einzige Zuordnung.

**Beleg:** T-21 Teil 1 Runde 5, Commit `92ee6a2`: Der ergänzte Check `#2d`
zählte alle Zeilen mit `identity_status = resolved`, prüfte aber nur, ob ihr
`mic` in der Menge bekannter Sammelcodes liegt. Eine vorbestehende Zeile
`VTI` mit Status `resolved`, aber `ticker=NULL` und `mic=NULL`, wurde als
fünfte „aufgelöste Zeile“ gezählt; das Script bestand mit 9/9. Die Migration
selbst übersprang diese unvollständige Identität anschließend dauerhaft, weil
sie jeden gesetzten Status als bereits bearbeitet behandelt.

**Beleg:** T-21 Teil 1 Runde 7, Commit `3148d09`: `#2d` versprach für
`resolved` einen echten MIC, schloss aber weiterhin nur die in `EXCHANGES`
bekannten Collector-Codes aus. Ein präparierter Bestand mit
`VTI/NOT-A-MIC/resolved` passierte `#2d` und den gesamten Smoke-Lauf mit 9/9;
die neuen Produkttests deckten ausschließlich den konkret besprochenen Wert
`US` und die positive Gegenprobe `XNAS` ab.

**Beleg:** T-21 Teil 1 Runde 8, Commit `62dcfd2`: Der Smoke ersetzte sein
eigenes MIC-Oracle durch einen Aufruf der Produktionsfunktion `is_real_mic`.
Der neue `$`-Regex akzeptierte einen finalen Zeilenumbruch; damit hielten
Produkt und Prüfung `VTI/XNAS\n/resolved` gemeinsam für gültig und der
präparierte Lauf bestand 9/9. Die neuen Grenztests enthielten Leerzeichen,
Länge, Kleinschreibung und Sonderzeichen, aber keinen Zeilenumbruch.

[↑ Übersicht](#übersicht)

## P-05 · Ein abgebrochener Prüflauf meldet sich als bestanden

**Erkennungsregel:** Ein Prüf-Script zählt die Ergebnisse, die es bekommen hat,
und schließt daraus auf Vollständigkeit. Bricht der geprüfte Vorgang mitten im
Lauf ab, sieht das Ergebnis aus wie ein vollständiger Lauf ohne Fehler — nur
mit weniger Zeilen. Verstärkt wird es, wenn die Fehlerausgabe nur dann gezeigt
wird, wenn **gar nichts** ankam.

**Prüffrage:** Woran erkennt das Script, dass der Lauf **zu Ende** gelaufen ist
— und nicht nur, dass das Angekommene grün war? Es braucht eine Schlussmarke
oder eine erwartete Anzahl; die Zahl im Erfolgssatz ist kein Beleg, sie zählt
nur mit. Gegenprobe: einen Abbruch mitten im Lauf erzwingen und nachsehen, ob
das Script rot wird.

**Beleg:** T-21 Teil 2b, 2026-08-23: Der Umzug von `figi_id_type` zum
OpenFIGI-Provider entfernte eine Spalte, die `T-21-smoke.sh` in seinem eigenen
Orakel noch las. Das Script stürzte nach vier von neun Prüfungen mit einer
`AttributeError` ab, die Fehlerausgabe blieb verborgen — und es meldete
„4 Checks bestanden, keine Fehler". Die vier Zeilen davor waren echt; die fünf
fehlenden fielen nur auf, weil die Ticketfußnote neun nannte.

**Nachbarschaft zu P-01:** Dort wird die Testtiefe in der Übergabe
überzeichnet. Hier überzeichnet sich das **Werkzeug** — die Übergabe gäbe
seine Zahl gutgläubig weiter.

[↑ Übersicht](#übersicht)
