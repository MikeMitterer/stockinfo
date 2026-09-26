"""StockInfo-Anbindung an den geteilten README-Upload."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".libs/ProjectTools/src/python/dockerhub-readme.py"


def test_cli_ohne_aktion_zeigt_hilfe_und_vorschau_braucht_keinen_token(
    tmp_path: Path,
) -> None:
    command = [sys.executable, str(SCRIPT)]
    help_result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert help_result.returncode == 0
    assert "--preview" in help_result.stdout and "--publish" in help_result.stdout
    output = tmp_path / "preview.md"
    result = subprocess.run(
        [
            *command,
            "--project-dir",
            str(ROOT),
            "--ref",
            "master",
            "--preview",
            "--output",
            str(output),
            "--token-file",
            str(tmp_path / "missing-token"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (
        "raw.githubusercontent.com/MikeMitterer/stockinfo/master/unraid/screenshots/dashboard.png"
        in output.read_text()
    )


@pytest.mark.parametrize(
    "target,image_status,readme_status,expected_status,expected_calls",
    [
        ("dockerhub", 0, 0, 0, ["image", "readme"]),
        ("dockerhub", 1, 0, 1, ["image"]),
        ("dockerhub", 0, 1, 1, ["image", "readme"]),
        ("ghcr", 0, 0, 0, ["image"]),
        ("ecr", 0, 0, 0, ["image"]),
    ],
)
def test_push_startet_readme_nur_nach_erfolgreichem_hub_push(
    tmp_path: Path,
    target: str,
    image_status: int,
    readme_status: int,
    expected_status: int,
    expected_calls: list[str],
) -> None:
    """Echtes Buildscript; Git, Docker und Upload-Prozess sind äußere Testgrenzen."""
    for directory in ("docker", "bin", "libs", ".venv/bin"):
        (tmp_path / directory).mkdir(parents=True)
    shutil.copy(ROOT / "docker/build.sh", tmp_path / "docker/build.sh")
    (tmp_path / "docker/Dockerfile").write_text("FROM python:3.11\n")
    (tmp_path / "docker/.last-build-tag").write_text(
        f"v1\n{int(time.time())}\nimage-id\nsource-commit\n{target}\n"
    )
    (tmp_path / "libs/build.lib.sh").write_text(
        'RED="" NC="" YELLOW="" GREEN="" BLUE="" ARCHITECTURE=arm64\n'
    )
    (tmp_path / "libs/version.lib.sh").write_text("gitDockerTag() { echo v1; }\n")
    (tmp_path / "libs/docker.lib.sh").write_text(
        'pushImage2DockerHub() { echo image >> "$CALL_LOG"; return "$IMAGE_STATUS"; }\n'
        "pushImage2GHCR() { pushImage2DockerHub; }\n"
        "pushImage2Amazon() { pushImage2DockerHub; }\n"
    )
    programs = {
        "bin/git": 'case "$*" in *rev-parse*) echo source-commit;; esac\n',
        "bin/docker": "echo image-id\n",
        ".venv/bin/python": (
            'echo readme >> "$CALL_LOG"\nprintf "%s\\n" "$@" > "$ARG_LOG"\n'
            'exit "$README_STATUS"\n'
        ),
    }
    for name, content in programs.items():
        path = tmp_path / name
        path.write_text("#!/bin/sh\n" + content)
        path.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
        "BASH_LIBS": str(tmp_path / "libs"),
        "TARGET": target,
        "AMAZON_REPO_URI": "example.ecr",
        "CALL_LOG": str(tmp_path / "calls"),
        "ARG_LOG": str(tmp_path / "args"),
        "IMAGE_STATUS": str(image_status),
        "README_STATUS": str(readme_status),
        "DOCKER_PW_FILE": str(tmp_path / "token file"),
    }
    result = subprocess.run(
        ["bash", str(tmp_path / "docker/build.sh"), "--push"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_status, result.stdout + result.stderr
    assert (tmp_path / "calls").read_text().splitlines() == expected_calls
    if "readme" in expected_calls:
        assert (tmp_path / "args").read_text().splitlines()[1:] == [
            "--project-dir",
            str(tmp_path / "docker/.."),
            "--ref",
            "master",
            "--publish",
            "--repository",
            "mangolila/stockinfo",
            "--token-file",
            str(tmp_path / "token file"),
        ]


def test_uploadfehler_nach_image_push_wird_klar_gemeldet(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--publish",
            "--project-dir",
            str(ROOT),
            "--ref",
            "master",
            "-r",
            "owner/repo",
            "-t",
            str(tmp_path / "missing-token"),
        ],
        env={**os.environ, "DOCKER_README_AFTER_PUSH": "1", "LANGUAGE": "de"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Image wurde bereits gepusht" in result.stderr
