#!/usr/bin/env bash

#------------------------------------------------------------------------------
# Build Docker-Image: mangolila/stockinfo
#------------------------------------------------------------------------------

# Vars die in .bashrc gesetzt sein müssen ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if [[ -z ${BASH_LIBS+x} ]]; then echo "Var 'BASH_LIBS' nicht gesetzt!"; exit 1; fi
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# -e  bricht bei erstem Fehler ab   (Ausnahme: 'command || true')
# -o pipefail  Pipeline-Exit-Code = rechtestes fehlgeschlagenes Kommando
# -u  unset-Variable = Fehler
set -eou pipefail

readonly APPNAME="$(basename "$0")"

readonly SCRIPT=$(realpath "$0")
readonly SCRIPTPATH=$(dirname "$SCRIPT")

#------------------------------------------------------------------------------
# Set WORKSPACE
#
cd "${SCRIPTPATH}"

mkdir -p logs
LOGFILE="logs/build-$(date +%y%m%d).log"

# shellcheck disable=SC2155
readonly DOCKER_BASE_IMAGE=$(\grep "^FROM " < Dockerfile | head -1 | sed "s/FROM //;s/ AS.*//")

readonly NAMESPACE="mangolila"
readonly NAME="stockinfo"

readonly TAGFILE="${SCRIPTPATH}/.last-build-tag"
readonly WARN_DAYS=7

#------------------------------------------------------------------------------
# Einbinden der globalen Build-Lib
#   Hier sind z.B. Farben, generell globale VARs und Funktionen definiert
#
if [[ "${__BUILD_LIB__:=""}"   == "" ]]; then . "${BASH_LIBS}/build.lib.sh";   fi
if [[ "${__DOCKER_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/docker.lib.sh";  fi
if [[ "${__VERSION_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/version.lib.sh"; fi

readonly PROJECT_NAME="${NAMESPACE}.${NAME}"

#------------------------------------------------------------------------------
# Registry-Ziel (TARGET) — wohin `--push` das Image lädt
#
#   Überschreibbar per Env:   TARGET=dockerhub ./build.sh --push
#
#   ghcr       GitHub Container Registry (ghcr.io)                       [Default]
#              Image:   ghcr.io/<GITHUB_OWNER>/<NAMESPACE>-<NAME>
#              Login:   einmalig manuell —
#                       echo <PAT> | docker login ghcr.io -u <user> --password-stdin   (Scope: write:packages)
#              Braucht: GITHUB_OWNER  (per Env/.bashrc, sonst der hier gesetzte Default)
#
#   dockerhub  Docker Hub (docker.io)
#              Image:   <NAMESPACE>/<NAME>            (NAMESPACE = Docker-Hub-User/Org)
#              Login:   loginToDockerHub — liest das Passwort aus ${DOCKER_PW_FILE} (12h-Cache)
#              Braucht: DOCKER_PW_FILE  (Default: ${HOME}/.docker/dockerhub.sec)
#
#   ecr        Amazon Elastic Container Registry
#              Image:   <AMAZON_REPO_URI>/<NAME>     (Repository muss in ECR vorab existieren)
#              Login:   aws ecr get-login-password | docker login  (automatisch beim Push)
#              Braucht: AMAZON_REPO_URI  (z.B. 123456789012.dkr.ecr.eu-west-1.amazonaws.com)
#                       AWS_REGION       (Default: eu-west-1)
#
readonly TARGET="${TARGET:-ghcr}"

# Registry-spezifische Variablen setzen: REGISTRY (Anzeige) + IMAGE (voll qualifizierte
# Registry-Referenz). Das lokal gebaute Image heisst immer ${NAMESPACE}/${NAME}.
case "${TARGET}" in
    ghcr)
        GITHUB_OWNER="${GITHUB_OWNER:-MikeMitterer}"
        if [[ -z "${GITHUB_OWNER}" ]]; then
            echo -e "\n${RED}TARGET=ghcr:${NC} Var 'GITHUB_OWNER' nicht gesetzt!" >&2
            exit 1
        fi
        readonly GITHUB_OWNER
        readonly REGISTRY="ghcr.io"
        readonly IMAGE="${REGISTRY}/${GITHUB_OWNER}/${NAMESPACE}-${NAME}"
    ;;
    dockerhub)
        readonly REGISTRY="docker.io"
        readonly IMAGE="${NAMESPACE}/${NAME}"
        # loginToDockerHub (docker.lib.sh) liest das Passwort aus dieser Datei:
        readonly DOCKER_CONFIG="${DOCKER_CONFIG:-${HOME}/.docker}"
        readonly DOCKER_PW_FILE="${DOCKER_PW_FILE:-${DOCKER_CONFIG}/dockerhub.sec}"
    ;;
    ecr)
        if [[ -z "${AMAZON_REPO_URI:-}" ]]; then
            echo -e "\n${RED}TARGET=ecr:${NC} Var 'AMAZON_REPO_URI' nicht gesetzt." >&2
            echo -e "${YELLOW}Beispiel:${NC} AMAZON_REPO_URI=123456789012.dkr.ecr.eu-west-1.amazonaws.com\n" >&2
            exit 1
        fi
        readonly AWS_REGION="${AWS_REGION:-eu-west-1}"
        readonly REGISTRY="${AMAZON_REPO_URI}"
        readonly IMAGE="${REGISTRY}/${NAME}"
    ;;
    *)
        echo -e "\n${RED}Unbekanntes TARGET: '${TARGET}'${NC} — erlaubt: ${YELLOW}ghcr | dockerhub | ecr${NC}\n" >&2
        exit 1
    ;;
esac

# CMDLINE kann ab hier verwendet werden ---------------------------------------

readonly CMDLINE=${1:-}
readonly OPTION=${2:-""}

# DEV_LOCAL ist bei den Jenkins-Tests bzw. in Docker-Containern nicht gesetzt,
# IS_CI geht also auf "true"
readonly IS_CI="${DEV_LOCAL:-"true"}"
readonly HAS_DEV_LOCAL="[[ ${IS_CI} != 'true' ]]"

# Die möglichen Plattformen:
#   https://docs.docker.com/build/building/multi-platform/
readonly PLATFORMS="linux/arm64 linux/amd64"

if [[ "${ARCHITECTURE}" == "x86_64" ]]; then
    readonly DEFAULT_PLATFORM="linux/amd64"
elif [[ "${ARCHITECTURE}" == "arm64" ]]; then
    readonly DEFAULT_PLATFORM="linux/arm64"
else
    readonly DEFAULT_PLATFORM="linux/amd64"
fi

PLATFORM="${DEFAULT_PLATFORM}"
BUILD_MULTIARCH=false

while [ $# -ne 0 ]; do
    case "${1}" in
        --build | -b)
            shift
            if [[ "${OPTION}" == "x86" ]]; then
                PLATFORM="linux/amd64"
            elif [[ "${OPTION}" == "arm" || "${OPTION}" == "m1" ]]; then
                PLATFORM="linux/arm64"
            elif [[ "${OPTION}" == "all" ]]; then
                PLATFORM="linux/arm64,linux/amd64"
                BUILD_MULTIARCH=true
            else
                PLATFORM="${DEFAULT_PLATFORM}"
                echo "Platform: ${PLATFORM}"
                break
            fi
        ;;
    esac
    shift
done

#------------------------------------------------------------------------------
# TAG via gitDockerTag (version.lib.sh): Git-Tag als Basis, docker-safe Build-Meta
# STRICT=2 (Default/relaxed): rc=2 kein Tag, rc=3 dirty — ahead erlaubt
# STRICT=1: zusätzlich rc=4 wenn ahead > 0
#
# Überschreiben via Env: STRICT=1 ./build.sh --build
#
readonly STRICT=${STRICT:-2}

_tag_rc=0
TAG="$(gitDockerTag "${STRICT}")" || _tag_rc=$?
if [[ $_tag_rc -eq 2 ]]; then
    echo -e "\n${RED}Build abgebrochen:${NC} Kein Git-Tag gefunden." >&2
    echo -e "${YELLOW}Tipp:${NC} semVerBump patch  ${BLUE}# oder manuell:${NC} git tag -a v0.1.0+$(date +%y%m%d.%H%M) -m 'Initial release'\n" >&2
    exit 1
elif [[ $_tag_rc -eq 3 ]]; then
    echo -e "\n${RED}Build abgebrochen:${NC} Working-Tree ist dirty." >&2
    echo -e "${YELLOW}Tipp:${NC} git commit oder git stash\n" >&2
    exit 1
elif [[ $_tag_rc -eq 4 ]]; then
    echo -e "\n${RED}Build abgebrochen:${NC} Repo ist ahead vom letzten Tag (STRICT=1)." >&2
    echo -e "${YELLOW}Tipp:${NC} semVerBump patch — oder mit ${BLUE}STRICT=2 ./build.sh --build${NC} (ahead erlaubt)\n" >&2
    exit 1
elif [[ $_tag_rc -ne 0 ]]; then
    echo -e "\n${RED}Build abgebrochen:${NC} gitDockerTag fehlgeschlagen (rc=${_tag_rc}).\n" >&2
    exit 1
fi
readonly TAG

#------------------------------------------------------------------------------
# Functions
#

# prepareConfig — Optionaler Build-Vorbereitungs-Schritt
#
#   No-op solange das (Multi-Stage-)Dockerfile Build + Deps selbst übernimmt.
#   Bei Services die vor dem Build Dateien ins Build-Kontext-Verzeichnis kopieren
#   müssen (Configs, Scripts, Zertifikate) hier befüllen — vgl. certbot-Template.
#
prepareConfig() {
    : # kein separates Config-Prep nötig
}

# pushImage — Delegiert an die Registry-spezifische Lib-Push-Funktion (nach TARGET)
#
#   Jede Lib-Push-Funktion kapselt ihren eigenen Login und pusht ${_tag} + latest.
#
#   Params:
#     - Tag des zu pushenden Images
#
pushImage() {
    local _tag=${1:?}

    case "${TARGET}" in
        ghcr)      pushImage2GHCR      "${GITHUB_OWNER}"    "${NAMESPACE}-${NAME}" "${_tag}" ;;
        dockerhub) pushImage2DockerHub "${NAMESPACE}"       "${NAME}"              "${_tag}" ;;
        ecr)       pushImage2Amazon    "${AMAZON_REPO_URI}" "${NAME}" "${_tag}" "${AWS_REGION}" ;;
    esac
}

# ensureRegistryLogin — Login/Check vor einem direkten Registry-Push (Multiarch)
#
#   Der Single-Arch-Pfad pusht via push()→pushImage(), das den Login selbst kapselt.
#   Der Multiarch-Pfad pusht dagegen direkt aus buildx heraus (buildMultiArchImage)
#   und braucht den Login deshalb VOR dem Build.
#
ensureRegistryLogin() {
    case "${TARGET}" in
        ghcr)      checkCHCRLogin ;;
        dockerhub) loginToDockerHub ;;
        ecr)       aws ecr get-login-password --region "${AWS_REGION}" \
                     | docker login --username AWS --password-stdin "${AMAZON_REPO_URI}" ;;
    esac
}

# showBuiltImages — Lokale (und bei ECR zusätzlich Registry-)Images anzeigen
#
#   showImages nimmt optional die Amazon-URI als 4. Parameter und listet dann
#   auch die ECR-getaggten Images — bei ghcr/dockerhub weggelassen.
#
showBuiltImages() {
    if [[ "${TARGET}" == "ecr" ]]; then
        showImages "${TAG}" "${NAMESPACE}" "${NAME}" "${AMAZON_REPO_URI}"
    else
        showImages "${TAG}" "${NAMESPACE}" "${NAME}"
    fi
}

# build — Image für die gewählte Plattform bauen
#
#   Multiarch (BUILD_MULTIARCH=true): buildx baut UND pusht in einem Schritt —
#   Login vorher via ensureRegistryLogin; danach kein TAGFILE, push() nicht aufrufen.
#   Single-arch: lokal bauen, Images anzeigen, Tag + Zeitstempel in TAGFILE
#   persistieren (von push()/loadLastBuildTag gelesen).
#
build() {
    prepareConfig

    echo -e "\nBuilding for Platform: ${YELLOW}${PLATFORM}${NC} → Target: ${YELLOW}${TARGET}${NC}\n"

    if [[ "${BUILD_MULTIARCH}" == true ]]; then
        ensureRegistryLogin
        buildMultiArchImage "${PLATFORM}" "${IMAGE}" "${TAG}" "${LOGFILE}"
        # Push ist bereits erledigt — kein TAGFILE, push() nicht aufrufen
        return
    fi

    buildSingleArchImage "${PLATFORM}" "${NAMESPACE}/${NAME}" "${IMAGE}" "${TAG}" "${LOGFILE}"
    showBuiltImages

    # Tag + Zeitstempel persistieren — wird von push() gelesen
    echo "${TAG}"      > "${TAGFILE}"
    echo "$(date +%s)" >> "${TAGFILE}"
}

# loadLastBuildTag — Tag des letzten Builds lesen und zurückgeben
#
#   Gibt den gespeicherten Tag via stdout zurück (für Zuweisung per $(...)).
#   Alle Meldungen und Warnungen gehen nach stderr, damit stdout sauber bleibt.
#   Bricht mit exit 1 ab wenn kein Build existiert.
#   Gibt eine Warnung aus wenn der Build älter als WARN_DAYS Tage ist.
#
#   Verwendung:
#     local _tag
#     _tag=$(loadLastBuildTag) || exit 1
#
loadLastBuildTag() {
    if [[ ! -f "${TAGFILE}" ]]; then
        echo -e "\n${RED}Kein gespeicherter Build-Tag gefunden: ${TAGFILE}${NC}" >&2
        echo -e "${YELLOW}Zuerst '--build' ausführen.${NC}\n" >&2
        exit 1
    fi

    local _saved_tag _build_ts _now _age_days _build_date
    _saved_tag=$(sed -n '1p' "${TAGFILE}")
    _build_ts=$(sed -n '2p'  "${TAGFILE}")
    _now=$(date +%s)
    _age_days=$(( (_now - _build_ts) / 86400 ))
    _build_date=$(date -d "@${_build_ts}" "+%Y-%m-%d" 2>/dev/null \
               || date -r "${_build_ts}" "+%Y-%m-%d" 2>/dev/null \
               || echo "unbekannt")

    if (( _age_days >= WARN_DAYS )); then
        echo -e "\n${YELLOW}Warnung: Build ist ${_age_days} Tage alt (gebaut am ${_build_date}).${NC}" >&2
        echo -e "${YELLOW}         Neu bauen? → $(basename "$0") --build${NC}\n" >&2
    fi

    echo -e "Build vom ${YELLOW}${_build_date}${NC}: ${BLUE}${_saved_tag}${NC}" >&2
    echo "${_saved_tag}"
}

# push — Zuletzt gebautes Image ins gewählte Registry-Ziel (TARGET) laden
#
#   Liest den Tag des letzten Builds aus TAGFILE und delegiert an pushImage(),
#   das je nach TARGET ghcr.io / Docker Hub / ECR bedient (Tag + latest).
#   Voraussetzung: der jeweilige Registry-Login ist vorhanden bzw. möglich.
#
push() {
    local _tag
    _tag=$(loadLastBuildTag) || exit 1

    echo -e "\nPushing ${YELLOW}${IMAGE}:${_tag}${NC} → ${YELLOW}${REGISTRY}${NC} (target: ${YELLOW}${TARGET}${NC})\n"
    pushImage "${_tag}"

    echo -e "\n${GREEN}Push erfolgreich: ${IMAGE}:${_tag}${NC}"
}

# Samples-Array — Beispiel-`docker run`-Befehle für dieses Image
#
#   Erste Zeile jedes Eintrags: "# Beschreibung ||"  ('#' → Sample-Index, '||' → Zeilenende)
#   Folgezeilen: \t und \\ für Einrückung/Zeilenfortsetzung. Wird von showSamples() gelesen.
#   Pro Service anpassen: Ports, Env-Variablen, Volumes.
#
# shellcheck disable=SC2034  # samples wird von showSamples() aus build.lib.sh gelesen
declare -a samples=(
"# StockInfo starten (Unraid: Cache im gemappten Pfad) ||
\t     docker run --name ${NAME} \\
\t         --rm -p 8000:8000 \\
\t         -v /mnt/user/appdata/stockinfo:/data \\
\t         --env-file .env \\
\t         ${NAMESPACE}/${NAME}
"
)

#------------------------------------------------------------------------------
# Options
#

# usage — Verwendungshinweise anzeigen (Optionen, aktuelles Target, Plattform, Base-Image)
#
usage() {
    echo
    echo -e "OS:           ${YELLOW}${MACHINE}${NC}"
    echo -e "Architecture: ${YELLOW}${ARCHITECTURE}${NC}"
    echo -e "Platform:     ${YELLOW}${PLATFORM}${NC}"
    echo -e "Target:       ${YELLOW}${TARGET}${NC} → ${YELLOW}${REGISTRY}${NC}"
    echo -e "Base Image:   ${YELLOW}${DOCKER_BASE_IMAGE}${NC}"
    echo
    echo "Usage: $(basename "$0") [ options ]"
    echo -e "       Env: ${YELLOW}TARGET=ghcr|dockerhub|ecr${NC} (Default: ghcr) — Registry-Ziel für --push"
    echo
    usageLine "-u | --update                          " "Update base image: ${YELLOW}${DOCKER_BASE_IMAGE}${NC}"
    echo
    usageLine "-b | --build [ ${YELLOW}platform${NC} ]" "Build docker image: ${BLUE}${NAMESPACE}/${NAME}:${TAG}${NC}" 14
    echo
    usageLine "                                         " "${YELLOW}$PLATFORMS${NC}" 2
    usageLine "                                         " "${YELLOW}x86${NC}      - shortcut for ${YELLOW}linux/amd64${NC}" 2
    usageLine "                                         " "${YELLOW}arm | m1${NC} - shortcut for ${YELLOW}linux/arm64${NC}" 2
    usageLine "                                         " "${YELLOW}all${NC}      - shortcut for ${YELLOW}linux/amd64, linux/arm64${NC}" 2
    echo
    usageLine "-p | --push                              " "Push zu ${YELLOW}${IMAGE}${NC}"
    echo
    usageLine "-i | --images                            " "Images anzeigen: ${YELLOW}${NAMESPACE}/${NAME}${NC}"
    usageLine "-s | --samples                           " "Beispiel docker run Befehle anzeigen"
    echo
}


case "${CMDLINE}" in

    -u|--update)
        docker pull "${DOCKER_BASE_IMAGE}"
    ;;

    -b|--build)
        build
    ;;

    -i|--images)
        showBuiltImages
    ;;

    -s|--samples)
        showSamples
    ;;

    -p|--push)
        push
    ;;

    help|-help|--help|*)
        usage
    ;;

esac

#------------------------------------------------------------------------------
# Alles OK...

exit 0
