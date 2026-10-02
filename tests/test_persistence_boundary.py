"""Datenbankzugriffe liegen nur in `app/persistence/`.

Der Test liest jede Python-Datei unter `app/` als Syntaxbaum und sucht zwei
Dinge: einen Import von `sqlite3` und einen Aufruf, der SQL an eine Verbindung
schickt (`execute`, `executemany`, `executescript`). Eine Textsuche fände
Docstrings, die `sqlite3` nur erwähnen, und übersähe `import sqlite3 as db`.

Die Gegenprobe läuft dieselbe Prüfung über eine Datei mit beiden Verstößen.
Findet sie dort nichts, wäre ein grüner Lauf über `app/` wertlos.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PERSISTENCE_DIR = APP_DIR / "persistence"
SQL_CALLS = frozenset({"execute", "executemany", "executescript"})


def database_accesses(source: str) -> list[str]:
    """Nennt jede Stelle im Quelltext, die direkt mit SQLite spricht."""
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            findings += [
                f"{node.lineno}: import {alias.name}"
                for alias in node.names
                if alias.name.split(".")[0] == "sqlite3"
            ]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "sqlite3":
                findings.append(f"{node.lineno}: from {node.module} import")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in SQL_CALLS
        ):
            findings.append(f"{node.lineno}: .{node.func.attr}(...)")
    return findings


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


def test_gegenprobe_die_pruefung_findet_beide_verstoesse() -> None:
    source = (
        "import sqlite3 as db\n"
        "from sqlite3 import Row\n"
        '"""Erwähnt sqlite3 nur im Text."""\n'
        "def read(connection):\n"
        "    return connection.execute('SELECT 1')\n"
    )

    assert database_accesses(source) == [
        "1: import sqlite3",
        "2: from sqlite3 import",
        "5: .execute(...)",
    ]
