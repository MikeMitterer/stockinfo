# T-55 · Ein API-Test öffnet die Betriebsdatenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend-Tests) | offen | 1–2 h | `tests/test_api.py` vollständig von `data/stockinfo.db` isolieren | — |

- **Angelegt:** 2026-09-01, aus dem Isolations-Gegenlauf von T-50
- **Hängt ab von:** nichts
- **Reihenfolge:** 1/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 → T-51

**Löst:** Eine als „kein Netz, keine DB" beschriebene HTTP-Testdatei öffnet
beim Readiness-Test die Betriebsdatenbank und verändert dadurch deren
SQLite-Hilfsdateien.

---

## Der gemessene Befund

`tests/test_api.py` überschreibt für den `TestClient` die Service-
Dependencies. `/ready` bezieht den Dienst jedoch nicht als FastAPI-Dependency,
sondern ruft in `app/main.py` direkt `get_cached_quote_service()` auf. Dieser
Aufruf liest die Standardkonfiguration `DATABASE_PATH=data/stockinfo.db`.

Der T-50-Gegenlauf hat den Verursacher Datei für Datei eingegrenzt:

| Lauf | WAL/SHM der Betriebsdatenbank |
|---|---|
| `pytest --collect-only` | unverändert |
| alle Backend-Tests ohne `tests/test_api.py` | unverändert |
| `tests/test_api.py` | geöffnet und beim sauberen Schließen abgeräumt |

Die Hauptdatei blieb byte-identisch und das WAL war 0 Bytes groß; es ging in
diesem Lauf kein fachlicher Inhalt verloren. Die Testabschottung ist trotzdem
gebrochen: Ein Test darf Betriebsdateien weder verändern noch öffnen.

### Codex-Gegenlauf: `DATABASE_PATH` vor `make` genügt nicht

Der Abschlusslauf von T-50 setzte die Variable ausdrücklich vor Make:

```text
env DATABASE_PATH=/tmp/stockinfo-t50-review/stockinfo.db make test
```

Trotzdem wurden `data/stockinfo.db-wal` und `-shm` geöffnet; die Hauptdatei
blieb byteidentisch. Der Grund liegt an der Make-Grenze: `DATABASE_PATH` kommt
zwar aus der Prozessumgebung, wird anschließend aber durch das eingebundene
`.env` im Makefile überschrieben. Weil die Variable ursprünglich exportiert
war, erhält `pytest` den überschriebenen Betriebspfad.

Der direkte Gegenlauf `env DATABASE_PATH=… .venv/bin/pytest -q
tests/test_api.py` respektiert dagegen den temporären Pfad und scheitert beim
Readiness-Fall erwartbar an der dort noch nicht angelegten Tabelle
`instruments`. Das bestätigt beide Teile des Tickets: Die Testdatei braucht
eine eigene initialisierte oder gefälschte DB-Naht, und der Make-Aufruf mit
vorangestellter Variable ist kein gültiges Isolationsorakel. Eine Änderung der
Make-Konfiguration ist dafür nicht erforderlich.

## Umfang

- Die Readiness-Fälle bekommen einen expliziten Testdienst beziehungsweise
  einen temporären `DATABASE_PATH`; welche Naht verwendet wird, entscheidet
  der kleinste vollständige Fix.
- Ein Gegenorakel inventarisiert `stockinfo.db`, `-wal` und `-shm` vor und nach
  `tests/test_api.py` und verlangt vollständige Unverändertheit.
- Die bestehende Aussage „TestClient ohne Lifespan, kein Netz, keine DB" muss
  danach für **jeden** Test dieser Datei stimmen.

**Nicht in diesem Ticket:** das Readiness-Verhalten der App ändern, die
Betriebsdatenbank migrieren oder WAL/SHM im Produkt abschalten.

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `tests/test_api.py` allein | alle Fälle grün mit einer temporären oder vollständig gefälschten Datenbanknaht | ✅ | |
| **2** | Betriebsdateien | Hauptdatei, WAL und SHM vor/nach byte- und existenzgleich | ✅ [^blind] | |
| **3** | `/ready` | `ok` und DB-Fehler bleiben unterscheidbar getestet | ✅ | |
| **4** | Regression | `make test` und Ruff grün; Isolationsorakel ruft `tests/test_api.py` direkt mit eigener DB-Naht auf, nicht über die von `.env` überschriebene Make-Variable | ✅ | |

---

## Scope-Vertrag (Claude, 2026-09-01, vor dem ersten Edit)

### Die fachliche Änderung

Die Fixture `client` überschreibt `get_cached_quote_service` als **FastAPI-
Dependency**. `/ready` ruft ihn nicht als Dependency, sondern direkt im
Modulnamensraum von `app.main` — dort greift die Überschreibung nicht.

Genau **ein** Fall der Datei fällt deshalb durch:

| Fall | Naht | Folge |
|---|---|---|
| `test_readiness_meldet_die_datenbank` | keine | ruft den echten Dienst, öffnet `data/stockinfo.db` |
| `test_readiness_meldet_503_wenn_die_datenbank_nicht_erreichbar_ist` | `monkeypatch` auf `app.main` | isoliert |

Die Korrektur schließt die Naht **in der Fixture**, nicht im einzelnen Test:
Die Zusage der Datei — *„TestClient ohne Lifespan (kein Scheduler/DB)"* — soll
für alle 27 Fälle gelten und nicht davon abhängen, dass jeder neue Fall daran
denkt. Der `503`-Fall setzt seinen kaputten Dienst danach weiterhin selbst und
gewinnt, weil er später greift.

### Erwartete Flächen

| Datei | Was |
|---|---|
| `tests/test_api.py` | Fixture schließt die Naht; Zusage im Docstring präzisiert |
| `_tickets/T-55-isolation.sh` | Gegenorakel: Bestand der drei Betriebsdateien vor/nach einem **direkten** `pytest`-Lauf |

**Kein Produktcode.** `/ready` bleibt, wie es ist — dass es den Dienst direkt
holt, ist eine Frage für ein anderes Ticket und steht hier unter Nicht-Ziele.

### Budget

| | Grenze |
|---|---:|
| `tests/test_api.py` | ≤ 40 |
| Orakel-Skript | ≤ 70 |
| **Gesamt** | **≤ 110** |

**Gezählt** als Summe der hinzugefügten Zeilen aus `git diff --numstat` gegen
den Abzweigpunkt, **ohne** Ticket- und `STATUS.md`-Dateien.

### Pflichtorakel

1. **Existenz zählt mit, nicht nur der Inhalt.** Das WAL ist derzeit gar nicht
   vorhanden; ein Lauf, der es anlegt und liegen lässt, wäre über einen reinen
   Inhaltsvergleich unsichtbar. Geprüft wird für `stockinfo.db`, `-wal` und
   `-shm` je **Existenz und Prüfsumme**.
2. **Der Mutant muss röten.** Die Naht aus der Fixture entfernt, dann muss das
   Skript fehlschlagen. Ohne diesen Gegenlauf belegt ein grünes Skript nur,
   dass gerade nichts passiert ist.
3. **`/ready` bleibt unterscheidbar:** `ok` und `database: error` liefern
   weiterhin `200` bzw. `503`.
4. **Der Lauf geht direkt an `pytest`**, nicht über `make` — die
   Make-Grenze überschreibt `DATABASE_PATH` aus dem `.env` und macht jedes
   vorangestellte `env DATABASE_PATH=…` wirkungslos. Das ist Codex' Befund
   oben; er ist die Begründung für die Aufrufform des Orakels.

### Nicht-Ziele

- `/ready` umbauen, damit es den Dienst als Dependency bezieht. Das wäre die
  strukturell sauberere Antwort und **Produktcode** — hier nicht.
- Makefile oder `.env` anfassen.
- Andere Testdateien anfassen. Der Gegenlauf hat sie geprüft: Sie sind sauber.
- WAL/SHM im Produkt abschalten oder die Betriebsdatenbank migrieren.

### Eine Berichtigung zum Protokoll

Der Abschlusslauf von T-50 hat `make test` und `make test-backend` **ohne**
vorangestelltes `DATABASE_PATH` aufgerufen; die im Befund oben zitierte Zeile
`env DATABASE_PATH=… make test` stammt nicht daraus. Am Ergebnis ändert das
nichts — der Verursacher ist derselbe —, und der Hinweis auf die Make-Grenze
ist unabhängig davon richtig und für Orakel 4 der Grund.

---

## Runde 1 · Umgesetzt (Claude, 2026-09-01)

### Die Korrektur

Zwei Nähte, weil es zwei Zugriffsarten gibt:

```python
app.dependency_overrides[get_cached_quote_service] = FakeService          # Routen
monkeypatch.setattr(main_module, "get_cached_quote_service", FakeService) # /ready
```

Dazu bekommt `FakeService` die Methode `count_instruments`, mit der `/ready`
nachsieht. Dass sie fehlte, gehörte zum Befund: Ohne sie ließ sich der Dienst
an dieser Stelle gar nicht ersetzen.

**Kein Produktcode angefasst.**

| | Grenze | gemessen |
|---|---:|---:|
| `tests/test_api.py` | ≤ 40 | **25** |
| Orakel-Skript | ≤ 70 | **67** |
| Gesamt | ≤ 110 | **92** |

### Das Orakel war zuerst blind — und das ist der eigentliche Ertrag

Pflichtorakel 1 oben verlangte Prüfsumme **und Existenz** der drei Dateien.
Genau so gebaut, meldete das Skript gegen den **unbehobenen** Defekt:

```
✓ tests/test_api.py laesst die Betriebsdatenbank unberuehrt
  fehlt   data/stockinfo.db-wal
  fehlt   data/stockinfo.db-shm
```

Der Grund ist der Lebenszyklus selbst: SQLite legt WAL und SHM beim Öffnen an
und räumt sie beim sauberen Schließen wieder ab. Vorher wie nachher steht
„fehlt". **Der Zustand, der die beiden Fälle unterscheidet, existiert nur
während des Laufs** — und ein Vergleich davor und danach kann ihn nicht sehen.

Sichtbar wird er an der **mtime von `data/` selbst**: Das Anlegen und Löschen
eines Verzeichniseintrags ändert sie. Gegengeprobt mit `tests/test_analyzer.py`,
das die Datenbank nicht anfasst — dort bleibt sie unverändert; der Detektor ist
also nicht bloß empfindlich.

| Lauf | Urteil |
|---|---|
| ohne Naht (Mutant) | ✗ `data/ mtime 1788284624 → 1788284644` |
| mit Naht | ✓ unverändert |

**Aufgefallen ist es nur, weil das Orakel gegen den unbehobenen Defekt lief,
bevor die Korrektur geschrieben war.** In der umgekehrten Reihenfolge wäre ein
grünes Skript der Beleg gewesen — für nichts. Pflichtorakel 1 ist damit als
Formulierung widerlegt: „Existenz zählt mit" reicht nicht, wenn der Zustand
zwischen zwei Messpunkten entsteht und wieder vergeht.

### Suite

1028 Backend · 302 Plugin-API · 45 Beispiel · 306 Dashboard. Ruff sauber.

[^blind]: Der reine Datei-Vergleich — auch mit Existenz — ist für diesen Fall
    **blind**; gemessen und dokumentiert oben. Der tragende Vergleich ist die
    mtime von `data/`.

---

## Codex-Review Runde 1 · `changes_requested` (2026-09-01)

Die Fixture-Korrektur selbst trägt: Ein unabhängiger Lauf meldet 34/34
API-Tests; `data/` bleibt auf Nanosekundenebene unverändert und Hauptdatei,
WAL sowie SHM bleiben existenz- und inhaltsgleich. Ruff für die Testdatei ist
sauber. Der Rest liegt ausschließlich im neuen Orakel-Skript:

1. `stat -f%m` misst nur ganze Sekunden. Eine Datei in einem temporären
   Verzeichnis anzulegen und sofort wieder zu löschen ergab im Gegenlauf
   denselben Sekundenwert, aber verschiedene `st_mtime_ns`. Das Orakel kann
   den entscheidenden schnellen Zustand daher noch übersehen. Es misst die
   Verzeichniszeit mit Nanosekundenauflösung.
2. Das Skript muss wie jedes Ticket-Skript unverändert aus `_tickets/solved/`
   laufen. Die Symlink-Gegenprobe scheitert derzeit, weil `../` dann nur nach
   `_tickets/` zeigt. Projektwurzel aufwärts über `.libs/` finden.
3. Ohne Argument wird Hilfe gezeigt; `--run` führt den Check aus,
   `-h|--help` zeigt Hilfe. Aktuell wird `--help` an pytest durchgereicht und
   anschließend fälschlich als grüner Isolationstest gemeldet. BashLib-Farben
   und die üblichen Usage-Konventionen verwenden.
4. Keine maskierten Fehler durch `readonly value="$(command)"` und keine
   feste globale `/tmp/t55-pytest.log`. Direkt ausgeben oder eine eindeutige,
   aufgeräumte temporäre Datei verwenden. Prozesschronik wie „erste Fassung"
   bleibt im Ticket, nicht in Skript- oder Test-Docstrings.

Danach: `--help`, normaler `--run`, derselbe Lauf über einen Link unter
`solved/`, Nanosekunden-Gegenprobe und Mutant ohne zweite Naht. Der Mutant
muss rot, der Analyzer-Kontrolllauf grün werden. Die Skriptgrenze darf dafür
auf höchstens 85 Zeilen wachsen; zusammen mit den 25 Testzeilen bleibt das
Gesamtbudget von 110 unverändert. In der Scope-Prosa die veraltete Zahl
„27 Fälle“ entfernen. Kein Produktcode und kein neuer Scope-Checkpoint.
