#!/usr/bin/env bash
#
# Belegt, dass `tests/test_api.py` die Betriebsdatenbank nicht anfasst.
#
# **Die Verzeichnis-mtime ist der eigentliche Detektor.** Ein Vergleich der
# drei Dateien allein — auch mit Existenz — ist **blind**: SQLite legt WAL und
# SHM beim Oeffnen an und raeumt sie beim sauberen Schliessen wieder ab. Vorher
# wie nachher steht dann "fehlt", und der Lauf sieht unschuldig aus. Gemessen:
# In genau dieser Lage meldete die erste Fassung dieses Skripts ein gruenes
# Ergebnis, obwohl der Defekt unveraendert vorlag.
#
# Das Anlegen und Loeschen aendert dagegen die mtime von `data/` selbst. Die
# Gegenprobe mit `tests/test_analyzer.py`, das die Datenbank nicht anfasst,
# laesst sie unveraendert — der Detektor ist also nicht bloss empfindlich.
#
# Die drei Dateizustaende bleiben trotzdem im Bericht: Sie sagen, **was**
# passiert ist, wenn die mtime anschlaegt.
#
# **Direkt an pytest, nicht ueber make.** Die Make-Grenze ueberschreibt
# DATABASE_PATH aus dem eingebundenen `.env`; ein vorangestelltes
# `env DATABASE_PATH=… make test` bleibt deshalb wirkungslos und waere als
# Isolationsorakel wertlos.
set -euo pipefail

readonly _PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly _TARGET="${1:-tests/test_api.py}"

cd "${_PROJECT}"

# Zustand der drei Betriebsdateien als eine Zeile je Datei: Pruefsumme oder
# ausdruecklich "fehlt". Beides ist ein Ergebnis, keins ist ein Abbruchgrund.
state() {
    local _FILE
    for _FILE in data/stockinfo.db{,-wal,-shm}; do
        if [[ -f "${_FILE}" ]]; then
            printf '%s  %s\n' "$(shasum -a 256 "${_FILE}" | cut -d' ' -f1)" "${_FILE}"
        else
            printf '%-64s  %s\n' "fehlt" "${_FILE}"
        fi
    done
}

readonly _BEFORE="$(state)"
readonly _DIR_BEFORE="$(stat -f%m data)"

.venv/bin/pytest "${_TARGET}" -q > /tmp/t55-pytest.log 2>&1 || {
    echo "✗ ${_TARGET} ist rot — Isolation nicht beurteilbar" >&2
    tail -20 /tmp/t55-pytest.log >&2
    exit 2
}

readonly _AFTER="$(state)"
readonly _DIR_AFTER="$(stat -f%m data)"

if [[ "${_BEFORE}" == "${_AFTER}" && "${_DIR_BEFORE}" == "${_DIR_AFTER}" ]]; then
    echo "✓ ${_TARGET} laesst die Betriebsdatenbank unberuehrt"
    echo "  data/ mtime ${_DIR_AFTER} unveraendert"
    echo "${_AFTER}"
else
    echo "✗ ${_TARGET} hat die Betriebsdatenbank angefasst:" >&2
    if [[ "${_DIR_BEFORE}" != "${_DIR_AFTER}" ]]; then
        echo "  data/ mtime ${_DIR_BEFORE} → ${_DIR_AFTER}" >&2
        echo "  (WAL/SHM angelegt und beim Schliessen wieder abgeraeumt)" >&2
    fi
    diff <(echo "${_BEFORE}") <(echo "${_AFTER}") >&2 || true
    exit 1
fi
