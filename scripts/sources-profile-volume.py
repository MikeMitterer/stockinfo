"""Überträgt ein vorbereitetes Quellenprofil in ein gemountetes Docker-Volume."""

import os
from pathlib import Path
import shutil
import sys
import tempfile


def copy_atomic(source: Path, target: Path) -> None:
    """Schreibt eine Datei erst vollständig und ersetzt dann das Ziel."""
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", dir=target.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as output, source.open("rb") as content:
            shutil.copyfileobj(content, output)
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


def install(
    input_dir: Path, volume_dir: Path, asset_name: str, asset_kind: str
) -> None:
    """Erhält vorhandene Fachdaten und sichert die bisherige Konfiguration."""
    if Path(asset_name).name != asset_name or asset_name == "sources.yaml":
        raise ValueError("invalid_asset_name")
    if asset_kind not in {"default", "custom"}:
        raise ValueError("invalid_asset_kind")
    source_asset = input_dir / asset_name
    source_config = input_dir / "sources.yaml"
    if (
        not volume_dir.is_dir()
        or not source_asset.is_file()
        or not source_config.is_file()
    ):
        raise ValueError("missing_input")

    target_asset = volume_dir / asset_name
    if target_asset.exists() and asset_kind == "custom":
        if target_asset.read_bytes() != source_asset.read_bytes():
            raise ValueError("asset_collision")
    elif not target_asset.exists():
        copy_atomic(source_asset, target_asset)

    target_config = volume_dir / "sources.yaml"
    if target_config.exists():
        file_descriptor, backup_name = tempfile.mkstemp(
            prefix="sources.yaml.bak.", dir=volume_dir
        )
        backup_path = Path(backup_name)
        try:
            with (
                os.fdopen(file_descriptor, "wb") as backup,
                target_config.open("rb") as current,
            ):
                shutil.copyfileobj(current, backup)
        except OSError:
            backup_path.unlink(missing_ok=True)
            raise
        print(f"backup:{backup_name}")
    copy_atomic(source_config, target_config)


def main(arguments: list[str]) -> int:
    """Die CLI-Grenze liefert stabile Fehlerkennungen an das Bash-Skript."""
    if len(arguments) == 2 and arguments[0] == "read":
        config = Path(arguments[1]) / "sources.yaml"
        if not config.is_file():
            print("config_missing", file=sys.stderr)
            return 3
        try:
            sys.stdout.buffer.write(config.read_bytes())
        except OSError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0
    if len(arguments) != 5 or arguments[0] != "install":
        print("invalid_arguments", file=sys.stderr)
        return 2
    _, input_name, volume_name, asset_name, asset_kind = arguments
    try:
        install(Path(input_name), Path(volume_name), asset_name, asset_kind)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
