#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-17-smoke.sh — Die maschinell prüfbaren Zeilen aus Ticket T-17 abarbeiten
#
# Startet einen eigenen Backend-Prozess auf einem eigenen Port mit einer
# frischen, temporären Datenbank. Die Arbeits-Datenbank bleibt unberührt.
#
# Drei Läufe mit verschiedener Vorgabebörse, weil die Zeilen verschiedene
# Auflösungen brauchen:
#
#   XPAR  → #1, #2   LVMH kommt nur über Paris als MC.PA herein, und nur dort
#                    meldet yfinance die kanadische Zweitnotierung dagegen.
#   XTSE  → #3       Die Royal-Bank-Papiere liegen in Toronto.
#   XETR  → #4       Der ETF muss über die ISIN hereinkommen, sonst läuft die
#                    justETF-Anreicherung nicht an.
#
# `CACHE_TTL_HOURS=0` ist die Bedingung für #4: Nur wenn der zweite Abruf live
# geht, während die Metadaten-TTL noch steht, entsteht die unvollständige
# Antwort, um die es geht.
#
# Braucht Netz — OpenFIGI, Yahoo und justETF werden echt gefragt.
#
# Verwendung:
#   ./_tickets/T-17-smoke.sh --run
#   ./_tickets/T-17-smoke.sh --run --keep-log
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
# Überschreibbar, falls der Port belegt ist: `PORT=8790 ./T-17-smoke.sh --run`
readonly PORT="${PORT:-8766}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Papiere, an denen die Zeilen hängen. Kommentar sagt, was sie beweisen sollen.
readonly ISIN_LVMH="FR0000121014"    # yfinance meldet dazu CA50244Q1037 (DR)
readonly ISIN_RBC_VZ="CA78012H5675"  # Vorzugsaktie; FIGI-Ticker ist kein Symbol
readonly ISIN_RBC_ST="CA7800871021"  # Stammaktie; löst sauber auf RY.TO auf
readonly ISIN_ETF="IE00B4L5Y983"     # justETF ist zuständig — liefert ein TER
readonly SYMBOL_ETF="EUNL.DE"        # dasselbe Papier an Xetra

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
    usageLine "-k | --keep-log  " "Server-Logs nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Mit Log:       ${GREEN}${APPNAME} --run --keep-log${NC}"
    echo
    echo -e "    Zeile ${YELLOW}#6${NC} (${GREEN}make test${NC}) prüft dieses Script mit,"
    echo -e "    die übrigen Zeilen laufen gegen einen echten Server."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port        ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Papiere     ${NC} = ${BLUE}${ISIN_LVMH}, ${ISIN_RBC_VZ}, ${ISIN_RBC_ST}, ${SYMBOL_ETF}${NC}"
    echo
}

# Beendet den selbst gestarteten Server, lässt das Arbeitsverzeichnis stehen.
#
# **Nur die eigene PID.** Eine frühere Fassung räumte zusätzlich alles ab, was
# auf dem Port lauschte — „Gürtel und Hosenträger". Das ist keine Absicherung,
# sondern ein Risiko: Ist der Port belegt, gehört der Prozess dort jemand
# anderem, womöglich Mikes laufendem Entwicklungsserver. Ein Prüf-Script darf
# nichts beenden, was es nicht selbst gestartet hat. Gegen einen belegten Port
# hilft `requirePortIsFree`, nicht der Holzhammer danach.
stopServer() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null
        wait "${SERVER_PID}" 2>/dev/null
    fi
    SERVER_PID=""
}

# Bricht ab, wenn auf dem Port schon jemand lauscht.
#
# Ohne diese Prüfung könnte der Health-Check unten den **fremden** Server für
# den eigenen halten: Er fragt nur, ob `${BASE_URL}/health` antwortet, und das
# tut auch ein Server, den jemand anderes gestartet hat. Der Lauf liefe dann
# gegen die falsche Instanz und mit der falschen Datenbank.
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
#   $1 - MIC der Vorgabebörse (z.B. 'XPAR')
#   $2 - Kennung des Laufs, benennt DB und Log (z.B. 'paris')
#
# Returns:
#   0 wenn der Server erreichbar ist, 1 bei Zeitüberschreitung
startServer() {
    local -r _MIC="$1"
    local -r _RUN="$2"

    requirePortIsFree || return 1
    [[ -z "${WORKDIR}" ]] && WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/${_RUN}.log"

    # CACHE_TTL_HOURS=0  → jeder Abruf geht live (Voraussetzung für #4)
    # METADATA_TTL_DAYS  → Vorgabe, damit justETF beim zweiten Abruf ausbleibt
    # REFRESH_INTERVAL_HOURS hoch → der Scheduler funkt nicht dazwischen
    # STATIC_DIR ins Leere → kein Dashboard-Mount nötig
    #
    # `exec` ist hier Pflicht, kein Stil: Ohne es wäre `$!` die PID der
    # Subshell, und ein `kill` darauf beendet die Hülle, während uvicorn als
    # Waise weiterläuft und den Port belegt.
    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${WORKDIR}/${_RUN}.db" \
            CACHE_TTL_HOURS=0 \
            METADATA_TTL_DAYS=7 \
            REFRESH_INTERVAL_HOURS=24 \
            DEFAULT_EXCHANGE="${_MIC}" \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL}, Vorgabebörse ${_MIC} (PID ${SERVER_PID})"
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
#   $1 - Zeilen-Kennung aus T-17, z.B. '#2'
#   $2 - Was geprüft wurde
#   $3 - true wenn bestanden
#   $4 - beobachteter Wert (für die Ausgabe)
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
#   $1 - Zeilen-Kennung, $2 - Beschreibung, $3 - URL, $4 - jq-Filter,
#   $5 - erwarteter Wert, $6 - Vergleichsart ('eq' exakt | 'not' ungleich)
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

# Prüft den HTTP-Statuscode einer URL.
#
# Params:
#   $1 - Zeilen-Kennung, $2 - Beschreibung, $3 - URL, $4 - erwarteter Code
checkStatus() {
    local -r _LINE="$1"
    local -r _WHAT="$2"
    local -r _URL="$3"
    local -r _EXPECTED="$4"
    local _ACTUAL

    _ACTUAL="$(curl -s -o /dev/null -w "%{http_code}" --max-time 60 "${_URL}")"
    if [[ "${_ACTUAL}" == "${_EXPECTED}" ]]; then
        report "${_LINE}" "${_WHAT}" true "HTTP ${_ACTUAL}"
    else
        report "${_LINE}" "${_WHAT}" false "HTTP ${_ACTUAL} statt ${_EXPECTED}"
    fi
}

# #1 — Die eingegebene ISIN muss die gespeicherte sein.
#
# yfinance meldet zu `MC.PA` die kanadische Zweitnotierung `CA50244Q1037`.
# Vorher gewann sie (`raw.isin or resolved.isin`) und landete in der Datenbank:
# richtiger Name, falsche Gattung, beim Draufschauen unauffällig.
checkInputIsinWins() {
    checkField "#1a" "Antwort trägt die eingegebene ISIN" \
        "${BASE_URL}/quote/${ISIN_LVMH}" ".isin" "${ISIN_LVMH}" "eq"
    checkField "#1b" "Gespeichert ist dieselbe ISIN" \
        "${BASE_URL}/instruments" \
        ".[] | select(.isin==\"${ISIN_LVMH}\") | .isin" "${ISIN_LVMH}" "eq"
}

# #2 — Die Abweichung gehört ins Protokoll, nicht ins Schweigen.
checkDeviationIsLogged() {
    local _LINE
    _LINE="$(grep -m1 "isin_mismatch" "${LOGFILE}" 2>/dev/null)"

    if [[ -n "${_LINE}" ]]; then
        report "#2 " "Abweichende Anbieter-ISIN wird protokolliert" true \
            "$(echo "${_LINE}" | cut -c1-120)"
    else
        report "#2 " "Abweichende Anbieter-ISIN wird protokolliert" false \
            "kein 'isin_mismatch' in ${LOGFILE}"
    fi
}

# #3 — Ein FIGI-Ticker, der kein Symbol sein kann, darf nicht durchgereicht
# werden. Vorher entstand daraus `RY V3.65 PERP BB.TO`; yfinance antwortet
# darauf 404, und weil OpenFIGI „getroffen" hatte, kam der Yahoo-Fallback nie
# an die Reihe.
#
# Die Vorzugsaktie bleibt unauflösbar — für sie liefert keine der beiden
# Quellen ein brauchbares Symbol. Geprüft wird, dass sie sauber durchfällt und
# kein unbrauchbares Symbol im Bestand hinterlässt.
checkUnusableTicker() {
    checkStatus "#3a" "Vorzugsaktie fällt sauber durch statt an einem Nicht-Symbol zu hängen" \
        "${BASE_URL}/quote/${ISIN_RBC_VZ}" "404"

    local _WITH_SPACES
    _WITH_SPACES="$(curl -s --max-time 60 "${BASE_URL}/instruments" \
        | "${JQ}" -r '[.[] | select(.symbol | test(" "))] | length')"
    if [[ "${_WITH_SPACES}" == "0" ]]; then
        report "#3b" "Kein Bloomberg-Bezeichner im Bestand" true \
            "Symbole mit Leerzeichen: 0"
    else
        report "#3b" "Kein Bloomberg-Bezeichner im Bestand" false \
            "Symbole mit Leerzeichen: ${_WITH_SPACES}"
    fi

    checkField "#3c" "Die Stammaktie löst weiterhin auf" \
        "${BASE_URL}/quote/${ISIN_RBC_ST}" ".symbol" "RY.TO" "eq"
}

# #4 — Die Antwort muss den gespeicherten Stand tragen.
#
# Erster Abruf holt alles inklusive justETF. Der zweite geht wegen
# `CACHE_TTL_HOURS=0` wieder live, die Metadaten-TTL steht aber noch — justETF
# wird zu Recht nicht gefragt, die frische Antwort hat deshalb keine ETF-Felder.
# Vorher wurde genau die an den Client durchgereicht: `ter` null in der Antwort,
# 0.2 in der Datenbank.
#
# Über die **ISIN**, nicht über das Symbol: Zu `EUNL.DE` nennt yfinance keine
# ISIN, und ohne sie läuft die justETF-Anreicherung gar nicht erst an
# (`enrich_etf and isin` in `_build`). Der erste Abruf hätte dann nichts, was
# der zweite verlieren könnte — die Zeile wäre grün, ohne etwas zu zeigen.
checkResponseKeepsStoredState() {
    local _TER_FIRST _TER_SECOND _TER_DB

    _TER_FIRST="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_ETF}" \
        | "${JQ}" -r '.ter')"
    _TER_SECOND="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_ETF}" \
        | "${JQ}" -r '.ter')"
    _TER_DB="$(curl -s --max-time 60 "${BASE_URL}/instruments" \
        | "${JQ}" -r ".[] | select(.symbol==\"${SYMBOL_ETF}\") | .ter")"

    if [[ "${_TER_FIRST}" == "null" ]]; then
        report "#4 " "Zweiter Live-Abruf zeigt denselben Stand wie die Datenbank" false \
            "schon der erste Abruf liefert kein TER — justETF nicht erreichbar, Zeile nicht aussagekräftig"
        return
    fi

    if [[ "${_TER_SECOND}" == "${_TER_DB}" && "${_TER_SECOND}" != "null" ]]; then
        report "#4 " "Zweiter Live-Abruf zeigt denselben Stand wie die Datenbank" true \
            "ter: 1. Abruf=${_TER_FIRST}, 2. Abruf=${_TER_SECOND}, DB=${_TER_DB}"
    else
        report "#4 " "Zweiter Live-Abruf zeigt denselben Stand wie die Datenbank" false \
            "ter: 1. Abruf=${_TER_FIRST}, 2. Abruf=${_TER_SECOND}, DB=${_TER_DB} — der Client sieht eine Lücke, die es nicht gibt"
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

# Fährt alle maschinell prüfbaren Zeilen aus T-17 durch.
runChecks() {
    checkIfToolIsAvailable "${JQ}"

    echo
    echo -e "${CYAN}▶ T-17 · maschinell prüfbare Zeilen${NC}"
    echo

    echo -e "  ${BLUE}ℹ${NC} Lauf 1 von 3 — Vorgabebörse Paris (Zeilen #1, #2)"
    startServer "XPAR" "paris" || exit 1
    checkInputIsinWins
    checkDeviationIsLogged
    stopServer

    echo
    echo -e "  ${BLUE}ℹ${NC} Lauf 2 von 3 — Vorgabebörse Toronto (Zeile #3)"
    startServer "XTSE" "toronto" || exit 1
    checkUnusableTicker
    stopServer

    echo
    echo -e "  ${BLUE}ℹ${NC} Lauf 3 von 3 — Vorgabebörse Xetra (Zeile #4)"
    startServer "XETR" "xetra" || exit 1
    checkResponseKeepsStoredState
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
