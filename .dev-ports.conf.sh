#!/usr/bin/env bash
# Config für dev-ports (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fürs IDE-Highlighting. Format-Doku: ProjectTools docs/tools/dev-ports.md
# Von Hand gepflegt: `dev-ports --example` kennt die Namen darunter nicht, die
# Procfile.dev braucht; die Ausgabe nicht über diese Datei schreiben.
# shellcheck disable=SC2034  # von dev-ports, Procfile.dev, Makefile und Skript gesourct

# Ports, die `make dev-up` öffnet — die einzige Quelle dafür. Die Namen lesen
# Procfile.dev (Backend, Vite, Proxy), das Makefile (hints, dev-up, info) und
# scripts/sources-profile.sh (Lebendabfrage lokal); PORTS liest dev-ports.
DASHBOARD_PORT=5173
BACKEND_PORT=8000
PORTS=("${DASHBOARD_PORT}" "${BACKEND_PORT}")
