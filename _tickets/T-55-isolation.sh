#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-55-isolation.sh — belegt, dass eine Testdatei `data/stockinfo.db` weder
# oeffnet noch veraendert
#
# **Der Dateivergleich allein ist blind:** SQLite legt WAL und SHM beim Oeffnen
# an und raeumt sie beim Schliessen ab — vorher wie nachher steht "fehlt".
# Sichtbar wird das Oeffnen an der mtime von `data/`, und erst auf
# **Nanosekunden**: Anlegen und Loeschen fallen in dieselbe Sekunde. Der Aufruf
# geht direkt an pytest, weil make DATABASE_PATH ueberschreibt.
#------------------------------------------------------------------------------
set -uo pipefail

# Aufwaerts, erkennbar an `.libs/` — ein festes `../` braeche in `solved/`.
findProjectRoot() {
    local _DIR="$1"
    while [[ "${_DIR}" != "/" ]]; do
        [[ -d "${_DIR}/.libs" ]] && { echo "${_DIR}"; return 0; }
        _DIR="$(dirname "${_DIR}")"
    done
    return 1
}
# `readonly` liefert **immer** 0 — der Exit-Code muss vorher gesichert werden.
_RC=0
PROJECT_ROOT="$(findProjectRoot "$(cd "$(dirname "$0")" && pwd)")" || _RC=$?
if [[ ${_RC} -ne 0 ]]; then
    echo "kein Projekt gefunden — kein .libs oberhalb von $(dirname "$0")" >&2
    exit 1
fi
readonly PROJECT_ROOT
BASH_LIBS="${BASH_LIBS:-${PROJECT_ROOT}/.libs/BashLib/src}"
if [[ "${__COLORS_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/colors.lib.sh"; fi
if [[ "${__TOOLS_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/tools.lib.sh";  fi
APPNAME="$(basename "$0")"
readonly APPNAME
readonly TARGET="${TARGET:-tests/test_api.py}"
readonly DB="data/stockinfo.db"
usage() {
    echo -e "\nUsage: ${APPNAME} [ options ]\n"
    usageLine "-r | --run " "Prueft, ob ${TARGET} ${DB} unberuehrt laesst"
    usageLine "-h | --help" "Diese Hilfe anzeigen"
    echo -e "\n    ${YELLOW}TARGET${NC}=<pfad> — andere Testdatei pruefen\n"
}

# Eine Zeile je DB-Datei; eine fehlende ist ein Ergebnis, kein Abbruchgrund.
state() {
    local _FILE _SUM
    for _FILE in "${DB}" "${DB}-wal" "${DB}-shm"; do
        _SUM="fehlt"
        [[ -f "${_FILE}" ]] && _SUM="$(shasum -a 256 "${_FILE}" | cut -d' ' -f1)"
        printf '%-64s  %s\n' "${_SUM}" "${_FILE}"
    done
}

runCheck() {
    cd "${PROJECT_ROOT}" || return 2
    local _OUT _BEFORE _AFTER _MTIME _MTIME_AFTER
    _BEFORE="$(state)"; _MTIME="$(stat -f%Fm data)"
    if ! _OUT="$(.venv/bin/pytest "${TARGET}" -q 2>&1)"; then
        echo -e "  ${RED}✗${NC} ${TARGET} ist rot — Isolation nicht beurteilbar"
        echo "${_OUT}" | tail -20 >&2; return 2
    fi
    _AFTER="$(state)"; _MTIME_AFTER="$(stat -f%Fm data)"
    if [[ "${_BEFORE}" == "${_AFTER}" && "${_MTIME}" == "${_MTIME_AFTER}" ]]; then
        echo -e "  ${GREEN}✓${NC} ${TARGET} laesst ${DB} unberuehrt (mtime ${_MTIME_AFTER})"
        return 0
    fi
    echo -e "  ${RED}✗${NC} ${TARGET} hat ${DB} angefasst"
    echo -e "      data/ mtime ${_MTIME} → ${_MTIME_AFTER}"
    diff <(echo "${_BEFORE}") <(echo "${_AFTER}") >&2
    return 1
}

RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -r|--run)  RUN=true ;;
        -h|--help) usage; exit 0 ;;
        *)         echo "Unbekannte Option: $1"; usage; exit 1 ;;
    esac
    shift
done
[[ "${RUN}" == true ]] || { usage; exit 0; }
runCheck
exit $?
