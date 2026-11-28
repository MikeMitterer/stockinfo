"""`make setup` stellt die .venv her, Prüf-Targets und BashLib-Targets richten bei Bedarf selbst ein.

Die Tests laufen mit dem echten Makefile in einer Sandbox unter `tmp_path`,
ohne Netz: Die Abhängigkeitsdateien sind leer, und `devtools` ist ein Ersatz,
der seine Aufrufe mitschreibt. `python3` im PATH der Sandbox ist ein Python in
der Mindestversion, wie auf einem Rechner mit Homebrew vor `/usr/bin`.
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
# Einrichtungsstempel des Makefiles (SETUP_STAMPS), relativ zur Arbeitskopie.
STAMPS = (
    f".venv/.installed-python{PYTHON_MIN}",
    "dashboard/node_modules/.installed",
    ".tools/.installed",
)

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


def _fake_devtools(tmp_path: Path, behaviour: str = "") -> tuple[str, Path]:
    """Ersatz für devtools, der seine Aufrufe mitschreibt und danach `behaviour` ausführt.

    Daneben `python3` als Link auf das Python der Mindestversion.

    Returns:
        PATH mit dem Ersatz vorn und die Datei mit den Aufrufen.
    """
    calls = tmp_path / "devtools-calls.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    devtools = fake_bin / "devtools"
    devtools.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{calls}"\n{behaviour}')
    devtools.chmod(0o755)
    (fake_bin / "python3").symlink_to(shutil.which(f"python{PYTHON_MIN}"))
    return f"{fake_bin}{os.pathsep}{os.environ['PATH']}", calls


def _set_up(workspace: Path, *, venv_stamp: bool = True) -> float:
    """Stand nach einem früheren `make setup`: Stempel neuer als ihre Abhängigkeiten, Hooks aktiv.

    Returns:
        Zeitstempel der Stempel.
    """
    stamps = [workspace / name for name in STAMPS if venv_stamp or not name.startswith(".venv/")]
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


def _make(
    workspace: Path, *goals: str, path: str | None = None, bootstrap: str | None = None
) -> subprocess.CompletedProcess:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in ("BASH_LIBS", "PYTHON_BOOTSTRAP")
    }
    if path is not None:
        environment["PATH"] = path
    if bootstrap is not None:
        environment["PYTHON_BOOTSTRAP"] = bootstrap
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
    """.venv aus der Zeit einer niedrigeren Mindestversion, samt deren Stempel."""
    if shutil.which(OLDER_PYTHON) is None:
        pytest.skip(f"{OLDER_PYTHON} nicht installiert")
    _venv(workspace, OLDER_PYTHON)
    (workspace / ".venv" / f".installed-{OLDER_PYTHON}").touch()


def _remove_minor_version_command(tmp_path: Path) -> None:
    """`python3.14` im PATH startet nicht mehr, wie nachdem Homebrew `python@3.14` entfernt hat.

    `python3` aus `_fake_devtools` zeigt weiter auf ein Python in der Mindestversion.
    """
    removed = tmp_path / "bin" / f"python{PYTHON_MIN}"
    removed.write_text(
        f'#!/usr/bin/env bash\necho "python{PYTHON_MIN}: No such file or directory" >&2\nexit 127\n'
    )
    removed.chmod(0o755)


@requires_bootstrap
@pytest.mark.parametrize(
    ("prepare", "venv_stamp"),
    [
        pytest.param(None, False, id="venv-fehlt"),
        pytest.param(_dead_link, True, id="interpreter-link-zeigt-ins-leere"),
        pytest.param(_older_python, False, id="venv-mit-zu-altem-python"),
    ],
)
def test_setup_legt_eine_unbrauchbare_venv_neu_an(tmp_path: Path, prepare, venv_stamp: bool) -> None:
    """Fehlende, kaputte und zu alte .venv enden in einer lauffähigen mit Python ab der Mindestversion.

    Die kaputte .venv stammt aus einem früheren `make setup`, ihr Stempel ist
    also aktuell. Zeigt der Interpreter-Link ins Leere, etwa nachdem Homebrew
    das alte Python entfernt hat, scheiterte `make setup` früher mit Errno 2
    oder hielt die .venv wegen des Stempels für eingerichtet (T-153). Die zu
    alte .venv trägt den Stempel einer niedrigeren Mindestversion.
    """
    workspace = _sandbox(tmp_path)
    path, calls = _fake_devtools(tmp_path)
    if prepare is not None:
        prepare(workspace, tmp_path)
    _set_up(workspace, venv_stamp=venv_stamp)

    result = _make(workspace, "setup", path=path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _python_version(workspace) == str(tuple(int(part) for part in PYTHON_MIN.split(".")))
    assert not calls.exists()


@requires_bootstrap
def test_setup_baut_eine_tote_venv_auch_ohne_den_befehl_der_alten_minor_version_neu(
    tmp_path: Path,
) -> None:
    """Nach einem Python-Wechsel baut ein einziger `make setup` die .venv mit `python3` neu.

    So war es am 2026-11-26: Homebrew entfernte `python@3.14`, die .venv zeigte
    ins Leere, und `python3.14` gab es nicht mehr. Das Makefile verlangte genau
    diesen Befehl und brach ab, auch im Worktree-Start eines Agenten (T-156).
    """
    workspace = _sandbox(tmp_path)
    path, calls = _fake_devtools(tmp_path)
    _dead_link(workspace, tmp_path)
    _set_up(workspace)
    _remove_minor_version_command(tmp_path)

    result = _make(workspace, "setup", path=path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _python_version(workspace) == str(tuple(int(part) for part in PYTHON_MIN.split(".")))
    assert _make(workspace, "--question", *STAMPS, path=path).returncode == 0
    assert not calls.exists()


@requires_bootstrap
@pytest.mark.skipif(shutil.which(OLDER_PYTHON) is None, reason=f"{OLDER_PYTHON} nicht installiert")
def test_setup_bricht_mit_zu_altem_python_ab_und_nennt_die_mindestversion(tmp_path: Path) -> None:
    """Ein zu altes `python3` legt keine .venv an; die Meldung nennt Mindestversion und Fund."""
    workspace = _sandbox(tmp_path)
    path, _ = _fake_devtools(tmp_path)

    result = _make(workspace, "setup", path=path, bootstrap=OLDER_PYTHON)

    assert result.returncode != 0
    assert f"Python {PYTHON_MIN} oder neuer nötig" in result.stderr
    assert OLDER_PYTHON.removeprefix("python") in result.stderr
    assert not (workspace / ".venv").exists()


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
    venv_stamp = workspace / STAMPS[0]
    installed = venv_stamp.stat().st_mtime
    changed = newer + 10
    os.utime(workspace / "plugin_api" / "pyproject.toml", (changed, changed))
    plugin_changed = _make(workspace, "require-setup", path=path)
    assert plugin_changed.returncode == 0, plugin_changed.stdout + plugin_changed.stderr
    assert venv_stamp.stat().st_mtime > installed
    assert calls.read_text().splitlines() == ["--project install"]


@requires_bootstrap
def test_bashlib_target_richtet_im_frischen_checkout_ein_und_laeuft_weiter(tmp_path: Path) -> None:
    """`make version` ohne .tools/ ruft einmal `make setup` auf und zeigt danach die Version.

    Fehlt BashLib, richtet require-bash-libs als Vorbedingung ein. Das Target
    danach sieht BashLib im selben Lauf nur, weil BASH_LIBS im Kopf des
    Makefiles mit `=` steht; mit `:=` bliebe es leer (T-155).
    """
    workspace = _sandbox(tmp_path)
    bashlib = tmp_path / "bashlib"
    bashlib.mkdir()
    (bashlib / "version.lib.sh").write_text("")
    (bashlib / "make.lib.sh").write_text('showProjectVersion() { echo "Version aus BashLib"; }\n')
    # install legt bashlib-path in .tools/ an; check bashlib besteht erst danach.
    path, calls = _fake_devtools(
        tmp_path,
        'case "$*" in\n'
        '  "--project install") mkdir -p .tools/bin\n'
        f"    printf '#!/usr/bin/env bash\\necho %s\\n' '{bashlib}' > .tools/bin/bashlib-path\n"
        "    chmod +x .tools/bin/bashlib-path ;;\n"
        '  "--project check bashlib") test -x .tools/bin/bashlib-path ;;\n'
        "esac\n",
    )
    _venv(workspace)
    _set_up(workspace)
    shutil.rmtree(workspace / ".tools")

    result = _make(workspace, "version", path=path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Version aus BashLib" in result.stdout
    assert calls.read_text().splitlines() == ["--project install", "--project check bashlib"]
