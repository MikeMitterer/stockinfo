---
schema_version: 1
id: SI-P-02
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- implementation
- tests
- handoff
subject_author: claude
discovered_by: unknown
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-02 · Punktuelle Korrektur wird als vollständige Regelumsetzung gemeldet
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 5a9de9209de8aec6e4bc6f76a6e65dbfbd5f83aaf938b14f7c50c0beb93469fb
  captured_at: '2026-09-11'
---

# SI-P-02 · Punktuelle Korrektur wird als vollständige Regelumsetzung gemeldet

**Implementer-Regel:** Den gesamten betroffenen Bestand inventarisieren, einschließlich Nebenpfaden, Tests und Dokumentation.

**Verifier-Prüfung:** Inventar und geänderte Stellen abgleichen; Stichproben oder Suchbegriffe belegen keine Vollständigkeit.

## Originalbelege und Einordnung

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

**Beleg wegen ausdrücklich gegenteiliger Vollständigkeitsbehauptung:** T-47
Teilstrecke 1b, Commit `0e6ca65`: OUTBOX und Ticket erklärten, ein Restore-
Fehler starte weder still weiter noch wiederhole sich endlos. `apply_pending()`
fing jedoch jede Ausnahme ab, ließ dieselbe Pending-Datei liegen und gab
`None` zurück; der Lifespan startete normal weiter und versuchte dieselbe
Absicht bei jedem folgenden Start erneut. Der neue Test verlangte genau dieses
gegenteilige Verhalten.

**Neuer Beleg derselben Regel:** T-47 Teilstrecke 1b Runde 2, Commit
`a904d42`: Die Korrektur meldete einen benannten Endzustand, der nicht mehr
pending sei. `restore_state()` und der neue Test lieferten bei einem Fehler
jedoch weiterhin gleichzeitig den Namen als `pending_restore` und den Grund
als `restore_error`, obwohl kein weiterer Startversuch mehr vorgesehen war.

**Neuer Beleg mit gegenteiliger Assertion:** T-47 UI-Runde, Commit `b0f5280`:
Scope, Übergabe und Testname erklärten, eine unpassende Sicherung verlange vor
dem Restore eine ausdrückliche Force-Handlung. Der Test klickte ohne gesetzten
Haken auf die positive Aktion und verlangte anschließend ausdrücklich genau
einen Restore-POST ohne `force`; er schrieb damit das Gegenteil der Regel als
grünes Orakel fest.

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
`_tickets/40-done/T-21b-smoke.sh` blieb im eingebetteten Python `zeilen`. Der
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
`_tickets/40-done/T-21-identitaet-mic-und-ticker.md:480`.

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
forderte `_tickets/40-done/T-21-identitaet-mic-und-ticker.md:481` unverändert einen
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

**Weitere unmittelbare Wiederholung:** T-47 Runde 8, Commit `2f70655`: Zwei
neu ergänzte Produktkommentare begründeten die heutige DRY-Struktur wieder mit
einem „ersten Nachtrag“, obwohl für genau dieses Ticket bereits der vollständige
neue Diff statt einzelner Fundstellen inventarisiert werden musste.

**Weitere Wiederholung:** T-48 Runde 1, Commit `a9d66a0`: Produkt- und
Testdocstrings führten erneut Ticket, Mike und die verworfene
`INSERT OR IGNORE`-Fassung als Begründung. Gleichzeitig entstanden nach der
AST-Pflicht wieder deutsche Hilfsfunktionen und lokale Variablen; die
Übergabe hatte nur die fachlichen Mutanten inventarisiert.

**Weitere Wiederholung:** T-53 Runde 1, Commit `05823a7`: Die neue
TypeScript-Testdatei führte mit `gemessen`, `VORGABE`, `gerendert` und
`erwartet` erneut deutsche Bezeichner ein. Fachtests, Mutanten und Ruff waren
grün, der neue Diff wurde aber wieder nicht gegen die verbindliche
Sprachtrennung geprüft. Das danach vollständig gelesene Sitzungsinventar fand
zusätzlich `antwort`, `erste`, `zweite`, `gespeichert` und `_NAMEN` im kurz
zuvor berührten Pflichtfeldtest. Codex zog beide rein mechanischen Korrekturen
im Review mit.

**Neue Spielart derselben Regel:** T-58 Runde 1, Commit `ac8b69d`. Der neue
TypeScript-Helfer hieß `KEYS_FOR` — **englisch, aber im Namensschema der
falschen Sprache.** Die Regel nennt für TypeScript `camelCase`; `GROSS` ist
die Bash-Konvention, und die stand in derselben Sitzung mehrfach im Kopf, weil
kurz zuvor `_tickets/40-done/T-56-vorlauf.sh` entstand. Dieselbe Übergabe trug
außerdem wieder Ticketchronik im Produktdocstring („seit T-44 … der
Aufnahmeweg sah sie nie … (T-58)"), obwohl genau das in T-54 Runde 1 Punkt 6
schon einmal beanstandet war. Codex heilte beides verhaltensneutral in
`edb2b4f`; die 17 Fälle blieben grün.

Der Zusatzbefund: Die Konstante war **zwischen** den Docstring von `reasonOf`
und die Funktion selbst gesetzt — der Kommentar dokumentierte danach das
falsche Gebilde. Ein Namensverstoß fällt beim Lesen auf; eine verwaiste
Dokumentation nicht, weil sie weiterhin plausibel aussieht.

**Die Regel prüft man nicht gegen die Sprache, in der man gerade gedacht
hat.** „Bezeichner sind englisch" war eingehalten. Verletzt war das
Namensschema *je Sprache* — die zweite Hälfte derselben Regel, die man
überliest, wenn die erste erfüllt ist.

**Neuer Beleg wegen ausdrücklich falscher Inventarbehauptung:** T-56 Runde 6,
Commit `cb33dcb`: Die OUTBOX nannte eine `grep`-Fundliste „Das Inventar, nicht
geschätzt" und meldete 16 nichtleere `error.value`-Zuweisungen in zwölf
Composables. Das TypeScript-AST-Inventar fand dieselben 16 Zuweisungen in
**13** Composables; die Textliste selbst führte `useMigration` nach den zwölf
anderen sogar auf. Aus der Zuweisungsliste wurde außerdem ein gemeinsamer
Vertragsumbau abgeleitet, obwohl das Verbraucherinventar nur sechs dieser
Fehler-Refs in den Notifier führt. Textfundstellen zählten die Erzeuger, aber
weder deren Anzahl noch die behauptete Verbrauchergrenze zuverlässig.

**Verallgemeinerung:** Eine Fundliste ist eine Vollständigkeitsbehauptung. Wird
sie mit `grep` erhoben, behauptet sie nur, dass die geratenen Suchwörter
vorkommen — nicht, dass es keine weiteren gibt. Wer über einen Bezeichnerscope
redet, zählt ihn vorher aus dem AST auf. Und wer eine Regelfrage stellt, liest
zuerst die Regel: Sie stand vollständig in der Skill `code-standards`, die in
dieser Runde nicht geladen war. Seither steht die Kernaussage in den
Projektregeln (`AGENTS.md`, über `CLAUDE.md` eingebunden), weil die laden,
ohne dass jemand daran denkt.
