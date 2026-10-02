# T-91 · SQLModel für die Kerntabellen

**Warum dieses Ticket:** Der Hausstandard verlangt eine schlanke ORM-Schicht
(SQLModel) für Datenbankzugriffe. Nach T-90 liegt aller Zugriff in
`app/persistence/` hinter einem Protocol, aber noch als rohes SQLite. T-91
stellt die meistgenutzten Tabellen auf SQLModel um.

**Beispiel:** `QuoteRepository.set_volatility` schreibt heute per SQL in
`detail_values`. Nach T-91 nutzt es ein SQLModel-Modell; Aufrufer merken
keinen Unterschied, weil sie nur das Protocol kennen.

**Stand:** Angelegt am 2026-10-02 aus T-90 (Mike: „Drei Tickets
nacheinander“). Aktiv seit 2026-10-02 nach T-90s technischer Freigabe;
Coder `claude`, Verifier `codex`, maßgeblich ist `STATUS.md`. Für Mike steht
kein Handgriff an.

## Scope-Vertrag (Claude, 2026-10-02)

**Ausgangslage (gemessen):** `app/persistence/repository.py` 1.089 Zeilen,
29 Verbindungsblöcke; `detail_store.py` 143 Zeilen und teilt die
Repository-Transaktion. `save_quote` schreibt Instrument, Kurs und
Detailwerte in **einer** Transaktion und fängt dabei das UNIQUE-Rennen beim
Anlegen ab. SQLModel 0.0.47 zieht SQLAlchemy 2.0.54; Python 3.11.

**Nachgeschlagen (Pflicht):** SQLModel-Tutorial (Tabellenmodelle, Session,
FastAPI-Abhängigkeit) und SQLAlchemy-2.0-Doku zum SQLite-Dialekt: Unter
Python < 3.12 braucht pysqlite für echte Transaktionen und SAVEPOINTs das
dokumentierte Ereignisrezept (`isolation_level = None` beim Verbinden,
eigenes `BEGIN`); Upserts über `sqlalchemy.dialects.sqlite.insert` mit
`on_conflict_do_update`.

- **Ergebnis:** `instruments`, `quotes`, `daily_closes`, `detail_values`
  und `detail_overrides` werden über SQLModel gelesen und geschrieben.
  Schema, API, Verhalten und Daten bleiben unverändert.
- **Fachliche Änderungen (5):**
  1. Abhängigkeit `sqlmodel==0.0.47` in `requirements.txt`.
  2. `app/persistence/session.py`: Engine je Datenbankpfad ohne
     Verbindungspool (wie heute: eine Verbindung je Vorgang), dieselben
     PRAGMAs wie `get_connection` aus **einer** gemeinsamen Funktion, das
     pysqlite-Rezept; ein Kontextmanager für Sessions mit Commit/Rollback.
  3. `app/persistence/tables.py`: fünf Tabellenmodelle, die das bestehende
     Schema abbilden. Das DDL in `db.py` bleibt maßgeblich; kein
     `create_all`.
  4. `QuoteRepository` und `detail_store` arbeiten mit der Session: ORM für
     die fünf Tabellen; das UNIQUE-Rennen über einen SAVEPOINT
     (`begin_nested`). Die übrigen Tabellen (`meta`, `daily_meta`,
     `fx_rates`, `instrument_overrides`) laufen bis T-92 über `text()` in
     derselben Session und Transaktion. Rückgaben bleiben `dict`; kein
     Modellobjekt verlässt `app/persistence/`.
  5. Die einmalige Detailübernahme (`detail_store.initialize`) schreibt
     über dieselben `put_provider`/`put_manual` wie das Repository — sonst
     stünde das Upsert zweimal da (DRY). Ihre Logik bleibt gleich; die
     übrigen Altdaten-Migrationen in `db.py` und `migration.py` bleiben
     unberührt.
- **Tests:** bestehende Suite unverändert grün (keine Testanpassung außer
  Fehlertypen, die sich durch SQLAlchemy ändern, je begründet). Neu: ein
  Abgleich, dass jedes Modell genau die Spalten der Tabelle hat (frische
  und aus dem Altformat migrierte Datenbank); der Grenzwächter verbietet
  `sqlmodel`/`sqlalchemy`-Importe außerhalb `app/persistence/`; ein Test
  für das UNIQUE-Rennen im SAVEPOINT, rot ohne ihn.
- **Sichtbare Prüfung:** Temp-Instanz und Alt-Datenbank: Dashboard,
  Detailbereich, Aufnahme und Löschen eines Instruments, manuelle Eingabe.
- **Doku:** `README.md`, `docker/README.md`, `unraid/README.md` auf
  Abhängigkeits- und Persistenzaussagen prüfen; Image-Größe messen.
- **Budget:** 1 neue Abhängigkeit (+ SQLAlchemy transitiv); Produktdateien
  rund 6; Diff höchstens 900 Zeilen.
- **Nicht-Ziele:** keine Schemaänderung, kein `create_all`, keine
  ORM-Umstellung der übrigen Tabellen (T-92), keine Änderung an Migration
  und Backup, keine Änderung an StockPortfolio.

## Umfang

- Tabellen: `instruments`, `quotes`, `daily_closes`, `detail_values`,
  `detail_overrides`.
- SQLModel als neue Abhängigkeit; vor der ersten Verwendung ein aktuelles
  Beispiel aus der offiziellen Doku (<https://sqlmodel.tiangolo.com/>)
  nachschlagen (Pflicht laut Standard).
- Bestehendes Schema bleibt; die Modelle bilden es ab, keine
  Schemaänderung. Die Altdaten-Migrationen bleiben in T-91 unberührt.
- Rohes SQL bleibt nur, wo das ORM schlecht passt, und dann im Repository.

### Akzeptanzkriterien

- [x] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [x] Bestehende Daten funktionieren ohne Migration; Tests mit temporärer
      Datenbank und einer Datenbank im Altformat belegen das.
- [x] Außerhalb `app/persistence/` gibt es keine ORM-Typen.
- [x] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Aufnahme und Löschen eines Instruments.

### Side-Effects

Neue Abhängigkeit `sqlmodel` (zieht SQLAlchemy nach); Docker-Image wird
größer. Keine Änderung an API oder Vertrag.

### Verify

Aktuelle Statusmatrix; sie wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `tests/test_persistence_tables.py` | Jedes der fünf Modelle trägt genau die Spalten seiner Tabelle, frisch und aus dem Altformat umgezogen | ✅ |
| 2 | `app/persistence/repository.py`, `detail_store.py` | Die fünf Kerntabellen nur über Modelle und SQLAlchemy-Ausdrücke; `meta`, `daily_meta`, `fx_rates`, `instrument_overrides` über `text()` in derselben Session | ✅ |
| 3 | `tests/test_persistence_boundary.py` | Kein `sqlite3`/`sqlalchemy`/`sqlmodel` und kein Import von `tables`/`session` außerhalb `app/persistence/`; Gegenproben | ✅ |
| 4 | Parallele Schreiber, verlorener Anlegeversuch | 8 echte Threads: genau einer legt an; nachgestellter UNIQUE-Konflikt: Retry findet die Zeile, Kurs wird in derselben Transaktion geschrieben | ✅ |
| 5 | Backend, Plugin-API, Ruff | Backend 1286, Plugin-API 324, Ruff grün | ✅ |
| 6 | Browser mit Temp-Datenbank | Dashboard, manuelle Eingabe übersteht Neuladen, Aufnahme und Löschen eines Instruments ohne verwaiste Zeilen | ✅ |
| 7 | Browser mit Alt-Datenbank | Umzug, danach Übersicht über den ORM-Leseweg mit Kurs und Kurszahl | ✅ |
| 8 | Doku | README-Projektaufbau nennt SQLModel; übrige Anleitungen ohne Aussage zu Abhängigkeiten | ✅ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Übergabe Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `6366844` gegen `master` (`21b5c84`). Produktcommits:
`c08d328` (Abhängigkeit, Session, Modelle, Spaltenabgleich), `2b1b50d`
(Repository und Detailspeicher), `880884c` (README), `6366844` (Typen).

**Abweichungen vom Scope-Vertrag, je gemessen:**

1. **Kein SAVEPOINT.** Geplant war `begin_nested()` für das UNIQUE-Rennen.
   Der neue Test `test_der_verlorene_anlegeversuch_kostet_die_transaktion_nicht`
   ist mit und ohne SAVEPOINT grün: SQLite nimmt nur die gescheiterte
   Anweisung zurück, und SQLAlchemy lässt die Transaktion für
   Core-Anweisungen nutzbar — genau wie vorher `sqlite3`. Ohne Retry wird
   der Test rot. Der SAVEPOINT ist deshalb entfallen (KISS).
2. **Schreibende Sessions mit `BEGIN IMMEDIATE`.** Neu gefunden: Mit dem
   pysqlite-Rezept beginnt die Transaktion bei `BEGIN`, nicht erst beim
   ersten Schreibbefehl. Der Test mit acht parallelen Schreibern brach
   daraufhin mit „database is locked“ ab: Alle lasen denselben alten Stand,
   und im WAL-Modus scheitert der Wechsel zur Schreibsperre sofort.
   `_session(write=True)` nimmt die Sperre gleich zu Beginn; alle zwölf
   schreibenden Methoden und die Detailübernahme in `init_db` nutzen es.
   Danach dreimal grün.
3. **Alt-Fixture ergänzt.** Der Spaltenabgleich zeigte, dass
   `tests/legacy_schema.py` `provider`, `ter`, `replication`, `fund_size`,
   `meta_fetched_at` und `daily_closes.currency` fehlten. `git show` belegt:
   Sie stehen seit dem ersten Schema (`e5947bf`, `8fd0738`); eine
   Datenbank ohne sie gab es nie. Das Fixture bildet jetzt den echten
   Altbestand ab; alle Migrationstests bleiben grün.

**Coder-Belege:**

- **#1:** 10 Parametrisierungen (5 Tabellen × frisch/umgezogen) grün; der
  umgezogene Fall prüft vorher, dass der Umzug wirklich lief (`EUNL`/`XETR`).
- **#2:** Lesen über `select(table_of(Record))` und Spalten statt
  Modellobjekten (`fetch_all`/`fetch_one`): Geschrieben wird per Upsert
  direkt in die Datenbank, und ein ORM-Objekt aus derselben Session zeigte
  den alten Stand. Schreiben über `insert(...).on_conflict_do_update`,
  `update`, `delete`. `identity_where` (SQL-Fragment) ist jetzt
  `identity_condition` (SQLAlchemy-Bedingung). Die Übersichtsabfrage
  erzeugt dasselbe SQL wie vorher (kompiliert verglichen). Die
  Tagesschlusskurse laufen als `executemany`, nicht als eine riesige
  `VALUES`-Liste — die stieße bei langer Historie an SQLites
  Platzhaltergrenze.
- **#3:** Wächter um `sqlalchemy`, `sqlmodel` und die Module `tables`,
  `session` erweitert; Gegenprobe mit allen drei Importarten.
- **#4:** siehe Abweichungen 1 und 2; Mutant „kein Retry“ macht den neuen
  Test rot.
- **#5:** Backend **1286 passed, 35 skipped**, Plugin-API **324 passed,
  1 skipped**, Ruff `app tests scripts` und `git diff --check` grün.
  Pyright über die vier Persistenzdateien: die neuen Befunde (Vergleiche,
  `__table__`, `rowcount`) mit `col()`, `table_of` und `CursorResult`
  behoben; übrig bleiben 10 ältere in unverändertem Code
  (`save_instrument(resolved: object)`, `applies(row.get(...))`).
- **#6:** Chrome sichtbar, 1512×801, Temp-Datenbank.
  [Manuelle Eingabe nach Neuladen](T-91-browser-manual-reloaded.png):
  „Fund provider“ bei GOLD.SG auf „Boerse Stuttgart“, danach wieder
  entfernt. [Aufnahme](T-91-browser-intake-added.png) von
  `DE0005557508` (`201`, DTE.DE/XETR), [Löschdialog](T-91-browser-delete-confirm.png)
  mit „1 price point will be lost“ (Kurszahl aus der neuen Abfrage),
  [danach](T-91-browser-deleted.png) wieder fünf Instrumente. Keine
  verwaisten Zeilen in `quotes`, `daily_closes`, `detail_values`,
  `detail_overrides`, `daily_meta` — Fremdschlüssel greifen auch in
  ORM-Verbindungen.
- **#7:** Alt-Datenbank auf eigenem Port: Umzug bestätigt,
  [Übersicht](T-91-browser-legacy-dashboard.png) mit APC.DE und EUNL.DE,
  Kurs und `history_count` 1.
- **Testanpassungen, je begründet:** Acht Testdateien holten sich für
  Testaufbau und Nachsehen die rohe Verbindung `repo._connect()`; die gibt
  es nicht mehr. Sie nutzen jetzt `tests/raw_database.py` auf dieselbe
  Datei, Prüfungen unverändert. `test_open_details_flow` macht jede
  Verbindung über `session.configure_connection` schreibgeschützt; eine
  Gegenprobe belegt, dass Schreiben dann scheitert.
  `test_migration_uebernimmt_waehrung_des_manuellen_betrags` lief auf einer
  Zwei-Spalten-Tabelle im Speicher, die es nie gab; jetzt auf dem echten
  Schema, gleiche Erwartung.
- **Bezeichner:** AST-Inventar über alle 20 geänderten Python-Dateien,
  6.722 Vorkommen; einziger nicht-ASCII-Name ist der zulässige deutsche
  Testname in `tests/test_identity_intake_paths.py`.

**Doku-Abgleich:** `README.md` „Project layout“ nennt jetzt „SQLite via
SQLModel“. Die Abhängigkeit kommt über `requirements.txt` in Entwicklung
und Image (`docker/Dockerfile` installiert sie); keine Anleitung zählt
Abhängigkeiten auf. `docker/README.md`, `unraid/README.md` und
`docs/plugin-authors.md` nennen keine Persistenzinterna. `LICENSING.md`
verweist allgemein auf die Lizenzen installierter Abhängigkeiten;
SQLModel und SQLAlchemy stehen unter MIT. Image-Größe nicht gebaut
(Docker-Build nur auf Auftrag); gemessen in der venv: SQLAlchemy 19 MB,
sqlmodel 0,3 MB.

**Standards** (`code-standards` mit `architecture.md`, `python.md`,
`persistence.md`, `quality.md`, `documentation.md`):

| Referenzgruppe | Ergebnis |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ PRAGMAs aus einer Funktion (`configure_connection`), Detail-Upserts einmal (`put_provider`/`put_manual` auch für die Übernahme); Namen englisch |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ Typen mit `col()`/`table_of`/`CursorResult`; Ruff grün |
| Datenbanken und Persistenzgrenzen | ✅ SQLModel für die fünf Kerntabellen, Doku vorher nachgeschlagen, keine ORM-Typen außerhalb (Wächter); vier Tabellen bis T-92 über `text()` |
| Fehler, Logging und Tests | ✅ Spaltenabgleich, paralleler Schreiber, verlorener Anlegeversuch, Gegenproben; temporäre Datenbanken |
| Markdown und Inhaltsverzeichnisse | ✅ README-Projektaufbau |

**Gelesene Lessons:** `CLAUDE-LESSONS.md`, besonders P-02 (Abweichungen
oben offen statt „wie geplant“), P-08 (der Test für den Anlegeversuch
erzeugt den Konflikt selbst) und P-12 (Inventar über alle Dateien).

**Umfang geplant / tatsächlich:** 5 / 5 fachliche Änderungen; 1 / 1 neue
Abhängigkeit; Produktdateien 6 / 6; Diff **900 / 1.233 Zeilen**
(Produkt 972 = +624 −348, Tests 261). Die Überschreitung kommt fast ganz
aus `repository.py`: Jede der rund 30 Methoden ist umgeschrieben, und die
Typumstellung auf `col()` berührte jede Bedingung ein zweites Mal.

Kein Merge, kein Push.
