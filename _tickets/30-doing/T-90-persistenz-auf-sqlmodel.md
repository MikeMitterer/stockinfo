# T-90 · Persistenz in `app/persistence/` mit Repository-Interface

**Warum dieses Ticket:** StockInfo greift mit rohem SQLite auf seine
Datenbank zu, verteilt über mehrere Module, sogar aus einem Router. Der
Hausstandard (`code-standards/references/persistence.md`) verlangt: alle
Datenbankzugriffe in `app/persistence/`, nach außen ein Repository-Interface
(`typing.Protocol`) per Dependency Injection, kein SQL und keine
Verbindungsobjekte außerhalb dieses Ordners, und eine schlanke ORM-Schicht
(SQLModel). T-90 ist der erste von drei Schritten.

**Beispiel:** `app/routers/migration.py` öffnet heute selbst eine
SQLite-Verbindung und setzt SQL ab. Nach T-90 ruft der Router eine Funktion
aus `app/persistence/` auf und kennt weder Verbindung noch SQL.

**Stand:** Mike: „Persistenz regelkonform umbauen“, „Eigenes Ticket T-90“,
nach Vorlage des Umfangs „Drei Tickets nacheinander“. Aktiv seit
2026-10-02; Coder `claude`, Verifier `codex`, maßgeblich ist `STATUS.md`.
Für Mike steht kein Handgriff an.

## Schnitt in drei Tickets (Mike, 2026-10-02)

| Ticket | Inhalt |
|---|---|
| **T-90** (dieses) | Ordner, Interface, kein SQL außerhalb `app/persistence/`; noch kein ORM |
| [T-91](../20-ready/T-91-sqlmodel-kerntabellen.md) | SQLModel für die Kerntabellen (Instrumente, Kurse, Tageskurse, Detailwerte) |
| [T-92](../20-ready/T-92-sqlmodel-restliche-tabellen.md) | SQLModel für die übrigen Tabellen; Migrationen und Backup bleiben begründet rohes SQL im Persistenzordner |

Die befristete Ausnahme aus T-89 endet mit T-92, wenn auch die ORM-Regel
erfüllt ist.

## Ausgangslage (gemessen am 2026-10-02)

| Bereich | Dateien | SQL-Aufrufe |
|---|---|---|
| Schema, Verbindung, Altdaten-Migration | `app/db.py` (601 Z.), `app/migration.py` (733 Z.) | 31 + 21 |
| Repository, Detailspeicher | `app/repository.py` (1.102 Z.), `app/detail_store.py` (143 Z.) | 30 + 16 |
| Datenversionen | `app/data_versions.py` | 4 |
| Router | `app/routers/migration.py` | 2 |
| Backup | `app/services/backup.py` | 4 |
| bereits im Ordner | `app/persistence/plugin_migration.py` | 3 |

`app/exchanges.py` und `app/providers/base.py` nennen `sqlite3.Row` nur im
Docstring; sie greifen nicht auf die Datenbank zu. 38 Dateien in `app`,
`tests` und `scripts` importieren die verschobenen Module.

## Scope-Vertrag (Claude, 2026-10-02)

- **Ergebnis:** Außerhalb `app/persistence/` gibt es kein SQL, kein
  `sqlite3`-Verbindungsobjekt und keinen Datenbankzugriff. Dienste
  bekommen das Repository über ein Protocol per Dependency Injection.
  Verhalten, API und Daten bleiben unverändert.
- **Fachliche Änderungen (3):**
  1. Verschieben per `git mv` nach `app/persistence/`: `db.py`,
     `repository.py`, `detail_store.py`, `migration.py`,
     `data_versions.py`; Importe in allen Nutzern anpassen. Keine
     Weiterleitungsmodule an den alten Pfaden.
  2. SQL aus `app/routers/migration.py` und `app/services/backup.py` in
     Funktionen unter `app/persistence/` verlagern; Router und Dienst rufen
     nur diese Funktionen.
  3. Protocol `QuoteStore` in `app/persistence/` mit den Methoden, die die
     Dienste nutzen; Dienste annotieren damit statt mit `QuoteRepository`.
- **Tests:** bestehende Suite unverändert grün; ein Wächtertest, der per
  `ast` sicherstellt, dass außerhalb `app/persistence/` kein `sqlite3`
  importiert und kein `.execute(` auf Verbindungen aufgerufen wird
  (negativer Gegenfall dokumentiert).
- **Sichtbare Prüfung:** Temp-Instanz: Dashboard, Detailbereich, Backup
  anlegen und wiederherstellen, Migrationsvorschau.
- **Doku:** Plugin-Anleitung und READMEs auf Pfade prüfen
  (`docs/plugin-authors.md` nennt Migrationen); `AGENTS.md` „Datenbankzugriffe
  in Tests“ auf Pfade prüfen.
- **Budget:** 0 neue Abhängigkeiten; Produktdateien rund 45 (überwiegend
  Importzeilen), Diff ohne reine Umbenennungen höchstens 800 Zeilen.
- **Nicht-Ziele:** kein ORM (T-91/T-92), keine Schemaänderung, keine
  Verhaltensänderung, keine Änderung an StockPortfolio.

### Akzeptanzkriterien

- [x] Außerhalb von `app/persistence/` gibt es kein SQL, kein
      `sqlite3`-Verbindungsobjekt und keinen Datenbankzugriff; ein Test
      sichert das ab.
- [x] Dienste kennen das Repository nur über ein Protocol und bekommen es
      per Dependency Injection.
- [x] Bestehende Daten, Migrationen, Backup und Wiederherstellung
      funktionieren unverändert; Tests mit temporärer Datenbank belegen das.
- [x] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Backup.

### Side-Effects

Betrifft fast alle Backend-Module über ihre Importe; keine Änderung an API
oder Vertrag. StockPortfolio ist nur über die API betroffen.

### Verify

Aktuelle Statusmatrix; sie wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `tests/test_persistence_boundary.py` | Kein `sqlite3`-Import und kein `execute`/`executemany`/`executescript` außerhalb `app/persistence/`; die Gegenprobe findet Import, Alias-Import und Aufruf | ✅ |
| 2 | `git diff -M --summary master..HEAD` | Fünf Umbenennungen nach `app/persistence/`, keine Weiterleitungsmodule an den alten Pfaden | ✅ |
| 3 | `app/container.py`, Dienste, `routers/fields.py` | `QuoteRepository` wird nur in `get_quote_store()` gebaut; Dienste und Feldrouter sind mit `QuoteStore` annotiert | ✅ |
| 4 | Backend, Plugin-API, Ruff | Backend 1269 grün, Plugin-API 324 grün, `ruff check app tests scripts` und `plugin_api` ohne Befund | ✅ |
| 5 | Browser mit Temp-Datenbank | Dashboard und Detailbereich wie vorher; Backup anlegen, vormerken, Neustart stellt den gelöschten Eintrag wieder her | ✅ |
| 6 | Browser mit Alt-Datenbank | Migrationsvorschau, Bestätigung und Bericht laufen über die verlagerten Funktionen | ✅ |
| 7 | Doku | Projektaufbau im `README.md` nennt `persistence/`; übrige Anleitungen ohne Modulpfade | ✅ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Übergabe Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `8804575` gegen `master` (`de620e9`). Fachliche Commits:
`2b5f908` (Verschieben), `7018e45` (SQL aus Router und Backup-Dienst),
`6c9d399` (`QuoteStore`), `f0bf476` (Wächtertest), `1d02a82` (README),
`8804575` (Ruff-Rest in `scripts/probe.py`).

**Coder-Belege:**

- **#1:** Der Wächtertest liest jede Datei unter `app/` als Syntaxbaum
  (Inventar, keine Textsuche), prüft 56 Dateien und findet nichts. Die
  Gegenprobe läuft dieselbe Funktion über einen Quelltext mit
  `import sqlite3 as db`, `from sqlite3 import Row`, einem Docstring mit
  „sqlite3“ und `connection.execute(...)`: drei Treffer, der Docstring
  zählt nicht. Ergänzend per `grep` außerhalb `app/persistence/`: kein
  `connect(`, `Connection`, `cursor` oder SQL-Text; übrig sind nur
  Docstrings (`models.py:357`, `services/backup.py:9`, `exchanges.py`,
  `providers/base.py`).
- **#2:** `git mv` für `db.py`, `repository.py`, `detail_store.py`,
  `migration.py`, `data_versions.py`. Alle Importe in `app`, `tests`,
  `scripts` und `plugin_api` angepasst; dabei auch alle älteren
  Importreihenfolge-Fehler (`I001`) behoben (Mike: „Selbst wenn die
  Importfehler schon vorher da waren – korrigiere sie“).
- **#2b · SQL verlagert:** `routers/migration.py` ruft
  `preview_migration` und `stored_rejections` aus
  `app/persistence/db.py`; `services/backup.py` ruft `write_stamp_if_missing`,
  `read_stamp` und `copy_database` aus dem neuen
  `app/persistence/backup_store.py`. Ein beschädigtes Backup meldet
  `UnreadableDatabaseError` statt `sqlite3.DatabaseError`.
- **#3:** `app/persistence/quote_store.py` mit `QuoteStore(Protocol)`, nur
  mit Methoden, die Dienste und Router nutzen. Pyright (`--pythonpath
  .venv/bin/python`) meldet keinen Konflikt zwischen `QuoteRepository` und
  `QuoteStore`; die übrigen Pyright-Meldungen in `quote_cache.py` sind
  ältere Optional-/`object`-Typen und `stockinfo_plugin`-Importauflösung,
  ohne Bezug zu T-90. Pyright gehört nicht zum Projekt-Gate.
- **#4:** Backend **1269 passed, 35 skipped** (vorher 1267 + 2 Wächtertests),
  Plugin-API **324 passed, 1 skipped**, Ruff in `app`, `tests`, `scripts`
  und `plugin_api` ohne Befund. `scripts/probe.py` misst Ladezeiten der
  Importe; die drei späten Importe sind deshalb mit `noqa: E402` und Grund
  markiert statt verschoben.
- **#5:** Chrome sichtbar, 1512×801, Temp-Datenbank im Scratchpad.
  [Detailbereich EUNL.DE](T-90-browser-detail.png) mit allen fünf
  Instrumenten. Backup per „Back up now“ angelegt und zum Einspielen
  vorgemerkt ([Hinweis „restart is pending“](T-90-browser-restore-pending.png)),
  danach `GOLD.SG` per API gelöscht und den Server neu gestartet: Log
  `backup_created reason=pre-restore`, `restore_applied`,
  `restore_completed`; `GOLD.SG` ist wieder da
  ([Backups danach](T-90-browser-restored.png)).
- **#6:** Alt-Datenbank (Schema aus `tests/legacy_schema.py`, EUNL.DE,
  APC.DE, XYZ) auf eigenem Port: [Migrationsvorschau](T-90-browser-migration-preview.png)
  mit 2 umzuziehenden und XYZ als „no exchange suffix“.
  `POST /migration/confirm` und `GET /migration/report` liefern denselben
  Ablehnungseintrag; `/ready` danach `200`, APC.DE hat die Identität
  `XETR`.
- **Bezeichner:** AST-Inventar über alle 31 geänderten Python-Dateien
  (822 Namen) — alles englisch, deutsch sind nur die beiden Testnamen.

**Bewusst offen, im Scope-Vertrag so festgelegt:** Der Backup-Dienst und der
Migrationsrouter rufen Modulfunktionen aus `app/persistence/` statt eines
Protocols; `app/main.py` ruft beim Start `init_db` und `migrate_plugins`
direkt. Die Funktionen nehmen nur einen Dateipfad und geben Domänendaten
zurück, kein Verbindungsobjekt. Das ORM selbst folgt in T-91/T-92.

**Doku-Abgleich:** `README.md` „Project layout“ nannte `db.py,
repository.py` und nennt jetzt `persistence/`. `docker/README.md` und
`unraid/README.md` nennen keine Modulpfade und bleiben unverändert.
`docs/plugin-authors.md` beschreibt Plugin-Migrationen über die API, nicht
über Modulpfade, und bleibt. `AGENTS.md` „Datenbankzugriffe in Tests“
nennt keine Module und bleibt. Pläne unter `docs/superpowers/plans/` sind
Historie und behalten die alten Pfade.

**Standards** (`code-standards` mit `architecture.md`, `python.md`,
`persistence.md`, `quality.md`, `documentation.md`):

| Referenzgruppe | Ergebnis |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ Kursspeicher an einer Stelle gebaut; Namen englisch (AST-Inventar) |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nur Ruff-Markierung in `scripts/probe.py` |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ `Depends(get_quote_store)` im Feldrouter; Ruff grün |
| Datenbanken und Persistenzgrenzen | ✅ Ordner, Interface, DI; kein SQL außerhalb, per Test gesichert. ORM-Regel bleibt bis T-92 offen (Mikes Ticketschnitt) |
| Fehler, Logging und Tests | ✅ Wächtertest mit Gegenprobe; alle Tests mit temporärer Datenbank |
| Markdown und Inhaltsverzeichnisse | ✅ README-Projektaufbau aktualisiert |

**Gelesene Lessons:** `CLAUDE-LESSONS.md` mit P-02 (keine Teilumsetzung als
vollständig melden: deshalb der offene Punkt oben) und P-12 (Fundlisten
nicht abschneiden: Inventar statt Stichprobe).

**Umfang geplant / tatsächlich:** 3 / 3 fachliche Änderungen; Diff ohne
reine Umbenennungen höchstens 800 / 785 Zeilen (547 hinzu, 238 entfernt,
davon `app` 476, `tests` 275, `plugin_api` 28, `scripts` 9, README 2);
0 / 0 neue Abhängigkeiten.

Kein Merge, kein Push.
