# T-23 · Registry: Quellen werden geladen statt einkompiliert

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | wartet · Plugin-MVP 4/4 | 1 Tag | Registry, zwei Ladewege, Isolation | — |

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
| 1 | `examples/canada_file.py` nach `data/plugins/`, Neustart | erscheint in `GET /sources`, löst `CA…` auf | | |
| 2 | dasselbe als installiertes Paket (Entry-Point) | erscheint gleichwertig, ohne Datei im Volume | | |
| 3 | Plugin mit falscher `api_version` | wird abgelehnt, mit Meldung — App startet trotzdem | | |
| 4 | Plugin, das bei jedem Aufruf wirft | wird nach wiederholtem Fehler stillgelegt; App bleibt bedienbar | | |
| 5 | Quelle liefert wiederholt `Unavailable` | Schutzschalter öffnet; weitere Aufrufe werden unterdrückt. Half-open und Reset mit **eingespeister Uhr** geprüft, ohne echte Wartezeit | | |
| 5b | Plugin, das endlos hängt | **kein Test** — die Grenze ist dokumentiert, nicht behauptet (siehe unten) | | |
| 6 | `yfinance` und `justetf` in `GET /sources` | erscheinen als **normale Quellen**, nicht als Sonderfall | | |
| 6b | **Host-Harness, Stufe 1**: temporäres Verzeichnis, leere DB, Plugin laden, Papier über REST aufnehmen | **Core-Antwort** kommt vollständig an. `generation_id` → T-25, Details/Herkunft → T-26 | | |
| ~~6c~~ | ~~`stockinfo plugin check <paket>`~~ | **gestrichen** — siehe „Scope-Riegel" unten | ➖ | |
| 7 | `make test` | Backend grün | | |

---

## Details

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
