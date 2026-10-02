"""Vergleicht die API vor und nach der SQL-Umstellung auf einer Kopie des Arbeitsbestands (T-97).

Ablauf:

1. Das Original wird einmal unveränderlich gesichert (`snapshot_read_only`).
   Aus diesem Snapshot entstehen alle Kopien. Die Prüfsummen des Originals
   (samt `-wal`/`-shm`) müssen vorher und nachher gleich sein.
2. Hat der Bestand weniger als 15 Papiere, nimmt der alte Stand die Papiere
   aus `supplement_assets.yaml` in eine Kopie auf; sie ist dann der
   gemeinsame Ausgangszustand beider Stände.
3. Der alte Stand (Standard `de620e9`, letzter Stand vor T-90) und `HEAD`
   laufen als `git archive` je auf eigener Kopie und eigenem Port, unter
   `sandbox-exec` ohne Netz und mit sehr großen TTL-Werten.
4. Beide Instanzen beantworten dieselben Abfragen. Die Antworten werden
   feldweise verglichen; **jeder** Unterschied ist ein Befund. Der alte
   Stand enthält T-88 und T-89 schon, und für T-94 ist keine Umrechnung
   belegt — eine Ausnahmeliste gibt es deshalb nicht.
5. Auf einer eigenen Kopie wird geschrieben (manuelle TER setzen, zurücknehmen,
   ein Papier aktualisieren). Für die Aktualisierung kennt deren Offline-Quelle
   genau dieses Papier mit einem neuen Kurs. Jeder Schritt muss mit 200
   antworten und darf nur die erwarteten Tabellen ändern (`EXPECTED_WRITES`);
   danach muss `/instruments` den neuen Kurs zeigen.
6. W17 in `dashboard/e2e/visual-check.mjs` läuft **sichtbar** auf einer
   weiteren Kopie, mit den Antworten des alten Stands als Erwartung.

Exit-Code 1 bei jedem Befund, bei einem abweichenden Schreibweg, bei rotem
W17 und bei verändertem Original; 0 nur, wenn alles grün ist.

Alles liegt unter `.tmp/t97/<Zeit>/` im Projekt-Root und wird am Ende
gelöscht (`--keep` lässt es zur Fehlersuche stehen). Ausgegeben werden nur
Zahlen, Feldpfade und Tabellennamen, keine Datensätze.

Aufruf aus dem Projekt-Root, bei gestoppter App:
    .venv/bin/python scripts/compare_database_versions.py [--source data/stockinfo.db]
        [--before de620e9] [--no-browser] [--keep]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.persistence.backup_store import copy_database, snapshot_read_only, table_contents  # noqa: E402
from app.persistence.repository import QuoteRepository  # noqa: E402

PYTHON = ROOT / ".venv" / "bin" / "python"
UVICORN = ROOT / ".venv" / "bin" / "uvicorn"

# Netz zu, nur die eigene Maschine erlaubt. Die Gegenprobe in
# `check_network_blocked` belegt die Wirkung je Instanz.
SANDBOX_POLICY = """(version 1)
(allow default)
(deny network-outbound)
(allow network-outbound (remote ip "localhost:*"))
(allow network-outbound (remote unix-socket))
"""

# Jeder gespeicherte Wert gilt als frisch, der Scheduler läuft nicht an.
NO_RELOAD = {
    "CACHE_TTL_HOURS": "1000000",
    "FX_TTL_HOURS": "1000000",
    "METADATA_TTL_DAYS": "100000",
    "REFRESH_INTERVAL_HOURS": "1000000",
}

EMPTY_ASSETS = "version: 1\ninstruments: []\nfx_rates: []\n"
SUPPLEMENT = Path(__file__).with_name("supplement_assets.yaml")
MINIMUM_ASSETS = 15  # Mike, 2026-10-02: „mindestens 15“

# Welche Tabellen jeder Schritt des Schreibwegs ändern darf. Aktualisieren
# (gemessen): ein neuer Kurspunkt samt Zähler, die daraus berechnete
# Volatilität und am Papier Abrufzeit und Quelle der Beschreibung.
EXPECTED_WRITES = {
    "setzen": ["detail_overrides"],
    "zurücksetzen": [],
    "aktualisieren": ["detail_values", "instruments", "quotes", "sqlite_sequence"],
}


def file_hashes(database: Path) -> dict[str, str]:
    """SHA-256 der Datenbank und ihrer WAL-/SHM-Dateien, soweit vorhanden."""
    hashes = {}
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{database}{suffix}")
        if path.exists():
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def extract(revision: str, target: Path) -> Path:
    """Legt einen Stand per `git archive` unter `.tmp/` ab — kein Worktree, keine Edits."""
    target.mkdir()
    archive = subprocess.run(["git", "archive", revision], cwd=ROOT, capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive.stdout, check=True)
    return target


def prepare_data_dir(directory: Path, snapshot: Path, assets_text: str = EMPTY_ASSETS) -> Path:
    """Kopie des Snapshots samt Offline-Quellen; ohne Fachdaten, außer beim Ergänzen."""
    directory.mkdir(parents=True)
    database = directory / "stockinfo.db"
    # `copy_database` nimmt die WAL mit; eine Dateikopie verlor sie (9 statt 16 Papiere).
    copy_database(snapshot, database)
    assets = directory / "assets.yaml"
    assets.write_text(assets_text)
    sources = (ROOT / "examples" / "sources-standalone.yaml").read_text()
    (directory / "sources.yaml").write_text(sources.replace("/data/assets-standalone.yaml", str(assets)))
    return database


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Instance:
    """Eine App-Instanz in der Netz-Sandbox; beendet wird nur dieser Prozess.

    Scheitert der Start, räumt der Konstruktor selbst auf: Die Instanz steht
    dann noch in keiner Aufräumliste, und ein übrig gebliebener Prozess wäre
    eine Nebenwirkung des Prüflaufs.
    """

    def __init__(self, source_dir: Path, database: Path, policy: Path, log: Path) -> None:
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = {**os.environ, **NO_RELOAD, "DATABASE_PATH": str(database)}
        # Jeder Stand nutzt die Plugin-API aus seinem eigenen Archiv.
        env["PYTHONPATH"] = str(source_dir / "plugin_api" / "src")
        self.log = log.open("w")
        self.process = subprocess.Popen(
            ["sandbox-exec", "-f", str(policy), str(UVICORN), "app.main:app",
             "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=source_dir, env=env, stdout=self.log, stderr=subprocess.STDOUT,
        )
        try:
            self._wait_until_healthy(log)
        except BaseException:
            self.stop()
            raise

    def _wait_until_healthy(self, log: Path) -> None:
        for _ in range(120):
            if self.process.poll() is not None:
                raise SystemExit(f"Instanz beendet, siehe {log}")
            try:
                if get(self.base, "/health")[0] == 200:
                    return
            except OSError:
                pass
            time.sleep(0.25)
        raise SystemExit(f"Instanz antwortet nicht, siehe {log}")

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.log.close()


def get(base: str, path: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(base + path, timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        body = error.read()
        try:
            return error.code, json.loads(body or b"null")
        except json.JSONDecodeError:
            return error.code, body.decode(errors="replace")[:200]


def send(base: str, path: str, method: str, body: object = None) -> int:
    data = b"" if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def check_network_blocked(policy: Path, port: int) -> None:
    """Gegenprobe: In der Sandbox scheitert eine externe Verbindung mit EPERM, lokal nicht."""
    probe = (
        "import errno, socket, sys\n"
        "try:\n    socket.create_connection(('1.1.1.1', 443), timeout=5)\n    sys.exit('extern offen')\n"
        "except OSError as error:\n"
        "    if error.errno != errno.EPERM: sys.exit(f'extern nicht durch die Sandbox gesperrt: {error}')\n"
        f"socket.create_connection(('127.0.0.1', {port}), timeout=5)\n"
    )
    result = subprocess.run(["sandbox-exec", "-f", str(policy), str(PYTHON), "-c", probe],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"Netzsperre nicht belegt: {result.stderr.strip() or result.stdout.strip()}")


def supplement(snapshot: Path, source_dir: Path, policy: Path, run_dir: Path) -> tuple[Path, list[str]]:
    """Nimmt mit dem alten Stand die Papiere aus `supplement_assets.yaml` auf.

    Returns:
        Die ergänzte Datenbank — der gemeinsame Ausgangszustand beider
        Stände — und die ergänzten Eingaben, damit echte und ergänzte Papiere
        getrennt gezählt werden.
    """
    assets_text = SUPPLEMENT.read_text()
    database = prepare_data_dir(run_dir / "supplement", snapshot, assets_text)
    instance = Instance(source_dir, database, policy, run_dir / "supplement.log")
    added = []
    try:
        check_network_blocked(policy, instance.port)
        for identifier in re.findall(r"isin: ([A-Z0-9]{12})|base: (\w+), quote_currency: (\w+)", assets_text):
            value = identifier[0] or f"{identifier[1]}-{identifier[2]}"
            status = send(instance.base, "/instruments/intake", "POST", {"identifier": value})
            if status not in (200, 201):
                raise SystemExit(f"Ergänzung {value} scheitert mit {status}, siehe supplement.log")
            added.append(value)
    finally:
        instance.stop()
    prepared = run_dir / "prepared.db"
    copy_database(database, prepared)
    return prepared, added


def instrument_key(item: dict) -> str:
    """Schlüssel je Papier über beide Stände: die Identität, nicht die interne ID."""
    identity = item.get("identity") or {}
    return identity.get("isin") or "/".join(str(identity.get(field)) for field in ("ticker", "mic", "base", "quote_currency"))


def collect(base: str, fx_pairs: list[tuple[str, str]]) -> dict:
    """Dieselben Abfragen an eine Instanz; Ergebnis als ein JSON-Baum."""
    status, instruments = get(base, "/instruments")
    if status != 200:
        raise SystemExit(f"/instruments antwortet {status}")
    answers: dict = {"instruments": {}, "daily": {}, "overrides": {}, "fx": {}}
    for item in instruments:
        key = instrument_key(item)
        answers["instruments"][key] = item
        symbol = urllib.parse.quote(item["symbol"], safe="")
        isin = (item.get("identity") or {}).get("isin")
        daily = f"/quote/{isin}/daily" if isin else f"/quote/by-symbol/{symbol}/daily"
        answers["daily"][key] = get(base, daily + "?period=max")
        answers["overrides"][key] = get(base, f"/instruments/by-symbol/{symbol}/overrides")
    for base_currency, quote_currency in fx_pairs:
        answers["fx"][f"{base_currency}{quote_currency}"] = get(base, f"/fx?base={base_currency}&quote={quote_currency}")
    answers["migration"] = get(base, "/migration")
    # Sicherungsliste und Datenversionen der Quellen (der Daten-Versionsstand).
    answers["backups"] = get(base, "/backups")
    answers["sources"] = get(base, "/sources")
    return answers


def flatten(value: object, path: str = "") -> dict[str, object]:
    if isinstance(value, dict):
        return {k: v for key, item in value.items() for k, v in flatten(item, f"{path}/{key}" if path else str(key)).items()}
    if isinstance(value, (list, tuple)):
        return {k: v for index, item in enumerate(value) for k, v in flatten(item, f"{path}/{index}").items()} or {path: []}
    return {path: value}


def compare(before: dict, after: dict) -> tuple[list[str], int]:
    """Befunde (Feldpfade mit Unterschied) und Zahl der verglichenen Felder."""
    old, new = flatten(before), flatten(after)
    paths = old.keys() | new.keys()
    missing = object()
    return sorted(path for path in paths if old.get(path, missing) != new.get(path, missing)), len(paths)


def changed_tables(old: dict[str, set[tuple]], new: dict[str, set[tuple]]) -> list[str]:
    return sorted(table for table in old.keys() | new.keys() if old.get(table) != new.get(table))


def refresh_source(item: dict) -> tuple[str, float]:
    """Eine Offline-Fachdatei, die genau dieses Papier mit einem neuen Kurs kennt.

    Ohne sie antwortet die Aktualisierung mit 502 und ändert nichts — und
    „nichts geändert“ sähe aus wie ein bestandener Schritt (Runde-2-Befund B6).
    JSON ist gültiges YAML.
    """
    price = round((item.get("latest_price") or 1.0) + 1.0, 4)
    identity = {field: value for field, value in (item.get("identity") or {}).items() if value is not None}
    entry = {
        "id": "refresh-target", "identity": identity, "name": item["name"], "instrument_type": item["type"],
        "price": {"value": price, "currency": item.get("latest_currency") or item.get("currency") or "EUR",
                  "as_of": datetime.now().astimezone().isoformat(timespec="seconds")},
    }
    return json.dumps({"version": 1, "instruments": [entry], "fx_rates": []}), price


def write_path(run_dir: Path, snapshot: Path, source_dir: Path, policy: Path,
               instruments: dict) -> tuple[dict[str, tuple[int, list[str]]], bool]:
    """Schreibt über die API einer eigenen Instanz; je Schritt Status und geänderte Tabellen.

    Je Schritt gegen den Stand davor: Nur Setzen und Zurücksetzen zusammen zu
    vergleichen hieße, einen wirkungslosen Schreibweg als bestanden zu zählen.
    Der Status gehört dazu: Ein gescheiterter Aufruf ändert ebenfalls nichts.

    Returns:
        Je Schritt (HTTP-Status, geänderte Tabellen) und ob die API danach
        den neuen Kurs zeigt.
    """
    item = next((item for item in instruments.values() if item.get("type") in ("etf", "fund")), next(iter(instruments.values())))
    assets_text, new_price = refresh_source(item)
    database = prepare_data_dir(run_dir / "write", snapshot, assets_text)
    instance = Instance(source_dir, database, policy, run_dir / "write.log")
    try:
        check_network_blocked(policy, instance.port)
        symbol = urllib.parse.quote(item["symbol"], safe="")
        path = f"/instruments/by-symbol/{symbol}/overrides"
        start = table_contents(database)
        _, overrides = get(instance.base, path)
        set_status = send(instance.base, path, "PUT", {**overrides, "ter": 0.42})
        after_set = table_contents(database)
        reset_status = send(instance.base, path, "PUT", overrides)
        after_reset = table_contents(database)
        refresh_status = send(instance.base, f"/refresh/by-symbol/{symbol}", "POST")
        after_refresh = table_contents(database)
        _, listed = get(instance.base, "/instruments")
    finally:
        instance.stop()
    shown = next((entry.get("latest_price") for entry in listed if entry.get("symbol") == item["symbol"]), None)
    return {
        "setzen": (set_status, changed_tables(start, after_set)),
        "zurücksetzen": (reset_status, changed_tables(start, after_reset)),
        "aktualisieren": (refresh_status, changed_tables(after_reset, after_refresh)),
    }, shown == new_price


def run_browser_check(run_dir: Path, snapshot: Path, expected: dict) -> bool:
    """W17 sichtbar auf einer eigenen Kopie; `HEADLESS` aus der Umgebung gilt hier nicht."""
    browser_db = prepare_data_dir(run_dir / "browser", snapshot)
    (run_dir / "expected.json").write_text(json.dumps(expected))
    env = {name: value for name, value in os.environ.items() if name != "HEADLESS"}
    env.update(NO_RELOAD, ONLY="W17", DB_COPY=str(browser_db), EXPECTED=str(run_dir / "expected.json"),
               VISUAL_OUT=str(run_dir / "visual"))
    return subprocess.run(["node", "e2e/visual-check.mjs"], cwd=ROOT / "dashboard", env=env).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "stockinfo.db")
    parser.add_argument("--before", default="de620e9")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--keep", action="store_true")
    options = parser.parse_args()

    run_dir = ROOT / ".tmp" / "t97" / datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_dir.mkdir(parents=True)
    policy = run_dir / "no-network.sb"
    policy.write_text(SANDBOX_POLICY)
    original_hashes = file_hashes(options.source)
    instances: list[Instance] = []
    problems: list[str] = []
    try:
        snapshot = run_dir / "snapshot.db"
        snapshot_read_only(options.source, snapshot)
        if file_hashes(options.source) != original_hashes:
            raise SystemExit("Das Original hat sich während der Sicherung geändert — Abbruch")
        # Beide Stände als unbearbeitetes Archiv: Der Root liest sonst seine
        # `.env` und lokale Paket-Metadaten, der alte Stand nicht.
        sources = {name: extract(revision, run_dir / f"{name}-src")
                   for name, revision in (("before", options.before), ("after", "HEAD"))}

        real_count = QuoteRepository(str(snapshot)).count_instruments()
        added: list[str] = []
        if real_count < MINIMUM_ASSETS:
            snapshot, added = supplement(snapshot, sources["before"], policy, run_dir)
        fx_pairs = QuoteRepository(str(snapshot)).list_fx_pairs()

        answers = {}
        for name, source_dir in sources.items():
            database = prepare_data_dir(run_dir / name, snapshot)
            instance = Instance(source_dir, database, policy, run_dir / f"{name}.log")
            instances.append(instance)
            check_network_blocked(policy, instance.port)
            # Der eigene Datenordner steht in Antworten wie `/sources`
            # (`config_path`); er unterscheidet die Läufe, nicht die Stände.
            raw = json.dumps(collect(instance.base, fx_pairs))
            answers[name] = json.loads(raw.replace(str(run_dir / name), "<datenordner>"))
            (run_dir / f"{name}.json").write_text(json.dumps(answers[name], indent=1, sort_keys=True))

        findings, field_count = compare(answers["before"], answers["after"])
        for instance in instances:
            instance.stop()
        instances.clear()
        writes, price_shown = write_path(run_dir, snapshot, sources["after"], policy, answers["after"]["instruments"])

        print(f"Instrumente: {len(answers['before']['instruments'])} vorher, {len(answers['after']['instruments'])} nachher "
              f"({real_count} aus dem Arbeitsbestand, {len(added)} ergänzt)")
        print(f"Wechselkurse: {len(fx_pairs)}; verglichene Felder: {field_count}")
        print(f"Befunde: {len(findings)}")
        for path in findings[:200]:
            print(f"  {path}")
        if findings:
            problems.append(f"{len(findings)} Befunde im Vergleich")
        for step, (status, tables) in writes.items():
            print(f"Schreibweg {step}: HTTP {status}, geänderte Tabellen {', '.join(tables) or 'keine'}")
            if status != 200:
                problems.append(f"Schreibweg {step} antwortet {status}")
            if tables != EXPECTED_WRITES[step]:
                problems.append(f"Schreibweg {step} ändert {tables or 'nichts'} statt {EXPECTED_WRITES[step] or 'nichts'}")
        if not price_shown:
            problems.append("Schreibweg aktualisieren: neuer Kurs nicht in /instruments")

        if not options.no_browser:
            visual_ok = run_browser_check(run_dir, snapshot, answers["before"]["instruments"])
            print(f"Browserweg W17: {'grün' if visual_ok else 'ROT'}")
            if not visual_ok:
                problems.append("W17 rot")
    finally:
        for instance in instances:
            instance.stop()
        unchanged = file_hashes(options.source) == original_hashes
        print(f"Original unverändert: {'ja' if unchanged else 'NEIN'}")
        if not options.keep:
            shutil.rmtree(run_dir, ignore_errors=True)
    if not unchanged:
        problems.append("Original verändert")
    for problem in problems:
        print(f"ROT: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
