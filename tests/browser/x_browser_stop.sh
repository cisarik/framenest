#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
B="$ROOT/.x-browser-tmp"
if [ -f "$B/run/server.pid" ]; then kill "$(cat "$B/run/server.pid")" 2>/dev/null; fi
exit 0
