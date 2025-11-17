#!/bin/bash

echo "Starting crash suite..."

for exe in bin/*; do
    echo "--------------------------------------"
    echo "Running: $exe"
    "$exe" &
    sleep 1
    wait || true
    sleep 5
done

echo "Crash suite finished."
