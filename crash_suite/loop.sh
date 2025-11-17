#!/bin/bash

echo "🔥 Chaos mode enabled — looping crash tests..."

while true; do
    exe=$(ls bin/* | shuf -n 1)
    echo "Running: $exe"
    "$exe" &
    sleep 1
    wait || true
    sleep 5
done
