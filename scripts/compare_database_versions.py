"""Vergleicht die API vor und nach der SQL-Umstellung auf einer Kopie des Arbeitsbestands (T-97).

Ablauf:

1. Das Original wird nur lesend geöffnet und einmal per SQLite-Backup in
   einen Snapshot gesichert. Aus diesem Snapshot entstehen alle Kopien.
   Die Prüfsummen des Originals (samt `-wal`/`-shm`) müssen vorher und
   nachher gleich sein, sonst bricht das Skript ab.
2. Der alte Stand (`git archive`, Standard `de620e9`, letzter Stand vor T-90)
   und der aktuelle Stand laufen je auf eigener Kopie und eigenem Port, unter
   `sandbox-exec` ohne Netz und mit sehr großen TTL-Werten.
3. Beide Instanzen beantworten dieselben Abfragen. Die Antworten werden
   feldweise verglichen; erwartete Unterschiede stehen mit Ticket in
   `EXPECTED_DIFFERENCES`, alles andere ist ein Befund.
4. Auf der Nachher-Kopie wird einmal geschrieben (manuelle TER setzen und
   zurücknehmen, ein Papier aktualisieren); danach dürfen nur erwartete
   Tabellen anders sein.
5. Die Antworten des alten Stands werden als Erwartung für den Browserweg
   W17 in `dashboard/e2e/visual-check.mjs` abgelegt, der dann sichtbar auf
   einer weiteren Kopie läuft.

Alles liegt unter `.tmp/t97/<Zeit>/` im Projekt-Root und wird am Ende
gelöscht (`--keep` lässt es zur Fehlersuche stehen). Ausgegeben werden nur
Zahlen, Feldpfade und Symbole, keine vollständigen Datensätze.

Aufruf aus dem Projekt-Root:
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
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"
UVICORN = ROOT / ".venv" / "bin" / "uvicorn"

# Netz zu, nur die eigene Maschine erlaubt. Die Gegenprobe in
# `check_network_blocked` belegt die Wirkung je Lauf.
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

# Unterschiede, die aus beauftragten Tickets stammen: (Feldpfad als
# regulärer Ausdruck, Ticket, Begründung). Alles andere ist ein Befund.
EXPECTED_DIFFERENCES: list[tuple[str, str, str]] = [
    (r"^instruments/[^/]+/fund_size$", "T-88", "Fondsgröße in Euro statt in Millionen"),
    (r"^instruments/[^/]+/details/fund_size/", "T-88", "Fondsgröße in Euro statt in Millionen"),
    (r"^instruments/[^/]+/(details/)?volatility", "T-89", "Volatilität neu berechnet"),
    (r"^fx/[^/]+/quote_time$", "T-94", "Zeitpunkt der Quelle statt Abruf"),
]


def file_hashes(database: Path) -> dict[str, str]:
    """SHA-256 der Datenbank und ihrer WAL-/SHM-Dateien, soweit vorhanden."""
    hashes = {}
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{database}{suffix}")
        if path.exists():
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def take_snapshot(source: Path, target: Path) -> None:
    """Sichert das Original einmal konsistent, ohne darin zu schreiben.

    Schon `mode=ro` legt bei einer WAL-Datenbank `-wal` und `-shm` neben dem
    Original an (gemessen im ersten Lauf). `immutable=1` lässt beides weg,
    liest aber eine WAL mit Inhalt nicht mit. Deshalb bricht das Skript ab,
    solange eine solche WAL besteht: Dann läuft die App, oder ihre letzten
    Schreibvorgänge stehen noch nicht in der Datenbankdatei.
    """
    wal = Path(f"{source}-wal")
    if wal.exists() and wal.stat().st_size > 0:
        raise SystemExit(f"{wal.name} ist nicht leer — bitte die App stoppen und erneut starten")
    original = sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        with sqlite3.connect(target) as copy:
            original.backup(copy)
    finally:
        original.close()


def prepare_data_dir(directory: Path, snapshot: Path, assets_text: str = EMPTY_ASSETS) -> Path:
    """Kopie des Snapshots samt Offline-Quellen; ohne Fachdaten, außer beim Ergänzen."""
    directory.mkdir(parents=True)
    database = directory / "stockinfo.db"
    # Über die Backup-Schnittstelle, nicht `copyfile`: Nach dem Ergänzen
    # steht ein Teil des Snapshots noch in dessen WAL (gemessen: 9 statt 16).
    with sqlite3.connect(f"{snapshot.as_uri()}?mode=ro", uri=True) as source, sqlite3.connect(database) as target:
        source.backup(target)
    assets = directory / "assets.yaml"
    assets.write_text(assets_text)
    sources = (ROOT / "examples" / "sources-standalone.yaml").read_text()
    (directory / "sources.yaml").write_text(sources.replace("/data/assets-standalone.yaml", str(assets)))
    return database


def extract(revision: str, target: Path) -> Path:
    """Legt einen Stand per `git archive` unter `.tmp/` ab — kein Worktree, keine Edits."""
    target.mkdir()
    archive = subprocess.run(["git", "archive", revision], cwd=ROOT, capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive.stdout, check=True)
    return target


def supplement(snapshot: Path, source_dir: Path, policy: Path, run_dir: Path) -> list[str]:
    """Nimmt mit dem alten Stand Papiere aus `supplement_assets.yaml` in den Snapshot auf.

    Danach ist der Snapshot der gemeinsame Ausgangszustand für beide Stände.
    Rückgabe: die ergänzten Eingaben, damit echte und ergänzte Papiere
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
            status = post_json(instance.base, "/instruments/intake", {"identifier": value})
            if status not in (200, 201):
                raise SystemExit(f"Ergänzung {value} scheitert mit {status}, siehe supplement.log")
            added.append(value)
    finally:
        instance.stop()
    with sqlite3.connect(database) as source, sqlite3.connect(snapshot) as target:
        source.backup(target)
    return added


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Instance:
    """Eine App-Instanz in der Netz-Sandbox; beendet wird nur dieser Prozess."""

    def __init__(self, source_dir: Path, database: Path, policy: Path, log: Path) -> None:
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = {**os.environ, **NO_RELOAD, "DATABASE_PATH": str(database)}
        # Der alte Stand nutzt seine eigene Plugin-API, nicht die des Root.
        env["PYTHONPATH"] = str(source_dir / "plugin_api" / "src")
        self.log = log.open("w")
        self.process = subprocess.Popen(
            ["sandbox-exec", "-f", str(policy), str(UVICORN), "app.main:app",
             "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=source_dir, env=env, stdout=self.log, stderr=subprocess.STDOUT,
        )
        for _ in range(120):
            if self.process.poll() is not None:
                raise SystemExit(f"Instanz beendet, siehe {log}")
            try:
                if get(self.base, "/health")[0] == 200:
                    return
            except OSError:
                time.sleep(0.25)
        raise SystemExit(f"Instanz antwortet nicht, siehe {log}")

    def stop(self) -> None:
        self.process.terminate()
        self.process.wait(timeout=20)
        self.log.close()


def get(base: str, path: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(base + path, timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null")


def put(base: str, path: str, body: object) -> int:
    request = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="PUT",
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status


def post(base: str, path: str) -> int:
    return post_json(base, path, None)


def post_json(base: str, path: str, body: object) -> int:
    data = b"" if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base + path, data=data, method="POST",
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


def compare(before: dict, after: dict) -> tuple[dict[str, list[str]], list[str], int]:
    """Erwartete Unterschiede je Ticket, Befunde, Zahl der verglichenen Felder."""
    old, new = flatten(before), flatten(after)
    expected: dict[str, list[str]] = {}
    findings = []
    for path in sorted(old.keys() | new.keys()):
        if old.get(path, "<fehlt>") == new.get(path, "<fehlt>"):
            continue
        ticket = next((ticket for pattern, ticket, _ in EXPECTED_DIFFERENCES if re.search(pattern, path)), None)
        (expected.setdefault(ticket, []) if ticket else findings).append(path)
    return expected, findings, len(old.keys() | new.keys())


def table_rows(database: Path) -> dict[str, set[tuple]]:
    """Alle Zeilen je Tabelle, nur lesend — für den Vergleich vor und nach dem Schreiben."""
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    try:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        return {table: set(connection.execute(f'SELECT * FROM "{table}"')) for table in tables}
    finally:
        connection.close()


def changed_tables(old: dict[str, set[tuple]], new: dict[str, set[tuple]]) -> list[str]:
    return sorted(table for table in old.keys() | new.keys() if old.get(table) != new.get(table))


def write_path(instance: Instance, database: Path, instruments: dict) -> dict[str, list[str]]:
    """Schreibt über die API und meldet je Schritt die geänderten Tabellen.

    Drei Schritte: eine manuelle TER setzen, den alten Satz zurückschreiben,
    ein Papier aktualisieren (ohne Netz: nichts Neues). Erwartet ist eine
    geänderte Override-Tabelle nach dem Setzen und danach wieder der
    Ausgangsstand. Nur Setzen und Zurücksetzen zusammen zu vergleichen hieße,
    einen wirkungslosen Schreibweg als bestanden zu zählen.
    """
    item = next((item for item in instruments.values() if item.get("type") in ("etf", "fund")), next(iter(instruments.values())))
    symbol = urllib.parse.quote(item["symbol"], safe="")
    start = table_rows(database)
    _, overrides = get(instance.base, f"/instruments/by-symbol/{symbol}/overrides")
    put(instance.base, f"/instruments/by-symbol/{symbol}/overrides", {**overrides, "ter": 0.42})
    after_set = table_rows(database)
    put(instance.base, f"/instruments/by-symbol/{symbol}/overrides", overrides)
    after_reset = table_rows(database)
    post(instance.base, f"/refresh/by-symbol/{symbol}")
    after_refresh = table_rows(database)
    return {
        "setzen": changed_tables(start, after_set),
        "zurücksetzen": changed_tables(start, after_reset),
        "aktualisieren": changed_tables(after_reset, after_refresh),
    }


def main() -> None:
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
    try:
        snapshot = run_dir / "snapshot.db"
        take_snapshot(options.source, snapshot)
        if file_hashes(options.source) != original_hashes:
            raise SystemExit("Das Original hat sich während der Sicherung geändert — Abbruch")
        # Beide Stände als unbearbeitetes Archiv: Der Root liest sonst seine
        # `.env` und lokale Paket-Metadaten, der alte Stand nicht (erster Lauf:
        # `yaml-file` fehlte nur im Root). So starten beide gleich.
        sources = {name: extract(revision, run_dir / f"{name}-src")
                   for name, revision in (("before", options.before), ("after", "HEAD"))}

        with sqlite3.connect(f"{snapshot.as_uri()}?mode=ro", uri=True) as connection:
            real_count = connection.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
        added = []
        if real_count < MINIMUM_ASSETS:
            added = supplement(snapshot, sources["before"], policy, run_dir)
        with sqlite3.connect(f"{snapshot.as_uri()}?mode=ro", uri=True) as connection:
            fx_pairs = list(connection.execute("SELECT base, quote FROM fx_rates ORDER BY base, quote"))

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

        expected, findings, field_count = compare(answers["before"], answers["after"])
        writes = write_path(instances[-1], run_dir / "after" / "stockinfo.db", answers["after"]["instruments"])
        for instance in instances:
            instance.stop()
        instances.clear()

        print(f"Instrumente: {len(answers['before']['instruments'])} vorher, {len(answers['after']['instruments'])} nachher "
              f"({real_count} aus dem Arbeitsbestand, {len(added)} ergänzt)")
        print(f"Wechselkurse: {len(fx_pairs)}; verglichene Felder: {field_count}")
        for ticket, paths in sorted(expected.items()):
            print(f"erwartet ({ticket}): {len(paths)} Felder, z. B. {paths[0]}")
        print(f"Befunde: {len(findings)}")
        for path in findings[:200]:
            print(f"  {path}")
        for step, tables in writes.items():
            print(f"Schreibweg {step}: geänderte Tabellen {', '.join(tables) or 'keine'}")

        if not options.no_browser:
            browser_db = prepare_data_dir(run_dir / "browser", snapshot)
            (run_dir / "expected.json").write_text(json.dumps(answers["before"]["instruments"]))
            # Sichtbar auf dem Hauptmonitor; Bilder echter Daten im Laufordner.
            visual = subprocess.run(
                ["node", "e2e/visual-check.mjs"], cwd=ROOT / "dashboard",
                env={**os.environ, **NO_RELOAD, "ONLY": "W17", "DB_COPY": str(browser_db),
                     "EXPECTED": str(run_dir / "expected.json"), "VISUAL_OUT": str(run_dir / "visual")},
            )
            print(f"Browserweg W17: {'grün' if visual.returncode == 0 else 'ROT'}")
    finally:
        for instance in instances:
            instance.stop()
        unchanged = file_hashes(options.source) == original_hashes
        print(f"Original unverändert: {'ja' if unchanged else 'NEIN'}")
        if not options.keep:
            shutil.rmtree(run_dir, ignore_errors=True)
    if not unchanged:
        sys.exit(1)


if __name__ == "__main__":
    main()
