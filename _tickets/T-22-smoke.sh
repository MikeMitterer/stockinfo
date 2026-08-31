#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-22-smoke.sh — Verify #1/#2/#3/#4/#4b/#5: Quellen konfigurieren statt verdrahten
#
# Die Verify-Zeilen von T-22 sagen alle „…, Neustart". Das ist der Kern: Eine
# Konfiguration, die erst nach einem Neustart gilt, muss auch **über einen
# Neustart** geprüft werden. Dieses Script startet den Server deshalb mehrfach
# über demselben Daten-Volume, mit je einer anderen `sources.yaml`.
#
# **Kein Netz nötig.** Geprüft wird, welche Kette entsteht — nicht, was die
# Quellen liefern. Die Arbeits-Datenbank wird nicht angefasst.
#
# Sechs Fragen, die nur hier zusammen beantwortet werden:
#
#   1. Gilt eine vertauschte Reihenfolge? (`#1`)
#   2. Bleibt OpenFIGI ohne Key **aktiv**? (`#2`)
#   3. Startet die App ohne Datei mit Vorgaben? (`#3`)
#   4. Nennt ein Tippfehler den Namen **und** die verfügbaren? (`#4`)
#   5. Fällt die unbrauchbare Quelle aus, ohne den Start zu kosten? (`#4b`)
#   6. Trägt die Datei Verweise statt Schlüsseln? (`#5`)
#
# **`#2b` aus T-22 läuft hier nicht**, und das ist keine Lücke, sondern der
# Stand: Der Check verlangt eine Quelle mit **pflichtigem** Schlüssel, und
# keine der gebauten deklariert einen (`SourceSpec.needs` ist überall leer).
# Die Zusage selbst prüfen die Unit-Tests zu `is_configured`; sobald eine
# Quelle mit Pflichtangabe entsteht, gehört sie hierher zurück.
#
# Die erwarteten Kennungen stehen in `EXPECTED_IDS`: Eine Zahl allein erkennt
# nicht, wenn ein zugesagter Check durch einen anderen ersetzt wird.
#
# Verwendung:
#   ./_tickets/T-22-smoke.sh --run
#   PORT=8792 ./_tickets/T-22-smoke.sh --run
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep-log   Server-Logs nach dem Lauf stehen lassen
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
readonly PORT="${PORT:-8774}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Welche Checks dieser Lauf **erwartet** — als Kennungen, nicht als Zahl.
#
# Die Zahl allein verhindert nur, dass ein unterwegs abgebrochener Lauf mit
# `COUNT_FAIL=0` grün endet. Sie sagt nichts darüber, ob die gelaufenen Checks
# **dieselben** sind: Wird einer ersetzt, stimmt die Summe weiter.
readonly EXPECTED_IDS="#1 #2 #3 #4 #4b #5"

# Was tatsächlich gelaufen ist — von `report` gefüllt, am Ende verglichen.
SEEN_IDS=""

COUNT_OK=0
COUNT_FAIL=0
SERVER_PID=""
WORKDIR=""
LOGFILE=""
DB_PATH=""
KEEP_LOG=false

# Zeigt die Verwendungshinweise an.
usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Checks ausführen (eigener Server, temporäres Volume)"
    usageLine "-k | --keep-log  " "Server-Logs nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Anderer Port:  ${GREEN}PORT=8792 ${APPNAME} --run${NC}"
    echo
    echo -e "    Dieser Lauf braucht ${GREEN}kein Netz${NC} — geprüft wird, welche"
    echo -e "    Kette entsteht, nicht was die Quellen liefern."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port  ${NC} = ${BLUE}${PORT}${NC}"
    echo
}

# Bricht ab, wenn auf dem Port schon jemand lauscht.
requirePortIsFree() {
    local _OCCUPANT
    _OCCUPANT="$(lsof -ti ":${PORT}" 2>/dev/null)"
    [[ -z "${_OCCUPANT}" ]] && return 0

    echo -e "  ${RED}✗${NC} Port ${PORT} ist belegt (PID ${_OCCUPANT//$'\n'/, })."
    echo -e "      Dieses Script beendet nichts, was es nicht selbst gestartet hat."
    echo -e "      Anderen Port wählen: ${GREEN}PORT=8792 ${APPNAME} --run${NC}"
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
            echo -e "  ${BLUE}ℹ${NC} Server-Logs und Volume: ${WORKDIR}"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Legt das temporäre Daten-Volume an.
prepareVolume() {
    WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/sources.log"
    DB_PATH="${WORKDIR}/stockinfo.db"
    (
        cd "${PROJECT_ROOT}" || exit 1
        "${VENV_PY}" -c "from app.db import init_db; init_db('${DB_PATH}')"
    ) || { echo -e "  ${RED}✗${NC} Schema konnte nicht angelegt werden"; return 1; }
    echo -e "  ${GREEN}✓${NC} Volume angelegt"
    return 0
}

# Schreibt eine `sources.yaml` neben die Datenbank — oder entfernt sie.
#
# Params:
#   $1 - Inhalt, oder "" zum Löschen
writeConfig() {
    local -r _CONTENT="$1"
    if [[ -z "${_CONTENT}" ]]; then
        rm -f "${WORKDIR}/sources.yaml"
        return 0
    fi
    printf '%s\n' "${_CONTENT}" > "${WORKDIR}/sources.yaml"
}

# Startet das Backend über dem Volume.
#
# Returns:
#   0 wenn der Server antwortet, 1 sonst
startServer() {
    requirePortIsFree || return 1
    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${DB_PATH}" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" >> "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
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

    # Die Kennung ohne Auffüll-Leerzeichen — `report` bekommt sie als `"#4 "`,
    # damit die Spalten stehen.
    SEEN_IDS="${SEEN_IDS}${SEEN_IDS:+ }${_LINE// /}"

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

# Die Namen einer Rolle aus `/sources`, in Reihenfolge.
#
# Params:
#   $1 - Rolle
chainOf() {
    curl -s --max-time 30 "${BASE_URL}/sources" | "${VENV_PY}" -c "
import json, sys
data = json.load(sys.stdin)
print(','.join(r['name'] for r in data['sources'] if r['role'] == '$1'))
" 2>/dev/null
}

# `#1`: Eine vertauschte Reihenfolge gilt.
checkOrder() {
    writeConfig "resolvers: [yahoo-search, openfigi]"
    startServer || return 1
    local -r _CHAIN="$(chainOf resolvers)"
    stopServer

    report "#1 " "die vertauschte Reihenfolge gilt nach dem Neustart" \
        "$([[ "${_CHAIN}" == "yahoo-search,openfigi" ]] && echo true || echo false)" \
        "resolvers: ${_CHAIN}"
}

# `#2`: OpenFIGI bleibt ohne Key aktiv.
checkOptionalKey() {
    writeConfig "resolvers: [openfigi]
providers:
  openfigi:
    api_key: \${GIBT_ES_NICHT}"
    startServer || return 1
    local -r _CONFIGURED="$(curl -s --max-time 30 "${BASE_URL}/sources" | "${VENV_PY}" -c "
import json, sys
data = json.load(sys.stdin)
print(next(r['configured'] for r in data['sources'] if r['name'] == 'openfigi'))
" 2>/dev/null)"
    stopServer

    report "#2 " "OpenFIGI bleibt ohne Key aktiv — der Key hebt nur das Limit" \
        "$([[ "${_CONFIGURED}" == "True" ]] && echo true || echo false)" \
        "configured=${_CONFIGURED}"
}

# `#3`: Ohne Datei gelten die Vorgaben.
checkDefaults() {
    writeConfig ""
    startServer || return 1
    local -r _CHAIN="$(chainOf resolvers)"
    local -r _PATH="$(curl -s --max-time 30 "${BASE_URL}/sources" | "${VENV_PY}" -c "
import json, sys
print(json.load(sys.stdin)['config_path'])" 2>/dev/null)"
    stopServer

    report "#3 " "ohne Datei startet die App mit Vorgaben" \
        "$([[ "${_CHAIN}" == "openfigi,yahoo-search" && "${_PATH}" == "None" ]] \
            && echo true || echo false)" \
        "resolvers: ${_CHAIN}, config_path: ${_PATH}"
}

# Ein Feld einer Quelle aus `/sources`.
#
# Params:
#   $1 - Name der Quelle
#   $2 - Feldname, z.B. `reason` oder `configured`
fieldOf() {
    curl -s --max-time 30 "${BASE_URL}/sources" | "${VENV_PY}" -c "
import json, sys
data = json.load(sys.stdin)
print(next((str(r['$2']) for r in data['sources'] if r['name'] == '$1'), ''))
" 2>/dev/null
}

# `#4`: Ein Tippfehler nennt Namen und Alternativen — in `/sources`, nicht im
# Log: Ein unbekannter Name kostet **seine** Quelle, nicht den Start, also gibt
# es keinen Abbruch, den ein Protokoll festhalten könnte.
checkTypo() {
    writeConfig "resolvers: [openfgi]"
    startServer || return 1
    local -r _REASON="$(fieldOf openfgi reason)"
    local -r _CONFIGURED="$(fieldOf openfgi configured)"
    local -r _HEALTH="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${BASE_URL}/health")"
    stopServer

    report "#4 " "der Tippfehler nennt sich selbst und die verfügbaren Namen" \
        "$([[ "${_REASON}" == *"openfgi"* && "${_REASON}" == *"openfigi"* ]] \
            && echo true || echo false)" \
        "${_REASON:-kein Grund in /sources}"

    # **Zwei Aussagen, und beide gehören zusammen.** Der Name allein sagt nur,
    # dass die Datei gelesen wurde; erst `configured: false` sagt, dass die
    # Quelle nicht gebaut wurde, und erst die lebende Route sagt, dass es den
    # Start trotzdem nicht gekostet hat. Ohne die erste wäre ein
    # stillschweigend arbeitender Tippfehler grün, ohne die zweite ein
    # abgestürzter Server.
    report "#4b" "die Quelle fällt aus, der Start überlebt sie" \
        "$([[ "${_CONFIGURED}" == "False" && "${_HEALTH}" == "200" ]] \
            && echo true || echo false)" \
        "configured=${_CONFIGURED:-<keine Angabe>}, GET /health → ${_HEALTH}"
}

# `#5`: Die Datei trägt Verweise statt Schlüssel.
checkNoSecrets() {
    writeConfig "resolvers: [openfigi]
providers:
  openfigi:
    api_key: \${OPENFIGI_API_KEY}"
    local -r _CONTENT="$(cat "${WORKDIR}/sources.yaml")"

    report "#5 " "die Datei ist in ein Issue kopierbar — nur Verweise" \
        "$([[ "${_CONTENT}" == *'${OPENFIGI_API_KEY}'* ]] && echo true || echo false)" \
        "$(printf '%s' "${_CONTENT}" | tail -1 | sed 's/^ *//')"
}

# Führt alle Checks aus.
runChecks() {
    trap cleanup EXIT INT TERM

    echo
    echo -e "${LIGHT_BLUE}T-22 — Quellen konfigurieren statt verdrahten${NC}"
    echo

    prepareVolume || return 1

    # **Ein abgebrochener Check ist ein Fehler, kein übersprungener Schritt.**
    # Die Prüffunktionen kehren mit 1 zurück, wenn der Server nicht startet —
    # ohne diese Auswertung liefe die Schleife weiter, `COUNT_FAIL` bliebe 0,
    # und der Lauf meldete sich als bestanden.
    local _CHECK
    for _CHECK in checkOrder checkOptionalKey checkDefaults checkTypo checkNoSecrets; do
        if ! "${_CHECK}"; then
            COUNT_FAIL=$((COUNT_FAIL + 1))
            echo -e "  ${RED}✗${NC} ${_CHECK} abgebrochen — der Lauf gilt als nicht bestanden"
        fi
    done

    echo
    # **Die Schlussmarke, und sie prüft die Identität statt der Anzahl.** Ein
    # Lauf, der unterwegs abbricht, erreicht sie nicht — und einer, der
    # einen Check gegen einen anderen tauscht, kommt an ihr nicht vorbei.
    if [[ "${COUNT_FAIL}" -eq 0 && "${SEEN_IDS}" == "${EXPECTED_IDS}" ]]; then
        echo -e "  ${GREEN}✓ ${COUNT_OK} Checks bestanden, keine Fehler${NC}"
        echo -e "      ${SEEN_IDS}"
        echo
        return 0
    fi
    if [[ "${COUNT_FAIL}" -eq 0 ]]; then
        echo -e "  ${RED}✗ es liefen andere Checks als zugesagt${NC}"
        echo -e "      erwartet:  ${EXPECTED_IDS}"
        echo -e "      gelaufen:  ${SEEN_IDS:-<keiner>}"
        echo -e "      Der Lauf ist unvollständig — das ist kein bestandener Lauf."
        echo
        return 1
    fi
    echo -e "  ${RED}✗ ${COUNT_FAIL} von $((COUNT_OK + COUNT_FAIL)) Checks fehlgeschlagen${NC}"
    echo
    return 1
}

main() {
    [[ $# -eq 0 ]] && { usage; exit 0; }

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -r|--run)      RUN=true ;;
            -k|--keep-log) KEEP_LOG=true ;;
            -i|--info)     showInfo; exit 0 ;;
            -h|--help)     usage; exit 0 ;;
            *)             echo -e "${RED}Unbekannte Option: $1${NC}"; usage; exit 1 ;;
        esac
        shift
    done

    [[ "${RUN:-false}" == true ]] && { runChecks; exit $?; }
    usage
}

main "$@"
