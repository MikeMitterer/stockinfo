"""Profilwechsel mit echten Dateien in einem isolierten Datenverzeichnis."""

import os
from pathlib import Path
import subprocess

import pytest
import yaml

from app.config import Settings
from app.sources_config import load_sources_config
from plugin_api.examples.yaml_file import YamlFileSource
from stockinfo_plugin import IsinOnlyIdentity, Quote, QuoteRequest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sources-profile.sh"


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
    config.write_text(yaml.safe_dump({"providers": {"yaml-file": {"path": str(asset)}}}))
    loaded = load_sources_config(config, Settings())
    assert loaded.config_for("yaml-file")["path"] == str(asset)
    assert YamlFileSource(loaded.config_for("yaml-file")).configuration_problem() == ""
