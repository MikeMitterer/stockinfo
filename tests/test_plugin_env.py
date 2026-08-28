"""Beigesteuerte Pakete installieren — Hash, Idempotenz, Fehlschlag.

Der Installer wird **ohne Netz** geprüft: `ensure` nimmt den Installationsweg
als Parameter, damit ein Test die Logik messen kann, statt ein Paket aus dem
Netz zu holen. Das ist kein zweiter Installationsweg — der echte steht als
Vorgabe in der Signatur und ist derselbe Code.

Was hier belegt wird, ist der Grund für das ganze Verzeichnis: Beim offiziellen
Container liegt `site-packages` im Image und überlebt kein `docker pull`. Unter
`/data` liegt es im Volume.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.plugin_env import ENV_DIRNAME, activate, ensure, environment_hash


def _fake_install(marker: str = "meinpaket"):
    """Ein Installer, der zählt und eine Datei hinterlässt."""
    calls: list[list[str]] = []

    def install(packages: Sequence[str], target: Path) -> None:
        calls.append(list(packages))
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{marker}.py").write_text("VALUE = 1\n", encoding="utf-8")

    install.calls = calls  # type: ignore[attr-defined]
    return install


def test_dieselbe_liste_ergibt_denselben_ordner() -> None:
    """Die Reihenfolge in der Datei ist keine Aussage.

    Wer zwei Zeilen tauscht, hat nichts geändert — und soll auch nichts neu
    installieren. Ohne die Sortierung wäre jede Umsortierung ein zweiter
    Ordner, und der Start dauerte plötzlich Minuten.
    """
    assert environment_hash(["b==2", "a==1"]) == environment_hash(["a==1", "b==2"])
    assert environment_hash(["a==1"]) != environment_hash(["a==2"]), (
        "eine andere Version ist eine andere Umgebung"
    )


def test_der_zweite_start_installiert_nicht_erneut(tmp_path: Path) -> None:
    """**Der Kern des Hashes: Idempotenz.**

    Ohne ihn liefe bei jedem Start ein `pip install` — im besten Fall langsam,
    im schlechteren gegen einen Paketindex, der gerade nicht da ist.
    """
    install = _fake_install()

    erste = ensure(["meinpaket==1.0"], tmp_path, install)
    zweite = ensure(["meinpaket==1.0"], tmp_path, install)

    assert erste == zweite
    assert len(install.calls) == 1, "der zweite Start hat nur nachgesehen"


def test_eine_geaenderte_liste_bekommt_ein_eigenes_verzeichnis(tmp_path: Path) -> None:
    """Ein Zurückrollen ist damit ein Zeileneditat in `sources.yaml`.

    Der alte Ordner bleibt liegen — das ist billiger als jede Migration und
    macht den Weg zurück sofort verfügbar.
    """
    install = _fake_install()

    alt = ensure(["meinpaket==1.0"], tmp_path, install)
    neu = ensure(["meinpaket==2.0"], tmp_path, install)

    assert alt != neu
    assert alt.is_dir() and neu.is_dir(), "die alte Umgebung bleibt bestehen"


def test_eine_leere_liste_legt_nichts_an(tmp_path: Path) -> None:
    """Die meisten Installationen haben keine beigesteuerten Pakete."""
    install = _fake_install()

    assert ensure([], tmp_path, install) is None
    assert not (tmp_path / ENV_DIRNAME).exists()
    assert install.calls == []


def test_ein_fehlschlag_kostet_die_pakete_und_nicht_den_start(tmp_path: Path) -> None:
    """**Dieselbe Regel wie bei jedem anderen Plugin-Defekt.**

    Und die zweite Hälfte ist die wichtigere: Es bleibt **kein halb gefüllter
    Ordner** unter dem endgültigen Namen zurück. Der nächste Start hielte ihn
    sonst für fertig und fände die Hälfte der Pakete nicht — genau der Grund,
    warum erst in einem Zwischenordner gebaut und dann umbenannt wird.
    """

    def kaputt(packages: Sequence[str], target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "halb.py").write_text("# angefangen\n", encoding="utf-8")
        raise RuntimeError("Paketindex nicht erreichbar")

    assert ensure(["meinpaket==1.0"], tmp_path, kaputt) is None

    root = tmp_path / ENV_DIRNAME
    assert not (root / environment_hash(["meinpaket==1.0"])).exists()
    assert list(root.glob("*")) == [], "auch der Zwischenordner ist weg"


def test_das_verzeichnis_kommt_vorn_in_den_suchpfad(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Vorn, damit ein beigesteuertes Paket gegen das Image gewinnt.

    Sonst trüge der Betreiber ein Paket ein, bekäme aber weiter die Fassung aus
    dem Image — und hätte keinen Hinweis darauf.
    """
    import sys

    monkeypatch.setattr(sys, "path", list(sys.path))
    ziel = ensure(["meinpaket==1.0"], tmp_path, _fake_install())

    activate(ziel)

    assert sys.path[0] == str(ziel)

    activate(ziel)
    assert sys.path.count(str(ziel)) == 1, "zweimal aktivieren fügt nichts hinzu"


def test_ein_installiertes_paket_ist_danach_importierbar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Die Probe aufs Exempel — ohne sie prüfte alles darüber nur Pfadarithmetik."""
    import sys

    monkeypatch.setattr(sys, "path", list(sys.path))
    activate(ensure(["meinpaket==1.0"], tmp_path, _fake_install("frisch_geliefert")))

    import frisch_geliefert  # noqa: PLC0415 — genau das ist der Test

    assert frisch_geliefert.VALUE == 1
