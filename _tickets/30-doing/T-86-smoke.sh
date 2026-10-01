#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-86-smoke.sh — Containerstart bei Rechteproblemen nachstellen (A1–A11 mit Unterfällen)
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
readonly ROOT_DATA='/data:uid=0,gid=0,mode=755'
readonly WARNING_TEXT='entrypoint WARNING'
FAILURES=0
OWN_VOLUMES=()

# Zeigt Optionen und Umgebungsvariablen, ohne etwas zu starten.
# Params: keine.
# Returns: 0.
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

# Entfernt nur die Container und Volumes dieses Laufs (Präfix mit eigener PID).
# Params: keine.
# Returns: 0.
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
# Returns: 0.
report() {
    if [[ $2 -eq 0 ]]; then
        printThemeStatus '✓' "$1 $3" SUCCESS
    else
        printThemeStatus '✗' "$1 $3" DANGER
        FAILURES=$((FAILURES + 1))
    fi
}

# Startet einen Container und wartet, bis er antwortet oder endet.
# Params: $1 Fall, weitere: docker-run-Argumente.
# Returns: 0; gibt den Containernamen auf stdout aus.
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

# Liefert UID:GID der App-Prozesse, ohne die eigene Prüf-Shell.
# Params: $1 Containername.
# Returns: 0; eine Zeile je unterschiedlichem UID:GID auf stdout.
processIds() {
    docker exec "$1" sh -c 'for P in /proc/[0-9]*; do
        [ "$P" = "/proc/$$" ] && continue
        C=$(tr "\0" " " < "$P/cmdline" 2>/dev/null) || continue
        case "$C" in *uvicorn*) awk "/^Uid:/{u=\$2}/^Gid:/{g=\$2}END{print u\":\"g}" "$P/status";; esac
    done' | sort -u
}

# Prüft Texte in den Containerlogs.
# Params: $1 Logs, weitere: Texte; ein Text mit Präfix '!' darf nicht vorkommen.
# Returns: 0, wenn alle Bedingungen gelten, sonst 1; stdout nennt die erste Abweichung.
checkTexts() {
    local -r _LOGS="$1"
    shift
    local _TEXT
    for _TEXT in "$@"; do
        if [[ ${_TEXT} == '!'* ]]; then
            if [[ ${_LOGS} == *"${_TEXT#!}"* ]]; then printf 'unerwartet: %s' "${_TEXT#!}"; return 1; fi
        elif [[ ${_LOGS} != *"${_TEXT}"* ]]; then
            printf 'fehlt: %s' "${_TEXT}"
            return 1
        fi
    done
}

# Erwartet einen laufenden Container mit Prozess- und Datei-IDs.
# Params: $1 Fall, $2 erwartete UID:GID, $3 zu prüfende Pfade (Leerzeichen),
#         dann Log-Texte (siehe checkTexts), '--', docker-run-Argumente.
# Returns: 0; das Ergebnis meldet report.
expectRunning() {
    local -r _CASE="$1" _IDS="$2" _PATHS="$3"
    shift 3
    local _TEXTS=()
    while [[ $1 != -- ]]; do _TEXTS+=("$1"); shift; done
    shift
    local _NAME _PROCS _FILES _LOGS _DETAIL
    _NAME=$(startCase "${_CASE}" "$@")
    _LOGS=$(docker logs "${_NAME}" 2>&1)
    if [[ $(docker inspect -f '{{.State.Status}}' "${_NAME}") != running ]]; then
        report "${_CASE}" 1 "erwartet Start, Container endete: $(tail -1 <<< "${_LOGS}")"
        return 0
    fi
    _PROCS=$(processIds "${_NAME}")
    # shellcheck disable=SC2086  # Pfadliste bewusst aufteilen.
    _FILES=$(docker exec "${_NAME}" stat -c '%u:%g' ${_PATHS} | sort -u)
    if ! _DETAIL=$(checkTexts "${_LOGS}" "${_TEXTS[@]+"${_TEXTS[@]}"}"); then
        report "${_CASE}" 1 "läuft, aber Log ${_DETAIL}"
    elif [[ ${_PROCS} == "${_IDS}" && ${_FILES} == "${_IDS}" ]]; then
        report "${_CASE}" 0 "läuft, Prozesse und ${_PATHS} ${_IDS}"
    else
        report "${_CASE}" 1 "Prozesse '${_PROCS//$'\n'/,}', Dateien '${_FILES//$'\n'/,}', erwartet ${_IDS}"
    fi
}

# Erwartet einen Abbruch vor dem App-Start.
# Params: $1 Fall, dann Log-Texte (siehe checkTexts), '--', docker-run-Argumente.
# Returns: 0; das Ergebnis meldet report.
expectFailure() {
    local -r _CASE="$1"
    shift
    local _TEXTS=()
    while [[ $1 != -- ]]; do _TEXTS+=("$1"); shift; done
    shift
    local _NAME _LOGS _EXIT _DETAIL
    _NAME=$(startCase "${_CASE}" "$@")
    _LOGS=$(docker logs "${_NAME}" 2>&1)
    _EXIT=$(docker inspect -f '{{.State.ExitCode}}' "${_NAME}")
    if [[ $(docker inspect -f '{{.State.Status}}' "${_NAME}") != exited || ${_EXIT} -eq 0 ]]; then
        report "${_CASE}" 1 "erwartet Abbruch, Status/Exit ${_EXIT}: $(tail -1 <<< "${_LOGS}")"
    elif ! _DETAIL=$(checkTexts "${_LOGS}" "${_TEXTS[@]}" '!app_started'); then
        report "${_CASE}" 1 "Abbruch (Exit ${_EXIT}), aber Log ${_DETAIL}: $(tail -1 <<< "${_LOGS}")"
    else
        report "${_CASE}" 0 "Abbruch (Exit ${_EXIT}): $(grep -m1 'entrypoint ERROR' <<< "${_LOGS}")"
    fi
}

# Legt ein eigenes Testvolume an: /data gehört 99:100, die Datenbankdatei
# erhält den angegebenen Eigentümer und Modus.
# Params: $1 Namenszusatz, $2 Eigentümer der Datei (UID:GID), $3 Dateimodus.
# Returns: 0; gibt den Volumenamen auf stdout aus.
prepareDatabase() {
    local _VOLUME
    _VOLUME=$(docker volume create "${PREFIX}-$1")
    docker run --rm --platform "${PLATFORM}" --entrypoint sh -v "${_VOLUME}:/data" "${IMAGE}" \
        -c ": > /data/stockinfo.db && chown $2 /data/stockinfo.db && chmod $3 /data/stockinfo.db \
            && chown 99:100 /data" >/dev/null
    printf '%s' "${_VOLUME}"
}

# Baut bei Bedarf das Testimage und prüft alle Fälle.
# Params: keine.
# Returns: 0, wenn alle Fälle bestehen, sonst 1.
runSmoke() {
    trap cleanupSmoke EXIT
    if [[ -z ${IMAGE_REF:-} ]]; then
        printThemeHeading "Testimage ${IMAGE} (${PLATFORM})"
        docker build --quiet --platform "${PLATFORM}" -f "${ROOT_DIR}/docker/Dockerfile" \
            -t "${IMAGE}" "${ROOT_DIR}" >/dev/null
    fi
    printThemeHeading "Fälle gegen ${IMAGE}"
    local -r _RANGE='must be a number from 1 to 4294967294'
    local -r _HUGE='999999999999999999999999'
    local _VOLUME

    expectRunning A1 99:100 '/data /data/stockinfo.db' "!${WARNING_TEXT}" -- --tmpfs "${ROOT_DATA}"
    expectRunning A2 99:100 '/data /data/stockinfo.db' -- --tmpfs /data:uid=1000,gid=1000,mode=700
    expectRunning A3 1234:4321 '/data /data/stockinfo.db' -- -e PUID=1234 -e PGID=4321 --tmpfs "${ROOT_DATA}"
    expectFailure A4a "PUID ${_RANGE}, got 'abc'" -- -e PUID=abc --tmpfs "${ROOT_DATA}"
    expectFailure A4b "PUID=0 would run the app as root" -- -e PUID=0 --tmpfs "${ROOT_DATA}"
    expectFailure A4c "PGID=0 would run the app as root" -- -e PGID=0 --tmpfs "${ROOT_DATA}"
    expectFailure A4d "PUID ${_RANGE}, got ''" -- -e PUID= --tmpfs "${ROOT_DATA}"
    expectFailure A4e "PGID ${_RANGE}, got ''" -- -e PGID= --tmpfs "${ROOT_DATA}"
    expectFailure A4f "PUID ${_RANGE}, got '${_HUGE}'" '!Illegal number' '!would run the app as root' \
        -- -e "PUID=${_HUGE}" --tmpfs "${ROOT_DATA}"
    expectFailure A4g "PGID ${_RANGE}, got '${_HUGE}'" '!Illegal number' '!would run the app as root' \
        -- -e "PGID=${_HUGE}" --tmpfs "${ROOT_DATA}"
    expectRunning A5 1000:1000 '/data /data/stockinfo.db' -- --user 1000:1000 --tmpfs /data:uid=1000,gid=1000,mode=755
    expectFailure A6a "/data is not writable for UID 1000 / GID 1000" "chown -R 1000:1000" '!--user 0:0' \
        -- --user 1000:1000 --tmpfs "${ROOT_DATA}"
    expectFailure A6b "/data is not writable for UID 2000 / GID 2000" "--user 1000:1000 to match its current owner" \
        -- --user 2000:2000 --tmpfs /data:uid=1000,gid=1000,mode=700
    expectFailure A7a "${WARNING_TEXT}: could not change the owner of /data" \
        "/data is not writable for UID 99 / GID 100" "chown -R 99:100" '!PUID=0' \
        -- --cap-drop CHOWN --tmpfs "${ROOT_DATA}"
    expectRunning A7b 99:100 '/data/stockinfo.db' "${WARNING_TEXT}: could not change the owner of /data" \
        -- --cap-drop CHOWN --tmpfs /data:uid=0,gid=0,mode=777
    expectFailure A7c "/data is not writable for UID 99 / GID 100" "set PUID=1000 PGID=1000 to match its current owner" \
        -- --cap-drop CHOWN --tmpfs /data:uid=1000,gid=1000,mode=700
    expectRunning A8 99:100 '/data /data/stockinfo.db' "!${WARNING_TEXT}" \
        -- --cap-drop CHOWN --tmpfs /data:uid=99,gid=100,mode=755
    expectFailure A9 "cannot switch to UID 99 / GID 100 to use /data" "remove --cap-drop for SETUID/SETGID" \
        -- --cap-drop SETUID --cap-drop SETGID --tmpfs "${ROOT_DATA}"
    _VOLUME=$(prepareDatabase rootdb 0:0 644)
    OWN_VOLUMES+=("${_VOLUME}")
    expectFailure A10a "/data/stockinfo.db is not writable for UID 99 / GID 100" "chown -R 99:100" '!PUID=0' \
        -- --cap-drop CHOWN -v "${_VOLUME}:/data"
    _VOLUME=$(prepareDatabase readonlydb 99:100 444)
    OWN_VOLUMES+=("${_VOLUME}")
    expectFailure A10b "/data/stockinfo.db is not writable for UID 99 / GID 100" "chmod -R u+rwX" '!chown -R' \
        -- -v "${_VOLUME}:/data"
    # Eigentümer stimmt, nur das Schreibbit fehlt: chown/--user ändern nichts.
    expectFailure A6c "/data is not writable for UID 1000 / GID 1000" "chmod -R u+rwX" '!chown -R' '!--user 1000:1000' \
        -- --user 1000:1000 --tmpfs /data:uid=1000,gid=1000,mode=555
    expectFailure A7d "/data is not writable for UID 99 / GID 100" "chmod -R u+rwX" '!chown -R' '!PUID=99' \
        -- --tmpfs /data:uid=99,gid=100,mode=555
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
    *)
        printThemeStatus '✗' "Unbekannte Option: $1" DANGER >&2
        usage >&2
        exit 2
        ;;
esac
