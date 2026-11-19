"""Router übersetzen nur HTTP — sie greifen nicht auf die Persistenz zu (T-142).

Der Test liest jede Python-Datei unter `app/routers/` als Syntaxbaum und sucht:

- einen Import aus `app.persistence` — absolut, als `from app import
  persistence` oder relativ (`from ..persistence import`),
- einen privaten Namen (`_name`), den ein Router aus einem anderen Router
  importiert. Was zwei Router teilen, gehört in ein eigenes Modul mit
  öffentlichen Namen (`routers/source_errors.py`, `routers/validation.py`).

Vorbild ist `test_persistence_boundary.py`: Inventar aus dem Ordner, nicht aus
einer Liste, und Gegenproben über Quelltext mit genau diesen Verstößen.
"""

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
ROUTERS_DIR = APP_DIR / "routers"
ROUTERS_PACKAGE = "app.routers"
PERSISTENCE_PACKAGE = "app.persistence"


def _absolute(module: str | None, level: int, package: str) -> str:
    """Löst einen relativen Import gegen das Paket der Datei auf."""
    if level == 0:
        return module or ""
    base = package.split(".")[: len(package.split(".")) - level + 1]
    return ".".join([*base, module] if module else base)


def _inside(module: str, package: str) -> bool:
    return module == package or module.startswith(f"{package}.")


def boundary_violations(source: str, package: str = ROUTERS_PACKAGE) -> list[str]:
    """Nennt Persistenz-Importe und private Router-Importe im Quelltext."""
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            findings.extend(
                f"{node.lineno}: import {alias.name}"
                for alias in node.names
                if _inside(alias.name, PERSISTENCE_PACKAGE)
            )
        elif isinstance(node, ast.ImportFrom):
            module = _absolute(node.module, node.level, package)
            names = [alias.name for alias in node.names]
            if _inside(module, PERSISTENCE_PACKAGE) or any(
                _inside(f"{module}.{name}", PERSISTENCE_PACKAGE) for name in names
            ):
                findings.append(f"{node.lineno}: from {module} import")
            if _inside(module, ROUTERS_PACKAGE):
                findings.extend(
                    f"{node.lineno}: privat {name} aus {module}"
                    for name in names
                    if name.startswith("_")
                )
    return sorted(findings, key=lambda finding: (int(finding.split(":")[0]), finding))


def test_kein_router_greift_auf_die_persistenz_zu() -> None:
    checked = sorted(ROUTERS_DIR.rglob("*.py"))
    violations = {
        str(path.relative_to(APP_DIR.parent)): found
        for path in checked
        if (found := boundary_violations(path.read_text(encoding="utf-8")))
    }

    assert len(checked) > 5, "Inventar zu klein — falscher Pfad?"
    assert violations == {}


def test_gegenprobe_jede_importform_wird_gefunden() -> None:
    source = (
        "import app.persistence.db\n"
        "from app.persistence.quote_store import QuoteStore\n"
        "from app import persistence\n"
        "from ..persistence import db\n"
        "from . import _hidden\n"
        "from app.routers.instruments import REASON, _currency_mismatch\n"
        '"""Erwähnt app.persistence nur im Text."""\n'
        "from app.services.migration import preview\n"
        "from app.routers.validation import IsinPath\n"
    )

    assert boundary_violations(source) == [
        "1: import app.persistence.db",
        "2: from app.persistence.quote_store import",
        "3: from app import",
        "4: from app.persistence import",
        "5: privat _hidden aus app.routers",
        "6: privat _currency_mismatch aus app.routers.instruments",
    ]


def test_gegenprobe_am_echten_dienst() -> None:
    """Der Migrationsdienst spricht mit der Persistenz — dort muss die Prüfung anschlagen."""
    service = (APP_DIR / "services" / "migration.py").read_text(encoding="utf-8")

    assert any("app.persistence" in finding for finding in boundary_violations(service))
