"""Eine Python-Mindestversion: pyproject.toml gibt sie vor, das Image folgt ihr."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_das_image_nutzt_die_python_version_aus_requires_python() -> None:
    """Das Laufzeit-Image baut auf der Mindestversion aus `requires-python`.

    Makefile und ruff lesen die Version aus pyproject.toml; das Dockerfile kann
    das nicht und nennt sie ein zweites Mal. Ohne diesen Vergleich bliebe das
    Image beim nächsten Anheben still auf der alten Version (T-152).
    """
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    minimum = project["project"]["requires-python"].removeprefix(">=")
    dockerfile = (ROOT / "docker/Dockerfile").read_text(encoding="utf-8")
    images = re.findall(r"^FROM python:(\d+\.\d+)-", dockerfile, flags=re.MULTILINE)

    assert images == [minimum]
