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


def _build_wheel(directory: Path) -> Path:
    """Baut ein winziges, gültiges Wheel — ohne Netz und ohne Build-Werkzeug.

    Ein Wheel **ist** ein ZIP mit festgelegter Struktur. Es hier von Hand zu
    schreiben ist ehrlicher als ein Mock: Der Test benutzt danach den echten
    `pip`-Aufruf samt `--only-binary=:all:` und Constraint, und genau der ist
    die Zusage.
    """
    import zipfile

    name, version = "demo_plugin", "1.0.0"
    dist = f"{name}-{version}.dist-info"
    wheel = directory / f"{name}-{version}-py3-none-any.whl"

    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"{name}/__init__.py", "MARKER = 'aus dem Zielordner'\n"
        )
        archive.writestr(
            f"{name}/quelle.py",
            "from stockinfo_plugin.sources import Resolver\n"
            "class DemoResolver(Resolver):\n"
            "    name = 'demo-installiert'\n",
        )
        archive.writestr(
            f"{dist}/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        )
        archive.writestr(
            f"{dist}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: handarbeit\nRoot-Is-Purelib: true\n"
            "Tag: py3-none-any\n",
        )
        archive.writestr(
            f"{dist}/entry_points.txt",
            "[stockinfo.sources]\n"
            f"demo-installiert = {name}.quelle:DemoResolver\n",
        )
        archive.writestr(f"{dist}/RECORD", "")
    return wheel


def test_ein_ueber_den_zielordner_installiertes_paket_wird_entdeckt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Der Beleg für den Installer selbst — nicht für die Entwicklungsumgebung.**

    Der mitgelieferte Beispiel-Entry-Point ist ohnehin installiert; er beweist
    den Ladeweg, aber nichts über diesen Installer. Hier wird ein Paket
    wirklich über `ensure()` in den hash-benannten Ordner gelegt und danach in
    `importlib.metadata` gesucht.

    Ohne Netz: `PIP_NO_INDEX` und `PIP_FIND_LINKS` sind pips eigene
    Einstellungen — dafür braucht der Produktionscode keinen Testhaken.
    """
    import sys
    from importlib import metadata

    from app.plugin_loader import ENTRY_POINT_GROUP

    lager = tmp_path / "wheels"
    lager.mkdir()
    _build_wheel(lager)

    monkeypatch.setenv("PIP_NO_INDEX", "1")
    monkeypatch.setenv("PIP_FIND_LINKS", str(lager))
    monkeypatch.setattr(sys, "path", list(sys.path))

    ziel = ensure(["demo-plugin==1.0.0"], tmp_path)

    assert ziel is not None, "die Installation ist fehlgeschlagen"
    assert (ziel / "demo_plugin").is_dir(), "das Paket liegt im Zielordner"

    activate(ziel)
    metadata.MetadataPathFinder.invalidate_caches()

    gefunden = {point.name for point in metadata.entry_points(group=ENTRY_POINT_GROUP)}
    assert "demo-installiert" in gefunden, (
        f"der Entry-Point aus {ziel} wurde nicht entdeckt: {sorted(gefunden)}"
    )


# ─── Das dokumentierte Format, und was es abweist ─────────────────────────────


def _config(tmp_path: Path, body: str):
    """Liest eine `sources.yaml` mit dem angegebenen Rumpf."""
    from app.config import Settings
    from app.sources_config import load_sources_config

    path = tmp_path / "sources.yaml"
    path.write_text(body, encoding="utf-8")
    return load_sources_config(path, Settings())


def test_die_paketliste_steht_unter_plugins(tmp_path: Path) -> None:
    """**Ein Parserpfad, der dokumentierte.**

    Ticket und Design zeigen `plugins.packages`. Bis Runde 4 las die App ein
    undokumentiertes Feld auf oberster Ebene — wer dem Design folgte, bekam
    eine leere Liste und keinen Hinweis darauf.
    """
    config = _config(
        tmp_path,
        "plugins:\n  packages:\n    - stockinfo-source-eodhd==1.2.3\n",
    )

    assert config.packages == ("stockinfo-source-eodhd==1.2.3",)


@pytest.mark.parametrize(
    ("eintrag", "warum"),
    [
        ("demo", "ohne Version wäre derselbe Hash morgen ein anderes Paket"),
        ("demo>=1.0", "eine Spanne ist keine feste Version"),
        ("git+https://example.test/x.git", "eine URL ist keine Anforderung"),
        ("--index-url=https://example.test", "eine pip-Option ist kein Paket"),
    ],
)
def test_was_nicht_fest_gepinnt_ist_wird_abgewiesen(
    tmp_path: Path, eintrag: str, warum: str
) -> None:
    """Feste `==`-Versionen sind Pflicht — die Regel steht im Design.

    Der Ordnername ist eine Prüfsumme über diese Liste. Ohne feste Version
    zeigte derselbe Hash morgen auf ein anderes Paket, und niemand sähe es.
    Eine URL oder eine Option wäre zusätzlich ein Weg, dem Installer etwas
    unterzuschieben.
    """
    config = _config(tmp_path, f"plugins:\n  packages:\n    - {eintrag!r}\n")

    assert config.packages == (), warum


def test_ein_gueltiger_eintrag_ueberlebt_neben_einem_abgewiesenen(
    tmp_path: Path,
) -> None:
    """Die zweite Hälfte: Ein schlechter Eintrag kostet nicht die guten.

    Dieselbe Regel wie bei jedem Plugin-Defekt — und ohne diesen Test bewiese
    die Prüfung nur, dass sie streng ist.
    """
    config = _config(
        tmp_path,
        "plugins:\n  packages:\n    - demo\n    - stockinfo-source-eodhd==1.2.3\n",
    )

    assert config.packages == ("stockinfo-source-eodhd==1.2.3",)
