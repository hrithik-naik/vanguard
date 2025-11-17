#!/bin/bash

set -e

mkdir -p bin

for f in tests/*.c; do
    name=$(basename "$f" .c)
    echo "Compiling $name..."
    gcc -g -pthread "$f" -o "bin/$name"
done

echo "Build complete. Binaries in ./bin/"
