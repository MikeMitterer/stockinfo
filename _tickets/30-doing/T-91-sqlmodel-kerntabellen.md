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

- [ ] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [ ] Bestehende Daten funktionieren ohne Migration; Tests mit temporärer
      Datenbank und einer Datenbank im Altformat belegen das.
- [ ] Außerhalb `app/persistence/` gibt es keine ORM-Typen.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Aufnahme und Löschen eines Instruments.

### Side-Effects

Neue Abhängigkeit `sqlmodel` (zieht SQLAlchemy nach); Docker-Image wird
größer. Keine Änderung an API oder Vertrag.
