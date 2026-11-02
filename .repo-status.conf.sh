#!/usr/bin/env bash
# Config fuer repo-status (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fuers IDE-Highlighting. Format-Doku: ProjectTools/README.md
# Anlegen/aktualisieren:  repo-status --example > .repo-status.conf.sh
# shellcheck disable=SC2034  # von repo-status gesourct

# Optional: GitHub-Repo fuer die Issue-Sektion (blocker/high-priority)
ISSUES_REPO="MikeMitterer/stockinfo"

# Workspace-Repos: "<pfad>:<anzeigename>" (Split am ersten ':')
REPOS=(
    ".:StockInfo (Root)"
)
