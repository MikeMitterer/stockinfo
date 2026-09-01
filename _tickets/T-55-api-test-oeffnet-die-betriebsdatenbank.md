# T-55 · Ein API-Test öffnet die Betriebsdatenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend-Tests) | offen | 1–2 h | `tests/test_api.py` vollständig von `data/stockinfo.db` isolieren | — |

- **Angelegt:** 2026-09-01, aus dem Isolations-Gegenlauf von T-50
- **Hängt ab von:** nichts
- **Reihenfolge:** offen, **nicht** in der `priority_chain`

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
| **1** | `tests/test_api.py` allein | alle Fälle grün mit einer temporären oder vollständig gefälschten Datenbanknaht | ➖ | |
| **2** | Betriebsdateien | Hauptdatei, WAL und SHM vor/nach byte- und existenzgleich | ➖ | |
| **3** | `/ready` | `ok` und DB-Fehler bleiben unterscheidbar getestet | ➖ | |
| **4** | Regression | `make test` und Ruff grün; Isolationsorakel ruft `tests/test_api.py` direkt mit eigener DB-Naht auf, nicht über die von `.env` überschriebene Make-Variable | ➖ | |
