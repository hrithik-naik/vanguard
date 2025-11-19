#!/bin/bash

# Resolve the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"

echo "=== Crash Suite Execution ==="

for exe in "$BIN_DIR"/*; do
    echo "--------------------------------------"
    echo "Running: $exe"

    "$exe" &
    PID=$!

    sleep 3

    if ps -p $PID > /dev/null; then
        echo "Process still running → killing PID $PID"
        kill -9 $PID
    else
        echo "Process exited or crashed."
    fi

    sleep 2
done

echo "=== Crash Suite Finished ==="
