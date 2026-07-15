#!/bin/sh
#------------------------------------------------------------------------------
# entrypoint.sh — Startet die App als non-root User 'stockinfo' (UID 99)
#
# Läuft kurz als root, um /data (Volume/Bind-Mount) dem App-User zu übergeben —
# bestehende Volumes älterer (root-)Installationen bleiben so schreibbar.
# Danach werden die Privilegien via setpriv dauerhaft abgegeben.
#------------------------------------------------------------------------------
set -e

chown -R stockinfo:users /data 2>/dev/null || true

exec setpriv --reuid stockinfo --regid users --init-groups "$@"
