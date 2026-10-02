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
  lesen und schreiben sie darüber. Verbleibendes rohes Daten-SQL steht nur
  in den Schema-, Migrations-, Backup- und Plugin-Migrationsmodulen und ist
  dort begründet. Einzige weitere Ausnahme (Nachtrag Runde 1): die
  Transaktionsanweisung `BEGIN`/`BEGIN IMMEDIATE` in `session.py`, dort
  begründet und vom Wächter auf genau diese beiden festen Anweisungen
  begrenzt. Verhalten, API und Daten bleiben unverändert.
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
| 2 | `tests/test_persistence_boundary.py` | `repository.py`, `detail_store.py`, `meta_store.py`, `tables.py` ohne rohes SQL (SQL-Text, `text()`, `exec_driver_sql`, `execute` mit String); `session.py` ebenso bis auf genau `BEGIN`/`BEGIN IMMEDIATE`; Gegenproben | ✅ |
| 3 | Rohe Stellen | Daten-SQL nur in `db.py`, `migration.py`, `backup_store.py`, `data_versions.py`, `plugin_migration.py`, je mit „Warum hier rohes SQL bleibt“; dazu die Transaktionsanweisung in `session.py`, dort begründet | ✅ |
| 4 | Backend, Plugin-API, Ruff | Backend 1308, Plugin-API 324, Ruff grün | ✅ |
| 5 | Browser mit Temp-Datenbank | Wechselkurs abrufen und aus dem Cache lesen, Einstellungen, manuelle Eingabe, Sicherung mit echtem Wiederherstellen | ✅ |
| 6 | Browser mit Alt-Datenbank | Vorschau, Bestätigung, Bericht über das Modell | ✅ |
| 7 | `STATUS.md` | T-89-Ausnahme entfernt | ✅ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Verifier-Prüfung · Runde 4 (Codex, 2026-10-02)

**Prüfstand:** `3d9286c` gegen `544e82a`; nur
`tests/test_persistence_boundary.py` geändert. Rollen, Owner, exakte
Priorität, Ticketpfad und Branch stimmten. Die Paket-VERSION blieb
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
**Ergebnis: `approved`**, Runde 4 von höchstens 5. Technische Freigabe für
den geprüften Commit; kein Push und keine menschliche Abnahme durch Codex.

**B2 behoben.** `raw_sql_violations` inventarisiert mit `rglob("*.py")`
alle Python-Module im Persistenzordner samt Unterordnern. Nur die fünf
begründeten Rohmodule sind ausgenommen; `session.py` erlaubt ausschließlich
den bereits geprüften festen `BEGIN`-Ausdruck. Die Prüfung verlangt zudem,
dass alle benannten Ausnahmedateien existieren. Im aktuellen Inventar stehen
zwölf Python-Dateien. Meine unabhängige Gegenprobe in einem temporären
Ordner meldete ein neues `new_reader.py` mit Alias-Aufruf und
`SELECT value FROM meta` sowie `deeper/writer.py` mit `executemany` und
`INSERT INTO meta`. Das zuvor übersehene Zusatzmodul wird ebenfalls von
der eingecheckten Gegenprobe erfasst. Damit ist Verify #3 ✅.

**Prüfläufe:** 13 gezielte Grenztests bestanden; Ruff für die geänderte
Testdatei und `git diff --check` grün. AST-Inventar der geänderten Datei
enthält englische Bezeichner; die deutschen `test_…`-Namen sind nach
`AGENTS.md` erlaubt. Die bekannte Grenze bei einem Alias für eine
Nicht-Daten-Anweisung wie `VACUUM` ist im Nacharbeitsbericht benannt;
im tatsächlichen Produktinventar gibt es dadurch keinen offenen Verstoß.
Backend-Gesamtlauf, Plugin-API und Browserbelege aus den vorigen Runden
bleiben gültig, da der Produktcode seitdem unverändert ist.

**DRY und Doku-Abgleich:** Im Testdiff keine zweite Fachregel oder
parallele Wissensquelle: das Verzeichnis liefert das Inventar, die fünf
begründeten Ausnahmen stehen einmal in `RAW_SQL_MODULES`. Der
README-Abgleich aus Runde 1 bleibt gültig; weder Verhalten noch
Installation änderten sich in Runde 4. `README.md` beschreibt SQLModel
im Persistenzordner; `docker/README.md` und `unraid/README.md` beschreiben
weiter zutreffend die SQLite-Datenbank. Die getrennte Übernahme der
Paketfassung `df699dd1` bleibt offen.

**Standards:** `code-standards/SKILL.md` mit `architecture.md`,
`python.md`, `persistence.md`, `quality.md`, `documentation.md`;
`task-verification-workflow` und lokale Autor-Lessons einschließlich
SI-P-14.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ Inventar statt gepflegter Sauberliste; keine doppelte Fachlogik; AST-Inventar geprüft. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ nur Testcode geändert; gezielte Tests und Ruff grün. |
| Datenbanken und Persistenzgrenzen | ✅ neue Roh-SQL-Module und Unterordner werden gefunden; fünf begründete Ausnahmen geprüft. |
| Fehler, Logging und Tests | ✅ unabhängige negative Gegenprobe mit zwei zusätzlichen Modulen meldet Verstöße. |
| Markdown und Inhaltsverzeichnisse | ✅ Ticket und drei READMEs inhaltlich abgeglichen; kein Dokumentationswechsel nötig. |

## Nacharbeit Runde 3 (Claude, 2026-10-02)

Prüfgegenstand: `3d9286c` gegen `544e82a` (Nacharbeit) und gegen `master`
`f4bc8ef` (Gesamtstand). Nur der Grenztest geändert; kein Produktdiff.

- **B2 · Inventar statt Liste** (Anwendung von SI-P-14):
  `raw_sql_violations(directory)` geht über **jede** `*.py` unter dem
  Ordner, einschließlich Unterordnern. Ein Modul aus `RAW_SQL_MODULES`
  muss „Warum hier rohes SQL bleibt“ tragen; jedes andere darf kein rohes
  SQL enthalten, `session.py` nur die feste `BEGIN`-Anweisung. Der Test
  prüft zusätzlich, dass jede genannte Ausnahme als Datei existiert. Die
  fünf parametrisierten Einzelprüfungen entfallen dafür (Backend −3).
- **Belege:**
  - Gegenprobe `test_gegenprobe_ein_neues_modul_mit_rohem_sql_faellt_auf`
    in `tmp_path`: deine Variante (`runtime_extra.py` mit
    `exec_driver_sql("SELECT * FROM meta")`), ein Modul im Unterordner
    mit `text()` in einer inneren Funktion und ein Rohmodul ohne
    Begründung werden gemeldet; ein sauberes neues Modul und das echte
    `session.py`-Muster nicht.
  - **Mutant im echten Ordner:** `app/persistence/runtime_extra.py` mit
    deiner Variante und einer Nachbarvariante über einen Aufruf-Alias
    (`run = session.execute; run("DELETE FROM fx_rates")`): Der Test wird
    rot und meldet beide (Zeile 2 über `exec_driver_sql` und SQL-Text,
    Zeile 7 über den SQL-Text). Datei entfernt, `git status` sauber.
- **Verbleibende Grenze, offen benannt:** Ein Aufruf über einen Alias mit
  einer Anweisung, die nicht wie Daten-SQL aussieht (etwa `VACUUM`),
  bliebe unerkannt — erkannt wird über Aufrufname oder SQL-Text. Jede
  Datenanweisung (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) fällt über ihren
  Text auf. Mehr wäre Datenflussanalyse (SI-P-09).
- **Läufe:** Backend **1307 passed, 36 skipped**, Ruff `tests`,
  `git diff --check` grün.

## Verifier-Prüfung · Runde 3 (Codex, 2026-10-02)

**Prüfstand:** `544e82a` gegen `7d0be5e`; Rollen, Owner, Priorität,
Ticketpfad und Branch stimmten. Paket-VERSION vor diesem Durchlauf
unverändert:
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
**Ergebnis: `changes_requested`**, Runde 3 von höchstens 5.
Kein Merge, Push oder menschliche Abnahme durch Codex.

**B1 behoben.** `_is_transaction_statement` prüft jetzt den ganzen
ersten Argumentausdruck: eine feste erlaubte Zeichenkette oder beide
festen Zweige eines bedingten Ausdrucks. Meine Gegenproben liefern
`[]` für die echte `session.py`, aber
`2: exec_driver_sql(...)` für den dynamischen Zweig aus Runde 2 und
für `"BEGIN" + suffix`. Der Scope-Vertrag nennt die nötige
Transaktionsausnahme nun ausdrücklich. Unabhängig **16 passed** im
Grenztest, Ruff für Test und Session-Modul sowie `git diff --check`
grün. Kein Verhaltensdiff am Produktcode. Verify #2 ist für die fünf
explizit genannten Module ✅.

**B2 · Die Vollständigkeitszusage für die Rohmodule ist nicht geschützt.**
Verify #3 sagt, dass rohes Daten-SQL nur in fünf begründeten Modulen
steht. Der neue Test parametrisiert jedoch ausschließlich die
handgeschriebene Liste `ORM_ONLY_MODULES` mit fünf anderen Dateien;
weitere Dateien unter `app/persistence/` werden weder entdeckt noch
gegen die Ausnahmeliste verglichen. Meine unabhängige Gegenprobe in
einem temporären Ordner fügte `runtime_extra.py` mit
`connection.exec_driver_sql("SELECT * FROM meta")` hinzu. `raw_sql`
meldete darin zwei Treffer, aber alle fünf Aufrufe des parametrisierten
Tests blieben grün: `runtime_extra.py` kam in seiner Liste nicht vor.
Im tatsächlichen Projekt habe ich alle zwölf Python-Module unter
`app/persistence/` unabhängig inventarisiert; heute enthält keines
außer den fünf begründeten Modulen Daten-SQL. Die Lücke betrifft den
zugesagten Wächter für neue Module. Bitte die Dateinamen aus dem Ordner
ermitteln, die begründeten Ausnahmen explizit vergleichen und einen
zusätzlichen Roh-SQL-Modulfall als negative Gegenprobe rot belegen.
Das ist die konkrete Anwendung der inzwischen eingetragenen
[SI-P-14](../.agents/lessons/SI-P-14-der-grenzwaechter-bestaetigt-eine-handgeschriebene-liste.md);
kein neues Analyse-Subsystem nötig. Verify #3 bleibt ⚠️.

**Unverändert:** 1293 netzunabhängige Backend-Tests und 324
Plugin-API-Tests aus Runde 1, Browserbelege, DRY-Prüfung und Doku-Abgleich
bleiben mangels Produkt-Verhaltensdiff gültig. AST-Inventar des erneut
geänderten Grenztests: 493 Bezeichnervorkommen, keine nicht-ASCII-Namen.
Verify #1–#2 und #4–#7 sind ✅. Die ungetrackte Lesson-Datei wurde
nach der Übergabe als Board-Commit `6cc18ef` eingetragen; ich habe sie
gelesen und nicht selbst geändert. Die getrennte Paket-Übernahme
`df699dd1` bleibt offen.

**Standards:** `/Users/macminipro/.codex/skills/code-standards/SKILL.md`
mit `architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`; `task-verification-workflow` und lokale
Autor-Lessons.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ ein Transaktionspfad, keine neue doppelte Logik; AST-Inventar oben. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ kein Produkt-Verhaltensdiff; gezielter Test und Ruff grün. |
| Datenbanken und Persistenzgrenzen | ⚠️ 1 Befund B2: der Wächter inventarisiert neue Persistenzmodule nicht. |
| Fehler, Logging und Tests | ⚠️ 1 Befund B2: temporäres zusätzliches Roh-SQL-Modul ergibt ein falsches Grün. |
| Markdown und Inhaltsverzeichnisse | ✅ Scope-Ausnahme und Doku-Abgleich nun stimmig. |

## Nacharbeit Runde 2 (Claude, 2026-10-02)

Prüfgegenstand: `544e82a` gegen `7d0be5e` (Nacharbeit) und gegen `master`
`f4bc8ef` (Gesamtstand). Nur der Grenztest geändert; kein Produktdiff.

- **B1 · dynamischer Zweig:** `_is_transaction_statement` prüft jetzt den
  ganzen ersten Argumentausdruck von `exec_driver_sql`: erlaubt ist eine
  feste Zeichenkette aus `{BEGIN, BEGIN IMMEDIATE}` oder ein bedingter
  Ausdruck, dessen beide Zweige es wieder sind. Name, Verkettung und
  f-String sind nicht erlaubt. Belege:
  - Deine Gegenprobe (`… if immediate else statement`) meldet jetzt
    `2: exec_driver_sql(...)`.
  - Neuer Test `test_die_transaktionsausnahme_nimmt_keinen_dynamischen_zweig`:
    Variable im Zweig, `'BEGIN' + suffix` und `f'BEGIN {suffix}'` rot, der
    feste Ausdruck daneben grün.
  - Der echte Ausdruck in `session.py` bleibt grün.
- **Scope-Vertrag:** Die Transaktionsausnahme steht jetzt auch im
  „Ergebnis“ (als Nachtrag Runde 1 markiert) und in der Standardmatrix der
  Übergabe.
- **Läufe:** Backend **1310 passed, 36 skipped** (+1), Ruff `tests`,
  `git diff --check` grün.

## Verifier-Prüfung · Runde 2 (Codex, 2026-10-02)

**Prüfstand:** `7d0be5e` gegen `833e3cf`; Rollen, Owner, Priorität,
Ticketpfad und Branch stimmten. Paket-VERSION vor diesem Durchlauf
unverändert:
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
**Ergebnis: `changes_requested`**, Runde 2 von höchstens 5.
Kein Merge, Push oder menschliche Abnahme durch Codex.

**B1 nur teilweise behoben · Die Ausnahme akzeptiert dynamisches SQL.**
Der neue Wächter meldet das tatsächliche `exec_driver_sql` in
`session.py:55` ohne Ausnahme und erlaubt die beiden festen
Transaktionsanweisungen mit Ausnahme. Er sammelt dafür jedoch alle
Stringkonstanten irgendwo in den Argumenten und prüft nur, ob diese
Teilmenge von `{BEGIN, BEGIN IMMEDIATE}` sind. Meine unabhängige
Gegenprobe:

```python
source = ('def run(connection, statement, immediate):\n'
          '    connection.exec_driver_sql("BEGIN IMMEDIATE" if immediate else statement)\n')
assert raw_sql(source, transactions_allowed=True) == []  # derzeitiger Fehler
```

Der zweite Zweig kann beliebiges SQL ausführen, obwohl die zugesagte
Ausnahme **genau** `BEGIN` und `BEGIN IMMEDIATE` umfasst. Ebenso passiert
`"BEGIN" + suffix` den Wächter. Bitte den ersten SQL-Argumentausdruck
vollständig prüfen (feste Zeichenkette oder bedingter Ausdruck mit zwei
festen erlaubten Zeichenketten); ein dynamischer Zweig muss als negative
Gegenprobe rot sein. Der vorhandene echte Session-Ausdruck muss grün
bleiben. Zusätzlich steht im Scope-Vertrag oben noch „rohes SQL nur in“
den fünf anderen Modulen; dort die begründete Transaktionsausnahme aus
Verify #2/#3 ebenfalls mitziehen. Verify #2/#3 bleiben ⚠️.

**Geprüfter Rest:** Die neue Gegenprobe erkennt feste `PRAGMA`-, `COMMIT`-
und `VACUUM`-Anweisungen; der Produktcode in `session.py` ist bis auf
Docstring und Kommentar unverändert. Unabhängig **15 passed** im
gezielten Grenztest, Ruff für `session.py` und den Grenztest sowie
`git diff --check` grün. Die **1293 netzunabhängigen Backend-Tests**,
**324 Plugin-API-Tests**, Browserbilder, übrige Verify-Zeilen,
DRY-Prüfung und Doku-Abgleich aus Runde 1 bleiben ohne betroffenen
Produktdiff gültig. Verify #1 und #4–#7 sind ✅.

**Standards:** `/Users/macminipro/.codex/skills/code-standards/SKILL.md`
mit `architecture.md`, `python.md`, `persistence.md`, `quality.md`,
`documentation.md`; `task-verification-workflow` und lokale
Autor-Lessons. Die getrennte Board-Übernahme `df699dd1` bleibt offen.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ nur ein bestehender Transaktionspfad; keine neue doppelte Logik, englische Namen im geänderten Code. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ➖ kein UI-Diff |
| Python, FastAPI und Webhooks | ✅ kein Python-Verhaltensdiff; gezielter Test und Ruff grün. |
| Datenbanken und Persistenzgrenzen | ⚠️ 1 Rest B1: dokumentierte Ausnahme wird vom Wächter zu weit gefasst. |
| Fehler, Logging und Tests | ⚠️ 1 Rest B1: dynamischer SQL-Ausdruck ist ein falsches Grün der Gegenprobe. |
| Markdown und Inhaltsverzeichnisse | ⚠️ 1 Rest B1: Scope-Vertrag nennt die Session-Ausnahme noch nicht. |

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
| Datenbanken und Persistenzgrenzen | ✅ alle Tabellen mit SQLModel-Modell; rohes Daten-SQL nur in Schema, Migration, Backup und Plugin-Migration, je begründet; in `session.py` nur `BEGIN`/`BEGIN IMMEDIATE`; Wächter für die Laufzeitmodule |
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
