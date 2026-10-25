#!/bin/bash
# Stops the server started with ./start.sh
PID=$(lsof -nP -iTCP:5050 -sTCP:LISTEN -t 2>/dev/null)
if [ -z "$PID" ]; then echo "The server is not running."; exit 0; fi
kill $PID && echo "Server stopped (PID $PID)."
