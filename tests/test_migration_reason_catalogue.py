"""Die Ablehnungsgründe stehen in **beiden** Sprachen — `#2b7`.

Der Vertrag ist bewusst geteilt: Das Backend schickt eine **stabile Kennung**,
den Satz dazu liefert das UI aus seinem Katalog. Ein Satz aus dem Backend wäre
in der zweiten Sprache sofort falsch.

Der Preis dieser Teilung ist eine Fuge, die niemand sieht: Wer in
`app/migration.py` eine Kennung ergänzt, merkt nicht, dass zwei
TypeScript-Dateien davon nichts wissen. Im UI stünde dann für ein entferntes
Papier die rohe Kennung statt eines Grundes — und das ausgerechnet in der
Liste, auf deren Grundlage jemand einer Löschung zustimmt.

Deshalb prüft dieser Test **über die Sprachgrenze hinweg**, genauso wie der
Test, der die `HEALTHCHECK`-URL im Dockerfile gegen `HEALTHCHECK_PATH` hält.
Python kann kein TypeScript importieren, also wird die Datei gelesen.
"""

import re
from pathlib import Path

import pytest

from app.migration import REJECTION_REASONS

_CATALOGUES = (
    Path("dashboard/src/i18n/de.ts"),
    Path("dashboard/src/i18n/en.ts"),
)


def _reason_keys(catalogue: Path) -> set[str]:
    """Die Schlüssel des `reason`-Blocks aus einem Message-Katalog.

    Gelesen wird nur der Block, nicht die ganze Datei: Ein `grep` über alles
    würde eine Kennung auch dann finden, wenn sie zufällig in einem Kommentar
    steht — der Test wäre grün und der Katalog trotzdem unvollständig.

    Args:
        catalogue: Pfad zur `de.ts` oder `en.ts`.

    Returns:
        Die Schlüssel im `reason`-Block.
    """
    text = catalogue.read_text(encoding="utf-8")
    start = text.index("reason: {") + len("reason: {")

    depth = 1
    end = start
    while depth > 0:
        char = text[end]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        end += 1

    block = text[start : end - 1]
    # Bewusst nicht nur `[a-z_]`: Sonst fiele ein versehentlich anders
    # geschriebener Schlüssel aus der Suche heraus und die Richtung
    # „überzählig" fände ihn nie.
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*):", block, flags=re.MULTILINE))


@pytest.mark.parametrize("catalogue", _CATALOGUES, ids=lambda path: path.name)
def test_jede_kennung_hat_einen_satz(catalogue: Path) -> None:
    """Keine Kennung ohne Text — in keiner Sprache.

    Die Gegenrichtung wird mitgeprüft: Ein Katalogeintrag ohne Kennung im
    Backend ist eine Leiche, die beim Lesen Vollständigkeit vortäuscht.
    """
    assert catalogue.exists(), f"{catalogue} fehlt"

    keys = _reason_keys(catalogue)

    assert keys == set(REJECTION_REASONS), (
        f"{catalogue.name}: fehlend {set(REJECTION_REASONS) - keys}, "
        f"überzählig {keys - set(REJECTION_REASONS)}"
    )


def test_beide_sprachen_kennen_dieselben_kennungen() -> None:
    """Deutsch ist die Basis, Englisch zieht nach — und zwar vollständig.

    Ohne diese Prüfung könnte `en.ts` eine Kennung verlieren, ohne dass es
    auffällt: `satisfies typeof de` prüft die **Form** des Katalogs, und die
    verlangt nur, dass die Schlüssel existieren — ein leerer String wäre
    typkonform. Der Vergleich beider Blöcke ist deshalb die zweite Frage.
    """
    de_keys, en_keys = (_reason_keys(catalogue) for catalogue in _CATALOGUES)

    assert de_keys == en_keys, f"nur in DE: {de_keys - en_keys}, nur in EN: {en_keys - de_keys}"
