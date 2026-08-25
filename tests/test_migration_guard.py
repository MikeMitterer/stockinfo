"""Die Verriegelung im Pending-Zustand (T-21 2A, `#2b6`, `#2b6d`, `#2b6h`, `#2b6j`).

Hier steht die **Regel**; dass sie über HTTP auch greift, prüft der
Routentabellen-Test, sobald der Guard in der App hängt. Der Unterschied ist
absichtlich: Eine Allowlist, die nur gegen sich selbst geprüft wird, hätte
weder die fehlende SVG noch das fehlende `/` gefunden — beide sind hier
namentlich verankert, weil beide schon einmal gefehlt haben.
"""

import os
import threading

import pytest

from app.migration_guard import (
    ALLOWED_ROUTES,
    HEALTHCHECK_PATH,
    MigrationGate,
    is_allowed,
    static_allowlist,
)

_DIST = "dashboard/dist"


def _real_files(root: str) -> set[str]:
    """Zählt die real ausgelieferten Dateien auf — **unabhängig** formuliert.

    Bewusst eine zweite, hier ausgeschriebene Wanderung statt eines Aufrufs
    von `static_allowlist`: Ein Orakel, das die geprüfte Funktion benutzt,
    bestätigt nur, dass sie mit sich selbst übereinstimmt. Ein vergessenes
    Unterverzeichnis fehlte dann auf beiden Seiten.

    Args:
        root: Verzeichnis mit dem gebauten Dashboard.

    Returns:
        Die Pfade mit führendem ``/``, ohne den Alias `/`.
    """
    found = set()
    for directory, _, filenames in os.walk(root):
        for filename in filenames:
            full = os.path.join(directory, filename)
            found.add("/" + os.path.relpath(full, root))
    return found


@pytest.mark.skipif(
    not os.path.isdir(_DIST), reason="Dashboard nicht gebaut — `make build` fehlt"
)
def test_jede_real_ausgelieferte_datei_ist_freigegeben() -> None:
    """Das Inventar wird abgeleitet, nicht abgeschrieben.

    Die Gegenrechnung läuft über eine eigene Wanderung, damit ein Fehler in
    der Ableitung nicht auf beiden Seiten gleich auftritt.
    """
    allowed = static_allowlist(_DIST)

    assert _real_files(_DIST) <= allowed


@pytest.mark.skipif(
    not os.path.isdir(_DIST), reason="Dashboard nicht gebaut — `make build` fehlt"
)
def test_das_favicon_aus_der_index_html_ist_dabei() -> None:
    """Der namentliche Rückfall: `/stockinfo-icon.svg`.

    Der frühere Entwurf zählte die statischen Pfade von Hand auf und nannte
    `/stockinfo-icon.png`, aber nicht die `.svg` — und genau die fordert
    `dashboard/index.html` als FavIcon an. Im Pending-Zustand hätte der Guard
    einen realen Dashboard-Request abgewiesen. Ursache war eine abgeschnittene
    Messung: `ls dashboard/dist | head -6`, und die SVG war der siebte Eintrag.
    """
    allowed = static_allowlist(_DIST)

    assert "/stockinfo-icon.svg" in allowed
    assert any(path.startswith("/assets/") for path in allowed)


def test_die_startadresse_ist_kein_praefix(tmp_path) -> None:
    """`#2b6j`: `/` gilt als **exakter** Pfad, nie als Präfix.

    Das Dashboard ist unter `/` gemountet. Gälte der Alias als Präfix, gäbe er
    jede Fach-API mit frei — der Guard wäre dann eine Zusage ohne Wirkung.
    """
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    allowed = static_allowlist(str(tmp_path))

    assert "/" in allowed
    assert is_allowed("GET", "/", allowed) is True
    assert is_allowed("GET", "/quote/EUNL.DE", allowed) is False
    assert is_allowed("GET", "/instruments", allowed) is False


def test_ohne_index_html_gibt_es_keine_startadresse(tmp_path) -> None:
    """Der Alias hängt an der Bedingung, nicht an der Gewohnheit."""
    (tmp_path / "logo.png").write_bytes(b"x")
    allowed = static_allowlist(str(tmp_path))

    assert allowed == frozenset({"/logo.png"})


def test_ohne_verzeichnis_ist_der_statische_teil_leer() -> None:
    """Der lokale Entwicklungsfall.

    Die Vorgabe zeigt auf den Container-Pfad `/app/web`, den es außerhalb des
    Images nicht gibt. Dann ist nichts gemountet — und nichts freigegeben.
    """
    assert static_allowlist("/gibt/es/nicht") == frozenset()


def test_ein_symlink_aus_dem_verzeichnis_hinaus_ist_gesperrt(tmp_path) -> None:
    """Begrenzt auf genau dieses Verzeichnis, ohne Pfadausbruch.

    Ein Symlink, der aus `static_dir` hinauszeigt, gehört nicht zur
    Oberfläche. Gäbe der Guard ihn frei, wäre die Allowlist ein Leseweg in
    beliebige Dateien des Containers.
    """
    außerhalb = tmp_path / "geheim.txt"
    außerhalb.write_text("nicht ausliefern", encoding="utf-8")
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<html></html>", encoding="utf-8")
    os.symlink(außerhalb, web / "leak.txt")

    allowed = static_allowlist(str(web))

    assert allowed == frozenset({"/", "/index.html"})


@pytest.mark.parametrize(
    ("method", "path"),
    sorted(ALLOWED_ROUTES),
)
def test_jeder_erlaubte_pfad_kommt_durch(method: str, path: str) -> None:
    """Die Allowlist ist die Quelle — der Test zählt **aus ihr** auf.

    Sie hier noch einmal abzuschreiben hieße, zwei Listen zu pflegen; der
    Test bestätigte dann seine eigene Kopie.
    """
    assert is_allowed(method, path, frozenset()) is True


def test_der_healthcheck_pfad_steht_in_der_allowlist() -> None:
    """`#2b6f`: Guard und Dockerfile hängen an derselben Konstante.

    Der Dockerfile kann kein Python importieren; dass seine `HEALTHCHECK`-URL
    genau dieser Pfad ist, prüft ein eigener Test. Hier wird nur festgehalten,
    dass die Konstante überhaupt freigegeben ist — sonst sperrte der Guard
    ausgerechnet den Endpunkt, an dem der Healthcheck hängt.
    """
    assert ("GET", HEALTHCHECK_PATH) in ALLOWED_ROUTES


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/quote/EUNL.DE"),
        ("GET", "/instruments"),
        ("POST", "/refresh"),
        ("PUT", "/instruments/1/isin"),
        ("DELETE", "/instruments/1"),
        ("GET", "/exchanges"),
        ("POST", "/migration"),
        ("GET", "/migration/confirm"),
    ],
    ids=[
        "lesen_quote",
        "lesen_instruments",
        "schreiben_refresh",
        "schreiben_put",
        "schreiben_delete",
        "lesen_exchanges",
        "falsche_methode_vorschau",
        "falsche_methode_bestaetigung",
    ],
)
def test_alles_andere_bleibt_gesperrt(method: str, path: str) -> None:
    """Auch **Lese**wege bleiben zu — und die Methode zählt mit.

    Ein `POST /migration` ist kein erlaubter Pfad, nur weil `/migration` in
    der Liste steht: Die Allowlist führt Paare, keine Pfade.
    """
    assert is_allowed(method, path, frozenset()) is False


def test_die_freigabe_gewinnt_genau_ein_aufrufer() -> None:
    """`#2b6d`: gegen parallele und doppelte Aufrufe verriegelt.

    Ein einfaches Flag hätte zwei Löcher: Zwei gleichzeitige Bestätigungen
    liefen beide durch, und eine wiederholte gäbe den Betrieb ein zweites Mal
    frei. Geprüft wird deshalb mit echten Threads, nicht nacheinander.
    """
    gate = MigrationGate()
    gate.block()
    gewonnen: list[bool] = []
    barrier = threading.Barrier(8)

    def bestaetigen() -> None:
        barrier.wait()
        gewonnen.append(gate.confirm())

    threads = [threading.Thread(target=bestaetigen) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert gewonnen.count(True) == 1
    assert gate.pending is False


def test_ohne_ausstehenden_umzug_gibt_es_nichts_freizugeben() -> None:
    """Eine Bestätigung ins Leere ist kein Erfolg.

    Sonst könnte ein zweiter Aufruf denselben Ablauf ein weiteres Mal
    auslösen — Scheduler und Endpunkte werden **genau einmal** freigegeben.
    """
    gate = MigrationGate()

    assert gate.pending is False
    assert gate.confirm() is False
