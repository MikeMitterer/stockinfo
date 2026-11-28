"""`make build-check` (docker/build.sh --check) prüft das gebaute Image und räumt auf."""

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ID = "sha256:" + "a" * 64
CONTAINER_ID = "container-1"


def _check_sandbox(tmp_path: Path, failing_step: str) -> tuple[Path, dict[str, str]]:
    """Echtes Buildscript; docker, curl, sleep, BashLib und CLITheme sind Attrappen.

    `failing_step` lässt einen Schritt nach dem Containerstart scheitern:
    `port` (docker port), `page` (Abruf von /) oder leer.

    Returns:
        Skriptpfad und Umgebung.
    """
    for directory in ("docker", "bin", "libs"):
        (tmp_path / directory).mkdir(parents=True)
    shutil.copy(ROOT / "docker/build.sh", tmp_path / "docker/build.sh")
    (tmp_path / "docker/Dockerfile").write_text("FROM python:3.11\n")
    (tmp_path / "docker/.last-build-tag").write_text(
        f"v1\n{int(time.time())}\n{IMAGE_ID}\nsource-commit\ndockerhub\n"
    )
    (tmp_path / "libs/build.lib.sh").write_text(
        'RED="" NC="" YELLOW="" GREEN="" BLUE="" ARCHITECTURE=arm64\n'
    )
    (tmp_path / "libs/version.lib.sh").write_text("gitDockerTag() { echo v1; }\n")
    (tmp_path / "libs/docker.lib.sh").write_text("")
    docker_stub = (
        'echo "$*" >> "$CALL_LOG"\n'
        'case "$1" in\n'
        f"  run) echo {CONTAINER_ID};;\n"
        '  port) [ "$FAILING_STEP" = port ] && exit 17; echo 127.0.0.1:49999;;\n'
        "esac\n"
    )
    curl_stub = (
        'case "$*" in\n'
        "  */health*) echo '{\"status\":\"ok\"}';;\n"
        '  *) [ "$FAILING_STEP" = page ] && exit 28; echo \'<div id="app"></div>\';;\n'
        "esac\n"
    )
    for name, content in {
        "bin/docker": docker_stub,
        "bin/curl": curl_stub,
        "bin/git": "echo source-commit\n",
    }.items():
        path = tmp_path / name
        path.write_text("#!/bin/sh\n" + content)
        path.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}",
        "BASH_LIBS": str(tmp_path / "libs"),
        "CLI_LIBS": str(tmp_path / "libs"),
        "CALL_LOG": str(tmp_path / "calls"),
        "FAILING_STEP": failing_step,
    }
    return tmp_path / "docker/build.sh", environment


@pytest.mark.parametrize(
    ("failing_step", "expected_status"),
    [("", 0), ("port", 17), ("page", 1)],
    ids=["erfolg", "docker-port-scheitert", "dashboard-abruf-scheitert"],
)
def test_check_startet_die_aufgezeichnete_image_id_und_raeumt_immer_auf(
    tmp_path: Path, failing_step: str, expected_status: int
) -> None:
    """Gestartet wird die Image-ID des Builds, nicht der Tag; der Container geht immer weg."""
    script, environment = _check_sandbox(tmp_path, failing_step)

    result = subprocess.run(
        ["bash", str(script), "--check"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == expected_status, result.stdout + result.stderr
    calls = (tmp_path / "calls").read_text().splitlines()
    run_call = next(call for call in calls if call.startswith("run "))
    assert run_call.endswith(f" {IMAGE_ID}"), run_call
    assert "--pull never" in run_call
    assert calls[-1] == f"rm -f {CONTAINER_ID}", calls
