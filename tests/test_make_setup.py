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
    (workspace / "dashboard" / "package-lock.json").write_text("{}\n")
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    return workspace


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


def _dead_link(workspace: Path, tmp_path: Path) -> None:
    """.venv, deren Interpreter-Link ins Leere zeigt, wie nach einem entfernten Homebrew-Python."""
    subprocess.run(
        [f"python{PYTHON_MIN}", "-m", "venv", "--without-pip", str(workspace / ".venv")],
        check=True,
    )
    interpreter = workspace / ".venv" / "bin" / f"python{PYTHON_MIN}"
    interpreter.unlink()
    interpreter.symlink_to(tmp_path / "entfernt" / f"python{PYTHON_MIN}")


def _older_python(workspace: Path, tmp_path: Path) -> None:
    if shutil.which(OLDER_PYTHON) is None:
        pytest.skip(f"{OLDER_PYTHON} nicht installiert")
    subprocess.run(
        [OLDER_PYTHON, "-m", "venv", "--without-pip", str(workspace / ".venv")], check=True
    )


@requires_bootstrap
@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(lambda workspace, tmp_path: None, id="venv-fehlt"),
        pytest.param(_dead_link, id="interpreter-link-zeigt-ins-leere"),
        pytest.param(_older_python, id="venv-mit-zu-altem-python"),
    ],
)
def test_setup_legt_eine_unbrauchbare_venv_neu_an(tmp_path: Path, prepare) -> None:
    """Fehlende, kaputte und zu alte .venv enden in einer lauffähigen mit Python ab der Mindestversion.

    Zeigt der Interpreter-Link ins Leere, etwa nachdem Homebrew das alte Python
    entfernt hat, scheiterte `make setup` früher mit Errno 2 (T-153).
    """
    workspace = _sandbox(tmp_path)
    prepare(workspace, tmp_path)

    result = _make(workspace, f".venv/.installed-python{PYTHON_MIN}")

    assert result.returncode == 0, result.stdout + result.stderr
    version = subprocess.run(
        [str(workspace / ".venv" / "bin" / "python"), "-c", "import sys; print(sys.version_info[:2])"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert version == str(tuple(int(part) for part in PYTHON_MIN.split(".")))


def test_pruef_targets_richten_nur_eine_veraltete_einrichtung_ein(tmp_path: Path) -> None:
    """require-setup ruft `make setup` genau dann auf, wenn ein Stempel fehlt oder veraltet ist.

    Ist alles eingerichtet, startet es nichts; nach einer geänderten
    `.dev-tools.conf.sh` richtet es die Werkzeuge genau einmal neu ein, statt
    abzubrechen und `make setup` zu verlangen (makefile-conventions,
    Einrichtungsvertrag).
    """
    workspace = _sandbox(tmp_path)
    calls = tmp_path / "devtools-calls.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    devtools = fake_bin / "devtools"
    devtools.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\n')
    devtools.chmod(0o755)
    path = f"{fake_bin}{os.pathsep}{os.environ['PATH']}"

    stamps = (
        workspace / ".venv" / f".installed-python{PYTHON_MIN}",
        workspace / "dashboard" / "node_modules" / ".installed",
        workspace / ".tools" / ".installed",
    )
    later = time.time() + 10
    for stamp in stamps:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        os.utime(stamp, (later, later))
    subprocess.run(
        ["git", "-C", str(workspace), "config", "core.hooksPath", ".githooks"], check=True
    )

    current = _make(workspace, "require-setup", path=path)
    assert current.returncode == 0, current.stdout + current.stderr
    assert not calls.exists()

    newer = later + 10
    os.utime(workspace / ".dev-tools.conf.sh", (newer, newer))
    outdated = _make(workspace, "require-setup", path=path)
    assert outdated.returncode == 0, outdated.stdout + outdated.stderr
    assert calls.read_text().splitlines() == ["--project install"]
