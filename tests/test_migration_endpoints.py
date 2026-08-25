"""Der Pflichtablauf über HTTP (T-21 2A, `#2b5`, `#2b6`, `#2b6b`, `#2b6e`, `#2b6f`).

Der Unterschied zu `test_migration_guard.py` ist der ganze Zweck dieser Datei:
Dort steht die **Regel**, hier läuft sie durch die echte App. Eine Allowlist,
die nur gegen sich selbst geprüft wird, belegt nicht, dass der Guard sie auch
anwendet — und der Routentabellen-Test fordert deshalb jeden Pfad wirklich an.

Für die statischen Pfade gilt dasselbe eine Stück strenger: Der Test
**enumeriert das gebaute Dashboard**, nicht die Konstante. Genau das hätte die
fehlende `stockinfo-icon.svg` gefunden, die im früheren Entwurf in einer
handgepflegten Liste fehlte.
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.container import get_cached_quote_service
from app.main import app, mount_dashboard
from app.migration_guard import ALLOWED_ROUTES, HEALTHCHECK_PATH
from app.routers.migration import get_gate

_DIST = "dashboard/dist"


def _legacy_database(path: str, rows: list[tuple[str, str | None]]) -> None:
    """Eine Datenbank im Stand **vor** T-21 — der Fall, der den Riegel auslöst."""
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isin TEXT UNIQUE, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                first_seen TEXT NOT NULL
            );
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL REFERENCES instruments(id),
                price REAL NOT NULL, quote_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL, UNIQUE (instrument_id, quote_time)
            );
            CREATE TABLE daily_closes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL REFERENCES instruments(id),
                date TEXT NOT NULL, close REAL NOT NULL,
                UNIQUE (instrument_id, date)
            );
            """
        )
        connection.executemany(
            "INSERT INTO instruments (symbol, isin, name, first_seen) "
            "VALUES (?, ?, ?, ?)",
            [(symbol, isin, f"Papier {symbol}", "2026-01-01T00:00:00+00:00")
             for symbol, isin in rows],
        )


def _mit_eigener_datenbank(monkeypatch, db_path: str) -> None:
    """Richtet die App auf eine **eigene** Datenbank aus — auch im Lifespan.

    **`dependency_overrides` genügt hier nicht.** Es greift nur für
    Route-Dependencies; Lifespan und Guard-Middleware rufen `get_settings()`
    direkt auf. Beim ersten Anlauf dieser Datei stand deshalb im Startlog
    `database_path=data/stockinfo.db` — der Test lief gegen den echten
    Bestand. Geschadet hat es nichts, weil `init_db` auf diesem Stand zufällig
    nichts zu schreiben hatte; verlassen darf man sich darauf nicht.

    Gesetzt wird deshalb die Umgebung und der Settings-Cache geleert. Damit
    sieht **jeder** Aufrufer denselben Wert, egal über welchen Weg er fragt.
    """
    monkeypatch.setenv("DATABASE_PATH", db_path)
    monkeypatch.setenv("STATIC_DIR", _DIST)

    # Beide Zwischenspeicher leeren, sonst hält der Container einen Dienst auf
    # die alte Datei — `/ready` und `/operational` fragten dann die falsche.
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


@contextmanager
def _gemountetes_dashboard() -> Iterator[None]:
    """Hängt das gebaute Dashboard an ``/`` — wie im Image.

    `app/main.py` mountet beim **Import**, und die Vorgabe zeigt auf den
    Container-Pfad `/app/web`, den es lokal nicht gibt. Ohne diesen Griff wäre
    im Test nichts gemountet: `GET /` käme als `404` zurück statt als
    Dashboard, und der Test belegte die statische Freigabe nicht — er
    verwechselte „gesperrt" mit „gar nicht da".

    Die Route wird danach wieder entfernt; `app` ist ein Modul-Singleton, und
    ein Mount auf `/` würde jeden folgenden Test überschatten.
    """
    mount_dashboard(app, _DIST)
    try:
        yield
    finally:
        app.router.routes = [
            route for route in app.router.routes
            if getattr(route, "name", None) != "dashboard"
        ]


@pytest.fixture
def pending(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    """Eine App im **Pending-Zustand**, über den echten Lifespan.

    `TestClient` als Kontextmanager, damit der Lifespan wirklich läuft — nur
    dann entsteht der Riegel so, wie er im Betrieb entsteht. Ihn von Hand zu
    setzen prüfte den Guard, aber nicht den Start.
    """
    db_path = str(tmp_path / "pending.db")
    _legacy_database(
        db_path,
        [("EUNL.DE", "IE00B4L5Y983"), ("VTI", "US9229087690")],
    )
    _mit_eigener_datenbank(monkeypatch, db_path)

    with _gemountetes_dashboard(), TestClient(app) as client:
        assert client.get("/migration").json()["pending"] is True
        yield client

    get_gate().confirm()  # Riegel für die nächsten Tests zurücksetzen
    get_settings.cache_clear()


@pytest.fixture
def serving(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    """Eine App im Normalbetrieb — frische Datenbank, nichts steht aus."""
    db_path = str(tmp_path / "serving.db")
    _mit_eigener_datenbank(monkeypatch, db_path)

    with TestClient(app) as client:
        yield client

    get_settings.cache_clear()


def test_der_start_erkennt_den_ausstehenden_umzug(pending: TestClient) -> None:
    """`#2b5`: Erkennen, nicht ausführen — und **nichts** verändern.

    Der Lifespan ist durchgelaufen. Wäre hier migriert worden, stünde `VTI`
    nicht mehr in der Vorschau, sondern im Bericht.
    """
    body = pending.get("/migration").json()

    assert body["pending"] is True
    assert [entry["symbol"] for entry in body["rejected"]] == ["VTI"]
    assert body["migrating"] == 1
    assert pending.get("/migration/report").json() == {
        "completed": False,
        "rejected": [],
    }


@pytest.mark.parametrize(("method", "path"), sorted(ALLOWED_ROUTES))
def test_jeder_erlaubte_pfad_antwortet_auch_wirklich(
    pending: TestClient, method: str, path: str
) -> None:
    """Der Routentabellen-Test zählt **aus der Allowlist** auf.

    Sie hier abzuschreiben hieße, zwei Listen zu pflegen; der Test bestätigte
    dann seine eigene Kopie. Geprüft wird, dass der Guard nicht dazwischengeht
    — `503` mit der stabilen Kennung wäre der Fehlerfall.

    `/migration/confirm` ist ausgenommen: Er *führt aus*, und ein Test, der
    ihn nebenbei aufriefe, zöge dem Rest der Datei den Boden weg.
    """
    if path == "/migration/confirm":
        pytest.skip("führt aus — eigener Test weiter unten")

    response = pending.request(method, path)

    assert response.status_code != 503 or response.json().get("detail") != (
        "migration_pending"
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/quote/IE00B4L5Y983"),
        ("GET", "/quote?symbol=EUNL.DE"),
        ("GET", "/instruments"),
        ("GET", "/exchanges"),
        ("POST", "/refresh"),
        ("DELETE", "/instruments/1"),
    ],
    ids=["quote_isin", "quote_symbol", "instruments", "exchanges", "refresh", "delete"],
)
def test_lese_und_schreibwege_bleiben_gesperrt(
    pending: TestClient, method: str, path: str
) -> None:
    """`#2b6`: Auch **Lese**wege bleiben zu, nicht nur Schreibwege.

    Eine eingeschränkte Oberfläche hindert weder ein `curl` noch einen alten
    offenen Browser-Tab. Und `/quote` schreibt: Es legt Instrumente an und
    aktualisiert sie — danach stimmte die vorgerechnete Auswirkung nicht mehr.
    """
    response = pending.request(method, path)

    assert response.status_code == 503
    assert response.json()["detail"] == "migration_pending"


def test_die_gesperrten_wege_lassen_die_datenbank_in_ruhe(pending: TestClient) -> None:
    """Abgewiesen heißt abgewiesen — nicht „abgewiesen, aber schon geschrieben".

    Die Vorschau vorher und nachher muss dieselbe sein, sonst hätte der
    gesperrte Request doch etwas verändert.
    """
    vorher = pending.get("/migration").json()

    pending.get("/quote", params={"symbol": "NEU.DE"})
    pending.post("/refresh")

    assert pending.get("/migration").json() == vorher


def test_ready_und_operational_beantworten_verschiedene_fragen(
    pending: TestClient,
) -> None:
    """`#2b6b` und `#2b6e`: drei Zustände, drei Aussagen.

    `/ready` sagt `503` — der Fachbetrieb ist nicht freigegeben, und das ist
    keine Schätzung, sondern beobachtbar: Der Guard weist die Fachwege ab.
    `/operational` sagt `200`, denn der Prozess tut genau das, was er tun
    soll. Beides mit `200` zu beantworten wäre eine Lüge an jeden Consumer,
    der Readiness am Statuscode bewertet.
    """
    ready = pending.get("/ready")
    operational = pending.get(HEALTHCHECK_PATH)

    assert (ready.status_code, ready.json()["status"]) == (503, "migration_pending")
    assert (operational.status_code, operational.json()["mode"]) == (
        200,
        "migration_pending",
    )
    assert pending.get("/health").status_code == 200


def test_im_normalbetrieb_sagen_beide_ja(serving: TestClient) -> None:
    """Die Gegenprobe — sonst bewiese der Test oben nur, dass etwas `503` sagt."""
    assert serving.get("/ready").json()["status"] == "ok"
    assert serving.get(HEALTHCHECK_PATH).json()["mode"] == "serving"
    assert serving.get("/exchanges").status_code == 200


def test_die_bestaetigung_fuehrt_aus_und_gibt_frei(pending: TestClient) -> None:
    """Phase 2: Erst die Bestätigung löst den Umzug aus.

    Danach ist der Fachbetrieb offen, und der Bericht nennt, was gegangen ist
    — mit Symbol und Grund, nicht nur mit einer Zahl.
    """
    bericht = pending.post("/migration/confirm")

    assert bericht.status_code == 200
    assert [entry["symbol"] for entry in bericht.json()["rejected"]] == ["VTI"]

    assert pending.get("/ready").json()["status"] == "ok"
    assert pending.get(HEALTHCHECK_PATH).json()["mode"] == "serving"
    assert pending.get("/exchanges").status_code == 200

    nachher = pending.get("/migration/report").json()
    assert nachher["completed"] is True
    assert nachher["rejected"][0]["reason"] == "symbol_without_exchange_suffix"


def test_eine_zweite_bestaetigung_laeuft_ins_leere(pending: TestClient) -> None:
    """`#2b6d`: Freigegeben wird **genau einmal**.

    Ein zweiter Aufruf darf den Ablauf nicht erneut auslösen — er fände einen
    bereits umgezogenen Bestand vor und schriebe einen zweiten Bericht.
    """
    assert pending.post("/migration/confirm").status_code == 200

    zweite = pending.post("/migration/confirm")

    assert zweite.status_code == 409
    assert len(pending.get("/migration/report").json()["rejected"]) == 1


@pytest.mark.skipif(
    not os.path.isdir(_DIST), reason="Dashboard nicht gebaut — `make build` fehlt"
)
def test_die_oberflaeche_bleibt_im_pending_zustand_erreichbar(
    pending: TestClient,
) -> None:
    """`#2b6h`/`#2b6j`: Der Test enumeriert die **Wirklichkeit**.

    Angefordert wird jede real ausgelieferte Datei — rekursiv, also auch die
    Dateien unter `/assets` — und ausdrücklich **`GET /`**. Letzteres ist
    keine Datei, sondern ein URL-Alias von `StaticFiles(html=True)`; eine rein
    aus dem Dateiinventar abgeleitete Allowlist hätte ausgerechnet die
    Adresse gesperrt, über die das Dashboard geöffnet wird.

    Ein Test, der stattdessen die Konstante durchginge, hätte weder das
    gefunden noch die fehlende `stockinfo-icon.svg` des früheren Entwurfs.
    """
    startseite = pending.get("/")
    assert startseite.status_code == 200
    assert "<!doctype html" in startseite.text.lower()

    gesperrt = []
    for directory, _, filenames in os.walk(_DIST):
        for filename in filenames:
            pfad = "/" + os.path.relpath(os.path.join(directory, filename), _DIST)
            if pending.get(pfad).status_code == 503:
                gesperrt.append(pfad)

    assert gesperrt == []
    assert pending.get("/stockinfo-icon.svg").status_code == 200


def test_ein_unbekannter_pfad_bleibt_gesperrt(pending: TestClient) -> None:
    """Die Gegenprobe zur Oberfläche: freigegeben ist, was **existiert**."""
    assert pending.get("/gibt-es-nicht.js").status_code == 503


def test_der_dockerfile_zeigt_auf_denselben_pfad() -> None:
    """`#2b6f`: Eine Routenquelle, drei Verbraucher.

    Der Dockerfile kann kein Python importieren, also kann er die Konstante
    nicht teilen. Was er kann, ist geprüft werden — sonst driften Guard und
    `HEALTHCHECK` beim nächsten Umbenennen auseinander, und zwar unbemerkt bis
    zum Deployment.
    """
    dockerfile = Path("docker/Dockerfile").read_text(encoding="utf-8")
    healthcheck = [
        line for line in dockerfile.splitlines() if "curl" in line and "localhost" in line
    ]

    assert len(healthcheck) == 1, "genau eine HEALTHCHECK-Zeile erwartet"
    assert f"{HEALTHCHECK_PATH}\"" in healthcheck[0], healthcheck[0]
