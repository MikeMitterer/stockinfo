"""Sicherung, Kennung und Liste.

Die Zusicherungen stammen aus der Verify-Matrix, nicht aus dem Code:

===== ======================================================================
`#1`  Eine Sicherung **während eines offenen Schreibvorgangs** trägt den
      festgeschriebenen Stand — und nicht den halb geschriebenen
`#2`  Die Liste nennt Zeitpunkt, Größe und Passung und stimmt mit dem
      Verzeichnis überein; Unpassendes steht mit Grund darin
`#9`  `PRAGMA user_version` ist gesetzt und wird gelesen
`#10` Die elfte Sicherung lässt zehn liegen, die älteste weicht samt Manifest
===== ======================================================================
"""

import json
import sqlite3
from collections import Counter
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import get_backup_service, get_sources_config
from app.db import SCHEMA_VERSION, get_connection, init_db
from app.main import app
from app.services.backup import (
    KEEP_BACKUPS,
    BackupService,
    fingerprint_of,
    stamp_fingerprint,
)
from app.sources_config import ROLES, SourcesConfig

_ONLINE = SourcesConfig(
    chains={
        "resolvers": ("openfigi", "yahoo-search"),
        "etf_meta": ("justetf",),
        "quotes": ("yfinance",),
        "daily": ("yfinance",),
        "fx": ("yfinance",),
    }
)
_FILE_ONLY = SourcesConfig(chains={role: ("yaml-file",) for role in ROLES})
"""**Der Fall, um den es geht:** Dieselben Papiere stehen hier in anderer Form."""


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    database = tmp_path / "stockinfo.db"
    init_db(str(database))
    stamp_fingerprint(database, fingerprint_of(_ONLINE))
    return tmp_path


def _service(volume: Path, config: SourcesConfig = _ONLINE) -> BackupService:
    return BackupService(str(volume / "stockinfo.db"), config)


def _insert(connection, symbol: str) -> None:
    connection.execute(
        "INSERT INTO instruments (symbol, isin, kind, type, first_seen) "
        "VALUES (?, ?, 'isin_only', 'bond', '2026-09-01T00:00:00Z')",
        (symbol, symbol),
    )


def _symbols(database: Path) -> list[str]:
    connection = sqlite3.connect(database)
    try:
        return sorted(row[0] for row in connection.execute("SELECT symbol FROM instruments"))
    finally:
        connection.close()


def _age(path: Path, index: int) -> Path:
    """Rückt eine Sicherung im Namen nach vorn — sonst steht die Reihenfolge nicht.

    Gibt den **neuen** Pfad zurück: Eine Zusicherung über den alten Namen
    beträfe eine Datei, die es nach dem Umbenennen nicht mehr gibt, und wäre
    damit immer erfüllt.
    """
    older = path.with_name(path.name.replace("stockinfo-2", f"stockinfo-1{index:03d}", 1))
    path.rename(older)
    if path.with_suffix(".json").exists():
        path.with_suffix(".json").rename(older.with_suffix(".json"))
    return older


# ─── #9 · die Schemaversion ───────────────────────────────────────────────────


def test_eine_frische_datenbank_traegt_ihre_schemaversion(volume: Path) -> None:
    """Ohne diese Zahl gäbe es keine Antwort auf „ist die Datei neuer als ich?".

    `schema_outdated()` prüft die Form strukturell und erkennt nur die
    Gegenrichtung; eine Sicherung aus einer neueren App sähe für sie
    unauffällig aus.
    """
    connection = sqlite3.connect(volume / "stockinfo.db")
    try:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    finally:
        connection.close()


def test_die_sicherung_traegt_die_schemaversion_mit(volume: Path) -> None:
    """`VACUUM INTO` nimmt `user_version` in die Kopie mit — deshalb erklärt
    jede Sicherung ihr Schema selbst und ist nicht auf ihr Manifest angewiesen."""
    info = _service(volume).create()

    connection = sqlite3.connect(_service(volume).directory / info.name)
    try:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    finally:
        connection.close()


def test_ein_neueres_schema_gilt_als_unpassend(volume: Path) -> None:
    """Der Befund unterscheidet sich von „andere Quellenlage" und sagt es auch.

    Der Grund wird hier nur **gemeldet**; was daraus folgt, entscheidet die
    zweite Teilstrecke.
    """
    service = _service(volume)
    info = service.create()
    connection = sqlite3.connect(service.directory / info.name)
    try:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        connection.commit()
    finally:
        connection.close()

    entry = service.list()[0]

    assert entry.compatible is False
    assert "Schema" in entry.reason and str(SCHEMA_VERSION + 1) in entry.reason


# ─── #1 · die Sicherung während des Schreibens ────────────────────────────────


def test_eine_sicherung_entsteht_waehrend_geschrieben_wird(volume: Path) -> None:
    """**Der Grund für `VACUUM INTO` statt einer Dateikopie.**

    Der Aufbau ist der Trick: Die Verbindung bleibt **offen**, der
    festgeschriebene Stand liegt damit noch im WAL. Wird sie vorher geschlossen,
    schreibt SQLite das WAL zurück — dann liefert auch eine simple Dateikopie
    das richtige Ergebnis, und der Test unterscheidet nichts mehr.
    """
    writer = get_connection(str(volume / "stockinfo.db"))
    try:
        _insert(writer, "FESTGESCHRIEBEN")
        writer.commit()  # ohne Checkpoint — steht jetzt im WAL
        writer.execute("BEGIN")
        _insert(writer, "SCHWEBEND")  # ohne Commit — darf nirgends auftauchen
        info = _service(volume).create()
    finally:
        writer.rollback()
        writer.close()

    assert _symbols(_service(volume).directory / info.name) == ["FESTGESCHRIEBEN"]


def test_die_sicherung_traegt_kennung_und_manifest(volume: Path) -> None:
    """Datei **und** Manifest nennen dieselbe Kennung — deshalb fällt ein
    vertauschtes Manifest auf, und eine Datei ohne bleibt zuordenbar."""
    info = _service(volume).create()
    manifest = json.loads(
        (_service(volume).directory / info.name).with_suffix(".json").read_text("utf-8")
    )

    assert info.fingerprint == fingerprint_of(_ONLINE)
    assert manifest["sources_fingerprint"] == info.fingerprint
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["sources"]["quotes"] == ["yfinance"]
    assert info.name.endswith(f"-{info.fingerprint}.db")
    assert info.created_at.endswith("Z")


def test_zwei_sicherungen_kurz_nacheinander_kollidieren_nicht(volume: Path) -> None:
    """`VACUUM INTO` schreibt in keine bestehende Datei.

    Zugesagt ist die **Abwesenheit einer Kollision**, nicht der
    Millisekundenstempel als Mittel: Auch mit Sekundenauflösung rückt
    `_free_name` vor, bis die Sekunde umspringt — langsam, aber kollisionsfrei.
    """
    service = _service(volume)

    names = {service.create().name for _ in range(3)}

    assert len(names) == 3
    assert len(list(service.directory.glob("stockinfo-*.db"))) == 3


# ─── Die Kennung ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("other", "same"),
    [
        pytest.param(_FILE_ONLY, False, id="andere-ketten"),
        pytest.param(
            SourcesConfig(chains={**_ONLINE.chains, "resolvers": ("yahoo-search", "openfigi")}),
            False,
            id="andere-reihenfolge",
        ),
        pytest.param(
            SourcesConfig(chains=_ONLINE.chains, packages=("stockinfo-source-x==0.1.0",)),
            False,
            id="beigesteuertes-paket",
        ),
        pytest.param(
            SourcesConfig(chains=_ONLINE.chains, providers={"openfigi": {"api_key": "x"}}),
            True,
            id="schluessel-aendert-nichts",
        ),
    ],
)
def test_woraus_die_kennung_entsteht(other: SourcesConfig, same: bool) -> None:
    """Ketten **in Reihenfolge** und Paketpins zählen; Geheimnisse nicht.

    Der letzte Fall ist die Gegenprobe zur Entscheidung im Scope-Vertrag: Ob
    `openfigi` gerade einen Schlüssel hat, ist Erreichbarkeit, keine
    Plugin-Variante. Ginge er ein, wäre jede gestrige Sicherung über Nacht
    „fremd".
    """
    assert (fingerprint_of(other) == fingerprint_of(_ONLINE)) is same


# ─── #10 · die Rotation ───────────────────────────────────────────────────────


def test_die_elfte_sicherung_verdraengt_die_aelteste(volume: Path) -> None:
    """Zehn bleiben liegen — und das Manifest geht mit.

    Bliebe es zurück, sammelte das Verzeichnis Manifeste ohne Datenbank.
    """
    service = _service(volume)
    aged = [
        _age(service.directory / service.create().name, index)
        for index in range(KEEP_BACKUPS + 1)
    ]

    remaining = sorted(path.name for path in service.directory.glob("stockinfo-*.db"))

    assert len(remaining) == KEEP_BACKUPS
    assert aged[0].name not in remaining, "die älteste liegt noch da"
    assert not aged[0].with_suffix(".json").exists(), "ihr Manifest blieb zurück"


# ─── #2 · die Liste ───────────────────────────────────────────────────────────


def test_die_liste_zeigt_auch_die_unpassenden_mit_ihrem_grund(volume: Path) -> None:
    """„Kennung verschieden" ist wahr und nutzlos — wer die Meldung liest,
    will wissen, was anders steht."""
    info = _service(volume).create()

    entries = _service(volume, _FILE_ONLY).list()

    assert [entry.name for entry in entries] == [info.name]
    assert entries[0].compatible is False
    difference = entries[0].reason
    assert "quotes" in difference and "yfinance" in difference and "yaml-file" in difference
    assert entries[0].size > 0


def test_die_juengste_steht_vorn(volume: Path) -> None:
    """Wer eine Sicherung sucht, sucht meist die letzte."""
    service = _service(volume)
    first = service.create()
    _age(service.directory / first.name, 0)
    second = service.create()

    assert [entry.name for entry in service.list()][0] == second.name


def test_eine_sicherung_ohne_manifest_bleibt_zuordenbar(volume: Path) -> None:
    """**Deshalb steht die Kennung auch in der Datenbank.**

    Ohne den Stempel wäre eine Datei ohne Manifest namenlos, und die Liste
    müsste sie als unpassend ausgeben, obwohl sie passt.
    """
    service = _service(volume)
    info = service.create()
    (service.directory / info.name).with_suffix(".json").unlink()

    assert service.list()[0].fingerprint == fingerprint_of(_ONLINE)
    assert service.list()[0].compatible is True


# ─── Der veröffentlichte Weg ──────────────────────────────────────────────────


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Die App auf einem frischen Volume — als Kontextmanager, damit der
    Lifespan läuft: Dort entsteht das Schema und der Stempel."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "stockinfo.db"))
    caches = (get_settings, get_sources_config, get_backup_service)
    for cache in caches:
        cache.cache_clear()
    with TestClient(app) as opened:
        yield opened
    for cache in caches:
        cache.cache_clear()


def test_der_weg_ueber_http_von_der_leeren_liste_bis_zum_eintrag(
    client: TestClient, tmp_path: Path
) -> None:
    """Anlegen und listen über die veröffentlichte Form.

    Die leere Liste nennt trotzdem die Kennung der Instanz: Ohne sie wäre sie
    stumm, und wer eine Sicherung von anderswo hereinlegt, sähe nicht, ob sie
    hierher passt. Und die Liste kommt aus dem **Verzeichnis**, nicht aus einem
    Gedächtnis — sonst stimmte sie bis zum ersten Neustart.
    """
    empty = client.get("/backups").json()
    assert empty["backups"] == [] and len(empty["fingerprint"]) == 12

    created = client.post("/backups")
    assert created.status_code == 201, created.text
    name = created.json()["name"]

    listed = client.get("/backups").json()
    assert [item["name"] for item in listed["backups"]] == [name]
    assert listed["backups"][0]["compatible"] is True
    assert listed["backups"][0]["size"] > 0
    assert listed["backups"][0]["created_at"].endswith("Z")
    assert {item["name"] for item in listed["backups"]} == {
        path.name for path in (tmp_path / "backups").glob("stockinfo-*.db")
    }


def test_es_gibt_keinen_zweiten_loeschweg(client: TestClient) -> None:
    """Kein `DELETE` — die elfte Sicherung verdrängt die älteste, und das
    genügt. Ein zweiter Löschweg wäre nur eine zweite Gelegenheit, die falsche
    Datei zu treffen."""
    paths = client.get("/openapi.json").json()["paths"]

    assert not any(
        "delete" in methods for route, methods in paths.items() if route.startswith("/backups")
    )


def test_gleichzeitige_aufrufe_bekommen_je_eine_eigene_sicherung(
    client: TestClient, tmp_path: Path
) -> None:
    """**Zwanzig Aufrufe zugleich — am HTTP-Eintritt, nicht im Dienst.**

    `_free_name()` prüft, ob ein Pfad frei ist; zwischen dieser Prüfung und dem
    `VACUUM INTO` kann ein zweiter Handler denselben Namen wählen. Der Test
    unterscheidet die serialisierte Folge von diesem Wettlauf.

    Ein sequenzieller Lauf ersetzt das nicht: Er erzeugt den Wettlauf gar
    nicht. Geprüft wird deshalb dreierlei — jede Antwort ist ein `201`, danach
    liegen genau zehn Paare aus Datenbank und Manifest, und kein
    Zwischenprodukt bleibt zurück.
    """
    with ThreadPoolExecutor(max_workers=20) as pool:
        responses = [pool.submit(client.post, "/backups") for _ in range(20)]
        codes = [future.result().status_code for future in responses]

    directory = tmp_path / "backups"
    assert codes == [201] * 20, f"nicht jeder Aufruf kam durch: {Counter(codes)}"
    assert len(list(directory.glob("stockinfo-*.db"))) == KEEP_BACKUPS
    assert len(list(directory.glob("stockinfo-*.json"))) == KEEP_BACKUPS
    assert list(directory.glob("*.tmp")) == [], "ein Zwischenprodukt blieb liegen"
