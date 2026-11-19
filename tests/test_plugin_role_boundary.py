"""Rollenklassen des Plugin-Vertrags kennt nur die Plugin-Schicht des Core (T-142).

Der Core nutzt die **Werttypen**, Fehlfälle und Invarianten aus
`stockinfo_plugin` als eigene (`Identity`, `Quote`, `NotFound`, `convert` …).
Die **Rollen** — die Protokolle, die ein Plugin erfüllt (`QuoteSource`,
`Resolver` …), samt `Source` und der Zuordnung Rolle → Kette — kennen nur:

- `app/plugin_loader.py` lädt Plugins und ordnet sie Rollen zu,
- `app/plugin_adapters.py` ruft sie über ihre Rolle auf,
- `app/sources_config.py` leitet die Kettennamen aus `ROLE_FOR_PROTOCOL` ab,
- `app/plugins/` — die eingebauten Plugins erfüllen die Rollen selbst.

Die Rollennamen stammen aus dem Vertrag (`ROLE_FOR_PROTOCOL`), nicht aus einer
Liste hier: Eine neue Rolle ist ohne Nachtrag dabei.
"""

import ast
from pathlib import Path

from stockinfo_plugin.sources import ROLE_FOR_PROTOCOL

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PLUGINS_DIR = APP_DIR / "plugins"
ROLE_MODULES = frozenset({"plugin_loader.py", "plugin_adapters.py", "sources_config.py"})
ROLE_NAMES = frozenset(
    {protocol.__name__ for protocol, _ in ROLE_FOR_PROTOCOL} | {"Source", "ROLE_FOR_PROTOCOL", "roles_of"}
)
CONTRACT_PACKAGE = "stockinfo_plugin"


def _from_contract(module: str) -> bool:
    return module == CONTRACT_PACKAGE or module.startswith(f"{CONTRACT_PACKAGE}.")


def role_uses(source: str) -> list[str]:
    """Nennt Rollennamen, die der Quelltext aus dem Vertrag holt.

    Erfasst `from stockinfo_plugin… import QuoteSource` und den Zugriff über
    ein importiertes Vertragsmodul (`stockinfo_plugin.sources.QuoteSource`).
    """
    tree = ast.parse(source)
    modules = {
        alias.asname or alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if _from_contract(alias.name)
    } | {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and _from_contract(node.module or "")
        for alias in node.names
        if alias.name not in ROLE_NAMES
    }
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and _from_contract(node.module or ""):
            findings.update(
                f"{node.lineno}: {alias.name}" for alias in node.names if alias.name in ROLE_NAMES
            )
        elif isinstance(node, ast.Attribute) and node.attr in ROLE_NAMES:
            root = node.value
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id in modules:
                findings.add(f"{node.lineno}: {node.attr}")
    return sorted(findings, key=lambda finding: (int(finding.split(":")[0]), finding))


def test_rollenklassen_stehen_nur_in_der_plugin_schicht() -> None:
    checked = [
        path
        for path in sorted(APP_DIR.rglob("*.py"))
        if PLUGINS_DIR not in path.parents and str(path.relative_to(APP_DIR)) not in ROLE_MODULES
    ]
    violations = {
        str(path.relative_to(APP_DIR.parent)): found
        for path in checked
        if (found := role_uses(path.read_text(encoding="utf-8")))
    }

    assert len(checked) > 20, "Inventar zu klein — falscher Pfad?"
    assert violations == {}


def test_die_ausnahmen_gibt_es_und_sie_nutzen_rollen() -> None:
    """Eine Ausnahme, die keine Rolle mehr nutzt, gehört gestrichen."""
    for name in sorted(ROLE_MODULES):
        assert role_uses((APP_DIR / name).read_text(encoding="utf-8")), name


def test_gegenprobe_jede_zugriffsform_wird_gefunden() -> None:
    source = (
        "import stockinfo_plugin\n"
        "import stockinfo_plugin.sources as contract\n"
        "from stockinfo_plugin import QuoteSource, Identity\n"
        "from stockinfo_plugin.sources import ROLE_FOR_PROTOCOL, roles_of\n"
        "from stockinfo_plugin import sources\n"
        "def check(source):\n"
        "    return isinstance(source, stockinfo_plugin.Resolver)\n"
        "def daily(source):\n"
        "    return isinstance(source, contract.DailyCloseSource)\n"
        "def fx(source):\n"
        "    return isinstance(source, sources.FxSource)\n"
        '"""Erwähnt QuoteSource nur im Text."""\n'
        "def unrelated(item):\n"
        "    return item.Resolver\n"
    )

    assert role_uses(source) == [
        "3: QuoteSource",
        "4: ROLE_FOR_PROTOCOL",
        "4: roles_of",
        "7: Resolver",
        "9: DailyCloseSource",
        "11: FxSource",
    ]
