#!/usr/bin/env bash
# Config fuer dev-ports.sh (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fuers IDE-Highlighting. Format-Doku: ProjectTools/README.md
# Anlegen/aktualisieren:  dev-ports.sh --example > .dev-ports.conf.sh
# shellcheck disable=SC2034  # von dev-ports.sh gesourct

# Ports, die `make dev-up` oeffnet: Dashboard (Vite) und Backend (uvicorn).
PORTS=(5173 8000)
