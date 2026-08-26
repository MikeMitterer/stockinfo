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


#: Kürzer als das ist kein Satz, sondern ein Platzhalter.
_MINDESTLAENGE = 25


def _reason_entries(catalogue: Path) -> dict[str, str]:
    """Die Einträge des `reason`-Blocks — Kennung **und** Satz.

    Gelesen wird nur der Block, nicht die ganze Datei: Ein `grep` über alles
    würde eine Kennung auch dann finden, wenn sie zufällig in einem Kommentar
    steht — der Test wäre grün und der Katalog trotzdem unvollständig.

    **Der Wert wird mitgenommen, seit Runde 35.** Vorher verwarf diese Funktion
    ihn, und beide Prüfungen verglichen nur Mengen von Schlüsseln. Ein auf `''`
    gesetzter englischer Grund blieb damit grün, obwohl der Test „jede Kennung
    hat einen Satz" zusagte — die Prüfung, die weniger konnte als ihr eigener
    Docstring.

    TypeScript setzt lange Texte aus mehreren Literalen mit `+` zusammen;
    zusammengefügt wird deshalb alles, was zwischen zwei Schlüsseln an
    einfach gequoteten Zeichenketten steht.

    Args:
        catalogue: Pfad zur `de.ts` oder `en.ts`.

    Returns:
        Kennung → zusammengesetzter Satz.
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
    key = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*):", flags=re.MULTILINE)
    matches = list(key.finditer(block))

    entries: dict[str, str] = {}
    for index, match in enumerate(matches):
        bis = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        rohwert = block[match.end() : bis]
        entries[match.group(1)] = "".join(re.findall(r"'((?:[^'\\]|\\.)*)'", rohwert))
    return entries


@pytest.mark.parametrize("catalogue", _CATALOGUES, ids=lambda path: path.name)
def test_jede_kennung_ist_im_katalog(catalogue: Path) -> None:
    """Keine Kennung ohne Eintrag — in keiner Sprache.

    Die Gegenrichtung wird mitgeprüft: Ein Katalogeintrag ohne Kennung im
    Backend ist eine Leiche, die beim Lesen Vollständigkeit vortäuscht.
    """
    assert catalogue.exists(), f"{catalogue} fehlt"

    keys = set(_reason_entries(catalogue))

    assert keys == set(REJECTION_REASONS), (
        f"{catalogue.name}: fehlend {set(REJECTION_REASONS) - keys}, "
        f"überzählig {keys - set(REJECTION_REASONS)}"
    )


@pytest.mark.parametrize("catalogue", _CATALOGUES, ids=lambda path: path.name)
def test_jede_kennung_hat_einen_brauchbaren_satz(catalogue: Path) -> None:
    """Ein Schlüssel ohne Satz ist schlimmer als kein Schlüssel.

    Er sieht im Katalog nach Vollständigkeit aus, und in der Oberfläche steht
    an der Stelle **nichts** — ausgerechnet in der Liste, auf deren Grundlage
    jemand einer Löschung zustimmt.

    Geprüft wird deshalb der Text selbst: nichtleer, nicht bloß die Kennung
    noch einmal, und lang genug, um ein Satz zu sein. Der frühere
    Mengenvergleich der Schlüssel ließ ein `''` durch (Codex, Runde 35).
    """
    for reason, satz in sorted(_reason_entries(catalogue).items()):
        assert satz.strip(), f"{catalogue.name}: `{reason}` hat keinen Text"
        assert satz.strip() != reason, f"{catalogue.name}: `{reason}` wiederholt nur sich selbst"
        assert len(satz.strip()) >= _MINDESTLAENGE, (
            f"{catalogue.name}: `{reason}` ist mit {len(satz.strip())} Zeichen "
            f"kein Satz, sondern ein Platzhalter"
        )


def test_beide_sprachen_kennen_dieselben_kennungen() -> None:
    """Deutsch ist die Basis, Englisch zieht nach — und zwar vollständig.

    Ohne diese Prüfung könnte `en.ts` eine Kennung verlieren, ohne dass es
    auffällt: `satisfies typeof de` prüft die **Form** des Katalogs, und die
    verlangt nur, dass die Schlüssel existieren — ein leerer String wäre
    typkonform. Dass sie auch gefüllt sind, prüft der Test darüber.
    """
    de_keys, en_keys = (set(_reason_entries(catalogue)) for catalogue in _CATALOGUES)

    assert de_keys == en_keys, f"nur in DE: {de_keys - en_keys}, nur in EN: {en_keys - de_keys}"


def test_die_beiden_sprachen_sagen_nicht_dasselbe() -> None:
    """Ein kopierter deutscher Satz im englischen Katalog ist keine Übersetzung.

    Der Fall ist real: Wer eine Kennung nachträgt, kopiert den Block und
    vergisst die zweite Sprache. Die Schlüssel stimmen dann, die Mengen
    stimmen, die Länge stimmt — und die englische Oberfläche ist deutsch.
    """
    de_entries, en_entries = (_reason_entries(catalogue) for catalogue in _CATALOGUES)

    gleich = [reason for reason, satz in de_entries.items() if en_entries.get(reason) == satz]

    assert not gleich, f"in beiden Katalogen wortgleich: {gleich}"
