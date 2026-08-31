#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-21c-smoke.sh — Verify #2f/#2i/#2j/#2k: Der zugesagte Aufnahmeweg
#
# Das dritte Gegenstück: `T-21-smoke.sh` migriert einen gewachsenen Bestand,
# `T-21b-smoke.sh` prüft den Neuzugang über `/quote`, und hier läuft der
# **zugesagte** Weg — `POST /instruments/intake` mit `core_version 2.0.0`.
#
# Geprüft wird über echtes HTTP gegen eine frische, temporäre Datenbank. Die
# Arbeits-Datenbank wird nicht angefasst.
#
# Dieser Lauf braucht **Netz**: Ein Papier aufzunehmen heißt, es aufzulösen und
# einen Kurs zu holen. Ohne Netz gilt der Lauf als **nicht geprüft** — nicht
# als grün. Genau dafür steht am Ende die Schlussmarke: Ein Script, das
# unterwegs abbricht, darf nicht wie ein bestandener Lauf aussehen.
#
# Vier Fragen, die nur hier zusammen beantwortet werden:
#
#   1. Ergeben **beide** Eingabeformen dasselbe Listing? (`#2f`)
#   2. Trennt der Endpunkt `201` von `200`? (`#2i`)
#   3. Antwortet eine unauflösbare Eingabe mit `{code, params}` — und **ohne**
#      eine halbe Zeile zu hinterlassen? (`#2i`)
#   4. Sagt `/fields` dieselbe Version zu wie das Artefakt? (`#2k`)
#
# Verwendung:
#   ./_tickets/T-21c-smoke.sh --run
#   PORT=8790 ./_tickets/T-21c-smoke.sh --run
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
readonly PORT="${PORT:-8772}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Ein europäischer ETF mit Xetra-Listing — er trägt einen Alias (`DE`) und
# einen echten MIC (`XETR`), also lassen sich beide Eingabeformen an ihm
# prüfen.
readonly ISIN_XETRA="IE00B3RBWM25"        # Vanguard FTSE All-World
readonly FORM_ALIAS="VGWL.DE"
readonly FORM_MIC="VGWL.XETR"

# Die erwartete Vertragsversion. Ausgeschrieben, nicht aus dem Artefakt
# gelesen: Ein Check, der seine Erwartung aus der geprüften Quelle holt,
# bestätigt nur, dass sie mit sich selbst übereinstimmt.
readonly EXPECTED_CORE_VERSION="2.0.0"

COUNT_OK=0
COUNT_FAIL=0
FIRST_LISTING_ID=""
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
    echo -e "    Dieser Lauf braucht ${YELLOW}Netz${NC} — ein Papier aufzunehmen heißt,"
    echo -e "    es aufzulösen. Ohne Netz gilt der Lauf als nicht geprüft."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Python:      " "${VENV_PY}"
    echo -e "    ${YELLOW}Port          ${NC} = ${BLUE}${PORT}${NC}"
    echo -e "    ${YELLOW}Aliasform     ${NC} = ${BLUE}${FORM_ALIAS}${NC}"
    echo -e "    ${YELLOW}MIC-Form      ${NC} = ${BLUE}${FORM_MIC}${NC}"
    echo -e "    ${YELLOW}core_version  ${NC} = ${BLUE}${EXPECTED_CORE_VERSION}${NC}"
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
# Returns:
#   0 wenn der Server erreichbar ist, 1 sonst
startServer() {
    requirePortIsFree || return 1
    WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/intake.log"
    DB_PATH="${WORKDIR}/intake.db"

    (
        cd "${PROJECT_ROOT}" || exit 1
        exec env \
            DATABASE_PATH="${DB_PATH}" \
            CACHE_TTL_HOURS=0 \
            REFRESH_INTERVAL_HOURS=24 \
            DEFAULT_EXCHANGE="XETR" \
            STATIC_DIR="${WORKDIR}/kein-dashboard" \
            "${VENV_PY}" -m uvicorn app.main:app \
                --host 127.0.0.1 --port "${PORT}" > "${LOGFILE}" 2>&1
    ) &
    SERVER_PID=$!

    local _ATTEMPT
    for _ATTEMPT in $(seq 1 40); do
        if curl -s -o /dev/null "${BASE_URL}/health" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Backend auf ${BASE_URL} (PID ${SERVER_PID})"
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

# Nimmt ein Papier über den zugesagten Weg auf.
#
# Params:
#   $1 - Der rohe Feldwert
#
# Ausgabe:
#   Statuscode und Rumpf, durch einen Zeilenumbruch getrennt.
intake() {
    curl -s --max-time 90 -w "\n%{http_code}" \
        -H "Content-Type: application/json" \
        -d "{\"identifier\": \"$1\"}" \
        "${BASE_URL}/instruments/intake"
}

# Liest ein Feld aus einer JSON-Antwort.
#
# Params:
#   $1 - Der JSON-Rumpf
#   $2 - Der Feldname
jsonField() {
    "${VENV_PY}" -c '
import json, sys
try:
    print(json.loads(sys.argv[1]).get(sys.argv[2], ""))
except json.JSONDecodeError:
    print("")
' "$1" "$2"
}

# Liest eine Abfrage aus der temporären Datenbank.
#
# Params:
#   $1 - SQL, das genau eine Zeile liefern soll
dbQuery() {
    "${VENV_PY}" -c '
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
rows = ["|".join("" if v is None else str(v) for v in row) for row in con.execute(sys.argv[2])]
print("\n".join(rows))
' "${DB_PATH}" "$1"
}

# #2f/#2i — Die erste Aufnahme legt an, und der Rumpf trägt die Identität.
#
# Setzt `FIRST_LISTING_ID`. **Nicht** über stdout: Diese Funktion meldet
# nebenbei ihre Checks, und `$(...)` finge beides zusammen ein — die
# Vergleiche danach liefen dann gegen Meldungstext plus Kennung und
# schlügen fehl, obwohl die Kennungen stimmen. Genau das ist beim ersten
# Lauf passiert.
#
# Returns:
#   0 wenn die Aufnahme geklappt hat, sonst 1
checkFirstIntakeCreates() {
    local _ANSWER _BODY _STATUS
    _ANSWER="$(intake "${ISIN_XETRA}")"
    _STATUS="${_ANSWER##*$'\n'}"
    _BODY="${_ANSWER%$'\n'*}"

    if [[ "${_STATUS}" != "201" ]]; then
        report "#2i" "Neuanlage antwortet mit 201" false \
            "HTTP ${_STATUS} — ohne Netz gibt es hier nichts zu prüfen"
        return 1
    fi

    local -r _TICKER="$(jsonField "${_BODY}" ticker)"
    local -r _MIC="$(jsonField "${_BODY}" mic)"
    local -r _LISTING="$(jsonField "${_BODY}" listing_id)"

    report "#2i" "Neuanlage antwortet mit 201" true "ISIN ${ISIN_XETRA}"

    if [[ -n "${_TICKER}" && "${_MIC}" == "XETR" && -n "${_LISTING}" ]]; then
        report "#2i" "der Rumpf trägt die volle Identität" true \
            "${_TICKER}/${_MIC}, listing_id gesetzt"
    else
        report "#2i" "der Rumpf trägt die volle Identität" false \
            "ticker='${_TICKER}' mic='${_MIC}' listing_id='${_LISTING}'"
    fi

    FIRST_LISTING_ID="${_LISTING}"
    [[ -n "${FIRST_LISTING_ID}" ]]
}

# #2i — Ein bekanntes Papier ist keine Neuanlage.
#
# Params:
#   $1 - Die `listing_id` aus der ersten Aufnahme
checkKnownPaperIsNotCreated() {
    local -r _EXPECTED_LISTING="$1"
    local _ANSWER _BODY _STATUS
    _ANSWER="$(intake "${ISIN_XETRA}")"
    _STATUS="${_ANSWER##*$'\n'}"
    _BODY="${_ANSWER%$'\n'*}"

    local -r _LISTING="$(jsonField "${_BODY}" listing_id)"
    if [[ "${_STATUS}" == "200" && "${_LISTING}" == "${_EXPECTED_LISTING}" ]]; then
        report "#2i" "das bekannte Papier antwortet mit 200" true \
            "dieselbe listing_id"
    else
        report "#2i" "das bekannte Papier antwortet mit 200" false \
            "HTTP ${_STATUS}, listing_id '${_LISTING}' statt '${_EXPECTED_LISTING}'"
    fi
}

# #2f — Beide Eingabeformen treffen dasselbe Listing.
#
# Der eigentliche Beweis der Eingabeentscheidung: `VGWL.DE` und `VGWL.XETR`
# sind zwei Schreibweisen **eines** Papiers. Träfen sie verschiedene Zeilen,
# entstünde ein zweites Listing desselben Wertpapiers — und der
# Eindeutigkeitsindex auf `(ticker, mic)` hielte es nicht auf, weil er die
# doppelte Identität dann gar nicht sähe.
#
# Params:
#   $1 - Die `listing_id` aus der ersten Aufnahme
checkBothInputForms() {
    local -r _EXPECTED_LISTING="$1"
    local _FORM _ANSWER _BODY _STATUS _LISTING

    for _FORM in "${FORM_ALIAS}" "${FORM_MIC}"; do
        _ANSWER="$(intake "${_FORM}")"
        _STATUS="${_ANSWER##*$'\n'}"
        _BODY="${_ANSWER%$'\n'*}"
        _LISTING="$(jsonField "${_BODY}" listing_id)"

        if [[ "${_STATUS}" == "200" && "${_LISTING}" == "${_EXPECTED_LISTING}" ]]; then
            report "#2f" "${_FORM} trifft dasselbe Listing" true "HTTP 200"
        else
            report "#2f" "${_FORM} trifft dasselbe Listing" false \
                "HTTP ${_STATUS}, listing_id '${_LISTING}'"
        fi
    done
}

# #2f — Eine aliaslose Börse bleibt die genannte.
#
# Der Befund aus Runde 39, live: `AAPL.XNAS` und `AAPL.XNYS` tragen denselben
# Abrufalias `AAPL`, weil die US-Plätze keinen Suffix führen. Wer über das
# Symbol nachschlägt, verliert genau die Börse, die der Benutzer genannt hat.
#
# Geprüft wird gegen das **echte** Yahoo: Der Kurs kommt für `AAPL`, die
# Identität aus der Eingabe.
checkAliaslessMic() {
    local _ANSWER _BODY _STATUS
    _ANSWER="$(intake "AAPL.XNAS")"
    _STATUS="${_ANSWER##*$'\n'}"
    _BODY="${_ANSWER%$'\n'*}"

    local -r _MIC="$(jsonField "${_BODY}" mic)"
    local -r _TICKER="$(jsonField "${_BODY}" ticker)"

    if [[ "${_STATUS}" == "201" && "${_MIC}" == "XNAS" && "${_TICKER}" == "AAPL" ]]; then
        report "#2f" "AAPL.XNAS behält die genannte Börse" true "AAPL/XNAS"
    else
        report "#2f" "AAPL.XNAS behält die genannte Börse" false \
            "HTTP ${_STATUS}, ${_TICKER}/${_MIC} statt AAPL/XNAS"
        return
    fi

    # Die Gegenprobe: Dieselbe Kennung an einem **anderen** Platz.
    #
    # Erwartet wird ein Wechsel, keine zweite Zeile — und das ist kein
    # Widerspruch zum Test daneben, sondern die ISIN-Regel des Vertrags:
    # `one_active_listing_per_isin`. Yahoo liefert für `AAPL` eine ISIN, also
    # gibt es dieses Papier genau einmal, und die Eingabe entscheidet, wo.
    # Ohne ISIN — im Kettentest so gebaut — stehen die beiden Notierungen
    # dagegen nebeneinander.
    _ANSWER="$(intake "AAPL.XNYS")"
    _STATUS="${_ANSWER##*$'\n'}"
    _BODY="${_ANSWER%$'\n'*}"

    local -r _ROWS="$(dbQuery "SELECT COUNT(*) FROM instruments WHERE ticker = 'AAPL'")"
    if [[ "${_STATUS}" == "200" && "$(jsonField "${_BODY}" mic)" == "XNYS" \
          && "${_ROWS}" == "1" ]]; then
        report "#2f" "AAPL.XNYS zieht dieselbe ISIN um" true \
            "200, XNYS, weiterhin eine Zeile"
    else
        report "#2f" "AAPL.XNYS zieht dieselbe ISIN um" false \
            "HTTP ${_STATUS}, mic $(jsonField "${_BODY}" mic), ${_ROWS} Zeilen"
    fi
}

# #2i — Unauflösbare Eingaben werden mit Kennung abgelehnt.
#
# Die Gegenprobe des ganzen Laufs: Ein Durchgang, in dem alles durchgeht, hat
# die Regel nicht geprüft. Geprüft wird die **Kennung**, nicht ein Satz — der
# Text steht im Dashboard und in zwei Sprachen.
checkRejections() {
    local -r _CASES=(
        "AAPL:symbol_without_exchange_suffix"
        "AAPL.US:unknown_exchange_suffix"
        "BRK-B.XNYS:non_canonical_ticker"
    )
    local _CASE _INPUT _EXPECTED _ANSWER _BODY _STATUS _CODE

    for _CASE in "${_CASES[@]}"; do
        _INPUT="${_CASE%%:*}"
        _EXPECTED="${_CASE##*:}"
        _ANSWER="$(intake "${_INPUT}")"
        _STATUS="${_ANSWER##*$'\n'}"
        _BODY="${_ANSWER%$'\n'*}"
        _CODE="$(jsonField "${_BODY}" code)"

        if [[ "${_STATUS}" == "400" && "${_CODE}" == "${_EXPECTED}" ]]; then
            report "#2i" "${_INPUT} wird abgelehnt" true "${_CODE}"
        else
            report "#2i" "${_INPUT} wird abgelehnt" false \
                "HTTP ${_STATUS}, code '${_CODE}' statt '${_EXPECTED}'"
        fi
    done
}

# #2b2 — Die Invariante: keine halbe Identität im Bestand.
checkNoHalfIdentity() {
    local -r _OPEN="$(dbQuery "SELECT COUNT(*) FROM instruments WHERE ticker IS NULL OR mic IS NULL")"
    local -r _TOTAL="$(dbQuery "SELECT COUNT(*) FROM instruments")"

    if [[ "${_OPEN}" == "0" && "${_TOTAL}" != "0" ]]; then
        report "#2b2" "keine Zeile trägt eine halbe Identität" true \
            "${_TOTAL} Zeilen, davon 0 offen"
    else
        report "#2b2" "keine Zeile trägt eine halbe Identität" false \
            "${_OPEN} offene von ${_TOTAL} Zeilen"
    fi
}

# #2k — Die zugesagte Version steht auch zur Laufzeit an.
checkCoreVersion() {
    local -r _BODY="$(curl -s --max-time 20 "${BASE_URL}/fields")"
    local -r _VERSION="$(jsonField "${_BODY}" core_version)"

    if [[ "${_VERSION}" == "${EXPECTED_CORE_VERSION}" ]]; then
        report "#2k" "/fields sagt core_version ${EXPECTED_CORE_VERSION} zu" true ""
    else
        report "#2k" "/fields sagt core_version ${EXPECTED_CORE_VERSION} zu" false \
            "beobachtet: '${_VERSION}'"
    fi
}

# #2j — Der Aufnahmeweg taucht in der Übersicht auf.
checkInstrumentListShowsIdentity() {
    local -r _BODY="$(curl -s --max-time 20 "${BASE_URL}/instruments")"
    local -r _COMPLETE="$("${VENV_PY}" -c '
import json, sys
rows = json.loads(sys.argv[1])
print(sum(1 for row in rows if row.get("ticker") and row.get("mic") and row.get("listing_id")))
print(len(rows))
' "${_BODY}")"
    local -r _WITH_IDENTITY="${_COMPLETE%%$'\n'*}"
    local -r _ROWS="${_COMPLETE##*$'\n'}"

    if [[ "${_WITH_IDENTITY}" == "${_ROWS}" && "${_ROWS}" != "0" ]]; then
        report "#2j" "/instruments zeigt die Identität aller Zeilen" true \
            "${_ROWS} Zeilen, alle vollständig"
    else
        report "#2j" "/instruments zeigt die Identität aller Zeilen" false \
            "${_WITH_IDENTITY} von ${_ROWS} Zeilen vollständig"
    fi
}

# Führt alle Checks aus.
runChecks() {
    trap cleanup EXIT INT TERM

    echo
    echo -e "${LIGHT_BLUE}T-21c — der zugesagte Aufnahmeweg${NC}"
    echo

    startServer || return 1

    if ! checkFirstIntakeCreates; then
        echo
        echo -e "  ${YELLOW}Ohne erste Aufnahme sind die übrigen Checks gegenstandslos.${NC}"
        echo -e "  ${YELLOW}Meist fehlt das Netz — dann gilt der Lauf als nicht geprüft.${NC}"
        return 1
    fi

    checkKnownPaperIsNotCreated "${FIRST_LISTING_ID}"
    checkBothInputForms "${FIRST_LISTING_ID}"
    checkAliaslessMic
    checkRejections
    checkNoHalfIdentity
    checkInstrumentListShowsIdentity
    checkCoreVersion

    echo
    # **Die Schlussmarke.** Sie steht am Ende und nur hier: Ein Lauf, der
    # unterwegs abbricht, erreicht sie nicht und sieht deshalb nie wie ein
    # bestandener aus (P-05).
    if [[ "${COUNT_FAIL}" -eq 0 ]]; then
        echo -e "  ${GREEN}✓ ${COUNT_OK} Checks bestanden, keine Fehler${NC}"
        echo
        return 0
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
