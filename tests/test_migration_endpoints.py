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
import threading
import time
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
from app.scheduler import RefreshScheduler

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
        # **Nichtleere, unterschiedliche Werte** für Börse, Gattung und
        # Währung. Bis Runde 31 blieben sie `NULL`, und der Metadatentest
        # verglich Vorschau und Bericht dann als `None == None` — er hätte
        # grün bleiben können, während beide Abbildungen die Felder weglassen.
        connection.executemany(
            "INSERT INTO instruments "
            "(symbol, isin, name, exchange, type, currency, first_seen) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    symbol,
                    isin,
                    f"Papier {symbol}",
                    f"Börse {symbol}",
                    "etf" if symbol.endswith(".DE") else "stock",
                    "EUR" if symbol.endswith(".DE") else "USD",
                    "2026-01-01T00:00:00+00:00",
                )
                for symbol, isin in rows
            ],
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

    # Der Riegel ist Modulzustand; bliebe er zu, bekämen alle folgenden Tests
    # `503`. Genau das ist beim ersten Anlauf passiert — `test_overrides.py`
    # war plötzlich rot, obwohl es allein grün lief.
    get_gate().release()
    get_gate().on_release(None)
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


@pytest.fixture
def serving(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    """Eine App im Normalbetrieb — frische Datenbank, nichts steht aus."""
    db_path = str(tmp_path / "serving.db")
    _mit_eigener_datenbank(monkeypatch, db_path)

    with TestClient(app) as client:
        yield client

    get_gate().on_release(None)
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


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


# Was jeder erlaubte Pfad im Pending-Zustand **konkret** antworten muss.
#
# Bis Runde 30 verlangte der Test nur „nicht `503`/`migration_pending`". Ein
# Pfad, der in der Allowlist steht, den es im Router aber gar nicht gibt,
# antwortet `404` — und bestand. Die Allowlist hätte gegen den Router driften
# können, ohne dass etwas rot wird; genau davor sollte `#2b6f` schützen.
#
# `/migration/confirm` fehlt hier bewusst: Er **führt aus**. Ein Test, der ihn
# nebenbei aufriefe, zöge dem Rest der Datei den Boden weg — er hat weiter
# unten einen eigenen, echten Integrationstest.
_ERWARTETE_ANTWORTEN = {
    ("GET", "/health"): 200,
    ("GET", HEALTHCHECK_PATH): 200,
    ("GET", "/ready"): 503,  # ehrlich: der Fachbetrieb ist gesperrt
    ("GET", "/migration"): 200,
    ("GET", "/migration/report"): 200,
}


def test_die_erwartungstabelle_deckt_die_allowlist_ab() -> None:
    """Der Test über den Test: keine Zeile darf stillschweigend fehlen.

    Ohne diese Prüfung wäre die Tabelle oben eine **zweite** Liste, die beim
    nächsten neuen Pfad zurückbleibt — und die Lücke fiele niemandem auf,
    weil ein nicht aufgezählter Pfad einfach nicht geprüft würde.
    """
    covered = set(_ERWARTETE_ANTWORTEN) | {("POST", "/migration/confirm")}

    assert covered == set(ALLOWED_ROUTES)


@pytest.mark.parametrize(
    ("method", "path", "expected"),
    [(m, p, code) for (m, p), code in sorted(_ERWARTETE_ANTWORTEN.items())],
)
def test_jeder_erlaubte_pfad_antwortet_auch_wirklich(
    pending: TestClient, method: str, path: str, expected: int
) -> None:
    """Jeder Allowlist-Eintrag mit seinem **konkreten** Status.

    Ein `404` ist damit rot: Er hieße, dass die Allowlist einen Pfad freigibt,
    den es nicht gibt — und dass Guard und Router auseinandergelaufen sind.
    """
    response = pending.request(method, path)

    assert response.status_code == expected
    assert response.headers["content-type"].startswith("application/json")


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
    """`#2b6b` und `#2b6e`: drei **Fragen**, drei Aussagen.

    „Zustände" hieß es hier bis Runde 34, und das Wort trägt seit dem
    `GateState`-Enum eine andere Bedeutung. Gemeint sind die drei Endpunkte,
    nicht die fünf Lagen des Riegels.

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
    report = pending.post("/migration/confirm")

    assert report.status_code == 200
    assert [entry["symbol"] for entry in report.json()["rejected"]] == ["VTI"]

    assert pending.get("/ready").json()["status"] == "ok"
    assert pending.get(HEALTHCHECK_PATH).json()["mode"] == "serving"
    assert pending.get("/exchanges").status_code == 200

    nachher = pending.get("/migration/report").json()
    assert nachher["completed"] is True
    assert nachher["rejected"][0]["reason"] == "symbol_without_exchange_suffix"


def test_vorschau_und_bericht_nennen_genug_zur_neuerfassung(
    pending: TestClient,
) -> None:
    """Geprüft wird die **HTTP-Antwort**, nicht die interne Tabelle.

    Bis Runde 30 hielt die Tabelle Name, Börse, Gattung und Währung — und
    keines davon kam über REST an: Das Modell kannte nur `name`, und die
    Übersetzung setzte nicht einmal den. Das UI in 2B hätte den Benutzer
    auffordern sollen, ein Papier neu zu erfassen, und ihm dazu nur ein Symbol
    nennen können.

    Der Test läuft **vor und nach** der Löschung, weil beide Wege verschiedene
    Quellen haben: die Vorschau den Plan, der Bericht die Tabelle. Nur einen
    zu prüfen ließe den anderen driften.

    **Verglichen wird gegen ausgeschriebene Werte, nicht miteinander.** Bis
    Runde 31 stellte der Test Vorschau und Bericht gegenüber — und weil die
    Fixture `exchange`, `type` und `currency` leer ließ, war das `None ==
    None`. Beide Abbildungen hätten die drei Felder weglassen können, und der
    Test wäre grün geblieben.
    """
    expected = {
        "symbol": "VTI",
        "isin": "US9229087690",
        "name": "Papier VTI",
        "exchange": "Börse VTI",
        "type": "stock",
        "currency": "USD",
        "reason": "symbol_without_exchange_suffix",
    }

    preview = pending.get("/migration").json()["rejected"][0]
    assert {field: preview[field] for field in expected} == expected

    pending.post("/migration/confirm")
    report = pending.get("/migration/report").json()["rejected"][0]

    assert {field: report[field] for field in expected} == expected


def test_die_bestaetigung_startet_den_scheduler(pending: TestClient) -> None:
    """`#2b6d`: Scheduler **und** Endpunkte werden freigegeben, genau einmal.

    Der Scheduler läuft im Lifespan an — und der ist längst durch, wenn der
    Benutzer bestätigt. Ohne einen eigenen Weg liefe der Hintergrund-Refresh
    bis zum nächsten Neustart nicht: Der Dienst sähe gesund aus, `/ready`
    sagte `ok`, und trotzdem käme kein einziger neuer Kurs. Genau die Sorte
    Fehler, die niemand bemerkt, bis die Kurse zu alt sind.

    Geprüft wird der Rückruf, nicht nur die Endpunktfreigabe — sonst bliebe
    die Hälfte der Zusage ungeprüft.
    """
    gestartet: list[str] = []
    get_gate().on_release(lambda: gestartet.append("scheduler"))

    assert pending.post("/migration/confirm").status_code == 200

    assert gestartet == ["scheduler"]

    # Und **nicht** ein zweites Mal.
    pending.post("/migration/confirm")
    assert gestartet == ["scheduler"]


def test_ein_gescheiterter_scheduler_start_meldet_keinen_normalbetrieb(
    tmp_path: Path, monkeypatch
) -> None:
    """`#2b6d`: „Scheduler **und** Endpunkte" — die Kopplung, ernst genommen.

    **Der Befund aus Runde 31.** Vorher schluckte `release()` jeden
    Rückruffehler: Die Bestätigung antwortete `200`, `/ready` sagte `ok`, der
    Riegel war offen — und kein Scheduler lief. Der Dienst meldete gesund und
    lieferte normal aus, während seine Kurse unbemerkt veralteten. Genau der
    betriebliche Fehler, den Runde 30 abstellen sollte, eine Ebene höher.

    **Der Test fährt den echten Weg.** Der vorige ersetzte den Rückruf durch
    ein `lambda` und belegte damit nur, dass ein Callback gerufen wird — nicht,
    dass der *Scheduler* startet. Hier scheitert `RefreshScheduler.start`
    selbst, und der Lifespan-Rückruf läuft bis dorthin durch.

    Der Umzug wird dabei **nicht** zurückgenommen: Er ist festgeschrieben, und
    ihn als ungeschehen auszugeben wäre die entgegengesetzte Lüge.
    """
    db_path = str(tmp_path / "kaputter-start.db")
    _legacy_database(db_path, [("EUNL.DE", "IE00B4L5Y983"), ("VTI", None)])
    _mit_eigener_datenbank(monkeypatch, db_path)

    attempts: list[int] = []
    real_start = RefreshScheduler.start

    def start_fails(self) -> None:
        attempts.append(1)
        raise RuntimeError("Scheduler startet nicht")

    monkeypatch.setattr(RefreshScheduler, "start", start_fails)

    with TestClient(app) as client:
        response = client.post("/migration/confirm")

        assert response.status_code == 503
        assert response.json()["detail"] == "startup_failed"
        assert attempts == [1], "der echte Scheduler wurde versucht"

        # Der Umzug **ist** durch — das darf niemand bestreiten.
        assert client.get("/migration").json()["pending"] is False
        assert client.get("/migration/report").json()["completed"] is True

        # Aber bereit ist der Dienst nicht, und beide Diagnosewege sagen es.
        ready = client.get("/ready")
        operational = client.get(HEALTHCHECK_PATH)
        assert (ready.status_code, ready.json()["status"]) == (503, "degraded")
        assert (operational.status_code, operational.json()["mode"]) == (
            503,
            "degraded",
        )

        # Und der Zustand ist **anstoßbar**: Ist der Grund behoben, genügt
        # eine weitere Bestätigung — kein Neustart nötig. Wiederhergestellt
        # wird der **echte** Start, nicht ein No-op: Sonst liefe der
        # Wiederholungsweg wieder gegen eine Attrappe, und der Lifespan
        # fände beim Herunterfahren einen Scheduler vor, der nie lief.
        monkeypatch.setattr(RefreshScheduler, "start", real_start)
        assert client.post("/migration/confirm").status_code == 200
        assert client.get("/ready").json()["status"] == "ok"
        assert client.get(HEALTHCHECK_PATH).json()["mode"] == "serving"

    get_gate().on_release(None)
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


def test_parallele_wiederholungen_starten_genau_einen_scheduler(
    tmp_path: Path, monkeypatch
) -> None:
    """`#2b6d`: Auch der **Wiederholungsweg** wird atomar beansprucht.

    **Der Befund aus Runde 32.** Der erste Umzug war mit `claim()` gegen
    Parallelität verriegelt, der neue Wiederholungsweg umging diesen Anspruch
    vollständig: `retry_release()` rief den Rückruf ohne jeden
    Zustandswechsel. Acht gleichzeitige zweite Bestätigungen sahen deshalb
    alle `startup_failed`, liefen alle in denselben Rückruf und starteten acht
    Scheduler. Ein zweiter Scheduler ist still — er refreshte parallel und
    fiele niemandem auf.

    **Deterministisch, nicht hoffnungsvoll.** Eine Barriere schickt alle acht
    Threads gemeinsam los, und der gezählte Start hält das Fenster offen,
    solange die übrigen ankommen. Die Erwartung hängt danach an keiner
    Zeitfrage mehr: Genau ein Aufrufer gewinnt den Übergang, die übrigen
    finden weder einen Umzug noch einen zu wiederholenden Start und bekommen
    `409` — gleichgültig, ob sie während oder nach dem Start eintreffen.

    Gestartet wird der **echte** Scheduler. Ein Zähler allein belegte nur,
    dass ein Rückruf lief; hier läuft der Lifespan-Rückruf bis in
    `RefreshScheduler.start()` durch.
    """
    db_path = str(tmp_path / "parallele-wiederholung.db")
    # `VTI` ohne ISIN ist nicht auflösbar und wird abgelehnt. **Genau das**
    # macht den Umzug bestätigungspflichtig: Ein rein verlustloser Bestand
    # wandert schon in `init_db` durch, und der Riegel fiele nie.
    _legacy_database(db_path, [("EUNL.DE", "IE00B4L5Y983"), ("VTI", None)])
    _mit_eigener_datenbank(monkeypatch, db_path)

    real_start = RefreshScheduler.start

    def start_fails(self) -> None:
        raise RuntimeError("Scheduler startet nicht")

    monkeypatch.setattr(RefreshScheduler, "start", start_fails)

    with TestClient(app) as client:
        assert client.post("/migration/confirm").status_code == 503
        assert get_gate().startup_failed is True, "der Ausgangszustand des Tests"

        starts: list[str] = []
        starts_sperre = threading.Lock()

        def start_zaehlt_und_haelt(self) -> None:
            with starts_sperre:
                starts.append("scheduler")
            # Das Fenster offen halten, damit die übrigen Aufrufer wirklich
            # *währenddessen* ankommen und nicht erst danach.
            time.sleep(0.05)
            real_start(self)

        monkeypatch.setattr(RefreshScheduler, "start", start_zaehlt_und_haelt)

        parallel = 8
        an_der_linie = threading.Barrier(parallel)
        codes: list[int] = []
        codes_sperre = threading.Lock()

        def bestaetigen() -> None:
            an_der_linie.wait(timeout=10)
            code = client.post("/migration/confirm").status_code
            with codes_sperre:
                codes.append(code)

        threads = [threading.Thread(target=bestaetigen) for _ in range(parallel)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        assert not any(thread.is_alive() for thread in threads), "ein Thread hängt"
        assert starts == ["scheduler"], f"{len(starts)} Scheduler statt einem"
        assert sorted(codes) == [200] + [409] * (parallel - 1), (
            "genau eine Wiederholung führt aus, der Rest bekommt 409"
        )

        # Und danach steht der Betrieb wirklich.
        assert client.get("/ready").json()["status"] == "ok"
        assert client.get(HEALTHCHECK_PATH).json()["mode"] == "serving"

    get_gate().on_release(None)
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


def test_waehrend_der_start_laeuft_meldet_niemand_normalbetrieb(
    tmp_path: Path, monkeypatch
) -> None:
    """`#2b6b`, `#2b6e`: Zwischen Commit und Scheduler gibt es kein `ok`.

    **Der zweite Befund aus Runde 32.** `release()` setzte den Riegel auf
    offen und rief *danach* den Rückruf; `startup_failed` entstand erst im
    `except`. Dazwischen existierte die Kombination „nicht ausstehend, nicht
    gescheitert" — also `200/ok` und `200/serving`, obwohl
    `RefreshScheduler.start()` noch gar nicht zurückgekehrt war. Bei einem
    langsamen Start war das ein kurzes Fenster, bei einem hängenden ein
    dauerhafter Zustand.

    **Der Test hält den Start an.** Der Rückruf blockiert mitten in
    `RefreshScheduler.start()`, und währenddessen werden beide Diagnosewege
    gefragt — nicht danach. Das ist der Unterschied zu einem Test, der nur
    Anfang und Ende sieht: Die Falschaussage lebte ausschließlich in der Mitte.
    """
    db_path = str(tmp_path / "haengender-start.db")
    # Siehe oben: Ohne eine abzulehnende Zeile ist der Umzug verlustlos und
    # läuft schon in `init_db` durch — dann gäbe es keine Bestätigung.
    _legacy_database(db_path, [("EUNL.DE", "IE00B4L5Y983"), ("VTI", None)])
    _mit_eigener_datenbank(monkeypatch, db_path)

    real_start = RefreshScheduler.start
    im_start = threading.Event()
    weiter = threading.Event()

    def start_haelt_an(self) -> None:
        im_start.set()
        assert weiter.wait(timeout=20), "der Test hat den Start nie freigegeben"
        real_start(self)

    monkeypatch.setattr(RefreshScheduler, "start", start_haelt_an)

    with TestClient(app) as client:
        codes: list[int] = []
        bestaetigung = threading.Thread(
            target=lambda: codes.append(client.post("/migration/confirm").status_code)
        )
        bestaetigung.start()

        assert im_start.wait(timeout=20), "der Start wurde nie erreicht"

        # **Hier** stand die Lüge. Der Umzug ist festgeschrieben, der
        # Scheduler läuft noch nicht — und genau das sagen jetzt beide.
        ready = client.get("/ready")
        operational = client.get(HEALTHCHECK_PATH)

        assert (ready.status_code, ready.json()["status"]) == (503, "starting"), (
            "der Fachbetrieb ist nicht freigegeben, solange der Start läuft"
        )
        assert (operational.status_code, operational.json()["mode"]) == (
            200,
            "starting",
        ), "der Prozess tut, was er soll — aber er liefert noch nicht aus"

        # Der Umzug selbst ist durch, und das darf niemand bestreiten.
        assert client.get("/migration").json()["pending"] is False

        # Eine zweite Bestätigung greift währenddessen nicht ein.
        assert client.post("/migration/confirm").status_code == 409

        weiter.set()
        bestaetigung.join(timeout=20)

        assert not bestaetigung.is_alive(), "die Bestätigung hängt"
        assert codes == [200]
        assert client.get("/ready").json()["status"] == "ok"
        assert client.get(HEALTHCHECK_PATH).json()["mode"] == "serving"

    get_gate().on_release(None)
    get_settings.cache_clear()
    get_cached_quote_service.cache_clear()


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
    home = pending.get("/")
    assert home.status_code == 200
    assert "<!doctype html" in home.text.lower()

    blocked = []
    for directory, _, filenames in os.walk(_DIST):
        for filename in filenames:
            pfad = "/" + os.path.relpath(os.path.join(directory, filename), _DIST)
            if pending.get(pfad).status_code == 503:
                blocked.append(pfad)

    assert blocked == []
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
