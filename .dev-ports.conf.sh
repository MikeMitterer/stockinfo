#!/usr/bin/env bash
# Config fuer dev-ports.sh (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fuers IDE-Highlighting. Format-Doku: ProjectTools/README.md
# Anlegen/aktualisieren:  dev-ports.sh --example > .dev-ports.conf.sh
# shellcheck disable=SC2034  # von dev-ports.sh und vom Makefile gesourct

# Ports, die `make dev-up` oeffnet. Die Namen liest das Makefile (hints, dev-up),
# PORTS liest dev-ports.sh.
DASHBOARD_PORT=5173
BACKEND_PORT=8000
PORTS=("${DASHBOARD_PORT}" "${BACKEND_PORT}")
