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
readonly PORT="${PORT:-8795}"
readonly BASE_URL="http://127.0.0.1:${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

# Welches Quellenprofil geprüft wird — **ein Schalter, keine zweite
# Prüfstrecke** (T-37).
#
# Das Profil entscheidet genau zwei Dinge: welche `sources.yaml` geschrieben
# wird und welche Dateien danebenliegen. **Die Checks darunter kennen es
# nicht.** Sie fragen nach dem Ergebnis — „kommt das Papier an dieser Börse in
# dieser Währung herein", „ist der Name gefüllt" —, und das Ergebnis muss
# dasselbe sein, egal wer geantwortet hat.
#
# Sobald ein Check ein `if [[ "${PROFILE}" == … ]]` braucht, ist die
# Schnittstelle an dieser Stelle keine gemeinsame. Das wäre ein **Befund**,
# kein Grund für einen Zweig.
readonly PROFILE="${PROFILE:-online}"

# Ein europäischer ETF, ein US-Papier und eines, das die Vorzugsbörse nicht
# führt. Zusammen decken sie alle drei Auflösungswege ab.
readonly ETF_ISIN="IE00B4L5Y983"
readonly US_ISIN="US0378331005"
readonly HOME_ISIN="CA7800871021"
readonly NONSENSE_ISIN="XX0000000000"

# Wie viele Checks dieser Lauf erwartet. Ohne die Zahl könnte ein Lauf, der
# unterwegs abbricht, mit COUNT_FAIL=0 grün enden (P-05).
readonly EXPECTED_CHECKS=20

COUNT_OK=0
COUNT_FAIL=0
SERVER_PID=""
WORKDIR=""
LOGFILE=""
DB_PATH=""
KEEP_LOG=false

# Welche Quellen dieses Profil erwartet — gesetzt beim Schreiben der Kette,
# gelesen von `checkChain`. Der **einzige** Erwartungswert, der sich zwischen
# den Profilen unterscheidet.
EXPECTED_SOURCES=""

# Welche Quelle die Devisenrolle dieses Profils liefert — der zweite und
# letzte Erwartungswert, der sich zwischen den Profilen unterscheidet.
EXPECTED_FX_SOURCE=""

usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Checks ausführen (eigener Server, temporäres Volume)"
    usageLine "-k | --keep-log  " "Server-Log und Volume stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    echo
    echo -e "    ${YELLOW}PROFILE${NC}=online|yaml — dieselben Checks, andere Quellen"
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

# Schreibt die Kette des Online-Profils: OpenFIGI, Yahoo, justETF.
writeOnlineProfile() {
    EXPECTED_SOURCES="justetf,openfigi,yahoo-search,yfinance"
    EXPECTED_FX_SOURCE="yfinance"
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
}

# Schreibt die Kette des YAML-Profils samt ihrer Fachdatendatei.
#
# **Dieselben drei Papiere wie online, mit denselben Werten** — nur so bleiben
# die Checks darunter identisch. Weicht ein Wert ab, prüft der Lauf nicht mehr
# dieselbe Aussage, sondern eine ähnliche.
writeYamlProfile() {
    EXPECTED_SOURCES="yaml-file"
    EXPECTED_FX_SOURCE="yaml-file"

    # **Eine Quelle in fuenf Rollen, eine Datei.** Bis T-37 standen hier vier
    # Beispiel-Plugins mit vier CSV-Dateien; der Betreiber musste sie
    # zueinander passend halten, ohne dass etwas das geprueft haette.
    #
    # Geladen wird ueber den **Entry-Point** — `yaml-file` ist im Paket
    # angemeldet und installiert. Eine Kopie ins Volume waere der zweite
    # Ladeweg, und den prueft `tests/test_plugin_vertical.py`.
    cat > "${WORKDIR}/assets.yaml" <<'YAML'
version: 1

instruments:
  - id: world-etf
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: iShares Core MSCI World UCITS ETF
    instrument_type: etf
    price: {value: 128.21, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}
    # Die TER steht in **Basispunkten** — `20` sind `0,20 %`, derselbe Wert,
    # den justETF online liefert. Dass beide Profile dasselbe anzeigen, obwohl
    # die Quellen in verschiedenen Einheiten liefern, ist der schaerfste
    # Einzelbeweis dafuer, dass die Einheitendeklaration des Vertrags traegt.
    metadata: {ter_bps: 20, provider: iShares, fund_domicile: Ireland}
    # Die Tagesreihe pruefen Check `#9`: Ohne sie liefert die Rolle `daily`
    # nichts, und der Lauf zeigte eine leere Reihe statt einer fehlenden
    # Zusage. Die CSV-Fassung trug diese Werte in `closes.csv`.
    history:
      currency: EUR
      closes:
        - {date: "2026-08-25", value: 127.90}
        - {date: "2026-08-26", value: 128.05}
        - {date: "2026-08-27", value: 128.21}

  - id: apple-xetra
    identity: {kind: listed, isin: US0378331005, ticker: APC, mic: XETR}
    name: Apple Inc.
    instrument_type: stock
    price: {value: 277.40, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}

  - id: rbc-toronto
    identity: {kind: listed, isin: CA7800871021, ticker: RY, mic: XTSE}
    name: Royal Bank of Canada
    instrument_type: stock
    price: {value: 283.40, currency: CAD, as_of: "2026-08-27T21:00:00+02:00"}
    history:
      currency: CAD
      closes:
        - {date: "2026-08-27", value: 283.40}

fx_rates:
  - {base: CAD, quote: EUR, rate: 0.6412, as_of: "2026-08-27T17:30:00+02:00"}
YAML

    cat > "${WORKDIR}/sources.yaml" <<YAML
resolvers: [yaml-file]
etf_meta:  [yaml-file]
quotes:    [yaml-file]
daily:     [yaml-file]
fx:        [yaml-file]

providers:
  yaml-file:
    path: ${WORKDIR}/assets.yaml
YAML
}

# Legt das Volume und die Kette des gewählten Profils an.
prepareVolume() {
    WORKDIR="$(mktemp -d)"
    LOGFILE="${WORKDIR}/server.log"
    DB_PATH="${WORKDIR}/stockinfo.db"

    case "${PROFILE}" in
        online) writeOnlineProfile ;;
        yaml)   writeYamlProfile ;;
        *)
            echo -e "  ${RED}✗${NC} Unbekanntes Profil '${PROFILE}' — erlaubt: online, yaml"
            return 1
            ;;
    esac

    (
        cd "${PROJECT_ROOT}" || exit 1
        "${VENV_PY}" -c "from app.db import init_db; init_db('${DB_PATH}')"
    ) || { echo -e "  ${RED}✗${NC} Schema konnte nicht angelegt werden"; return 1; }
    echo -e "  ${GREEN}✓${NC} Volume und Kette angelegt (Profil ${PROFILE})"
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
connection = sqlite3.connect(sys.argv[1])
row = connection.execute(
    f'select {sys.argv[2]} from instruments where isin = ?', (sys.argv[3],)
).fetchone()
print('' if row is None or row[0] is None else row[0])
" "${DB_PATH}" "$2" "$1" 2>/dev/null
}

# Die von Hand gepflegte TER eines Papiers — **aus der Datenbank**.
overrideTer() {
    "${VENV_PY}" -c "
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
sql = (
    'select overrides.ter from instrument_overrides overrides '
    'join instruments instrument on instrument.id = overrides.instrument_id '
    'where instrument.isin = ?'
)
row = connection.execute(sql, (sys.argv[2],)).fetchone()
print('' if row is None or row[0] is None else row[0])
" "${DB_PATH}" "$1" 2>/dev/null
}

# Der gespeicherte Cache-Zustand: Zeilenzahl **und** juengster `fetched_at`.
#
# Beides zusammen, weil einzeln jede Groesse taeuscht — die Begruendung steht
# in `checkOverrideAndCache`.
quoteState() {
    "${VENV_PY}" -c "
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
sql = (
    \"select count(*), coalesce(max(quote.fetched_at), '') from quotes quote \"
    'join instruments instrument on instrument.id = quote.instrument_id '
    'where instrument.isin = ?'
)
row = connection.execute(sql, (sys.argv[2],)).fetchone()
print(f'{row[0]} Zeilen, zuletzt {row[1]}')
" "${DB_PATH}" "$1" 2>/dev/null
}

# ─── Die Checks ───────────────────────────────────────────────────────────────

# **Vor allen anderen: Taugen die Erwartungswerte selbst?**
#
# Mike ausdrücklich: „Stelle natürlich vorher fest, dass die Testdaten
# passen." Ohne diesen Check misst ein grüner Lauf womöglich nur, dass beide
# Seiten denselben Tippfehler teilen.
#
# Geprüft wird gegen `stockinfo_plugin.invariants` — **dieselben** Funktionen,
# an denen auch die Quellen gemessen werden. Eigene Prüfungen zu schreiben
# wäre eine zweite Wahrheit über dasselbe.
#
# Der Check läuft in **beiden** Profilen und ist damit kein Sonderweg: Online
# prüft er die Erwartungen, gegen die die echten Quellen gehalten werden; im
# YAML-Profil zusätzlich die Werte, die in der Fachdatendatei stehen. Ein
# falsch erwarteter MIC fiele online genauso auf.
# Prueft die Daten **eines** Verzeichnisses gegen die Vertragsinvarianten.
#
# Herausgezogen, damit die Negativprobe weiter unten **denselben** Parser
# benutzt und keine Kopie davon — zwei Pruefer waeren zwei Wahrheiten, und
# genau die Sorte Doppelung faellt in diesem Projekt regelmaessig auf.
#
# Params:
#   $1 - Verzeichnis mit der Fachdatendatei
#
# Returns:
#   Exitstatus des Parsers; die Befunde stehen auf stdout.
checkDataIn() {
    "${VENV_PY}" - "$1" <<'PY'
import sys
from pathlib import Path

from stockinfo_plugin.invariants import (
    currency_problem,
    is_finite_price,
    is_real_mic,
    isin_check_digit_is_valid,
)

workdir = Path(sys.argv[1])
findings: list[str] = []

# Die Erwartungen, gegen die die Checks unten messen — in beiden Profilen
# dieselben. Sie stehen hier und nicht in den Checks, damit die Prüflogik
# darunter profilfrei bleibt.
expected = [
    ("IE00B4L5Y983", "EUNL", "XETR", "EUR"),
    ("US0378331005", "APC", "XETR", "EUR"),
    ("CA7800871021", "RY", "XTSE", "CAD"),
]
for isin, ticker, mic, currency in expected:
    if not isin_check_digit_is_valid(isin):
        findings.append(f"erwartete ISIN mit falscher Pruefziffer: {isin}")
    if not is_real_mic(mic):
        findings.append(f"erwarteter MIC ist kein echter Handelsplatz: {mic}")
    problem = currency_problem(currency)
    if problem:
        findings.append(f"erwartete Waehrung {currency}: {problem}")

# Die Gegenprobe: Eine Pruefung, die nichts abweisen kann, belegt nur, dass
# sie durchgelaufen ist.
if isin_check_digit_is_valid("XX0000000000"):
    findings.append("die Pruefziffer-Pruefung greift nicht")
if is_real_mic("US"):
    findings.append("der Sammelcode US wird nicht abgewiesen")
if not currency_problem("GBX"):
    findings.append("Pence werden nicht als Untereinheit erkannt")

# Im YAML-Profil zusaetzlich die Fachdatendatei selbst.
def as_number(raw: object, where: str) -> float | None:
    """Eine Zahl aus der Datei — oder ein Befund statt eines Abbruchs.

    Hier stand blankes `float(...)`. Ein unbrauchbarer Wert liess den Pruefer
    mit einem Traceback abbrechen, und der Aufrufer las eine leere Ausgabe —
    also „keine Befunde". Ein Pruefer, der beim Finden eines Fehlers stirbt,
    meldet ihn nicht.
    """
    try:
        return float(raw)
    except (TypeError, ValueError):
        findings.append(f"{where}: {raw!r} ist keine Zahl")
        return None


assets = workdir / "assets.yaml"
if assets.is_file():
    import yaml

    try:
        data = yaml.safe_load(assets.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        findings.append(f"assets.yaml ist kein gueltiges YAML: {error}")
        data = {}

    for entry in data.get("instruments") or []:
        where = f"assets.yaml/{entry.get('id')}"
        identity = entry.get("identity") or {}
        kind = identity.get("kind")

        if kind not in ("listed", "pair", "isin_only"):
            findings.append(f"{where}: unbekannte Identitaetsform {kind!r}")
        if kind in ("listed", "isin_only") and not isin_check_digit_is_valid(
            identity.get("isin")
        ):
            findings.append(f"{where}: falsche Pruefziffer {identity.get('isin')!r}")
        if kind == "listed" and not is_real_mic(identity.get("mic")):
            findings.append(f"{where}: kein echter MIC {identity.get('mic')!r}")
        if kind == "pair":
            problem = currency_problem(identity.get("quote_currency"))
            if problem:
                findings.append(f"{where}: quote_currency {problem}")

        if not (entry.get("name") or "").strip():
            findings.append(f"{where}: Name fehlt")
        # Der Katalog aus T-31, Entscheidung 2. Ein Tippfehler in der Gattung
        # waere sonst genau der Fall, den der UI-Lauf teuer gemacht hat.
        if entry.get("instrument_type") not in (
            "stock", "etf", "etc", "fund", "crypto", "bond"
        ):
            findings.append(
                f"{where}: unbekannte Gattung {entry.get('instrument_type')!r}"
            )

        price = entry.get("price") or {}
        if price:
            problem = currency_problem(price.get("currency"))
            if problem:
                findings.append(f"{where}: price.currency {problem}")
            value = as_number(price.get("value"), where)
            if value is not None and not is_finite_price(value):
                findings.append(f"{where}: unbrauchbarer Kurs {price.get('value')!r}")

        history = entry.get("history") or {}
        if history:
            problem = currency_problem(history.get("currency"))
            if problem:
                findings.append(f"{where}: history.currency {problem}")
            for close in history.get("closes") or []:
                value = as_number(close.get("value"), where)
                if value is not None and not is_finite_price(value):
                    findings.append(
                        f"{where}: unbrauchbarer Schlusskurs {close.get('value')!r}"
                    )

        metadata = entry.get("metadata") or {}
        raw_bps = metadata.get("ter_bps")
        if raw_bps is not None:
            bps = as_number(raw_bps, where)
            if bps is not None and not 0 <= bps <= 500:
                findings.append(f"{where}: TER {raw_bps} bps ausserhalb des Bereichs")

    for rate in data.get("fx_rates") or []:
        where = f"assets.yaml/fx {rate.get('base')}/{rate.get('quote')}"
        for field in ("base", "quote"):
            problem = currency_problem(rate.get(field))
            if problem:
                findings.append(f"{where}: {rate.get(field)!r} — {problem}")
        value = as_number(rate.get("rate"), where)
        if value is not None and not is_finite_price(value):
            findings.append(f"{where}: unbrauchbarer Kurs {rate.get('rate')!r}")

print("; ".join(findings))
PY
}

# **Vor allen anderen: Taugen die Erwartungswerte selbst?**
checkTestData() {
    local _FINDINGS _STATUS
    _FINDINGS="$(checkDataIn "${WORKDIR}")"
    _STATUS=$?

    # **Ein abgestuerzter Pruefer ist kein bestandener Check.** Bricht der
    # Parser ab — etwa an `float("keine-zahl")` —, ist seine Ausgabe leer, und
    # eine Pruefung auf „leer heisst sauber" meldet Erfolg. Gemessen:
    # Exitstatus 1, Ausgabe leer, Check gruen. Von Codex in Runde 2 gefunden.
    if [[ "${_STATUS}" -ne 0 ]]; then
        report "#0 " "die Testdaten halten die Vertragsinvarianten" false \
            "die Pruefung selbst ist abgebrochen (Exitstatus ${_STATUS})"
        return 0
    fi

    [[ -z "${_FINDINGS}" ]] \
        && report "#0 " "die Testdaten halten die Vertragsinvarianten" true \
            "Pruefziffer, echter MIC, Waehrung ohne Untereinheit, endliche Kurse" \
        || report "#0 " "die Testdaten halten die Vertragsinvarianten" false "${_FINDINGS}"
}

# **Die Negativprobe zum Check darueber — dauerhaft, nicht einmalig.**
#
# Eine Pruefung, die nichts abweisen kann, belegt nur, dass sie durchgelaufen
# ist. `checkTestData` prueft die echten Daten und ist deshalb per Definition
# immer gruen; ob er einen Fehler *finden* wuerde, sagt er nicht.
#
# Hier bekommt er deshalb **eine** Datei mit drei eingebauten Fehlern: falsche
# Pruefziffer, Sammelcode statt MIC, unbrauchbarer Kurs. Findet er sie nicht
# — oder bricht er dabei ab, ohne es zu melden —, ist der Check oben wertlos.
#
# Drei Fehler in einem Eintrag, weil der Pruefer sie alle melden muss und nicht
# beim ersten stehenbleiben darf.
checkTestDataCatchesErrors() {
    local -r _BROKEN="${WORKDIR}/negativprobe"
    mkdir -p "${_BROKEN}"

    cat > "${_BROKEN}/assets.yaml" <<'YAML'
version: 1
instruments:
  - id: kaputt
    identity: {kind: listed, isin: XX0000000000, ticker: EUNL, mic: US}
    name: Falsche Pruefziffer und Sammelcode
    instrument_type: etf
    price: {value: keine-zahl, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}
YAML

    local _OUTPUT _STATUS
    _OUTPUT="$(checkDataIn "${_BROKEN}" 2>&1)"
    _STATUS=$?

    # **Ein Abbruch ist kein Erfolg.** Der erste Anlauf akzeptierte jeden
    # Exitstatus ungleich 0 als „erkannt" — auch einen Tippfehler im Pruefer
    # selbst — und behauptete danach, alle drei Mutanten seien gefunden
    # worden. Codex hat das in Runde 3 aufgegriffen: Die Meldung war eine
    # Behauptung ueber etwas, das der Check nicht gemessen hatte.
    #
    # Verlangt wird deshalb ein **sauberer** Lauf, der **jeden** eingebauten
    # Fehler beim Namen nennt. Ein Traceback ist rot.
    if [[ "${_STATUS}" -ne 0 ]]; then
        report "#0b" "die Datenpruefung findet eingebaute Fehler" false \
            "der Pruefer ist abgebrochen (Exitstatus ${_STATUS}) statt zu melden: ${_OUTPUT}"
        return 0
    fi

    local -ar _WANTED=(
        "falsche Pruefziffer"
        "kein echter MIC"
        "ist keine Zahl"
    )
    local _MISSING=""
    local _WANT
    for _WANT in "${_WANTED[@]}"; do
        [[ "${_OUTPUT}" == *"${_WANT}"* ]] || _MISSING+="${_WANT}; "
    done

    if [[ -z "${_MISSING}" ]]; then
        report "#0b" "die Datenpruefung findet eingebaute Fehler" true \
            "Pruefziffer, Sammelcode und unbrauchbarer Kurs — jeder einzeln benannt"
    else
        report "#0b" "die Datenpruefung findet eingebaute Fehler" false \
            "unbemerkt geblieben: ${_MISSING%; } — gemeldet wurde: ${_OUTPUT:-nichts}"
    fi
}

checkChain() {
    local _BODY _NAMES
    _BODY="$(curl -s "${BASE_URL}/sources")"
    _NAMES="$("${VENV_PY}" -c "
import json, sys
payload = json.loads(sys.argv[1])
sources = payload['sources']
unconfigured = [source['name'] for source in sources if not source.get('configured')]
print(','.join(sorted({source['name'] for source in sources})), '|', ','.join(unconfigured))
" "${_BODY}" 2>/dev/null)"

    # **Der einzige Erwartungswert, der sich je Profil unterscheidet** — und
    # er steht deshalb dort, wo die Kette geschrieben wird, nicht hier. Ein
    # `if [[ "${PROFILE}" == … ]]` an dieser Stelle waere der Anfang einer
    # zweiten Pruefstrecke; die Frage „stehen genau die erwarteten Quellen da
    # und sind alle einsatzbereit" ist in beiden Profilen dieselbe.
    if [[ "${_NAMES}" == "${EXPECTED_SOURCES} | " ]]; then
        report "#1 " "die vorgegebene Kette steht und ist einsatzbereit" true \
            "${EXPECTED_SOURCES}"
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
connection = sqlite3.connect(sys.argv[1])
print(connection.execute(
    'select count(*) from instruments where isin = ?', (sys.argv[2],)
).fetchone()[0])
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
        && report "#3a" "der Name ist gefüllt (Auflösung)" true "${_NAME}" \
        || report "#3a" "der Name ist gefüllt (Auflösung)" false "leer"

    [[ "${_TYPE}" == "etf" ]] \
        && report "#3b" "die Gattung ist erkannt (Auflösung)" true "etf" \
        || report "#3b" "die Gattung ist erkannt (Auflösung)" false "'${_TYPE}'"

    [[ "${_CURRENCY}" == "EUR" ]] \
        && report "#3c" "der Kurs trägt seine Währung (Kursquelle)" true "EUR" \
        || report "#3c" "der Kurs trägt seine Währung (Kursquelle)" false "'${_CURRENCY}'"

    if [[ -n "${_TER}" && -n "${_PROVIDER}" ]]; then
        report "#3d" "TER und Anbieter kommen an (Metadatenquelle)" true "TER ${_TER} · ${_PROVIDER}"
    else
        report "#3d" "TER und Anbieter kommen an (Metadatenquelle)" false \
            "TER '${_TER}', Anbieter '${_PROVIDER}' — wird die Metadatenquelle überhaupt gefragt?"
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
connection = sqlite3.connect(sys.argv[1])
print(connection.execute(
    'select count(*) from instruments where isin = ?', (sys.argv[2],)
).fetchone()[0])
" "${DB_PATH}" "${NONSENSE_ISIN}")"
    [[ "${_COUNT}" == "0" ]] \
        && report "#5b" "und legt keine kaputte Zeile an" true "" \
        || report "#5b" "und legt keine kaputte Zeile an" false "${_COUNT} Zeilen"
}

checkOverrideAndCache() {
    # **Beide Checks hier haben in Runde 1 etwas anderes geprueft, als sie
    # sagten** — von Codex aufgegriffen, und der Befund ist lehrreich: Ein
    # gruener Check, dessen Zusage nicht seine Messung ist, ist schlimmer als
    # gar keiner. Er belegt eine Eigenschaft, die niemand angesehen hat.
    #
    #   `#6c` sagte „die Handpflege ueberlebt den Abruf", setzte Apples
    #         Override, refreshte danach aber den **ETF** und pruefte dessen
    #         **Namen**. Ob der Override ueberlebt, blieb ungemessen.
    #   `#7`  sagte „aus dem Cache", las den Zeitstempel aber zweimal aus der
    #         **API-Antwort** — also aus genau der Quelle, die er pruefen soll.

    curl -s -o /dev/null -X PUT \
        "${BASE_URL}/instruments/by-symbol/APC.DE/overrides" \
        -H 'Content-Type: application/json' -d '{"ter": 1.25}'

    local _MANUAL
    _MANUAL="$(overrideTer "${US_ISIN}")"
    [[ "${_MANUAL}" == "1.25" ]] \
        && report "#6 " "die Handpflege liegt in der Override-Tabelle" true "TER ${_MANUAL}" \
        || report "#6 " "die Handpflege liegt in der Override-Tabelle" false "'${_MANUAL}'"

    # **Dasselbe** Papier refreshen, dessen Override gerade gesetzt wurde, und
    # danach erneut aus SQLite lesen. Das ist die Zusage von T-35 `#6c`.
    curl -s -o /dev/null -X POST "${BASE_URL}/refresh/${US_ISIN}"
    local _AFTER_REFRESH
    _AFTER_REFRESH="$(overrideTer "${US_ISIN}")"
    [[ "${_AFTER_REFRESH}" == "1.25" ]] \
        && report "#6c" "die Handpflege ueberlebt den Refresh desselben Papiers" true \
            "TER ${_AFTER_REFRESH} nach POST /refresh/${US_ISIN}" \
        || report "#6c" "die Handpflege ueberlebt den Refresh desselben Papiers" false \
            "vorher 1.25, nachher '${_AFTER_REFRESH}'"

    # Der Namensschutz bleibt als **eigener** Check — er gehoert zu demselben
    # Vorgang und ist der Befund aus dem UI-Lauf.
    local _NAME_BEFORE _NAME_AFTER
    _NAME_BEFORE="$(column "${ETF_ISIN}" name)"
    curl -s -o /dev/null -X POST "${BASE_URL}/refresh/${ETF_ISIN}"
    _NAME_AFTER="$(column "${ETF_ISIN}" name)"
    [[ -n "${_NAME_AFTER}" && "${_NAME_BEFORE}" == "${_NAME_AFTER}" ]] \
        && report "#6d" "ein Refresh loescht den Namen nicht" true "${_NAME_AFTER}" \
        || report "#6d" "ein Refresh loescht den Namen nicht" false \
            "vorher '${_NAME_BEFORE}', nachher '${_NAME_AFTER}'"

    # **Der Cache wird in der Datenbank gemessen, nicht in der Antwort.**
    # Zwei Groessen zusammen, denn einzeln taeuscht jede: Der gespeicherte
    # `fetched_at` bliebe auch dann gleich, wenn ein zweiter Abruf eine neue
    # Zeile **anlegte**; und die Zeilenzahl allein saehe eine Aktualisierung
    # derselben Zeile nicht.
    local _BEFORE _AFTER
    _BEFORE="$(quoteState "${ETF_ISIN}")"
    curl -s -o /dev/null "${BASE_URL}/quote/${ETF_ISIN}"
    _AFTER="$(quoteState "${ETF_ISIN}")"

    if [[ -n "${_BEFORE}" && "${_BEFORE}" == "${_AFTER}" ]]; then
        report "#7 " "der zweite Abruf hat nichts geholt (SQLite unveraendert)" true \
            "${_AFTER}"
    else
        report "#7 " "der zweite Abruf hat nichts geholt (SQLite unveraendert)" false \
            "vorher '${_BEFORE}', nachher '${_AFTER}'"
    fi
}

# **Tagesreihe und Devisen wirklich abrufen — nicht nur ihre Konfiguration.**
#
# Bis Runde 2 belegte `/sources` nur, dass beide Rollen eingerichtet sind. Ob
# sie **antworten**, stand nirgends; zwei der fuenf Rollen liefen in keinem
# Check. Codex hat das aufgegriffen, und der Einwand traegt: Eine Rolle, die
# nur in der Konfiguration vorkommt, ist nicht geprueft.
#
# Die Checks selbst bleiben profilfrei — gefragt wird nach dem Ergebnis. Nur
# der erwartete Devisen-Lieferant steht in der Profiltabelle, wie
# `EXPECTED_SOURCES` auch.
checkDailyAndFx() {
    local _DAILY _POINTS _CURRENCIES
    _DAILY="$(curl -s "${BASE_URL}/quote/${ETF_ISIN}/daily?period=1m")"
    _POINTS="$("${VENV_PY}" -c "
import json, sys
try:
    rows = json.loads(sys.argv[1])
except Exception:
    print('0 |')
    raise SystemExit
currencies = sorted({row.get('currency') for row in rows})
print(len(rows), '|', ','.join(currency for currency in currencies if currency))
" "${_DAILY}" 2>/dev/null)"
    _CURRENCIES="${_POINTS#*| }"
    _POINTS="${_POINTS%% |*}"

    if [[ "${_POINTS}" -gt 0 && "${_CURRENCIES}" == "EUR" ]]; then
        report "#9 " "die Tagesreihe liefert Werte mit Waehrung" true \
            "${_POINTS} Punkte, alle in ${_CURRENCIES}"
    else
        report "#9 " "die Tagesreihe liefert Werte mit Waehrung" false \
            "${_POINTS} Punkte, Waehrungen '${_CURRENCIES}'"
    fi

    local _FX _RATE _FX_SOURCE
    _FX="$(curl -s "${BASE_URL}/fx?base=CAD&quote=EUR")"
    _RATE="$(field "${_FX}" rate)"
    _FX_SOURCE="$(field "${_FX}" source)"

    # Der Kurs muss brauchbar sein **und** die Herkunft muss die Quelle
    # nennen, die tatsaechlich geantwortet hat — genau das war bis Runde 2
    # eine Konstante.
    if [[ -n "${_RATE}" && "${_FX_SOURCE}" == "${EXPECTED_FX_SOURCE}" ]]; then
        report "#10" "die Devisenrolle antwortet und nennt ihre Quelle" true \
            "1 CAD = ${_RATE} EUR aus ${_FX_SOURCE}"
    else
        report "#10" "die Devisenrolle antwortet und nennt ihre Quelle" false \
            "Kurs '${_RATE}', Quelle '${_FX_SOURCE}' statt '${EXPECTED_FX_SOURCE}'"
    fi
}

checkDelete() {
    curl -s -o /dev/null -X DELETE "${BASE_URL}/instruments/${HOME_ISIN}"
    local _REST _ORPHANS
    _REST="$(column "${HOME_ISIN}" isin)"
    _ORPHANS="$("${VENV_PY}" -c "
import sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
print(connection.execute('''
  select count(*) from quotes quote
  where not exists (
    select 1 from instruments instrument where instrument.id = quote.instrument_id
  )
''').fetchone()[0])
" "${DB_PATH}")"

    if [[ -z "${_REST}" && "${_ORPHANS}" == "0" ]]; then
        report "#8 " "gelöscht — ohne Waisen zu hinterlassen" true ""
    else
        report "#8 " "gelöscht — ohne Waisen zu hinterlassen" false \
            "Zeile '${_REST}', ${_ORPHANS} verwaiste Kurse"
    fi
}

runChecks() {
    trap cleanup EXIT INT TERM

    echo
    echo -e "${LIGHT_BLUE}T-35 — die Verify-Matrix über die REST-Schnittstelle${NC}  (Profil ${PROFILE})"
    echo

    prepareVolume || return 1
    startServer || return 1
    echo

    checkTestData
    checkTestDataCatchesErrors
    checkChain
    checkIntake
    checkChainProvesItself
    checkHomeExchange
    checkUnresolvable
    checkOverrideAndCache
    checkDailyAndFx
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
