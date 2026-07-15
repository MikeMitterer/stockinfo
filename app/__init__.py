"""StockInfo — REST-Kursabfrage für Aktien und ETFs mit SQLite-Cache."""

import tomllib
from pathlib import Path

_PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _read_version() -> str:
    """Liest die App-Version aus pyproject.toml (Single Source of Truth).

    Returns:
        Versions-String aus [project].version.

    Raises:
        FileNotFoundError: Wenn pyproject.toml fehlt — Packaging-Fehler,
            bewusst fail-fast statt einer stillen Fallback-Version.
        KeyError: Wenn [project].version in der Datei fehlt.
    """
    with _PYPROJECT_PATH.open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)["project"]["version"]


__version__ = _read_version()
