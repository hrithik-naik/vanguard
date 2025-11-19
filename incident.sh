#!/bin/bash
set -e

cd "$(dirname "$0")" || exit

source build/.venv/bin/activate

python3 selfhealing/selfhealing.py &
echo $! > /tmp/vanguard_incident.pid
