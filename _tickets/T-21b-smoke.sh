#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-21b-smoke.sh — Verify #5: Ein neu aufgenommenes Papier bringt seine
#                  Identität mit
#
# Das Gegenstück zu `T-21-smoke.sh`: Dort wird ein **gewachsener Bestand**
# migriert, hier entsteht ein **Neuzugang** — auf einer frischen, temporären
# Datenbank, über den echten HTTP-Weg, mit echten Auflösungen.
#
# Deshalb braucht dieser Lauf **Netz**. Ein Papier anzulegen heißt, es
# aufzulösen; ohne OpenFIGI und Yahoo gibt es nichts zu prüfen. Bleibt das
# Netz weg, meldet der Lauf das und gilt als **nicht geprüft** — nicht als
# grün.
#
# Zwei Läufe, weil die Kaskade zwei Wege hat:
#
#   1. `DEFAULT_EXCHANGE=XETR` — OpenFIGI beantwortet die Frage, das Symbol
#      trägt ein Suffix, der MIC kommt aus der eigenen Börsentabelle.
#   2. `DEFAULT_EXCHANGE=US`   — der Sammelcode wird übersprungen, Yahoo
#      antwortet, und der MIC kommt aus Yahoos Börsencode. Genau die Lücke,
#      die Teil 1 offenlassen musste.
#
# Der zweite Lauf enthält die **Gegenprobe**: `BRK-B` darf nicht angelegt
# werden. Ein Lauf, in dem alles durchgeht, hat die Regel nicht geprüft.
#
# Die Arbeits-Datenbank wird nicht angefasst — jeder Lauf bekommt seine eigene.
#
# Verwendung:
#   ./_tickets/T-21b-smoke.sh --run
#   PORT=8790 ./_tickets/T-21b-smoke.sh --run
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
readonly PORT="${PORT:-8771}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Ein Papier mit Xetra-Listing — OpenFIGI beantwortet es, das Symbol trägt
# das Suffix `.DE`, der MIC steht in der eigenen Börsentabelle.
readonly ISIN_XETRA="IE00B3RBWM25"        # Vanguard FTSE All-World

# Ein US-Papier ohne Sonderzeichen im Ticker. Hier kommt der MIC aus Yahoos
# Börsencode, weil das Symbol suffixlos ist.
readonly ISIN_US="US0378331005"           # Apple

# Die Gegenprobe: Yahoo schreibt die Anteilsklasse mit Bindestrich (`BRK-B`).
# Dieses Papier darf **nicht** angelegt werden.
readonly ISIN_UNEINDEUTIG="US0846707026"  # Berkshire Hathaway B

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
    usageLine "-r | --run       " "Checks ausführen (eigener Server, temporäre DB)"
    usageLine "-k | --keep-log  " "Server-Logs nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Anderer Port:  ${GREEN}PORT=8790 ${APPNAME} --run${NC}"
    echo
    echo -e "    Dieser Lauf braucht ${YELLOW}Netz${NC} — ein Papier anzulegen heißt, es"
    echo -e "    aufzulösen. Ohne Netz gilt der Lauf als nicht geprüft."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port        ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Xetra-Weg   ${NC} = ${BLUE}${ISIN_XETRA}${NC}"
    echo -e "    ${YELLOW}US-Weg      ${NC} = ${BLUE}${ISIN_US}${NC}"
    echo -e "    ${YELLOW}Gegenprobe  ${NC} = ${BLUE}${ISIN_UNEINDEUTIG}${NC}"
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
            echo -e "  ${BLUE}ℹ${NC} Server-Logs und Datenbanken: ${WORKDIR}"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Startet das Backend auf einer frischen DB und wartet, bis es antwortet.
#
# Params:
#   $1 - Kennung des Laufs (benennt DB und Log)
#   $2 - Wert für DEFAULT_EXCHANGE
#
# Returns:
#   0 wenn der Server erreichbar ist, 1 sonst
startServer() {
    local -r _RUN="$1"
    local -r _EXCHANGE="$2"

    requirePortIsFree || return 1
    [[ -z "${WORKDIR}" ]] && WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/${_RUN}.log"
    DB_PATH="${WORKDIR}/${_RUN}.db"

    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${DB_PATH}" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            DEFAULT_EXCHANGE="${_EXCHANGE}" \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL}, DEFAULT_EXCHANGE=${_EXCHANGE} (PID ${SERVER_PID})"
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

# Liest eine Abfrage aus der temporären Datenbank.
#
# Params:
#   $1 - SQL, das genau eine Zeile liefern soll
#
# Ausgabe:
#   Die Spalten mit '|' getrennt, leere Werte als leerer String.
dbQuery() {
    local -r _SQL="$1"
    "${VENV_PY}" -c '
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
zeilen = ["|".join("" if v is None else str(v) for v in row) for row in con.execute(sys.argv[2])]
print("\n".join(zeilen))
' "${DB_PATH}" "${_SQL}"
}

# Legt ein Papier über den echten HTTP-Weg an.
#
# Params:
#   $1 - ISIN
#
# Ausgabe:
#   Der HTTP-Statuscode.
fetchQuote() {
    curl -s -o /dev/null -w "%{http_code}" --max-time 90 "${BASE_URL}/quote/$1"
}

# #5a/#5b — Der Weg über die eigene Börsentabelle.
#
# Zwei Prüfungen in einer Zeile wären zwei Behauptungen: dass die Zuordnung
# **gesetzt** ist und dass sie **stimmt**. Die zweite rechnet in der
# Gegenrichtung nach — aus `(ticker, mic)` muss sich über die Börsentabelle
# wieder genau das Symbol ergeben, unter dem der Kurs geholt wurde.
checkExchangeTablePath() {
    local _STATUS
    _STATUS="$(fetchQuote "${ISIN_XETRA}")"
    if [[ "${_STATUS}" != "200" ]]; then
        report "#5a" "Xetra-Papier wird angelegt" false \
            "HTTP ${_STATUS} — ohne Netz gibt es hier nichts zu prüfen"
        return 1
    fi

    local _ROW
    _ROW="$(dbQuery "SELECT symbol, ticker, mic, identity_status FROM instruments WHERE isin = '${ISIN_XETRA}'")"
    local _SYMBOL="${_ROW%%|*}"
    local _REST="${_ROW#*|}"
    local _TICKER="${_REST%%|*}"
    _REST="${_REST#*|}"
    local _MIC="${_REST%%|*}"
    local _STATE="${_REST#*|}"

    if [[ -n "${_TICKER}" && "${_MIC}" == "XETR" && "${_STATE}" == "resolved" ]]; then
        report "#5a" "Xetra-Papier bringt ticker und mic mit" true \
            "${_SYMBOL} → ${_TICKER}/${_MIC} (${_STATE})"
    else
        report "#5a" "Xetra-Papier bringt ticker und mic mit" false \
            "${_SYMBOL} → '${_TICKER}'/'${_MIC}' (${_STATE})"
        return 1
    fi

    local _COMPOSED
    _COMPOSED="$("${VENV_PY}" -c '
import sys
sys.path.insert(0, sys.argv[3])
from app.exchanges import EXCHANGES
print(f"{sys.argv[1]}{EXCHANGES[sys.argv[2]].suffix}")
' "${_TICKER}" "${_MIC}" "${PROJECT_ROOT}")"

    if [[ "${_COMPOSED}" == "${_SYMBOL}" ]]; then
        report "#5b" "das Symbol lässt sich aus der Identität zusammensetzen" true \
            "${_TICKER} + Suffix(${_MIC}) = ${_COMPOSED}"
    else
        report "#5b" "das Symbol lässt sich aus der Identität zusammensetzen" false \
            "${_COMPOSED} statt ${_SYMBOL}"
    fi
}

# #5c — Der Weg über Yahoos Börsencode. **Die Lücke aus Teil 1.**
#
# Die Migration konnte `AAPL` nicht zuordnen: Für suffixlose Symbole führt die
# Börsentabelle nur den Sammelcode `US`, und welcher der sechs Handelsplätze
# gilt, steht dort nicht. Die Auflösung weiß es.
checkYahooCodePath() {
    local _STATUS
    _STATUS="$(fetchQuote "${ISIN_US}")"
    if [[ "${_STATUS}" != "200" ]]; then
        report "#5c" "US-Papier bekommt einen echten MIC" false \
            "HTTP ${_STATUS} — ohne Netz gibt es hier nichts zu prüfen"
        return 1
    fi

    local _ROW
    _ROW="$(dbQuery "SELECT symbol, ticker, mic FROM instruments WHERE isin = '${ISIN_US}'")"
    local _SYMBOL="${_ROW%%|*}"
    local _REST="${_ROW#*|}"
    local _TICKER="${_REST%%|*}"
    local _MIC="${_REST#*|}"

    local _IS_REAL
    _IS_REAL="$("${VENV_PY}" -c '
import sys
sys.path.insert(0, sys.argv[2])
from app.exchanges import is_real_mic
print("ja" if is_real_mic(sys.argv[1]) else "nein")
' "${_MIC}" "${PROJECT_ROOT}")"

    if [[ "${_IS_REAL}" == "ja" && "${_TICKER}" == "${_SYMBOL}" ]]; then
        report "#5c" "US-Papier bekommt einen echten MIC statt des Sammelcodes" true \
            "${_SYMBOL} → ${_TICKER}/${_MIC}"
    else
        report "#5c" "US-Papier bekommt einen echten MIC statt des Sammelcodes" false \
            "${_SYMBOL} → '${_TICKER}'/'${_MIC}' (echter MIC: ${_IS_REAL})"
    fi
}

# #5d — Die Gegenprobe. **Ohne sie prüft der Lauf nur die Erfolgsfälle.**
#
# `BRK-B` trägt Yahoos Bindestrich. Der MIC steht fest, der Ticker nicht —
# und ein halb geratenes Papier anzulegen ist schlechter, als den Fall
# sichtbar offen zu lassen. Geprüft wird beides: die Absage nach außen und
# dass **keine Zeile** entstanden ist.
checkAmbiguousIsRejected() {
    local _STATUS
    _STATUS="$(fetchQuote "${ISIN_UNEINDEUTIG}")"

    if [[ "${_STATUS}" == "502" ]]; then
        report "#5d" "uneindeutiger Treffer wird abgelehnt statt geraten" true \
            "HTTP ${_STATUS}"
    else
        report "#5d" "uneindeutiger Treffer wird abgelehnt statt geraten" false \
            "HTTP ${_STATUS} statt 502"
    fi

    local _COUNT
    _COUNT="$(dbQuery "SELECT COUNT(*) FROM instruments WHERE isin = '${ISIN_UNEINDEUTIG}'")"
    if [[ "${_COUNT}" == "0" ]]; then
        report "#5e" "und hinterlässt keine halbe Zeile" true "keine Zeile angelegt"
    else
        report "#5e" "und hinterlässt keine halbe Zeile" false \
            "${_COUNT} Zeile(n) in der Datenbank"
    fi
}

# #5f — Jede Zeile trägt eine eigene, dauerhafte Kennung.
#
# Sie entstand bisher allein in der Migration. Ein zur Laufzeit angelegtes
# Papier blieb ohne — und weil SQLite `NULL` im Eindeutigkeits-Index als
# eigenen Wert zählt, fiel das nicht einmal auf.
checkListingIds() {
    local _COUNTS
    _COUNTS="$(dbQuery "SELECT COUNT(*), COUNT(listing_id), COUNT(DISTINCT listing_id) FROM instruments")"
    local _TOTAL="${_COUNTS%%|*}"
    local _REST="${_COUNTS#*|}"
    local _WITH_ID="${_REST%%|*}"
    local _DISTINCT="${_REST#*|}"

    if [[ "${_TOTAL}" -gt 0 && "${_WITH_ID}" == "${_TOTAL}" && "${_DISTINCT}" == "${_TOTAL}" ]]; then
        report "#5f" "jede Zeile hat eine eigene listing_id" true \
            "${_TOTAL} Papiere, ${_DISTINCT} verschiedene Kennungen"
    else
        report "#5f" "jede Zeile hat eine eigene listing_id" false \
            "${_TOTAL} Papiere, ${_WITH_ID} mit Kennung, ${_DISTINCT} verschieden"
    fi
}

# Fährt alle maschinell prüfbaren Teile von Zeile #5 durch.
runChecks() {
    echo
    echo -e "${CYAN}▶ T-21 Teil 2 · Verify #5 — neues Papier bringt seine Identität mit${NC}"
    echo

    echo -e "  ${BLUE}ℹ${NC} Lauf 1 von 2 — über die eigene Börsentabelle (#5a, #5b)"
    startServer "xetra" "XETR" || exit 1
    checkExchangeTablePath
    checkListingIds
    stopServer

    echo
    echo -e "  ${BLUE}ℹ${NC} Lauf 2 von 2 — über Yahoos Börsencode (#5c) und die Gegenprobe (#5d, #5e)"
    startServer "us" "US" || exit 1
    checkYahooCodePath
    checkAmbiguousIsRejected
    stopServer

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
        *)             echo -e "${RED}Unbekannte Option: $1${NC}"; usage; exit 1 ;;
    esac
done
