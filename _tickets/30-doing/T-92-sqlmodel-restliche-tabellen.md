# T-92 · SQLModel für die übrigen Tabellen

**Warum dieses Ticket:** Nach T-91 nutzen die Kerntabellen SQLModel. T-92
zieht die übrigen Tabellen nach und schließt damit den Persistenzumbau ab.
Danach endet die befristete Ausnahme aus T-89.

**Beispiel:** Wechselkurse (`fx_rates`) und Metadaten (`meta`) werden heute
noch per SQL gelesen; nach T-92 über SQLModel-Modelle.

**Stand:** Angelegt am 2026-10-02 aus T-90 (Mike: „Drei Tickets
nacheinander“). Aktiv seit 2026-10-02 als fünftes Ticket in `30-doing/`
auf Mikes ausdrückliche Freigabe; Coder `claude`, Verifier `codex`,
maßgeblich ist `STATUS.md`. Die visuelle Gesamtprüfung folgt in T-93. Für
Mike steht kein Handgriff an.

## Scope-Vertrag (Claude, 2026-10-02)

**Ausgangslage (gemessen nach T-91):** Zur Laufzeit lesen und schreiben
`repository.py` (`daily_meta`, `fx_rates`, `meta`) und `detail_store.py`
(`meta`, `instrument_overrides`) noch per `text()`; `db.stored_rejections`
liest `migration_rejections` roh. Roh bleiben sollen nach dem Ticket nur
Schema, Altdaten-Migration, Backup und Plugin-Migration.

- **Ergebnis:** `daily_meta`, `fx_rates`, `meta`, `instrument_overrides`
  und `migration_rejections` haben SQLModel-Modelle; alle Laufzeitwege
  lesen und schreiben sie darüber. Verbleibendes rohes SQL steht nur in
  den Schema-, Migrations-, Backup- und Plugin-Migrationsmodulen und ist
  dort begründet. Verhalten, API und Daten bleiben unverändert.
- **Fachliche Änderungen (3):**
  1. Fünf Modelle in `tables.py`; der Spaltenabgleich aus T-91 deckt sie
     mit ab (frisch und umgezogen).
  2. `repository.py`, `detail_store.py` und `db.stored_rejections` ohne
     `text()`. Das DDL der Detailtabellen wandert aus `detail_store.py` zum
     übrigen Schema in `db.py`, damit der Detailspeicher reiner ORM-Code ist.
  3. Begründung je verbleibender Rohstelle im Code (Schema/DDL,
     `VACUUM INTO`/`PRAGMA`, Altdaten-Migration in einer Transaktion,
     Nur-Lese-Zugriff auf Sicherungsdateien, Plugin-Migration mit
     `BEGIN IMMEDIATE`). Die T-89-Ausnahme in `STATUS.md` entfällt.
- **Tests:** bestehende Suite grün; Spaltenabgleich erweitert; ein
  Wächter, dass die Laufzeitmodule (`repository.py`, `detail_store.py`)
  kein rohes SQL mehr enthalten, mit Gegenprobe.
- **Sichtbare Prüfung:** Temp-Instanz: Wechselkurse, Sicherung anlegen und
  wiederherstellen, Einstellungen, Detailbereich mit manueller Eingabe;
  Migrationsvorschau mit Alt-Datenbank.
- **Doku:** README, `docker/README.md`, `unraid/README.md` prüfen;
  voraussichtlich keine Änderung (keine Aussage zur Zugriffsschicht außer
  dem Projektaufbau).
- **Budget:** 0 neue Abhängigkeiten; Produktdateien rund 6; Diff höchstens
  600 Zeilen.
- **Nicht-Ziele:** keine Schemaänderung, kein `create_all`, keine
  Umstellung von Migration, Backup und Plugin-Migration auf das ORM, keine
  Änderung an StockPortfolio.

## Umfang

- Tabellen: `daily_meta`, `fx_rates`, `meta`, `instrument_overrides`,
  `migration_rejections`.
- Altdaten-Migrationen (`app/persistence/db.py`, `migration.py`), Backup
  (`VACUUM INTO`, `PRAGMA user_version`) und die Plugin-Migration bleiben
  begründet rohes SQL im Persistenzordner; die Begründung steht je Stelle
  im Code.
- Die befristete Ausnahme aus T-89 in `STATUS.md` wird entfernt.

### Akzeptanzkriterien

- [ ] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [ ] Jedes verbleibende rohe SQL steht in `app/persistence/` und ist dort
      begründet.
- [ ] Backup, Wiederherstellung und Migrationsvorschau funktionieren
      unverändert; Tests mit temporärer Datenbank belegen das.
- [ ] Die T-89-Ausnahme in `STATUS.md` ist entfernt.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Wechselkurse,
      Backup, Einstellungen.

### Side-Effects

Keine Änderung an API oder Vertrag.
