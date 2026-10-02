"""Datenbankzugriffe liegen nur in `app/persistence/`.

Der Test liest jede Python-Datei unter `app/` als Syntaxbaum und sucht:

- einen Import von `sqlite3`, `sqlalchemy` oder `sqlmodel` — oder der
  Modelle und Sessions aus `app/persistence/` (`tables`, `session`),
- einen Aufruf, der SQL an eine Verbindung schickt (`execute`,
  `executemany`, `executescript`),
- SQL im Text eines Strings — auch ein bloßes `WHERE`-Fragment mit
  `?`-Platzhalter, das erst an anderer Stelle ausgeführt wird,
- einen Dateizugriff auf die Datenbankdatei: `os.replace`, `shutil.copy2`
  und Verwandte mit einem Datenbankpfad als Argument, oder Pfadmethoden wie
  `exists`, `stat`, `unlink` auf einem solchen Pfad,
- die Journalendungen `-wal` und `-shm` als String.

Ein Datenbankpfad ist ein Ausdruck mit einem Namen, der `database` enthält,
oder ein Alias davon: `path = Path(database_path)` macht `path` innerhalb
dieser Funktion zum Datenbankpfad, auch über weitere Zuweisungen. `.parent`
beendet die Spur — das Verzeichnis ist nicht die Datei. Sicherungsdateien
im Archiv entstehen über das Verzeichnis und bleiben Sache des Dienstes.

Docstrings zählen nicht: Sie erklären SQL, sie setzen keines ab. Eine
Textsuche fände dagegen jede Erwähnung in einem Docstring und übersähe
`import sqlite3 as db`.

Die Gegenproben laufen dieselbe Prüfung über Quelltext mit genau diesen
Verstößen. Findet sie dort nichts, wäre ein grüner Lauf über `app/` wertlos.
"""

import ast
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PERSISTENCE_DIR = APP_DIR / "persistence"
SQL_CALLS = frozenset({"execute", "executemany", "executescript"})
# Treiber und ORM: Außerhalb des Persistenzordners gibt es weder Verbindungen
# noch Modellobjekte (T-91).
DATABASE_MODULES = frozenset({"sqlite3", "sqlalchemy", "sqlmodel"})
# Die Modelle und Sessions selbst: Wer sie importiert, hält ORM-Typen in der Hand.
ORM_MODULES = frozenset({"app.persistence.tables", "app.persistence.session"})
SQL_TEXT = re.compile(
    r"\bSELECT\b.+\bFROM\b"
    r"|\bINSERT\s+INTO\b|\bUPDATE\s+\w+\s+SET\b|\bDELETE\s+FROM\b"
    r"|\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|UNIQUE\s+INDEX)\b|\bPRAGMA\s+\w+"
    r"|\b\w+\s*=\s*\?",
    re.IGNORECASE | re.DOTALL,
)
FILE_FUNCTIONS = frozenset(
    {
        ("os", "replace"), ("os", "rename"), ("os", "remove"), ("os", "unlink"),
        ("shutil", "copy"), ("shutil", "copy2"), ("shutil", "copyfile"),
        ("shutil", "move"),
    }
)
PATH_METHODS = frozenset(
    {
        "exists", "is_file", "stat", "unlink", "rename", "replace", "open",
        "read_bytes", "write_bytes", "touch",
    }
)
JOURNAL_SUFFIXES = frozenset({"-wal", "-shm"})


def _names_database(node: ast.AST, aliases: frozenset[str]) -> bool:
    """Ob ein Ausdruck auf die Datenbankdatei zeigt.

    Das tut er, wenn ein Name darin `database` enthält oder ein Alias ist, der
    aus einem solchen Ausdruck stammt (`path = Path(database_path)`).
    `.parent` beendet die Spur: Das Verzeichnis ist nicht die Datei.
    """
    if isinstance(node, ast.Attribute):
        if node.attr == "parent":
            return False
        if "database" in node.attr.lower() or node.attr in aliases:
            return True
        return _names_database(node.value, aliases)
    if isinstance(node, ast.Name):
        return "database" in node.id.lower() or node.id in aliases
    return any(_names_database(child, aliases) for child in ast.iter_child_nodes(node))


def _database_aliases(scope: ast.AST, known: frozenset[str] = frozenset()) -> frozenset[str]:
    """Alle Namen in `scope`, denen ein Datenbankpfad zugewiesen wird — auch über Ketten.

    Args:
        scope: Eine Funktion oder die ganze Datei.
        known: Bereits bekannte Aliase, etwa Attribute aus der ganzen Datei.
    """
    aliases: set[str] = set(known)
    while True:
        found = set(aliases)
        for node in ast.walk(scope):
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value:
                targets, value = [node.target], node.value
            else:
                continue
            if not _names_database(value, frozenset(found)):
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    found.add(target.id)
                elif isinstance(target, ast.Attribute):
                    found.add(target.attr)
        if found == aliases:
            return frozenset(aliases)
        aliases = found


def _scoped_aliases(tree: ast.Module) -> dict[int, frozenset[str]]:
    """Die Aliase, die für jeden Knoten gelten — je innerster Funktion.

    Ein lokaler Name wie `path` gilt nur in der Funktion, in der er einen
    Datenbankpfad bekommt. Attribute (`self._file = Path(database_path)`)
    gelten in der ganzen Datei, weil sie über Methoden hinweg leben.
    """
    attributes = frozenset(
        target.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute)
        and target.attr in _database_aliases(tree)
    )
    module_level = _database_aliases(
        ast.Module(
            body=[
                statement
                for statement in tree.body
                if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ],
            type_ignores=[],
        ),
        attributes,
    )
    owners = {id(node): module_level for node in ast.walk(tree)}
    for function in ast.walk(tree):
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local = _database_aliases(function, attributes)
            for node in ast.walk(function):
                owners[id(node)] = local
    return owners


def _file_access(call: ast.Call, aliases: frozenset[str]) -> str | None:
    """Beschreibt einen Dateizugriff auf die Datenbank, sonst ``None``."""
    function = call.func
    if not isinstance(function, ast.Attribute):
        return None
    module = function.value.id if isinstance(function.value, ast.Name) else None
    if (module, function.attr) in FILE_FUNCTIONS and any(
        _names_database(argument, aliases) for argument in call.args
    ):
        return f"{module}.{function.attr}(Datenbank)"
    if function.attr in PATH_METHODS and _names_database(function.value, aliases):
        return f"Datenbankpfad.{function.attr}()"
    return None


def _docstrings(tree: ast.AST) -> set[int]:
    """Die Knoten-IDs aller Strings, die allein als Anweisung stehen."""
    return {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }


def _string_text(node: ast.AST) -> str | None:
    """Der Text eines String-Literals; bei f-Strings mit `{}` für jeden Ausdruck."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) else "{}"
            for part in node.values
        )
    return None


def database_accesses(source: str) -> list[str]:
    """Nennt jede Stelle im Quelltext, die direkt mit SQLite spricht."""
    tree = ast.parse(source)
    docstrings = _docstrings(tree)
    aliases = _scoped_aliases(tree)
    findings: set[str] = set()
    for node in ast.walk(tree):
        text = _string_text(node)
        if isinstance(node, ast.Import):
            findings.update(
                f"{node.lineno}: import {alias.name}"
                for alias in node.names
                if alias.name.split(".")[0] in DATABASE_MODULES or alias.name in ORM_MODULES
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in DATABASE_MODULES or module in ORM_MODULES:
                findings.add(f"{node.lineno}: from {node.module} import")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in SQL_CALLS:
                findings.add(f"{node.lineno}: .{node.func.attr}(...)")
            elif access := _file_access(node, aliases[id(node)]):
                findings.add(f"{node.lineno}: {access}")
        elif text is not None and id(node) not in docstrings:
            if SQL_TEXT.search(text):
                findings.add(f"{node.lineno}: SQL im String")
            elif text in JOURNAL_SUFFIXES:
                findings.add(f"{node.lineno}: Journaldatei {text}")
    return sorted(findings, key=lambda finding: (int(finding.split(":")[0]), finding))


def test_nur_die_persistenzschicht_spricht_mit_der_datenbank() -> None:
    checked = [
        path
        for path in sorted(APP_DIR.rglob("*.py"))
        if PERSISTENCE_DIR not in path.parents
    ]
    violations = {
        str(path.relative_to(APP_DIR.parent)): found
        for path in checked
        if (found := database_accesses(path.read_text(encoding="utf-8")))
    }

    assert len(checked) > 20, "Inventar zu klein — falscher Pfad?"
    assert violations == {}


def test_die_persistenzschicht_selbst_wird_gefunden() -> None:
    """Gegenprobe am echten Code: Im Schema- und Migrationsmodul muss die Prüfung anschlagen."""
    schema = (PERSISTENCE_DIR / "db.py").read_text(encoding="utf-8")

    found = database_accesses(schema)

    assert any("SQL im String" in finding for finding in found)
    assert any(".execute(...)" in finding for finding in found)


# Die Laufzeitwege laufen vollständig über die SQLModel-Modelle (T-92). Rohes
# SQL bleibt nur in Schema, Migration, Backup und Plugin-Migration — und ist
# dort begründet.
ORM_ONLY_MODULES = ["repository.py", "detail_store.py", "meta_store.py", "session.py", "tables.py"]

# Die eine zugelassene Ausnahme: `session.py` setzt die Transaktion selbst
# (SQLAlchemy-Rezept für pysqlite) — genau diese beiden Anweisungen, sonst nichts.
TRANSACTION_STATEMENTS = frozenset({"BEGIN", "BEGIN IMMEDIATE"})


def _is_transaction_statement(node: ast.expr) -> bool:
    """Ob der Ausdruck **nur** eine erlaubte Transaktionsanweisung ergeben kann.

    Erlaubt sind eine feste Zeichenkette aus `TRANSACTION_STATEMENTS` oder ein
    bedingter Ausdruck, dessen beide Zweige es wieder sind. Ein Name, eine
    Verkettung oder ein f-String könnte beliebiges SQL tragen.
    """
    if isinstance(node, ast.Constant):
        return node.value in TRANSACTION_STATEMENTS
    if isinstance(node, ast.IfExp):
        return _is_transaction_statement(node.body) and _is_transaction_statement(node.orelse)
    return False


def raw_sql(source: str, *, transactions_allowed: bool = False) -> list[str]:
    """Nennt rohes SQL — das, was ein ORM-Modul nicht hat.

    Gezählt werden SQL-Text in Strings, `text(...)`, jeder Aufruf von
    `exec_driver_sql(...)` und ein `execute(...)`, dessen erstes Argument
    selbst ein String ist — nicht Spaltennamen in einem SQLAlchemy-Ausdruck.
    Mit `transactions_allowed` bleibt ein `exec_driver_sql` erlaubt, dessen
    erstes Argument nur eine Anweisung aus `TRANSACTION_STATEMENTS` ergeben
    kann (`_is_transaction_statement`).
    """
    found = [finding for finding in database_accesses(source) if "SQL im String" in finding]
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else None
        )
        if name == "text":
            found.append(f"{node.lineno}: text(...)")
        elif name == "exec_driver_sql":
            allowed = transactions_allowed and node.args and _is_transaction_statement(node.args[0])
            if not allowed:
                found.append(f"{node.lineno}: exec_driver_sql(...)")
        elif name == "execute" and node.args and _string_text(node.args[0]) is not None:
            found.append(f"{node.lineno}: execute('...')")
    return sorted(found)


# Die Module, in denen rohes Daten-SQL begründet bleibt. Jedes trägt den
# Abschnitt „Warum hier rohes SQL bleibt“; jedes andere Modul unter
# `app/persistence/` ist frei davon — auch eines, das erst später dazukommt.
RAW_SQL_MODULES = frozenset(
    {"db.py", "migration.py", "backup_store.py", "data_versions.py", "plugin_migration.py"}
)
RAW_SQL_REASON = "Warum hier rohes SQL bleibt"
TRANSACTION_MODULE = "session.py"


def raw_sql_violations(directory: Path) -> dict[str, list[str]]:
    """Prüft **jede** Python-Datei unter `directory` gegen die Ausnahmeliste.

    Das Inventar kommt aus dem Ordner, nicht aus einer Liste: Eine neue Datei
    ist automatisch dabei. Ein Rohmodul muss seine Begründung tragen; jedes
    andere darf kein rohes SQL enthalten, `session.py` nur `BEGIN`.
    """
    violations: dict[str, list[str]] = {}
    for path in sorted(directory.rglob("*.py")):
        name = str(path.relative_to(directory))
        source = path.read_text(encoding="utf-8")
        if name in RAW_SQL_MODULES:
            if RAW_SQL_REASON not in source:
                violations[name] = [f"Begründung „{RAW_SQL_REASON}“ fehlt"]
            continue
        found = raw_sql(source, transactions_allowed=name == TRANSACTION_MODULE)
        if found:
            violations[name] = found
    return violations


def test_rohes_sql_steht_nur_in_den_begruendeten_modulen() -> None:
    inventory = {str(path.relative_to(PERSISTENCE_DIR)) for path in PERSISTENCE_DIR.rglob("*.py")}

    assert RAW_SQL_MODULES <= inventory, "eine Ausnahme nennt eine Datei, die es nicht gibt"
    assert {TRANSACTION_MODULE, *ORM_ONLY_MODULES} <= inventory
    assert raw_sql_violations(PERSISTENCE_DIR) == {}


def test_gegenprobe_ein_neues_modul_mit_rohem_sql_faellt_auf(tmp_path: Path) -> None:
    """Gegenprobe aus dem Review und Nachbarvarianten (SI-P-14).

    Ein zusätzliches Modul, eines in einem Unterordner, eines mit verstecktem
    `text()` und ein Rohmodul ohne Begründung werden gefunden; ein sauberes
    neues Modul und das echte `session.py`-Muster nicht.
    """
    (tmp_path / "runtime_extra.py").write_text(
        "def read(connection):\n"
        "    return connection.exec_driver_sql('SELECT * FROM meta')\n"
    )
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.py").write_text(
        "from sqlalchemy import text\n"
        "def wipe(session):\n"
        "    def inner():\n"
        "        session.execute(text('DELETE FROM fx_rates'))\n"
        "    inner()\n"
    )
    (tmp_path / "migration.py").write_text("def plan(connection):\n    connection.execute('SELECT 1')\n")
    (tmp_path / "clean.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "session.py").write_text(
        "def begin(connection, immediate):\n"
        "    connection.exec_driver_sql('BEGIN IMMEDIATE' if immediate else 'BEGIN')\n"
    )

    assert raw_sql_violations(tmp_path) == {
        "migration.py": [f"Begründung „{RAW_SQL_REASON}“ fehlt"],
        "runtime_extra.py": ["2: SQL im String", "2: exec_driver_sql(...)"],
        "sub/nested.py": ["4: SQL im String", "4: text(...)"],
    }


def test_die_transaktionsausnahme_nimmt_keinen_dynamischen_zweig() -> None:
    """Gegenprobe aus dem Review: Ein Zweig mit Variable oder Verkettung ist kein `BEGIN`."""
    source = (
        "def run(connection, statement, suffix, immediate):\n"
        "    connection.exec_driver_sql('BEGIN IMMEDIATE' if immediate else statement)\n"
        "    connection.exec_driver_sql('BEGIN' + suffix)\n"
        "    connection.exec_driver_sql(f'BEGIN {suffix}')\n"
        "    connection.exec_driver_sql('BEGIN IMMEDIATE' if immediate else 'BEGIN')\n"
    )

    assert raw_sql(source, transactions_allowed=True) == [
        "2: exec_driver_sql(...)",
        "3: exec_driver_sql(...)",
        "4: exec_driver_sql(...)",
    ]


def test_die_transaktionsausnahme_gilt_nur_fuer_begin() -> None:
    """Gegenprobe zur Ausnahme: Anderes rohes SQL im Session-Modul fällt auf."""
    source = (
        "def _on_begin(connection, immediate):\n"
        "    connection.exec_driver_sql('BEGIN IMMEDIATE' if immediate else 'BEGIN')\n"
        "def _on_connect(connection):\n"
        "    connection.exec_driver_sql('PRAGMA foreign_keys = OFF')\n"
        "    connection.exec_driver_sql('COMMIT')\n"
        "    connection.execute('VACUUM')\n"
    )

    assert raw_sql(source, transactions_allowed=True) == [
        "4: SQL im String",
        "4: exec_driver_sql(...)",
        "5: exec_driver_sql(...)",
        "6: execute('...')",
    ]
    assert raw_sql(source) == [
        "2: exec_driver_sql(...)",
        "4: SQL im String",
        "4: exec_driver_sql(...)",
        "5: exec_driver_sql(...)",
        "6: execute('...')",
    ]


def test_gegenprobe_rohes_sql_im_ormmodul_wird_gefunden() -> None:
    source = (
        "from sqlalchemy import text\n"
        "def read(session):\n"
        "    return session.execute(text('SELECT value FROM meta WHERE key = :key'))\n"
        "def write(session):\n"
        "    session.execute(text('DELETE FROM instrument_overrides'))\n"
    )

    assert raw_sql(source) == [
        "3: SQL im String",
        "3: text(...)",
        "5: SQL im String",
        "5: text(...)",
    ]


def test_gegenprobe_die_pruefung_findet_jeden_verstoss() -> None:
    source = (
        "import sqlite3 as db\n"
        "from sqlite3 import Row\n"
        '"""Erwähnt sqlite3 und SELECT name FROM instruments nur im Text."""\n'
        "def read(connection):\n"
        "    return connection.execute('SELECT 1')\n"
        "def where(identity):\n"
        "    return ('kind = ? AND isin = ?', (identity.kind, identity.isin))\n"
        "QUERY = f'SELECT {1} FROM quotes'\n"
    )

    assert database_accesses(source) == [
        "1: import sqlite3",
        "2: from sqlite3 import",
        "5: .execute(...)",
        "7: SQL im String",
        "8: SQL im String",
    ]


def test_gegenprobe_orm_importe_werden_gefunden() -> None:
    source = (
        "from sqlmodel import Session\n"
        "import sqlalchemy.exc\n"
        "from app.persistence.tables import InstrumentRecord\n"
    )

    assert database_accesses(source) == [
        "1: from sqlmodel import",
        "2: import sqlalchemy.exc",
        "3: from app.persistence.tables import",
    ]


def test_gegenprobe_dateizugriffe_auf_die_datenbank_werden_gefunden() -> None:
    source = (
        "import os, shutil\n"
        "def swap(database, source, temporary):\n"
        "    shutil.copy2(source, temporary)\n"
        "    os.replace(temporary, database)\n"
        "    database.with_name(database.name + '-wal').unlink(missing_ok=True)\n"
        "def fresh(database_path):\n"
        "    return not database_path.exists()\n"
        "def rotate(stale, pending):\n"
        "    stale.unlink(missing_ok=True)\n"
        "    os.replace(pending, stale)\n"
    )

    assert database_accesses(source) == [
        "4: os.replace(Datenbank)",
        "5: Datenbankpfad.unlink()",
        "5: Journaldatei -wal",
        "7: Datenbankpfad.exists()",
    ]


def test_gegenprobe_ein_alias_des_datenbankpfads_wird_verfolgt() -> None:
    source = (
        "import os\n"
        "from pathlib import Path\n"
        "def swap(database_path, incoming):\n"
        "    path = Path(database_path)\n"
        "    os.replace(incoming, path)\n"
        "def chain(settings):\n"
        "    target = Path(settings.database_path)\n"
        "    file = target\n"
        "    return file.stat().st_size\n"
        "def directory(database_path):\n"
        "    folder = Path(database_path).parent\n"
        "    return folder.exists()\n"
    )

    assert database_accesses(source) == [
        "5: os.replace(Datenbank)",
        "9: Datenbankpfad.stat()",
    ]


def test_der_austausch_der_datenbankdatei_wird_gefunden() -> None:
    """Gegenprobe am echten Code: Der Restore-Tausch muss anschlagen."""
    backup_store = (PERSISTENCE_DIR / "backup_store.py").read_text(encoding="utf-8")

    found = database_accesses(backup_store)

    assert any("os.replace(Datenbank)" in finding for finding in found)
    assert any("Datenbankpfad.is_file()" in finding for finding in found)


def test_gegenprobe_gewoehnlicher_text_ist_kein_sql() -> None:
    source = (
        "MESSAGE = 'Bitte eine Börse auswählen, bevor du speicherst.'\n"
        "LABEL = 'Update der Kurse läuft'\n"
        "QUESTION = 'Ist das richtig?'\n"
    )

    assert database_accesses(source) == []
