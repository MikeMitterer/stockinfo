#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-86-smoke.sh — Containerstart bei Rechteproblemen nachstellen (A1–A11)
#
# Baut ein eigenes Testimage aus dem Arbeitsstand und startet je Fall einen
# eigenen Container. /data ist ein tmpfs oder ein eigenes Testvolume. Danach
# werden nur diese Container und Volumes entfernt; nichts wird gepusht.
#
# Verwendung:
#   ./_tickets/30-doing/T-86-smoke.sh --run
#   IMAGE_REF=mangolila/stockinfo:latest ./_tickets/30-doing/T-86-smoke.sh --run
#
# Optionen:
#   -r | --run    Testimage bauen (ohne IMAGE_REF) und alle Fälle prüfen
#   -h | --help   Diese Hilfe anzeigen; auch ohne Argumente
#
# Umgebung:
#   IMAGE_REF       Vorhandenes Image prüfen statt selbst zu bauen
#   SMOKE_PLATFORM  Plattform des Testbuilds (Standard: linux/amd64)
#------------------------------------------------------------------------------
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT_DIR
BASH_LIBS="${BASH_LIBS:-${ROOT_DIR}/.libs/BashLib/src}"
# shellcheck disable=SC1091  # Pfad kommt aus der Umgebung oder dem lokalen Link.
if [[ "${__TOOLS_LIB__:=}" == "" ]]; then . "${BASH_LIBS}/tools.lib.sh"; fi

readonly APPNAME="${0##*/}"
readonly PREFIX="si-t86-$$"
readonly PLATFORM="${SMOKE_PLATFORM:-linux/amd64}"
IMAGE="${IMAGE_REF:-stockinfo-t86:smoke}"
readonly IMAGE
FAILURES=0
OWN_VOLUMES=()

usage() {
    printf '\nUsage: %s [ options ]\n' "${APPNAME}"
    printThemeHeading 'Optionen'
    printThemeRow '-r | --run' 'Testimage bauen (ohne IMAGE_REF) und A1–A11 prüfen'
    printThemeRow '-h | --help' 'Diese Hilfe anzeigen'
    printThemeHeading 'Umgebung'
    printThemeRow 'IMAGE_REF' 'Vorhandenes Image prüfen statt selbst zu bauen'
    printThemeRow 'SMOKE_PLATFORM' "Plattform des Testbuilds (Standard: ${PLATFORM})"
    printf '\n'
}

# Entfernt nur die eigenen Container und Volumes dieses Laufs.
cleanupSmoke() {
    local _NAME _VOLUME
    for _NAME in $(docker ps -aq --filter "name=^${PREFIX}-"); do
        docker rm -f "${_NAME}" >/dev/null 2>&1 || true
    done
    for _VOLUME in "${OWN_VOLUMES[@]+"${OWN_VOLUMES[@]}"}"; do
        docker volume rm "${_VOLUME}" >/dev/null 2>&1 || true
    done
}

# Meldet ein Ergebnis und zählt Fehlschläge.
# Params: $1 Fall, $2 0 = bestanden, $3 Beschreibung.
report() {
    if [[ $2 -eq 0 ]]; then
        printThemeStatus '✓' "$1 $3" SUCCESS
    else
        printThemeStatus '✗' "$1 $3" DANGER
        FAILURES=$((FAILURES + 1))
    fi
}

# Startet einen Container und wartet, bis er läuft oder endet.
# Params: $1 Fall, weitere: docker-run-Argumente. Gibt den Namen aus.
startCase() {
    local -r _NAME="${PREFIX}-$1"
    shift
    docker run -d --platform "${PLATFORM}" --name "${_NAME}" "$@" "${IMAGE}" >/dev/null
    local _ATTEMPT
    for ((_ATTEMPT = 1; _ATTEMPT <= 40; _ATTEMPT++)); do
        if [[ $(docker inspect -f '{{.State.Status}}' "${_NAME}") != running ]]; then break; fi
        if docker exec "${_NAME}" curl -fsS -o /dev/null http://localhost:8000/operational >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    printf '%s' "${_NAME}"
}

# Liefert UID:GID aller App-Prozesse (ohne Probe-Shell), eine Zeile je Prozess.
# Params: $1 Containername.
processIds() {
    docker exec "$1" sh -c 'for P in /proc/[0-9]*; do
        [ "$P" = "/proc/$$" ] && continue
        C=$(tr "\0" " " < "$P/cmdline" 2>/dev/null) || continue
        case "$C" in *uvicorn*) awk "/^Uid:/{u=\$2}/^Gid:/{g=\$2}END{print u\":\"g}" "$P/status";; esac
    done' | sort -u
}

# Erwartet einen laufenden Container mit Prozess- und Datei-IDs.
# Params: $1 Fall, $2 erwartete UID:GID, weitere: docker-run-Argumente.
expectRunning() {
    local -r _CASE="$1" _IDS="$2"
    shift 2
    local _NAME _PROCS _FILES
    _NAME=$(startCase "${_CASE}" "$@")
    if [[ $(docker inspect -f '{{.State.Status}}' "${_NAME}") != running ]]; then
        report "${_CASE}" 1 "erwartet Start, Container endete: $(docker logs "${_NAME}" 2>&1 | tail -1)"
        return
    fi
    _PROCS=$(processIds "${_NAME}")
    _FILES=$(docker exec "${_NAME}" stat -c '%u:%g' /data /data/stockinfo.db | sort -u)
    if [[ ${_PROCS} == "${_IDS}" && ${_FILES} == "${_IDS}" ]]; then
        report "${_CASE}" 0 "läuft, Prozesse und Dateien ${_IDS}"
    else
        report "${_CASE}" 1 "Prozesse '${_PROCS//$'\n'/,}', Dateien '${_FILES//$'\n'/,}', erwartet ${_IDS}"
    fi
}

# Erwartet einen Abbruch vor dem App-Start mit einer Meldung.
# Params: $1 Fall, $2 erwarteter Text in den Logs, weitere: docker-run-Argumente.
expectFailure() {
    local -r _CASE="$1" _TEXT="$2"
    shift 2
    local _NAME _LOGS _EXIT
    _NAME=$(startCase "${_CASE}" "$@")
    _LOGS=$(docker logs "${_NAME}" 2>&1)
    _EXIT=$(docker inspect -f '{{.State.ExitCode}}' "${_NAME}")
    if [[ $(docker inspect -f '{{.State.Status}}' "${_NAME}") == exited && ${_EXIT} -ne 0 \
        && ${_LOGS} == *"${_TEXT}"* && ${_LOGS} != *"app_started"* ]]; then
        report "${_CASE}" 0 "Abbruch (Exit ${_EXIT}): $(grep -m1 'entrypoint ERROR' <<< "${_LOGS}")"
    else
        report "${_CASE}" 1 "erwartet Abbruch mit '${_TEXT}', Status/Exit ${_EXIT}: $(tail -2 <<< "${_LOGS}")"
    fi
}

# Legt ein Testvolume mit Datenbankdatei im Besitz von root (644) an,
# /data selbst gehört 99:100. Gibt den Volumenamen aus.
prepareRootOwnedDatabase() {
    local _VOLUME
    _VOLUME=$(docker volume create "${PREFIX}-rootdb")
    docker run --rm --platform "${PLATFORM}" --entrypoint sh -v "${_VOLUME}:/data" "${IMAGE}" \
        -c ': > /data/stockinfo.db && chmod 644 /data/stockinfo.db && chown 99:100 /data' >/dev/null
    printf '%s' "${_VOLUME}"
}

runSmoke() {
    trap cleanupSmoke EXIT
    if [[ -z ${IMAGE_REF:-} ]]; then
        printThemeHeading "Testimage ${IMAGE} (${PLATFORM})"
        docker build --quiet --platform "${PLATFORM}" -f "${ROOT_DIR}/docker/Dockerfile" \
            -t "${IMAGE}" "${ROOT_DIR}" >/dev/null
    fi
    printThemeHeading "Fälle gegen ${IMAGE}"
    local -r _ROOT_DATA='/data:uid=0,gid=0,mode=755'
    local _VOLUME

    expectRunning A1 99:100 --tmpfs "${_ROOT_DATA}"
    expectRunning A2 99:100 --tmpfs /data:uid=1000,gid=1000,mode=700
    expectRunning A3 1234:4321 -e PUID=1234 -e PGID=4321 --tmpfs "${_ROOT_DATA}"
    expectFailure A4a "PUID must be a positive number" -e PUID=abc --tmpfs "${_ROOT_DATA}"
    expectFailure A4b "PUID=0 would run the app as root" -e PUID=0 --tmpfs "${_ROOT_DATA}"
    expectRunning A5 1000:1000 --user 1000:1000 --tmpfs /data:uid=1000,gid=1000,mode=755
    expectFailure A6 "/data is not writable for UID 1000 / GID 1000" --user 1000:1000 --tmpfs "${_ROOT_DATA}"
    expectFailure A7 "/data is not writable for UID 99 / GID 100" --cap-drop CHOWN --tmpfs "${_ROOT_DATA}"
    expectRunning A8 99:100 --cap-drop CHOWN --tmpfs /data:uid=99,gid=100,mode=755
    if docker logs "${PREFIX}-A8" 2>&1 | grep -q 'entrypoint WARNING'; then
        report A8 1 "unnötige chown-Warnung bei passendem Eigentümer"
    fi
    expectFailure A9 "cannot switch to UID 99 / GID 100" --cap-drop SETUID --cap-drop SETGID --tmpfs "${_ROOT_DATA}"
    _VOLUME=$(prepareRootOwnedDatabase)
    OWN_VOLUMES+=("${_VOLUME}")
    expectFailure A10 "/data/stockinfo.db is not writable" --cap-drop CHOWN -v "${_VOLUME}:/data"
    # A11 steckt in jedem expectRunning: Prozess-IDs müssen den Zielwert treffen, nie 0:0.

    if ((FAILURES > 0)); then
        printThemeStatus '✗' "${FAILURES} Fall/Fälle fehlgeschlagen" DANGER
        return 1
    fi
    printThemeStatus '✓' 'Alle Fälle bestanden' SUCCESS
}

if (($# == 0)); then usage; exit 0; fi
case "$1" in
    -r | --run) runSmoke ;;
    -h | --help) usage ;;
    *) printThemeStatus '✗' "Unbekannte Option: $1" DANGER >&2; exit 2 ;;
esac
