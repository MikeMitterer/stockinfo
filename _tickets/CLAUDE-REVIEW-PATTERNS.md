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
- [P-06 · Weiterarbeiten, während eine Übergabe offen ist](#p-06--weiterarbeiten-während-eine-übergabe-offen-ist)
- [P-07 · Eine neue Zwischenlage wird gebaut statt benannt](#p-07--eine-neue-zwischenlage-wird-gebaut-statt-benannt)
- [P-08 · Der Test erzeugt den entscheidenden Unterschied nicht](#p-08--der-test-erzeugt-den-entscheidenden-unterschied-nicht)
- [P-09 · Eine Testanforderung wächst zum unbeauftragten Subsystem](#p-09--eine-testanforderung-wächst-zum-unbeauftragten-subsystem)
- [P-10 · Ein Integrationstest berührt seine Außengrenze nicht](#p-10--ein-integrationstest-berührt-seine-außengrenze-nicht)
- [P-11 · Die Übergabe steht in der Mailbox, bevor es sie gibt](#p-11--die-übergabe-steht-in-der-mailbox-bevor-es-sie-gibt)
- [Leitplanken für das spätere Skill-Proposal](#leitplanken-für-das-spätere-skill-proposal)

## Leitplanken für das spätere Skill-Proposal

Dieser Abschnitt ist **kein Claude-Fehlermuster**, sondern das Prozesslearning
aus T-21 Teil 3. Dort brauchte ein reiner Entwurf die Runden 8 bis 24. Ein
Review-Skill muss deshalb nicht nur Fehler finden, sondern aktiv Konvergenz
erzwingen und klare Grenzen setzen:

1. **Scope-Grenze:** Eine Übergabe hat genau ein beobachtbares Ergebnis.
   Mehrere unabhängig lieferbare Regeln werden vor dem Review getrennt; ein
   vertikaler Schnitt darf mehrere Schichten berühren, muss aber als eine
   durchgehende Kette prüfbar bleiben.
2. **Runden-Leitplanke:** Ungefähr drei nicht erfolgreiche Entwurfsrunden sind
   ein Richtwert für eine ausdrückliche Konvergenzprüfung, keine absolute
   Grenze. Eine weitere Runde ist sinnvoll, wenn Rest und Abschlussweg konkret,
   klein und voraussichtlich abschließend sind; andernfalls verlangt der
   Reviewer eine konsolidierte Neufassung oder einen kleineren Zuschnitt.
   Nach jeder weiteren erfolglosen Runde wird neu bewertet.
3. **Entscheidungs-Grenze:** Eine neue Grundentscheidung invalidiert alle
   davon abhängigen Aussagen, Tests und Verify-Markierungen. Der Entwurf wird
   auf eine neue Basis gestellt; alte Regeln werden nicht mit Warnungen,
   Durchstreichungen und Nachträgen weitergeschleppt.
4. **Auswirkungs-Grenze:** Vor einer Vollständigkeitsbehauptung wird jede neue
   Fachregel einmal über ihre Erzeuger und Verbraucher verfolgt: Datenmodell,
   Repository, Service, REST, UI, Migration, Betrieb, Dokumentation und Tests.
   Nicht zutreffende Schichten werden ausdrücklich ausgeschlossen.
5. **Evidenz-Grenze:** Lange Prosa ersetzt keine ausführbare Gegenprobe.
   Vertrags- und Integrationsfragen werden früh mit kleinen Spikes oder Tests
   gegen den realen Umgebungscode geprüft.
6. **Rollen-Grenze:** Technische Folgefragen bleiben bei Implementierer und
   Reviewer. Der Mensch wird nur für eine echte Produktentscheidung oder eine
   notwendige Scope-Erweiterung unterbrochen, nicht für unbestimmte Fragen wie
   „trägt der Entwurf zu viele Sonderfälle?".
7. **Reviewer-Verantwortung:** Der Reviewer bewertet auch den Prozess. Er muss
   eine nicht konvergierende Schleife stoppen, selbst wenn jedes einzelne
   Finding sachlich korrekt ist.
8. **Skelett-Grenze:** Nennt ein Vorhaben einen Erfolgsweg, muss dieser Weg
   **einmal durchgelaufen** sein, bevor die Vorarbeiten weiterlaufen — als
   dünnstes lauffähiges Skelett, hartverdrahtet und hässlich erlaubt. Ein
   Maßstab, an dem erst am Ende gemessen wird, ist ein Wunsch.
9. **Budget-Grenze:** Überschreitet ein Ticket seine Time-Box um ein
   Vielfaches, ist das ein Anlass für eine ausdrückliche Zuschnittsprüfung —
   nicht für weitere Runden. Der Implementierer stellt die Frage, bevor der
   Mensch sie stellen muss.
10. **Testinfrastruktur-Grenze:** Unit-Tests und echte Online-
    Integrationstests über die vorhandenen Bibliotheks- und Sprach-APIs sind
    der Standard. Ein eigenes Test-Subsystem braucht vor Entwurf und Code eine
    ausdrückliche, im Ticket dokumentierte Freigabe von Mike.

**Beleg für Leitplanke 8 — und der Anlass, sie aufzuschreiben** *(Mike,
2026-08-27, nach Runde 52)*: Der Plugin-Entwurf vom 2026-08-19 nennt als
Maßstab ausdrücklich, „dass jemand in Toronto tatsächlich ein Plugin einsetzen
kann". Dieselbe Datei stellt den Lader (T-22, T-23) an Position sechs und
sieben. Nach 52 Runden war der Stand: **880 Zeilen zugesagter Plugin-Vertrag,
und der Core führt davon genau drei Namen aus** — `NotFound`,
`NotResponsible`, `Unavailable`. `sources.py`, `testing.py` und beide
Beispiel-Plugins hat StockInfo nie geladen.

Dass das gefährlich ist, belegen die teuersten Befunde derselben Runden. Sie
sind **alle vom selben Typ: geschrieben, nie ausgeführt.**

* Der `409` bei mehrdeutigem Symbol stand seit T-24 im **abgenommenen**
  Vertrag und war an keinem Endpunkt gebaut — über zwanzig Runden unbemerkt.
* Zwei Wächterregeln (Runden 48 und 49) passten nicht einmal auf den
  unveränderten Bestand.
* Die Pluralformen standen in beiden Katalogen verkehrt herum — sichtbar in
  einer Sekunde, sobald man sie einmal laufen lässt.

**Reviewqualität ersetzt keine Ausführung.** Ein Review findet Widersprüche
zwischen Artefakten; dass ein Vertrag der Wirklichkeit nie begegnet ist, findet
es nicht.

**Auslöser für das Skill-Proposal:** T-21 Teil 3 endete nach 17
Entwurfsrunden bei einer 936-zeiligen Spec. Die Runden 8, 9, 10, 13 und 17 bis
23 lieferten zugleich elf Belege für P-02. Das zeigt: Fachliche Gründlichkeit
ohne Scope-, Runden- und Entscheidungsgrenzen verhindert keine
Review-Eskalation.

[↑ Übersicht](#übersicht)

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

**Neuer Beleg wegen ausdrücklich falscher Testtiefenbehauptung:** T-21 Teil 3
Übergabe 2A, Runde 30, Commit `d361fbc`: Ticketfußnote und Test-Docstring
erklärten, `test_die_bestaetigung_startet_den_scheduler` prüfe, dass der
Scheduler anlaufe. Der Test ersetzt den registrierten Produkt-Callback jedoch
durch `lambda: gestartet.append("scheduler")`; weder `RefreshScheduler` noch
sein `start()` laufen. Geprüft ist nur, dass irgendein Callback aufgerufen
wird — und auch das vor statt nach der Migration.

**Neuer Beleg:** T-22 Runde 1, Commit `20af8fa`: Smoke und Übergabe erklärten,
über echte Neustarts werde geprüft, „welche Kette entsteht“. Der Smoke las
jedoch ausschließlich `/sources`; die Verdrahtung lief nur in einem getrennten
Unit-Test. Weil der Endpunkt die Datei frisch las, die Services aber eine
gecachete Konfiguration hielten, konnte die laufende Kette `OpenFigiResolver`
sein und `/sources` zugleich `yahoo-search` melden. Beide Tests blieben grün,
weil keiner die beiden Seiten in derselben gestarteten App verglich.

**Neuer Beleg:** T-22 Runde 2, Commit `d5bb327`: Die Übergabe erklärte, die
Korrektur habe für beide Hälften eigene Tests und der HTTP-Test prüfe denselben
Stand wie die laufenden Dienste. Der benannte Test schrieb jedoch nur eine
Konfiguration, leerte den Cache und rief danach `/sources` auf. Er primte keine
Laufzeitkette und änderte die Datei nicht anschließend; eine Rückkehr zum
frischen Dateilesen im Endpunkt wäre deshalb unentdeckt grün geblieben.

**Neuer Beleg:** T-23 Runde 1, Commit `e6ca003`: Die Übergabe erklärte, zwei
Plugins beantworteten dieselbe Rolle und ausschließlich `sources.yaml` wähle
zwischen ihnen. Der benannte Test verlangte jedoch ausdrücklich
`not isinstance(chain[0], YFinancePlugin)` und baute für `yfinance` weiter den
alten nativen `YFinanceProvider`. Das Datei-Plugin wurde nur direkt unterhalb
des Core aufgerufen; Registry → Core → REST blieb ungetestet und laut OUTBOX
noch offen.

**Neuer Beleg:** T-23 Runde 3, Commit `4e23cde`: Der neue Rollentest wurde als
Nachweis beschrieben, dass alle fünf Rollen dem Core nun das von ihm
aufgerufene Objekt liefern. Er prüfte jedoch ausschließlich `hasattr` auf dem
Ergebnis von `build_chain`. Der echte Daily-Aufruf mit `AAPL/XNAS` endete vor
dem Provider mit `None`, und der Metadatenaufruf übernahm eine Ratio-TER ohne
Umrechnung und verlor ihre Herkunft. Vorhandensein einer Methode war keine
Ausführung der behaupteten Core-Grenze.

**Neuer Beleg:** T-23 Runde 4, Commit `adcb505`: OUTBOX und Test-Docstring
erklärten, beide Loader-Namen würden in `GET /sources` geprüft. Der Test
konfigurierte dort jedoch nur `local-file`; für `canada-file` akzeptierte die
Assertion alternativ dessen bloßes Vorkommen in `specs_by_name()`. Damit war
der Test grün, obwohl der zweite Name in der HTTP-Antwort fehlen durfte.

**Neuer Beleg:** T-23 Runde 5, Commit `d4f9036`: OUTBOX erklärte, beide
Metadatenfälle liefen durch `CompositeEtfEnricher → Adapter → Plugin` und
`close()` werde je Objekt genau einmal gerufen. Im Produktcommit wurde jedoch
kein Test für einen dieser Wege ergänzt; der Test-Diff betraf Installer,
Parser, einen Diagnosefall nach vorherigem Bau und die zwei Namen in
`/sources`. Claudes eigene Fehleranalyse („kein Test lief durch
`CompositeEtfEnricher`“) blieb damit auch nach der Reparatur ohne dauerhafte
Gegenprobe.

**Neuer Beleg:** T-37, Commit `d313318`: Ticket und OUTBOX meldeten dieselbe
Prüfstrecke für ein CSV-Profil mit Quellen in allen fünf Rollen. Der Smoke
prüfte die fünf Namen jedoch nur über `/sources`; seine 17 fachlichen Checks
riefen Resolver, Quote und Metadaten auf, aber weder `/quote/{isin}/daily`
noch `/fx`. Konfiguration war damit für Ausführung eingetreten, obwohl die
beiden Rollen den Core in diesem Lauf nie berührten.

**Neuer Beleg:** T-31 Runde 5, Commit `1133dd9`: Übergabe und Test-Docstring
meldeten für `BTC-EUR` die „echte Kette; nur Außengrenzen ersetzt". Der Test
injizierte mit `_TypingResolver` jedoch direkt einen eigenen Kern-Resolver und
umging damit Registry, `ResolverAdapter` und `YahooSearchResolverPlugin`. Die
reale Online-Quelle akzeptierte weder Symbol-Requests noch `crypto`; der
behauptete Produktweg blieb trotz grünem Orakel unberührt.

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

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 2
und 2b, Commit `556c23d`: Commit und Übergabe erklärten, neue Papiere brächten
`ticker` und `mic` beim Anlegen mit, und Verify `#5` stand auf ✅. Der
öffentliche Symbolpfad `GET /quote?symbol=…` erzeugte jedoch weiterhin nur ein
`ResolvedInstrument(symbol=…)`; selbst das eindeutig zerlegbare `VGWL.DE`
landete dadurch als `NULL/NULL/legacy_unresolved` in der Datenbank. Die neuen
Tests bauten entweder bereits eine fertige `QuoteResponse` mit Identität oder
prüften ausschließlich den ISIN-Resolver-Pfad. Im selben Diff entstanden nach
den wiederholten Naming-Korrekturen außerdem erneut deutsche Produktbezeichner
und strukturierte Log-Felder wie `_identitaet`, `boersencode`,
`_FIGI_AUSNAHMEN` und `quelle`.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 2
und 2b Runde 4, Commit `c6f69a9`: Die Übergabe erklärte, ein `tokenize`-Scan
belege „keine deutschen Bezeichner mehr in den berührten Dateien“. Im
berührten `app/services/quote_service.py` blieben jedoch `fehlend`, `feld`
sowie die strukturierten Log-Bezeichner `core_unvollstaendig` und `fehlend`;
`tests/test_resolver.py` enthält unter anderem `_FigiNachBoerse`, `treffer`,
`unzustaendig`, `zustaendig` und `_mit_suche`. Im ebenfalls berührten
`_tickets/T-21b-smoke.sh` blieb im eingebetteten Python `zeilen`. Der
angekündigte Scan deckte seinen behaupteten Dateiscope damit nicht ab.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 2
und 2b Runde 5, Commit `3cc223d`: Die Korrektur erklärte alle vier Kopien der
leeren Außengrenzen einschließlich des Helfers für ersetzt und
`app/resolver.py` für „ganz englisch“. Der Aufnahmewege-Test verdrahtete
`DailyCloseSync(repository, EmptyDailyCloseProvider())` jedoch weiterhin
parallel zum neu eingeführten `empty_daily_sync(repository)`. Im Resolver blieb
zugleich der deutsche strukturierte Event-Identifier
`resolve_isin_andere_boerse` sowie der nichtsprechende Bezeichner `q`; im
ebenfalls vollständig inventarisierten `tests/test_resolver.py` blieb `e`.
Der Bezeichner-Scan erfasste den Log-Event als String grundsätzlich nicht.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21 Teil 3
Runde 8, Commit `f65dfcc`: Der Entwurf behauptete, „zwei Stellen im Produktcode“
versprächen noch die inzwischen gestrichene Handzuordnung, und nannte daneben
nur README und Service-Kommentar. Projektweit blieben dieselben Zusagen jedoch
mindestens in `app/repository.py`, `app/resolver.py`, `app/db.py` und
`docs/rest-core-contract.md` stehen. Die angekündigte Dokumentationskorrektur
hatte ihren behaupteten Scope damit nicht vollständig inventarisiert.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 9, Commit `7321bfc`: Nach dem Befund aus Runde 8 trug der Entwurf
den Titel „Dokumentationsinventur, diesmal vollständig“ und nannte einen breiten
Scan über Produktcode, Tests, Dashboard, Dokumentation und Plugin-API. Dennoch
fehlten mindestens `app/exchanges.py:167`, `tests/test_exchanges.py:82`,
`tests/test_openfigi_lookup.py:36`, `app/services/quote_service.py:171-177` und
die weiterhin widersprechende Zusage im selben Handoff berührten
`_tickets/T-21-identitaet-mic-und-ticker.md:480`.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 10, Commit `2421f65`: Die Korrektur erklärte, der Entwurf nenne
jetzt nicht mehr das Prädikat „vollständig“, ließ aber unmittelbar über dieser
Aussage die Überschrift „Dokumentationsinventur, diesmal vollständig“ stehen.
Zugleich sollte der TypeScript-Parser „ersatzlos“ entfallen und der Core die
einzige Parserquelle sein, ohne den bereits produktiven ISIN-Parser
`dashboard/src/api/paths.ts:isIsin` und dessen Routing in
`useInstrumentActions.add` als zu entfernende Stellen zu erfassen.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 13, Commit `8f0e9b4`: Die Übergabe erklärte die
Collector-Mitgliedschaft als ausschließlich am Collector-Eintrag geführt und
damit „nachzählbar“ zu einer Quelle. Der übergebene Entwurf schloss
`collectors` an jeder Börse zunächst ausdrücklich aus, verlangte aber wenige
Absätze später genau solche parallelen Listen an `XNAS`, `XNYS`, `ARCX`,
`XASE` und `BATS`. Gleichzeitig blieb die angeblich zurückgebaute
Mehrfachalias-Anforderung als „Suffixformen im Plural“ in der Begründung des
Descriptors stehen.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 17, Commit `201c960`: Die Übergabe erklärte den Entwurf „an der
Wurzel umgebaut“ und `identity_status` für ersatzlos entfallen. Das kanonische
Ticket behielt jedoch als aktuelle Regeln „der Rest bleibt offen“, den
zweiwertigen Status, offene NULL-Zeilen und die spätere Handzuordnung; seine
weiterhin grünen Verifikationsbelege prüfen genau diesen alten Zustand. Im
übergebenen Entwurf stand zugleich „Keine Schemaänderung“, obwohl derselbe
Entwurf einen getrennten Berichtsspeicher, den Ausbau der Statusspalte und
`NOT NULL` verlangt, und der neue Vierer-Schnitt behielt darunter die alten
Teilnummern bei.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 18, Commit `c9d6670`: Die Übergabe erklärte die überholten Stellen
des kanonischen Tickets als Historie markiert und nannte ausdrücklich den in
Runde 17 beanstandeten Schlusssatz. Dennoch blieben im aktuellen Scope „offene
Zuordnungen sichtbar“, im Entscheidungskasten zwei Zustände einschließlich
offener Zuordnungen, im AAPL-Block `legacy_unresolved`, im Detailabschnitt die
Zuordnung von Hand und genau der beanstandete Schlusssatz aktiv und
ungestrichen. Der neue Warnhinweis stand nur vor den Fußnoten und erfasste
diese anderen Abschnitte nicht.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 19, Commit `20a4422`: OUTBOX und Commit meldeten das Ticket als
„einstimmig“ und die Gegenprobe als leer, begrenzten die Suche aber auf den
Bereich oberhalb des Fußnotenblocks. Im weiterhin aktiven Detailabschnitt
forderte `_tickets/T-21-identitaet-mic-und-ticker.md:481` unverändert einen
„Weg zur Zuordnung von Hand“. Besonders eindeutig war der Fund, weil die
Dokumentationsinventur im selben übergebenen Entwurf genau diese Ticketstelle
selbst aufführte, ohne sie zu korrigieren. Die Fundliste war damit vorhanden;
die Fachregel wurde erneut nicht über den ganzen kanonischen Text angewendet.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 20, Commit `5970806`: OUTBOX und Commit erklärten alle vier
Reviewbefunde für umgesetzt und `/ready` ausdrücklich für im Pending-Zustand
erreichbar. Die neu formulierte zentrale Allowlist erlaubte aber nur statische
UI, `/health`, Vorschau, Bestätigung und Bericht; `/ready` fehlte unmittelbar
vor seiner eigenen `200`-Anforderung. Zugleich wurde aus dem vorhandenen
Dockerfile-Kommentar ungeprüft abgeleitet, der Docker-`HEALTHCHECK` starte den
Container neu und steuere Traffic, obwohl die Projektkonfiguration nur einen
Health-Status und `unless-stopped` definiert. Die Korrektur übernahm damit
erneut das besprochene Beispiel, ohne seine neue Regel gegen die angrenzenden
Vertragsverbraucher und ihre tatsächliche Betriebssemantik zu prüfen.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 21, Commit `28ba9f9`: OUTBOX erklärte beide Round-20-Befunde für
umgesetzt und die Allowlist als „Liste aus Methode und Pfad“. Tatsächlich waren
nur `GET /health` und `GET /ready` konkret; statische UI, der neue
Healthcheck-Endpunkt sowie Vorschau, Bestätigung und Bericht blieben
unbenannte Platzhalter. Zugleich sollten Bedeutung, Modell, README und Tests
unverändert bleiben, obwohl die README den Docker-Healthcheck weiter an
`/ready` bindet und nur eine nicht erreichbare DB als 503-Ursache kennt;
Docker-Kommentar und Test-Docstrings wiederholen die gerade widerlegte
Restart-/Healthcheck-Erklärung. Die punktuelle Korrektur inventarisierte ihre
unmittelbaren Vertragsverbraucher erneut nicht vollständig.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 22, Commit `a9fde37`: OUTBOX und Commit bezeichneten die
Methode/Pfad-Allowlist als vollständig und ihre statischen Pfade als
abschließende Wiedergabe von `dashboard/dist`. Die Liste ließ jedoch das von
`dashboard/index.html` tatsächlich angeforderte `/stockinfo-icon.svg` aus.
Außerdem inventarisierte sie den vorhandenen Dev-Router
`dashboard/vite.config.ts:apiPrefixes` nicht; ohne `/migration` liefert Vite
dem verpflichtenden Migrations-UI-Ablauf das SPA-HTML statt der Backend-Antwort
— exakt der bereits in T-04 dokumentierte Ausfallmodus. Der aus einer
Driftkorrektur entstandene neue Routenvertrag wurde damit erneut nur gegen
seine neuen Verbraucher, nicht gegen die vorhandenen Routingquellen geprüft.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 23, Commit `fd79566`: OUTBOX erklärte nun alle drei Routingquellen
für abgeglichen und ersetzte die unvollständige statische Pfadliste durch eine
Ableitung aus allen Dateien in `static_dir`. Diese Ableitung enthält zwar
`/index.html`, aber nicht den von `StaticFiles(html=True)` bereitgestellten
URL-Alias `/`, über den das Dashboard normalerweise geöffnet wird. Auch der
neue Test enumeriert nur Dateien und Assets und hätte den gesperrten Einstieg
deshalb nicht bemerkt. Die Korrektur beseitigte den konkret fehlenden siebten
Dateinamen, ohne die vollständige URL-Semantik des berührten Static-Mounts zu
inventarisieren.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Runde 26, Commit `083414c`: OUTBOX erklärte alle vier Befunde ohne
Auslassung umgesetzt und Ticket #2h2 den Alias in Python, OpenAPI und
TypeScript als optional. Das TypeScript-Interface verlangte die Property aber
weiterhin; der neue Typ-Test belegte nur `null`, nicht die ebenfalls zugesagte
fehlende Form. Gleichzeitig setzte die Korrektur eine konkrete aliaslose
US-Börse und den Sammelcode `US` auf dasselbe leere Alias-Ergebnis. Der
Resolver behandelte daher jeden punktlosen Treffer als bevorzugt und konnte
für `XNAS` einen früheren `PCX`/`ARCX`-Treffer trotz eines späteren
`NMS`/`XNAS`-Treffers wählen. Erneut waren die genannten Beispiele grün,
während benachbarte Verbraucher und Reihenfolgen des geänderten Vertrags
ungeprüft blieben.

**Neuer Beleg wegen ausdrücklich falscher Gleichheitsbehauptung:** T-21 Teil 3
Runde 27, Commit `43003a9`: OUTBOX erklärte, `_at_exchange` verwende dieselbe
Yahoo-Abbildung, die `_identity` demselben Treffer anschließend als MIC gebe.
Die Abbildung war zwar dieselbe, ihre Vorrangregel aber nicht: `_identity`
benutzt den Yahoo-Code ausschließlich bei suffixlosen Symbolen, `_at_exchange`
benutzte ihn bei jedem nicht zur Präferenz passenden Suffix. So wählte
`DEFAULT_EXCHANGE=XNAS` einen ersten Treffer `WRONG.DE`/`NMS` als NASDAQ und
speicherte ihn unmittelbar danach als `WRONG`/`XETR`, obwohl ein gültiger
suffixloser `NMS`-Treffer folgte. Die Korrektur teilte die Mappingtabelle, aber
nicht die vollständige Fachregel, die sie anwendet.

**Neuer Beleg:** T-21 Teil 3 Übergabe 1, Runde 28, Commit `192ac94`: Nach den
wiederholten Naming-Korrekturen führte der neue zentrale Produkt-Helper
`mic_for_alias` mit `d` erneut einen nichtsprechenden Ein-Buchstaben-Bezeichner
ein. Die fachliche Zentralisierung ist korrekt; der vollständige hinzugefügte
Diff wurde dennoch nicht gegen dieselbe bereits mehrfach beanstandete
Naming-Regel geprüft.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 2A, Runde 30, Commit `d361fbc`: OUTBOX und Ticketfußnote
erklärten den durch `executescript` ausgelösten Vorab-Commit für beseitigt und
den Rollback-Test als Beleg für „alles oder nichts“. Korrigiert wurde nur die
Tabellenanlage in `app/migration.py`; `app/db.py:198` ruft innerhalb derselben
Migration weiter `executescript(_IDENTITY_INDICES)` auf. Eine erzwungene
Indexfehler-Gegenprobe warf zwar eine Exception, ließ Daten, Berichtstabelle
und gehärtetes Schema aber bereits dauerhaft committed zurück.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 2A, Runde 31, Commit `d06a6a1`: OUTBOX erklärte „alle sieben
Befunde umgesetzt“. Der Callback-Befund aus Runde 30 blieb jedoch als bewusst
festgeschriebenes Verhalten bestehen: `MigrationGate.release()` setzt den
Gate vor dem Callback frei und schluckt dessen Fehler. Eine Gegenprobe über den
echten Lifespan mit fehlschlagender `RefreshScheduler.start()` erhielt `200`
auf die Bestätigung und danach `200/ok` auf `/ready`, obwohl kein Scheduler
lief. Der als Integrationsbeleg benannte Test ersetzt den Produktcallback
weiterhin durch `lambda: ...`; der neue Callbackfehler-Test erklärt gerade das
falsche Freigabeverhalten zur Erwartung. Zugleich behauptete die Übergabe, der
REST-Test belege Börse, Gattung und Währung, obwohl seine Fixture alle drei
Felder `NULL` lässt und der Test nur `None == None` zwischen Vorschau und
Bericht vergleicht.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 2A, Runde 32, Commit `21865c0`: OUTBOX erklärte alle vier
Befunde umgesetzt und führte `startup_failed` als belastbaren vierten Zustand
ein. Der neue Retry umging jedoch die bestehende Einmal-Verriegelung vollständig:
Eine Barrier-Gegenprobe mit acht parallelen Bestätigungen rief den
Scheduler-Callback achtmal. Zugleich setzte `release()` `pending=False`, bevor
der Start lief, und `startup_failed=True` erst nach dessen Fehler; ein
angehaltener Callback ließ `/ready` und `/operational` deshalb erneut den
Normalzustand sehen, obwohl der Scheduler noch nicht gestartet war. Die
kanonischen Gate- und Response-Docstrings beschrieben daneben weiter drei
Zustände beziehungsweise nur zwei 503-Gründe.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 2A, Runde 33, Commit `2c9f454`: OUTBOX erklärte die
Dokumentation des neuen Zustands für vollständig und nannte Modelle, Ticket
und Spec. Im direkt ausführenden `app.main` behauptete `/ready` weiter, es gebe
nur zwei 503-Gründe, und `/operational` beschrieb 503 nur für den DB-Ausfall.
Die zugleich geänderte Spec listete DB- und Scheduler-Ausfall beide als
`degraded`, erklärte sie einen Absatz später aber allein über `status` für
unterscheidbar. Die neue Tabelle war richtig; ihre unmittelbar angrenzenden
Aussagen blieben auf dem alten Vertrag.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 2B, Runde 36, Commit `7d9c671`: OUTBOX erklärte alle vier
Befunde umgesetzt. Fachlich stimmte das, aber der Korrekturdiff führte nach den
Naming-Runden 3 bis 5, 7, 8 und 28 erneut deutsche Bezeichner in Produkt und
Tests ein: unter anderem `wartezeit`, `nachfrage`, `runde`, `abstaende`,
`freigeben`, `_MINDESTLAENGE`, `rohwert`, `satz` und `gleich`. Die behauptete
Vollständigkeit prüfte den neuen Diff damit wieder nicht gegen dieselbe bereits
mehrfach beanstandete Projektregel.

**Neuer Beleg — die Fundliste selbst war unvollständig:** T-21 Teil 3 Übergabe
2B, Runde 37, Commit `556d148`. Diesmal war der Korrekturdiff sauber, aber die
OUTBOX legte eine Liste der verbliebenen deutschen Bezeichner in
`tests/test_migration_endpoints.py` und `tests/test_migration_guard.py` vor und
bat um eine Scope-Entscheidung. Beides war falsch. Die Liste stammte aus einer
`grep`-Suche nach erratenen Wörtern und übersah `_ERWARTETE_ANTWORTEN`, `m`,
`p`, `vorher`, `nachher`, `gestartet`, `zweite`, `pfad` und `außerhalb`;
Codex' AST-Inventar fand sie sofort. Und die Scope-Frage war längst
beantwortet: Die Naming-Regel sagt „was ohnehin angefasst wird, zieht mit".

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 3, Runde 39, Commit `909b11e`: OUTBOX erklärte den Aufnahmeweg
für fertig und atomar mit dem Vertrag. Der verpflichtende Fall `AAPL.XNAS`
wurde zwar zu `(AAPL, XNAS)` geparst, danach aber auf den aliaslosen String
`AAPL` reduziert und durch den alten Symbolpfad geschickt. Auf leerem Bestand
antwortete der neue Endpunkt deshalb mit HTTP 500; bei einem vorhandenen
`AAPL/XNYS` sogar mit HTTP 200 und dem **falschen MIC XNYS**. Kettentest und
Smoke prüften ausschließlich eine Börse mit Alias (`XETR`/`DE`) und konnten
die im Entwurf ausdrücklich genannte aliaslose Klasse nicht sehen. Parallel
versprach das Artefakt `quote.ticker`/`quote.mic` als Pflicht, während das neu
erzeugte OpenAPI beide weiterhin optional und nullable auswies.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 3, Runde 42, Produktstand `d119449`: OUTBOX erklärte alle fünf
Befunde aus Runde 39 für umgesetzt. Der normale Repository-Lookup reichte die
neue `(ticker, mic)`-Identität weiter, sein `IntegrityError`-Retry rief dieselbe
Funktion aber weiterhin ohne beide Werte auf; ein erzwungen verlorenes Rennen
für aliasloses `AAPL/XNAS` ohne ISIN endete deshalb erneut mit HTTP 500 statt
`created=false`. Der neue Test namens „jedes Pflichtfeld“ erfasste zugleich nur
`quote` und `instrument` und prüfte bewusst nicht die OpenAPI-`required`-Liste.
Dadurch blieben acht im Artefakt verpflichtende Felder im Antwortschema
optional sowie `daily.currency` und `history.currency` zusätzlich nullable.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-21
Teil 3 Übergabe 3, Runde 43, Commit `385b819`: OUTBOX erklärte alle vier
Befunde aus Runde 42 für umgesetzt und den zweiten Identitätskonflikt für vom
HTTP 500 befreit. Geändert war jedoch nur die Exception im Repository; Service
und Router behandelten sie nicht. Die ausdrücklich verlangte echte
Intake-Gegenprobe fehlte, und derselbe Aufbau antwortete weiter mit 500. Auch
die als eine DRY-Quelle bezeichnete `PRECHECKED_CORE_FIELDS`-Liste lief
parallel zu einem positionalen Wertetupel: Ein viertes, laut Artefakt
zulässiges Feld ließ den neuen Wächter grün, aber `zip(strict=True)` mit
`ValueError` abbrechen.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-22
Runde 1, Commit `20af8fa`: Übergabe und Ticket erklärten
`DailyCloseProvider` und `FxProvider` zu den zwei Verträgen, die „nirgends
standen“. Tatsächlich existierten bereits
`app.services.daily_sync.DailyCloseProvider` und
`app.services.fx_service.FxRateProvider`, und alle Verbraucher importierten
weiter diese alten Protokolle. Die neu in `app.providers.base` angelegten
Typen waren daher unbenutzt; statt zwei fehlender Verträge gab es nun je zwei
Sources of Truth.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-27b
Runde 5, Commit `cd3e2f3`: OUTBOX erklärte „alle drei umgesetzt“,
`real_ok`/`only_real` samt zwei Betriebsarten aus der öffentlichen API entfernt
und in der Integrationsdatei vier echte Netzfälle belassen. Die beiden Namen
waren tatsächlich weg, ihre Fachzusage aber nicht: `testing/__init__.py`
versprach weiter „zwei Betriebsarten“, `Scenario`, `ScenarioRunner`,
`test_scenarios.py` und `test_prices_file.py` erklärten weiter Aufzeichnungen,
Replay beziehungsweise den kommenden T-27b-HTTP-Runner zum aktuellen Modell.
Die aktive Verify-Matrix und Fußnoten von T-27a wiederholten dieselbe
aufgehobene Zusage. Zugleich fragte
`test_ein_sammelcode_liefert_keinen_treffer` in der angeblich rein echten
Integrationsdatei absichtlich **nicht** den Dienst und duplizierte den
gleichnamigen Unit-Fall. Die Korrektur entfernte die besprochenen Bezeichner,
nicht alle Erzeuger und Verbraucher ihrer Regel.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-23
Runde 2, Commit `e35d190`: OUTBOX erklärte „alle fünf umgesetzt“, beide
eingebauten Quellen würden nun ihre Plugin-Klassen benutzen und alle zehn
Integrationstests einen echten Dienst berühren. Tatsächlich endeten die neuen
yfinance-Pfade für `daily` und `fx` beim ersten Core-Aufruf mit
`AttributeError`; justETF und yfinance-Metadaten blieben native Sonderwege.
Der angeblich verschobene EUR→EUR-Fall stand weiter in der Integrationsdatei,
der neue justETF-US-Fall brach ebenfalls vor dem Provider ab, und `/sources`
meldete ein wegen fehlender Datei verworfenes Plugin weiterhin als
`configured` und `usable`. Die punktuellen Resolver-/Quote-Erfolgswege wurden
als vollständige Rollen-, Diagnose- und Testumstellung berichtet.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-23
Runde 3, Commit `4e23cde`: Übergabe und Docstrings erklärten den Widerspruch
zwischen `/sources` und Bauweg durch „eine Auswertung“ beseitigt. Beide Wege
riefen `_evaluate` aber weiterhin getrennt auf und konstruierten je eine neue
Plugin-Instanz. Eine Quelle, deren erste Konstruktion gelang und deren zweite
warf, lief daher produktiv und wurde gleichzeitig als unbrauchbar gemeldet.
Die gemeinsame Funktion beseitigte duplizierten Code, nicht die zwei
unterschiedlichen Laufzeitzustände.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-23
Runde 4, Commit `adcb505`: OUTBOX meldete einen Laufzeit-Snapshot,
wirklich aufgerufenen `Source.close()` und den entschiedenen festen
Installationsweg. Tatsächlich erzeugte `describe_chain` für jede noch nicht
gebaute Rolle weiter Wegwerf-Instanzen; ein erneuter Rollenbau überschrieb die
Close-Liste der noch laufenden alten Kette, und `close_all()` fragte den
Adapter statt der darunterliegenden `Source`, sodass die Gegenprobe keinen
einzigen Close-Aufruf sah. Parallel ignorierte der Parser das dokumentierte
`plugins.packages`, akzeptierte im abweichenden Top-Level-Feld unversionierte
Namen und Git-URLs und gab sie an pip weiter. Die konkret ergänzten
Mechanismen waren vorhanden, ihre behaupteten End-to-End-Regeln nicht.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-23
Runde 5, Commit `d4f9036`: Der Installer fing pip-Fehler ab und die Übergabe
meldete erneut, ein schlechter Eintrag koste die guten nicht. Der anschließend
konfigurierte, aber nicht geladene Pluginname lief jedoch in
`UnknownSourceError`; selbst mit `openfigi` dahinter brach der FastAPI-Lifespan
ab, bevor `/health` erreichbar war. Parallel hieß der neue Registryzustand
„laufende Kette“, obwohl `/sources` vor dem ersten Bau eine Quelle mit
`configuration_problem() == 'Datei fehlt'` als `configured=true` ohne Grund
meldete. Die lokalen Teilmechanismen erfüllten ihre Regeln, die nachgelagerten
Verbraucher widerlegten beide End-to-End-Behauptungen.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-37,
Commit `d313318`: OUTBOX meldete, Quote- und FX-Dienst würden nun beide die
tatsächlich antwortende Quelle nennen. Für einen angereicherten ETF ersetzte
`_enrich_etf` die Kursquelle `prices-file-quote` jedoch weiter durch
`metadata-file`; der neue Test umging den Pfad mit `type="stock"`. Der
FX-Dienst bekam gar keinen neuen Test und wurde vom Smoke nicht aufgerufen.
Die lokale Konstante war entfernt, die fachliche Herkunft über alle Verbraucher
aber nicht vollständig verfolgt.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-36/
T-37 Runde 3, Commit `cc0f028`: OUTBOX erklärte, ein AST-/Bash-/TS-Inventar
habe alle Bezeichner in den berührten Dateien erfasst und der Massen-Rename
habe sämtliche Prosaschäden repariert. Das frische AST-Inventar fand weiterhin
unter anderem `KenntNichts`, `antwort`, `eintrag`, `rolle`, `fehlend`,
`gefragt`, `woher`, `typ`, `stunde` und `gesehen`; im eingebetteten Python
blieb `unkonfiguriert`. Zugleich standen neue Mischsätze wie „zweimal built",
„gar nichts built“, „Kettennamen unusable“ und `NamedQuoteSource` mitten in
deutscher Prosa. Die Fundliste war trotz des richtigen Werkzeugs nicht gegen
ihren behaupteten Scope und der Diff nicht gegen die angekündigte
Prosa-Gegenprobe geprüft worden.

**Unmittelbare Wiederholung in der Folgerunde:** T-36/T-37 Runde 4, Commit
`c44b932`: OUTBOX erklärte erneut, das Inventar sei über alle berührten Dateien
gelaufen und alles sei „einschließlich des eingebetteten Python“ nachgezogen.
Der neue FX-Test führte dabei selbst `frisch`, `aus_dem_cache` und
`ausgefallen` ein. Im berührten Vertikaltest blieben unter anderem `woher`,
`gefragt`, `rolle`, `fehlend` und `e` sowie die bereits wörtlich gemeldeten
Prosaschäden „gar nichts built“ und „Kettennamen unusable“; im Smoke blieb
`unkonfiguriert`, im Dashboard-Test `_fall`. Der behauptete Scan kann seinen
angegebenen Scope damit erneut nicht geprüft haben.

**Dritte Wiederholung trotz ausdrücklich gewechseltem Verfahren:** T-36/T-37
Runde 5, Commit `adc8907`: OUTBOX erklärte nun, statt einer Markerliste alle
selbst vergebenen Namen per AST inventarisiert und die ungefilterte Liste
gelesen zu haben. Im berührten TypeScript-Test standen dennoch `felder`,
`hervorgehoben` und `f`; in den eingebetteten Python-Blöcken des ebenfalls
berührten Smoke-Scripts blieben `c`, `d`, `r` und `s` sowie die
Einbuchstaben-SQL-Aliase `i`, `o` und `q`. Das Python-Inventar der `.py`-
Dateien war diesmal sauber, aber die behauptete Vollständigkeit wurde nicht
für jede genannte Sprachschicht mit dem passenden Parser eingelöst.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-31
Runde 5, Commit `1133dd9`: OUTBOX meldete die Capability-Regel „durch alle
Rollen" und erklärte ausdrücklich, eine leere `SUPPORTED_TYPES`-Menge bedeute
„nichts zugesagt". `ResolverAdapter` prüfte die Antwort aber nur unter
`and declared_types`; gerade die leere Menge schaltete den Riegel daher aus
und ließ einen nicht deklarierten `crypto`-Treffer passieren. Für genau diesen
Randfall gab es keine Gegenprobe.

**Neuer Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-37
Runde 3, Commit `b464471`: OUTBOX und Commit erklärten, der Lade-Rand lasse
keinen Benutzerwert mehr entkommen und prüfe jeden Listenpunkt. Geprüft waren
die vier wörtlich genannten Mutanten. Daneben warfen `identity: nope`, ein
numerischer Name/Typ und skalare Einträge in `history.closes` oder `fx_rates`
weiter aus dem Konstruktor; falsey Listen an Objektblöcken verschwanden durch
`value or {}`. Die Beispiele waren geschlossen, die behauptete Schema-Regel
nicht inventarisiert.

**Unmittelbare Wiederholung nach der Konsolidierungsansage:** T-37 Runde 4,
Commit `1c70425`: Die Übergabe erklärte die fünf neuen `_require_*`-Funktionen
zur vollständigen Validator-Schicht. Die inneren Identitätsfelder benutzten
keine davon; Zahlen liefen weiter zuerst durch `float()`. Numerische
Ticker/MIC/ISIN warfen deshalb aus dem Konstruktor, Bool und Zahlenstring
galten als TER, ein großer Integer warf in Metadaten sowie später in Quote,
Daily und FX. Die Schicht war angelegt, aber nicht über alle bereits
ausgeschriebenen Verbraucher verfolgt.

**Neuer Beleg:** T-41 Runde 1, Commit `115ac6c`: Die Quote-Kaskade gab als
`name` stets die erste konfigurierte Quelle aus und erklärte im Docstring,
die tatsächliche Herkunft stehe an der einzelnen Antwort. `RawQuote` trägt
diese Herkunft jedoch nicht. Fiel die erste Quelle durch und lieferte eine
zweite `RawQuote` samt Name, Gattung und Börse, übernahm der Core diese
Metadaten, schrieb als `quote.source` aber den Namen der ersten Quelle. Die
Reihenfolge funktionierte; der bestehende Herkunftsvertrag wurde nicht durch
den neuen Composite bis zu seinem Verbraucher verfolgt.

**Unmittelbare Wiederholung an derselben Herkunft:** T-43 Runde 1, Commit
`50b7341`: Die Statuszeile versprach mit `Kurse: yfinance` die Quelle der
angezeigten Kurse, las aus `/sources` aber nur den ersten einsatzbereiten
Eintrag der Kette. Beim Rückfall auf `yaml-file` blieb die sichtbare Aussage
damit falsch. Ticket und OUTBOX behaupteten zusätzlich, die tatsächliche
Herkunft stehe über `RawQuote.source` im Drilldown; am REST-Rand bezeichnet
`QuoteResponse.source` jedoch die Metadatenherkunft, und die Quote-Tabelle
speichert den Kursprovider nicht. Der vorhandene Zwei-Quellen-Test erwartete
ausdrücklich den ersten Namen und konservierte so erneut genau den
Herkunftsfehler aus T-41.

**Unmittelbare Wiederholung bei einem gemeinsamen Validator:** T-44 Runde 2,
Commit `5668dc7`: OUTBOX und Test erklärten alle fünf `{isin}`-Routen für
vollständig dokumentiert. `normalize_isin()` hatte aber zwei weitere direkte
Verbraucher in `/analyze` und im PUT zum Nachtragen einer ISIN; beide lieferten
zur Laufzeit den neuen top-level `ErrorDetail`, veröffentlichten weiter
`HTTPValidationError`. Der neue Test leitete sein Inventar ausschließlich aus
dem Pfadplatzhalter `{isin}` ab und konnte diese Verbraucher prinzipbedingt
nicht finden. Außerdem ersetzte dieselbe Deklaration bei Daily und History den
gesamten 422-Vertrag durch `ErrorDetail`, obwohl ungültige Query-Parameter dort
weiter `HTTPValidationError` beziehungsweise `{"detail": "…"}` liefern. Die
Korrektur schloss die besprochenen fünf Pfade, ohne Erzeuger und alle
Antwortvarianten des gemeinsamen Statuscodes zu inventarisieren.

**Neuer Beleg:** T-42 Phase B Runde 3, Commit `f75df2d`: OUTBOX und Ticket
meldeten sechs Anzeigebefunde als vollständig behoben. Die Desktop-Tabelle
blendete bei `isin_only` den technischen ISIN-Platzhalter mit `symbolOf()` aus;
die mobile `InstrumentCard` zeigte denselben Wert weiter unverändert als
Börsensymbol. Gleichzeitig wurde die Typ-Auszeichnung gerade wegen einer
vergessenen zweiten Darstellungsstelle repariert, ihre neue Farbzuordnung aber
wieder nahezu identisch in Tabelle und Karte angelegt. Die sichtbaren Beispiele
waren korrigiert, die gemeinsame Darstellungsregel erneut nicht über alle
Verbraucher und nicht auf eine Wissensquelle gezogen.

**Unmittelbare Wiederholung:** T-42 Runde 7, Produktstand `20b4b7b`: Der
Mixin-Refactor `d3f1949` entfernte zusammen mit der doppelten Typregel auch die
kurz zuvor gemessenen `.caret-col`-/`.caret-only`-Regeln; das Ticket meldete
deren Mindestbreite am finalen Stand dennoch weiter als behoben. Beim späteren
Verschieben der Platzhaltererklärung in die Spaltenköpfe verlor zugleich die
mobile Karte ohne Symbol-Spaltenkopf genau diese Auskunft wieder und zwei neue
Katalogschlüssel duplizierten die vorhandenen Gründe. Derselbe Umbau schloss
die sichtbare Desktopstelle, ohne finalen Stand, zweite Darstellungsform und
Katalogquelle gemeinsam zu inventarisieren.

**Unmittelbare Wiederholung in der Korrektur:** T-42 Runde 8, Produktstand
`09f37d0`: OUTBOX und Ticket erklärten `#2b` ehrlich aus dem Smoke entfernt und
die Prozesschronik aus den Kommentaren beseitigt. Die erste Kopfzeile des
Scripts führte `#2b` dennoch weiter und ließ `#4b` aus; unmittelbar darunter
standen „fünf Fragen" vor sechs Einträgen. Neue Kommentare beschrieben zudem
weiter den Tausch der Check-IDs und „Mikes Einwand". Das Laufverhalten war
richtig, aber die behauptete Kommentar- und Kopfinventur erneut nur an den
besprochenen Stellen erfolgt; Codex heilte die technische Prosa in `4905877`.

**Unmittelbare Wiederholung:** T-47 Runde 2, Commit `aa239fb`: OUTBOX erklärte,
Ticketnummer, Teilstrecke, Person, Datum und „erste Fassung" seien im gesamten
neuen Diff entfernt. Der neu ergänzte Lock-Kommentar und der parallele
HTTP-Test konservierten stattdessen das Review-Messergebnis „13 von 20"; der
Testkopf erklärte zusätzlich den noch nicht gebauten Teilstand. Die
besprochenen alten Stellen waren sauber, die im selben Korrekturdiff neu
entstandene Prosa nicht. Codex heilte sie verhaltensneutral in `ab056d5`.

**Verallgemeinerung:** Eine Fundliste ist eine Vollständigkeitsbehauptung. Wird
sie mit `grep` erhoben, behauptet sie nur, dass die geratenen Suchwörter
vorkommen — nicht, dass es keine weiteren gibt. Wer über einen Bezeichnerscope
redet, zählt ihn vorher aus dem AST auf. Und wer eine Regelfrage stellt, liest
zuerst die Regel: Sie stand vollständig in der Skill `code-standards`, die in
dieser Runde nicht geladen war. Seither steht die Kernaussage in `CLAUDE.md`,
weil die lädt, ohne dass jemand daran denkt.

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

**Zweite Prüffrage — das Orakel.** Ein Großteil der Belege unten ist derselbe
Griff: Die Gegenprobe ruft die Funktion auf, die sie prüfen soll. Deshalb vor
jeder Vollständigkeitsbehauptung zusätzlich fragen: *Woher kommt der
Erwartungswert?* Zulässig sind ein **Literal** und eine **hier eigens
ausgeschriebene Regel**; unzulässig ist jeder Aufruf der geprüften Logik. Eine
Tabelle nachzuschlagen ist erlaubt — sie ist Daten. Die Regel auf sie
anzuwenden ist es nicht.

Der DRY-Reflex zeigt hier in die falsche Richtung: Im Orakel ist die Dopplung
der **Zweck**. Wo sie absichtlich steht, gehört ein Satz dazu, der das sagt —
sonst zentralisiert sie der nächste Durchgang weg.

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

**Neuer Beleg:** T-21 Teil 3 Übergabe 1, Runde 25, Commit `0f79eec`:
`T-21-smoke.sh`, `T-21b-smoke.sh` und
`tests/test_identity_creation.py` ersetzten ihre bisher getrennt formulierte
Vorwärtsrechnung durch einen Aufruf der neuen Produktfunktion
`provider_alias`. Damit bestätigen Produkt und angebliche Gegenprobe wieder
dieselbe Implementierung. Zusätzlich behauptet
`test_beide_eingabeformen_treffen_dieselbe_boerse`, `EUNL.XETR` geprüft zu
haben, konstruiert dieses Ergebnis aber nur als Tupel aus der
`EXCHANGES`-Mitgliedschaft; kein MIC-Eingabeweg wird ausgeführt.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2A, Runde 30, Commit `d361fbc`:
`test_jeder_erlaubte_pfad_antwortet_auch_wirklich` akzeptiert jede Antwort,
solange sie nicht exakt `503` mit `migration_pending` ist. Ein in die
Allowlist eingetragener, aber nicht existierender Pfad liefert `404` und der
Test bleibt grün. Damit prüft der angekündigte Routentabellen-Test nur die
Beschriftung „nicht vom Guard gesperrt“, nicht die Zusage, dass der erlaubte
Endpunkt tatsächlich existiert und erfolgreich antwortet.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2A, Runde 31, Commit `d06a6a1`:
`test_vorschau_und_bericht_nennen_genug_zur_neuerfassung` soll die neu durch
REST geführten Felder Börse, Gattung und Währung absichern. Seine Fixture
setzt aber keines davon; der Test vergleicht anschließend nur Bericht gegen
Vorschau. Werden die Felder in beiden Mappings wieder weggelassen, bleibt
`None == None` grün. Der Erwartungswert kommt damit aus dem zweiten zu
prüfenden Pfad statt aus einem ausgeschriebenen, nichtleeren Orakel.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2B, Runde 35, Commit `5b0fa31`:
`test_jede_kennung_hat_einen_satz` verspricht für jeden Ablehnungsgrund einen
Satz in beiden Sprachen, `_reason_keys()` liest aber ausschließlich die
Schlüssel. Eine In-Memory-Mutation des ersten englischen Werts auf `''` ließ
die Schlüsselmenge unverändert und alle drei Katalogtests grün. Der ergänzende
Vue-Test prüft nur einen einzigen deutschen Grund; leere Texte der übrigen
Codes oder der englischen Sprache bleiben unbeobachtet.

**Neuer Beleg:** T-36/T-37 Runde 3, Commit `cc0f028`: Smoke `#0b` speist drei
Fehler ein, verlangt danach aber nur `status != 0 || output != leer`. Der
nichtnumerische Kurs lässt `float(...)` vor der Ausgabe aller gesammelten
Befunde abbrechen; allein der Traceback genügt trotzdem für die Erfolgsmeldung
„Prüfziffer, Sammelcode und unbrauchbarer Kurs erkannt“. Keiner der drei
behaupteten Befunde wird einzeln verlangt. Ebenso fragen vier
Drilldown-Assertions gelöschte i18n-Schlüssel ab; vue-i18n liefert die Kennung
unter Warnung zurück und `not.toContain(...)` bleibt ohne existierenden
Vergleichstext grün.

**Neuer Beleg:** T-37 Runde 3, Commit `b464471`: Der neue Test
`test_die_history_wird_auf_das_fenster_beschnitten` erzeugte das richtige
leere Zeitfenster, schrieb aber `NotFound` als Erwartung fest. Der öffentliche
`DailyCloseSource`-Vertrag sagt ausdrücklich, dass ein bekanntes Papier ohne
Punkte im Fenster eine leere `DailySeries` liefert; `NotFound` bedeutet
hingegen unbekanntes Papier. Der Test unterschied die Tage, bestätigte aber
die falsche Ergebnisart.

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

**Neuer Beleg:** T-22 Runde 1, Commit `20af8fa`: Das neue Smoke-Script
kommentierte ausdrücklich, seine Schlussmarke verhindere einen grünen
Teil-Lauf. Scheitert `startServer()` jedoch vor `report()`, kehrt nur die
Check-Funktion mit 1 zurück; `runChecks()` läuft ohne `set -e` weiter,
`COUNT_FAIL` bleibt unverändert und der Erfolg verlangt keine erwartete Anzahl
von fünf Checks. Ein später vollständig laufender Rest kann deshalb mit vier
Checks und „keine Fehler" grün enden.

**Neuer Beleg:** T-27a Runde 1, Commit `6121a94`: Der öffentliche
Szenario-Runner liefert bei `only_real=True` und null mit `real_ok`
freigegebenen Fällen eine leere Finding-Liste — dieselbe Erfolgsform wie nach
einem vollständigen grünen Lauf. Der Test schreibt dieses Verhalten sogar als
Erwartung fest. T-27b könnte damit „Real" melden, ohne einen Anbieter gefragt
zu haben.

**Neuer Beleg:** T-37, Commit `d313318`: `checkTestData` entscheidet allein
an leerem Standardoutput über Erfolg. Wirft der eingebettete Parser etwa bei
`float("not-a-number")`, endet Python mit Status 1 und leerem Output; die
Shell ignoriert den Status und meldet Check `#0` grün. Die erwartete Gesamtzahl
17 schützt hier nicht, weil der fehlerhaft als Erfolg gezählte Check vorhanden
ist.

**Neuer Beleg:** T-36/T-37 Runde 3, Commit `cc0f028`: Die Korrektur prüft den
Exitstatus beim positiven Check, erklärt im neuen Negativcheck `#0b` aber
ausdrücklich jeden von Null verschiedenen Parserstatus zum Erfolg. Genau der
bekannte Abbruch an `float("keine-zahl")` ergibt damit 20/20 und die erfundene
Aussage, alle drei Mutanten seien erkannt worden. Die Abbrucherkennung wurde
vom Prüfling in die Gegenprobe verschoben, nicht in einen roten Lauf verwandelt.

**Neuer Beleg:** T-42 Runde 7, Commit `c046297`: `T-22-smoke.sh` meldete sechs
von sechs Checks und trug im Kopf weiterhin Verify `#2b`. Tatsächlich liefen
`#1`, `#2`, `#3`, `#4`, das neue `#4b` und `#5`; `#2b` lief gar nicht. Die
erwartete **Anzahl** stimmte damit exakt, obwohl eine zugesagte Identität durch
eine andere ersetzt worden war. Eine Schlussmarke braucht neben der Zahl auch
die erwarteten Check-IDs.

**Nachbarschaft zu P-01:** Dort wird die Testtiefe in der Übergabe
überzeichnet. Hier überzeichnet sich das **Werkzeug** — die Übergabe gäbe
seine Zahl gutgläubig weiter.

[↑ Übersicht](#übersicht)

## P-06 · Weiterarbeiten, während eine Übergabe offen ist

**Erkennungsregel:** Nach `ready_for_codex` entsteht ein weiterer
Produkt-Commit — typischerweise, weil das Warten auf die Prüfung als Leerlauf
erscheint und der nächste Teil ohnehin ansteht. Ein eigener Branch fühlt sich
dabei wie eine Trennung an und ist keine: Der Automationsvertrag prüft
**`HEAD`**, nicht den Branch-Namen. Wer auf dem neuen Branch steht, hat den
neuen Commit in `HEAD` — und damit liegt zwischen `handoff_commit` und `HEAD`
Produktcode.

Der Vertrag sagt es wörtlich: *„alle Commits danach betreffen nur `_tickets/`
bzw. Kommunikationsdateien"*. Von Branches steht dort nichts, weil sie nichts
zur Sache tun.

**Prüffrage:** Vor jedem Commit bei offener Übergabe: `git log
<handoff_commit>..HEAD --name-only` — steht dort etwas außerhalb von
`_tickets/`? Dann ist der zu prüfende Stand nicht mehr eindeutig. Entweder der
Commit wartet, oder die Übergabe wird auf den **tatsächlichen** Produktstand
umgestellt (neuer `handoff_commit`, `review_round` erhöht, OUTBOX auf den
neuen Umfang gebracht).

**Beleg:** T-21, Runde 2 → 3, 2026-08-23: Übergeben war `6abce88` (Teil 2).
Während die Prüfung lief, entstand `556c23d` (Teil 2b) auf dem Branch
`t-21c-exchangedef-aufraeumen`. Codex hat vor dem Review geblockt: Ein Review
von genau `6abce88` wäre nicht mehr eindeutig gewesen. Aufgelöst durch
Ausweisen des tatsächlichen Stands, nicht durch Rückbau.

**Beleg:** T-21 Übergabe 3, Runde 41 → 42, 2026-08-26: Nach Codex' Claim
`2583c7a` entstand mit `89e003a` ein Commit außerhalb von `_tickets/`, der
`AGENTS.md` entfernte und `CLAUDE.md` änderte. Anlass war Mikes Klarstellung
zur Agentendatei; der richtige Kanal wäre trotzdem die Mailbox gewesen. Claude
hat den Verstoß selbst erkannt und die Übergabe auf den tatsächlichen Stand
als neues Tupel Runde 42 umgestellt.

**Beleg:** T-42 Runde 4, 2026-08-31: Nach der Übergabe des Produktstands
`d3f1949` und sogar nach Codex' Claim `98920b5` begann ein weiterer
UI-Refactor an `InstrumentCard.vue`, `InstrumentsTable.vue`, deren Tests und
der neuen Komponente `EmptyReason.vue`. Der Arbeitsbaum war damit nicht nur
hinter dem `handoff_commit` weitergelaufen, sondern uncommittet und zugleich
im Widerspruch zur OUTBOX-Aussage „Worktree sauber“. Codex hat nicht zwischen
alter und angefangener neuer Fassung geraten, sondern die Übergabe bis zu
einem neuen stabilen Tupel zurückgegeben.

**Unmittelbare Wiederholung:** T-42 Runde 7, 2026-08-31: Nach dem korrekten
Handoff `20b4b7b` und Codex' Claim `5e71cc7` entstand uncommittet
`scripts/sources-profile.sh`. Die Datei gehört zum nicht priorisierten T-25
und weder zum T-42-Handoff noch zum Review. Der Owner-Riegel wurde damit im
selben Ticket erneut durch Produktarbeit während des Reviews verletzt.

**Die Verwandtschaft:** Dasselbe Muster wie im Guard-Log, nur andersherum.
Dort werden **Freigaben zu eng** gelesen (die Klasse wird auf den wörtlichen
Befehl verkürzt), hier eine **Regel zu wörtlich** — „zwischen Übergabe und
HEAD nur Kommunikation" gelesen als Aussage über den Branch statt über die
Commit-Linie. Beide Male entscheidet, was die Regel *bezweckt*: Der Prüfer
soll wissen, was er prüft.

[↑ Übersicht](#übersicht)

## P-07 · Eine neue Zwischenlage wird gebaut statt benannt

**Erkennungsregel:** Ein Zustand wird von mehreren booleschen Feldern
gemeinsam getragen, und eine Lage ist nicht ein Wert, sondern eine
*Kombination*. Dann existieren automatisch Kombinationen, die niemand
entworfen hat — und genau die sind zwischen zwei Zuweisungen sichtbar. Das
Muster tarnt sich als Reihenfolgefehler („die Flags werden in der falschen
Reihenfolge gesetzt"); die Ursache ist, dass es für die Zwischenzeit gar
keinen Namen gibt.

Ein zuverlässiger Geruch: Eine Methode setzt Flags und ruft **danach** etwas
auf, das dauern oder scheitern kann. Zwischen beidem liegt eine Lage, die
kein Feld beschreibt.

**Prüffrage:** Jede Lage einzeln benennen und zählen — gibt es mehr
Kombinationen der Felder als benannte Lagen? Dann für jede Zeile im
Zustandsübergang fragen: *Was antwortet die Diagnose genau hier?* Ein
angehaltener Rückruf beantwortet das ausführbar; ein Test, der nur Anfang und
Ende sieht, kann es nicht.

**Beleg 1:** T-21 2A, Runde 30, Codex: `confirm()` setzte den Riegel zurück
und startete den Scheduler, **bevor** der Umzug begann. Die Lage „Umzug läuft
gerade" hatte keinen Namen; sie war „nicht mehr pending, noch nicht fertig".
Behoben, indem sie einen bekam (`claim`/`release`/`abandon`).

**Beleg 2:** T-21 2A, Runde 32, Codex, Commit `21865c0`: Exakt dieselbe Form
eine Stufe später. `release()` setzte `pending=False`, `startup_failed` entstand
erst im `except` — dazwischen lief `RefreshScheduler.start()`, und `/ready`
meldete `ok`, `/operational` meldete `serving`. Bei einem hängenden Start
unbegrenzt lange. Behoben, indem die Lage einen Namen bekam (`starting`) und
alle Lagen zu **einer** `Enum`-Zustandsgröße zusammengezogen wurden: Ein
`Enum` kann nicht halb umgeschaltet sein.

**Beleg 3:** T-21 2B, Runde 35, Codex, Commit `5b0fa31`: Das UI unterscheidet
`startupFailed`, führt dessen Retry aber über dieselbe `confirm()`-Funktion wie
den noch ausstehenden Umzug. Noch bevor der gemeinsame HTTP-Aufruf beginnt,
setzt sie die Lage auf `confirming`; das Template deutet diese ausschließlich
als Phase 1 und zeigt wieder Vorschau, Backup-Warnung und „Migration läuft".
Ein hängender Schedulerstart hält diese falsche Lage unbegrenzt sichtbar. Der
Server-Endpunkt darf gemeinsam sein; der Browservorgang braucht dennoch eine
eigene oder die bereits vorhandene benannte Lage `starting`.

**Warum die Reparatur aus Beleg 1 den Fall in Beleg 2 nicht verhindert hat:**
Sie war punktuell. Benannt wurde die eine fehlende Lage, nicht die
Darstellung. Solange der Zustand aus Flags besteht, entsteht die nächste
unbenannte Kombination beim nächsten Nachtrag von selbst — und der Nachtrag
erbt auch die Verriegelung des Originals nicht (in Runde 32 umging der neue
Wiederholungsweg den `claim` vollständig). Das ist die Verwandtschaft zu
[P-02](#p-02--punktuelle-korrektur-wird-als-vollständige-regelumsetzung-gemeldet):
Dort steht, dass die Meldung zu vollständig war; hier steht, woran es
technisch lag.

[↑ Übersicht](#übersicht)

## P-08 · Der Test erzeugt den entscheidenden Unterschied nicht

**Erkennungsregel:** Der Test soll zwei Implementierungen oder Zustände
unterscheiden, baut aber Eingaben auf, bei denen beide dieselbe Antwort geben.
Typische Formen sind eine Einerliste für eine Sortierregel, ein Aufruf unterhalb
der zu prüfenden Verdrahtung oder nur ein Zustand bei einem Cache-/Reload-Fehler.
Die Assertion kann dabei vollkommen richtig sein; wertlos ist der Aufbau.

**Prüffrage:** Welche zwei Zustände oder Implementierungen soll der Test
unterscheiden? Erzeugt sein Arrange-Schritt einen Fall, in dem deren Antworten
wirklich verschieden sind? Bei Zweifel denselben Test gegen einen minimalen
Mutanten der alten oder falschen Implementierung laufen lassen.

**Beleg 1:** T-22, erste Umsetzung von Verify #1: Der Reihenfolgetest verwendete
nur eine Quelle. Eine umgedrehte Einerliste ist dieselbe Liste; der Test konnte
eine ignorierte Reihenfolge nicht erkennen.

**Beleg 2:** T-22, nachgeschärfter Verdrahtungstest: Die erste Fassung rief
`_chain()` statt `_build_resolver()` auf. Sie prüfte damit eine Ebene unter der
Composition-Root und konnte eine dort verbliebene Verdrahtungsentscheidung
nicht erkennen.

**Beleg 3:** T-22 Runde 2, Commit `d5bb327`: Der HTTP-Test schrieb nur einen
Konfigurationsstand und rief danach `/sources` auf. Frisches Dateilesen und
gecacheter Laufzeitstand lieferten in diesem Aufbau dasselbe. Runde 3,
Commit `490314a`, erzeugt zuerst Laufzeit A, ändert danach die Datei auf B und
weist mit einem Frischlese-Mutanten nach, dass der Test nun unterscheidet.

**Beleg 4:** T-27a Runde 1, Commit `6121a94`: `DailyContract` prüfte
Sortierung, Schlusskurse und Zeitraum ausschließlich in Schleifen über
`answer.bars`; eine leere `DailySeries` bestand deshalb die vollständige Suite.
`MetadataContract` verwendete parallel `fetch(...) or []`, sodass selbst
`None` beim als bekannt deklarierten verantwortlichen Fall alle Feld-, Typ-,
Einheiten-, Plausibilitäts- und Herkunftsprüfungen übersprang. Die Testdaten
erzeugten keinen einzigen Wert, an dem die zugesagten Regeln hätten
unterscheiden können.

**Beleg 5:** T-27a Runde 2, Commit `db53189`: `ROLE_RESULTS` und seine Tests
erzeugten ausschließlich den Unterschied „bekannter Request, falscher
Treffertyp“. Für Miss-Erwartungen kehrte `_check_role_match()` vor der
Request-Prüfung zurück. Ein völlig unbekannter `object()`-Request mit
`expect=Unavailable` bestand deshalb Validierung und vollständigen Lauf: Der
`DirectRunner` erzeugte für den unbekannten Request genau das erwartete
`Unavailable`. Der neue Test unterschied die konkret besprochene Hit-Kombination,
nicht die behauptete allgemeine Rollenpassung.

**Beleg 6:** T-23 Runde 3, Commit `4e23cde`: Der Test „jede Rolle liefert dem
Core was er ruft“ prüfte nur `hasattr` auf fünf gebauten Objekten. Er erzeugte
weder einen aliaslosen US-Daily-Request noch eine Metadatenantwort mit einer
vom Core-Zielformat abweichenden Einheit. Beide Adapterfehler bestanden den
Test, weil der entscheidende Unterschied erst beim Methodenaufruf entsteht.

**Beleg 7:** T-23 Runde 4, Commit `adcb505`: Der Test „beide Namen erscheinen
in `/sources`“ konfigurierte nur `local-file`. Die zweite Assertion durfte
`canada-file` statt in der HTTP-Antwort alternativ in der internen Registry
finden. Der Arrange-Schritt erzeugte nie den behaupteten Zustand „beide Namen
im Endpunkt“, und die Assertion wechselte für den zweiten Namen die
Systemgrenze.

**Beleg 8:** T-46 Runde 1 (vor der Übergabe selbst gefunden): Das Pflichtorakel
„im Dateiprofil geht nichts ins Netz" hielt `socket.socket.connect` und
`socket.getaddrinfo` zu und prüfte zusätzlich die Quellennamen der Antwort.
Beide Hälften waren blind. `yfinance` 1.5.1 telefoniert über `curl_cffi`, also
über libcurl — die Python-`socket`-Sperre bewacht eine Leitung, die die Quelle
gar nicht benutzt. Und die Stufenliste entsteht aus der **konfigurierten**
Kette, ein Aufruf daneben bekommt keine Zeile. Ein Mutant mit
`yf.Ticker(...).history()` mitten in der Diagnose ließ das Orakel grün. Die
Lehre über den Einzelfall hinaus: **Eine Sperre prüft den Kanal, den sie
kennt.** Wo die Abstinenz von einer fremden Bibliothek abhängt, ist die
Abhängigkeit selbst das belastbarere Orakel — hier ein `ast`-Inventar aller
Importe des Moduls gegen eine aufgezählte Liste konkreter Quellen.

**Beleg 9:** T-46 Runde 1, Codex: Die Ersatzprüfung inventarisierte bei
`from … import …` nur den **Modulnamen**. Der Mutant
`from app.resolver import CompositeResolver, YahooSearchResolver` änderte die
gemessene Menge daher nicht: `app.resolver` war vorher schon erlaubt. Das
Mischmodul enthält aber neben dem Composite konkrete Online-Resolver und
importiert yfinance. Der zweite Versuch prüfte die richtige Idee eine Ebene zu
grob — ein Orakel über Importe muss bei Mischmodulen auch die importierten
Symbole unterscheiden.

**Beleg 10:** T-46 Runde 1, Codex: Der neue Test
`test_ein_quellenausfall_ist_kein_leeres_ergebnis` sagte in Name und Docstring,
`Unavailable` müsse von „leer" unterschieden werden, behauptete aber nur noch
`detail == "Unavailable"`. Der Produktcode klassifizierte denselben Wert als
`empty`; der Test blieb grün. Die alte Fassung hatte genau den entscheidenden
Unterschied (`status == "error"`) geprüft — bei der Neufassung wurde nicht nur
Code ersetzt, sondern unbemerkt das Orakel abgeschwächt.

**Beleg 11:** T-47 Runde 1a, Commit `c56c7b6`: Der Test
`test_zwei_sicherungen_kurz_nacheinander_kollidieren_nicht` rief `create()`
dreimal **nacheinander** auf und meldete damit die Abwesenheit von
Dateinamenskollisionen. FastAPI führt die synchronen POST-Handler jedoch
parallel aus. Ein Gegenlauf mit 20 gleichzeitigen `POST /backups` erhielt nur
siebenmal `201`; 13 Aufrufe wählten zwischen Existenzprüfung und
`VACUUM INTO` denselben Zielpfad und warfen einen SQLite-Fehler. „Kurz
nacheinander" erzeugte nicht den Zustand „gleichzeitig", den die
Kollisionsregel beherrschen muss.

[↑ Übersicht](#übersicht)

## P-09 · Eine Testanforderung wächst zum unbeauftragten Subsystem

**Erkennungsregel:** Eine einfache Forderung nach Unit- und Integrationstests
wird ohne Produktentscheidung um dauerhafte Test-Infrastruktur erweitert —
etwa Record/Replay, Cassettes oder vollständige Datenverkehrsmitschnitte,
eigene Transportabstraktionen, Socket-Sperren, Bereinigungs- und
Serialisierungsformate, Freshness-Tore, CLIs oder pytest-Plugins. Die einzelnen
Bausteine können technisch begründbar sein; zusammen lösen sie eine neue
Anforderung, die niemand gestellt hat.

**Prüffrage:** Welcher wörtliche Auftrag verlangt das zusätzliche Subsystem?
Wenn die Antwort nur „offline wäre robuster“, „für CI wäre es bequemer“ oder
eine Ableitung aus einer allgemeinen Qualitätsregel ist, gilt die schlanke
Variante: normale Unit-Tests und echte Online-Integrationstests über die
bereits vorhandenen APIs. Eine Ausnahme darf weder Claude noch Codex aus
vermuteten Betriebsbedingungen ableiten; sie braucht Mikes ausdrückliche,
datierte Freigabe im Ticket.

**Beleg und ausdrückliche Produktkorrektur:** T-27b, Entwurfsstände
`a1ac605` bis `af72b5a`, 2026-08-28. Aus dem Ziel, ein echtes API-Plugin zu
prüfen, entstanden über drei Reviewrunden vier neue Testkit-Module,
Aufzeichnungsformat und Signaturen, Scrubbing, Socket-Guard, pytest-Entry-Point,
Freshness-Policy und Release-CLI. Unmittelbar vor Mikes Eingriff lag davon
bereits ein uncommitteter Produktstand mit `testing/http.py`,
`testing/recordings.py`, `testing/freshness.py` und `testing/pytest_plugin.py`
vor. Mike strich die Grundannahme ausdrücklich: Unit-Tests plus
Integrationstests gegen den echten Dienst, unter Verwendung der APIs, die für
die jeweilige Programmiersprache beziehungsweise Bibliothek bereits zur
Verfügung stehen. Claude verwarf den begonnenen Offline-Code in `ebf8a14`;
die Neufassung steht in `8698aa0`.

**Reviewer-Mitverantwortung:** Codex hat den Ausbau drei Runden lang
detailgenau verbessert und schließlich zur Umsetzung freigegeben. Das ist
nicht nur ein Implementiererfehler, sondern ein fehlender YAGNI-Riegel im
Review: Lokale technische Korrektheit darf die unbeauftragte Grundannahme nicht
legitimieren.

[↑ Übersicht](#übersicht)

## P-10 · Ein Integrationstest berührt seine Außengrenze nicht

**Erkennungsregel:** Eine Datei oder ein ganzer Test trägt den Marker
`integration` beziehungsweise wird als echter Online-Fall gezählt, obwohl der
geprüfte Pfad absichtlich vor Client, Bibliothek oder Netz abbricht. Die Suite
wirkt tiefer als sie ist und der Fall verschwindet zugleich aus dem normalen
Unit-Lauf.

**Prüffrage:** Für jeden einzelnen Integrationstest: Welcher konkrete Aufruf
verlässt den Prozess? Eine testlokal vergiftete Außengrenze muss den Test rot
machen. Bleibt er grün, ist es ein Unit-Test und wird dorthin verschoben.

**Beleg 1:** T-27b Runde 5, Commit `cd3e2f3`: Der Sammelcode-Test stand unter
dem modulweiten OpenFIGI-Integrationsmarker. Der Kern-Resolver musste bei `US`
aber gerade **vor** dem Client abbrechen; derselbe Fall existierte bereits als
Unit-Test. Runde 6 entfernte ihn aus der Integrationsdatei.

**Beleg 2:** T-23 Runde 1, Commit `e6ca003`: Der yfinance-Test für EUR→EUR
steht unter dem modulweiten Integrationsmarker und wird als einer von sieben
echten Netzfällen gezählt. `YFinancePlugin.fetch_rate` beantwortet die
Identität definitionsgemäß vor `_provider.fetch_fx_rate`; der Test berührt
Yahoo nicht und gehört in die Unit-/Contract-Suite.

**Beleg 3:** T-23 Runde 2, Commit `e35d190`: Die Übergabe meldete zehn
Integrationstests, die ausnahmslos einen Dienst berührten. Der EUR→EUR-Fall
blieb jedoch zusätzlich zu seiner neuen Unit-Kopie in der Integrationsdatei;
auch der neue justETF-Fall mit US-ISIN kehrte vor dem Provider zurück. Nur acht
der zehn gesammelten Fälle überschritten tatsächlich die Außengrenze.

[↑ Übersicht](#übersicht)

## P-11 · Die Übergabe steht in der Mailbox, bevor es sie gibt

**Erkennungsregel:** `phase: ready_for_codex` und `owner: codex` stehen in
`STATUS.md`, während die Datei **uncommitted** im Arbeitsverzeichnis liegt
oder ein `handoff_commit` nennt, hinter dem noch Produktcommits folgen. Die
Mailbox ist damit für einen Zeitraum in einem Zustand, den sie nicht halten
kann: Sie sagt „übergeben" über einen Stand, den es im Repository so nicht
gibt.

**Der Unterschied zu P-06** ist die Richtung. Dort entsteht Produktcode
**nach** einer gültigen Übergabe. Hier ist die Übergabe von Anfang an
ungültig — sie wurde ausgesprochen, bevor der Stand fertig war, und der
Nachtrag kam später. Beide Male ist das Ergebnis dasselbe: Der Prüfer weiß
nicht, was er prüfen soll. Nur ist es hier kein Verstoß gegen den Riegel,
sondern eine Reihenfolge, die ihn gar nicht erst herstellt.

**Warum es so leicht passiert:** Die Mailbox wird beim Schreiben der Übergabe
gefüllt — Befundtabelle, Matrixzuordnung, Läufe —, und `phase`/`owner` sind
zwei Zeilen im selben Dokument. Es fühlt sich wie *ein* Vorgang an. Der
Zeitpunkt der Wirkung ist aber ein anderer als der des Schreibens: Wirksam
wird die Übergabe, sobald ein anderer Agent die Datei liest, und der wartet
nicht darauf, dass man fertig wird.

**Prüffrage — die Übergabe ist genau ein Commit, und er ist der letzte.** Vor
dem Setzen von `phase`/`owner`:

1. `git status --short` — ist alles außer `STATUS.md` committed?
2. `git log <handoff_commit>..HEAD --name-only` — steht dort noch Produktcode?
3. Zeigt `handoff_commit` auf **den letzten** Produktcommit, nicht auf einen
   Zwischenstand?

Erst wenn alle drei stimmen, werden `phase` und `owner` gesetzt — und
unmittelbar danach als **eigener** Commit gesichert, ohne etwas anderes
darin.

**Beleg:** T-31 Runde 6, 2026-08-29: Ich schrieb die vollständige OUTBOX samt
`phase: ready_for_codex`, `owner: codex` und `handoff_commit: 5b3c406` in die
Datei — und committete sie nicht. Beim Zusammenstellen der Matrixzuordnung
fand ich anschließend eine Testlücke bei `identity_form`, schloss sie mit
`6635c0e` und zog `handoff_commit` erst danach nach. Codex hat in genau dieses
Fenster gesehen: eine angekündigte Übergabe, uncommitted, auf einen Stand
zeigend, hinter dem noch ein Produktcommit lag. Zurückgewiesen ohne Review —
richtigerweise, denn der Riegel verbietet, den gemeinten Stand zu raten.

**Die Lehre steckt in der Ursache, nicht in der Regel:** Das Schreiben der
Übergabe ist selbst noch Arbeit, die Befunde erzeugt. Wer die Mailbox
umschaltet, *während* er sie schreibt, hat die Übergabe für die Dauer dieser
Arbeit versprochen.

[↑ Übersicht](#übersicht)
