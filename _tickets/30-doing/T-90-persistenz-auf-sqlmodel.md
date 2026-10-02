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

- [ ] Außerhalb von `app/persistence/` gibt es kein SQL, kein
      `sqlite3`-Verbindungsobjekt und keinen Datenbankzugriff; ein Test
      sichert das ab.
- [ ] Dienste kennen das Repository nur über ein Protocol und bekommen es
      per Dependency Injection.
- [ ] Bestehende Daten, Migrationen, Backup und Wiederherstellung
      funktionieren unverändert; Tests mit temporärer Datenbank belegen das.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Backup.

### Side-Effects

Betrifft fast alle Backend-Module über ihre Importe; keine Änderung an API
oder Vertrag. StockPortfolio ist nur über die API betroffen.
