#!/usr/bin/env bash
#------------------------------------------------------------------------------
# update-template.sh — Unraid-CA-Template auf einen Docker-Image-Tag umstellen
#
# Schreibt den <Repository>-Eintrag in unraid/stockinfo.xml auf
# mangolila/stockinfo:<TAG>. Wird von docker/build.sh nach jedem erfolgreichen
# Push (Docker Hub) automatisch aufgerufen — erst beim Build/Push existiert der
# endgültige Image-Tag (gitDockerTag stempelt zur Build-Zeit). Der direkte
# Aufruf ist jederzeit möglich.
#
# Verwendung:
#   ./scripts/update-template.sh [--tag <TAG> | --last-build | --show] [--help]
#
# Optionen:
#   -t | --tag <TAG>    Template auf diesen Image-Tag setzen
#   -l | --last-build   Tag aus docker/.last-build-tag übernehmen
#   -s | --show         Template-Eintrag, letzten Build-Tag und Version anzeigen
#   -h | --help         Diese Hilfe anzeigen
#------------------------------------------------------------------------------

# Vars die in .bashrc gesetzt sein müssen ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if [[ -z ${BASH_LIBS+x} ]]; then echo "Var 'BASH_LIBS' nicht gesetzt!"; exit 1; fi
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

set -euo pipefail

if [[ "${__COLORS_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/colors.lib.sh";  fi
if [[ "${__TOOLS_LIB__:=""}"   == "" ]]; then . "${BASH_LIBS}/tools.lib.sh";   fi
if [[ "${__VERSION_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/version.lib.sh"; fi

readonly APPNAME="$(basename "$0")"
readonly SCRIPT="$(realpath "$0")"
readonly SCRIPTPATH="$(dirname "${SCRIPT}")"

readonly TEMPLATE="${SCRIPTPATH}/../unraid/stockinfo.xml"
readonly TAGFILE="${SCRIPTPATH}/../docker/.last-build-tag"
readonly NAMESPACE="mangolila"
readonly NAME="stockinfo"

#------------------------------------------------------------------------------
# Functions
#

# Liest den aktuellen <Repository>-Eintrag aus dem Template.
#
# Returns:
#   0 und Eintrag via stdout, 1 wenn kein <Repository>-Eintrag gefunden
#
readTemplateRepository() {
    local -r _LINE="$(grep -o '<Repository>[^<]*</Repository>' "${TEMPLATE}" | head -1)"
    [[ -z "${_LINE}" ]] && return 1

    local -r _VALUE="${_LINE#<Repository>}"
    printf '%s\n' "${_VALUE%</Repository>}"
}

# Liest den Tag des letzten Builds aus docker/.last-build-tag (Zeile 1).
#
# Returns:
#   0 und Tag via stdout, 1 wenn kein Build-Tag vorhanden
#
readLastBuildTag() {
    [[ -f "${TAGFILE}" ]] || return 1
    sed -n '1p' "${TAGFILE}"
}

# Stellt den <Repository>-Eintrag im Template auf den angegebenen Image-Tag um.
#
# Params:
#   $1 - Docker-Image-Tag, z.B. 0.2.0-260715.1102.abc12
#
updateTemplate() {
    local -r _TAG="${1:-}"

    if [[ -z "${_TAG}" ]]; then
        echo -e "\n${RED}Fehler:${NC} Kein Tag angegeben.\n" >&2
        usage
        exit 1
    fi
    if [[ ! "${_TAG}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]]; then
        echo -e "\n${RED}Fehler:${NC} '${_TAG}' ist kein gültiger Docker-Tag.\n" >&2
        exit 1
    fi

    local _CURRENT
    _CURRENT="$(readTemplateRepository)" || {
        echo -e "\n${RED}Fehler:${NC} Kein <Repository>-Eintrag in ${TEMPLATE} gefunden.\n" >&2
        exit 1
    }

    local -r _REPOSITORY="${NAMESPACE}/${NAME}:${_TAG}"
    if [[ "${_CURRENT}" == "${_REPOSITORY}" ]]; then
        echo -e "  ${GREEN}✓${NC} Unraid-Template bereits aktuell: ${BLUE}${_REPOSITORY}${NC}"
        return 0
    fi

    local _TMPFILE
    _TMPFILE="$(mktemp)"
    awk -v REPO="${_REPOSITORY}" \
        '{ sub(/<Repository>[^<]*<\/Repository>/, "<Repository>" REPO "</Repository>"); print }' \
        "${TEMPLATE}" > "${_TMPFILE}"
    mv "${_TMPFILE}" "${TEMPLATE}"

    echo -e "  ${GREEN}✓${NC} Unraid-Template aktualisiert (${TEMPLATE#"${SCRIPTPATH}/../"})"
    echo -e "      ${YELLOW}alt${NC} ${_CURRENT}"
    echo -e "      ${YELLOW}neu${NC} ${BLUE}${_REPOSITORY}${NC}"
    echo -e "  ${BLUE}ℹ${NC} ${YELLOW}→${NC} Änderung committen nicht vergessen"
}

# Zeigt Template-Eintrag, letzten Build-Tag und Projekt-Version an.
#
show() {
    local _REPOSITORY _BUILD_TAG _VERSION
    _REPOSITORY="$(readTemplateRepository)"                            || _REPOSITORY="kein <Repository> gefunden"
    _BUILD_TAG="$(readLastBuildTag)"                                   || _BUILD_TAG="kein Build vorhanden"
    _VERSION="$(readProjectVersion auto "${SCRIPTPATH}/.." 2>/dev/null)" || _VERSION="unbekannt"

    echo
    echo -e "    ${YELLOW}Template     ${NC} = ${BLUE}${_REPOSITORY}${NC}"
    echo -e "    ${YELLOW}Letzter Build${NC} = ${BLUE}${_BUILD_TAG}${NC}"
    echo -e "    ${YELLOW}Version      ${NC} = ${BLUE}${_VERSION}${NC}"
    echo
}

# Zeigt die Verwendungshinweise an.
#
usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    usageLine "-t | --tag <TAG>       " "Template auf ${YELLOW}${NAMESPACE}/${NAME}:<TAG>${NC} umstellen"
    usageLine "-l | --last-build      " "Tag des letzten Builds übernehmen (${YELLOW}docker/.last-build-tag${NC})"
    usageLine "-s | --show            " "Template-Eintrag, letzten Build-Tag und Version anzeigen"
    usageLine "-h | --help            " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Automatik:     ${GREEN}docker/build.sh${NC} ruft dieses Script nach jedem Push (Docker Hub) auf"
    echo -e "    Direkt:        ${GREEN}${APPNAME} --last-build${NC}"
    echo -e "    Anzeigen:      ${GREEN}${APPNAME} --show${NC}"
    echo
}

#------------------------------------------------------------------------------
# Options
#

# Kein Argument → Help anzeigen (keine Ausnahmen)
if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

case "${1}" in
    -t|--tag)
        updateTemplate "${2:-}"
    ;;

    -l|--last-build)
        _TAG="$(readLastBuildTag)" || {
            echo -e "\n${RED}Fehler:${NC} Kein Build-Tag gefunden (${TAGFILE})." >&2
            echo -e "${YELLOW}Tipp:${NC} Zuerst ${GREEN}docker/build.sh --build${NC} ausführen.\n" >&2
            exit 1
        }
        updateTemplate "${_TAG}"
    ;;

    -s|--show)
        show
    ;;

    -h|--help)
        usage
    ;;

    *)
        echo -e "\n${RED}Unbekannte Option: ${1}${NC}" >&2
        usage
        exit 1
    ;;
esac

#------------------------------------------------------------------------------
# Alles OK...

exit 0
