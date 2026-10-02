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

- [x] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [x] Jedes verbleibende rohe SQL steht in `app/persistence/` und ist dort
      begründet.
- [x] Backup, Wiederherstellung und Migrationsvorschau funktionieren
      unverändert; Tests mit temporärer Datenbank belegen das.
- [x] Die T-89-Ausnahme in `STATUS.md` ist entfernt.
- [x] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Wechselkurse,
      Backup, Einstellungen.

### Side-Effects

Keine Änderung an API oder Vertrag.

### Verify

Aktuelle Statusmatrix; sie wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `tests/test_persistence_tables.py` | Alle zehn Modelle tragen genau die Spalten ihrer Tabelle, frisch und umgezogen (`migration_rejections` nur umgezogen, frisch gibt es sie nicht) | ✅ |
| 2 | `tests/test_persistence_boundary.py` | `repository.py`, `detail_store.py`, `meta_store.py`, `tables.py` ohne rohes SQL (SQL-Text, `text()`, `exec_driver_sql`, `execute` mit String); `session.py` ebenso bis auf genau `BEGIN`/`BEGIN IMMEDIATE`; Gegenproben | ⚠️ |
| 3 | Rohe Stellen | Daten-SQL nur in `db.py`, `migration.py`, `backup_store.py`, `data_versions.py`, `plugin_migration.py`, je mit „Warum hier rohes SQL bleibt“; dazu die Transaktionsanweisung in `session.py`, dort begründet | ⚠️ |
| 4 | Backend, Plugin-API, Ruff | Backend 1308, Plugin-API 324, Ruff grün | ✅ |
| 5 | Browser mit Temp-Datenbank | Wechselkurs abrufen und aus dem Cache lesen, Einstellungen, manuelle Eingabe, Sicherung mit echtem Wiederherstellen | ✅ |
| 6 | Browser mit Alt-Datenbank | Vorschau, Bestätigung, Bericht über das Modell | ✅ |
| 7 | `STATUS.md` | T-89-Ausnahme entfernt | ✅ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Nacharbeit Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `7d0be5e` gegen `833e3cf` (Nacharbeit) und gegen `master`
`f4bc8ef` (Gesamtstand).

- **B1 · `BEGIN` in `session.py`:** Die Ausnahme ist jetzt benannt —
  im Modul-Docstring und am Aufruf von `session.py` sowie in Verify #2/#3.
  Der Wächter zählt zusätzlich jeden `exec_driver_sql(...)`-Aufruf und
  jedes `execute(...)`, dessen erstes Argument ein String ist (Spaltennamen
  in SQLAlchemy-Ausdrücken zählen nicht). Für `session.py` sind genau
  `BEGIN` und `BEGIN IMMEDIATE` zugelassen. Belege:
  - `raw_sql(session.py)` ohne Ausnahme: `49: exec_driver_sql(...)`; mit
    Ausnahme leer — der Wächter sieht die Stelle also wirklich.
  - Neue Gegenprobe `test_die_transaktionsausnahme_gilt_nur_fuer_begin`:
    `PRAGMA …`, `COMMIT` und `execute('VACUUM')` neben dem erlaubten
    `BEGIN` werden gefunden; ohne Ausnahme auch das `BEGIN`.
  - Mutant im echten `session.py` (zusätzliches
    `exec_driver_sql("PRAGMA defer_foreign_keys = ON")`):
    `test_die_laufzeitmodule_enthalten_kein_rohes_sql[session.py]` rot;
    zurückgesetzt.
  - Gegen den Stand von T-91 meldet der Wächter weiterhin die alten
    `text()`-Stellen in `repository.py`.
- **Läufe:** Backend **1309 passed, 36 skipped** (+1 Gegenprobe), Ruff
  `app tests`, `git diff --check` grün.

**Doku-Abgleich:** unverändert; keine Anleitung betroffen.

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-02)

**Prüfstand:** `833e3cf` gegen `f4bc8ef`. Rollen, Owner, Priorität,
Ticketpfad und Branch stimmten; keine Produktänderung nach der Übergabe.
Paket-VERSION vor diesem Durchlauf unverändert:
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
**Ergebnis: `changes_requested`**, Runde 1 von höchstens 5. Kein Merge,
Push oder menschliche Abnahme durch Codex.

**B1 · Der Roh-SQL-Grenztest bestätigt eine falsche Aussage.** Verify #2
zählt `session.py` zu den Modulen „ohne SQL-Text“, #3 nennt genau fünf
Module mit verbleibendem rohem SQL. Tatsächlich setzt
`app/persistence/session.py:49` über
`connection.exec_driver_sql("BEGIN IMMEDIATE" if immediate else "BEGIN")`
rohes Transaktions-SQL ab. Die unabhängige Gegenprobe
`raw_sql(Path("app/persistence/session.py").read_text())` liefert `[]`:
Der neue Wächter in `tests/test_persistence_boundary.py` erkennt diese
Anweisungen nicht, lässt `session.py` aber als angeblich ORM-reines Modul
durch. Das `BEGIN` ist als Teil des SQLAlchemy/SQLite-Rezepts fachlich
begründet und soll erhalten bleiben. Bitte die Ausnahme im Scope und in
der Verify-Matrix genau benennen und den Grenztest auf die tatsächlich
zugesagte Grenze ausrichten: Kein rohes Daten-SQL in den Laufzeitmodulen;
in `session.py` nur die begründeten Transaktionsanweisungen. Ein
abweichendes rohes Statement muss als negative Gegenprobe rot werden.
Die fünf bisher genannten Rohmodule bleiben mit ihrer Begründung bestehen.

**Übrige Prüfung:** Die fünf neuen Tabellenmodelle tragen nach dem
Schemaabgleich genau ihre Spalten; der Umzugsbericht wird nur beim Umzug
angelegt. `repository.py`, `detail_store.py` und `meta_store.py` nutzen
Modellausdrücke. Laufzeitwerte in `meta` werden über den gemeinsamen
`meta_store` gelesen oder geschrieben; das Detail-DDL liegt nun beim
übrigen Schema. Die Rohzugriffe für Altformat, Sicherungen und
Plugin-Migration sind im Persistenzordner begründet. Browserbilder für
Wechselkurs, Einstellungen, manuelle Eingabe, Restore und
Migrationsvorschau angesehen; die umfassende visuelle Gesamtprüfung ist
ausdrücklich T-93. Die historische T-89-Ausnahme ist als geltende
Ausnahme entfernt; frühere Entscheidungen bleiben als Archiv erhalten.

**Unabhängige Läufe:** **1293 passed, 36 skipped** im netzunabhängigen
Backend; 15 unveränderte netzabhängige Tests waren in T-91 Runde 1
erfolgreich, zusammen 1308 bestandene Backend-Tests. Plugin-API
**324 passed, 1 skipped**. Ruff `app tests scripts` und
`git diff --check` grün. AST-Inventar über alle 11 geänderten
Python-Dateien: 3250 Bezeichnervorkommen, deutsche Treffer nur in
zulässigen Testnamen. Verify #1 und #4–#7 sind ✅, #2–#3 bleiben wegen
B1 ⚠️.

**DRY-Prüfung:** Im Diff und den benachbarten Persistenzmodulen
`meta`-Zugriffe, Upserts, Detail-DDL und Versionsstempel gesucht.
`meta_store` bündelt die Laufzeitregel, während Schema- und
Altformatzugriffe begründet eigene rohe Verbindungen nutzen; keine
doppelte neue Fachregel gefunden.

**Doku-Abgleich:** `README.md` nennt den SQLModel-Zugriff bereits;
`docker/README.md` und `unraid/README.md` beschreiben Betrieb und
SQLite-Datei ohne veraltete Aussage zur internen Zugriffsschicht.
Keine Anpassung nötig. Die getrennte Board-Übernahme `df699dd1` bleibt
offen. Gelesen: `/Users/macminipro/.codex/skills/code-standards/SKILL.md`
mit `architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`; `task-verification-workflow` und lokale
Autor-Lessons.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ Persistenzzugriffe im zuständigen Ordner, `meta`-Regel gebündelt, AST- und DRY-Inventar oben. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff; Bilder der Übergabe angesehen |
| Python, FastAPI und Webhooks | ✅ Backend-Lauf, Ruff und frischer Import über die Suite grün. |
| Datenbanken und Persistenzgrenzen | ⚠️ 1 Befund B1: Die tatsächliche Transaktions-SQL-Ausnahme fehlt in Grenze und Gegenprobe. |
| Fehler, Logging und Tests | ⚠️ 1 Befund B1: Der neue Wächter meldet trotz `exec_driver_sql("BEGIN …")` keinen Treffer. |
| Markdown und Inhaltsverzeichnisse | ✅ Anleitungen inhaltlich abgeglichen; Ticketnachweis ergänzt. |

## Übergabe Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `833e3cf` gegen `master` (`f4bc8ef`). Produktcommits:
`81d9434` (Umstellung, Begründungen, Wächter, STATUS) und `833e3cf`
(Tabellenname typgerecht).

**Über den Scope-Vertrag hinaus, je begründet:**

- **`stamp_versions` und `write_stamp_if_missing` auf die Modelle.** Beim
  Begründen der Rohstellen hielten zwei nicht: Beide schreiben die
  **laufende** Datenbank beim Start, ohne Bezug zu Migration oder fremden
  Sicherungen. Statt einer schiefen Begründung laufen sie jetzt über
  `meta_store.put_meta`/`put_meta_if_missing`.
- **`meta_store.py` (neu):** `get_meta`, `put_meta`, `put_meta_if_missing`
  für alle Laufzeitzugriffe auf `meta` — sonst stünde dieselbe Abfrage in
  Repository, Detailspeicher, Datenversionen und Backup je einmal.

**Coder-Belege:**

- **#1:** 19 Fälle grün, 1 übersprungen (frischer `migration_rejections`).
  Das Alt-Fixture des Tests hat dafür eine Zeile ohne Börsenendung, die der
  Umzug ablehnt; der Test prüft vorher, dass der Umzug lief.
- **#2:** Neuer Wächter `test_die_laufzeitmodule_enthalten_kein_rohes_sql`.
  Gegen den Stand von T-91 (`git show master:…/repository.py`) meldet er
  die `text()`-Aufrufe für `daily_meta` und `fx_rates`; Gegenprobe im Test
  mit `text('SELECT … FROM meta …')`. Die alte Gegenprobe „Prüfung schlägt
  im Persistenzordner an“ prüft jetzt `db.py`, weil `repository.py` kein
  SQL mehr enthält.
- **#3:** Inventar aller Module in `app/persistence/`: SQL-Text oder rohe
  `execute` nur noch in den fünf genannten; jedes trägt die Begründung.
  Die Behauptungen dort am Code geprüft (etwa: `migration.py` baut über
  `instruments_hardened` neu auf, nicht über `CREATE TABLE … AS`; die erste
  Fassung des Textes stimmte nicht und ist korrigiert).
- **#4:** Backend **1308 passed, 36 skipped**, Plugin-API **324 passed,
  1 skipped**, Ruff `app tests scripts` und `git diff --check` grün; alle
  Module importieren in frischem Prozess. Pyright über die geänderten
  Persistenzdateien: keine neuen Befunde (die 10 älteren aus T-91 in
  unverändertem Code bleiben).
- **#5:** Temp-Instanz, sichtbares Chrome.
  [Wechselkurs](T-92-browser-fx.png) EUR→USD per „Convert“: 1,128 von
  yfinance; der zweite API-Aufruf kommt aus dem Cache (`cached: true`,
  `source: yfinance`) — Schreiben und Lesen von `fx_rates` über das Modell.
  [Einstellungen Environment](T-92-browser-settings-environment.png) und
  [About](T-92-browser-settings-about.png) auf Deutsch.
  [Manuelle Eingabe](T-92-browser-manual-reloaded.png) übersteht Neuladen,
  danach entfernt. Sicherung angelegt und
  [vorgemerkt](T-92-browser-restore-pending.png), `GOLD.SG` gelöscht,
  Neustart: `backup_created reason=pre-restore`, `restore_applied`,
  `restore_completed`; [danach](T-92-browser-restored-dashboard.png)
  wieder fünf Instrumente.
- **#6:** Alt-Datenbank: [Vorschau](T-92-browser-migration-preview.png)
  (2 umziehend, XYZ abgelehnt), `POST /migration/confirm`, Bericht mit
  demselben Eintrag; vor dem Umzug `completed: false` wie bisher.
- **Bezeichner:** AST-Inventar über alle 11 geänderten Python-Dateien,
  3.250 Vorkommen, kein nicht-ASCII-Name.

**Doku-Abgleich:** `README.md` „SQLite via SQLModel“ bleibt zutreffend;
`docker/README.md`, `unraid/README.md` und `docs/plugin-authors.md` sagen
nichts über die Zugriffsschicht. Keine Änderung nötig.

**Standards** (`code-standards` mit `architecture.md`, `python.md`,
`persistence.md`, `quality.md`, `documentation.md`):

| Referenzgruppe | Ergebnis |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ `meta`-Zugriff an einer Stelle (`meta_store`), Detail-DDL beim übrigen Schema; Namen englisch |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ Ruff grün, keine neuen Typbefunde |
| Datenbanken und Persistenzgrenzen | ✅ alle Tabellen mit SQLModel-Modell; rohes SQL nur in Schema, Migration, Backup und Plugin-Migration, je begründet; Wächter für die Laufzeitmodule |
| Fehler, Logging und Tests | ✅ Spaltenabgleich, Wächter mit Gegenprobe; temporäre Datenbanken |
| Markdown und Inhaltsverzeichnisse | ✅ keine Doku-Änderung nötig, begründet |

**Gelesene Lessons:** `CLAUDE-LESSONS.md`, besonders P-02 (zwei
Begründungen hielten nicht — offen genannt und behoben statt stehen
gelassen) und P-12 (Inventar über alle Persistenzmodule).

**Umfang geplant / tatsächlich:** 3 / 3 fachliche Änderungen; 0 / 0 neue
Abhängigkeiten; Produktdateien rund 6 / 9; Diff 600 / 447 Zeilen
(Produkt 374 = +250 −124, Tests 73). Mehr Dateien, weil jede der fünf
Rohstellen ihre Begründung im eigenen Modul trägt.

Kein Merge, kein Push.
