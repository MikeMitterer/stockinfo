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
| 1 | `tests/test_persistence_boundary.py` | Kein SQL und kein direkter Zugriff auf die aktive SQLite-Datei außerhalb `app/persistence/`; Gegenproben erkennen auch einfache Pfad-Aliase beim physischen Restore | ⚠️ B5 |
| 2 | `git diff -M --summary master..HEAD` | Fünf Umbenennungen nach `app/persistence/`, keine Weiterleitungsmodule an den alten Pfaden | ✅ |
| 3 | `app/container.py`, Dienste, `routers/fields.py` | `QuoteRepository` wird nur in `get_quote_store()` gebaut; Dienste und Feldrouter kennen nur `QuoteStore` und unabhängige Domänentypen | ✅ |
| 4 | Backend, Plugin-API, Ruff | Backend 1273 grün, Plugin-API 324 grün, `ruff check app tests scripts` und `plugin_api` ohne Befund | ✅ |
| 5 | Browser mit Temp-Datenbank | Dashboard und Detailbereich wie vorher; Backup anlegen, vormerken, Neustart stellt den gelöschten Eintrag wieder her | ✅ |
| 6 | Browser mit Alt-Datenbank | Migrationsvorschau, Bestätigung und Bericht laufen über die verlagerten Funktionen | ✅ |
| 7 | Doku | Projektaufbau im `README.md` nennt `persistence/` und seine Aussage „data access (only here)“ stimmt mit dem aktuellen Code überein | ✅ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Nacharbeit Runde 3 (Claude, 2026-10-02)

Prüfgegenstand: `65d7f05` gegen `44f72ab` (Nacharbeit) und gegen `master`
`de620e9` (Gesamtstand). Nur `tests/test_persistence_boundary.py`
geändert; kein Produktcode.

- **B5 · Alias des Datenbankpfads:** Der Wächter verfolgt jetzt die
  Herkunft des Pfads. Eine Zuweisung, deren Wert auf die Datenbank zeigt
  (`path = Path(database_path)`), macht den Namen zum Datenbankpfad, auch
  über Ketten (`target = Path(settings.database_path)`, `file = target`).
  Lokale Namen gelten je innerster Funktion, Attribute
  (`self._file = …`) in der ganzen Datei. `.parent` beendet die Spur: Das
  Verzeichnis ist nicht die Datei — so bleiben Sicherungsverzeichnis,
  Absichtsdatei und Archivdateien beim Dienst.
- **Gegenproben:**
  - Neuer Test mit genau dem Mutanten aus dem Review
    (`path = Path(database_path); os.replace(incoming, path)`) und einer
    Kette über zwei Zuweisungen bis `stat()`: beide gefunden;
    `Path(database_path).parent` mit `exists()` nicht.
  - **Mutant im echten Produktcode:** `replace_database(...)` in
    `apply_pending` testweise durch `path = Path(database_path)` und
    `os.replace(source, path)` ersetzt: Der Wächter wird rot und meldet
    genau `app/services/backup.py` Zeile 401 `os.replace(Datenbank)`.
    Zurückgesetzt, `git diff -- app` leer.
  - Ein erster Entwurf sammelte Aliase dateiweit; am Mutanten meldete er
    zusätzlich vier unbeteiligte Stellen (226, 269, 357, 480), weil `path`
    in anderen Funktionen dasselbe Wort ist. Deshalb je Funktion.
  - Alter Stand `88d54d8`: Jetzt findet er auch, was vorher durchrutschte —
    `stamped_fingerprint` (`path.is_file()`, Zeile 445) und die
    `.incoming`-Kopie (404, 410). Die Archivprüfung in `resolve` (Zeile
    356) bleibt korrekt unberührt.
  - Aktueller Stand: 56 Dateien außerhalb `app/persistence/` ohne Treffer.
- **Verbleibende Grenze, bewusst nicht verfolgt:** Ein Datenbankpfad, der
  als Argument unter anderem Namen in eine andere Funktion wandert, sowie
  Tupel-Zuweisungen und Closures. Das wäre Datenflussanalyse über
  Funktionen hinweg — das Test-Subsystem, das Codex ausgeschlossen hat.
- **Läufe:** Backend **1274 passed, 35 skipped** (1 neue Gegenprobe), zwei
  Läufe mit verschiedenen `PYTHONHASHSEED`; Ruff `app tests scripts` und
  `git diff --check` grün. Kein Produktdiff, daher kein neuer Browserlauf;
  die Restore- und Migrationsbilder aus Runde 2/3 gelten.
- **Bezeichner:** neu nur `_database_aliases`, `_scoped_aliases` und deren
  lokale Namen (`scope`, `known`, `attributes`, `module_level`, `owners`,
  `local`), dazu ein deutscher Testname.

**Doku-Abgleich:** Nur der Modul-Docstring des Tests beschreibt die neue
Erkennung; Anleitungen sind nicht betroffen.

## Verifier-Prüfung · Runde 3 (Codex, 2026-10-02)

**Prüfstand:** `44f72ab` gegen `88d54d8`, Gesamtstand gegen `de620e9`.
Rollen, Owner, Priorität, Ticketpfad und Branch stimmten; nach dem
Produktcommit folgten nur Boarddateien. Paket-VERSION
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`
vor dem Durchlauf unverändert. Mike hat das Limit ausdrücklich auf **5**
angehoben; Runde 3 von höchstens 5. **Ergebnis: `changes_requested`**
wegen eines verbleibenden Testlochs. Keine technische oder menschliche
Abnahme.

**B4 im Produkt behoben.** `app/services/backup.py` steuert die
Wiederherstellung und ruft `backup_store.replace_database` auf. Kopie,
atomarer Austausch und WAL/SHM-Bereinigung liegen jetzt in
`app/persistence/backup_store.py`. Auch die Existenzfragen in
`apply_pending`, `stamped_fingerprint` und `app/main.py` sind in den
Persistenzordner gezogen. Der Dienst enthält keinen `shutil.copy2` mehr.
Der Coder-Gegenlauf findet am alten Stand die benannten Datei-Operationen;
am aktuellen Produktstand habe ich keine direkte Operation auf die laufende
DB-Datei außerhalb des Ordners gefunden. Die neuen Browserbilder zeigen
die vorgemerkte Wiederherstellung und danach `GOLD.SG` wieder im Dashboard.

### Befund für Runde 4

**B5 · Der neue Wächter übersieht einen einfachen Pfad-Alias.**
`tests/test_persistence_boundary.py:52–75` erkennt Dateizugriffe nur,
wenn ein Argument oder Attribut einen Namen mit `database` enthält.
Die unabhängige In-Memory-Gegenprobe mit
`path = Path(database_path); os.replace(incoming, path)` außerhalb der
Persistenz liefert von `database_accesses` **`[]`**. Dieser minimale
Mutant schreibt wieder auf die aktive Datenbankdatei und verletzt genau
Akzeptanzkriterium #1; die Suite bliebe dennoch grün. Die Übergabe nennt
diese Grenze selbst, behandelt den Namen aber als Konvention. `AGENTS.md`
fordert englische Bezeichner, keinen bestimmten Variablennamen für einen
DB-Pfad. Bitte den Test so schärfen, dass er mindestens den einfachen
Alias von `database_path` über `Path(...)` bis zum Dateiaufruf verfolgt,
und den Mutanten rot belegen. Eine kleine AST-Ergänzung genügt; kein
eigenes Analyse- oder Test-Subsystem.

**Rest:** B5 ist ein blockierender Nachweisfehler für das ausdrücklich
geforderte Testgate; der aktuelle Produktpfad B4 ist korrigiert. Der
Aliasfall blieb offen, weil die neue Prüfung an Namen statt an der
Herkunft des Pfads hängt. Claude ergänzt die Gegenprobe und den Wächter;
Codex prüft die eingefrorene Runde-4-Fassung. T-91/T-92 folgen erst nach
T-90-Freigabe. Zwei reguläre Runden bleiben nach Mikes neuem Limit.

### Weitere Gegenproben und Standards

- **#4:** Unabhängig **1273 passed, 35 skipped** im Backend, gezielt
  **51 passed** für Grenz- und Backuptests; Ruff für
  `app tests scripts plugin_api` und `git diff --check` grün. Plugin-API
  **324 passed, 1 skipped** aus Runde 1 bleibt ohne Plugin-Diff gültig.
- **#5–#6:** Beide neuen Browserbilder angesehen. Der sichtbare
  Restore-Pfad zeigt `GOLD.SG` wieder; Migrationspfad seit Runde 2
  unverändert. Backendtests laufen mit temporärer Datenbank.
- **Bezeichner:** AST-Inventar über alle 78 im Gesamtstand geänderten
  Python-Dateien: 22.272 Name-/Argument-/Funktions-/Klassenvorkommen,
  nur der nach `AGENTS.md` zulässige deutsche Testname mit Nicht-ASCII.
- **Doku-Abgleich:** `README.md` „data access (only here)“ stimmt mit dem
  aktuellen Produktcode überein. `docker/README.md`, `unraid/README.md`,
  `docs/plugin-authors.md` und `AGENTS.md` enthalten keine veralteten
  Modulpfade. T-91/T-92 bleiben geplante ORM-Schritte; Mikes Ticketschnitt
  ist weiterhin die lokale Ausnahme.

**Gelesener Standard:**
`/Users/macminipro/.codex/skills/code-standards/SKILL.md`, Referenzen
`architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`; lokale Claude-Lessons aus dem vollständigen Inventar,
insbesondere SI-P-02, SI-P-08, SI-P-11, SI-P-12 und SI-P-13.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ Dateiaustausch und DB-Dateiprüfung im Persistenzordner, keine neue doppelte Logik; Bezeichnerinventar vollständig. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff; Browserbilder geprüft |
| Python, FastAPI und Webhooks | ✅ DI und Interface unverändert; 1273 Backendtests grün. |
| Datenbanken und Persistenzgrenzen | ✅ B4 im Produkt behoben; physischer DB-Tausch und Dateiprüfung liegen im zuständigen Ordner. ORM folgt nach Mikes Ticketschnitt. |
| Fehler, Logging und Tests | ⚠️ B5: einfacher Pfad-Alias entgeht dem AST-Wächter trotz grünem Gesamtlauf. |
| Markdown und Inhaltsverzeichnisse | ✅ README-Inhalt mit aktuellem Code konsistent; übrige Anleitungen ohne alten Pfad. |

Codex änderte keinen Produktcode und erteilte keine menschliche Abnahme.
Die getrennte Board-Übernahme aus Paketfassung `df699dd1` bleibt offen.

## Nacharbeit Runde 2 (Claude, 2026-10-02)

Prüfgegenstand: `44f72ab` gegen `88d54d8` (Nacharbeit) und gegen `master`
`de620e9` (Gesamtstand). Ein Produktcommit.

**Grenze, jetzt ausdrücklich:** Jeder Zugriff auf die **laufende**
Datenbankdatei samt Journalen liegt in `app/persistence/`. Die
Sicherungsdateien verwaltet der Dienst als Archiv (Namen, Rotation,
Manifeste); ihren Inhalt liest er nur über `read_stamp`. So steht es auch im
Modul-Docstring von `backup_store.py`.

- **B4 · Restore-Tausch:** `backup_store.replace_database(database_path,
  source)` kopiert über `.incoming`, tauscht atomar und löscht `-wal`/`-shm`;
  scheitert ein Schritt, entfernt sie `.incoming` und reicht den Fehler
  weiter. `apply_pending` steuert nur noch Absicht, Prüfung, Vorabsicherung,
  Aufruf und Fehlerzustand; `shutil` ist aus dem Dienst verschwunden.
- **Selbst gefunden, gleiche Klasse:** Drei weitere Datei-Abfragen auf die
  laufende Datenbank lagen außerhalb und sind mitgezogen:
  `apply_pending` (`database.is_file()` vor der Vorabsicherung) und
  `stamped_fingerprint` (`path.is_file()`) nutzen jetzt
  `backup_store.database_exists`; `app/main.py:107` (Existenz und Größe für
  „frische Datenbank“) nutzt `db.is_fresh_database`. Das Verhalten ist
  gleich: `is_file` bleibt `is_file`, „fehlt oder leer“ bleibt „fehlt oder
  leer“.
- **Wächter:** erkennt jetzt auch `os.replace`/`os.rename`/`os.remove`/
  `shutil.copy*`/`shutil.move` mit einem Argument, dessen Name `database`
  enthält, Pfadmethoden (`exists`, `is_file`, `stat`, `unlink`, `rename`,
  `replace`, `open`, …) auf einem solchen Pfad und die Strings `-wal`/`-shm`.
  Gegenproben:
  - Alter Stand (`git show 88d54d8:…`): `app/services/backup.py` meldet
    Zeilen 401 (`is_file`), 405 (`os.replace`), 406 (`-wal`, `-shm`),
    407 (`unlink`); `app/main.py` Zeile 107 (`exists`, `stat`). Neuer Stand:
    beide leer, ebenso alle 56 Dateien außerhalb.
  - Synthetischer Fall im Test: Tausch, Journal, Existenzfrage werden
    gefunden; Rotation mit anders benannten Archivpfaden nicht.
  - Echter `backup_store.py` muss mit `os.replace(Datenbank)` und
    `is_file()` anschlagen.
  - **Grenze des Wächters:** Er erkennt den Dateizugriff am Namen. Ein
    Datenbankpfad, der etwa `path` heißt, rutscht durch — so wie das alte
    `stamped_fingerprint`. Diese Stelle ist verlegt; für neue Fälle ist der
    Name die Konvention.
- **Test angepasst:** `tests/test_backup.py:764` setzte den Kopierfehler
  über `app.services.backup.shutil.copy2`; der Kopierschritt liegt jetzt in
  `app.persistence.backup_store`, das Patch-Ziel zieht mit. Die Prüfungen
  des Tests (Fehler sichtbar, kein `.incoming`, kein zweiter Versuch) sind
  unverändert und grün.
- **Stabile Reihenfolge:** Zwei Funde in derselben Zeile kamen aus einer
  Menge in wechselnder Reihenfolge; der Gesamtlauf fiel einmal. Sortiert
  wird jetzt nach Zeile und Text; drei Läufe mit verschiedenen
  `PYTHONHASHSEED` grün.
- **Läufe:** Backend **1273 passed, 35 skipped**; Restore-/Backup-Auswahl
  (`-k "restore or backup"`) grün, darunter der Journaltest
  `tests/test_backup.py:492–510`; Ruff `app tests scripts` und `git diff
  --check` grün. Plugin-API ohne Diff seit Runde 1 (**324 passed**).
- **Sichtbar, echter Restore mit Temp-Datenbank:** Backup per Oberfläche
  angelegt und vorgemerkt ([Hinweis](T-90-browser-r3-restore-pending.png)),
  `GOLD.SG` per API gelöscht (vier Instrumente), Neustart: Log
  `backup_created reason=pre-restore`, `restore_applied`,
  `restore_completed`; `restore-pending.json` ist weg. Das
  [Dashboard danach](T-90-browser-r3-restored-dashboard.png) zeigt wieder
  alle fünf Instrumente samt `GOLD.SG`.
- **Bezeichner:** Inventar über alle 78 geänderten Python-Dateien,
  22.272 Vorkommen; einziger nicht-ASCII-Name bleibt der zulässige
  Testname. Neu: `database_exists`, `replace_database`,
  `is_fresh_database`, `_JOURNAL_SUFFIXES`, `FILE_FUNCTIONS`,
  `PATH_METHODS`, `JOURNAL_SUFFIXES`, `_names_database`, `_file_access`,
  zwei deutsche Testnamen.

**Doku-Abgleich:** `README.md` „data access (only here)“ trifft jetzt auch
für Restore und Dateiprüfungen zu; `README.md:175` („`POST
/backups/{name}/restore` replaces the whole database with a backup“) bleibt
richtig. `docker/README.md` „Updates, backups and troubleshooting“
beschreibt nur die Sicherung des ganzen `/data`-Volumes von außen und ist
nicht betroffen. `unraid/README.md`, `docs/plugin-authors.md`, `AGENTS.md`
unverändert, weil sie keine Modulpfade nennen.

## Verifier-Prüfung · Runde 2 (Codex, 2026-10-02)

**Prüfstand:** `88d54d8` gegen `8804575`, Gesamtstand gegen `de620e9`.
Rollen, Owner, Priorität, Ticketpfad und Branch stimmten; der Übergabecommit
`a5b4ac3` enthielt nur Boarddateien. Paket-VERSION
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`
vor dem Durchlauf unverändert. **Ergebnis: `changes_requested`**. Runde 2
von höchstens 3; eine reguläre Runde bleibt. Keine technische oder
menschliche Abnahme.

**B1–B3 behoben.** `identity_where` liegt jetzt beim einzigen Aufrufer in
`app/persistence/repository.py`. Die neue AST-Gegenprobe meldet am alten
`app/models.py` genau die drei SQL-Fragmente in Zeilen 361, 365 und 367,
am neuen Modell keinen Treffer. `_REPORT_COLUMNS` entfiel; `stored_rejections`
liest `SELECT *`, und der Router leitet seine Feldliste aus
`RejectedInstrument.model_fields` ab. Die neun Felder stimmen im Lauf
überein. `SavedQuote` und `PROTECTED_META_FIELDS` stehen einmalig im
Interface-Modul; dessen Import lädt die konkrete Repository-Datei nicht.
`quote_cache.py` importiert keine Repository-Implementierung mehr. Der
Type-/Feldvertrag ist damit unabhängig.

### Befund für Runde 3

**B4 · Der Restore ersetzt die Datenbankdatei außerhalb des
Persistenzordners.** `app/services/backup.py:365–419` enthält
`apply_pending`. Die Funktion kopiert das gewählte Backup mit
`shutil.copy2(source, temporary)`, ersetzt die aktive SQLite-Datei mit
`os.replace(temporary, database)` und löscht danach deren `-wal`-/`-shm`-
Dateien. Das ist ein direkter Schreibzugriff auf Datenbankdatei und Journale
außerhalb `app/persistence/`; T-90 verspricht ausdrücklich auch „keinen
Datenbankzugriff“ außerhalb dieses Ordners. Der neue
`database_accesses`-Wächter meldet für das gesamte
`app/services/backup.py` dennoch `[]`, weil er nur SQLite-Importe,
`execute` und SQL-Strings erkennt. Bitte den physischen Austausch samt
Journalbereinigung in `app/persistence/backup_store.py` oder eine dortige
zuständige Funktion verlegen. Der Dienst soll Zeitpunkt, Auswahl,
Vorabsicherung und Fehlermeldung steuern. Den echten Restore mit temporärer
DB erneut prüfen und die Grenze so gegenprüfen, dass genau dieser übersehene
Pfad sichtbar wäre; kein neues Test-Subsystem.

**Rest für die Maximalrunde:** B4 ist blockierend, weil er dem eigenen
T-90-Akzeptanzkriterium und der technischen Zugriffsgrenze widerspricht;
der Restore schreibt tatsächlich auf die aktive Datenbankdatei. Er blieb
offen, weil Runde 1 SQL, Verbindung und Interface inventarisierte, den
physischen Wiederherstellungstausch im schon vorhandenen Backup-Dienst aber
übersah. Nächster Schritt: Claude verlegt diesen Tausch im T-90-Branch,
belegt die Grenze und die unveränderte Wiederherstellung; Codex prüft die
konkrete Runde-3-Fassung. T-91/T-92 hängen von einem technisch freigegebenen
T-90 ab. Weitere Befunde sind derzeit nicht offen.

### Weitere Gegenproben und Standards

- **#4:** Unabhängig **1271 passed, 35 skipped** im Backend, gezielt
  **33 passed** für Persistenzgrenze und Migrationsendpunkte; Ruff für
  `app tests scripts plugin_api` und Gesamt-Diff-Prüfung grün. Die
  Plugin-API **324 passed, 1 skipped** aus Runde 1 ist seitdem ohne
  Plugin-Diff. Grüne Tests lösen B4 nicht auf.
- **#5–#6:** Das neue Bild der Alt-Datenbank-Vorschau angesehen: zwei
  umziehende, ein abgelehntes Instrument. Dashboard- und Backupbilder aus
  Runde 1 gelten für den dort unveränderten Code; die physischen
  Restore-Operationen blieben bis jetzt unverändert.
- **Bezeichner:** Eigenes AST-Inventar über alle 78 im Gesamtstand
  geänderten Python-Dateien: 22.163 Name-/Argument-/Funktions-/
  Klassenvorkommen, nur ein zulässiger deutscher Testname mit Nicht-ASCII.
- **Doku-Abgleich:** `README.md:527` sagt „data access (only here)“; das
  trifft wegen B4 noch nicht vollständig zu. `docker/README.md`,
  `unraid/README.md`, `docs/plugin-authors.md` und `AGENTS.md` nennen keine
  alten Modulpfade und widersprechen dem geplanten Endstand nicht. T-91/T-92
  und die befristete ORM-Ausnahme bleiben im Board sichtbar.

**Gelesener Standard:**
`/Users/macminipro/.codex/skills/code-standards/SKILL.md`, Referenzen
`architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`; Claudes lokale Lessons nach dem vollständigen
`lessons/`-Inventar, insbesondere SI-P-02, SI-P-08, SI-P-11, SI-P-12 und
SI-P-13. Vor der Runde wurde das gemeinsame VERSION erneut geprüft.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ⚠️ B4 physischer DB-Tausch im Backup-Dienst; B2/B3 beseitigt, Bezeichnerinventar vollständig. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ kein Skriptverhalten im Runde-2-Diff |
| TypeScript, Vue und i18n | ➖ kein UI-Diff; Browserbelege angesehen |
| Python, FastAPI und Webhooks | ✅ `QuoteStore` ohne konkreten Repository-Import, FastAPI-DI unverändert; Backendtests grün. |
| Datenbanken und Persistenzgrenzen | ⚠️ B4: `copy2`, `os.replace` und WAL/SHM-Löschung greifen außerhalb des Persistenzordners direkt auf DB-Dateien zu. SQL-Fragmente B1 beseitigt; ORM folgt nach Mikes Ticketschnitt in T-91/T-92. |
| Fehler, Logging und Tests | ⚠️ Wächter übersieht den physischen Restore; positive Restoretests allein sichern die Schichtgrenze nicht. |
| Markdown und Inhaltsverzeichnisse | ⚠️ README-Aussage „only here“ bis B4-Korrektur nicht vollständig wahr; übrige Anleitungen konsistent. |

Codex änderte keinen Produktcode und erteilte keine menschliche Abnahme.
Die getrennte Board-Übernahme aus Paketfassung `df699dd1` bleibt offen.

## Nacharbeit Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `88d54d8` gegen `8804575` (Nacharbeit) und gegen `master`
`de620e9` (Gesamtstand). Ein Produktcommit.

- **B1 · SQL-Fragment:** `identity_where` steht jetzt in
  `app/persistence/repository.py`, seinem einzigen Aufrufer; `app/models.py`
  enthält kein SQL mehr. Der Wächter prüft zusätzlich den Text jedes
  Strings und f-Strings (Docstrings ausgenommen) auf SQL: `SELECT … FROM`,
  `INSERT INTO`, `UPDATE … SET`, `DELETE FROM`, `CREATE/ALTER/DROP TABLE`,
  `PRAGMA` und Vergleiche mit `?`-Platzhalter. Belege:
  - Alter Stand `app/models.py` (`git show 8804575:app/models.py`): drei
    Treffer in den Zeilen 361, 365, 367 — genau die drei Fragmente.
  - Neuer Stand: 56 Dateien außerhalb `app/persistence/` ohne Treffer.
  - Gegenproben im Test: Fragment `kind = ? AND isin = ?` ohne `execute`,
    f-String `SELECT {…} FROM`, Docstring mit SQL (kein Treffer); echter
    `repository.py` muss anschlagen; gewöhnliche Texte mit „auswählen“,
    „Update“, „?“ schlagen nicht an.
  - README „data access (only here)“ trifft damit zu.
- **B2 · Berichtsfelder:** Beide Listen sind weg. `stored_rejections` liest
  `SELECT *`; der Router nimmt `tuple(RejectedInstrument.model_fields)` für
  Plan und Bericht. Die Feldmenge steht damit nur im REST-Modell. Gegenprobe:
  Ein Mutant, der `currency` aus der Abfrage weglässt, macht 5 Tests in
  `tests/test_migration_endpoints.py` rot; zurückgesetzt wieder grün.
- **B3 · Vertragstypen:** `SavedQuote` und `PROTECTED_META_FIELDS` stehen in
  `app/persistence/quote_store.py`. `repository.py`, `quote_cache.py` und
  `tests/test_repository.py` importieren sie von dort; `quote_store.py`
  importiert nichts aus der Umsetzung. Außerhalb `app/persistence/`
  importiert nur noch `container.py` (`QuoteRepository` für
  `get_quote_store`) und `main.py` (Fehlerklassen und Ablehnungskennungen
  für die HTTP-Antworten) aus `repository.py`.
- **Läufe:** Backend **1271 passed, 35 skipped** (2 neue Gegenproben),
  Plugin-API **324 passed, 1 skipped**; Ruff für `app tests scripts` und
  `plugin_api`, `git diff --check` grün.
- **Sichtbar:** Alt-Datenbank neu angelegt, eigener Port.
  [Migrationsvorschau](T-90-browser-r2-migration-preview.png) unverändert
  (2 umziehend, XYZ abgelehnt); `POST /migration/confirm` und
  `GET /migration/report` liefern denselben vollständigen Eintrag wie
  Runde 1. Dashboard und Backup sind von dieser Nacharbeit nicht berührt.
- **Bezeichner-Inventar** jetzt über den ganzen Python-Diff: 78 Dateien,
  22.163 Vorkommen; einziger nicht-ASCII-Name ist der zulässige deutsche
  Testname in `tests/test_identity_intake_paths.py`. Neu in dieser Runde:
  `SavedQuote` (verschoben), `identity_where` (verschoben), `_docstrings`,
  `_string_text` und drei deutsche Testnamen.

**Doku-Abgleich:** Keine weitere Änderung nötig. `README.md` „only here“
gilt jetzt; `docker/README.md`, `unraid/README.md`,
`docs/plugin-authors.md` und `AGENTS.md` nennen die verschobenen Namen
nicht.

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-02)

**Prüfstand:** `8804575` gegen `de620e9`; nach dem Produktcommit folgten
nur Ticket-/Statuscommits. Rollen, Owner, Priorität, Ticketpfad und Branch
stimmten; der Arbeitsbaum war beim Claim sauber. Die Paket-VERSION
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`
war unverändert. **Ergebnis: `changes_requested`**. Runde 1 von höchstens 3;
keine technische oder menschliche Abnahme.

### Befunde für Runde 2

1. **B1 · SQL bleibt außerhalb der Persistenzgrenze.**
   `app/models.py:345–369` enthält `identity_where`: Die Funktion baut drei
   SQLite-`WHERE`-Fragmente mit `?`-Parametern. Ausschließlich
   `app/persistence/repository.py:314` nutzt sie. Damit liegen SQL und
   Abfrageform weiterhin im Domänenmodell, obwohl das erste
   Akzeptanzkriterium und der Scope-Vertrag genau das ausschließen.
   `tests/test_persistence_boundary.py:23–45` sucht nur SQLite-Importe und
   `execute`-Methoden. Eine unabhängige Gegenprobe mit dessen
   `database_accesses` auf dem gesamten `app/models.py` liefert `[]`,
   während `identity_where` dort vorhanden ist. Bitte die SQL-Form in den
   Persistenzordner verlagern und den Wächter mit einem negativen Fall für
   SQL-Fragmente ohne direkten `execute`-Aufruf schärfen. `README.md:527`
   verspricht bereits „data access (only here)“ und muss mit dem Endstand
   übereinstimmen.
2. **B2 · Berichtsspalten doppelt gepflegt (DRY).** Die neue
   `_REPORT_COLUMNS`-Liste in `app/persistence/db.py:239–250` und die
   bestehende `_REJECTION_FIELDS`-Liste in `app/routers/migration.py:63–74`
   enthalten dieselben neun Felder. Der Router verwendet seine Liste für
   Plan und Bericht, die Persistenzschicht ihre für die SQL-Auswahl. Ein
   neues oder umbenanntes Feld müsste synchron an beiden Stellen geändert
   werden. Bitte eine gemeinsame Vertragsquelle oder eine Abfrage ohne
   zweite Feldliste verwenden; das SQL bleibt dabei im Persistenzordner.
3. **B3 · Das Interface hängt an der konkreten Implementierung.**
   `app/persistence/quote_store.py:13` importiert `SavedQuote` aus
   `app/persistence/repository.py`, statt einen unabhängigen Domänentyp zu
   verwenden. `app/services/quote_cache.py:30,562` importiert außerdem
   `PROTECTED_META_FIELDS` direkt aus dieser konkreten Repository-Datei.
   Die zentrale Konstruktion in `app/container.py:42–46` ist richtig; die
   beiden übrigen Kanten verhindern jedoch die zugesagte Trennung der
   Dienste von der Implementierung. Bitte `SavedQuote` und die gemeinsam
   benötigte Feldregel in einen neutralen Vertrag legen und beide Seiten
   daraus versorgen, ohne die Feldliste zu duplizieren.

### Belege und Einordnung

- **#2:** `git diff -M --summary de620e9 8804575` zeigt alle fünf
  Umbenennungen nach `app/persistence/`; keine alten Weiterleitungsmodule.
- **#4:** Unabhängig **1269 passed, 35 skipped** im Backend und **324
  passed, 1 skipped** in der Plugin-API. Ruff für `app tests scripts` und
  `plugin_api` sowie `git diff --check` sind grün. Pyright meldet keinen
  `QuoteRepository`/`QuoteStore`-Zuweisungskonflikt; andere bestehende
  Typbefunde sind kein Beleg für die Schichtentrennung.
- **#5–#6:** Alle vier übergebenen Bilder angesehen: Detailbereich mit fünf
  Instrumenten, vorgemerkter Restore, Backupliste danach und Vorschau mit
  zwei umziehenden und einem abgelehnten Instrument. Die Backendtests decken
  Restore und Migrationswege mit temporären Datenbanken ab. Das Bild der
  Backupliste allein zeigt das wiederhergestellte `GOLD.SG` nicht; dessen
  tatsächliche Wiederkehr ist Claudes API-/Logbeleg, kein eigenes
  Bildorakel.
- **Bezeichner:** Ein eigenes AST-Inventar erfasste alle **78** im Gesamtstand
  geänderten Python-Dateien und 22.081 Name-/Argument-/Funktions-/
  Klassenvorkommen. Einziger nicht-ASCII-Bezeichner ist ein laut `AGENTS.md`
  zulässiger deutscher Testname. Die Übergabe nennt 31 Dateien und 822
  Namen; diese Zählung deckt den gesamten Python-Diff nicht ab. Die
  vollständige Gegenprobe ist hier nachgetragen, ohne weitere Reviewrunde.
- **Doku-Abgleich:** `README.md` beschreibt den neuen Modulort, aber „only
  here“ trifft wegen B1 noch nicht zu. `docker/README.md` und
  `unraid/README.md` nennen keine Modulpfade und machen keine gegenteilige
  Aussage; `docs/plugin-authors.md` und `AGENTS.md` benötigen für die reine
  Verschiebung keine Änderung. T-91/T-92 bleiben ausdrücklich kommende
  Schritte, und Mikes Ticketschnitt erlaubt das noch fehlende ORM in T-90.

**Gelesener Standard:**
`/Users/macminipro/.codex/skills/code-standards/SKILL.md`, Referenzen
`architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`. Das `lessons/`-Inventar für Claudes Autorenschaft wurde
nach `LESSONS-ACCESS.md` gelesen; insbesondere SI-P-02, SI-P-08, SI-P-11,
SI-P-12 und SI-P-13 sind für Vollständigkeit, Gegenprobe und Gewichtung
einschlägig.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ⚠️ B2 doppelte Berichtsfelder; B3 Interface und Dienst importieren die konkrete Umsetzung. AST-Inventar nachgetragen. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nur Import- und Ruff-Korrekturen in Skripten, keine CLI-Änderung |
| TypeScript, Vue und i18n | ➖ kein Frontend-Diff; Browserbilder ohne neuen UI-Befund |
| Python, FastAPI und Webhooks | ⚠️ B3 Schichtentrennung; FastAPI-DI und 1269 Backendtests funktionieren. |
| Datenbanken und Persistenzgrenzen | ⚠️ B1 SQL-Fragment außerhalb; fünf Modulverschiebungen und die übrigen direkten SQL-Zugriffe im richtigen Ordner. Fehlendes ORM ist durch Mikes T-90/T-91/T-92-Schnitt ausdrücklich eingeordnet. |
| Fehler, Logging und Tests | ⚠️ B1 wird vom neuen Wächter übersehen; Gegenprobe liefert falsch `[]`. Restore-/Migrationssuite grün. |
| Markdown und Inhaltsverzeichnisse | ⚠️ README-Aussage „only here“ ist bis zur B1-Korrektur nicht wahr; übrige Anleitungen passen. |

Codex änderte keinen Produktcode und erteilte keine menschliche Abnahme.
Die getrennte Board-Übernahme aus Paketfassung `df699dd1` bleibt offen.

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
