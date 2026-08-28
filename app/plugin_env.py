"""Beigesteuerte Pakete installieren — schlank, idempotent, unter `/data`.

Der Entry-Point-Weg findet jedes Paket, das in der Umgebung der App liegt. Beim
offiziellen Container genügt `pip install` trotzdem nicht: Dessen
`site-packages` liegt im **Image** und ist nach dem nächsten `docker pull`
wieder weg. Wer sein Plugin behalten will, müsste es nach jedem Update erneut
installieren — und würde es vergessen.

Deshalb installiert die App die in `sources.yaml` genannten Pakete selbst,
**unter `/data`**, wo das Volume liegt. Ein Image-Update lässt sie unberührt.

**Der Hash ist der Kern.** Der Zielordner heißt nach einer Prüfsumme über die
sortierte Paketliste:

    data/plugin-env/9f2a1c…/

Dieselbe Liste ⇒ derselbe Ordner ⇒ **keine Installation**. Der Start ist damit
idempotent und kostet im Normalfall einen `exists()`-Aufruf. Eine geänderte
Liste ergibt einen anderen Ordner; der alte bleibt liegen, bis jemand aufräumt
— das ist billiger als jede Migration und macht ein Zurückrollen zu einem
Zeileneditat in `sources.yaml`.

**Was hier ausdrücklich nicht steht:** keine Kandidatenumgebung, kein
Aktivierungszeiger, kein Preflight, keine Netzsperre. Diese Maschinerie
beantwortet die Frage „ein fremdes, unbekanntes Paket in eine laufende Instanz
schleusen" — die es hier nicht gibt. Ein Plugin läuft ohnehin mit den Rechten
der App; wer es einträgt, hat sich dafür entschieden. Vgl. die gestrichene
Verify-Zeile `#6c` in T-23.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

import structlog

logger = structlog.get_logger()

ENV_DIRNAME = "plugin-env"
"""Unterverzeichnis im Datenvolume für die installierten Pakete."""

HASH_LENGTH = 16
"""Wie viele Hex-Stellen des Hashes den Ordner benennen.

Sechzehn Stellen sind 64 Bit — für eine Handvoll Paketlisten pro Installation
weit jenseits jeder Kollision, und kurz genug, um in einer Fehlermeldung noch
lesbar zu sein.
"""

INSTALL_TIMEOUT = 300
"""Sekunden für den Installationslauf.

Ohne Grenze hängt der **Start der App** an einem stummen Paketindex, und der
Dienst sähe aus, als wäre er abgestürzt.
"""


def environment_hash(packages: Sequence[str]) -> str:
    """Die Kennung einer Paketliste.

    Sortiert und normalisiert, damit die Reihenfolge in der Datei keine Rolle
    spielt: Wer zwei Zeilen tauscht, hat nichts geändert und soll auch nichts
    neu installieren.
    """
    normalised = sorted(entry.strip() for entry in packages if entry.strip())
    payload = "\n".join(normalised).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:HASH_LENGTH]


def _pip_install(packages: Sequence[str], target: Path) -> None:
    """Installiert die Pakete nach `target` — der echte Weg.

    `--target` statt einer virtuellen Umgebung: Wir brauchen nur ein
    Verzeichnis im Suchpfad, keinen zweiten Interpreter. Das ist weniger, und
    weniger ist hier richtig.
    """
    subprocess.run(  # noqa: S603 — Argumente stammen aus sources.yaml, nicht von außen
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--disable-pip-version-check",
            "--target",
            str(target),
            *packages,
        ],
        check=True,
        timeout=INSTALL_TIMEOUT,
        capture_output=True,
    )


def ensure(
    packages: Sequence[str],
    data_dir: Path | str = "data",
    installer: Callable[[Sequence[str], Path], None] = _pip_install,
) -> Path | None:
    """Stellt sicher, dass die Pakete installiert sind, und liefert ihr Verzeichnis.

    Args:
        packages: Die Paketliste aus `sources.yaml`, mit festen Versionen.
        data_dir: Das Datenvolume.
        installer: Wie installiert wird. Hereingereicht, damit ein Test die
            Logik prüfen kann, ohne ein Paket aus dem Netz zu holen — nicht,
            um einen zweiten Installationsweg anzubieten.

    Returns:
        Das Verzeichnis zum Einhängen in `sys.path`, oder ``None`` — dann gibt
        es nichts zu tun oder die Installation ist gescheitert.

    **Ein Fehlschlag kostet die Pakete, nicht den Start.** Dieselbe Regel wie
    bei jedem anderen Plugin-Defekt: Die App läuft weiter, mit den Quellen, die
    sie hat, und der Grund steht im Protokoll.
    """
    wanted = [entry.strip() for entry in packages if entry.strip()]
    if not wanted:
        return None

    root = Path(data_dir) / ENV_DIRNAME
    target = root / environment_hash(wanted)
    if target.is_dir():
        logger.info("plugin_env_reused", path=str(target), packages=len(wanted))
        return target

    # **Erst vollständig bauen, dann umbenennen.** Ein abgebrochener Lauf darf
    # keinen halb gefüllten Ordner unter dem endgültigen Namen hinterlassen —
    # der nächste Start hielte ihn für fertig und fände die Hälfte der Pakete
    # nicht. Dasselbe Muster wie beim atomaren Schreiben einer Datei.
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=root, prefix=".unfertig-"))
    try:
        installer(wanted, staging)
        os.replace(staging, target)
    except Exception as error:  # noqa: BLE001 — pip, Netz, Zeitgrenze: alles zählt
        shutil.rmtree(staging, ignore_errors=True)
        logger.warning(
            "plugin_env_install_failed",
            packages=wanted,
            error=f"{type(error).__name__}: {error}",
        )
        return None

    logger.info("plugin_env_installed", path=str(target), packages=len(wanted))
    return target


def activate(path: Path | None) -> None:
    """Hängt das Verzeichnis vorn in den Suchpfad.

    **Vorn und nicht hinten:** Ein beigesteuertes Paket soll gelten, wenn es
    denselben Namen trägt wie etwas im Image — sonst hätte der Betreiber es
    eingetragen und bekäme trotzdem die alte Fassung.

    Danach findet `importlib.metadata` die Entry-Points der Gruppe
    `stockinfo.sources`; ab dort ist ein installiertes Plugin von einem
    mitgelieferten nicht mehr zu unterscheiden.
    """
    if path is None:
        return
    location = str(path)
    if location not in sys.path:
        sys.path.insert(0, location)
