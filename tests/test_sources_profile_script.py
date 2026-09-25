"""Profilwechsel mit echten Dateien in einem isolierten Datenverzeichnis."""

import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

from app.config import Settings
from app.sources_config import load_sources_config
from plugin_api.examples.yaml_file import YamlFileSource
from stockinfo_plugin import IsinOnlyIdentity, Quote, QuoteRequest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sources-profile.sh"
VOLUME_HELPER = ROOT / "scripts/sources-profile-volume.py"


def test_docker_vorgaben_passen_zu_make_up(tmp_path):
    """Volume und Image aus dem Startbefehl gelten auch für den Profilwechsel."""
    makefile = (ROOT / "Makefile").read_text()
    volume_name = re.search(r"^DATA_VOLUME\s+\?=\s+(\S+)$", makefile, re.MULTILINE)
    image_name = re.search(r"^IMAGE_NAME\s+\?=\s+(\S+)$", makefile, re.MULTILINE)
    assert volume_name is not None
    assert image_name is not None
    environment = {**os.environ, "DATABASE_PATH": str(tmp_path / "stockinfo.db")}
    environment.pop("STOCKINFO_VOLUME", None)
    environment.pop("STOCKINFO_IMAGE", None)
    result = subprocess.run(
        ["bash", str(SCRIPT), "--info", "--target", "docker"],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert f"{volume_name.group(1)}:/data/sources.yaml" in result.stdout
    assert f"{image_name.group(1)}:latest" in result.stdout


def run_profile(directory: Path, *arguments: str) -> subprocess.CompletedProcess:
    """Führt das Skript ohne Zugriff auf die Betriebsdatenbank aus."""
    return subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        cwd=directory,
        env={**os.environ, "DATABASE_PATH": str(directory / "stockinfo.db")},
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize("target", ["local", "docker"])
def test_profile_bleiben_getrennt_und_benutzerdaten_erhalten(tmp_path, target):
    directory = tmp_path / "Mike's data #1"
    directory.mkdir()
    arguments = ("--target", target, "--data-dir", str(directory))
    config = directory / "sources.yaml"
    config.write_text("# Eigene Konfiguration\nquotes: [yfinance]\n")
    original = config.read_bytes()
    for action, suffix in [("--online", "fallback"), ("--yaml", "standalone")]:
        result = run_profile(directory, action, *arguments)
        assert result.returncode == 0, result.stderr + result.stdout
        asset = directory / f"assets-{suffix}.yaml"
        assert (
            asset.read_bytes() == (ROOT / f"examples/assets-{suffix}.yaml").read_bytes()
        )
        settings = yaml.safe_load(config.read_text())
        expected = asset.name
        assert settings["providers"]["yaml-file"]["path"] == expected
        assert settings["quotes"] == (
            ["yfinance", "yaml-file"] if suffix == "fallback" else ["yaml-file"]
        )
        template = yaml.safe_load(
            (ROOT / f"examples/sources-{suffix}.yaml").read_text()
        )
        template["providers"]["yaml-file"]["path"] = expected
        assert settings == template
        loaded = load_sources_config(config, Settings())
        plugin = YamlFileSource(loaded.config_for("yaml-file"))
        assert plugin.configuration_problem() == ""
        quote = plugin.fetch_quote(
            QuoteRequest(identity=IsinOnlyIdentity(isin="DE0001102531"))
        )
        assert isinstance(quote, Quote)
        assert quote.price == 99.42
        assert (
            Path(loaded.config_for("yaml-file")["path"]).read_bytes()
            == asset.read_bytes()
        )
        asset.write_text(asset.read_text() + "\n# Eigener Kursstand\n")
    assert any(
        path.read_bytes() == original for path in directory.glob("sources.yaml.bak*")
    )
    result = run_profile(directory, "--online", *arguments)
    assert result.returncode == 0, result.stderr + result.stdout
    assert (
        (directory / "assets-fallback.yaml")
        .read_text()
        .endswith("# Eigener Kursstand\n")
    )
    assert (
        (directory / "assets-standalone.yaml")
        .read_text()
        .endswith("# Eigener Kursstand\n")
    )


def test_fehlende_eigene_datei_laesst_konfiguration_unberuehrt(tmp_path):
    config = tmp_path / "sources.yaml"
    config.write_text("quotes: [yfinance]\n")
    result = run_profile(tmp_path, "--yaml", "--assets", str(tmp_path / "missing.yaml"))
    assert result.returncode != 0
    assert config.read_text() == "quotes: [yfinance]\n"


def test_docker_kopiert_nicht_ueber_vorhandene_fachdaten(tmp_path):
    source = tmp_path / "custom.yaml"
    source.write_text("# Neue Datei\n")
    volume = tmp_path / "volume"
    volume.mkdir()
    (volume / source.name).write_text("# Bestehende Benutzerdaten\n")
    result = run_profile(
        tmp_path,
        "--yaml",
        "--target",
        "docker",
        "--data-dir",
        str(volume),
        "--assets",
        str(source),
    )
    assert result.returncode != 0
    assert (volume / source.name).read_text() == "# Bestehende Benutzerdaten\n"
    assert not (volume / "sources.yaml").exists()


@pytest.mark.parametrize("arguments", [(), ("--help",), ("--info",)])
def test_auskunft_schreibt_keine_dateien(tmp_path, arguments):
    result = run_profile(tmp_path, *arguments)
    assert result.returncode == 0, result.stderr
    assert result.stdout
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("target", ["local", "docker"])
def test_eigene_datei_wird_neben_die_konfiguration_kopiert(tmp_path, target):
    source = tmp_path / "custom.yaml"
    source.write_bytes((ROOT / "examples/assets-fallback.yaml").read_bytes())
    volume = tmp_path / "volume"
    volume.mkdir()
    result = run_profile(
        tmp_path,
        "--online",
        "--target",
        target,
        "--data-dir",
        str(volume),
        "--assets",
        str(source),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (volume / source.name).read_bytes() == source.read_bytes()
    settings = yaml.safe_load((volume / "sources.yaml").read_text())
    assert settings["providers"]["yaml-file"]["path"] == "custom.yaml"


def test_absolute_altpfade_bleiben_gueltig(tmp_path):
    asset = ROOT / "examples/assets-fallback.yaml"
    config = tmp_path / "sources.yaml"
    config.write_text(
        yaml.safe_dump({"providers": {"yaml-file": {"path": str(asset)}}})
    )
    loaded = load_sources_config(config, Settings())
    assert loaded.config_for("yaml-file")["path"] == str(asset)
    assert YamlFileSource(loaded.config_for("yaml-file")).configuration_problem() == ""


@pytest.mark.parametrize(
    ("extra_arguments", "volume_name"),
    [((), "stockinfo-data"), (("--volume", "other-volume"), "other-volume")],
)
@pytest.mark.parametrize(
    ("action", "expected_quotes", "asset_name"),
    [
        ("--yaml", ["yaml-file"], "assets-standalone.yaml"),
        ("--online", ["yfinance", "yaml-file"], "assets-fallback.yaml"),
    ],
)
def test_docker_vorgabe_schreibt_vor_dem_start_ins_benannte_volume(
    tmp_path, extra_arguments, volume_name, action, expected_quotes, asset_name
):
    """Ein falscher Host-Pfad darf nicht als erfolgreicher Docker-Wechsel gelten."""
    volume = tmp_path / "volume"
    volume.mkdir()
    config = volume / "sources.yaml"
    config.write_text("# Eigene Konfiguration\nquotes: [yfinance]\n")
    original = config.read_bytes()
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    fake_docker = executable_dir / "docker"
    fake_docker.write_text(
        "#!/usr/bin/env python3\n"
        "import os, subprocess, sys\n"
        "arguments = sys.argv[1:]\n"
        "assert arguments[:2] == ['run', '--rm']\n"
        "mounts = [arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == '--mount']\n"
        "assert 'type=volume,src=' + os.environ['PROFILE_TEST_VOLUME_NAME'] + ',dst=/data' in mounts\n"
        "input_mount = next(value for value in mounts if ',dst=/input,readonly' in value)\n"
        "input_dir = input_mount.split('src=', 1)[1].split(',dst=', 1)[0]\n"
        "helper_arguments = arguments[arguments.index('/profile-volume.py') + 1:]\n"
        "helper_arguments[1:3] = [input_dir, os.environ['PROFILE_TEST_VOLUME_DIR']]\n"
        "raise SystemExit(subprocess.call([sys.executable, os.environ['PROFILE_TEST_VOLUME_HELPER'], *helper_arguments]))\n"
    )
    fake_docker.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SCRIPT), action, "--target", "docker", *extra_arguments],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{executable_dir}{os.pathsep}{os.environ['PATH']}",
            "DATABASE_PATH": str(tmp_path / "stockinfo.db"),
            "PROFILE_TEST_VOLUME_DIR": str(volume),
            "PROFILE_TEST_VOLUME_NAME": volume_name,
            "PROFILE_TEST_VOLUME_HELPER": str(VOLUME_HELPER),
        },
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert yaml.safe_load(config.read_text())["quotes"] == expected_quotes
    assert (volume / asset_name).is_file()
    assert any(
        path.read_bytes() == original for path in volume.glob("sources.yaml.bak.*")
    )
    assert not (tmp_path / "stockinfo.db").exists()


def test_named_volume_anzeige_liest_quellenprofil_ohne_aenderung(tmp_path):
    """Die Volume-Anzeige liest die Datei, ohne eine zweite Quelle zu erfinden."""
    volume = tmp_path / "volume"
    volume.mkdir()
    config = volume / "sources.yaml"
    config.write_text("# stockinfo-profile: yaml\nquotes: [yaml-file]\n")
    result = subprocess.run(
        [sys.executable, str(VOLUME_HELPER), "read", str(volume)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == config.read_text()
    assert sorted(path.name for path in volume.iterdir()) == ["sources.yaml"]


def test_docker_show_nennt_das_benannte_volume(tmp_path):
    """Die Anzeige darf den früheren Unraid-Pfad nicht als aktive Datei ausgeben."""
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    fake_docker = executable_dir / "docker"
    fake_docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = volume ]; then exit 0; fi\n'
        'if [ "$1" = run ]; then\n'
        "  printf '# stockinfo-profile: yaml\\nquotes: [yaml-file]\\n'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_docker.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SCRIPT), "--show", "--target", "docker"],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{executable_dir}{os.pathsep}{os.environ['PATH']}",
            "PORT": "1",
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "stockinfo-data:/data/sources.yaml" in result.stdout
    assert "quotes" in result.stdout
    assert "/mnt/user/appdata/stockinfo" not in result.stdout


def test_named_volume_custom_asset_collision_erhaelt_config(tmp_path):
    """Eine fremde Fachdatei wird vor Sicherung und Konfigurationswechsel erkannt."""
    input_dir = tmp_path / "input"
    volume = tmp_path / "volume"
    input_dir.mkdir()
    volume.mkdir()
    (input_dir / "sources.yaml").write_text("quotes: [yaml-file]\n")
    (input_dir / "custom.yaml").write_text("new\n")
    (volume / "custom.yaml").write_text("existing\n")
    config = volume / "sources.yaml"
    config.write_text("quotes: [yfinance]\n")

    result = subprocess.run(
        [
            sys.executable,
            str(VOLUME_HELPER),
            "install",
            str(input_dir),
            str(volume),
            "custom.yaml",
            "custom",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "asset_collision" in result.stderr
    assert config.read_text() == "quotes: [yfinance]\n"
    assert (volume / "custom.yaml").read_text() == "existing\n"
    assert not list(volume.glob("sources.yaml.bak.*"))


def test_named_volume_behaelt_bereits_bearbeitete_standard_fachdaten(tmp_path):
    """Ein erneuter Profilwechsel darf die Werte im Volume nicht ersetzen."""
    input_dir = tmp_path / "input"
    volume = tmp_path / "volume"
    input_dir.mkdir()
    volume.mkdir()
    (input_dir / "sources.yaml").write_text("quotes: [yaml-file]\n")
    (input_dir / "assets-standalone.yaml").write_text("# Vorlage\n")
    asset = volume / "assets-standalone.yaml"
    asset.write_text("# Eigene Werte\n")

    result = subprocess.run(
        [
            sys.executable,
            str(VOLUME_HELPER),
            "install",
            str(input_dir),
            str(volume),
            "assets-standalone.yaml",
            "default",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert asset.read_text() == "# Eigene Werte\n"
    assert (volume / "sources.yaml").read_text() == "quotes: [yaml-file]\n"


def test_docker_fehler_meldet_keinen_erfolgreichen_wechsel(tmp_path):
    """Ohne Docker-Zugriff wird kein Profilwechsel als Erfolg ausgegeben."""
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    fake_docker = executable_dir / "docker"
    fake_docker.write_text("#!/bin/sh\necho 'Docker nicht erreichbar' >&2\nexit 44\n")
    fake_docker.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SCRIPT), "--yaml", "--target", "docker"],
        cwd=tmp_path,
        env={**os.environ, "PATH": f"{executable_dir}{os.pathsep}{os.environ['PATH']}"},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "nicht geändert" in result.stderr
    assert "Profil" not in result.stdout
