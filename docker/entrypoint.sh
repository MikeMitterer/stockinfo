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

readonly MAX_ID=4294967294

# Gibt eine Meldung mit Präfix auf stderr aus.
# Params: $1 Stufe (ERROR|WARNING), $2 Text.
# Returns: 0.
log() {
    printf 'entrypoint %s: %s\n' "$1" "$2" >&2
}

# Bricht vor dem App-Start ab.
# Params: $1 Text.
# Returns: kehrt nicht zurück; beendet den Container mit Exit 1.
fail() {
    log ERROR "$1"
    exit 1
}

# Prüft eine ID: nur Ziffern, 1 bis MAX_ID. Längenprüfung vor dem
# Zahlenvergleich, damit sehr große Werte nicht als 0 erscheinen.
# Params: $1 Variablenname, $2 Wert.
# Returns: 0 bei gültigem Wert, sonst Abbruch über fail.
validateId() {
    case "$2" in
        '' | *[!0-9]*) fail "$1 must be a number from 1 to ${MAX_ID}, got '$2'." ;;
    esac
    if [ "${#2}" -gt 10 ] || [ "$2" -gt "${MAX_ID}" ]; then
        fail "$1 must be a number from 1 to ${MAX_ID}, got '$2'."
    fi
    [ "$2" -ne 0 ] || fail "$1=0 would run the app as root; use a non-root ID (default 99/100)."
}

# Führt einen Befehl als Zielbenutzer aus, ohne Root-Gruppen.
# Params: $1 UID, $2 GID, weitere Argumente: Befehl.
# Returns: Exit-Code des Befehls; ungleich 0 auch, wenn setpriv scheitert.
runAs() {
    _UID="$1"
    _GID="$2"
    shift 2
    setpriv --reuid "${_UID}" --regid "${_GID}" --clear-groups "$@"
}

# Beschreibt eine ausführbare Abhilfe für einen nicht beschreibbaren Pfad.
# Gehört er schon den Ziel-IDs, fehlt nur das Schreibrecht: chmod auf dem Host.
# Gehört er root, hilft nur ein chown auf dem Host. Sonst kann der Container
# auch die IDs des Eigentümers übernehmen.
# Params: $1 Pfad, $2 Ziel als UID:GID, $3 Startweg (puid|user).
# Returns: 0; gibt den Text auf stdout aus.
remedyFor() {
    _OWNER="$(stat -c '%u:%g' "$1")"
    _HOST_FIX="change the owner of the mounted host path to $2 (for example: chown -R $2 <host path>)"
    if [ "${_OWNER}" = "$2" ]; then
        printf 'it already belongs to %s but lacks write permission; add it on the host (for example: chmod -R u+rwX <host path>)' "$2"
    elif [ "${_OWNER%%:*}" -eq 0 ]; then
        printf '%s' "${_HOST_FIX}"
    elif [ "$3" = puid ]; then
        printf '%s, or set PUID=%s PGID=%s to match its current owner' "${_HOST_FIX}" "${_OWNER%%:*}" "${_OWNER##*:}"
    else
        printf '%s, or start the container with --user %s to match its current owner' "${_HOST_FIX}" "${_OWNER}"
    fi
}

# Probiert als aktueller Prozess, ob /data und eine vorhandene Datenbank
# beschreibbar sind. Wird direkt oder über runAs aufgerufen.
# Params: $1 Datenordner, $2 Datenbankdatei, $3 Ziel als UID:GID,
#         $4 Startweg (puid|user).
# Returns: 0, wenn beides beschreibbar ist, sonst Abbruch über fail.
probeWritable() {
    _IDS="UID ${3%%:*} / GID ${3##*:}"
    _PROBE="$1/.write-test.$$"
    # touch statt ': >': Eine scheiternde Umleitung beendet sh beim Spezialbefehl ':'.
    if ! touch "${_PROBE}" 2>/dev/null; then
        fail "$1 is not writable for ${_IDS}. To fix: $(remedyFor "$1" "$3" "$4")."
    fi
    rm -f "${_PROBE}"
    if [ -e "$2" ] && [ ! -w "$2" ]; then
        fail "$2 is not writable for ${_IDS}. To fix: $(remedyFor "$2" "$3" "$4")."
    fi
}

# Als Unterprozess der Schreibprobe aufgerufen (siehe runAs unten).
if [ "${1:-}" = "--probe-writable" ]; then
    shift
    probeWritable "$@"
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    probeWritable "${DATA_DIR}" "${DATABASE_FILE}" "$(id -u):$(id -g)" user
    exec "$@"
fi

# Nur ein nicht gesetzter Wert fällt auf die Vorgabe zurück; ein ausdrücklich
# leerer Wert ist ein Konfigurationsfehler.
PUID="${PUID-99}"
PGID="${PGID-100}"
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
    fail "cannot switch to ${IDS} to use ${DATA_DIR}: the container lacks the SETUID and SETGID capabilities. To fix: remove --cap-drop for SETUID/SETGID, or start the container with --user ${PUID}:${PGID} and make ${DATA_DIR} writable for that user."
fi

runAs "${PUID}" "${PGID}" "$0" --probe-writable "${DATA_DIR}" "${DATABASE_FILE}" "${PUID}:${PGID}" puid

exec setpriv --reuid "${PUID}" --regid "${PGID}" --clear-groups "$@"
