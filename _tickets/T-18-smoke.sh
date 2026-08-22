#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-18-smoke.sh — Die maschinell prüfbaren Zeilen aus Ticket T-18 abarbeiten
#
# Startet einen eigenen Backend-Prozess auf einem eigenen Port mit einer
# frischen, temporären Datenbank. Die Arbeits-Datenbank bleibt unberührt.
#
# Ein Lauf mit Vorgabebörse `XETR` — genau darum geht es: Die Papiere haben
# dort kein Listing, und die Kaskade muss auf ihre Heimatbörse ausweichen.
#
# Braucht Netz — OpenFIGI, Yahoo und justETF werden echt gefragt.
#
# Verwendung:
#   ./_tickets/T-18-smoke.sh --run
#   ./_tickets/T-18-smoke.sh --run --keep-log
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep-log   Server-Log nach dem Lauf stehen lassen
#   -i | --info       Einstellungen anzeigen
#   -h | --help       Diese Hilfe anzeigen
#------------------------------------------------------------------------------
set -uo pipefail

BASH_LIBS="${BASH_LIBS:-$(cd "$(dirname "$0")/../.libs/BashLib/src" && pwd)}"

if [[ "${__COLORS_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/colors.lib.sh"; fi
if [[ "${__TOOLS_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/tools.lib.sh";  fi
if [[ "${__APPS_LIB__:=""}"   == "" ]]; then . "${BASH_LIBS}/apps.lib.sh";   fi

readonly APPNAME="$(basename "$0")"
readonly PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Überschreibbar, falls der Port belegt ist: `PORT=8790 ./T-18-smoke.sh --run`
readonly PORT="${PORT:-8767}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Papiere, an denen die Zeilen hängen. Kommentar sagt, was sie beweisen sollen.
readonly ISIN_RBC="CA7800871021"     # kein Xetra-Listing, Toronto schon
readonly ISIN_TOYOTA="JP3633400001"  # dito für Tokio
readonly ISIN_ETF_EU="IE00B4L5Y983"  # muss an Xetra bleiben
readonly SYMBOL_CA="XIC.TO"          # yfinance nennt dazu keine ISIN

# Nicht `PASSED`/`FAILED`: `FAILED` ist in colors.lib.sh als Farbe readonly.
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
    usageLine "-k | --keep-log  " "Server-Log nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Mit Log:       ${GREEN}${APPNAME} --run --keep-log${NC}"
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port        ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Papiere     ${NC} = ${BLUE}${ISIN_RBC}, ${ISIN_TOYOTA}, ${ISIN_ETF_EU}, ${SYMBOL_CA}${NC}"
    echo
}

# Bricht ab, wenn auf dem Port schon jemand lauscht.
#
# Ohne diese Prüfung könnte der Health-Check den **fremden** Server für den
# eigenen halten — der Lauf liefe gegen die falsche Datenbank.
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

# Räumt Server und Arbeitsverzeichnis ab. Wird per trap aufgerufen.
#
# **Nur die eigene PID** — ein Prüf-Script beendet nichts, was es nicht selbst
# gestartet hat.
cleanup() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null
        wait "${SERVER_PID}" 2>/dev/null
    fi
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP_LOG}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Server-Log: ${LOGFILE}"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Startet das Backend auf einer frischen DB und wartet, bis es antwortet.
#
# Returns:
#   0 wenn der Server erreichbar ist, 1 bei Zeitüberschreitung
startServer() {
    requirePortIsFree || return 1
    WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/server.log"
    echo -e "  ${BLUE}ℹ${NC} Frische DB unter ${WORKDIR}"

    # DEFAULT_EXCHANGE=XETR ist der Kern: Keines der geprüften Papiere hat dort
    # ein Listing. STRICT_EXCHANGE bleibt aus — sonst gäbe es keine Kaskade.
    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${WORKDIR}/t18.db" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            DEFAULT_EXCHANGE=XETR \
            STRICT_EXCHANGE=false \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL}, Vorgabebörse XETR (PID ${SERVER_PID})"
            return 0
        fi
        sleep 0.5
    done
    echo -e "  ${RED}✗${NC} Backend startet nicht — Log:"
    tail -20 "${LOGFILE}"
    return 1
}

# Meldet das Ergebnis eines Checks und zählt mit.
#
# Params:
#   $1 - Zeilen-Kennung aus T-18, $2 - Beschreibung, $3 - true wenn bestanden,
#   $4 - beobachteter Wert
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

# Prüft ein einzelnes JSON-Feld einer Antwort gegen einen erwarteten Wert.
#
# Params:
#   $1 - Kennung, $2 - Beschreibung, $3 - URL, $4 - jq-Filter, $5 - erwartet,
#   $6 - Vergleichsart ('eq' | 'not')
checkField() {
    local -r _LINE="$1"
    local -r _WHAT="$2"
    local -r _URL="$3"
    local -r _FILTER="$4"
    local -r _EXPECTED="$5"
    local -r _MODE="${6:-eq}"
    local _ACTUAL

    _ACTUAL="$(curl -s --max-time 60 "${_URL}" | "${JQ}" -r "${_FILTER}" 2>/dev/null)"

    local _OK=false
    case "${_MODE}" in
        eq)  [[ "${_ACTUAL}" == "${_EXPECTED}" ]] && _OK=true ;;
        not) [[ "${_ACTUAL}" != "${_EXPECTED}" ]] && _OK=true ;;
    esac

    if [[ "${_OK}" == true ]]; then
        report "${_LINE}" "${_WHAT}" true "${_FILTER} = ${_ACTUAL}"
    else
        report "${_LINE}" "${_WHAT}" false "${_FILTER} = '${_ACTUAL}' (erwartet ${_MODE} '${_EXPECTED}')"
    fi
}

# #4 — Das Ausweichen auf die Heimatbörse gehört ins Protokoll.
checkAusweichenImLog() {
    local _LINE
    _LINE="$(grep -m1 "resolve_home_exchange" "${LOGFILE}" 2>/dev/null)"

    if [[ -n "${_LINE}" ]]; then
        report "#4 " "Ausweichen auf die Heimatbörse wird protokolliert" true \
            "$(echo "${_LINE}" | cut -c1-130)"
    else
        report "#4 " "Ausweichen auf die Heimatbörse wird protokolliert" false \
            "kein 'resolve_home_exchange' in ${LOGFILE}"
    fi
}

# #6 — Die Backend-Suite.
checkTests() {
    local _OUTPUT
    _OUTPUT="$(cd "${PROJECT_ROOT}" && .venv/bin/pytest tests/ -q 2>&1 | tail -1)"
    if [[ "${_OUTPUT}" == *"passed"* && "${_OUTPUT}" != *"failed"* ]]; then
        report "#6 " "Backend-Suite" true "${_OUTPUT}"
    else
        report "#6 " "Backend-Suite" false "${_OUTPUT}"
    fi
}

# Fährt alle maschinell prüfbaren Zeilen aus T-18 durch.
runChecks() {
    checkIfToolIsAvailable "${JQ}"

    echo
    echo -e "${CYAN}▶ T-18 · maschinell prüfbare Zeilen${NC}"
    echo

    startServer || exit 1
    echo

    checkField "#1a" "Kanadisches Papier wird über die Heimatbörse aufgelöst" \
        "${BASE_URL}/quote/${ISIN_RBC}" ".symbol" "RY.TO" "eq"
    checkField "#1b" "und notiert in CAD" \
        "${BASE_URL}/quote/${ISIN_RBC}" ".currency" "CAD" "eq"

    checkField "#2 " "Japanisches Papier landet in Tokio statt im Fehlschlag" \
        "${BASE_URL}/quote/${ISIN_TOYOTA}" ".symbol" "7203.T" "eq"

    checkField "#3a" "Europäischer ETF bleibt an der bevorzugten Börse" \
        "${BASE_URL}/quote/${ISIN_ETF_EU}" ".symbol" "EUNL.DE" "eq"
    checkField "#3b" "und in EUR" \
        "${BASE_URL}/quote/${ISIN_ETF_EU}" ".currency" "EUR" "eq"

    checkAusweichenImLog

    checkField "#5 " "Kanadischer ETF bekommt einen Anbieter, obwohl die ISIN fehlt" \
        "${BASE_URL}/quote?symbol=${SYMBOL_CA}" ".provider" "null" "not"

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
