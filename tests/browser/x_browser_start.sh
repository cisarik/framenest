#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
B="$ROOT/.x-browser-tmp"
ARGS=("$@")
mkdir -p "$B/run"
rm -rf "$B/db" "$B/fixtures" "$B/staging" "$B/quarantine" "$B/publish"
mkdir -p "$B/run" "$B/db" "$B/fixtures" "$B/staging" "$B/quarantine" "$B/publish"
setsid "$ROOT/.venv/bin/python" -u "$ROOT/tests/browser/x_browser_server.py" "$B/db/catalog.sqlite3" "$B/fixtures" "$B/staging" "$B/quarantine" "$B/publish" "${ARGS[@]}" > "$B/run/server.log" 2>&1 < /dev/null &
echo $! > "$B/run/server.pid"
exit 0
