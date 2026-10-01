#!/bin/sh
#------------------------------------------------------------------------------
# entrypoint.sh — Bereitet /data vor und startet die App ohne Root-Rechte
#
# Als root (Standard, auch unter Unraid): PUID/PGID prüfen (Vorgabe 99/100 =
# Unraid nobody:users), /data nur bei abweichendem Eigentümer übergeben, als
# Zielbenutzer schreiben probieren und die App dann per setpriv starten.
# Mit --user gestartet: kein Rechtewechsel, nur die Schreibprobe.
#
# Jeder Abbruch geschieht vor dem App-Start und nennt Ordner, IDs und Abhilfe.
# Die Meldungen sind englisch wie die übrige Containerausgabe und Doku.
#------------------------------------------------------------------------------
set -eu

readonly DATA_DIR=/data
readonly DATABASE_FILE="${DATABASE_PATH:-${DATA_DIR}/stockinfo.db}"

# Gibt eine Meldung mit Präfix auf stderr aus.
# Params: $1 Stufe (ERROR|WARNING), $2 Text.
log() {
    printf 'entrypoint %s: %s\n' "$1" "$2" >&2
}

# Bricht vor dem App-Start ab.
# Params: $1 Text.
fail() {
    log ERROR "$1"
    exit 1
}

# Prüft eine ID: nur Ziffern, nicht 0.
# Params: $1 Variablenname, $2 Wert.
validateId() {
    case "$2" in
        '' | *[!0-9]*) fail "$1 must be a positive number, got '$2'." ;;
    esac
    [ "$2" -ne 0 ] || fail "$1=0 would run the app as root; use a non-root ID (default 99/100)."
}

# Führt einen Befehl als Zielbenutzer aus, ohne Root-Gruppen.
# Params: $1 UID, $2 GID, weitere Argumente: Befehl.
runAs() {
    _UID="$1"
    _GID="$2"
    shift 2
    setpriv --reuid "${_UID}" --regid "${_GID}" --clear-groups "$@"
}

# Probiert als aktueller Prozess, ob /data und eine vorhandene Datenbank
# beschreibbar sind. Wird direkt oder über runAs aufgerufen.
# Params: $1 Datenordner, $2 Datenbankdatei, $3 Beschreibung der IDs,
#         $4 Abhilfe passend zum Startweg.
probeWritable() {
    _PROBE="$1/.write-test.$$"
    # touch statt ': >': Eine scheiternde Umleitung beendet sh beim Spezialbefehl ':'.
    if ! touch "${_PROBE}" 2>/dev/null; then
        fail "$1 is not writable for $3. Make the mounted host directory writable for these IDs, or $4."
    fi
    rm -f "${_PROBE}"
    if [ -e "$2" ] && [ ! -w "$2" ]; then
        fail "$2 is not writable for $3. Change its owner to these IDs, or $4."
    fi
}

# Als Unterprozess der Schreibprobe aufgerufen (siehe runAs unten).
if [ "${1:-}" = "--probe-writable" ]; then
    shift
    probeWritable "$@"
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    probeWritable "${DATA_DIR}" "${DATABASE_FILE}" "UID $(id -u) / GID $(id -g) (started with --user)" \
        "start the container with --user set to the owner of ${DATA_DIR}"
    exec "$@"
fi

PUID="${PUID:-99}"
PGID="${PGID:-100}"
validateId PUID "${PUID}"
validateId PGID "${PGID}"
readonly IDS="UID ${PUID} / GID ${PGID}"

# Nur übergeben, was nicht schon dem Zielbenutzer gehört.
if [ -n "$(find "${DATA_DIR}" \( ! -uid "${PUID}" -o ! -gid "${PGID}" \) -print -quit 2>/dev/null)" ]; then
    if ! chown -R "${PUID}:${PGID}" "${DATA_DIR}" 2>/dev/null; then
        log WARNING "could not change the owner of ${DATA_DIR} to ${IDS} (e.g. NFS/SMB or missing CHOWN capability); continuing if it is writable."
    fi
fi

if ! runAs "${PUID}" "${PGID}" true 2>/dev/null; then
    fail "cannot switch to ${IDS}: the container needs the SETUID and SETGID capabilities, or start it with --user ${PUID}:${PGID}."
fi

runAs "${PUID}" "${PGID}" "$0" --probe-writable "${DATA_DIR}" "${DATABASE_FILE}" "${IDS}" \
    "set PUID/PGID to the owner of ${DATA_DIR}"

exec setpriv --reuid "${PUID}" --regid "${PGID}" --clear-groups "$@"
