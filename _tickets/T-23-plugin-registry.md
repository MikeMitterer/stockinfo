# T-23 · Registry: Quellen werden geladen statt einkompiliert

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | Codex-freigegeben · Plugin-MVP 4/4 | 1 Tag | Registry, zwei Ladewege, Isolation | — |

**Löst:** Der Schlussstein. Die App soll weltweit funktionieren, lässt sich hier
aber nur für wenige Märkte prüfen — allein die Auflösung eines kanadischen
Papiers hat am 2026-08-19 drei Anläufe gebraucht. Wer vor Ort sitzt, findet das
Problem in Minuten. Also muss die Lösung von außen kommen können.

**Hängt an:** T-20, T-21, T-22 — und **T-27a/T-27b** als Abnahmewerkzeug:
Ohne Doubles und kaputte Test-Plugins sind die Verify-Zeilen unten nicht
automatisierbar. T-23 gilt erst als fertig, wenn seine Tests damit laufen. Ohne sie wäre das Plugin-System eine Hülle: Ein
Plugin müsste Yahoo-Symbole verstehen, Yahoos Gattungsnamen kennen und mit `None`
drei Zustände ausdrücken.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** T-22 → T-27a →
> T-27b → **T-23**. T-23 ist erst fertig, wenn mindestens ein Datei-Plugin
> und ein Entry-Point-Plugin wirklich über **Registry → Core → REST** laufen,
> in `GET /sources` erscheinen und die eingebauten Quellen denselben
> Registry-Weg verwenden.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `examples/canada_file.py` nach `data/plugins/`, Neustart | erscheint in `GET /sources`, löst `CA…` auf | ✅ | |
| 2 | dasselbe als installiertes Paket (Entry-Point) | erscheint gleichwertig, ohne Datei im Volume | ✅ | |
| 2b | **Installationsweg** — Paketliste in `sources.yaml`, hash-benannte Umgebung unter `/data`, überlebt Image-Updates | ⚠️ | |
| 3 | Plugin mit falscher `api_version` | wird abgelehnt, mit Meldung — App startet trotzdem | ✅ | |
| 4 | Plugin, das bei jedem Aufruf wirft | wird nach wiederholtem Fehler stillgelegt; App bleibt bedienbar | ✅ | |
| 5 | Quelle liefert wiederholt `Unavailable` | Schutzschalter öffnet; weitere Aufrufe werden unterdrückt. Half-open und Reset mit **eingespeister Uhr** geprüft, ohne echte Wartezeit | ✅ | |
| 5b | Plugin, das endlos hängt | **kein Test** — die Grenze ist dokumentiert, nicht behauptet (siehe unten) | ➖ | |
| 6 | `yfinance` und `justetf` in `GET /sources` | erscheinen als **normale Quellen**, nicht als Sonderfall | ✅ | |
| 6b | **Host-Harness, Stufe 1**: temporäres Verzeichnis, leere DB, Plugin laden, Papier über REST aufnehmen | **Core-Antwort** kommt vollständig an. `generation_id` → T-25, Details/Herkunft → T-26 | ✅ | |
| ~~6c~~ | ~~`stockinfo plugin check <paket>`~~ | **gestrichen** — siehe „Scope-Riegel" unten | ➖ | |
| 7 | `make test` | Backend grün | ✅ | |

---

## Details

> ## ⚠ Entscheidung Mike, 2026-08-28: Installationsweg **in T-23 nachziehen**
>
> Wörtlich: *„Bei T-23 nachziehen — dieser Teil muss endlich fertig werden."*
> Damit ist Verify `#2b` Teil dieses Tickets und kein Folgeticket.
>
> **Der Zuschnitt ist trotzdem schlank**, und das ist keine Abschwächung,
> sondern die Lehre aus `#6c` und `P-09`: Gebaut wird der Weg, den der Betrieb
> braucht — **nicht** die Absicherung gegen ein Paket, dem man nicht traut.
>
> | gebaut | nicht gebaut |
> |---|---|
> | Paketliste mit fester Version in `sources.yaml` | Kandidatenumgebung |
> | Installation nach `data/plugin-env/<hash>` | Aktivierungszeiger, last-known-good |
> | Hash über die sortierte Paketliste → Wiederanlauf ohne Neuinstallation | Netzsperre, Offline-Selbsttest |
> | Verzeichnis in `sys.path`, danach greifen die Entry-Points | `stockinfo plugin check` (bleibt gestrichen) |
> | Fehlschlag wird gemeldet, die App startet ohne diese Pakete | |
>
> Der Hash ist der Kern: Er macht den Start **idempotent** — dieselbe Liste,
> dieselbe Umgebung, keine Installation. Und weil sie unter `/data` liegt,
> überlebt sie ein Image-Update, ohne dass jemand etwas nachinstalliert.
>
> Ein Fehlschlag beim Installieren ist wie jeder andere Plugin-Defekt: Er
> kostet die betroffenen Quellen, nicht den Start.

### Zwei Ladewege, eine Registry

**Entry-Points** (`importlib.metadata`) für Beigesteuertes — versioniert und
teilbar. Der Python-Standard; pytest und Airflow machen es so.

Installiert wird **nicht** über ein selbstgebautes Image, sondern über eine
Paketliste mit fester Version in `sources.yaml`; ein Launcher legt die Pakete
vor dem App-Start in eine hash-benannte Umgebung unter `/data` und hängt sie in
den Suchpfad. Das überlebt Image-Updates, weil nur `/data` beschrieben wird.
Einzelheiten und Sicherheitsregeln stehen im Design.

**Verzeichnis** (`data/plugins/*.py`) zum Ausprobieren und für lokale Anpassungen.
Ein Modul exportiert `SOURCES = [MeineQuelle]`.

Beide landen in derselben Registry; `sources.yaml` (T-22) bestimmt Auswahl und
Reihenfolge. Geladen wird **beim Start** — das genügt und ist auch, was Home
Assistant für Custom Components tut. Nachladen ohne Neustart kostet
Zustandsverwaltung für einen Gewinn, den man selten spürt.

### Isolation — die eine Stelle, an der fremdem Code misstraut wird

Jeder Aufruf gekapselt: `except Exception` → als `Unavailable` behandeln, nach
wiederholtem Fehlschlag die Quelle stilllegen statt bei jedem Abruf erneut zu
hängen. Dafür gibt es genau **einen** Ort.

**Was die Registry nicht kann: einen laufenden Aufruf abbrechen.** Für
synchronen Python-Code im selben Prozess gibt es keine harte Zeitgrenze — ein
Future-Timeout lässt den Aufrufer zurückkehren, der Thread hängt weiter. Die
Zeitgrenzen setzt deshalb das **Plugin** bei seinen eigenen I/O-Aufrufen; der
Vertrag verlangt es, erzwingen kann er es nicht.

**Daraus folgt eine Korrektur an diesem Ticket** *(Codex, 2026-08-20)*: Eine
frühere Fassung verlangte, der Schutzschalter greife bei einem hängenden Plugin
„ohne echte Wartezeit". Das ist unmöglich. Ein Schutzschalter kann einen Fehler
erst zählen, wenn der Aufruf **zurückkehrt** oder fehlschlägt. Bei einem endlos
hängenden synchronen Aufruf kehrt er nie zurück — daran ändert auch eine
eingespeiste Uhr nichts.

Ehrlich prüfbar ist deshalb nur der erste Fall: wiederholtes `Unavailable`
öffnet den Schalter, Half-open und Reset laufen gegen die Fake-Uhr. Das endlose
Hängen bleibt eine **nicht beherrschbare Grenze** und wird dokumentiert, statt
mit einem scheinbar wirksamen Test versehen zu werden.

Soll auch der erste hängende Aufruf zeitlich begrenzt zum Client zurückkehren,
braucht es Executor-Timeouts samt Begrenzung hängender Threads oder echte
Prozessisolation — eine deutlich größere Architekturentscheidung.

Das ist eine dokumentierte Grenze, keine Lücke im Entwurf — echte
Abbruchgarantien bräuchten eigene Worker-Prozesse samt IPC, und das ist für
eine selbstgehostete App mit wenigen Quellen unverhältnismäßig.

### ~~Ein Preflight für beide Seiten~~ — gestrichen

> **Scope-Riegel, Mike und Codex, 2026-08-28.** Dieser Abschnitt und Verify
> `#6c` sind aufgehoben. Die Kandidatenumgebung beantwortet die Frage „ein
> **fremdes, unbekanntes** Paket in eine laufende Instanz installieren" — die
> es hier nicht gibt. Mikes Wortlaut: *„Weshalb sollte ein Plugin-Test die
> laufende Instanz verändern?"* Er tut es nicht: Ein Plugin-Test ist ein Test.
>
> Ohne ausdrückliche, datierte Ausnahme entstehen weder `stockinfo plugin
> check`, ein Test-CLI, eine Socket-Sperre noch eine eigene
> Installations- oder Preflight-Umgebung. Der schlanke, **tatsächliche**
> Entry-Point-Lauf ist Teil des Produktwegs und braucht dieses Subsystem
> nicht — er läuft seit Runde 2 (`tests/test_plugin_vertical.py`).
>
> Der ursprüngliche Text bleibt darunter stehen, damit die Review-Historie
> nicht ins Leere zeigt.

### ~~Der ursprüngliche Preflight-Entwurf~~

`stockinfo plugin check <paket-oder-datei>` prüft ohne dauerhafte Änderung an
der laufenden Instanz: Import und Entry-Point, unterstützte `api_version`,
eindeutige Namen und Felddeklarationen, Pflichtkonfiguration (**ohne Geheimnisse
auszugeben**), Rollenabdeckung des Profils und — falls das Plugin Testfälle
mitbringt — einen kurzen Offline-Selbsttest.

**Der Profilwechsel verwendet denselben Preflight** — die Abnahme dafür liegt
aber bei **T-25**, nicht hier: T-23 stellt ihn bereit, T-25 weist die
Wiederverwendung nach.

**„Ohne die aktive Instanz zu ändern" ist nur belastbar mit Kandidatenumgebung**
*(Codex, 2026-08-21)*. Ein Python-Import kann bereits Seiteneffekte haben, und
ein eigener Prozess schützt nichts, wenn er dieselben Pfade und
Umgebungsvariablen bekommt. Also:

- das Paket in die spätere **hash-benannte Kandidatenumgebung** installieren
- aktive Datenbank- und Datenpfade **nicht** übergeben, sondern auf temporäre zeigen
- Netz beim Offline-Selbsttest technisch sperren
- den Aktivierungszeiger erst **nach** Erfolg umstellen
- bei Fehlern die last-known-good-Umgebung unangetastet lassen

Das ist keine Sandbox gegen bösartigen Code — es ist Zustandsisolation gegen
Fehler in einem Plugin, dem man vertraut.

### Der Harness: einmal ganz durch, in-process — aber gestaffelt

Isolierte Contract-Tests finden keine Fehler **zwischen** den Schichten. Dafür
ein kleiner Integrationslauf: temporäres Datenverzeichnis, leere Datenbank,
Beispielplugin als Datei **und** als Entry-Point laden, App mit Testkonfiguration
starten, ein Papier über den öffentlichen REST-Endpunkt aufnehmen — und am Ende
alles abbauen.

**Gestaffelt, sonst entsteht ein Ringschluss** *(Codex, 2026-08-21)*: Eine
frühere Fassung verlangte hier in **einem** Lauf `listing_id`, `generation_id`,
Herkunft und ein unbekanntes Detailfeld. Aber `generation_id` entsteht erst in
T-25, die Details erst in T-26 — und T-26 hängt seinerseits an T-23. Damit hätte
T-23 vor T-26 fertig sein und zugleich T-26-Ergebnisse abnehmen müssen. Das ist
keine Reihenfolgefrage, sondern eine zirkuläre Definition von „fertig".

| Stufe | Ticket | Prüft zusätzlich |
|---|---|---|
| 1 | **T-23** | Plugin laden → Resolver/Provider → stabile **Core**-Antwort |
| 2 | **T-25** | Profil und `generation_id` |
| 3 | **T-26** | unbekanntes Detailfeld, Herkunft, Persistenz, Override |

Derselbe Harness wächst mit; jedes Ticket besitzt seine Stufe.

Kein echter Serverprozess nötig: eine In-process-ASGI-App mit temporärem
Dateisystem genügt. Entscheidend ist, dass Registry, Container, Service,
Repository und das Pydantic-REST-Modell **gemeinsam** durchlaufen werden.

### Der erste Plugin-Autor ist die App selbst

`YFinanceResolver` und `JustEtfProvider` werden über denselben Weg geladen wie
ein fremdes Plugin — nicht als verdrahteter Sonderfall daneben. Nur so fällt auf,
wo der Vertrag zwickt, bevor es jemand anderes merkt.

### Sicherheit: bewusst, nicht beiläufig

Ein Python-Plugin läuft mit den Rechten der App. Das lässt sich nicht
wegargumentieren — wer selbst hostet, hat aber ohnehin ein Container-Image
installiert, dem er vertraut. Was die App schuldet: eine klare Ansage in der
Dokumentation und **keine Automatik, die von selbst etwas nachlädt**.

Einen risikoärmeren Nebenweg gibt es nicht: Der deklarative Ansatz wurde
gestrichen (siehe Design). Damit gilt diese Ansage für **jedes** Plugin.

---

## Auflösung

_(offen)_

---

## Codex-Review · Runde 1 · `e6ca003` · Nacharbeit

Der Teilstand enthält brauchbare Bausteine: Beide Ladewege werden gefunden,
Import- und Versionsfehler reißen die übrigen Kandidaten nicht mit, und der
Schutzschalter lässt sich über eine eingespeiste Uhr ohne Wartezeit prüfen.
Freigabefähig ist die Runde noch nicht. Der ausdrücklich verlangte
Erfolgsweg endet vor dem Core, und die vorhandenen T-27a-Verträge wurden auf
die neuen App-Plugins nicht angewandt.

1. **Hoch · Registry und Core sprechen noch verschiedene Schnittstellen.**
   Der Core erwartet beispielsweise `fetch_quote(symbol: str) -> RawQuote`
   und `resolve_isin(isin: str) -> ResolvedInstrument`; die Plugin-Rollen
   erwarten `fetch_quote(QuoteRequest) -> QuoteResult` und
   `resolve(ResolveRequest) -> Resolution`. Es gibt noch keine Brücke zwischen
   beiden. Entsprechend bauen die `BUILTIN_SOURCES` weiterhin
   `YFinanceProvider`, `JustEtfProvider`, `YFinanceEtfEnricher` und den
   Core-`OpenFigiResolver`; keine der drei Klassen unter `app/plugins/` wird im
   Produktweg benutzt. Besonders deutlich ist die Gegenprobe im angeblichen
   Auswahltest: Sie verlangt ausdrücklich, dass `quotes: [yfinance]` **kein**
   `YFinancePlugin` baut. Damit wählen nicht „zwei Plugins dieselbe Rolle".
   Runde 2 muss das dünnste vollständige Skelett liefern: ein vorhandenes
   Datei-Plugin und ein echter Entry-Point laufen jeweils über Registry → Core
   → öffentlichen REST-Endpunkt; die eingebauten Quellen benutzen denselben
   Rollen-/Adapterweg. Welche Seite übersetzt wird, ist eine
   Implementierungsentscheidung, aber die Fachlogik wird nicht dupliziert.
2. **Hoch · Die neuen App-Plugins bestehen den vorhandenen Vertrag nicht.**
   Es gibt weder `MetadataContract` für `JustEtfMetadataPlugin` noch
   `QuoteContract`, `DailyContract` und `FxContract` für `YFinancePlugin`.
   Direkte Gegenproben zeigen bereits die Folgen: justETF lässt `FIELDS` leer,
   liefert bei Unzuständigkeit `None` statt `[]` und versieht
   `fund_size` (`Unit.ABSOLUTE`) nicht mit einer Währung. yfinance meldet einen
   ungültigen FX-Request korrekt als unzuständig, fragt in `fetch_rate`
   trotzdem den Provider und lässt dessen Ausnahme durch. Die geerbten
   Contract-Suiten mit kleinen testlokalen Doubles sind hier das
   Abnahmewerkzeug, nicht neue handgeschriebene Teilprüfungen.
3. **Hoch · Isolation beginnt zu spät und Konfiguration wird ignoriert.** Ein
   geladenes Plugin, dessen Konstruktor wirft, lässt `build_chain` mit dieser
   Ausnahme abbrechen; `GuardedSource` entsteht erst danach. Ebenso gilt ein
   Plugin mit nichtleerem `configuration_problem()` heute als
   `configured: true`, weil `SourceSpec.needs` bei geladenen Quellen leer ist;
   es wird gebaut und in die Kette aufgenommen. Konstruktion und
   `is_configured`/`configuration_problem` müssen am einen Lade-/Bau-Rand
   sicher ausgewertet werden. Ein Defekt verliert seine Quelle und wird
   benannt, nicht den App-Start.
4. **Mittel · Half-open ist nicht thread-sicher.** Nach Ablauf der Öffnungszeit
   meldet `is_open` nur `False`; es gibt keinen reservierten Probeaufruf. Eine
   Barrier-Gegenprobe mit zwei Threads ließ beide gleichzeitig in die Quelle
   (`HALF_OPEN_CALLS 2`), obwohl Klasse und Ticket genau **einen** Versuch
   zusagen. Den Zustand unter einer Sperre reservieren und Erfolg/Fehler
   atomar zurückführen; keine Wartezeit und kein Executor-Subsystem ergänzen.
5. **Mittel · Die Tests beginnen erneut neben dem vorhandenen Testfundament zu
   wachsen.** `test_plugin_selection.py` enthält ein rund 90-zeiliges zweites
   CSV-Plugin samt zwei erneut definierten Formaten, obwohl
   `plugin_api/examples/canada_file.py` und `prices_file.py` genau dafür
   existieren und bereits Contract-getestet sind. Die vorhandenen Beispiele
   über die echten Ladewege verwenden; eine kleine Testkonfiguration genügt.
   Der yfinance-Identitätsfall berührt absichtlich keinen Anbieter und gehört
   daher in die Unit-Suite, nicht unter den `integration`-Marker—derselbe
   Fehler wurde gerade in T-27b korrigiert. Online-Integrationstests berühren
   ausnahmslos den echten Dienst; für den justETF-Adapter fehlt ein solcher
   Fall noch.

**Scope-Riegel:** Verify `#6c` und der Abschnitt zur Kandidatenumgebung werden
gestrichen. Ohne ausdrückliche datierte Ausnahme von Mike entstehen weder
`stockinfo plugin check`, ein Test-CLI, eine Socket-Sperre noch eine eigene
Installations-/Preflight-Umgebung. Ein schlanker tatsächlicher Entry-Point-
Lauf ist Teil des Produktwegs und braucht dieses Subsystem nicht.

**Evidenz:** Die lokalen Registry-/Auswahltests bestehen mit **34 passed**,
der echte yfinance-Lauf mit **4 passed** und `make test` mit Backend **704
passed / 29 skipped**, Plugin-API **257 passed / 1 skipped**, Dashboard **259
passed**. Die grünen Zahlen widerlegen die Befunde nicht: Der Auswahltest
bleibt unterhalb des Core, einer der vier angeblichen Online-Fälle ruft kein
Netz auf, und die bestehenden Contract-Suiten werden auf die neuen Klassen
nicht gesammelt.

---

## Codex-Review · Runde 2 · `e35d190` · Nacharbeit

Der vertikale Resolver-/Quote-Lauf ist jetzt echt: Beide Loader erreichen über
Adapter, Core und `POST /instruments/intake` den REST-Rand. Die geerbten
Contract-Suiten laufen ebenfalls. Der übergebene Stand ist trotzdem kein
fertiges Plugin-MVP; mehrere grüne Tests umgehen erneut die produktiven
Bruchstellen.

1. **Blocker · Zwei produktive Rollen sind nach der Umschaltung kaputt, zwei
   weitere bleiben native Sonderwege.** `SourceSpec("yfinance", ...,
   contract=True)` gilt für `quotes`, `daily`, `fx` und `etf_meta`, aber
   `ROLE_ADAPTERS` enthält nur `resolvers` und `quotes`. Daher gibt
   `build_chain("daily", …)` beziehungsweise `build_chain("fx", …)` ein
   `YFinancePlugin` an Core-Dienste zurück, die `fetch_daily_closes` und
   `fetch_fx_rate` aufrufen. Beide enden reproduzierbar mit `AttributeError`.
   Zugleich bauen `justetf` und `yfinance/etf_meta` weiterhin
   `JustEtfProvider` und `YFinanceEtfEnricher`; `JustEtfMetadataPlugin` läuft
   im Produkt nirgends. Das Übergangs-Flag `contract` darf nicht der Endstand
   von T-23 sein: alle fünf Rollen adaptieren und über ihre echten Core-
   Verbraucher prüfen; die eingebauten Quellen nehmen danach denselben Weg
   ohne parallele Sonderverdrahtung.
2. **Hoch · Der Schutzschalter öffnet im realen Resolver-Ablauf nie.** Er
   kapselt jede aufrufbare Methode. `CompositeResolver` ruft zuerst
   `handles()` auf; dessen normales `True` wird als Erfolg gewertet und setzt
   den Fehlerzähler zurück. Danach liefert `resolve()` `Unavailable` und zählt
   auf eins. Nach fünf vollständigen Durchläufen stand der Zähler weiterhin
   bei eins und `is_open` blieb `False`. Nur die eigentlichen Arbeitsmethoden
   zählen Erfolg oder Ausfall; `handles`, Diagnose, Deklaration und Lifecycle
   dürfen einen Ausfallverlauf nicht heilen. Die Gegenprobe läuft über
   `handles → resolve`, nicht direkt fünfmal über `resolve`.
3. **Hoch · `/sources` und Laufzeit widersprechen sich bei
   Plugin-Konfiguration.** `_build_one` fragt nun korrekt
   `configuration_problem()` und verwirft eine unbrauchbare Quelle.
   `describe_chain`, die Grundlage von `GET /sources`, prüft weiterhin nur
   das leere `SourceSpec.needs`. Eine `CanadaFileResolver` mit fehlender Datei
   erscheint dadurch als `configured: true` und `usable: true`, während
   `build_chain` null Quellen baut. Dieselbe eine operationalisierte
   Registry-Entscheidung muss Diagnose und Bauweg speisen; kein zweites
   Importieren und keine Preflight-Umgebung ergänzen.
4. **Hoch · Das justETF-Fondsvolumen trägt die falsche Währung.** Der native
   Client liest den Betrag ausdrücklich aus `fund_size_eur`, der Adapter setzt
   jedoch `Reading.currency = details.fund_currency`. Der echte Fall
   `IE00B4L5Y983` belegt den Fehler: Rohwerte
   `fund_size_eur=127160.0`, `fund_currency='USD'`; geliefert wird derzeit
   `fund_size=127160.0, currency='USD'`. Der Betrag ist EUR. Die Golden-
   Erwartung kommt aus dem Feldnamen/Clientvertrag, nicht aus derselben
   Adapterantwort.
5. **Hoch · Der installierbare Entry-Point-Weg ist nur halb umgesetzt.** Das
   immer benötigte Vertragspaket `stockinfo-plugin-api` exportiert nun selbst
   `canada-file`; damit ist Discovery über `importlib.metadata` real, aber
   kein beigesteuertes Plugin installierbar. Der weiterhin aktive
   Ticketabschnitt verlangt eine fest versionierte Paketliste in
   `sources.yaml` und einen Start-Launcher unter `/data/plugin-envs/<hash>`;
   dafür gibt es weder Parser noch Launcher. Der Dateitest importiert zudem
   dieselben bereits installierten Beispielmodule, statt die vorhandene
   `canada_file.py` als eigenständige Datei ins Volume zu kopieren. Den
   vereinbarten schlanken Installationsweg umsetzen oder eine ausdrückliche
   datierte Produktentscheidung von Mike zur Verschiebung eintragen; ein
   automatisch mit dem Host ausgeliefertes Beispiel beweist ihn nicht.
6. **Mittel · Die angekündigte Testbereinigung ist erneut unvollständig.** Der
   EUR→EUR-Fall wurde als Unit-Test **kopiert**, blieb aber unverändert in
   `test_plugin_yfinance_integration.py`. Zusätzlich steht der neue
   justETF-US-Fall unter dem modulweiten Integrationsmarker und beendet sich
   absichtlich vor dem Provider. Damit berühren nur acht der zehn gesammelten
   Integrationstests einen Dienst, nicht zehn. Beide Fälle ausschließlich in
   die Unit-/Contract-Suite verschieben. Außerdem greifen die geänderten
   Konfigurationstests mit `._client._api_key` wieder in Plugin-Interna;
   Mikes Schnittstellenanforderung verlangt hier die vorhandene öffentliche
   `api_key`-Sicht.

**Signaturinventar:** Die Änderung von `QuoteProvider.fetch_quote(str)` auf
`fetch_quote(ResolvedInstrument)` ist fachlich begründet, aber nicht an allen
Implementierern und Doubles nachgezogen. `YFinanceProvider` und mehrere
Testquellen deklarieren/verwenden weiterhin `str`. Den vollständigen
Protokollscope aktualisieren und mindestens eine Gegenprobe die übergebene
Identität tatsächlich lesen lassen; ein Double, das sein Argument ignoriert,
beweist die neue Schnittstelle nicht.

**Evidenz:** Contract/Registry/Vertical lokal **99 passed**, Ruff und
`git diff --check` sauber; echter justETF-Lauf **3 passed**; `make test`
Backend **772 passed / 29 skipped**, Plugin-API **257 passed / 1 skipped**,
Dashboard **259 passed**. Die grünen Gesamtläufe enthalten keine Core-Aufrufe
für Daily/FX, prüfen die falsche `fund_size`-Währung nur auf syntaktische
Gültigkeit und zählen zwei netzfreie Fälle als Integration.

---

## Codex-Review · Runde 3 · `4e23cde` · Nacharbeit

Vier Befunde aus Runde 2 sind jetzt belastbar erledigt: Der Schutzschalter
überlebt `handles → resolve`, justETF bezeichnet `fund_size_eur` als EUR, die
Quote-Signatur ist im Core-Scope nachgezogen, und die Online-Suite besteht aus
acht tatsächlichen Dienstaufrufen. Die öffentliche Plugin-API selbst ist
grundsätzlich knapp und gut testbar: Konstruktor, `configuration_problem`,
`handles` und je eine Rollenoperation; Contract- und Online-Tests benutzen
diese öffentlichen Einstiege. Freigabefähig ist der Hostpfad noch nicht.

1. **Blocker · Der neue Daily-Adapter schaltet alle aliaslosen Börsen ab.**
   `DailyCloseSync` reicht weiterhin nur das Anbieter-Symbol weiter.
   `DailyAdapter` versucht daraus `(ticker, mic)` zurückzurechnen und gibt bei
   einem Symbol ohne Punkt sofort `None` zurück. Genau die fünf US-Börsen haben
   laut `EXCHANGES` absichtlich keinen Alias; `AAPL/XNAS` wird als `AAPL`
   gespeichert. Die Gegenprobe am durch `build_chain("daily", …)` gebauten
   Objekt ergab `DAILY_AAPL_RESULT None` und **null Provider-Aufrufe**;
   `EUNL.DE/XETR` erreichte denselben Double dagegen. Die Identität darf nicht
   erst verworfen und danach geraten werden. Wie beim Quote-Pfad muss der echte
   Core-Verbraucher Ticker und MIC bis zum `DailyRequest` tragen; danach ein
   Test über `DailyCloseSync` oder `DailyHistoryService` für mindestens
   `AAPL/XNAS` und `EUNL/XETR`, nicht nur `hasattr`.
2. **Blocker · Der Metadatenadapter verletzt die Semantik der knappen
   Schnittstelle.** Er kopiert `Reading.value` direkt in `EtfDetails` und
   ignoriert `Reading.unit`, `currency` und `source`. Ein vollständig
   vertragskonformes Plugin mit `ter=0.0019, unit=RATIO, source='ratio-meta'`
   kommt deshalb im Core als `ter=0.0019` statt `0.19 %` und mit
   `source=None` an. Auch der eingebaute justETF-Pfad verliert so seine
   Herkunft. Bekannte Core-Felder gegen ihre kanonischen Einheiten übersetzen,
   inkompatible Beträge nicht still übernehmen und die Herkunft erhalten;
   unbekannte Felder bleiben wie vereinbart T-26. Der Adapter wird über einen
   echten Core-Verbraucher geprüft. Das Übergangsfeld `contract_roles` und der
   native yfinance-Metadaten-Sonderweg dürfen nicht kommentiert als Endzustand
   von T-23 stehen bleiben: entweder jetzt auf den Vertrag führen oder den
   verbleibenden, konkret abgegrenzten Schritt einem bereits beschlossenen
   Folgeticket zuordnen.
3. **Hoch · `/sources` berichtet weiterhin nicht den Laufzeitstand und erzeugt
   dabei weggeworfene Plugin-Instanzen.** `build_chain` und `describe_chain`
   rufen zwar dieselbe Funktion `_evaluate` auf, aber zu verschiedenen Zeiten
   und mit jeweils neuer Konstruktion. Eine testlokale Quelle, deren erste
   Konstruktion gelingt und deren zweite wirft, blieb in der laufenden Kette,
   während `describe_chain` sie als `configured=false/usable=false` meldete
   (`RUNTIME_SOURCES 1`, `CONSTRUCTOR_CALLS 2`). Das ist derselbe Widerspruch
   in neuer Form und kann bei jedem GET Konstruktor-Seiteneffekte oder
   Ressourcen erzeugen. Einen beim Bau erfassten operationalen Snapshot
   anzeigen; nicht beim Lesen neu bauen. Der öffentliche `Source.close()`-
   Lifecycle wird aktuell ebenfalls nirgends aufgerufen. Ihn für tatsächlich
   gebaute Instanzen beim Shutdown verdrahten oder aus der knappen öffentlichen
   API entfernen; nicht als unbenutzte Zusage stehen lassen. Die dokumentierte
   Diagnose muss außerdem im Endpunkt sichtbar sein oder die gegenteilige
   Dokumentationsbehauptung muss entfallen.
4. **Blocker · Der Installationsweg ist jetzt ausdrücklich entschieden und
   fehlt im Produkt.** Der nach der Übergabe hinzugekommene Entscheidungscommit
   `87c953c` legt den schlanken Umfang fest: feste Paketversionen in
   `sources.yaml`, Installation nach `data/plugin-env/<hash>`, idempotenter
   Wiederanlauf, Einhängen in `sys.path`, Fehler isolieren. Genau das umsetzen.
   Keine Kandidatenumgebung, kein Aktivierungszeiger, kein Preflight, keine
   Netzsperre und kein Offline-/Replay-System ergänzen. Die bisherige Anleitung
   `pip install …` genügt beim offiziellen Container nicht: dessen
   `site-packages` liegt im Image und überlebt ein Image-Update nicht.
5. **Mittel · Die Abnahmetests beweisen die noch offenen Aussagen nicht.** Der
   neue Fünf-Rollen-Test prüft ausschließlich, ob ein Attribut existiert; die
   obigen Daily- und Metadata-Gegenproben bleiben damit grün. Der vertikale
   Dateipfad kopiert nicht wie Verify `#1` das vorhandene
   `examples/canada_file.py`, sondern importiert dieselbe installierte
   `stockinfo_plugin_examples`-Distribution wie der Entry-Point-Weg. Und beide
   REST-Fälle prüfen `POST /instruments/intake`, aber nicht das in Verify `#1`,
   `#2` und der MVP-Entscheidung verlangte Erscheinen in `GET /sources`.
   Bestehende Tests schlank vertiefen: tatsächliche Core-Aufrufe, das vorhandene
   Einzeldatei-Beispiel und beide Namen am öffentlichen Diagnose-Endpunkt.

**Evidenz:** `make test` unabhängig grün mit Backend **779 passed / 29
skipped**, Plugin-API **257 passed / 1 skipped**, Dashboard **259 passed**;
Registry/Contract/Vertical/Config **124 passed**. Die echten Online-Läufe sind
justETF **2**, OpenFIGI **3**, yfinance **3** — alle grün und alle mit
Dienstkontakt. Diese guten Ergebnisse bleiben erhalten; die Nacharbeit braucht
keine neue Testinfrastruktur.

---

## Codex-Review · Runde 4 · `adcb505` · Nacharbeit

Daily reicht die kanonische Identität jetzt bis zum Anbieter durch, Ratio-TER
und Herkunft werden korrekt übersetzt, die Dateivariante kopiert die echten
Beispiele, und im Produkt-Diff ist keine Offline-/Replay-Infrastruktur mehr
vorhanden. Die acht Online-Fälle berühren weiterhin ihre echten Dienste. Die
Übergabe ist dennoch nicht abnahmefähig: Drei öffentliche Produktpfade sind
funktional gebrochen oder noch nicht der vereinbarte Weg; ein Test behauptet
weiter mehr als er prüft.

1. **Blocker · Der neue Metadatenadapter verletzt das vorhandene
   `EtfEnricher`-Protokoll und schaltet die ETF-Anreicherung ab.** Der Core ruft
   `fetch_etf(isin, symbol=…, exchange=…, currency=…)` auf. Der Adapter nimmt
   nur `isin` an; die Gegenprobe endet deshalb bereits bei jedem zuständigen
   justETF- oder Yahoo-Pfad mit `TypeError: unexpected keyword argument
   'symbol'`. Selbst der direkte Aufruf ohne diese Argumente hilft Yahoo
   nicht: `MetadataAdapter` baut nur `ResolveRequest(isin=…)`, während
   `YFinanceMetadataPlugin` für den Abruf das Symbol benötigt; gemessen wurden
   `ENRICHER_CONTEXT US9229087690 None None None` und Ergebnis `None`. Den
   vollständigen vorhandenen Core-Kontext über die **öffentliche knappe
   Plugin-Schnittstelle** tragen und über `CompositeEtfEnricher → Adapter →
   Plugin` für einen europäischen sowie einen Yahoo-Fall ausführen. Das neu
   erfundene, per `getattr` erkannte `is_responsible` neben `handles` ist
   derzeit ein eingebauter Sondervertrag, den ein fremdes Plugin nicht hat;
   damit ist die behauptete einheitliche Schnittstelle noch nicht erreicht.
2. **Hoch · Snapshot und Lifecycle sind weiterhin keine Abbildung der
   laufenden Instanzen.** Für eine noch nicht gebaute Rolle ruft
   `describe_chain` weiterhin `_evaluate(..., settings)` auf und konstruiert
   bei jedem `GET /sources` Wegwerf-Instanzen. Wird eine Rolle zweimal gebaut
   — im realen Composition-Root etwa `daily` für Quote-Cache und Historie oder
   `resolvers` später für den Analyzer — überschreiben `_SNAPSHOT[role]` und
   `_BUILT[role]` die ältere, weiterhin verwendete Kette. Schließlich sucht
   `close_all()` `close` am Adapter; die Adapter reichen den öffentlichen
   Lifecycle nicht durch. Die ausführbare Gegenprobe ergab vier
   Konstruktionen, zwei verschiedene laufende Builds und **null** Close-
   Aufrufe. Je Rolle eine tatsächlich verwendete Kette besitzen und
   wiederverwenden, Diagnose daraus lesen und jede gebaute öffentliche
   `Source` genau einmal schließen; ein reiner Lesezugriff baut nichts.
3. **Blocker · Der Installationsweg liest nicht das dokumentierte Format und
   erzwingt seine eigenen Regeln nicht.** Ticket und Design zeigen
   `plugins.packages`; `load_sources_config` liest stattdessen nur das
   undokumentierte Top-Level-Feld `packages`. Die Gegenprobe mit dem
   dokumentierten YAML ergab `packages == ()`. Umgekehrt werden dort
   `demo`, eine Git-URL und auch pip-Optionen ungeprüft akzeptiert, obwohl
   feste `==`-Versionen Pflicht sind. Außerdem fehlen die im verbindlich
   referenzierten Design genannten `--only-binary=:all:`-Regel und der
   Constraint für die Version von `stockinfo-plugin-api`. Den dokumentierten
   einen Parserpfad verwenden, ausschließlich normale exakt gepinnte
   Paketanforderungen zulassen und den echten pip-Aufruf entsprechend
   begrenzen. Danach mindestens einmal belegen, dass eine über **diesen**
   Zielordner installierte Distribution per Entry-Point entdeckt wird; der
   schon mit der Entwicklungsumgebung installierte Beispiel-Entry-Point prüft
   den neuen Installer nicht.
4. **Mittel · Der neue `/sources`-Test verlangt den angekündigten zweiten Namen
   ausdrücklich nicht.** Konfiguriert wird nur `local-file`; für
   `canada-file` lautet die Assertion `name in endpoint_names OR name in
   specs_by_name()`. Damit bleibt der Test grün, wenn der Entry-Point im
   öffentlichen Endpunkt fehlt — genau die zweite Hälfte seines Namens und
   Docstrings. Beide Plugins in derselben diagnostizierten Kette konfigurieren
   und beide ausschließlich in der HTTP-Antwort verlangen. Keine alternative
   Registry-Assertion als Ersatz für die REST-Zusage.

**Evidenz:** fokussierte Registry-/Vertical-/Config-/Adapter-Suite **220
passed**; `make test` Backend **789 passed / 29 skipped**, Plugin-API **257
passed / 1 skipped**, Dashboard **259 passed**; Ruff und `git diff --check`
sauber. Echte Online-Läufe: justETF **2**, OpenFIGI **3**, yfinance **3**, alle
grün und mit Dienstkontakt. Die vier kleinen Gegenproben oben treffen Übergänge,
die in diesen grünen Suites nicht ausgeführt werden. Es ist keine neue
Testinfrastruktur erforderlich.

---

## Codex-Review · Runde 5 · `d4f9036` · Nacharbeit

Die vier Komponentenbefunde aus Runde 4 sind technisch korrigiert: Der
öffentliche Request trägt den Metadatenkontext, europäischer, US- und
ISIN-loser Kanada-Fall laufen durch `CompositeEtfEnricher → Adapter → Plugin`,
ein zweiter Rollenbau liefert dasselbe Objekt und `close()` erreicht es genau
einmal, der lokale Wheel-Lauf wird aus dem hash-benannten Ziel entdeckt, und
beide Loader-Namen werden im HTTP-Ergebnis verlangt. Zwei Betriebsgrenzen und
die dazugehörige dauerhafte Testevidenz fehlen noch.

1. **Blocker · Ein Installationsfehler beendet weiterhin die App, statt nur das
   Plugin zu kosten.** `plugin_env.ensure` isoliert zwar pip und liefert bei
   einem Fehler `None`; der konfigurierte Pluginname bleibt danach aber in der
   Kette. `build_chain` wirft für ihn `UnknownSourceError`, und der Lifespan
   ruft diesen Weg beim Schedulerbau auf. Die Gegenprobe ersetzte nur den
   Installer durch einen Fehlschlag und konfigurierte
   `resolvers: [missing-plugin, openfigi]`. Trotz des gesunden Fallbacks endete
   der Start mit `START_ERROR UnknownSourceError 'missing-plugin' …`; nicht
   einmal `/health` war erreichbar. Ein fehlendes oder abgewiesenes Paket als
   unbrauchbaren Ketteneintrag mit Grund behandeln, nachfolgende Quellen
   weiterverwenden und mindestens Health sowie `/sources` erreichbar halten.
   Wenn in einer zwingenden Rolle gar keine Quelle übrigbleibt, darf der
   Fachbetrieb entsprechend nicht operational sein — der Prozess und seine
   Diagnose müssen laut Ticket trotzdem starten.
2. **Hoch · `/sources` zeigt vor dem ersten Rollenbau weiterhin nicht den
   operationalen Zustand.** Ein reiner Lesezugriff konstruiert jetzt korrekt
   nichts. Für eine geladene Quelle, deren `configuration_problem()` sicher
   „Datei fehlt“ liefert, meldet er vor dem Bau aber
   `usable=True, reason=''`; erst nach einem Produktbau wird daraus
   `usable=False, reason='Datei fehlt'`. Im normalen Start baut der Scheduler
   vier Rollen, `fx` bleibt bis zum ersten Aufruf ungeprüft; bei ausstehender
   Migration startet der Scheduler nicht und **alle** Rollen bleiben
   spekulativ. Die Kettenzustände einmal unabhängig vom ersten Fachrequest
   operationalisieren oder einen noch nicht gebauten Zustand ehrlich als
   solchen ausgeben. Der Endpunkt darf nicht `configured=true` als „kann
   arbeiten“ melden, wenn die öffentliche Diagnose noch gar nicht gefragt
   wurde, und seine Antwort darf nicht erst durch den ersten Fachrequest die
   Wahrheit wechseln.
3. **Mittel · Die zwei wichtigsten Reparaturen haben keine committed
   Regressionstests.** Der Produktcommit ändert für Metadaten und Lifecycle
   ausschließlich Produktdateien; der Test-Diff ergänzt nur Installer,
   Parser, den bestehenden Diagnose-Test **nach** dem Bau und den vertikalen
   Namenscheck. Claudes eigene Feststellung lautet, dass zuvor kein Test durch
   `CompositeEtfEnricher` lief — und auch Runde 5 fügt keinen solchen Test
   hinzu. Ebenso fehlen Tests für „zweimal bauen = dasselbe Objekt“, „reines
   Lesen baut null Objekte“ und „Shutdown schließt genau einmal“. Die
   unabhängigen Gegenproben sind aktuell grün, schützen aber keinen späteren
   Commit. Diese kleinen Fälle in den vorhandenen Testdateien festhalten,
   einschließlich der fehlgeschlagenen Installation über einen
   `TestClient`-Lifespan mit gesundem Fallback. Keine neue Testschicht bauen.

**Evidenz:** fokussierte Installer-/Registry-/Vertical-/Provider-/Quote-Suite
**212 passed**; `make test` Backend **796 passed / 29 skipped**, Plugin-API
**257 passed / 1 skipped**, Dashboard **259 passed**; Ruff und
`git diff --check` sauber. Echte Online-Läufe: justETF **2**, OpenFIGI **3**,
yfinance **3**, alle grün und mit Dienstkontakt. Unabhängige Erfolgsskripte
belegen drei Metadatenfälle sowie eine Konstruktion/einen Close-Aufruf; die
beiden negativen Skripte belegen den Lifespan-Abbruch und den wechselnden
Diagnosestatus. Keine Offline-/Replay-Infrastruktur gefunden oder benötigt.

---

## Codex-Review · Runde 6 · `a9e49f9` · freigegeben

Die Reststrecke ist geschlossen. Ein fehlgeschlagenes, exakt gepinntes Paket
wird nicht geladen; sein Kettenname erscheint in `/sources` als unbrauchbar
mit eigenem und verfügbaren Namen. Ein gesunder Fallback arbeitet weiter. Ohne
jede Kursquelle starten Prozess und Diagnose ebenfalls, `/health` antwortet
mit 200 und `/operational` ehrlich mit 503. Alle fünf Rollen werden vor dem
ersten Request einmal operationalisiert und danach als dieselben Objekte
wiederverwendet; reines Lesen baut nichts, Shutdown schließt einmal.

Die Plugin-Schnittstelle bleibt relativ knapp und ist durch ihre öffentlichen
Einstiege prüfbar: gemeinsamer Konstruktor/Lifecycle, `handles` und je Rolle
genau eine Arbeitsoperation; Metadaten deklarieren zusätzlich ihre Felder.
EU-, US- und ISIN-loser Kanada-Fall laufen dauerhaft durch
`CompositeEtfEnricher → MetadataAdapter → Plugin`. Eingebaute und externe
Quellen nehmen denselben Registry-/Adapterweg. Im Produkt- und Testbestand
gibt es keine Cassette-, Record-/Replay-, Datenverkehrsmitschnitt- oder
Offline-Testschicht.

**Abschlussevidenz:** fokussierte Regression **175 passed**; `make test`
Backend **803 passed / 29 skipped**, Plugin-API **257 passed / 1 skipped**,
Dashboard **259 passed**; Ruff und `git diff --check` sauber. Echte
Online-Läufe: justETF **2**, OpenFIGI **3**, yfinance **3**, alle grün und mit
Dienstkontakt. Zwei zusätzliche Lifespan-Gegenproben belegen den Paketfehler
mit gesundem Fallback sowie ohne verbleibende Kursquelle.

**Einschränkung zu Verify #2b:** Der echte lokale Wheel-/pip-/Entry-Point-Weg
und das persistente Ziel unter dem Datenverzeichnis sind ausgeführt. Ein
tatsächliches Container-Image-Update mit demselben `/data`-Volume wurde in
diesem Review nicht gefahren; deshalb steht dort ehrlich ⚠️ statt ✅. Das ist
kein Codeblocker für T-23, sondern die ausstehende Betriebsabnahme.
