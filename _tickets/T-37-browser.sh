#!/usr/bin/env bash
#------------------------------------------------------------------------------
# T-37-browser.sh — startet den Stack fuer die Browser-Abnahme (Verify #6/#7)
#
# Der Smoke `T-35-smoke.sh` raeumt hinter sich auf; fuer einen Blick mit Augen
# braucht es einen Stack, der **stehen bleibt**. Genau das tut dieses Script:
# Volume anlegen, Profil schreiben, Server starten, Adresse nennen, warten.
#
# Eigener Port und eigenes Volume — die Arbeitsdatenbank wird nicht angefasst.
# Beendet wird nur die selbst gestartete PID.
#
# Verwendung:
#   ./_tickets/T-37-browser.sh --run            # YAML-Profil
#   PROFILE=online ./_tickets/T-37-browser.sh --run
#   ./_tickets/T-37-browser.sh --stop
#------------------------------------------------------------------------------
set -uo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
readonly PORT="${PORT:-8799}"
readonly PROFILE="${PROFILE:-yaml}"
readonly STATE="/tmp/t-37-browser-${PORT}"
readonly VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

writeVolume() {
    local -r _WORKDIR="$1"

    cat > "${_WORKDIR}/assets.yaml" <<'YAML'
version: 1

instruments:
  # Ein Papier, das beide Profile fuehren — hier entscheidet sich, ob online
  # gewinnt oder die Datei ueberschreibt (Verify #7).
  - id: world-etf
    identity: {kind: listed, isin: IE00B4L5Y983, ticker: EUNL, mic: XETR}
    name: iShares Core MSCI World UCITS ETF
    instrument_type: etf
    price: {value: 111.11, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}
    metadata: {ter_bps: 20, provider: iShares, fund_domicile: Ireland}

  # Die Coin — im YAML-Profil aus der Datei, im Online-Profil von YFinance.
  - id: bitcoin-eur
    identity: {kind: pair, base: BTC, quote_currency: EUR}
    name: Bitcoin
    instrument_type: crypto
    price: {value: 94500.00, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}

  # Die Anleihe: kein Handelsplatz, keine Online-Kursquelle. Sie ist der Grund
  # fuer den Datei-Rueckfall im Online-Profil.
  - id: german-bond
    identity: {kind: isin_only, isin: DE0001102531}
    name: Bundesrepublik Deutschland
    instrument_type: bond
    history:
      currency: EUR
      closes:
        - {date: "2026-08-25", value: 99.18}
        - {date: "2026-08-26", value: 99.31}
        - {date: "2026-08-27", value: 99.42}

  # Ein nicht boersengehandelter Fonds — Gattung `fund`, Form `isin_only`.
  - id: active-fund
    identity: {kind: isin_only, isin: DE0009848119}
    name: DWS Top Dividende LD
    instrument_type: fund
    price: {value: 142.50, currency: EUR, as_of: "2026-08-27T17:30:00+02:00"}

fx_rates:
  - {base: CAD, quote: EUR, rate: 0.6412, as_of: "2026-08-27T17:30:00+02:00"}
YAML

    if [[ "${PROFILE}" == "online" ]]; then
        # Dieselbe Datei **hinter** den Online-Quellen: Sie ergaenzt, wo die
        # Kette nichts hat, und ueberschreibt nichts.
        cat > "${_WORKDIR}/sources.yaml" <<YAML
resolvers: [openfigi, yahoo-search, yaml-file]
etf_meta:  [justetf, yfinance, yaml-file]
quotes:    [yfinance, yaml-file]
daily:     [yfinance, yaml-file]
fx:        [yfinance, yaml-file]

providers:
  yaml-file:
    path: ${_WORKDIR}/assets.yaml
YAML
    else
        cat > "${_WORKDIR}/sources.yaml" <<YAML
resolvers: [yaml-file]
etf_meta:  [yaml-file]
quotes:    [yaml-file]
daily:     [yaml-file]
fx:        [yaml-file]

providers:
  yaml-file:
    path: ${_WORKDIR}/assets.yaml
YAML
    fi
}

runStack() {
    local _WORKDIR
    _WORKDIR="$(mktemp -d)"
    writeVolume "${_WORKDIR}"

    (
        cd "${PROJECT_ROOT}" || exit 1
        DATABASE_PATH="${_WORKDIR}/stockinfo.db" \
        DATA_DIR="${_WORKDIR}" \
        STATIC_DIR="${PROJECT_ROOT}/dashboard/dist" \
        "${VENV_PY}" -m uvicorn app.main:app --port "${PORT}" --log-level warning \
            > "${_WORKDIR}/server.log" 2>&1 &
        echo $! > "${STATE}.pid"
    )
    echo "${_WORKDIR}" > "${STATE}.dir"

    local _TRY
    for _TRY in $(seq 1 40); do
        if curl -sf "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1; then
            echo "bereit: http://127.0.0.1:${PORT}/  (Profil ${PROFILE}, Volume ${_WORKDIR})"
            return 0
        fi
        sleep 0.5
    done
    echo "Server kam nicht hoch — Log:"
    tail -20 "${_WORKDIR}/server.log"
    return 1
}

stopStack() {
    if [[ -f "${STATE}.pid" ]]; then
        kill "$(cat "${STATE}.pid")" 2>/dev/null && echo "beendet: PID $(cat "${STATE}.pid")"
        rm -f "${STATE}.pid"
    else
        echo "keine eigene PID vermerkt"
    fi
}

case "${1:-}" in
    -r|--run)  runStack ;;
    -s|--stop) stopStack ;;
    *)         sed -n '3,17p' "$0" ;;
esac
