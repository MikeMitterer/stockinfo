#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-35-smoke.sh — dieselbe Verify-Matrix wie der UI-Lauf, nur ohne Browser
#
# Der Browser-Lauf hat gefunden, was kein Unit-Test sah. Er hat aber einen
# Nachteil: Er läuft nicht von selbst. Dieses Script stellt dieselben Fragen
# über die REST-Schnittstelle — die Zeilen `#1` bis `#8` aus T-35, ohne `#9`
# (Browserkonsole) und ohne die rein visuellen Anteile.
#
# **Dieser Lauf braucht Netz.** Das ist Absicht und keine Nachlässigkeit: Die
# Aussage von T-35 ist „die Kette arbeitet mit den echten Quellen". Ein
# Mitschnitt bewiese nur, dass der Mitschnitt noch da ist. Ist kein Netz da,
# bricht der Lauf sichtbar ab, statt grün zu werden.
#
# **Die Arbeitsdatenbank wird nicht angefasst.** Eigener Port, eigenes
# temporäres Volume, eigene `sources.yaml`; beendet wird nur die selbst
# gestartete PID.
#
# Verwendung:
#   ./_tickets/T-35-smoke.sh --run
#   PORT=8795 ./_tickets/T-35-smoke.sh --run
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep-log   Server-Log und Volume nach dem Lauf stehen lassen
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
readonly PORT="${PORT:-8795}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Ein europäischer ETF, ein US-Papier und eines, das die Vorzugsbörse nicht
# führt. Zusammen decken sie alle drei Auflösungswege ab.
readonly ETF_ISIN="IE00B4L5Y983"
readonly US_ISIN="US0378331005"
readonly HOME_ISIN="CA7800871021"
readonly NONSENSE_ISIN="XX0000000000"

# Wie viele Checks dieser Lauf erwartet. Ohne die Zahl könnte ein Lauf, der
# unterwegs abbricht, mit COUNT_FAIL=0 grün enden (P-05).
readonly EXPECTED_CHECKS=15

COUNT_OK=0
COUNT_FAIL=0
SERVER_PID=""
WORKDIR=""
LOGFILE=""
DB_PATH=""
KEEP_LOG=false

usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Checks ausführen (eigener Server, temporäres Volume)"
    usageLine "-k | --keep-log  " "Server-Log und Volume stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Anderer Port:  ${GREEN}PORT=8796 ${APPNAME} --run${NC}"
    echo
    echo -e "    Dieser Lauf ${RED}braucht Netz${NC} — er fragt OpenFIGI, Yahoo"
    echo -e "    und justETF wirklich."
    echo
}

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
    echo -e "      Anderen Port wählen: ${GREEN}PORT=8796 ${APPNAME} --run${NC}"
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

cleanup() {
    stopServer
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP_LOG}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Server-Log und Volume: ${WORKDIR}"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Legt Volume und die Kette an, die Mike für T-35 vorgegeben hat.
prepareVolume() {
    WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/server.log"
    DB_PATH="${WORKDIR}/stockinfo.db"

    cat > "${WORKDIR}/sources.yaml" <<'YAML'
resolvers: [openfigi, yahoo-search]
etf_meta:  [justetf, yfinance]
quotes:    [yfinance]
daily:     [yfinance]
fx:        [yfinance]

providers:
  openfigi:
    api_key: ${OPENFIGI_API_KEY}
YAML

    (
        cd "${PROJECT_ROOT}" || exit 1
        "${VENV_PY}" -c "from app.db import init_db; init_db('${DB_PATH}')"
    ) || { echo -e "  ${RED}✗${NC} Schema konnte nicht angelegt werden"; return 1; }
    echo -e "  ${GREEN}✓${NC} Volume und Kette angelegt"
    return 0
}

startServer() {
    requirePortIsFree || return 1
    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${DB_PATH}" \
            REFRESH_INTERVAL_HOURS=24 \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" >> "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend läuft auf ${PORT}"
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
        [[ -n "${_ACTUAL}" ]] && echo -e "      ${RED}${_ACTUAL}${NC}"
    fi
    # **Immer `0`.** Die Aufrufer stehen in `bedingung && report … || report …`;
    # ohne diese Zeile entschiede der letzte Ausdruck über den Rückgabewert.
    # Der ist `[[ -n "${_ACTUAL}" ]]` und damit `1`, sobald ein Check ohne
    # Zusatztext meldet — dann lief **beides**, Erfolgs- und Fehlermeldung.
    # Genau das ist beim ersten Lauf passiert (17 Meldungen bei 12 Checks),
    # und nur die Vollständigkeitsprüfung am Ende hat es aufgedeckt.
    return 0
}

# Liest ein Feld aus einer JSON-Antwort.
#
# Params:
#   $1 - JSON
#   $2 - Feldname (flach)
field() {
    "${VENV_PY}" -c "
import json, sys
try:
    print(json.loads(sys.argv[1]).get(sys.argv[2], ''))
except Exception:
    print('')
" "$1" "$2" 2>/dev/null
}

# Eine Spalte aus der Datenbank.
column() {
    "${VENV_PY}" -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
row = c.execute(f'select {sys.argv[2]} from instruments where isin = ?', (sys.argv[3],)).fetchone()
print('' if row is None or row[0] is None else row[0])
" "${DB_PATH}" "$2" "$1" 2>/dev/null
}

# ─── Die Checks ───────────────────────────────────────────────────────────────

checkChain() {
    local _BODY _NAMES
    _BODY="$(curl -s "${BASE_URL}/sources")"
    _NAMES="$("${VENV_PY}" -c "
import json, sys
d = json.loads(sys.argv[1])
unkonfiguriert = [s['name'] for s in d['sources'] if not s.get('configured')]
print(','.join(sorted({s['name'] for s in d['sources']})), '|', ','.join(unkonfiguriert))
" "${_BODY}" 2>/dev/null)"

    local _WANTED="justetf,openfigi,yahoo-search,yfinance"
    if [[ "${_NAMES}" == "${_WANTED} | " ]]; then
        report "#1 " "die vorgegebene Kette steht und ist einsatzbereit" true "${_WANTED}"
    else
        report "#1 " "die vorgegebene Kette steht und ist einsatzbereit" false "${_NAMES}"
    fi
}

checkIntake() {
    local _CODE _BODY
    _BODY="$(curl -s -o "${WORKDIR}/intake.json" -w '%{http_code}' \
        -X POST "${BASE_URL}/instruments/intake" \
        -H 'Content-Type: application/json' \
        -d "{\"identifier\":\"${ETF_ISIN}\"}")"
    _CODE="${_BODY}"
    [[ "${_CODE}" == "201" ]] \
        && report "#2 " "der ETF wird angelegt" true "HTTP 201" \
        || report "#2 " "der ETF wird angelegt" false "HTTP ${_CODE}"

    local _COUNT
    _COUNT="$("${VENV_PY}" -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(c.execute('select count(*) from instruments where isin = ?', (sys.argv[2],)).fetchone()[0])
" "${DB_PATH}" "${ETF_ISIN}")"
    [[ "${_COUNT}" == "1" ]] \
        && report "#2b" "genau eine Zeile in der Datenbank" true "" \
        || report "#2b" "genau eine Zeile in der Datenbank" false "${_COUNT} Zeilen"
}

checkChainProvesItself() {
    local _BODY _NAME _TYPE _TER _PROVIDER _CURRENCY
    _BODY="$(curl -s "${BASE_URL}/quote/${ETF_ISIN}")"
    _NAME="$(field "${_BODY}" name)"
    _TYPE="$(field "${_BODY}" type)"
    _TER="$(field "${_BODY}" ter)"
    _PROVIDER="$(field "${_BODY}" provider)"
    _CURRENCY="$(field "${_BODY}" currency)"

    # **Der eigentliche Beweis der Kette**: Name und Gattung stammen von
    # OpenFIGI, der Kurs von yfinance, TER und Anbieter von justETF. Drei
    # Quellen in einer Antwort — fehlt eine, ist es keine Kette.
    [[ -n "${_NAME}" ]] \
        && report "#3a" "der Name ist gefüllt (OpenFIGI)" true "${_NAME}" \
        || report "#3a" "der Name ist gefüllt (OpenFIGI)" false "leer"

    [[ "${_TYPE}" == "etf" ]] \
        && report "#3b" "die Gattung ist erkannt (OpenFIGI)" true "etf" \
        || report "#3b" "die Gattung ist erkannt (OpenFIGI)" false "'${_TYPE}'"

    [[ "${_CURRENCY}" == "EUR" ]] \
        && report "#3c" "der Kurs trägt seine Währung (yfinance)" true "EUR" \
        || report "#3c" "der Kurs trägt seine Währung (yfinance)" false "'${_CURRENCY}'"

    if [[ -n "${_TER}" && -n "${_PROVIDER}" ]]; then
        report "#3d" "TER und Anbieter kommen an (justETF)" true "TER ${_TER} · ${_PROVIDER}"
    else
        report "#3d" "TER und Anbieter kommen an (justETF)" false \
            "TER '${_TER}', Anbieter '${_PROVIDER}' — wird justETF überhaupt gefragt?"
    fi
}

checkHomeExchange() {
    curl -s -o /dev/null -X POST "${BASE_URL}/instruments/intake" \
        -H 'Content-Type: application/json' -d "{\"identifier\":\"${HOME_ISIN}\"}"
    local _MIC _CURRENCY
    _MIC="$(column "${HOME_ISIN}" mic)"
    _CURRENCY="$(column "${HOME_ISIN}" currency)"

    [[ "${_MIC}" == "XTSE" && "${_CURRENCY}" == "CAD" ]] \
        && report "#4 " "die Heimatbörsen-Kaskade greift" true "${_MIC} / ${_CURRENCY}" \
        || report "#4 " "die Heimatbörsen-Kaskade greift" false "${_MIC} / ${_CURRENCY}"

    curl -s -o /dev/null -X POST "${BASE_URL}/instruments/intake" \
        -H 'Content-Type: application/json' -d "{\"identifier\":\"${US_ISIN}\"}"
    local _US_MIC
    _US_MIC="$(column "${US_ISIN}" mic)"
    # Die Vorzugsbörse gewinnt, wenn sie das Papier führt (T-18) — Apple kommt
    # deshalb an Xetra herein und **nicht** in New York. Das ist die Zusage.
    [[ "${_US_MIC}" == "XETR" ]] \
        && report "#4b" "die Vorzugsbörse bleibt vorrangig" true "${_US_MIC}" \
        || report "#4b" "die Vorzugsbörse bleibt vorrangig" false "${_US_MIC}"
}

checkUnresolvable() {
    local _CODE _BODY _KIND
    _CODE="$(curl -s -o "${WORKDIR}/nope.json" -w '%{http_code}' \
        "${BASE_URL}/quote/${NONSENSE_ISIN}")"
    _BODY="$(cat "${WORKDIR}/nope.json")"
    _KIND="$(field "${_BODY}" code)"

    # **Zwei Zusagen in einer Zeile.** Der Statuscode sagt „Eingabefehler", und
    # der Körper trägt eine *Kennung* statt eines deutschen Satzes — sonst
    # kann die Oberfläche den Grund nicht übersetzen und zeigt nur „ging
    # nicht". Genau das war der Befund des UI-Laufs.
    if [[ "${_CODE}" == "404" && "${_KIND}" == "instrument_not_found" ]]; then
        report "#5 " "die unauflösbare ISIN wird typisiert abgelehnt" true \
            "HTTP 404 · ${_KIND}"
    else
        report "#5 " "die unauflösbare ISIN wird typisiert abgelehnt" false \
            "HTTP ${_CODE} · '${_BODY}'"
    fi

    local _COUNT
    _COUNT="$("${VENV_PY}" -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(c.execute('select count(*) from instruments where isin = ?', (sys.argv[2],)).fetchone()[0])
" "${DB_PATH}" "${NONSENSE_ISIN}")"
    [[ "${_COUNT}" == "0" ]] \
        && report "#5b" "und legt keine kaputte Zeile an" true "" \
        || report "#5b" "und legt keine kaputte Zeile an" false "${_COUNT} Zeilen"
}

checkOverrideAndCache() {
    # Handpflege setzen …
    curl -s -o /dev/null -X PUT \
        "${BASE_URL}/instruments/by-symbol/APC.DE/overrides" \
        -H 'Content-Type: application/json' -d '{"ter": 1.25}'

    local _MANUAL
    _MANUAL="$("${VENV_PY}" -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
row = c.execute('''
  select o.ter from instrument_overrides o
  join instruments i on i.id = o.instrument_id
  where i.isin = ?''', (sys.argv[2],)).fetchone()
print('' if row is None or row[0] is None else row[0])
" "${DB_PATH}" "${US_ISIN}")"
    [[ "${_MANUAL}" == "1.25" ]] \
        && report "#6 " "die Handpflege liegt in der Override-Tabelle" true "TER ${_MANUAL}" \
        || report "#6 " "die Handpflege liegt in der Override-Tabelle" false "'${_MANUAL}'"

    # … und einen Refresh überstehen. **Der Befund aus dem UI-Lauf**: Hier
    # löschte der Kurs-Weg den Namen, weil er Spalten schrieb, die er gar
    # nicht kennen kann.
    local _NAME_VORHER _NAME_NACHHER
    _NAME_VORHER="$(column "${ETF_ISIN}" name)"
    curl -s -o /dev/null -X POST "${BASE_URL}/refresh/${ETF_ISIN}"
    _NAME_NACHHER="$(column "${ETF_ISIN}" name)"

    [[ -n "${_NAME_NACHHER}" && "${_NAME_VORHER}" == "${_NAME_NACHHER}" ]] \
        && report "#6c" "ein Refresh löscht den Namen nicht" true "${_NAME_NACHHER}" \
        || report "#6c" "ein Refresh löscht den Namen nicht" false \
            "vorher '${_NAME_VORHER}', nachher '${_NAME_NACHHER}'"

    # Zweimal derselbe Abruf: Der zweite kommt aus dem Cache. Gemessen wird der
    # **Zeitstempel**, nicht die Antwortzeit — die kann täuschen.
    local _ERSTER _ZWEITER
    _ERSTER="$(field "$(curl -s "${BASE_URL}/quote/${ETF_ISIN}")" fetched_at)"
    _ZWEITER="$(field "$(curl -s "${BASE_URL}/quote/${ETF_ISIN}")" fetched_at)"
    [[ -n "${_ERSTER}" && "${_ERSTER}" == "${_ZWEITER}" ]] \
        && report "#7 " "der zweite Abruf kommt aus dem Cache" true "${_ZWEITER}" \
        || report "#7 " "der zweite Abruf kommt aus dem Cache" false \
            "'${_ERSTER}' vs '${_ZWEITER}'"
}

checkDelete() {
    curl -s -o /dev/null -X DELETE "${BASE_URL}/instruments/${HOME_ISIN}"
    local _REST _WAISEN
    _REST="$(column "${HOME_ISIN}" isin)"
    _WAISEN="$("${VENV_PY}" -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(c.execute('''
  select count(*) from quotes q
  where not exists (select 1 from instruments i where i.id = q.instrument_id)
''').fetchone()[0])
" "${DB_PATH}")"

    if [[ -z "${_REST}" && "${_WAISEN}" == "0" ]]; then
        report "#8 " "gelöscht — ohne Waisen zu hinterlassen" true ""
    else
        report "#8 " "gelöscht — ohne Waisen zu hinterlassen" false \
            "Zeile '${_REST}', ${_WAISEN} verwaiste Kurse"
    fi
}

runChecks() {
    trap cleanup EXIT INT TERM

    echo
    echo -e "${LIGHT_BLUE}T-35 — die Verify-Matrix über die REST-Schnittstelle${NC}"
    echo

    prepareVolume || return 1
    startServer || return 1
    echo

    checkChain
    checkIntake
    checkChainProvesItself
    checkHomeExchange
    checkUnresolvable
    checkOverrideAndCache
    checkDelete

    echo
    local -r _TOTAL=$((COUNT_OK + COUNT_FAIL))
    if [[ "${_TOTAL}" -ne "${EXPECTED_CHECKS}" ]]; then
        echo -e "  ${RED}✗${NC} Nur ${_TOTAL} von ${EXPECTED_CHECKS} Checks gelaufen —"
        echo -e "      der Lauf ist unterwegs abgebrochen und zählt nicht als grün."
        return 1
    fi
    if [[ "${COUNT_FAIL}" -gt 0 ]]; then
        echo -e "  ${RED}${COUNT_FAIL} von ${_TOTAL} Checks fehlgeschlagen${NC}"
        return 1
    fi
    echo -e "  ${GREEN}Alle ${_TOTAL} Checks bestanden${NC}"
    return 0
}

# ─── Argumente ────────────────────────────────────────────────────────────────

RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -r|--run)      RUN=true ;;
        -k|--keep-log) KEEP_LOG=true ;;
        -i|--info)     showInfo; exit 0 ;;
        -h|--help)     usage; exit 0 ;;
        *)             echo "Unbekannte Option: $1"; usage; exit 1 ;;
    esac
    shift
done

if [[ "${RUN}" != true ]]; then
    usage
    exit 0
fi

runChecks
exit $?
