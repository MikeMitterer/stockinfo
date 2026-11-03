"""`make tag-*` bumpt, taggt und schreibt den Changelog nur lokal."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _bash_libs() -> str:
    """BashLib wie im Makefile: ein gesetztes BASH_LIBS, sonst bashlib-path."""
    configured = os.environ.get("BASH_LIBS", "")
    if configured:
        return configured
    if shutil.which("bashlib-path") is None:
        return ""
    return subprocess.run(
        ["bashlib-path"], capture_output=True, text=True, check=False
    ).stdout.strip()


BASH_LIBS = _bash_libs()

# Ein Release braucht BashLib und changelog aus ProjectTools, beides
# Maintainer-Werkzeuge. Ohne sie gilt der Test als übersprungen statt als Fehler.
requires_release_tools = pytest.mark.skipif(
    not (BASH_LIBS and (Path(BASH_LIBS) / "version.lib.sh").is_file())
    or shutil.which("changelog") is None,
    reason="BashLib oder changelog (ProjectTools) nicht installiert",
)


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _release_sandbox(tmp_path: Path) -> tuple[Path, Path]:
    """Repo mit dem echten Makefile, erstem Release und einem Bare-Remote als origin.

    Returns:
        Arbeitskopie und Remote.
    """
    remote = tmp_path / "remote.git"
    repository = tmp_path / "work"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "-q", "--bare", "-b", "master", str(remote)], check=True
    )
    _git(repository, "init", "-q", "-b", "master")
    _git(repository, "config", "user.name", "Release Test")
    _git(repository, "config", "user.email", "release-test@example.invalid")
    _git(repository, "config", "commit.gpgsign", "false")
    _git(repository, "config", "tag.gpgsign", "false")
    for name in ("Makefile", ".dev-tools.conf.sh", ".dev-ports.conf.sh"):
        shutil.copy(ROOT / name, repository / name)
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "release-test"\nversion = "0.1.0"\n'
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-q", "-m", "feat: erster Stand")
    _git(repository, "tag", "-a", "v0.1.0+260101.1200.00000", "-m", "Release 0.1.0")
    _git(repository, "remote", "add", "origin", str(remote))
    _git(repository, "push", "-q", "-u", "origin", "master", "--follow-tags")
    _git(repository, "commit", "-q", "--allow-empty", "-m", "fix: kleine Korrektur")
    return repository, remote


@requires_release_tools
def test_tag_patch_committet_und_taggt_nur_lokal(tmp_path: Path) -> None:
    """Versions-Commit, Tag und Changelog-Commit entstehen, der Remote bleibt gleich."""
    repository, remote = _release_sandbox(tmp_path)
    remote_before = _git(remote, "show-ref")

    result = subprocess.run(
        ["make", "--no-print-directory", "tag-patch", "DEV_TOOLS=true"],
        cwd=repository,
        env={**os.environ, "BASH_LIBS": BASH_LIBS, "LANGUAGE": "en"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert _git(remote, "show-ref") == remote_before
    assert _git(repository, "status", "--porcelain") == ""
    assert _git(repository, "log", "-1", "--format=%s") == (
        "docs(changelog): update release history\n"
    )
    assert "CHANGELOG.md" in _git(repository, "ls-files")
    new_tag = _git(repository, "describe", "--tags", "--abbrev=0", "HEAD~1").strip()
    assert new_tag.startswith("v0.1.1+"), new_tag
    assert 'version = "0.1.1"' in (repository / "pyproject.toml").read_text()
    assert f"## {new_tag} " in (repository / "CHANGELOG.md").read_text()
