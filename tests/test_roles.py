"""Die Rollen der Quellenkette stehen einmal; wer sie wiederholen muss, bleibt gleich.

`sources_config.ROLES` leitet sich aus dem Plugin-Vertrag ab
(`stockinfo_plugin.sources.ROLE_FOR_PROTOCOL`). Drei Stellen können das nicht:
das Bash-Skript `scripts/sources-profile.sh`, die Adapter-Tabelle der Registry
(je Rolle eine Klasse) und die Analyse (je Rolle eine Methode und eine
Störungsform). Dieser Test hält sie zusammen; T-140.
"""

import re
from pathlib import Path

from app.services import analyzer
from app.sources_config import ROLES
from app.sources_registry import ROLE_ADAPTERS

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sources-profile.sh"


def _script_roles(text: str) -> tuple[str, ...]:
    """Die Rollen aus `readonly ROLES="…"` eines Bash-Skripts, in ihrer Reihenfolge."""
    match = re.search(r'^readonly ROLES="([^"]*)"', text, re.MULTILINE)
    return tuple(match.group(1).split()) if match else ()


def test_das_profilskript_kennt_dieselben_rollen_in_derselben_reihenfolge() -> None:
    assert _script_roles(SCRIPT.read_text(encoding="utf-8")) == ROLES


def test_die_skriptpruefung_bemerkt_eine_abweichende_liste() -> None:
    """Gegenprobe: Fände der Parser nichts, wäre der Vergleich oben wertlos."""
    assert _script_roles('readonly ROLES="quotes resolvers"\n') == ("quotes", "resolvers")
    assert _script_roles('readonly ROLES="quotes resolvers"\n') != ROLES


def test_jede_rolle_hat_genau_einen_adapter() -> None:
    assert set(ROLE_ADAPTERS) == set(ROLES)


def test_die_analyse_beschreibt_genau_ihre_rollen() -> None:
    """Messung und Störungsform je Rolle der Analyse, nicht mehr und nicht weniger."""
    assert set(analyzer.INSTRUMENT_ROLES) <= set(ROLES)
    assert set(analyzer._MEASURED) == set(analyzer.INSTRUMENT_ROLES)
    assert set(analyzer._BROKEN) == set(analyzer.INSTRUMENT_ROLES)
