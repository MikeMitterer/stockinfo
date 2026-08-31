#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-20-smoke.sh — Die maschinell prüfbaren Zeilen aus Ticket T-20 abarbeiten
#
# Startet einen eigenen Backend-Prozess auf einem eigenen Port mit einer
# frischen, temporären Datenbank. Die Arbeits-Datenbank bleibt unberührt.
#
# Zwei Läufe, weil die Zeilen entgegengesetzte Bedingungen brauchen:
#
#   1. mit Netz     → #1: eine unbekannte ISIN ist ein 404, weil beide Quellen
#                     nachgesehen haben
#   2. ohne Netz    → #2/#3: dieselbe Anfrage muss 502 werden und sagen, wer
#                     ausgefallen ist
#
# Das Netz wird über einen Proxy auf einen **geschlossenen** Port abgeschnitten
# (Port 9, discard). Das trifft OpenFIGI wie Yahoo und braucht keinen Eingriff
# in den Code — eine Testschaltung im Produktivpfad wäre der schlechtere Weg.
#
# Verwendung:
#   ./_tickets/T-20-smoke.sh --run
#   ./_tickets/T-20-smoke.sh --run --keep-log
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep-log   Server-Logs nach dem Lauf stehen lassen
#   -i | --info       Einstellungen anzeigen
#   -h | --help       Diese Hilfe anzeigen
#------------------------------------------------------------------------------
set -uo pipefail

# **Das Projekt findet sich selbst — aufwärts, erkennbar an `.libs/`.**
#
# Ein festes `../` bindet das Script an seine Tiefe im Baum und bricht damit
# genau beim vorgesehenen Abschluss: In `_tickets/solved/` liegt es eine Ebene
# tiefer, und beide Pfade zeigen ins Leere.
#
# Params:
#   $1 - Verzeichnis, ab dem gesucht wird
#
# Returns:
#   0 und das Projektverzeichnis auf stdout, 1 wenn keines gefunden wurde
findProjectRoot() {
    local _DIR="$1"
    while [[ "${_DIR}" != "/" ]]; do
        [[ -d "${_DIR}/.libs" ]] && { echo "${_DIR}"; return 0; }
        _DIR="$(dirname "${_DIR}")"
    done
    return 1
}

# `readonly` gibt **immer** 0 zurück — der Exit-Code muss vorher gesichert
# werden, sonst greift die Prüfung nie.
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
if [[ "${__APPS_LIB__:=""}"   == "" ]]; then . "${BASH_LIBS}/apps.lib.sh";   fi

readonly APPNAME="$(basename "$0")"
# Überschreibbar, falls der Port belegt ist: `PORT=8790 ./T-20-smoke.sh --run`
readonly PORT="${PORT:-8769}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Port 9 ist „discard" und hier zu — jede Verbindung dorthin scheitert sofort.
readonly TOTER_PROXY="http://127.0.0.1:9"

readonly ISIN_UNBEKANNT="XX0000000000"  # Präfix existiert nicht
readonly ISIN_BEKANNT="IE00B4L5Y983"    # gibt es — nur eben nicht ohne Netz

COUNT_OK=0
COUNT_FAIL=0
SERVER_PID=""
WORKDIR=""
LOGFILE=""
KEEP_LOG=false

# Zeigt die Verwendungshinweise an.
usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Checks ausführen (eigener Server, temporäre DB)"
    usageLine "-k | --keep-log  " "Server-Logs nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Mit Log:       ${GREEN}${APPNAME} --run --keep-log${NC}"
    echo
    echo -e "    Zeile ${YELLOW}#4${NC} (unzuständige Quelle wird übersprungen) prüft dieses"
    echo -e "    Script ${YELLOW}nicht${NC} — dafür braucht es eine Kette mit einer unzuständigen"
    echo -e "    Quelle, und die gibt es erst mit den Plugins aus T-23."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port        ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Papiere     ${NC} = ${BLUE}${ISIN_UNBEKANNT}, ${ISIN_BEKANNT}${NC}"
    echo
}

# Bricht ab, wenn auf dem Port schon jemand lauscht.
#
# Returns:
#   0 wenn der Port frei ist, sonst 1
requirePortIsFree() {
    local _OCCUPANT
    _OCCUPANT="$(lsof -ti ":${PORT}" 2>/dev/null)"
    [[ -z "${_OCCUPANT}" ]] && return 0

    echo -e "  ${RED}✗${NC} Port ${PORT} ist belegt (PID ${_OCCUPANT//$'\n'/, })."
    echo -e "      Dieses Script beendet nichts, was es nicht selbst gestartet hat."
    echo -e "      Anderen Port wählen: ${GREEN}PORT=8790 ${APPNAME} --run${NC}"
    return 1
}

# Beendet den selbst gestarteten Server. **Nur die eigene PID.**
stopServer() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null
        wait "${SERVER_PID}" 2>/dev/null
    fi
    SERVER_PID=""
}

# Räumt Server und Arbeitsverzeichnis ab. Wird per trap aufgerufen.
cleanup() {
    stopServer
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP_LOG}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Server-Logs: ${WORKDIR}"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Startet das Backend auf einer frischen DB und wartet, bis es antwortet.
#
# Params:
#   $1 - Kennung des Laufs (benennt DB und Log)
#   $2 - 'blockiert' schneidet das Netz per toter Proxy-Adresse ab
#
# Returns:
#   0 wenn der Server erreichbar ist, 1 sonst
startServer() {
    local -r _RUN="$1"
    local -r _NETZ="${2:-offen}"

    requirePortIsFree || return 1
    [[ -z "${WORKDIR}" ]] && WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/${_RUN}.log"

    local _PROXY=""
    [[ "${_NETZ}" == "blockiert" ]] && _PROXY="${TOTER_PROXY}"

    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${WORKDIR}/${_RUN}.db" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            DEFAULT_EXCHANGE=XETR \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            HTTP_PROXY="${_PROXY}" \
            HTTPS_PROXY="${_PROXY}" \
            NO_PROXY="127.0.0.1,localhost" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL}, Netz ${_NETZ} (PID ${SERVER_PID})"
            return 0
        fi
        sleep 0.5
    done
    echo -e "  ${RED}✗${NC} Backend startet nicht — Log:"
    tail -20 "${LOGFILE}"
    return 1
}

# Meldet das Ergebnis eines Checks und zählt mit.
report() {
    local -r _LINE="$1"
    local -r _WHAT="$2"
    local -r _OK="$3"
    local -r _ACTUAL="$4"

    if [[ "${_OK}" == true ]]; then
        COUNT_OK=$((COUNT_OK + 1))
        echo -e "  ${GREEN}✓${NC} ${_LINE} ${_WHAT}"
        [[ -n "${_ACTUAL}" ]] && echo -e "      ${_ACTUAL}"
    else
        COUNT_FAIL=$((COUNT_FAIL + 1))
        echo -e "  ${RED}✗${NC} ${_LINE} ${_WHAT}"
        echo -e "      ${RED}beobachtet:${NC} ${_ACTUAL}"
    fi
}

# Prüft den HTTP-Statuscode einer URL.
checkStatus() {
    local -r _LINE="$1"
    local -r _WHAT="$2"
    local -r _URL="$3"
    local -r _EXPECTED="$4"
    local _ACTUAL

    _ACTUAL="$(curl -s -o /dev/null -w "%{http_code}" --max-time 90 "${_URL}")"
    if [[ "${_ACTUAL}" == "${_EXPECTED}" ]]; then
        report "${_LINE}" "${_WHAT}" true "HTTP ${_ACTUAL}"
    else
        report "${_LINE}" "${_WHAT}" false "HTTP ${_ACTUAL} statt ${_EXPECTED}"
    fi
}

# #3 — Der Antwortkörper nennt die ausgefallenen Quellen.
checkAusfallImKoerper() {
    local _DETAIL
    _DETAIL="$(curl -s --max-time 90 "${BASE_URL}/quote/${ISIN_BEKANNT}" \
        | "${JQ}" -r '.detail // ""')"

    if [[ "${_DETAIL}" == *"openfigi"* && "${_DETAIL}" == *"yahoo"* ]]; then
        report "#3 " "Antwortkörper nennt die ausgefallenen Quellen" true \
            "$(echo "${_DETAIL}" | cut -c1-120)"
    else
        report "#3 " "Antwortkörper nennt die ausgefallenen Quellen" false \
            "detail = '${_DETAIL}'"
    fi
}

# #5 — Die Backend-Suite.
checkTests() {
    local _OUTPUT
    _OUTPUT="$(cd "${PROJECT_ROOT}" && .venv/bin/pytest tests/ -q 2>&1 | tail -1)"
    if [[ "${_OUTPUT}" == *"passed"* && "${_OUTPUT}" != *"failed"* ]]; then
        report "#5 " "Backend-Suite" true "${_OUTPUT}"
    else
        report "#5 " "Backend-Suite" false "${_OUTPUT}"
    fi
}

# Fährt alle maschinell prüfbaren Zeilen aus T-20 durch.
runChecks() {
    checkIfToolIsAvailable "${JQ}"

    echo
    echo -e "${CYAN}▶ T-20 · maschinell prüfbare Zeilen${NC}"
    echo

    echo -e "  ${BLUE}ℹ${NC} Lauf 1 von 2 — mit Netz (Zeile #1)"
    startServer "mit-netz" "offen" || exit 1
    checkStatus "#1 " "Unbekannte ISIN ist ein 404 — beide Quellen haben nachgesehen" \
        "${BASE_URL}/quote/${ISIN_UNBEKANNT}" "404"
    checkStatus "#1b" "Bekannte ISIN geht mit Netz durch" \
        "${BASE_URL}/quote/${ISIN_BEKANNT}" "200"
    stopServer

    echo
    echo -e "  ${BLUE}ℹ${NC} Lauf 2 von 2 — Netz abgeschnitten (Zeilen #2, #3)"
    startServer "ohne-netz" "blockiert" || exit 1
    checkStatus "#2 " "Dieselbe ISIN wird zu 502, nicht zu 404" \
        "${BASE_URL}/quote/${ISIN_BEKANNT}" "502"
    checkAusfallImKoerper
    stopServer

    echo
    checkTests

    echo
    if [[ ${COUNT_FAIL} -eq 0 ]]; then
        echo -e "  ${GREEN}✓ ${COUNT_OK} Checks bestanden, keine Fehler${NC}"
    else
        echo -e "  ${RED}✗ ${COUNT_FAIL} von $((COUNT_OK + COUNT_FAIL)) Checks fehlgeschlagen${NC}"
    fi
    echo
    return "${COUNT_FAIL}"
}

trap cleanup EXIT

if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -k|--keep-log) KEEP_LOG=true; shift ;;
        -r|--run)      shift; runChecks; exit $? ;;
        -i|--info)     showInfo; exit 0 ;;
        -h|--help)     usage; exit 0 ;;
        *) echo -e "${RED}Unbekannte Option: $1${NC}" >&2; usage; exit 1 ;;
    esac
done

usage
