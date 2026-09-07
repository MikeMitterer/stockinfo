#!/usr/bin/env bash
#------------------------------------------------------------------------------
# sources-profile.sh — zwischen der Online-Kette und dem YAML-Plugin umschalten
#
# Die App liest ihre Quellen aus `sources.yaml` **neben der Datenbank**
# (`app/container.py:sources_path`) — nicht aus einer eigenen Einstellung. Wer
# das Plugin wechseln will, tauscht also diese eine Datei und startet neu.
# Genau das tut dieses Script, samt Sicherung einer eigenen Fassung.
#
# Zwei Profile aus den Betriebsvorlagen unter examples/:
#
#   online  Die Online-Kette (OpenFIGI, Yahoo, justETF, yfinance) mit
#           `yaml-file` als **letztem** Glied. Online gewinnt bei
#           Überschneidung; die Datei liefert nur, wo die Kette nichts hat.
#   yaml    Nur `yaml-file` — alle fünf Rollen aus einer Datei, ohne Netz.
#
# local schreibt neben die lokale Datenbank, docker in das Host-Verzeichnis
# des Daten-Volumes. sources.yaml enthält in beiden Fällen nur den Dateinamen:
# Die App löst ihn relativ zu sources.yaml auf. Eigene Dateien von außerhalb
# werden in dieses Verzeichnis kopiert, ohne vorhandene Daten zu überschreiben.
#
# Die Fachdaten für `yaml-file` liegen im **Datenverzeichnis**, nicht im Repo:
# `assets-fallback.yaml` für online, `assets-standalone.yaml` für yaml.
# Fehlende Dateien werden einmalig aus examples/ kopiert. Vorhandene
# Fachdaten werden nicht überschrieben; sources.yaml wird vor dem Wechsel gesichert.
#
# Verwendung:
#   ./scripts/sources-profile.sh --show
#   ./scripts/sources-profile.sh --yaml
#   ./scripts/sources-profile.sh --online --target docker
#   ./scripts/sources-profile.sh --yaml --target docker --data-dir /mnt/user/appdata/stockinfo
#
# Optionen:
#   -o | --online          Auf die Online-Kette umschalten
#   -y | --yaml            Auf das YAML-Plugin umschalten
#   -t | --target TARGET   local (Vorgabe) oder docker
#   -a | --assets FILE     Fachdatendatei für `yaml-file`
#   -d | --data-dir DIR    Datenverzeichnis (bei Docker der Host-Mount)
#   -s | --show            Aktives Profil zeigen — Datei und laufender Server
#   -i | --info            Einstellungen anzeigen
#   -h | --help            Diese Hilfe anzeigen
#------------------------------------------------------------------------------
set -uo pipefail

BASH_LIBS="${BASH_LIBS:-$(cd "$(dirname "$0")/../.libs/BashLib/src" && pwd)}"

if [[ "${__COLORS_LIB__:=""}" == "" ]]; then . "${BASH_LIBS}/colors.lib.sh"; fi
if [[ "${__TOOLS_LIB__:=""}"  == "" ]]; then . "${BASH_LIBS}/tools.lib.sh";  fi

readonly APPNAME="${0##*/}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)" || exit 1
readonly PROJECT_ROOT

# Wo die App im **Entwicklungsstand** ihre Quellen sucht: neben der Datenbank.
# Steht `DATABASE_PATH` in der Umgebung, gilt sie auch hier — sonst die Vorgabe
# aus `app/config.py`.
LOCAL_DATA_DIR="$(dirname "${DATABASE_PATH:-${PROJECT_ROOT}/data/stockinfo.db}")"

# Der Host-Pfad, den das Beispiel in `docker/build.sh` auf `/data` mappt.
readonly DEFAULT_DOCKER_DATA_DIR="/mnt/user/appdata/stockinfo"

# Wie das Volume **im Container** heißt (`docker/Dockerfile`: `VOLUME ["/data"]`).
readonly CONTAINER_DATA_DIR="/data"
readonly CONTAINER_NAME="${STOCKINFO_CONTAINER:-stockinfo}"

# Der Port, auf dem der Server lauscht — nur für die Lebendabfrage. `make dev`
# und das `docker run`-Beispiel verwenden beide 8000.
readonly PORT="${PORT:-8000}"
readonly BASE_URL="http://127.0.0.1:${PORT}"

# Wie die Fachdaten im Datenverzeichnis heißen. **Sie gehören neben die
# Datenbank**, nicht ins Repo: Sie sind Betriebsdaten, überleben ein Update und
# sind im Container derselbe Pfad wie hier.
ASSETS_NAME=""

# Vorlagen werden nach der Profilwahl festgelegt.
SAMPLE_ASSETS=""
SAMPLE_SOURCES=""

# **Kein YAML-Schlüssel.** `profile:` ist in `sources.yaml` bereits vergeben —
# dort benennt er ein Paket. Die Marke steht deshalb im Kommentar; sie sagt
# nur, welches der beiden Profile dieses Script zuletzt geschrieben hat.
readonly PROFILE_MARK="# stockinfo-profile:"

readonly ROLES="resolvers etf_meta quotes daily fx"

TARGET="local"
DOCKER_DATA_DIR="${DEFAULT_DOCKER_DATA_DIR}"
ACTION=""
DATA_DIR=""

# Leer, bis `--assets` etwas anderes sagt. Die Vorgabe steht erst fest, wenn
# das Ziel geparst ist — sie hängt am Datenverzeichnis, und das unterscheidet
# sich zwischen `local` und `docker`.
ASSETS_FILE=""

usage() {
    echo
    echo "Usage: ${APPNAME} [ options ]"
    echo
    echo -e "    ${BLUE}# Umschalten --------------------------------------------------------${NC}"
    usageLine "-o | --online       " "Online-Kette, ${YELLOW}yaml-file${NC} als letztes Glied"
    usageLine "-y | --yaml         " "Nur ${YELLOW}yaml-file${NC} — fünf Rollen aus einer Datei"
    usageLine "-t | --target TARGET" "${YELLOW}local${NC} (Vorgabe) oder ${YELLOW}docker${NC}"
    usageLine "-a | --assets FILE  " "Eigene Fachdatei (sonst assets-fallback.yaml / assets-standalone.yaml)"
    usageLine "-d | --data-dir DIR " "Datenverzeichnis; bei Docker der Host-Mount"
    echo
    echo -e "    ${BLUE}# Auskunft ----------------------------------------------------------${NC}"
    usageLine "-s | --show         " "Aktives Profil — Datei und laufender Server"
    usageLine "-i | --info         " "Einstellungen anzeigen"
    usageLine "-h | --help         " "Diese Hilfe anzeigen"
    echo
    echo -e "${LIGHT_BLUE}Hints:${NC}"
    echo -e "    Umschalten:    ${GREEN}${APPNAME} --yaml${NC}"
    echo -e "    Zurück:        ${GREEN}${APPNAME} --online${NC}"
    echo -e "    Im Container:  ${GREEN}${APPNAME} --yaml --target docker${NC}"
    echo -e "    Nachsehen:     ${GREEN}${APPNAME} --show${NC}"
    echo
    echo -e "    Die Kette wird beim ${RED}Start${NC} gelesen — Umschalten allein wirkt nicht."
    echo -e "    Danach ${GREEN}make dev-down && make dev-up${NC} bzw. ${GREEN}docker restart ${CONTAINER_NAME}${NC}."
    echo
}

# Das Verzeichnis, in das `sources.yaml` geschrieben wird — je Ziel ein anderes.
configDir() {
    if [[ "${TARGET}" == "docker" ]]; then echo "${DOCKER_DATA_DIR}"; else echo "${LOCAL_DATA_DIR}"; fi
}

configFile() {
    echo "$(configDir)/sources.yaml"
}

showInfo() {
    echo
    logFileStatus "Projekt-Root: " "${PROJECT_ROOT}"
    logFileStatus "sources.yaml: " "$(configFile)"
    logFileStatus "Fallback:    " "$(configDir)/assets-fallback.yaml"
    logFileStatus "Standalone:  " "$(configDir)/assets-standalone.yaml"
    [[ -z "${ASSETS_FILE}" ]] || logFileStatus "Eigene Datei: " "${ASSETS_FILE}"
    echo -e "    ${YELLOW}Ziel  ${NC} = ${BLUE}${TARGET}${NC}"
    if [[ "${TARGET}" == "docker" ]]; then
        echo -e "    ${YELLOW}Mount ${NC} = ${BLUE}${DOCKER_DATA_DIR}${NC} → ${BLUE}${CONTAINER_DATA_DIR}${NC}"
        echo -e "    ${YELLOW}Cont. ${NC} = ${BLUE}${CONTAINER_NAME}${NC}"
    fi
    echo -e "    ${YELLOW}Port  ${NC} = ${BLUE}${PORT}${NC}"
    echo
}

# Sichert eine vorhandene Konfiguration, bevor sie überschrieben wird.
#
# Auch generierte Dateien können nachträglich bearbeitet worden sein.
# Jede bisherige Fassung bekommt deshalb eine eigene Sicherung.
#
# Returns:
#   0 wenn nichts zu sichern war oder die Sicherung steht, 1 bei Schreibfehler
backupConfig() {
    local -r _FILE="$(configFile)"
    [[ -f "${_FILE}" ]] || return 0
    local _BACKUP
    _BACKUP="$(mktemp "${_FILE}.bak.XXXXXX")" || return 1
    cp "${_FILE}" "${_BACKUP}" || return 1
    echo -e "  ${BLUE}ℹ${NC} bisherige Fassung gesichert → ${_BACKUP}"
    return 0
}

# Legt fehlende Fachdaten aus der passenden Betriebsvorlage an.
#
# Wer `--assets` angibt, meint eine bestimmte Datei; fehlt sie, ist das ein
# Fehler und kein Anlass, ihm eine andere unterzuschieben.
#
# **Kopie, kein Symlink.** Ein Link ins Repo zeigt im Container ins Leere — dort
# ist nur `/data` gemountet, und `_tickets/…` gibt es nicht. Dazu gehören diese
# Zeilen dem Betreiber: Er ändert Kurse und Papiere darin, und ein Link würde
# ihn eine eingecheckte Beispieldatei bearbeiten lassen.
#
# Returns:
#   0 wenn die Datei danach existiert, 1 sonst
seedDefaultAssets() {
    [[ "${ASSETS_IS_DEFAULT}" == true ]] || return 0
    [[ -f "${ASSETS_FILE}" ]] && return 0

    cp "${SAMPLE_ASSETS}" "${ASSETS_FILE}" || return 1
    echo -e "  ${BLUE}ℹ${NC} Fachdaten angelegt aus ${BLUE}$(basename "${SAMPLE_ASSETS}")${NC} → ${ASSETS_FILE}"
    echo -e "      Ab jetzt deine Datei — sie wird nicht mehr überschrieben."
    return 0
}

# Legt Fachdaten neben sources.yaml und gibt den relativen Dateinamen aus.
# Vorhandene Dateien dürfen nur identisch sein; abweichende werden abgewiesen.
#
# Returns:
#   0 und den Dateinamen auf stdout, 1 bei Kopierfehler oder Kollision
placeAssets() {
    local -r _TARGET_FILE="$(configDir)/$(basename "${ASSETS_FILE}")"
    if [[ "${ASSETS_FILE}" != "${_TARGET_FILE}" ]]; then
        if [[ -e "${_TARGET_FILE}" ]]; then
            cmp -s "${ASSETS_FILE}" "${_TARGET_FILE}" || {
                echo "Vorhandene Fachdatei wird nicht überschrieben: ${_TARGET_FILE}" >&2
                return 1
            }
        else
            cp "${ASSETS_FILE}" "${_TARGET_FILE}" || return 1
        fi
    fi
    basename "${ASSETS_FILE}"
    return 0
}

# Übernimmt die versionierte Vorlage und ersetzt nur den Fachdateipfad.
# YAML-Einfachquotierung schützt auch Leerzeichen, Doppelpunkte und Apostrophe.
#
# Params:
#   $1 - Pfad zu den Fachdaten, wie ihn die App sieht
writeProfile() {
    local -r _ASSETS_PATH="$1"
    local _QUOTED_PATH _TEMP_FILE
    _QUOTED_PATH="$(printf '%s' "${_ASSETS_PATH}" | sed "s/'/''/g")" || return 1
    _TEMP_FILE="$(mktemp "$(configFile).tmp.XXXXXX")" || return 1
    if {
        printf '%s %s\n' "${PROFILE_MARK}" "${ACTION}"
        STOCKINFO_ASSET_PATH="${_QUOTED_PATH}" awk '
            /^    path:/ { print "    path: " sprintf("%c", 39) ENVIRON["STOCKINFO_ASSET_PATH"] sprintf("%c", 39); next }
            { print }
        ' "${SAMPLE_SOURCES}"
    } > "${_TEMP_FILE}"; then
        mv "${_TEMP_FILE}" "$(configFile)"
    else
        unlink "${_TEMP_FILE}"
        return 1
    fi
}

# Prüft, ob geschrieben werden kann. Meldet die Ursache, nicht nur ein Nein.
#
# Returns:
#   0 wenn Verzeichnis und Fachdaten da sind, 1 sonst
requireWritableTarget() {
    if [[ ! -d "$(configDir)" ]]; then
        echo -e "\n  ${RED}✗${NC} ${BLUE}$(configDir)${NC} gibt es nicht." >&2
        if [[ "${TARGET}" == "docker" ]]; then
            echo -e "      Das ist der Host-Pfad, der auf ${YELLOW}${CONTAINER_DATA_DIR}${NC} gemappt ist." >&2
            echo -e "      Anderer Pfad: ${GREEN}${APPNAME} --target docker --data-dir <pfad>${NC}\n" >&2
        else
            echo -e "      Die Kette gehört neben die Datenbank — erst ${GREEN}make dev${NC}, dann umschalten.\n" >&2
        fi
        return 1
    fi
    seedDefaultAssets || {
        echo -e "\n  ${RED}✗${NC} Fachdaten konnten nicht angelegt werden: ${BLUE}${ASSETS_FILE}${NC}\n" >&2
        return 1
    }
    if [[ ! -f "${ASSETS_FILE}" ]]; then
        echo -e "\n  ${RED}✗${NC} Fachdaten fehlen: ${BLUE}${ASSETS_FILE}${NC}" >&2
        echo -e "      Ohne sie antwortet ${YELLOW}yaml-file${NC} auf nichts.\n" >&2
        return 1
    fi
    return 0
}

# Nennt den Neustart, der das Umschalten wirksam macht — je Ziel einen anderen.
showRestartHint() {
    if [[ "${TARGET}" == "docker" ]]; then
        echo -e "  ${BLUE}ℹ${NC} Wirksam wird es beim Start: ${GREEN}docker restart ${CONTAINER_NAME}${NC}"
        echo -e "      Dieses Script startet nichts neu — es weiß nicht, wem der Container gehört."
    else
        echo -e "  ${BLUE}ℹ${NC} Wirksam wird es beim Start: ${GREEN}make dev-down && make dev-up${NC}"
        echo -e "      ${YELLOW}--reload${NC} sieht diese Datei nicht; sie wird nur beim Start gelesen."
    fi
}

# Schaltet auf ein Profil um.
#
# Params:
#   $1 - "online" oder "yaml"
#
# Returns:
#   0 wenn geschrieben, 1 sonst
switchTo() {
    local -r _PROFILE="$1"
    requireWritableTarget || return 1

    local _ASSETS_PATH
    _ASSETS_PATH="$(placeAssets)" || {
        echo -e "  ${RED}✗${NC} Fachdaten konnten nicht nach ${BLUE}$(configDir)${NC} kopiert werden" >&2
        return 1
    }

    backupConfig || return 1
    writeProfile "${_ASSETS_PATH}" || {
        echo -e "  ${RED}✗${NC} Schreiben fehlgeschlagen" >&2
        return 1
    }

    echo
    echo -e "  ${GREEN}✓${NC} Profil ${YELLOW}${_PROFILE}${NC} geschrieben → ${BLUE}$(configFile)${NC}"
    echo -e "      Fachdaten relativ zu sources.yaml: ${YELLOW}${_ASSETS_PATH}${NC}"
    showFileProfile
    showRestartHint
    echo
    return 0
}

# Zeigt, was in der Datei steht — Rolle für Rolle.
#
# Gelesen wird mit `awk`, nicht mit einem YAML-Parser: Das Script soll auch auf
# einem Unraid-Host laufen, auf dem es weder `.venv` noch `python3` gibt.
showFileProfile() {
    local -r _FILE="$(configFile)"
    if [[ ! -f "${_FILE}" ]]; then
        echo -e "      Datei:  ${YELLOW}keine — die App läuft mit ihren Vorgaben${NC}"
        return 0
    fi

    local -r _MARK="$(sed -n "s|^${PROFILE_MARK} ||p" "${_FILE}" | head -1)"
    echo -e "      Datei:  ${YELLOW}${_MARK:-eigene Fassung}${NC} (${_FILE})"
    awk -v roles="${ROLES}" '
        BEGIN { split(roles, wanted, " ") }
        /^    path:/ { printf "        Fachdaten  %s\n", substr($0, 11) }
        {
            for (index_ in wanted) {
                role = wanted[index_]
                if ($0 ~ "^" role ":") {
                    line = $0
                    sub("^" role ": *", "", line)
                    printf "        %-10s %s\n", role, line
                }
            }
        }
    ' "${_FILE}"
}

# Zeigt, was der **laufende** Server tut.
#
# Das ist die einzige Aussage, die zählt, solange er läuft: Die Datei kann
# längst umgeschaltet sein — gelesen wird sie beim Start.
showLiveProfile() {
    local _ANSWER
    _ANSWER="$(curl -s --max-time 3 "${BASE_URL}/sources" 2>/dev/null)"
    if [[ -z "${_ANSWER}" ]]; then
        echo -e "      Server: ${YELLOW}antwortet nicht auf ${BASE_URL}${NC}"
        return 0
    fi

    echo -e "      Server: ${GREEN}${BASE_URL}${NC}"
    # `/sources` liefert eine flache Liste; die Reihenfolge je Rolle ist die
    # Rangfolge. `tr` und `awk` reichen dafür — siehe showFileProfile.
    echo "${_ANSWER}" \
        | tr '{' '\n' \
        | awk -F'"' '/"name"/ && /"role"/ {
              name = ""; role = ""
              for (field = 1; field < NF; field++) {
                  if ($field == "name")  name = $(field + 2)
                  if ($field == "role")  role = $(field + 2)
              }
              if (role != "") chains[role] = chains[role] (chains[role] ? ", " : "") name
          }
          END {
              split("resolvers etf_meta quotes daily fx", order, " ")
              for (position = 1; position <= 5; position++)
                  printf "        %-10s %s\n", order[position], (chains[order[position]] ? chains[order[position]] : "—")
          }'
}

showProfile() {
    echo
    showFileProfile
    echo
    showLiveProfile
    echo
}

# Macht aus einem relativen einen absoluten Pfad, ohne die Datei zu öffnen.
#
# Params:
#   $1 - Pfad, relativ oder absolut
absolutePath() {
    local -r _PATH="$1"
    if [[ "${_PATH}" == /* ]]; then
        printf '%s\n' "${_PATH}"
    else
        printf '%s/%s\n' "${PWD}" "${_PATH}"
    fi
}

#------------------------------------------------------------------------------
# Options
#

if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--online) ACTION="online" ;;
        -y|--yaml)   ACTION="yaml"   ;;
        -s|--show)   ACTION="show"   ;;
        -i|--info)   ACTION="info"   ;;
        -h|--help)   usage; exit 0   ;;
        -t|--target)
            shift
            [[ $# -gt 0 ]] || { echo -e "${RED}--target braucht local oder docker${NC}" >&2; exit 1; }
            case "$1" in
                local|docker) TARGET="$1" ;;
                *) echo -e "${RED}Unbekanntes Ziel '$1' — erlaubt: local, docker${NC}" >&2; exit 1 ;;
            esac
            ;;
        -a|--assets)
            shift
            [[ $# -gt 0 ]] || { echo -e "${RED}--assets braucht eine Datei${NC}" >&2; exit 1; }
            ASSETS_FILE="$(absolutePath "$1")"
            ;;
        -d|--data-dir)
            shift
            [[ $# -gt 0 ]] || { echo -e "${RED}--data-dir braucht ein Verzeichnis${NC}" >&2; exit 1; }
            DATA_DIR="$1"
            ;;
        *)
            echo -e "${RED}Unbekannte Option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
    shift
done

# **Die Vorgabe steht erst hier fest.** Sie liegt im Datenverzeichnis, und
# welches das ist, entscheidet `--target` — das oben noch nicht geparst war.
ASSETS_IS_DEFAULT=false
if [[ -n "${DATA_DIR}" ]]; then
    if [[ "${TARGET}" == "docker" ]]; then
        DOCKER_DATA_DIR="${DATA_DIR}"
    else
        LOCAL_DATA_DIR="${DATA_DIR}"
    fi
fi
LOCAL_DATA_DIR="$(absolutePath "${LOCAL_DATA_DIR}")"
DOCKER_DATA_DIR="$(absolutePath "${DOCKER_DATA_DIR}")"
case "${ACTION}" in
    online) ASSETS_NAME="assets-fallback.yaml"; SAMPLE_SOURCES="${PROJECT_ROOT}/examples/sources-fallback.yaml" ;;
    yaml) ASSETS_NAME="assets-standalone.yaml"; SAMPLE_SOURCES="${PROJECT_ROOT}/examples/sources-standalone.yaml" ;;
esac
SAMPLE_ASSETS="${PROJECT_ROOT}/examples/${ASSETS_NAME}"
if [[ -z "${ASSETS_FILE}" && -n "${ASSETS_NAME}" ]]; then
    ASSETS_FILE="$(configDir)/${ASSETS_NAME}"
    ASSETS_IS_DEFAULT=true
fi
readonly ASSETS_FILE ASSETS_IS_DEFAULT

case "${ACTION}" in
    online|yaml) switchTo "${ACTION}" || exit 1 ;;
    show)        showProfile ;;
    info)        showInfo ;;
    *)           usage ;;
esac
