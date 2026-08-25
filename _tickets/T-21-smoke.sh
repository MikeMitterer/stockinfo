#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-21-smoke.sh — Die Identitäts-Migration gegen einen echten Bestand prüfen
#
# Die Migration ist die einzige der Serie, die bestehende Daten anfasst. Ein
# synthetischer Testbestand zeigt, dass die Regeln stimmen; er zeigt **nicht**,
# was ein gewachsener Bestand an Sonderfällen mitbringt.
#
# Gearbeitet wird auf einer **Sicherung** der Arbeits-Datenbank, erzeugt über
# die SQLite-Backup-API. Ein `cp` der Hauptdatei würde nicht genügen: Die App
# läuft im WAL-Modus, und committete Änderungen können noch im WAL stehen —
# die Prüfung liefe dann an genau den neuesten Sonderfällen vorbei und meldete
# trotzdem Vollständigkeit.
#
# Die Originaldatei wird nur gelesen.
#
# Verwendung:
#   ./_tickets/T-21-smoke.sh --run
#   DATABASE_PATH=/pfad/zur/anderen.db ./_tickets/T-21-smoke.sh --run
#
# Optionen:
#   -r | --run        Checks ausführen
#   -k | --keep       Sicherung nach dem Lauf stehen lassen
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
readonly SOURCE_DB="${DATABASE_PATH:-${PROJECT_ROOT}/data/stockinfo.db}"

COUNT_OK=0
COUNT_FAIL=0
WORKDIR=""
KEEP=false

# Zeigt die Verwendungshinweise an.
usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-r | --run       " "Migration gegen eine Sicherung des Bestands prüfen"
    usageLine "-k | --keep      " "Sicherung nach dem Lauf stehen lassen"
    usageLine "-i | --info      " "Einstellungen anzeigen"
    usageLine "-h | --help      " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Lauf:          ${GREEN}${APPNAME} --run${NC}"
    echo -e "    Andere DB:     ${GREEN}DATABASE_PATH=/pfad/zur/db ${APPNAME} --run${NC}"
    echo
    echo -e "    Ein ${YELLOW}leerer${NC} Bestand lässt den Lauf fehlschlagen — er würde sonst"
    echo -e "    grün melden, ohne einen einzigen Migrationsfall geprüft zu haben."
    echo
}

# Zeigt die wichtigsten Einstellungen des Scripts an.
showInfo() {
    echo
    logFileStatus "Projekt-Root:" "${PROJECT_ROOT}"
    logFileStatus "Datenbank:   " "${SOURCE_DB}"
    echo
}

# Räumt die Sicherung ab. Wird per trap aufgerufen.
cleanup() {
    if [[ -n "${WORKDIR}" && -d "${WORKDIR}" ]]; then
        if [[ "${KEEP}" == true ]]; then
            echo -e "  ${BLUE}ℹ${NC} Sicherung: ${WORKDIR}/backup.db"
        else
            rm -rf "${WORKDIR}"
        fi
    fi
}

# Meldet das Ergebnis eines Checks und zählt mit.
#
# Params:
#   $1 - Kennung, $2 - Beschreibung, $3 - true wenn bestanden, $4 - beobachtet
report() {
    local -r _LINE="$1"
    local -r _WHAT="$2"
    local -r _OK="$3"
    local -r _ACTUAL="$4"

    if [[ "${_OK}" == true ]]; then
        COUNT_OK=$((COUNT_OK + 1))
        echo -e "  ${GREEN}✓${NC} ${_LINE} ${_WHAT}"
    else
        COUNT_FAIL=$((COUNT_FAIL + 1))
        echo -e "  ${RED}✗${NC} ${_LINE} ${_WHAT}"
        [[ -n "${_ACTUAL}" ]] && echo -e "      ${RED}beobachtet:${NC} ${_ACTUAL}"
    fi
}

# Sichert die Datenbank und führt die Migration auf der Sicherung aus.
#
# Die Prüfungen rechnen die Erwartung **selbst nach**, statt sie zu behaupten,
# und zwar in der **Gegenrichtung** zur Migration: Diese zerlegt `symbol` in
# `(ticker, mic)`, die Prüfung setzt es daraus wieder zusammen — mit einer
# hier eigens formulierten Regel, nicht mit der Funktion des Produkts. Geprüft wird
# nur, was dieser Lauf zugeordnet hat; bereits bestehende — etwa von Hand
# gesetzte — Zuordnungen werden nicht nachvalidiert, sondern nur darauf, dass
# sie unverändert blieben und keinen Sammelcode tragen.
#
# Ein Lauf, der nichts zugeordnet hat, gilt als **nicht geprüft**, nicht als
# bestanden.
#
# Ausgabe je Check: `KENNUNG|True|False|Text`.
runMigration() {
    cd "${PROJECT_ROOT}" || return 1
    "${VENV_PY}" - "$1" "$2" <<'PYTHON'
import sqlite3
import string
import sys

from app.db import init_db
from app.exchanges import EXCHANGES

source, backup = sys.argv[1], sys.argv[2]

# Transaktionskonsistente Sicherung über die Backup-API. `cp` würde committete
# Einträge im WAL auslassen — der Lauf liefe dann an den neuesten Fällen vorbei
# und meldete trotzdem Vollständigkeit.
with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as origin:
    with sqlite3.connect(backup) as target:
        origin.backup(target)


def check(name: str, ok: bool, text: str) -> None:
    print(f"{name}|{ok}|{text}")


def state_before(connection: sqlite3.Connection) -> dict[int, dict]:
    """Der Zustand je Zeile **vor** der Migration.

    Auf einer Alt-Datenbank gibt es die Identitätsspalten noch nicht — dann
    gilt jede Zeile als unbetrachtet. Nur so lässt sich hinterher sagen,
    welche Zeile *dieser* Lauf zugeordnet hat.
    """
    connection.row_factory = sqlite3.Row
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
    }
    has_identity = {"ticker", "mic", "identity_status"} <= columns
    selection = (
        "id, symbol, ticker, mic, identity_status"
        if has_identity
        else "id, symbol, NULL AS ticker, NULL AS mic, NULL AS identity_status"
    )
    return {
        row["id"]: dict(row)
        for row in connection.execute(f"SELECT {selection} FROM instruments")
    }


with sqlite3.connect(backup) as connection:
    before = state_before(connection)
    quotes_before = connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]

# Ein leerer Bestand ist kein bestandener Lauf, sondern ein ungeprüfter.
if not before:
    check("#0 ", False, f"{source} enthält keine Instrumente — nichts zu prüfen")
    sys.exit(0)

init_db(backup)
init_db(backup)  # zweiter Start — dort hat die Alt-Bereinigung Zeilen gelöscht

with sqlite3.connect(backup) as connection:
    connection.row_factory = sqlite3.Row
    after = {
        row["id"]: dict(row)
        for row in connection.execute(
            "SELECT id, symbol, isin, ticker, mic, identity_status, listing_id "
            "FROM instruments"
        )
    }
    quotes_after = connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    indexes = {
        index["name"]: index["unique"]
        for index in connection.execute("PRAGMA index_list(instruments)")
    }

listing_ids = [row["listing_id"] for row in after.values()]
# Nur die Zeilen, die **dieser** Lauf zugeordnet hat. Was schon eine Identität
# trug — etwa von Hand gesetzt — wird nicht nachvalidiert.
newly_resolved = [
    row
    for identifier, row in after.items()
    if row["identity_status"] == "resolved"
    and not before.get(identifier, {}).get("identity_status")
]
still_open = [row for row in after.values() if row["identity_status"] == "legacy_unresolved"]
preexisting = [
    (before[identifier], row)
    for identifier, row in after.items()
    if before.get(identifier, {}).get("identity_status")
]

check("#0 ", True, f"{len(before)} Instrumente, {quotes_before} Kurspunkte im Bestand")
check(
    "#1a", len(after) == len(before),
    f"Instrumente vorher {len(before)}, nachher {len(after)}",
)
check(
    "#1b", quotes_after == quotes_before,
    f"Kurspunkte vorher {quotes_before}, nachher {quotes_after}",
)
check(
    "#1c",
    all(listing_ids) and len(set(listing_ids)) == len(after),
    f"listing_id: {len(set(listing_ids))} eindeutige für {len(after)} Zeilen",
)

def composed(row: dict) -> str | None:
    """Setzt `symbol` aus `(ticker, mic)` zusammen — die Gegenrichtung.

    ``None`` für einen MIC, den die eigene Tabelle nicht kennt — dann ist die
    Zusammensetzung keine Aussage.

    Seit T-21 Teil 3 kennt die Tabelle auch die fünf US-Plätze, `XNAS` steht
    also nicht mehr darin fehl.

    **Die Regel steht hier absichtlich noch einmal**, statt `provider_alias`
    aufzurufen. Das ist keine übersehene Dopplung: Ein Orakel, das die geprüfte
    Funktion benutzt, bestätigt nur, dass sie mit sich selbst übereinstimmt —
    ein falsch gesetzter Punkt oder ein vertauschter Alias träte im Produkt und
    in der Gegenrechnung gleich auf und bliebe grün. Nachgeschlagen wird nur
    die Tabelle; sie ist Daten, nicht die geprüfte Logik.
    """
    if row["mic"] not in EXCHANGES:
        return None
    alias = EXCHANGES[row["mic"]].alias
    return f"{row['ticker']}.{alias}" if alias else row["ticker"]


# Jede Zeile muss nach dem Lauf in **genau einem** gültigen Zustand sein.
# Nur auf den Sammelcode zu prüfen genügte nicht: Eine Zeile, die `resolved`
# behauptet und weder Ticker noch MIC trägt, käme sonst durch — und die
# Migration überspringt sie beim nächsten Start wieder.
# Eigenes MIC-Urteil, bewusst **ohne** `is_real_mic`: Ein Orakel darf nicht
# die Funktion befragen, die es prüft. Sonst bestätigt es nur, dass sie mit
# sich selbst übereinstimmt — ein fehlerhafter regulärer Ausdruck bliebe
# unsichtbar (Codex, Runde 8). Formuliert ist die Regel deshalb anders:
# Zeichenmenge statt Muster.
MIC_CHARACTERS = set(string.ascii_uppercase + string.digits)
# **Bewusst als Literal**, nicht aus der App geholt. Dieses Script prüft die
# Migration von außen; übernähme es die Liste des Produktcodes, prüfte es die
# Regel gegen sich selbst. Kommt ein Sammelcode dazu, gehört diese Zeile
# angefasst — und genau das soll auffallen.
#
# Vorher stand hier eine Ableitung aus `ExchangeDef.figi_id_type`. Die Spalte
# ist mit T-21 Teil 2b zum OpenFIGI-Provider gezogen, und die Ableitung ließ
# das Script mitten im Lauf abstürzen.
COLLECTOR_CODES = {"US"}


def looks_like_mic(mic: str | None) -> bool:
    """Vier Zeichen aus `A-Z0-9`, und kein interner Sammelcode."""
    if not mic or len(mic) != 4 or set(mic) - MIC_CHARACTERS:
        return False
    return mic not in COLLECTOR_CODES


def invalid_state(row: dict) -> str | None:
    """Nennt den Widerspruch einer Zeile, oder ``None`` wenn sie stimmig ist."""
    status = row["identity_status"]
    if status == "resolved":
        if not row["ticker"] or not row["mic"]:
            return f"{row['symbol']}: resolved ohne vollständige Identität"
        if not looks_like_mic(row["mic"]):
            return f"{row['symbol']}: {row['mic']!r} ist kein echter MIC"
        return None
    if status == "legacy_unresolved":
        if row["ticker"] or row["mic"]:
            return f"{row['symbol']}: offen, trägt aber eine Identität"
        return None
    return f"{row['symbol']}: unbekannter Status {status!r}"


resolved_rows = [row for row in after.values() if row["identity_status"] == "resolved"]
broken_states = [
    problem for problem in (invalid_state(row) for row in after.values()) if problem
]
wrongly_resolved = [
    f"{row['symbol']}≠{composed(row)}"
    for row in newly_resolved
    if composed(row) != row["symbol"]
]
wrongly_open = [row["symbol"] for row in still_open if row["ticker"] or row["mic"]]
changed = [
    f"{old['symbol']}: {old['ticker']}/{old['mic']} → {new['ticker']}/{new['mic']}"
    for old, new in preexisting
    if (old["ticker"], old["mic"]) != (new["ticker"], new["mic"])
]

# Ein Lauf, der nichts zugeordnet hat, hat die Migration nicht geprüft. Das
# passiert, wenn die Quelle schon migriert war — dann ist die Antwort „nicht
# geprüft", nicht „bestanden".
check(
    "#2 ",
    bool(newly_resolved) and not wrongly_resolved,
    f"{len(newly_resolved)} neu zerlegt, vorwärts gegengerechnet: "
    + (
        ", ".join(
            f"{row['ticker']}/{row['mic']}→{row['symbol']}" for row in newly_resolved
        )
        or "keine — der Bestand war bereits migriert, die Zerlegung ist ungeprüft"
    )
    + (f" — falsch: {wrongly_resolved}" if wrongly_resolved else ""),
)
check(
    "#2d",
    not broken_states,
    f"{len(after)} Zeilen in gültigem Zustand "
    f"({len(resolved_rows)} zugeordnet, {len(still_open)} offen)"
    + (f" — widersprüchlich: {broken_states}" if broken_states else ""),
)
check(
    "#2b",
    not wrongly_open,
    f"{len(still_open)} offen, nichts geraten: "
    + (", ".join(row["symbol"] for row in still_open) or "keine")
    + (f" — zu Unrecht offen: {wrongly_open}" if wrongly_open else ""),
)
check(
    "#2c",
    not changed,
    f"{len(preexisting)} bereits zugeordnete Zeilen unverändert"
    + (f" — verändert: {changed}" if changed else ""),
)
check(
    "#3b",
    "idx_instruments_symbol" not in indexes
    and indexes.get("idx_instruments_ticker_mic") == 1
    and indexes.get("idx_instruments_listing_id") == 1,
    "Indizes (1 = eindeutig): "
    + ", ".join(f"{name}={flag}" for name, flag in sorted(indexes.items())),
)

# Schlussmarke. Ohne sie ist ein Abbruch mitten im Lauf von einem vollständigen
# Lauf nicht zu unterscheiden: Die Shell liest, was schon kam, zählt es und
# meldet „keine Fehler" — ein Script, das vier von neun Prüfungen geschafft
# hat, sieht dann aus wie eines, das alle bestanden hat.
#
# Genau das ist am 2026-08-23 passiert, als der Umbau aus Teil 2b eine
# Spalte entfernte, die dieses Script noch las.
print("#ende|True|alle Prüfungen durchlaufen")
PYTHON
}

# Fährt die Prüfung durch.
runChecks() {
    echo
    echo -e "${CYAN}▶ T-21 · Migration gegen einen echten Bestand${NC}"
    echo

    if [[ ! -f "${SOURCE_DB}" ]]; then
        echo -e "  ${RED}✗${NC} Keine Datenbank unter ${SOURCE_DB}."
        echo -e "      Ohne echten Bestand ist hier nichts zu prüfen — die Regeln"
        echo -e "      selbst deckt ${GREEN}pytest tests/test_identity_migration.py${NC} ab."
        echo
        return 1
    fi

    WORKDIR="$(mktemp -d)"
    echo -e "  ${BLUE}ℹ${NC} Sicherung von ${SOURCE_DB} über die SQLite-Backup-API"
    echo -e "  ${BLUE}ℹ${NC} Das Original wird nur gelesen"
    echo

    local _LINE _OK _TEXT
    local _COMPLETE=false
    while IFS='|' read -r _LINE _OK _TEXT; do
        # Nur die eigenen Checkzeilen: Die Migration protokolliert selbst nach
        # stdout, und ihre Meldungen sind keine Prüfergebnisse.
        [[ "${_LINE}" != \#* ]] && continue
        if [[ "${_LINE}" == "#ende" ]]; then
            _COMPLETE=true
            continue
        fi
        report "${_LINE}" "${_TEXT}" \
            "$([[ "${_OK}" == "True" ]] && echo true || echo false)" "${_TEXT}"
    done < <(runMigration "${SOURCE_DB}" "${WORKDIR}/backup.db" 2>"${WORKDIR}/errors.log")

    # Ein abgebrochener Lauf hat nicht bestanden — er hat aufgehört. Ohne diese
    # Prüfung zählt die Schleife die Ergebnisse, die noch kamen, und meldet
    # „keine Fehler".
    if [[ "${_COMPLETE}" != true && ${COUNT_OK} -gt 0 ]]; then
        echo
        echo -e "  ${RED}✗${NC} Der Lauf brach nach ${COUNT_OK} Prüfungen ab:"
        grep -v "^20" "${WORKDIR}/errors.log" | tail -8
        COUNT_FAIL=$((COUNT_FAIL + 1))
    fi

    echo
    if [[ ${COUNT_OK} -eq 0 && ${COUNT_FAIL} -eq 0 ]]; then
        # Ohne diese Ausgabe stünde hier nur „keine Ausgabe" — und der Grund
        # (ein Importfehler etwa) bliebe unsichtbar.
        echo -e "  ${RED}✗ Die Migration lieferte keine Ausgabe:${NC}"
        grep -v "^20" "${WORKDIR}/errors.log" | tail -8
        COUNT_FAIL=1
    elif [[ ${COUNT_FAIL} -eq 0 ]]; then
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
        -k|--keep) KEEP=true; shift ;;
        -r|--run)  shift; runChecks; exit $? ;;
        -i|--info) showInfo; exit 0 ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unbekannte Option: $1${NC}" >&2; usage; exit 1 ;;
    esac
done

usage
