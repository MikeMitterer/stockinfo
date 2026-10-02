"""Datenbankzugriffe liegen nur in `app/persistence/`.

Der Test liest jede Python-Datei unter `app/` als Syntaxbaum und sucht drei
Dinge: einen Import von `sqlite3`, einen Aufruf, der SQL an eine Verbindung
schickt (`execute`, `executemany`, `executescript`), und SQL im Text eines
Strings — auch ein bloßes `WHERE`-Fragment mit `?`-Platzhalter, das erst an
anderer Stelle ausgeführt wird. Docstrings zählen nicht: Sie erklären SQL,
sie setzen keines ab. Eine Textsuche fände dagegen jede Erwähnung in einem
Docstring und übersähe `import sqlite3 as db`.

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
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in SQL_CALLS
        ):
            findings.add(f"{node.lineno}: .{node.func.attr}(...)")
        elif text is not None and id(node) not in docstrings and SQL_TEXT.search(text):
            findings.add(f"{node.lineno}: SQL im String")
    return sorted(findings, key=lambda finding: int(finding.split(":")[0]))


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


def test_gegenprobe_gewoehnlicher_text_ist_kein_sql() -> None:
    source = (
        "MESSAGE = 'Bitte eine Börse auswählen, bevor du speicherst.'\n"
        "LABEL = 'Update der Kurse läuft'\n"
        "QUESTION = 'Ist das richtig?'\n"
    )

    assert database_accesses(source) == []
