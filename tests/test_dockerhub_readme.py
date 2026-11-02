"""StockInfo-Anbindung an den geteilten README-Upload."""

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECT_TOOLS = os.environ.get("PROJECT_TOOLS", "")
SCRIPT = Path(PROJECT_TOOLS) / "bash/dockerhub-readme.sh" if PROJECT_TOOLS else None

# Der README-Upload ist ein Maintainer-Werkzeug aus ProjectTools; einen
# pipx-Befehl hat er noch nicht, deshalb kommt er über PROJECT_TOOLS. Ohne die
# Variable gilt der Test als übersprungen statt als Fehler.
requires_project_tools = pytest.mark.skipif(
    SCRIPT is None or not SCRIPT.exists(),
    reason="PROJECT_TOOLS zeigt nicht auf ProjectTools/src (Maintainer-Werkzeug)",
)


# Netz nötig: Mit leerem `XDG_CACHE_HOME` richtet das Skript seine
# Werkzeug-venv neu ein und lädt die Pakete aus dem Paketindex.
@pytest.mark.integration
@requires_project_tools
def test_cli_ohne_aktion_zeigt_hilfe_und_vorschau_braucht_keinen_token(
    tmp_path: Path,
) -> None:
    command = [str(SCRIPT)]
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
        env={**os.environ, "XDG_CACHE_HOME": str(tmp_path / "cache")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    content = output.read_text()
    assert "docker run -d" in content
    assert "python3.11 -m venv" not in content
    assert (
        "raw.githubusercontent.com/MikeMitterer/stockinfo/master/unraid/screenshots/dashboard.png"
        in output.read_text()
    )


def _push_sandbox(tmp_path: Path, target: str) -> dict[str, str]:
    """Echtes Buildscript in tmp_path; Git, Docker und BashLib sind Attrappen.

    Returns:
        Umgebung für den Push-Lauf, ohne PROJECT_TOOLS.
    """
    for directory in ("docker", "bin", "libs"):
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
    for name, content in {
        "bin/git": 'case "$*" in *rev-parse*) echo source-commit;; esac\n',
        "bin/docker": "echo image-id\n",
    }.items():
        path = tmp_path / name
        path.write_text("#!/bin/sh\n" + content)
        path.chmod(0o755)
    environment = {
        key: value for key, value in os.environ.items() if key != "PROJECT_TOOLS"
    }
    environment.update(
        {
            "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
            "BASH_LIBS": str(tmp_path / "libs"),
            "TARGET": target,
            "AMAZON_REPO_URI": "example.ecr",
            "CALL_LOG": str(tmp_path / "calls"),
            "IMAGE_STATUS": "0",
            "DOCKER_PW_FILE": str(tmp_path / "token file"),
        }
    )
    return environment


def _push(
    tmp_path: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(tmp_path / "docker/build.sh"), "--push"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
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
    environment = _push_sandbox(tmp_path, target)
    upload = tmp_path / "tools/bash/dockerhub-readme.sh"
    upload.parent.mkdir(parents=True)
    upload.write_text(
        '#!/bin/sh\necho readme >> "$CALL_LOG"\nprintf "%s\\n" "$@" > "$ARG_LOG"\n'
        'exit "$README_STATUS"\n'
    )
    upload.chmod(0o755)
    environment.update(
        {
            "PROJECT_TOOLS": str(tmp_path / "tools"),
            "ARG_LOG": str(tmp_path / "args"),
            "IMAGE_STATUS": str(image_status),
            "README_STATUS": str(readme_status),
        }
    )
    result = _push(tmp_path, environment)
    assert result.returncode == expected_status, result.stdout + result.stderr
    assert (tmp_path / "calls").read_text().splitlines() == expected_calls
    if "readme" in expected_calls:
        assert (tmp_path / "args").read_text().splitlines() == [
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


def test_push_ohne_project_tools_nennt_die_variable(tmp_path: Path) -> None:
    """Nach dem Hub-Push fehlt der Upload: klare Meldung statt „No such file“."""
    result = _push(tmp_path, _push_sandbox(tmp_path, "dockerhub"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert (tmp_path / "calls").read_text().splitlines() == ["image"]
    assert "PROJECT_TOOLS zeigt nicht auf ProjectTools/src" in result.stderr


@requires_project_tools
def test_uploadfehler_nach_image_push_wird_klar_gemeldet(tmp_path: Path) -> None:
    result = subprocess.run(
        [
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
