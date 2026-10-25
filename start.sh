#!/bin/bash
# Starts the server on http://127.0.0.1:5050/ . Usage: ./start.sh [TIME_SCALE]   (e.g. ./start.sh 0.25)
cd "$(dirname "$0")"
if lsof -nP -iTCP:5050 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Something already listens on port 5050 (is the server already running? ./stop.sh stops it)."
    exit 1
fi
[ -n "$1" ] && export TIME_SCALE="$1"
exec .venv/bin/python -u server.py
