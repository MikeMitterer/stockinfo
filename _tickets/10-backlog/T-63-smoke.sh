#!/usr/bin/env bash
# Isolierter Container-Test für T-63. Erstellt und entfernt nur eigene
# Container und Volumes. IMAGE_REF kann einen festen Release-Tag wählen.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT_DIR
readonly IMAGE_REF="${IMAGE_REF:-mangolila/stockinfo:latest}"
TEMP_DIR="$(mktemp -d /private/tmp/stockinfo-smoke.XXXXXX)"
VOLUME_NAME="$(docker volume create)"
CONTAINER_NAME="stockinfo-smoke-$(basename "${TEMP_DIR}")"
BAD_VOLUME_NAME=""
BAD_CONTAINER_NAME="${CONTAINER_NAME}-invalid"

cleanupSmoke() {
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker rm -f "${BAD_CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker volume rm "${VOLUME_NAME}" >/dev/null 2>&1 || true
    if [[ -n "${BAD_VOLUME_NAME}" ]]; then
        docker volume rm "${BAD_VOLUME_NAME}" >/dev/null 2>&1 || true
    fi
    rm -f "${TEMP_DIR}/test.env" "${TEMP_DIR}/ready.json" \
        "${TEMP_DIR}/fields.json" "${TEMP_DIR}/index.html" \
        "${TEMP_DIR}/quote.json" "${TEMP_DIR}/intake.json" \
        "${TEMP_DIR}/instruments.json" "${TEMP_DIR}/invalid.env" \
        "${TEMP_DIR}/invalid.log"
    rmdir "${TEMP_DIR}" 2>/dev/null || true
}
trap cleanupSmoke EXIT

printf 'STRICT_EXCHANGE=false\n' > "${TEMP_DIR}/test.env"
printf 'image=%s\nvolume=%s\n' "${IMAGE_REF}" "${VOLUME_NAME}"

cd "${ROOT_DIR}"
./scripts/sources-profile.sh --yaml --target docker --volume "${VOLUME_NAME}"

startContainer() {
    docker run -d --platform linux/amd64 --name "${CONTAINER_NAME}" \
        -p 127.0.0.1::8000 --env-file "${TEMP_DIR}/test.env" \
        -e HOST=0.0.0.0 -e PORT=8000 -e DATABASE_PATH=/data/stockinfo.db \
        -v "${VOLUME_NAME}:/data" "${IMAGE_REF}" >/dev/null
    local -r ADDRESS="$(docker port "${CONTAINER_NAME}" 8000/tcp)"
    BASE_URL="http://${ADDRESS}"
    for ((ATTEMPT = 1; ATTEMPT <= 45; ATTEMPT++)); do
        if curl -fsS --max-time 2 "${BASE_URL}/ready" \
            > "${TEMP_DIR}/ready.json" 2>/dev/null; then
            printf 'ready=%s after=%s\n' "${BASE_URL}" "${ATTEMPT}"
            return 0
        fi
        sleep 1
    done
    docker logs "${CONTAINER_NAME}" >&2
    return 1
}

startContainer
curl -fsS "${BASE_URL}/health" >/dev/null
curl -fsS "${BASE_URL}/fields" > "${TEMP_DIR}/fields.json"
curl -fsS "${BASE_URL}/" > "${TEMP_DIR}/index.html"
rg -qi '<!doctype html|<html' "${TEMP_DIR}/index.html"
INTAKE_STATUS="$(curl -sS -o "${TEMP_DIR}/intake.json" -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    -d '{"identifier":"IE00B4L5Y983"}' \
    "${BASE_URL}/instruments/intake")"
test "${INTAKE_STATUS}" = 201
python3 -c 'import json, sys; item = json.load(open(sys.argv[1])); assert item["identity"]["isin"] == "IE00B4L5Y983"; print("intake=", item["identity"]["isin"])' "${TEMP_DIR}/intake.json"
curl -fsS "${BASE_URL}/quote/IE00B4L5Y983" > "${TEMP_DIR}/quote.json"
python3 -c 'import json, sys; item = json.load(open(sys.argv[1])); assert item["identity"]["isin"] == "IE00B4L5Y983"; assert abs(float(item["price"]) - 128.21) < 0.01; assert item["provider"] == "iShares"; assert abs(float(item["ter"]) - 0.2) < 0.001; print("quote=", item["identity"]["isin"], item["price"], item["provider"], item["ter"])' "${TEMP_DIR}/quote.json"
curl -fsS "${BASE_URL}/instruments" > "${TEMP_DIR}/instruments.json"
python3 -c 'import json, sys; data = json.load(open(sys.argv[1])); assert "IE00B4L5Y983" in json.dumps(data); print("stored=IE00B4L5Y983")' "${TEMP_DIR}/instruments.json"
docker top "${CONTAINER_NAME}" -eo pid,uid,gid,args

docker rm -f "${CONTAINER_NAME}" >/dev/null
startContainer
curl -fsS "${BASE_URL}/instruments" > "${TEMP_DIR}/instruments.json"
python3 -c 'import json, sys; data = json.load(open(sys.argv[1])); assert "IE00B4L5Y983" in json.dumps(data); print("persisted=IE00B4L5Y983")' "${TEMP_DIR}/instruments.json"
for ((ATTEMPT = 1; ATTEMPT <= 45; ATTEMPT++)); do
    HEALTH_STATUS="$(docker inspect "${CONTAINER_NAME}" --format '{{.State.Health.Status}}')"
    if [[ "${HEALTH_STATUS}" == healthy ]]; then
        printf 'health=%s after=%s\n' "${HEALTH_STATUS}" "${ATTEMPT}"
        break
    fi
    sleep 1
done
test "${HEALTH_STATUS}" = healthy

BAD_VOLUME_NAME="$(docker volume create)"
printf 'STRICT_EXCHANGE=false   \n' > "${TEMP_DIR}/invalid.env"
docker run -d --platform linux/amd64 --name "${BAD_CONTAINER_NAME}" \
    --env-file "${TEMP_DIR}/invalid.env" -e DATABASE_PATH=/data/stockinfo.db \
    -v "${BAD_VOLUME_NAME}:/data" "${IMAGE_REF}" >/dev/null
for ((ATTEMPT = 1; ATTEMPT <= 30; ATTEMPT++)); do
    BAD_STATE="$(docker inspect "${BAD_CONTAINER_NAME}" --format '{{.State.Status}}')"
    if [[ "${BAD_STATE}" == exited ]]; then
        break
    fi
    sleep 1
done
docker logs "${BAD_CONTAINER_NAME}" > "${TEMP_DIR}/invalid.log" 2>&1
test "${BAD_STATE}" = exited
rg -qi 'strict_exchange|validationerror' "${TEMP_DIR}/invalid.log"
printf 'invalid_env=ValidationError\n'
