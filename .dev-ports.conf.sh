#!/usr/bin/env bash
# Config fuer dev-ports.sh (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fuers IDE-Highlighting. Format-Doku: ProjectTools/README.md
# Anlegen/aktualisieren:  dev-ports.sh --example > .dev-ports.conf.sh
# shellcheck disable=SC2034  # von dev-ports.sh, Procfile.dev, Makefile und Skript gesourct

# Ports, die `make dev-up` oeffnet — die einzige Quelle dafuer. Die Namen lesen
# Procfile.dev (Backend, Vite, Proxy), das Makefile (hints, dev-up, info) und
# scripts/sources-profile.sh (Lebendabfrage lokal); PORTS liest dev-ports.sh.
DASHBOARD_PORT=5173
BACKEND_PORT=8000
PORTS=("${DASHBOARD_PORT}" "${BACKEND_PORT}")
