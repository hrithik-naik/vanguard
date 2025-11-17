#!/bin/bash

INCIDENT_FILE="data/incidents.json"

echo "🧹 Resetting incidents..."

# Create folder if missing
mkdir -p "$(dirname "$INCIDENT_FILE")"

# Overwrite file with empty JSON object
echo "{}" > "$INCIDENT_FILE"

# Fix permissions (optional but useful if AI writes to it)
chmod 666 "$INCIDENT_FILE"

echo "✅ incidents.json has been cleared and reset."
echo "📁 Path: $INCIDENT_FILE"
cat "$INCIDENT_FILE"
