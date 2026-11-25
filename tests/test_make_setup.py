"""`make setup` stellt die .venv her, Prüf-Targets richten bei Bedarf selbst ein.

Beide Tests laufen mit dem echten Makefile in einer Sandbox unter `tmp_path`,
ohne Netz: Die Abhängigkeitsdateien sind leer, und `devtools` ist ein Ersatz,
der nur seine Aufrufe mitschreibt.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_MIN = "3.14"
OLDER_PYTHON = "python3.13"

requires_bootstrap = pytest.mark.skipif(
    shutil.which(f"python{PYTHON_MIN}") is None,
    reason=f"python{PYTHON_MIN} nicht installiert",
)


def _sandbox(tmp_path: Path) -> Path:
    """Arbeitskopie mit dem echten Makefile und leeren Abhängigkeiten."""
    workspace = tmp_path / "work"
    (workspace / "dashboard").mkdir(parents=True)
    for name in ("Makefile", ".dev-tools.conf.sh"):
        shutil.copy(ROOT / name, workspace / name)
    (workspace / "pyproject.toml").write_text(
        f'[project]\nname = "setup-test"\nrequires-python = ">={PYTHON_MIN}"\n'
    )
    for name in ("requirements.txt", "requirements-dev.txt"):
        (workspace / name).write_text("")
    (workspace / "plugin_api").mkdir()
    (workspace / "plugin_api" / "pyproject.toml").write_text('[project]\nname = "plugin-test"\n')
    (workspace / "dashboard" / "package-lock.json").write_text("{}\n")
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    return workspace


def _fake_devtools(tmp_path: Path) -> tuple[str, Path]:
    """Ersatz für devtools, der nur seine Aufrufe mitschreibt.

    Returns:
        PATH mit dem Ersatz vorn und die Datei mit den Aufrufen.
    """
    calls = tmp_path / "devtools-calls.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    devtools = fake_bin / "devtools"
    devtools.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\n')
    devtools.chmod(0o755)
    return f"{fake_bin}{os.pathsep}{os.environ['PATH']}", calls


def _set_up(workspace: Path, *, venv_stamp: bool = True) -> float:
    """Stand nach einem früheren `make setup`: Stempel neuer als ihre Abhängigkeiten, Hooks aktiv.

    Returns:
        Zeitstempel der Stempel.
    """
    stamps = [
        workspace / "dashboard" / "node_modules" / ".installed",
        workspace / ".tools" / ".installed",
    ]
    if venv_stamp:
        stamps.append(workspace / ".venv" / f".installed-python{PYTHON_MIN}")
    later = time.time() + 10
    for stamp in stamps:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        os.utime(stamp, (later, later))
    subprocess.run(
        ["git", "-C", str(workspace), "config", "core.hooksPath", ".githooks"], check=True
    )
    return later


def _python_version(workspace: Path) -> str:
    return subprocess.run(
        [str(workspace / ".venv" / "bin" / "python"), "-c", "import sys; print(sys.version_info[:2])"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _make(workspace: Path, *goals: str, path: str | None = None) -> subprocess.CompletedProcess:
    environment = {key: value for key, value in os.environ.items() if key != "BASH_LIBS"}
    if path is not None:
        environment["PATH"] = path
    return subprocess.run(
        ["make", "--no-print-directory", *goals],
        cwd=workspace,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def _venv(workspace: Path, interpreter: str = f"python{PYTHON_MIN}") -> None:
    subprocess.run(
        [interpreter, "-m", "venv", "--without-pip", str(workspace / ".venv")], check=True
    )


def _break_interpreter(workspace: Path, tmp_path: Path) -> None:
    """Interpreter-Link der .venv zeigt ins Leere, wie nach einem entfernten Homebrew-Python."""
    interpreter = workspace / ".venv" / "bin" / f"python{PYTHON_MIN}"
    interpreter.unlink()
    interpreter.symlink_to(tmp_path / "entfernt" / f"python{PYTHON_MIN}")


def _dead_link(workspace: Path, tmp_path: Path) -> None:
    _venv(workspace)
    _break_interpreter(workspace, tmp_path)


def _older_python(workspace: Path, tmp_path: Path) -> None:
    if shutil.which(OLDER_PYTHON) is None:
        pytest.skip(f"{OLDER_PYTHON} nicht installiert")
    _venv(workspace, OLDER_PYTHON)


@requires_bootstrap
@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(None, id="venv-fehlt"),
        pytest.param(_dead_link, id="interpreter-link-zeigt-ins-leere"),
        pytest.param(_older_python, id="venv-mit-zu-altem-python"),
    ],
)
def test_setup_legt_eine_unbrauchbare_venv_neu_an(tmp_path: Path, prepare) -> None:
    """Fehlende, kaputte und zu alte .venv enden in einer lauffähigen mit Python ab der Mindestversion.

    Die kaputte und die zu alte .venv stammen aus einem früheren `make setup`,
    ihr Stempel ist also aktuell. Zeigt der Interpreter-Link ins Leere, etwa
    nachdem Homebrew das alte Python entfernt hat, scheiterte `make setup`
    früher mit Errno 2 oder hielt die .venv wegen des Stempels für eingerichtet
    (T-153).
    """
    workspace = _sandbox(tmp_path)
    path, calls = _fake_devtools(tmp_path)
    if prepare is not None:
        prepare(workspace, tmp_path)
    _set_up(workspace, venv_stamp=prepare is not None)

    result = _make(workspace, "setup", path=path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _python_version(workspace) == str(tuple(int(part) for part in PYTHON_MIN.split(".")))
    assert not calls.exists()


@requires_bootstrap
def test_pruef_targets_richten_nur_eine_veraltete_einrichtung_ein(tmp_path: Path) -> None:
    """require-setup ruft `make setup` genau dann auf, wenn die Einrichtung fehlt oder veraltet ist.

    Ist alles eingerichtet, startet es nichts. Nach einer geänderten
    `.dev-tools.conf.sh` richtet es die Werkzeuge genau einmal neu ein, und
    eine .venv mit ins Leere zeigendem Interpreter legt es trotz aktuellem
    Stempel neu an, statt abzubrechen und `make setup` zu verlangen
    (makefile-conventions, Einrichtungsvertrag).
    """
    workspace = _sandbox(tmp_path)
    path, calls = _fake_devtools(tmp_path)
    _venv(workspace)
    later = _set_up(workspace)

    current = _make(workspace, "require-setup", path=path)
    assert current.returncode == 0, current.stdout + current.stderr
    assert not calls.exists()
    assert "neu angelegt" not in current.stdout

    newer = later + 10
    os.utime(workspace / ".dev-tools.conf.sh", (newer, newer))
    outdated = _make(workspace, "require-setup", path=path)
    assert outdated.returncode == 0, outdated.stdout + outdated.stderr
    assert calls.read_text().splitlines() == ["--project install"]

    # Wieder eingerichtet: Der Ersatz-devtools stempelt mit der echten Zeit, die Config lag in
    # der Zukunft. Jede weitere Phase hat so genau einen Grund für make setup, und kein
    # zweiter devtools-Aufruf zeigt, dass der Werkzeugstempel ihn nicht geliefert hat.
    past = time.time() - 100
    os.utime(workspace / ".dev-tools.conf.sh", (past, past))
    settled = _make(workspace, "require-setup", path=path)
    assert settled.returncode == 0, settled.stdout + settled.stderr
    assert calls.read_text().splitlines() == ["--project install"]

    _break_interpreter(workspace, tmp_path)
    broken = _make(workspace, "require-setup", path=path)
    assert broken.returncode == 0, broken.stdout + broken.stderr
    assert _python_version(workspace) == str(tuple(int(part) for part in PYTHON_MIN.split(".")))
    assert calls.read_text().splitlines() == ["--project install"]

    # requirements.txt installiert das Plugin-Paket editierbar; dessen Abhängigkeiten und
    # Entry-Points landen nur beim Installieren in der .venv (T-154).
    venv_stamp = workspace / ".venv" / f".installed-python{PYTHON_MIN}"
    installed = venv_stamp.stat().st_mtime
    changed = newer + 10
    os.utime(workspace / "plugin_api" / "pyproject.toml", (changed, changed))
    plugin_changed = _make(workspace, "require-setup", path=path)
    assert plugin_changed.returncode == 0, plugin_changed.stdout + plugin_changed.stderr
    assert venv_stamp.stat().st_mtime > installed
    assert calls.read_text().splitlines() == ["--project install"]
