#!/usr/bin/env bash
# Config fuer dev-ports (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fuers IDE-Highlighting. Format-Doku: ProjectTools docs/tools/dev-ports.md,
# Abschnitt „Bestehende .dev-ports.conf.sh“. Von Hand pflegen; `dev-ports --example`
# gibt nur ein leeres PORTS=() aus und darf diese Datei nicht ersetzen.
# shellcheck disable=SC2034  # von dev-ports, Procfile.dev, Makefile und Skript gesourct

# Ports, die `make dev-up` oeffnet — die einzige Quelle dafuer. Die Namen lesen
# Procfile.dev (Backend, Vite, Proxy), dev-ports (NAME_PORT als Name, PORTS) und
# scripts/sources-profile.sh (Lebendabfrage lokal). Das Makefile (info, hints, dev-up)
# fragt dev-ports --port-of und liest die Datei nur ohne dev-ports selbst.
DASHBOARD_PORT=5173
BACKEND_PORT=8000
PORTS=("${DASHBOARD_PORT}" "${BACKEND_PORT}")
