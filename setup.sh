#!/bin/bash
# One-time setup: creates the Python virtual environment and installs the (two) dependencies.
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "python3 is required (https://www.python.org/downloads/)"; exit 1; }
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "Done. Start the game with ./start.sh, or build the app with ./tools/make_app.sh"
