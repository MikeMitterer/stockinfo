#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-21-smoke.sh — Die Identitäts-Migration gegen einen echten Bestand prüfen
#
# Die Migration ist die einzige der Serie, die bestehende Daten anfasst. Ein
# synthetischer Testbestand zeigt, dass die Regeln stimmen; er zeigt **nicht**,
# was ein gewachsener Bestand an Sonderfällen mitbringt.
#
# Dieses Script arbeitet deshalb auf einer **Kopie** der Arbeits-Datenbank.
# Die Originaldatei wird nur gelesen, nie geöffnet zum Schreiben — ein
# Prüf-Script darf an echten Daten nichts verändern.
#
# Verwendung:
#   ./_tickets/T-21-smoke.sh --run
#   DATABASE_PATH=/pfad/zur/anderen.db ./_tickets/T-21-smoke.sh --run
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep       Kopie nach dem Lauf stehen lassen
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
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"
readonly QUELLE="${DATABASE_PATH:-${PROJECT_ROOT}/data/stockinfo.db}"

COUNT_OK=0
COUNT_FAIL=0
WORKDIR=""
KEEP=false

# Zeigt die Verwendungshinweise an.
usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Migration gegen eine Kopie des Bestands prüfen"
    usageLine "-k | --keep      " "Kopie nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Andere DB:     ${GREEN}DATABASE_PATH=/pfad/zur/db ${APPNAME} --run${NC}"
    echo
    echo -e "    Die Originaldatei wird ${YELLOW}nur gelesen${NC}. Gearbeitet wird auf einer"
    echo -e "    Kopie in einem temporären Verzeichnis."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Datenbank:   " "${QUELLE}"
    echo
}

# Räumt die Kopie ab. Wird per trap aufgerufen.
cleanup() {
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Kopie: ${WORKDIR}/kopie.db"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
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

# Führt die Migration auf der Kopie aus und prüft das Ergebnis.
#
# Die eigentliche Arbeit macht Python: Zählen vorher, zweimal migrieren,
# Zählen nachher, Eindeutigkeit prüfen. Ausgegeben wird eine Zeile je Check
# im Format `KENNUNG|ok|text`.
#
# Der Wechsel ins Projektverzeichnis ist Pflicht, kein Stil: `app.db` liegt
# relativ dazu, und ohne ihn scheitert schon der Import.
runMigration() {
    cd "${PROJECT_ROOT}" || return 1
    "${VENV_PY}" - "$1" <<'PYTHON'
import sqlite3
import sys

from app.db import init_db

pfad = sys.argv[1]


# Vorher zählen, nicht lesen: Die neuen Spalten gibt es an dieser Stelle
# naturgemäß noch nicht.
with sqlite3.connect(pfad) as verbindung:
    vorher = verbindung.execute("SELECT COUNT(*) FROM instruments").fetchone()[0]
    kurse_vorher = verbindung.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]

init_db(pfad)
init_db(pfad)  # zweiter Start — hier hat die Alt-Bereinigung Listings gelöscht

with sqlite3.connect(pfad) as verbindung:
    verbindung.row_factory = sqlite3.Row
    nachher = verbindung.execute(
        "SELECT symbol, ticker, mic, identity_status, listing_id FROM instruments"
    ).fetchall()
    kurse_nachher = verbindung.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    indizes = {
        r[1] for r in verbindung.execute("PRAGMA index_list(instruments)")
    }

aufgeloest = [r for r in nachher if r["identity_status"] == "resolved"]
offen = [r for r in nachher if r["identity_status"] == "legacy_unresolved"]
ids = [r["listing_id"] for r in nachher]

print(f"#1a|{vorher == len(nachher)}|Instrumente vorher {vorher}, nachher {len(nachher)}")
print(f"#1b|{kurse_vorher == kurse_nachher}|Kurspunkte vorher {kurse_vorher}, nachher {kurse_nachher}")
print(f"#1c|{all(ids) and len(set(ids)) == len(ids)}|listing_id: {len(set(ids))} eindeutige für {len(nachher)} Zeilen")
print(
    f"#2 |{all(r['ticker'] and r['mic'] for r in aufgeloest)}|"
    f"{len(aufgeloest)} zerlegt: "
    + ", ".join(f"{r['symbol']}→{r['ticker']}/{r['mic']}" for r in aufgeloest)
)
print(
    f"#2b|{all(r['ticker'] is None and r['mic'] is None for r in offen)}|"
    f"{len(offen)} offen, nichts geraten: "
    + (", ".join(r["symbol"] for r in offen) or "keine")
)
print(
    f"#3b|{'idx_instruments_symbol' not in indizes and 'idx_instruments_ticker_mic' in indizes}|"
    f"Indizes: {', '.join(sorted(indizes))}"
)
PYTHON
}

# Fährt die Prüfung durch.
runChecks() {
    echo
    echo -e "${CYAN}▶ T-21 · Migration gegen einen echten Bestand${NC}"
    echo

    if [[ ! -f "${QUELLE}" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Keine Datenbank unter ${QUELLE}."
        echo -e "      Ohne echten Bestand ist hier nichts zu prüfen — die Regeln"
        echo -e "      selbst deckt ${GREEN}pytest tests/test_identity_migration.py${NC} ab."
        echo
        return 0
    fi

    WORKDIR="$(mktemp -d)"
    cp "${QUELLE}" "${WORKDIR}/kopie.db"
    echo -e "  ${BLUE}ℹ${NC} Kopie von ${QUELLE}"
    echo -e "  ${BLUE}ℹ${NC} Das Original wird nicht angefasst"
    echo

    local _LINE _OK _TEXT
    while IFS='|' read -r _LINE _OK _TEXT; do
        # Nur die eigenen Checkzeilen: Die Migration protokolliert selbst nach
        # stdout, und ihre Meldungen sind keine Prüfergebnisse.
        [[ "${_LINE}" != \#* ]] && continue
        report "${_LINE}" "$(echo "${_TEXT}" | cut -c1-100)" \
            "$([[ "${_OK}" == "True" ]] && echo true || echo false)" "${_TEXT}"
    done < <(runMigration "${WORKDIR}/kopie.db" 2>"${WORKDIR}/fehler.log")

    echo
    if [[ ${COUNT_FAIL} -eq 0 && ${COUNT_OK} -gt 0 ]]; then
        echo -e "  ${GREEN}✓ ${COUNT_OK} Checks bestanden, keine Fehler${NC}"
    elif [[ ${COUNT_OK} -eq 0 ]]; then
        # Ohne diese Ausgabe stünde hier nur „keine Ausgabe" — und der Grund
        # (ein Importfehler etwa) bliebe unsichtbar.
        echo -e "  ${RED}✗ Die Migration lieferte keine Ausgabe:${NC}"
        grep -v "^20" "${WORKDIR}/fehler.log" | tail -8
        COUNT_FAIL=1
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
        -k|--keep) KEEP=true; shift ;;
        -r|--run)  shift; runChecks; exit $? ;;
        -i|--info) showInfo; exit 0 ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unbekannte Option: $1${NC}" >&2; usage; exit 1 ;;
    esac
done

usage
