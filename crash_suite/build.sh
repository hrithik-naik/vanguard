#!/bin/bash

set -e

# Resolve directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_DIR="$SCRIPT_DIR/tests"
BIN_DIR="$SCRIPT_DIR/bin"

mkdir -p "$BIN_DIR"

echo "Building crash suite from: $TEST_DIR"
echo "Output directory: $BIN_DIR"
echo

for f in "$TEST_DIR"/*.c; do
    name=$(basename "$f" .c)
    echo "Compiling: $name"

    gcc -g -pthread "$f" -o "$BIN_DIR/$name" || {
        echo "Failed to build $name"
        exit 1
    }
done

echo
echo "Build complete. Binaries available in: $BIN_DIR"
