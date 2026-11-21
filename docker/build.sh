#!/usr/bin/env bash

#------------------------------------------------------------------------------
# Build Docker-Image: mangolila/stockinfo
#------------------------------------------------------------------------------

# BashLib: make build/push setzen BASH_LIBS; direkt aufgerufen hilft bashlib-path (make setup).
BASH_LIBS="${BASH_LIBS:-$(bashlib-path 2>/dev/null || true)}"
if [[ -z "${BASH_LIBS}" ]]; then echo "✗ BashLib nicht gefunden. Einrichten: make setup" >&2; exit 1; fi
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

readonly NAMESPACE="mangolila"
readonly NAME="stockinfo"

readonly TAGFILE="${SCRIPTPATH}/.last-build-tag"
readonly WARN_DAYS=7

# Lizenz- und Hinweisdateien, die das Image unter /app mitliefert. Vor dem
# Build müssen sie im Repository liegen, danach im Image bytegleich sein.
# docker/Dockerfile kopiert und prüft dieselben Dateien.
readonly LICENSE_FILES=(
    LICENSE
    LICENSE.de.txt
    LICENSING.md
    THIRD_PARTY_NOTICES.md
    plugin_api/LICENSE
    plugin_api/examples/us-example/LICENSE
)

#------------------------------------------------------------------------------
# Einbinden der globalen Build-Lib
#   Hier sind z.B. Farben, generell globale VARs und Funktionen definiert
#
if [[ "${__BUILD_LIB__:=""}"   == "" ]]; then . "${BASH_LIBS}/build.lib.sh";   fi
if [[ "${__DOCKER_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/docker.lib.sh";  fi
if [[ "${__VERSION_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/version.lib.sh"; fi

readonly PROJECT_NAME="${NAMESPACE}.${NAME}"

# Base-Image aus dem Dockerfile lesen — über eine temporäre Variable, damit
# DOCKER_BASE_IMAGE erst NACH der Prüfung readonly wird ('readonly VAR=$(cmd)'
# würde den Exit-Code des Subshell-Befehls verschlucken).
_BASE_IMAGE=$(\grep "^FROM " < Dockerfile | head -1 | sed "s/FROM //;s/ AS.*//") || _BASE_IMAGE=""
if [[ -z "${_BASE_IMAGE}" ]]; then
    echo -e "\n${RED}✗ Fehler:${NC} Kein 'FROM' im Dockerfile gefunden (${SCRIPTPATH}/Dockerfile)." >&2
    echo -e "${YELLOW}Prüfen:${NC} grep -n '^FROM' docker/Dockerfile\n" >&2
    exit 1
fi
readonly DOCKER_BASE_IMAGE="${_BASE_IMAGE}"
unset _BASE_IMAGE

#------------------------------------------------------------------------------
# Registry-Ziel (TARGET) — wohin `--push` das Image lädt
#
#   Überschreibbar per Env:   TARGET=dockerhub ./build.sh --push
#
#   ghcr       GitHub Container Registry (ghcr.io)
#              Image:   ghcr.io/<GITHUB_OWNER>/<NAMESPACE>-<NAME>
#              Login:   einmalig manuell —
#                       echo <PAT> | docker login ghcr.io -u <user> --password-stdin   (Scope: write:packages)
#              Braucht: GITHUB_OWNER  (per Env/.bashrc, sonst der hier gesetzte Default)
#
#   dockerhub  Docker Hub (docker.io)                                     [Default]
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
readonly TARGET="${TARGET:-dockerhub}"

# Registry-spezifische Variablen setzen: REGISTRY (Anzeige) + IMAGE (voll qualifizierte
# Registry-Referenz). Das lokal gebaute Image heisst immer ${NAMESPACE}/${NAME}.
case "${TARGET}" in
    ghcr)
        GITHUB_OWNER="${GITHUB_OWNER:-MikeMitterer}"
        if [[ -z "${GITHUB_OWNER}" ]]; then
            echo -e "\n${RED}✗ TARGET=ghcr:${NC} Var 'GITHUB_OWNER' nicht gesetzt!" >&2
            echo -e "${YELLOW}Setzen:${NC} GITHUB_OWNER=<user> TARGET=ghcr make build" >&2
            exit 1
        fi
        readonly GITHUB_OWNER
        readonly REGISTRY="ghcr.io"
        # Docker/OCI-Image-Referenzen müssen lowercase sein — GITHUB_OWNER kommt i.d.R.
        # in GitHub-Schreibweise (z.B. "MikeMitterer").
        readonly IMAGE="${REGISTRY}/${GITHUB_OWNER,,}/${NAMESPACE}-${NAME}"
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
            echo -e "\n${RED}✗ TARGET=ecr:${NC} Var 'AMAZON_REPO_URI' nicht gesetzt." >&2
            echo -e "${YELLOW}Beispiel:${NC} AMAZON_REPO_URI=123456789012.dkr.ecr.eu-west-1.amazonaws.com\n" >&2
            exit 1
        fi
        readonly AWS_REGION="${AWS_REGION:-eu-west-1}"
        readonly REGISTRY="${AMAZON_REPO_URI}"
        readonly IMAGE="${REGISTRY}/${NAME}"
    ;;
    *)
        echo -e "\n${RED}✗ Unbekanntes TARGET: '${TARGET}'${NC} — erlaubt: ${YELLOW}ghcr | dockerhub | ecr${NC}" >&2
        echo -e "${YELLOW}Zum Beispiel:${NC} TARGET=dockerhub make build\n" >&2
        exit 1
    ;;
esac

# CMDLINE kann ab hier verwendet werden ---------------------------------------

readonly CMDLINE=${1:-}
readonly OPTION=${2:-""}

# Jeder Buildversuch entwertet den vorherigen Push-Nachweis, auch wenn schon
# die Plattformwahl oder die Tag-Ermittlung fehlschlägt.
if [[ "${CMDLINE}" == "-b" || "${CMDLINE}" == "--build" ]]; then
    rm -f "${TAGFILE}"
fi

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

while [ $# -ne 0 ]; do
    case "${1}" in
        --build | -b)
            shift
            if [[ "${OPTION}" == "x86" ]]; then
                PLATFORM="linux/amd64"
            elif [[ "${OPTION}" == "arm" || "${OPTION}" == "m1" ]]; then
                PLATFORM="linux/arm64"
            elif [[ "${OPTION}" == "all" ]]; then
                echo -e "${RED}✗ Build abgebrochen:${NC} PLATFORM=all würde vor der Image-Prüfung automatisch veröffentlichen. x86 oder arm verwenden." >&2
                echo -e "${YELLOW}Stattdessen:${NC} make build PLATFORM=x86" >&2
                exit 1
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

# Streng nur für --build (dort wird das Image getaggt). Für Anzeige/Hilfe reicht
# best-effort (STRICT=0) — so funktioniert --help auch ohne Git-Tag im Clone.
if [[ "${CMDLINE}" == "-b" || "${CMDLINE}" == "--build" ]]; then
    BUILD_SOURCE_COMMIT=$(git -C .. rev-parse HEAD) || exit 1
    TAG_RC=0
    TAG="$(gitDockerTag "${STRICT}")" || TAG_RC=$?
    if [[ ${TAG_RC} -eq 2 ]]; then
        echo -e "\n${RED}✗ Build abgebrochen:${NC} Kein Git-Tag gefunden." >&2
        echo -e "${YELLOW}Tipp:${NC} semVerBump patch  ${BLUE}# oder manuell:${NC} git tag -a v0.1.0+$(date +%y%m%d.%H%M) -m 'Initial release'\n" >&2
        exit 1
    elif [[ ${TAG_RC} -eq 3 ]]; then
        echo -e "\n${RED}✗ Build abgebrochen:${NC} Working-Tree ist dirty." >&2
        echo -e "${YELLOW}Tipp:${NC} git commit oder git stash\n" >&2
        exit 1
    elif [[ ${TAG_RC} -eq 4 ]]; then
        echo -e "\n${RED}✗ Build abgebrochen:${NC} Repo ist ahead vom letzten Tag (STRICT=1)." >&2
        echo -e "${YELLOW}Tipp:${NC} semVerBump patch — oder mit ${BLUE}STRICT=2 ./build.sh --build${NC} (ahead erlaubt)\n" >&2
        exit 1
    elif [[ ${TAG_RC} -ne 0 ]]; then
        echo -e "\n${RED}✗ Build abgebrochen:${NC} gitDockerTag fehlgeschlagen (rc=${TAG_RC})." >&2
        echo -e "${YELLOW}Prüfen:${NC} git describe --tags --match 'v[0-9]*'\n" >&2
        exit 1
    fi
    unset TAG_RC
    if [[ "$(git -C .. rev-parse HEAD)" != "${BUILD_SOURCE_COMMIT}" ]]; then
        echo -e "${RED}✗ Build abgebrochen:${NC} Quellcommit hat sich während der Tag-Ermittlung geändert." >&2
        echo -e "${YELLOW}Neu bauen:${NC} make build" >&2
        exit 1
    fi
else
    TAG="$(gitDockerTag 0 2>/dev/null)" || TAG="n/a"
    BUILD_SOURCE_COMMIT=""
fi
readonly TAG
readonly BUILD_SOURCE_COMMIT

#------------------------------------------------------------------------------
# Functions
#

verifySourceTree() {
    local UNTRACKED
    if ! git -C .. diff --quiet HEAD --; then
        echo -e "${RED}✗ Abgebrochen:${NC} Der Quellstand enthält vorgemerkte oder ungespeicherte Änderungen." >&2
        echo -e "${YELLOW}Ansehen und committen:${NC} git status --short" >&2
        return 1
    fi
    UNTRACKED=$(git -C .. ls-files --others --exclude-standard -- app dashboard plugin_api contract docker/entrypoint.sh) || return 1
    if [[ -n "${UNTRACKED}" ]]; then
        echo -e "${RED}✗ Abgebrochen:${NC} Nicht versionierte Dateien liegen im Docker-Build-Kontext:${NC}" >&2
        printf '%s\n' "${UNTRACKED}" >&2
        echo -e "${YELLOW}Versionieren oder entfernen:${NC} git add <datei>" >&2
        return 1
    fi
}

# prepareConfig — Build-Eingaben prüfen. Das Dockerfile kopiert die Lizenzen
# direkt aus dem Repository; es gibt keinen manuellen Vorbereitungsschritt.
#
prepareConfig() {
    local FILE
    if (( STRICT >= 1 )); then
        verifySourceTree || return 1
    fi
    for FILE in "${LICENSE_FILES[@]}"; do
        if [[ ! -s "../${FILE}" ]]; then
            echo -e "${RED}✗ Build abgebrochen:${NC} Lizenz fehlt oder ist leer: ${FILE}" >&2
            echo -e "${YELLOW}Wiederherstellen:${NC} git restore -- ${FILE}" >&2
            return 1
        fi
    done
}

# verifyBuiltImage — Den tatsächlich gebauten Tag und die kopierten Lizenzen
# prüfen. Erst danach darf der Tag als pushbar gespeichert werden.
verifyBuiltImage() {
    local -r LOCAL_IMAGE="${NAMESPACE}/${NAME}:${TAG}"
    local IMAGE_ID LATEST_ID REGISTRY_ID REGISTRY_LATEST_ID ARCH
    local LICENSE EXPECTED ACTUAL

    IMAGE_ID=$(docker image inspect "${LOCAL_IMAGE}" --format '{{.Id}}') || return 1
    LATEST_ID=$(docker image inspect "${NAMESPACE}/${NAME}:latest" --format '{{.Id}}') || return 1
    REGISTRY_ID=$(docker image inspect "${IMAGE}:${TAG}" --format '{{.Id}}') || return 1
    REGISTRY_LATEST_ID=$(docker image inspect "${IMAGE}:latest" --format '{{.Id}}') || return 1
    if [[ "${IMAGE_ID}" != "${LATEST_ID}" ]] \
       || [[ "${IMAGE_ID}" != "${REGISTRY_ID}" ]] \
       || [[ "${IMAGE_ID}" != "${REGISTRY_LATEST_ID}" ]]; then
        echo -e "${RED}✗ Build-Prüfung fehlgeschlagen:${NC} Image-Tags zeigen auf unterschiedliche Images." >&2
        echo -e "${YELLOW}Neu bauen:${NC} make build" >&2
        return 1
    fi

    ARCH=$(docker image inspect "${LOCAL_IMAGE}" --format '{{.Architecture}}') || return 1
    if [[ "linux/${ARCH}" != "${PLATFORM}" ]]; then
        echo -e "${RED}✗ Build-Prüfung fehlgeschlagen:${NC} Architektur ${ARCH} statt ${PLATFORM}." >&2
        echo -e "${YELLOW}Mit Plattform neu bauen:${NC} make build PLATFORM=x86" >&2
        return 1
    fi

    if [[ "$(docker image inspect "${LOCAL_IMAGE}" --format '{{index .Config.Labels "org.opencontainers.image.licenses"}}')" != "EUPL-1.2" \
       || "$(docker image inspect "${LOCAL_IMAGE}" --format '{{index .Config.Labels "org.opencontainers.image.source"}}')" != "https://github.com/MikeMitterer/stockinfo" ]]; then
        echo -e "${RED}✗ Build-Prüfung fehlgeschlagen:${NC} Lizenz- oder Quelllabel fehlt." >&2
        echo -e "${YELLOW}Labels im Dockerfile prüfen:${NC} grep -n 'org.opencontainers' docker/Dockerfile" >&2
        return 1
    fi

    for LICENSE in "${LICENSE_FILES[@]}"; do
        EXPECTED=$(shasum -a 256 "../${LICENSE}") || return 1
        EXPECTED=${EXPECTED%% *}
        ACTUAL=$(docker run --rm --platform "${PLATFORM}" --entrypoint sha256sum "${LOCAL_IMAGE}" "/app/${LICENSE}") || return 1
        ACTUAL=${ACTUAL%% *}
        if [[ "${EXPECTED}" != "${ACTUAL}" ]]; then
            echo -e "${RED}✗ Build-Prüfung fehlgeschlagen:${NC} Lizenz weicht ab: ${LICENSE}" >&2
            echo -e "${YELLOW}Neu bauen:${NC} make build" >&2
            return 1
        fi
    done

    echo -e "${GREEN}Build geprüft:${NC} ${LOCAL_IMAGE} (${ARCH}, ${IMAGE_ID}); ${#LICENSE_FILES[@]} Lizenzdokumente und OCI-Labels stimmen."
}

# pushImage — Delegiert an die Registry-spezifische Lib-Push-Funktion (nach TARGET)
#
#   Jede Lib-Push-Funktion kapselt ihren eigenen Login und pusht den Tag + latest.
#
#   Params:
#     - Tag des zu pushenden Images
#
pushImage() {
    local -r PUSH_TAG=${1:?}

    case "${TARGET}" in
        ghcr)      pushImage2GHCR      "${GITHUB_OWNER,,}"  "${NAMESPACE}-${NAME}" "${PUSH_TAG}" ;;
        dockerhub) pushImage2DockerHub "${NAMESPACE}"       "${NAME}"              "${PUSH_TAG}" ;;
        ecr)       pushImage2Amazon    "${AMAZON_REPO_URI}" "${NAME}" "${PUSH_TAG}" "${AWS_REGION}" ;;
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
#   Das Image wird lokal gebaut, geprüft und erst danach als pushbar markiert.
#
build() {
    prepareConfig

    echo -e "\nBuilding for Platform: ${YELLOW}${PLATFORM}${NC} → Target: ${YELLOW}${TARGET}${NC}\n"

    buildSingleArchImage "${PLATFORM}" "${NAMESPACE}/${NAME}" "${IMAGE}" "${TAG}" "${LOGFILE}"
    verifyBuiltImage
    verifySourceTree
    if [[ "$(git -C .. rev-parse HEAD)" != "${BUILD_SOURCE_COMMIT}" ]]; then
        echo -e "${RED}✗ Build abgebrochen:${NC} Quellcommit hat sich während des Builds geändert." >&2
        echo -e "${YELLOW}Neu bauen:${NC} make build" >&2
        return 1
    fi
    showBuiltImages

    # Tag, Zeitpunkt, Image-ID, Quellcommit und Registry-Ziel festhalten.
    local BUILT_IMAGE_ID
    BUILT_IMAGE_ID=$(docker image inspect "${NAMESPACE}/${NAME}:${TAG}" --format '{{.Id}}')
    printf '%s\n' "${TAG}" "$(date +%s)" "${BUILT_IMAGE_ID}" "${BUILD_SOURCE_COMMIT}" "${TARGET}" > "${TAGFILE}"
}

# loadLastBuildTag — Tag des letzten Builds lesen und zurückgeben
#
#   Gibt den gespeicherten Tag via stdout zurück (für Zuweisung per $(...)).
#   Alle Meldungen und Warnungen gehen nach stderr, damit stdout sauber bleibt.
#   Bricht mit exit 1 ab wenn kein Build existiert.
#   Gibt eine Warnung aus wenn der Build älter als WARN_DAYS Tage ist.
#
#   Verwendung:
#     local LAST_TAG
#     LAST_TAG=$(loadLastBuildTag) || exit 1
#
loadLastBuildTag() {
    if [[ ! -f "${TAGFILE}" ]]; then
        echo -e "\n${RED}✗ Kein gespeicherter Build-Tag gefunden: ${TAGFILE}${NC}" >&2
        echo -e "${YELLOW}Zuerst bauen:${NC} make build\n" >&2
        exit 1
    fi

    local SAVED_TAG BUILD_TS NOW AGE_DAYS BUILD_DATE
    SAVED_TAG=$(sed -n '1p' "${TAGFILE}")
    BUILD_TS=$(sed -n '2p'  "${TAGFILE}")
    NOW=$(date +%s)
    AGE_DAYS=$(( (NOW - BUILD_TS) / 86400 ))
    BUILD_DATE=$(date -d "@${BUILD_TS}" "+%Y-%m-%d" 2>/dev/null \
               || date -r "${BUILD_TS}" "+%Y-%m-%d" 2>/dev/null \
               || echo "unbekannt")

    if (( AGE_DAYS >= WARN_DAYS )); then
        echo -e "\n${YELLOW}Warnung: Build ist ${AGE_DAYS} Tage alt (gebaut am ${BUILD_DATE}).${NC}" >&2
        echo -e "${YELLOW}         Neu bauen? → $(basename "$0") --build${NC}\n" >&2
    fi

    echo -e "Build vom ${YELLOW}${BUILD_DATE}${NC}: ${BLUE}${SAVED_TAG}${NC}" >&2
    echo "${SAVED_TAG}"
}

# verifyRemoteReleaseTag — Release-Tag des Quellcommits liegt unverändert in origin
#
#   make tag-* taggt nur lokal. Ein Image mit einer Version, deren Tag niemand
#   im Repo findet, geht deshalb nicht hinaus. Verglichen wird das Tag-Objekt,
#   damit auch ein gleichnamiger, aber anderer Tag im Remote auffällt.
#   Release-Tag ist, was gitDockerTag (version.lib.sh) für den Image-Tag nimmt:
#   der nächste Tag mit --match 'v[0-9]*'. Eine eigene Funktion dafür hat die
#   BashLib noch nicht (BashLib T-17); bis dahin muss der Filter hier derselbe bleiben.
#
#   Params:
#     $1 - Quellcommit des Builds
#
verifyRemoteReleaseTag() {
    local -r SOURCE_COMMIT="${1:?verifyRemoteReleaseTag: commit fehlt}"
    local RELEASE_TAG LOCAL_OBJECT REMOTE_LINE
    RELEASE_TAG=$(git -C .. describe --tags --abbrev=0 --match 'v[0-9]*' "${SOURCE_COMMIT}") || {
        echo -e "${RED}✗ Push abgebrochen:${NC} Kein Release-Tag für ${SOURCE_COMMIT}." >&2
        echo -e "${YELLOW}Version taggen:${NC} make tag-patch" >&2
        return 1
    }
    LOCAL_OBJECT=$(git -C .. rev-parse "refs/tags/${RELEASE_TAG}") || return 1
    REMOTE_LINE=$(git -C .. ls-remote --tags origin "refs/tags/${RELEASE_TAG}") || {
        echo -e "${RED}✗ Push abgebrochen:${NC} origin nicht erreichbar; Tag ${RELEASE_TAG} nicht geprüft." >&2
        echo -e "${YELLOW}Verbindung prüfen:${NC} git ls-remote --tags origin" >&2
        return 1
    }
    if [[ "${REMOTE_LINE%%[[:space:]]*}" != "${LOCAL_OBJECT}" ]]; then
        echo -e "${RED}✗ Push abgebrochen:${NC} Git-Tag ${RELEASE_TAG} liegt nicht in origin." >&2
        echo -e "${YELLOW}Zuerst veröffentlichen:${NC} git push --follow-tags" >&2
        return 1
    fi
}

# push — Zuletzt gebautes Image ins gewählte Registry-Ziel (TARGET) laden
#
#   Liest den Tag des letzten Builds aus TAGFILE und delegiert an pushImage(),
#   das je nach TARGET ghcr.io / Docker Hub / ECR bedient (Tag + latest).
#   Voraussetzung: der jeweilige Registry-Login ist vorhanden bzw. möglich.
#
push() {
    local LAST_TAG SAVED_IMAGE_ID SAVED_COMMIT SAVED_TARGET CURRENT_COMMIT REF CURRENT_IMAGE_ID
    verifySourceTree || return 1
    LAST_TAG=$(loadLastBuildTag) || exit 1
    SAVED_IMAGE_ID=$(sed -n '3p' "${TAGFILE}")
    SAVED_COMMIT=$(sed -n '4p' "${TAGFILE}")
    SAVED_TARGET=$(sed -n '5p' "${TAGFILE}")
    CURRENT_COMMIT=$(git -C .. rev-parse HEAD) || return 1
    if [[ -z "${SAVED_IMAGE_ID}" || -z "${SAVED_COMMIT}" || "${SAVED_COMMIT}" != "${CURRENT_COMMIT}" ]]; then
        echo -e "${RED}✗ Push abgebrochen:${NC} Build-Nachweis fehlt oder der Quellcommit hat sich geändert. Erneut make build ausführen." >&2
        return 1
    fi
    if [[ "${SAVED_TARGET}" != "${TARGET}" ]]; then
        echo -e "${RED}✗ Push abgebrochen:${NC} Build-Ziel ${SAVED_TARGET:-unbekannt} passt nicht zu ${TARGET}. Mit TARGET=${TARGET} make build neu bauen." >&2
        return 1
    fi
    verifyRemoteReleaseTag "${SAVED_COMMIT}" || return 1
    for REF in "${NAMESPACE}/${NAME}:${LAST_TAG}" "${NAMESPACE}/${NAME}:latest" "${IMAGE}:${LAST_TAG}" "${IMAGE}:latest"; do
        CURRENT_IMAGE_ID=$(docker image inspect "${REF}" --format '{{.Id}}') || return 1
        if [[ "${CURRENT_IMAGE_ID}" != "${SAVED_IMAGE_ID}" ]]; then
            echo -e "${RED}✗ Push abgebrochen:${NC} ${REF} gehört nicht zum zuletzt geprüften Build." >&2
            echo -e "${YELLOW}Neu bauen:${NC} make build" >&2
            return 1
        fi
    done

    echo -e "\nPushing ${YELLOW}${IMAGE}:${LAST_TAG}${NC} → ${YELLOW}${REGISTRY}${NC} (target: ${YELLOW}${TARGET}${NC})\n"
    pushImage "${LAST_TAG}"

    echo -e "\n${GREEN}Push erfolgreich: ${IMAGE}:${LAST_TAG}${NC}"
    if [[ "${TARGET}" == "dockerhub" ]]; then
        # dockerhub-readme hat im pipx-Paket noch keinen Befehl (ProjectTools T-16).
        if [[ ! -r "${PROJECT_TOOLS:-}/bash/dockerhub-readme.sh" ]]; then
            echo -e "${RED}✗ Docker-Hub-Beschreibung nicht übertragen:${NC} PROJECT_TOOLS zeigt nicht auf ProjectTools/src." >&2
            echo -e "${YELLOW}Setzen und wiederholen:${NC} PROJECT_TOOLS=<pfad>/ProjectTools/src make push" >&2
            return 1
        fi
        if ! DOCKER_README_AFTER_PUSH=1 \
            "${PROJECT_TOOLS}/bash/dockerhub-readme.sh" \
            --project-dir "${SCRIPTPATH}/.." --ref master \
            --publish --repository "${NAMESPACE}/${NAME}" --token-file "${DOCKER_PW_FILE}"; then
            return 1
        fi
    fi
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
    echo -e "       Env: ${YELLOW}TARGET=ghcr|dockerhub|ecr${NC} (Default: dockerhub) — Registry-Ziel für --push"
    echo
    usageLine "-u | --update                          " "Update base image: ${YELLOW}${DOCKER_BASE_IMAGE}${NC}"
    echo
    usageLine "-b | --build [ ${YELLOW}platform${NC} ]" "Build docker image: ${BLUE}${NAMESPACE}/${NAME}:${TAG}${NC}" 14
    echo
    usageLine "                                         " "${YELLOW}$PLATFORMS${NC}" 2
    usageLine "                                         " "${YELLOW}x86${NC}      - shortcut for ${YELLOW}linux/amd64${NC}" 2
    usageLine "                                         " "${YELLOW}arm | m1${NC} - shortcut for ${YELLOW}linux/arm64${NC}" 2
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
