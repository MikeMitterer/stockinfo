# T-23 · Registry: Quellen werden geladen statt einkompiliert

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 1 Tag | Registry, zwei Ladewege, Isolation | — |

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
| 6b | **Host-Harness**: temporäres Verzeichnis, leere DB, Plugin laden, Papier über REST aufnehmen | Core, `listing_id`, `generation_id`, Herkunft und ein unbekanntes Detailfeld kommen korrekt an | | |
| 6c | `stockinfo plugin check <paket>` | prüft Import, `api_version`, Namen, Felddeklarationen, Pflichtkonfiguration und Rollenabdeckung — **ohne** die aktive Instanz zu ändern | | |
| 6d | derselbe Preflight beim Profilwechsel | identische Logik, keine zweite Validierung | | |
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

### Ein Preflight für beide Seiten

`stockinfo plugin check <paket-oder-datei>` prüft ohne dauerhafte Änderung an
der laufenden Instanz: Import und Entry-Point, unterstützte `api_version`,
eindeutige Namen und Felddeklarationen, Pflichtkonfiguration (**ohne Geheimnisse
auszugeben**), Rollenabdeckung des Profils und — falls das Plugin Testfälle
mitbringt — einen kurzen Offline-Selbsttest.

**Denselben Preflight verwendet der Profilwechsel** vor jeder Rotation. Damit
gibt es keine zweite, abweichende Validierungslogik. Ein bestandener Check
beweist keine fachliche Richtigkeit, verhindert aber, dass ein Syntaxfehler, ein
fehlendes Wheel oder ein unvollständiges Profil die aktive Datenbankgeneration
ablöst.

### Der Harness: einmal ganz durch, in-process

Isolierte Contract-Tests finden keine Fehler **zwischen** den Schichten. Dafür
ein kleiner Integrationslauf: temporäres Datenverzeichnis, leere Datenbank,
Beispielplugin als Datei **und** als Entry-Point laden, App mit Testkonfiguration
starten, ein Papier über den öffentlichen REST-Endpunkt aufnehmen, dann Quote,
Instrument, Details und `/fields` abfragen — und am Ende alles abbauen.

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
