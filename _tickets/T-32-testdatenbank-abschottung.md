# T-32 · Ein Test darf die Arbeitsdatenbank nicht erreichen

**In Arbeit: zweites Ticket der von Mike beauftragten Kette.** Codex entwickelt,
Claude prüft. Der Schutz entsteht in der Testumgebung; die Repository-
Verdrahtung der App bleibt unverändert. Der frühere Pflichtpunkt #3 entfällt
entsprechend der eingeplanten Eingrenzung.

## Für dich

Aktuell kein Handgriff nötig. Die Gegenproben arbeiten nur mit temporären
Stand-ins; kein Test öffnet absichtlich die echte Arbeitsdatenbank.

## Scope-Vertrag · 2026-09-07

Ergebnis: Der normale Backend-Testlauf verwendet je Test einen frischen
Datenbankpfad und verweigert Verbindungsaufbauten zur Arbeitsdatenbank.

1. Autouse-Fixture für `DATABASE_PATH` und Settings-/Service-Caches.
2. Nativer Python-Audit-Hook für `sqlite3.connect`: schützt das Projekt-`data/`
   und den vor Testbeginn konfigurierten Datenbankpfad; normalisiert relative
   Pfade, SQLite-Datei-URIs und Symlinks. Auch gespeicherte Connect-Referenzen
   und direkte Connection-Konstruktoren bleiben erfasst. Keine eigene SQLite-
   Implementierung, kein pytest-Plugin und kein Test-Subsystem.
3. Eingecheckte Gegenproben sowie kurze Regel in `CLAUDE.md`.

Dateien: `tests/conftest.py`, `tests/test_database_isolation.py`, `CLAUDE.md`
und dieses Ticket. Budget: zwei Testdateien, zwei Dokumentationsdateien,
höchstens 400 manuelle Diff-Zeilen. Keine App-Datei, keine neue Abhängigkeit,
kein Backup, kein Composition-Root-Umbau und keine Sicherheits-Sandbox gegen
absichtlichen Umgehungscode.

Akzeptanzfälle: #1 zwei aufeinanderfolgende Tests erhalten unterschiedliche,
leere Standarddatenbanken; ein neuer Settings-Wert und neu gebaute Dienste
verwenden den aktuellen Testpfad. #2 gesperrte Verbindungen über native und
zuvor gespeicherte Aufrufe scheitern **vor Dateierstellung**; normale temporäre
und In-Memory-Verbindungen bleiben möglich. #4 der normale Make-Gesamtlauf
bleibt grün; #5 die dauerhafte Entwicklungsregel steht in `CLAUDE.md`.

## Umsetzung und Nachweise · Codex, 2026-09-07

Der Zugriffsschutz ist implementiert; die unabhängige Prüfung durch Claude
steht an. Der native Audit-Hook wird bereits beim Import von `conftest.py`
registriert, bevor Testmodule gesammelt werden. Die Autouse-Fixture setzt
je Test einen frischen Pfad und leert Settings-, Service- und Quellen-Caches
vor und nach dem Test. Die App-Verdrahtung bleibt unverändert.

| # | Aktueller Nachweis | AI |
|---|---|:--:|
| 1 | Zwei aufeinanderfolgende Tests erhalten leere Datenbanken; zwei weitere prüfen den aktuellen Pfad des gecachten Tagesdienstes. | ✅ |
| 2 | 15 Kombinationen aus Connect-Aufruf und Pfadform, Verzeichnisschutz sowie extern konfigurierter Pfad im frischen Python-Prozess: Abbruch vor Dateierstellung. Temporäre und Speicherdatenbanken bleiben verwendbar. | ✅ |
| 3 | Aus dem aktuellen Pflichtumfang genommen; siehe Scope-Vertrag. | ➖ |
| 4 | Normaler Make-Gesamtlauf ohne manuell gesetzten Datenpfad: 1110 Backendtests bestanden, 29 übersprungen, 8 Online-Integrationstests abgewählt; Plugin-API 309 bestanden/1 übersprungen, Beispiel 47, Dashboard 339 samt ESLint. Onlinefälle wegen zuvor beobachteter Netzwerk-Timeouts nicht erneut ausgeführt. | ⚠️ |
| 5 | Entwicklungsregel in `CLAUDE.md` ergänzt. | ✅ |

```bash
.venv/bin/pytest -q tests/test_database_isolation.py
.venv/bin/ruff check tests/conftest.py tests/test_database_isolation.py
make test ARGS="-m 'not integration'"
```

Gezielte Prüfung zuletzt **23 bestanden**, Ruff ohne Befund. Der Gesamtlauf
steht in `/tmp/stockinfo-t32-final-suite.log`. Kein vorbereiteter Datenbestand
oder extern gesetzter `DATABASE_PATH` ist für diesen Lauf erforderlich.

**Gegenproben:** Vor der Implementierung 18 fehlgeschlagen/2 bestanden.
Ohne Registrierung des Audit-Hooks scheiterten 16 von damals 22 Fällen;
ohne Cache-Leerung des Tagesdienstes scheiterte dessen zweiter Durchlauf
(1 fehlgeschlagen/21 bestanden). Ohne Erfassung von `PROTECTED_DATABASES`
scheiterte der neue externe Startpfad-Fall (1 fehlgeschlagen/22 abgewählt).
Alle Mutanten sind zurückgenommen. Sie verwenden ausschließlich temporäre
Stand-ins. Logs: `/tmp/stockinfo-t32-mutant-guard.log`,
`/tmp/stockinfo-t32-mutant-cache.log`, `/tmp/stockinfo-t32-mutant-configured.log`.

**Umfang und Grenzen:** Zwei Testdateien und zwei Dokumentationsdateien,
unter 400 Diff-Zeilen; keine Produktdatei oder Abhängigkeit. Native Python-
Audits, pytest-Fixture und ein kleiner Subprozess zur Startprüfung bilden
kein eigenes Test-Subsystem. AST-Bezeichnerinventar geprüft; DRY-Suche findet
keinen bestehenden zentralen Datenbankschutz. Die Cache-Liste ist notwendige
Verdrahtung bestehender Factory-Funktionen. Der Schutz betrifft SQLite-
Verbindungsaufbauten im Testprozess; er ist keine allgemeine Sandbox für
beliebige Dateioperationen, SQL-ATTACH oder nicht instrumentierte Kindprozesse.

## Frühere Einordnung und Nachweise · Historie

Die folgenden Einschätzungen und Prüfnummern bleiben erhalten. Der damalige
reine Prüfauftrag ist durch Mikes Auftrag zur Ausführung der Kette abgelöst;
#3 ist keine aktuelle Implementierungsanforderung.

## Erneute Einordnung · Codex, 2026-09-07

**Weiterhin offen. Für sichere Entwicklung wichtig, für die Funktion des
Plugin-MVP kein Auslieferungsblocker.** Mike hat eine Bestandsprüfung und
Relevanzbewertung beauftragt, keine Umsetzung.

Aktuell bestätigt: Es gibt weiterhin keine `tests/conftest.py` und keinen
zentralen SQLite-Zugriffsschutz. `make test-backend` startet pytest ohne
isolierten Datenpfad. `get_daily_history_service` baut sein Repository aus
`get_settings().database_path`. Einzeltests wie `tests/test_daily_history.py`
verwenden eigene temporäre Repositories; das ersetzt keine zentrale Sperre.

Der letzte T-25-Gesamtlauf war ausdrücklich auf einen frischen temporären
`DATABASE_PATH` umgelenkt (1087 bestanden, 29 übersprungen, 8 abgewählt).
Das belegt keinen allgemeinen Zugriffsschutz. Claudes frühere Verbindungs-
Sonde wurde hier nicht wiederholt; insbesondere wurde kein absichtlicher
Zugriff auf die aktuelle Arbeitsdatenbank durchgeführt.

**Empfehlung: kleines Entwicklungsschutz-Ticket, etwa 1–2 Stunden inklusive
Gegenprobe und Suite; Schätzung, noch kein Implementierungsplan.** Auf temporäre
Standardpfade, passende Cache-Bereinigung und einen getesteten Zugriffsschutz
begrenzen. Relative Pfade, SQLite-Datei-URIs und Symlinks dürfen den Schutz
nicht umgehen; der tatsächlich konfigurierte Arbeitsdatenpfad muss ebenfalls
berücksichtigt werden. Keine Datenkopie oder Backup-Automatik nötig.

Die aktuelle Matrix widerspricht sich bei #3: Sie verlangt einen Umbau der
Repository-Verdrahtung, während „Was hier nicht hineingehört“ diese
Architekturfrage ausschließt. Für den Schutz ist dieser Umbau nicht nötig;
er sollte aus dem Pflichtumfang genommen werden. Ein Composition-Root darf
Repositories aus Settings bauen, sofern Tests zuverlässig isoliert sind.
Die konkrete alte IntakeService-Lücke ist bereits behoben.

T-32 verhindert keinen bekannten aktuellen Plugin-Fehler. Es schützt davor,
dass ein zukünftiger Test unbemerkt echte Daten liest oder verändert. Daher
höher priorisieren als kosmetische Restpunkte, aber den Plugin-Abschluss
nicht mit einer Architekturüberarbeitung verknüpfen. Keine Statusänderung.

---


- **Status:** offen — nichts umgesetzt; Stand gemessen 2026-09-07
- **Angelegt:** 2026-08-26, beim Bau von T-21 Teil 3, Übergabe 3 (Runde 40)
- **Repo:** StockInfo
- **Hängt ab von:** nichts — unabhängig umsetzbar
- **Ausgelöst durch:** Codex, Runde 39, „nicht blockierender Folgepunkt"

## Worum es geht

Ein Dienst, der sich sein Repository **selbst aus den Settings baut**, landet
im Test an der Produktivdatenbank — auch dann, wenn die Vorrichtung den
Kursdienst längst ersetzt hat. `dependency_overrides` greift nur dort, wo
FastAPI die Abhängigkeit auflöst; ein direkter Aufruf von `get_settings()`
oder `QuoteRepository(settings.database_path)` im Konstruktor geht daran
vorbei.

**Real passiert, nicht ausgedacht:** Beim Bau des Aufnahmewegs baute
`IntakeService` sein eigenes Repository. Der Kettentest schrieb damit in die
Testdatenbank und las die Antwortzeile aus `data/stockinfo.db`. Aufgefallen
ist es nur, weil in der Antwort plötzlich ein Papier mit gepflegten
Kennzahlen stand, das die Vorrichtung nie angelegt hatte — bei einem
schlichteren Fixture wäre es durchgelaufen.

Geschrieben wurde nichts (nachgeprüft: 6 Zeilen, mtime unverändert). Das war
Glück, keine Eigenschaft des Aufbaus.

## Warum das ein eigenes Ticket ist

Der konkrete Fall ist in Übergabe 3 behoben — `IntakeService` bekommt nur noch
den `CachedQuoteService`. **Der Baufehler steht aber weiterhin im Code:**
`get_daily_history_service()` baut sein Repository genauso aus den Settings.
Und jede künftige Ergänzung darf ihn wiederholen, solange nichts widerspricht.

Ein Riegel gehört deshalb in die Testumgebung, nicht in die Sorgfalt des
Nächsten, der einen Dienst schreibt.

## Verify-Matrix

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine
Live-Verifikation · ❌ gemessen und **nicht** erfüllt.

Die `AI`-Spalte trägt den von Claude am 2026-09-07 gemessenen Stand; die
Messungen stehen unter [Prüfstand 2026-09-07](#prüfstand-2026-09-07).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `tests/conftest.py` | eine `autouse`-Vorrichtung setzt `DATABASE_PATH` für **jeden** Test auf ein temporäres Verzeichnis und leert die Settings-Caches | ❌ | |
| 2 | Gegenprobe | ein absichtlich auf `data/` zielender Test schlägt **fehl**, statt die Datei zu öffnen — der Riegel wird also geprüft, nicht nur behauptet | ❌ | |
| 3 | `app/container.py` | `get_daily_history_service` bezieht sein Repository über dieselbe Abhängigkeit wie die übrigen Dienste, statt es selbst zu bauen | ❌ | |
| 4 | ganzer Lauf | `make test` bleibt grün, und kein Test hängt still an einer anderen Datenbank als seiner eigenen | ◑ | |
| 5 | Dauerhaftigkeit | die Regel steht dort, wo sie beim nächsten Dienst gelesen wird — Skill `code-standards` oder `CLAUDE.md`, nicht nur in diesem Ticket | ❌ | |

<a id="prüfstand-2026-09-07"></a>

### Prüfstand 2026-09-07 · gemessen von Claude

**Nichts vom Riegel ist gebaut — aber die Gefahr ist heute latent, nicht akut.**
Das ist der ganze Befund in einem Satz, und die beiden Hälften gehören zusammen.

**`#1`** `tests/conftest.py` existiert nicht; im ganzen Repo liegt keine
`conftest.py`. `[tool.pytest.ini_options]` in `pyproject.toml` setzt kein
`DATABASE_PATH`. Es gibt also weder Umlenkung noch Cache-Leerung.

**`#3`** Der im Ticket benannte Baufehler steht unverändert im Code:
`app/container.py:213` baut `QuoteRepository(settings.database_path)` selbst.

**`#2`** Gemessen statt geschlossen: Ein Test, der absichtlich
`get_connection('data/stockinfo.db')` aufruft, läuft **durch**.

```
tests/test_t32_selftest.py .                    [100%]
1 passed in 0.07s
```

Verlangt ist das Gegenteil. Der Testfall lag nur für diese Messung im Baum und
ist wieder entfernt; er gehört mit dem Riegel zusammen eingecheckt.

**`#4` ist der Grund für `◑`.** Über den vollständigen Lauf hat eine Sonde jeden
`sqlite3.connect` mitgeschrieben und auf Pfade unterhalb von `data/` geprüft:

```
1069 passed, 29 skipped, 8 deselected
Zugriffe auf data/ während des Laufs: KEINE
```

Die Suite ist grün und **kein einziger Test** hängt derzeit an der
Arbeitsdatenbank. Das ist die gute Nachricht — und genau der Zustand, den das
Ticket beschreibt: „Das war Glück, keine Eigenschaft des Aufbaus." Ohne `#1`
und `#2` sichert nichts, dass der nächste Dienst es nicht wieder tut.

**Die Sonde ist gegengeprüft.** Eine Messung, die nichts findet, ist wertlos,
solange nicht feststeht, dass sie etwas finden *kann*. Derselbe Lauf gegen den
absichtlichen Zugriff meldet ihn mit Testnamen:

```
…/data/stockinfo.db <- tests/test_t32_selftest.py::…_absichtlichen_zugriff (call)
```

**`#5`** Die Regel steht weder in `CLAUDE.md` noch in `AGENTS.md` noch im Skill
`code-standards`.

**Ein Hinweis zur Methode, damit ihn niemand nachbaut:** Der Hash von
`data/stockinfo.db` ändert sich während eines Testlaufs — er ändert sich aber
auch, wenn gar nichts läuft. Auf diesem Rechner bedienen zwei uvicorn-Instanzen
(Ports 8801 und 8802) die Datei samt Scheduler. „Hash vorher/nachher" ist hier
also **kein** Orakel; nur das Mitschreiben der Verbindungen unterscheidet
zuverlässig.

```bash
# Sonde: jeden sqlite3.connect auf einen Pfad unterhalb von data/ mitschreiben,
# den Lauf aber durchlassen, damit die Liste vollständig wird.
env PYTHONPATH=. T32_GUARDED_DIR="$(pwd)/data" T32_REPORT=/tmp/t32.txt \
  .venv/bin/pytest -q -p dbwatch_probe -m "not integration"
```

## Vorschlag für den Riegel

Zwei Teile, und der zweite ist der wichtigere:

1. **Umlenken.** Eine `autouse`-Fixture in `tests/conftest.py` setzt
   `DATABASE_PATH` auf `tmp_path` und ruft `get_settings.cache_clear()` sowie
   `get_cached_quote_service.cache_clear()`. Damit zeigt der Vorgabewert
   nirgends mehr auf `data/`.
2. **Verbieten.** Ein Zugriff auf die reale Datei soll **scheitern**, nicht
   still gelingen. Denkbar ist ein Monkeypatch auf `sqlite3.connect`, der
   einen Pfad unterhalb von `data/` mit einem sprechenden Fehler ablehnt.
   Ohne diesen Teil verhindert das Ticket nur den heutigen Fall: Ein Dienst,
   der seinen Pfad aus einer *anderen* Quelle zieht, käme weiterhin durch.

Die Gegenprobe aus `#2` gehört mit eingecheckt. Ein Riegel ohne einen Test,
der ihn auslöst, ist eine Behauptung.

## Was hier **nicht** hineingehört

* Die Frage, ob Dienste ihr Repository überhaupt selbst bauen dürfen. Das ist
  eine Architekturfrage; hier geht es nur darum, dass ein Fehler dabei im Test
  auffliegt statt an der Produktivdatenbank.
* Ein Backup-Mechanismus. Der liegt in T-29. *(Nachtrag 2026-09-07: T-29 ist
  verworfen. Der SQLite-Snapshot ist in T-25 entstanden und steht in
  `app/services/backup.py`; der portable JSON-Weg ist gestrichen. An dieser
  Abgrenzung ändert sich nichts — ein Riegel im Test ist kein Backup.)*
