#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-16-smoke.sh — Die maschinell prüfbaren Zeilen aus Ticket T-16 abarbeiten
#
# Startet einen eigenen Backend-Prozess auf einem eigenen Port mit einer
# frischen, temporären Datenbank und fährt die Checks dagegen. Damit bleibt die
# Arbeits-Datenbank unberührt, und Zeile #1 läuft tatsächlich gegen eine leere
# DB — genau die Bedingung, unter der der Insert-Absturz auftrat.
#
# Die Cache-TTL steht auf 0: Jeder Abruf geht live. Nur so lässt sich prüfen,
# ob ein bekanntes Papier beim Nachschlagen seine Börse behält (#7).
#
# Braucht Netz — Yahoo und justETF werden echt gefragt.
#
# Verwendung:
#   ./_tickets/T-16-smoke.sh --run
#   ./_tickets/T-16-smoke.sh --run --keep-log
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
# Überschreibbar, falls der Port belegt ist: `PORT=8790 ./T-16-smoke.sh --run`
readonly PORT="${PORT:-8765}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Papiere, an denen die Zeilen hängen. Kommentar sagt, was sie beweisen sollen.
readonly ISIN_US="US9229087690"     # Vanguard Total Stock Market — justETF kennt ihn nicht
readonly ISIN_CA="CA46434V6817"     # iShares Core S&P/TSX — dito, plus CAD
readonly SYMBOL_CA="XIC.TO"         # dasselbe Papier; yfinance nennt dafür keine ISIN
readonly ISIN_EU="IE00B4L5Y983"     # iShares Core MSCI World — justETF ist zuständig
readonly SYMBOL_EU="EUNL.DE"
readonly SYMBOL_CRYPTO="BTC-USD"    # Gattung, die QUOTE_TYPE_MAP nicht kennt

# Nicht `PASSED`/`FAILED`: `FAILED` ist in colors.lib.sh als Farbe readonly.
COUNT_OK=0
COUNT_FAIL=0
SERVER_PID=""
WORKDIR=""
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
    echo -e "    Die UI-Zeilen aus T-16 (#3, #6-UI, #8, #10) prüft dieses Script"
    echo -e "    ${YELLOW}nicht${NC} — die bleiben beim Menschen."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port        ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Papiere     ${NC} = ${BLUE}${ISIN_US}, ${SYMBOL_CA}, ${ISIN_EU}, ${SYMBOL_CRYPTO}${NC}"
    echo
}

# Bricht ab, wenn auf dem Port schon jemand lauscht.
#
# Ohne diese Prüfung könnte der Health-Check in `startServer` den **fremden**
# Server für den eigenen halten: Er fragt nur, ob `${BASE_URL}/health`
# antwortet, und das tut auch ein Server, den jemand anderes gestartet hat.
# Der Lauf liefe dann gegen die falsche Instanz und die falsche Datenbank.
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
# **Nur die eigene PID.** Eine frühere Fassung räumte zusätzlich alles ab, was
# auf dem Port lauschte — „Gürtel und Hosenträger". Das ist keine Absicherung,
# sondern ein Risiko: Ist der Port belegt, gehört der Prozess dort jemand
# anderem, womöglich einem laufenden Entwicklungsserver. Gegen einen belegten
# Port hilft `requirePortIsFree` davor, nicht der Holzhammer danach.
cleanup() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null
        wait "${SERVER_PID}" 2>/dev/null
    fi
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP_LOG}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Server-Log: ${WORKDIR}/server.log"
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
    echo -e "  ${BLUE}ℹ${NC} Frische DB unter ${WORKDIR}"

    # CACHE_TTL_HOURS=0  → jeder Abruf geht live (Voraussetzung für #7)
    # REFRESH_INTERVAL_HOURS hoch → der Scheduler funkt nicht dazwischen
    # STATIC_DIR ins Leere → kein Dashboard-Mount nötig
    #
    # `exec` ist hier Pflicht, kein Stil: Ohne es wäre `$!` die PID der
    # Subshell, und ein `kill` darauf beendet die Hülle, während uvicorn als
    # Waise weiterläuft und den Port belegt. Mit `exec` ersetzt uvicorn die
    # Subshell und ist damit selbst der Prozess, den cleanup() erwischt.
    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${WORKDIR}/t16.db" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${WORKDIR}/server.log" 2>&1
    ) &
    SERVER_PID=$!

    local _VERSUCH
    for _VERSUCH in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL} (PID ${SERVER_PID})"
            return 0
        fi
        sleep 0.5
    done
    return 1
}

# Meldet das Ergebnis eines Checks und zählt mit.
#
# Params:
#   $1 - Zeilen-Kennung aus T-16, z.B. '#2'
#   $2 - Was geprüft wurde
#   $3 - true wenn bestanden
#   $4 - beobachteter Wert (für die Ausgabe)
report() {
    local -r _ZEILE="$1"
    local -r _WAS="$2"
    local -r _OK="$3"
    local -r _IST="$4"

    if [[ "${_OK}" == true ]]; then
        COUNT_OK=$((COUNT_OK + 1))
        echo -e "  ${GREEN}✓${NC} ${_ZEILE} ${_WAS}"
        [[ -n "${_IST}" ]] && echo -e "      ${_IST}"
    else
        COUNT_FAIL=$((COUNT_FAIL + 1))
        echo -e "  ${RED}✗${NC} ${_ZEILE} ${_WAS}"
        echo -e "      ${RED}beobachtet:${NC} ${_IST}"
    fi
}

# Prüft den HTTP-Statuscode einer URL.
#
# Params:
#   $1 - Zeilen-Kennung, $2 - Beschreibung, $3 - URL, $4 - erwarteter Code
checkStatus() {
    local -r _ZEILE="$1"
    local -r _WAS="$2"
    local -r _URL="$3"
    local -r _ERWARTET="$4"
    local _IST

    _IST="$(curl -s -o /dev/null -w "%{http_code}" --max-time 60 "${_URL}")"
    if [[ "${_IST}" == "${_ERWARTET}" ]]; then
        report "${_ZEILE}" "${_WAS}" true "HTTP ${_IST}"
    else
        report "${_ZEILE}" "${_WAS}" false "HTTP ${_IST} statt ${_ERWARTET}"
    fi
}

# Prüft ein einzelnes JSON-Feld einer Antwort gegen einen erwarteten Wert.
#
# Params:
#   $1 - Zeilen-Kennung, $2 - Beschreibung, $3 - URL, $4 - jq-Filter,
#   $5 - erwarteter Wert, $6 - Vergleichsart ('eq' exakt | 'has' enthält |
#        'not' ungleich)
checkField() {
    local -r _ZEILE="$1"
    local -r _WAS="$2"
    local -r _URL="$3"
    local -r _FILTER="$4"
    local -r _ERWARTET="$5"
    local -r _ART="${6:-eq}"
    local _IST

    _IST="$(curl -s --max-time 60 "${_URL}" | "${JQ}" -r "${_FILTER}" 2>/dev/null)"

    local _OK=false
    case "${_ART}" in
        eq)  [[ "${_IST}" == "${_ERWARTET}" ]]  && _OK=true ;;
        has) [[ "${_IST}" == *"${_ERWARTET}"* ]] && _OK=true ;;
        not) [[ "${_IST}" != "${_ERWARTET}" ]]  && _OK=true ;;
    esac

    if [[ "${_OK}" == true ]]; then
        report "${_ZEILE}" "${_WAS}" true "${_FILTER} = ${_IST}"
    else
        report "${_ZEILE}" "${_WAS}" false "${_FILTER} = '${_IST}' (erwartet ${_ART} '${_ERWARTET}')"
    fi
}

# #7 — Ein bekanntes Papier zweimal abrufen: Börse und Währung müssen bleiben.
#
# Die TTL steht auf 0, also geht auch der zweite Abruf live. Vor dem Fix lief
# der Lesepfad dabei erneut durch den Resolver und konnte ein anderes Listing
# treffen — mit anderer Währung, und das Ergebnis wird gespeichert.
checkListingBleibt() {
    local _ERSTER _ZWEITER

    _ERSTER="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_EU}" \
        | "${JQ}" -r '"\(.symbol)|\(.currency)|\(.exchange)"')"
    _ZWEITER="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_EU}" \
        | "${JQ}" -r '"\(.symbol)|\(.currency)|\(.exchange)"')"

    if [[ "${_ERSTER}" == "${_ZWEITER}" && -n "${_ERSTER}" && "${_ERSTER}" != "null|null|null" ]]; then
        report "#7" "Listing bleibt über zwei Live-Abrufe stabil" true "${_ERSTER}"
    else
        report "#7" "Listing bleibt über zwei Live-Abrufe stabil" false \
            "1. '${_ERSTER}' → 2. '${_ZWEITER}'"
    fi
}

# #5c — Ein Live-Abruf bei frischer Metadaten-TTL darf die gespeicherten
# ETF-Kennzahlen nicht als `null` an den Client zurückgeben.
#
# Der Fall: Kurs-TTL abgelaufen, Metadaten-TTL noch frisch. `_build` fragt
# justETF dann nicht (richtig — der Stand ist jung), die frische Antwort hat
# folglich keine ETF-Felder, und `_save_fresh` reicht **genau diese** Antwort
# an den Client durch. In der Datenbank bleibt der Stand korrekt stehen; nur
# wer gerade fragt, sieht Lücken.
checkAntwortHaeltDenStand() {
    local _TER_ANTWORT _TER_DB

    _TER_ANTWORT="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_EU}" | "${JQ}" -r '.ter')"
    _TER_DB="$(curl -s --max-time 60 "${BASE_URL}/instruments" \
        | "${JQ}" -r ".[] | select(.isin==\"${ISIN_EU}\") | .ter")"

    if [[ "${_TER_ANTWORT}" == "${_TER_DB}" ]]; then
        report "#5c" "Live-Antwort zeigt denselben Stand wie die Datenbank" true \
            "ter: Antwort=${_TER_ANTWORT}, DB=${_TER_DB}"
    else
        report "#5c" "Live-Antwort zeigt denselben Stand wie die Datenbank" false \
            "ter: Antwort=${_TER_ANTWORT}, DB=${_TER_DB} — der Client sieht eine Lücke, die es nicht gibt"
    fi
}

# #6 — Refresh per Symbol muss ISIN und Gattung durchreichen, sonst bleiben
# die justETF-Kennzahlen stehen (metadata_complete=false).
checkRefreshPerSymbol() {
    local _TER _COMPLETE

    curl -s -o /dev/null --max-time 60 "${BASE_URL}/quote/${ISIN_EU}"   # anlegen
    _TER="$(curl -s -X POST --max-time 60 "${BASE_URL}/refresh/by-symbol/${SYMBOL_EU}" \
        | "${JQ}" -r '.ter')"
    _COMPLETE="$(curl -s --max-time 60 "${BASE_URL}/quote/${ISIN_EU}" | "${JQ}" -r '.ter')"

    if [[ "${_TER}" != "null" && -n "${_TER}" ]]; then
        report "#6" "Refresh per Symbol liefert die ETF-Kennzahlen mit" true \
            "ter nach Refresh = ${_TER}, gespeichert = ${_COMPLETE}"
    else
        report "#6" "Refresh per Symbol liefert die ETF-Kennzahlen mit" false \
            "ter = '${_TER}' — Anreicherung lief nicht"
    fi
}

# Führt die Testsuiten aus (Zeile #11).
checkTests() {
    local _AUSGABE
    _AUSGABE="$(cd "${PROJECT_ROOT}" && "${VENV_PY}" -m pytest -q 2>&1 | tail -1)"
    if [[ "${_AUSGABE}" == *"passed"* && "${_AUSGABE}" != *"failed"* ]]; then
        report "#11" "Backend-Suite" true "${_AUSGABE}"
    else
        report "#11" "Backend-Suite" false "${_AUSGABE}"
    fi
}

# Fährt alle maschinell prüfbaren Zeilen aus T-16 durch.
runChecks() {
    checkIfToolIsAvailable "${JQ}"

    echo
    echo -e "${CYAN}▶ T-16 · maschinell prüfbare Zeilen${NC}"
    echo

    if ! startServer; then
        echo -e "  ${RED}✗${NC} Backend startet nicht — Log:"
        [[ -n "${WORKDIR}" ]] && tail -20 "${WORKDIR}/server.log"
        exit 1
    fi
    echo

    checkStatus "#1 " "Krypto-Papier auf frischer DB legt an statt abzustürzen" \
        "${BASE_URL}/quote?symbol=${SYMBOL_CRYPTO}" "200"

    checkField "#2a" "US-ETF bekommt einen Anbieter" \
        "${BASE_URL}/quote/${ISIN_US}" ".provider" "null" "not"
    checkField "#2b" "US-ETF nennt yfinance als Quelle" \
        "${BASE_URL}/quote/${ISIN_US}" ".source" "yfinance" "eq"
    checkField "#2c" "US-ETF hat kein geratenes TER" \
        "${BASE_URL}/quote/${ISIN_US}" ".ter" "null" "eq"

    # Das kanadische Papier ist der ehrliche Grenzfall, siehe Fußnote im Ticket:
    # Über die ISIN scheitert schon die Auflösung (OpenFIGI kennt kein Listing,
    # Yahoos ISIN-Suche liefert nichts) — über das Symbol kommt es herein, aber
    # yfinance nennt dafür keine ISIN ('-'), und ohne sie greift der
    # konservative Pfad. Geprüft wird deshalb der Ist-Zustand, nicht der Wunsch.
    checkField "#4a" "Kanadisches Papier kommt per Symbol herein" \
        "${BASE_URL}/quote?symbol=${SYMBOL_CA}" ".currency" "CAD" "eq"
    checkStatus "#4b" "Kanadische ISIN ist weiterhin nicht auflösbar (bekannte Lücke)" \
        "${BASE_URL}/quote/${ISIN_CA}" "404"

    checkField "#5a" "EU-ETF behält sein TER" \
        "${BASE_URL}/quote/${ISIN_EU}" ".ter" "null" "not"
    # Gegen die **gespeicherte** Zeile, nicht gegen einen zweiten Live-Abruf:
    # Steht die Metadaten-TTL noch frisch, fragt der zweite Abruf justETF nicht
    # und nennt folglich nur yfinance. Was zählt, ist der gepflegte Stand.
    checkField "#5b" "EU-ETF ist mit beiden Quellen gespeichert" \
        "${BASE_URL}/instruments" \
        ".[] | select(.isin==\"${ISIN_EU}\") | .source" "yfinance+justetf" "eq"
    checkAntwortHaeltDenStand

    checkRefreshPerSymbol
    checkListingBleibt
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
