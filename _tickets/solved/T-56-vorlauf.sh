#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-56-vorlauf.sh — baut die zwei isolierten Instanzen fuer den Browser-Vorlauf
#
# **O** — Online-Kette mit YAML als letztem Rueckfall (sources-fallback)
# **Y** — reines Dateiprofil (sources-standalone)
#
# Jede Instanz bekommt ein eigenes `data/`, eine eigene Datenbank, einen
# eigenen Port und ihre eigene Fachdatei. Mikes `data/stockinfo.db` wird
# nicht angefasst; `--checksum` belegt das vorher wie nachher.
#
# Die Vorlagen unter `examples/` nennen `/data/assets-*.yaml` — den Pfad im
# Container. Beim Kopieren wird er auf das isolierte Verzeichnis gebogen;
# das ist der einzige Eingriff in den Inhalt.
#------------------------------------------------------------------------------
set -uo pipefail

# Aufwaerts, erkennbar an `.libs/` — ein festes `../` braeche in `solved/`.
findProjectRoot() {
    local _DIR="$1"
    while [[ "${_DIR}" != "/" ]]; do
        [[ -d "${_DIR}/.libs" ]] && { echo "${_DIR}"; return 0; }
        _DIR="$(dirname "${_DIR}")"
    done
    return 1
}
# `readonly` liefert **immer** 0 — der Exit-Code muss vorher gesichert werden.
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

APPNAME="$(basename "$0")"
readonly APPNAME
readonly WORKDIR="${WORKDIR:-/private/tmp/claude-501/t-56-vorlauf}"
readonly LIVE_DB="${PROJECT_ROOT}/data/stockinfo.db"

# Je Profil: Verzeichnisname, Quellendatei, Fachdatei, Backend-Port, Vite-Port.
profileSpec() {
    case "$1" in
        O) echo "O sources-fallback.yaml assets-fallback.yaml 8901 5901" ;;
        Y) echo "Y sources-standalone.yaml assets-standalone.yaml 8902 5902" ;;
        *) return 1 ;;
    esac
}

usage() {
    echo -e "\nUsage: ${APPNAME} [ options ]\n"
    usageLine "-s | --setup  <O|Y>" "Isolierte Instanz aufbauen und starten"
    usageLine "-x | --stop   <O|Y>" "Diese Instanz stoppen (nur eigene PIDs)"
    usageLine "-c | --checksum    " "Pruefsumme von Mikes Betriebsdatenbank"
    usageLine "-i | --info        " "Pfade und Ports zeigen"
    usageLine "-h | --help        " "Diese Hilfe anzeigen"
    echo -e "\n    ${YELLOW}WORKDIR${NC}=<pfad> — anderes Arbeitsverzeichnis\n"
}

checksum() {
    if [[ ! -f "${LIVE_DB}" ]]; then
        echo -e "  ${RED}✗${NC} ${LIVE_DB} fehlt"
        return 1
    fi
    echo -e "  ${YELLOW}data/stockinfo.db${NC}  $(shasum -a 256 "${LIVE_DB}" | cut -d' ' -f1)"
}

setupProfile() {
    local -r _PROFILE="$1"
    local _SPEC
    _SPEC="$(profileSpec "${_PROFILE}")" || { echo "unbekanntes Profil: ${_PROFILE}" >&2; return 1; }
    # shellcheck disable=SC2086
    set -- ${_SPEC}
    local -r _NAME="$1" _SOURCES="$2" _ASSETS="$3" _API_PORT="$4" _WEB_PORT="$5"
    local -r _ROOT="${WORKDIR}/${_NAME}"
    local -r _DATA="${_ROOT}/data"

    rm -rf "${_ROOT}"
    mkdir -p "${_DATA}/plugins"

    cp "${PROJECT_ROOT}/plugin_api/examples/yaml_file.py" "${_DATA}/plugins/"
    cp "${PROJECT_ROOT}/examples/${_ASSETS}" "${_DATA}/${_ASSETS}"
    # Der einzige Eingriff: der Container-Pfad wird auf dieses `data/` gebogen.
    sed "s#/data/${_ASSETS}#${_DATA}/${_ASSETS}#" \
        "${PROJECT_ROOT}/examples/${_SOURCES}" > "${_DATA}/sources.yaml"

    (
        cd "${PROJECT_ROOT}" || exit 1
        DATABASE_PATH="${_DATA}/stockinfo.db" \
        PORT="${_API_PORT}" \
        CORS_ORIGINS="[\"http://localhost:${_WEB_PORT}\"]" \
        nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${_API_PORT}" \
            > "${_ROOT}/backend.log" 2>&1 &
        echo $! > "${_ROOT}/backend.pid"
    )
    (
        cd "${PROJECT_ROOT}/dashboard" || exit 1
        VITE_DEV_API_TARGET="http://127.0.0.1:${_API_PORT}" \
        nohup npm run dev -- --port "${_WEB_PORT}" --strictPort \
            > "${_ROOT}/web.log" 2>&1 &
        echo $! > "${_ROOT}/web.pid"
    )

    echo -e "  ${GREEN}✓${NC} Profil ${YELLOW}${_NAME}${NC} — API ${BLUE}http://127.0.0.1:${_API_PORT}${NC} · UI ${BLUE}http://localhost:${_WEB_PORT}${NC}"
    echo -e "    Daten: ${_DATA}"
}

stopProfile() {
    local -r _PROFILE="$1"
    local _SPEC
    _SPEC="$(profileSpec "${_PROFILE}")" || { echo "unbekanntes Profil: ${_PROFILE}" >&2; return 1; }
    # shellcheck disable=SC2086
    set -- ${_SPEC}
    local -r _ROOT="${WORKDIR}/$1"

    local _PIDFILE
    for _PIDFILE in "${_ROOT}/backend.pid" "${_ROOT}/web.pid"; do
        [[ -f "${_PIDFILE}" ]] || continue
        # Nur die eigene PID — pkill auf Muster traefe fremde Prozesse.
        pkill -P "$(cat "${_PIDFILE}")" 2>/dev/null
        kill "$(cat "${_PIDFILE}")" 2>/dev/null
        rm -f "${_PIDFILE}"
    done
    echo -e "  ${GREEN}✓${NC} Profil ${YELLOW}${_PROFILE}${NC} gestoppt"
}

info() {
    echo -e "\n  ${YELLOW}PROJECT_ROOT${NC} ${PROJECT_ROOT}"
    echo -e "  ${YELLOW}WORKDIR${NC}      ${WORKDIR}"
    local _PROFILE
    for _PROFILE in O Y; do
        echo -e "  ${YELLOW}${_PROFILE}${NC}            $(profileSpec "${_PROFILE}")"
    done
    echo
}

case "${1:-}" in
    -s|--setup)    setupProfile "${2:-}" ;;
    -x|--stop)     stopProfile  "${2:-}" ;;
    -c|--checksum) checksum ;;
    -i|--info)     info ;;
    -h|--help|"")  usage ;;
    *)             usage; exit 1 ;;
esac
