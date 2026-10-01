#!/usr/bin/env bash
#------------------------------------------------------------------------------
# setup-libs.sh — BashLib, MakeLib und ProjectTools unter .libs/ verlinken
#
# Farben und Abstände kommen aus BashLib/colors.lib.sh, abgestimmt mit
# MakeLib/colours.mk und ProjectTools projecttools.ui.colors. Vor dem ersten Setup bleibt
# ohne Bibliothek eine kurze Starthilfe verfügbar. Keine Bibliotheken oder Pakete kopieren.
#
# Verwendung:
#   ./scripts/setup-libs.sh --install | --info | --help
#   MAKE_THEME=ocean ./scripts/setup-libs.sh --info
#   make setup
#
# Optionen:
#   -i | --install   Symlinks anlegen (vorhandene Symlinks ersetzen)
#   -s | --info      Verlinkung und gemeinsame CLI-Dateien anzeigen
#   -h | --help      Diese Hilfe anzeigen; auch ohne Argumente
#------------------------------------------------------------------------------
set -euo pipefail

readonly APPNAME="${0##*/}"
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly PROJECT_ROOT
readonly LIBS_DIR="${PROJECT_ROOT}/.libs"
BASH_LIBS="${BASH_LIBS:-${LIBS_DIR}/BashLib/src}"

# Ohne Quellbibliothek bleibt nur die Starthilfe; keine Kopie ihrer Ausgabehelfer.
if [[ ! -r ${BASH_LIBS}/tools.lib.sh ]]; then
    printf '\nUsage: %s --install | --info | --help\n' "${APPNAME}"
    printf 'BASH_LIBS auf das src-Verzeichnis von BashLib setzen: %s\n' "${BASH_LIBS}"
    if (( $# == 0 )) || [[ $# == 1 && ( $1 == --help || $1 == -h ) ]]; then exit 0; fi
    exit 1
fi
# shellcheck disable=SC1091  # Pfad kommt aus der Umgebung oder dem lokalen Link.
if [[ "${__TOOLS_LIB__:=}" == "" ]]; then . "${BASH_LIBS}/tools.lib.sh"; fi

# Repos über die bisherigen Variablen finden. Vorhandene lokale Links sind
# ebenfalls nutzbar; vor dem Ersetzen wird ihr tatsächliches Ziel aufgelöst.
readonly LINKED_REPOS=(
    "BashLib|BASH_LIBS|${BASH_LIBS%/src}|.../BashLib/src"
    "MakeLib|DEV_MAKE|${DEV_MAKE:-${LIBS_DIR}/MakeLib}|.../MakeLib"
    "ProjectTools|PROJECT_TOOLS|${PROJECT_TOOLS:-${LIBS_DIR}/ProjectTools/src}|.../ProjectTools/src"
)
readonly CLI_FILES=(
    "BashLib/src/colors.lib.sh"
    "BashLib/src/tools.lib.sh"
    "MakeLib/colours.mk"
    "ProjectTools/src/python/projecttools/ui/colors.py"
    "ProjectTools/src/bash/py-run.sh"
    "ProjectTools/src/python/changelog.py"
)

# Zeigt Optionen und Voraussetzungen ohne Änderungen an Links oder Umgebungen.
# Params: keine.
# Returns: 0 nach Ausgabe der Hilfe.
usage() {
    printf '\nUsage: %s [ options ]\n' "${APPNAME}"
    printThemeHeading 'Optionen'
    printThemeRow '-i | --install' 'Symlinks unter .libs/ anlegen (idempotent)'
    printThemeRow '-s | --info' 'Verlinkung und gemeinsame CLI-Dateien anzeigen'
    printThemeRow '-h | --help' 'Diese Hilfe anzeigen'
    printThemeHeading 'Beispiele'
    printThemeRow "${APPNAME} --install" 'Symlinks anlegen'
    printThemeRow "${APPNAME} --info" 'Verlinkung und CLI-Dateien prüfen'
    printThemeRow 'py-run.sh --list' 'Python-Werkzeuge aus ProjectTools anzeigen'
    printThemeHeading 'Voraussetzungen'
    printThemeRow 'BASH_LIBS' "${BASH_LIBS}"
    printThemeRow 'DEV_MAKE' "${DEV_MAKE:-${LIBS_DIR}/MakeLib}"
    printThemeRow 'PROJECT_TOOLS' "${PROJECT_TOOLS:-${LIBS_DIR}/ProjectTools/src}"
    printf '\n'
}

# Ersetzt nur Links. Echte Dateien und Verzeichnisse bleiben erhalten.
# $1 vorhandenes Quell-Repo; $2 Ziel unter .libs/. Fehler: Status 1.
linkOnce() {
    local -r _SOURCE="${1}" _DESTINATION="${2}"
    if [[ -e ${_DESTINATION} && ! -L ${_DESTINATION} ]]; then
        printThemeStatus '✗' "${_DESTINATION} ist kein Symlink; bleibt unverändert." DANGER >&2
        return 1
    fi
    if [[ -L ${_DESTINATION} && ${_DESTINATION} -ef ${_SOURCE} ]]; then return 0; fi
    mkdir -p "$(dirname -- "${_DESTINATION}")" || return 1
    ln -sfn "${_SOURCE}" "${_DESTINATION}"
}

# Prüft die tatsächlich konsumierten CLI-Dateien ohne Programme zu starten.
# Params: keine.
# Returns: 0 wenn alle Dateien lesbar sind, sonst 1.
checkCliFiles() {
    local _FILE _RESULT=0
    printThemeHeading 'Gemeinsame CLI-Dateien'
    for _FILE in "${CLI_FILES[@]}"; do
        if [[ -r ${LIBS_DIR}/${_FILE} ]]; then
            printThemeRow "${_FILE}" '✓ verfügbar'
        else
            printThemeStatus '✗' "${_FILE} fehlt; das Quell-Repository aktualisieren." DANGER >&2
            _RESULT=1
        fi
    done
    return "${_RESULT}"
}

# Löst alle Quellen vor ihrem Link-Ersatz physisch auf; keine Selbstlinks.
# Params: keine; Quellen stammen aus LINKED_REPOS.
# Returns: 0 bei vollständigem Setup, sonst 1.
installLinks() {
    local _RESULT=0 _ENTRY _NAME _VARIABLE _REPO _EXPECTED _SOURCE
    printThemeHeading "Symlinks unter ${LIBS_DIR}"
    if [[ -L ${LIBS_DIR} || ( -e ${LIBS_DIR} && ! -d ${LIBS_DIR} ) ]]; then
        printThemeStatus '✗' '.libs muss ein eigener Ordner sein.' DANGER >&2
        return 1
    fi
    for _ENTRY in "${LINKED_REPOS[@]}"; do
        IFS='|' read -r _NAME _VARIABLE _REPO _EXPECTED <<< "${_ENTRY}"
        if [[ ${_NAME} == ProjectTools ]]; then _REPO="${_REPO%/src}"; fi
        if [[ ! -d ${_REPO} ]]; then
            printThemeStatus '✗' "${_NAME}-Repo fehlt. ${_VARIABLE} soll auf ${_EXPECTED} zeigen." DANGER >&2
            _RESULT=1
            continue
        fi
        _SOURCE=$(cd -- "${_REPO}" && pwd -P)
        if linkOnce "${_SOURCE}" "${LIBS_DIR}/${_NAME}"; then
            printThemeRow "${_NAME}" "✓ ${_SOURCE}"
        else
            _RESULT=1
        fi
    done
    checkCliFiles || _RESULT=1
    if (( _RESULT != 0 )); then
        printThemeStatus '✗' 'Setup unvollständig. Quellen prüfen und erneut versuchen.' DANGER >&2
        return "${_RESULT}"
    fi
    printThemeStatus '✓' 'Setup fertig' SUCCESS
}

# Zeigt Linkstatus und nutzbare CLI-Dateien, ohne Links oder venv anzulegen.
# Params: keine.
# Returns: 0 wenn Links und Dateien nutzbar sind, sonst 1.
showLinks() {
    local _ENTRY _NAME _PATH _TARGET _RESULT=0
    printThemeHeading 'Aktuelle Verlinkung'
    for _ENTRY in "${LINKED_REPOS[@]}"; do
        _NAME="${_ENTRY%%|*}"
        _PATH="${LIBS_DIR}/${_NAME}"
        if [[ -L ${_PATH} && -d ${_PATH} ]]; then
            _TARGET=$(readlink "${_PATH}")
            printThemeRow "${_NAME}" "✓ ${_TARGET}"
        else
            printThemeStatus '⚠' "${_NAME}: fehlt, Ziel fehlt oder kein Symlink." WARNING
            _RESULT=1
        fi
    done
    checkCliFiles || _RESULT=1
    return "${_RESULT}"
}

if (( $# == 0 )); then usage; exit 0; fi
if (( $# != 1 )); then
    printThemeStatus '✗' 'Genau eine Option angeben; siehe --help.' DANGER >&2
    exit 2
fi
case "${1}" in
    -i|--install) installLinks ;;
    -s|--info) showLinks ;;
    -h|--help) usage ;;
    *) printThemeStatus '✗' "Unbekannte Option: ${1}" DANGER >&2; exit 2 ;;
esac
