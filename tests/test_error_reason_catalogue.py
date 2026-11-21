"""Jede Fehlerkennung des Backends hat im Dashboard einen Satz — T-139.

Die API antwortet mit `{code, params}`; den Satz bildet die Oberfläche aus
`errors.reason` oder `migration.reason` (`dashboard/src/api/reason.ts`). Fehlt
dort eine Kennung, sieht der Benutzer nur „Die Quelle meldet einen Fehler, den
diese Oberfläche nicht kennt".

**Der Bestand ist ein Inventar, keine Liste von Hand.** Jede Kennung steht als
Konstante `REASON_*` im Modul, das sie wirft; die Ablehnungen des
Sicherungswegs stehen als Klassenattribute von `BackupError`. Der Test liest
alle Python-Dateien unter `app/` per `ast` und sammelt diese Konstanten. Damit
keine Kennung an dieser Sammlung vorbeiläuft, prüft der zweite Test, dass
keine Fehlerantwort ihren Code als Literal oder ihren Text als Satz trägt.
"""

import ast
from pathlib import Path

import pytest

from tests.test_migration_reason_catalogue import reason_entries

_APP = Path("app")
_CATALOGUES = (Path("dashboard/src/i18n/de.ts"), Path("dashboard/src/i18n/en.ts"))

# Kürzer als das ist kein Satz, sondern ein Platzhalter. Kürzer als im
# Migrationstest, weil es kurze vollständige Sätze gibt („Nothing was entered.").
_MIN_SENTENCE_LENGTH = 15

# Wo `reason.ts` nach dem Satz zu einer Kennung sucht, in dieser Reihenfolge.
_SCOPES = ("  errors: {", "  migration: {")

# Konstruktoren einer Fehlerantwort und die Stelle ihres Codes: Position oder
# Schlüsselwort. `ApiError(status, code, …)` trägt ihn an zweiter Stelle.
_CODE_CARRIERS = {
    "ApiError": 1,
    "BackupError": 0,
    "DetailValueError": 0,
    "IntakeRejected": 0,
    "ErrorDetail": None,
    "BackupErrorDetail": None,
    "AmbiguousSymbolDetail": None,
}


def _modules() -> list[tuple[Path, ast.Module]]:
    return [
        (path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for path in sorted(_APP.rglob("*.py"))
    ]


def _string_constant(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _backend_codes() -> dict[str, str]:
    """Kennung → Fundstelle, für jede `REASON_*`-Konstante und jeden `BackupError`-Code."""
    codes: dict[str, str] = {}
    for path, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "BackupError":
                for statement in node.body:
                    if isinstance(statement, ast.Assign) and (value := _string_constant(statement.value)):
                        codes[value] = f"{path}:{statement.lineno}"
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            value = _string_constant(node.value)
            if isinstance(target, ast.Name) and target.id.startswith("REASON_") and value:
                codes[value] = f"{path}:{node.lineno}"
    return codes


def _catalogue_codes(catalogue: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for scope in _SCOPES:
        entries.update(reason_entries(catalogue, scope))
    return entries


def test_das_inventar_findet_die_kennungen() -> None:
    """Die Gegenprobe zur Sammlung: Findet sie nichts, beweist der Abgleich nichts."""
    codes = _backend_codes()

    assert {"quote_unavailable", "instrument_not_stored", "detail_not_editable", "backup_not_found"} <= set(codes)


@pytest.mark.parametrize("catalogue", _CATALOGUES, ids=lambda path: path.name)
def test_jede_kennung_des_backends_hat_einen_satz(catalogue: Path) -> None:
    """Keine Kennung ohne brauchbaren Satz — in keiner Sprache."""
    entries = _catalogue_codes(catalogue)

    missing = {code: where for code, where in _backend_codes().items() if code not in entries}
    assert not missing, f"{catalogue.name}: kein Satz für {missing}"

    too_short = {
        code: entries[code]
        for code in _backend_codes()
        if len(entries[code].strip()) < _MIN_SENTENCE_LENGTH
    }
    assert not too_short, f"{catalogue.name}: kein brauchbarer Satz für {too_short}"


def test_keine_fehlerantwort_traegt_einen_satz_oder_ein_codeliteral() -> None:
    """Der Riegel hinter dem Inventar.

    Verboten sind zwei Formen, mit denen eine Kennung oder ein Satz an der
    Sammlung vorbeiliefe:

    * ein Code als Literal in einem Fehlerkonstruktor, etwa
      ``ApiError(404, "irgendwas")`` statt einer `REASON_*`-Konstante;
    * ein Text in ``HTTPException(detail=…)`` als Literal oder f-String — die
      Form, die T-139 abgelöst hat.
    """
    findings: list[str] = []
    for path, tree in _modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name == "HTTPException":
                for keyword in node.keywords:
                    if keyword.arg == "detail" and isinstance(keyword.value, (ast.Constant, ast.JoinedStr)):
                        findings.append(f"{path}:{node.lineno} HTTPException mit Text")
            if name not in _CODE_CARRIERS:
                continue
            position = _CODE_CARRIERS[name]
            candidates = [keyword.value for keyword in node.keywords if keyword.arg == "code"]
            if position is not None and len(node.args) > position:
                candidates.append(node.args[position])
            for candidate in candidates:
                if isinstance(candidate, (ast.Constant, ast.JoinedStr)):
                    findings.append(f"{path}:{node.lineno} {name} mit Code-Literal")

    assert not findings, "\n".join(findings)
