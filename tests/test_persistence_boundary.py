"""Datenbankzugriffe liegen nur in `app/persistence/`.

Der Test liest jede Python-Datei unter `app/` als Syntaxbaum und sucht:

- einen Import von `sqlite3`,
- einen Aufruf, der SQL an eine Verbindung schickt (`execute`,
  `executemany`, `executescript`),
- SQL im Text eines Strings — auch ein bloßes `WHERE`-Fragment mit
  `?`-Platzhalter, das erst an anderer Stelle ausgeführt wird,
- einen Dateizugriff auf die Datenbankdatei: `os.replace`, `shutil.copy2`
  und Verwandte mit einem Argument, dessen Name `database` enthält, oder
  Pfadmethoden wie `exists`, `stat`, `unlink` auf einem solchen Pfad,
- die Journalendungen `-wal` und `-shm` als String.

Docstrings zählen nicht: Sie erklären SQL, sie setzen keines ab. Eine
Textsuche fände dagegen jede Erwähnung in einem Docstring und übersähe
`import sqlite3 as db`. Der Dateizugriff wird am Namen erkannt; die
Sicherungsdateien im Archiv heißen anders und bleiben Sache des Dienstes.

Die Gegenproben laufen dieselbe Prüfung über Quelltext mit genau diesen
Verstößen. Findet sie dort nichts, wäre ein grüner Lauf über `app/` wertlos.
"""

import ast
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PERSISTENCE_DIR = APP_DIR / "persistence"
SQL_CALLS = frozenset({"execute", "executemany", "executescript"})
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


def _names_database(node: ast.AST) -> bool:
    """Ob ein Ausdruck einen Namen mit `database` darin enthält."""
    return any(
        "database" in (part.id if isinstance(part, ast.Name) else part.attr).lower()
        for part in ast.walk(node)
        if isinstance(part, (ast.Name, ast.Attribute))
    )


def _file_access(call: ast.Call) -> str | None:
    """Beschreibt einen Dateizugriff auf die Datenbank, sonst ``None``."""
    function = call.func
    if not isinstance(function, ast.Attribute):
        return None
    module = function.value.id if isinstance(function.value, ast.Name) else None
    if (module, function.attr) in FILE_FUNCTIONS and any(
        _names_database(argument) for argument in call.args
    ):
        return f"{module}.{function.attr}(Datenbank)"
    if function.attr in PATH_METHODS and _names_database(function.value):
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
    findings: set[str] = set()
    for node in ast.walk(tree):
        text = _string_text(node)
        if isinstance(node, ast.Import):
            findings.update(
                f"{node.lineno}: import {alias.name}"
                for alias in node.names
                if alias.name.split(".")[0] == "sqlite3"
            )
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "sqlite3":
                findings.add(f"{node.lineno}: from {node.module} import")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in SQL_CALLS:
                findings.add(f"{node.lineno}: .{node.func.attr}(...)")
            elif access := _file_access(node):
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
    """Gegenprobe am echten Code: Im Persistenzordner muss die Prüfung anschlagen."""
    repository = (PERSISTENCE_DIR / "repository.py").read_text(encoding="utf-8")

    found = database_accesses(repository)

    assert any("SQL im String" in finding for finding in found)
    assert any(".execute(...)" in finding for finding in found)


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
