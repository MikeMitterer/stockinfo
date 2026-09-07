# T-32 · Ein Test darf die Arbeitsdatenbank nicht erreichen

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
