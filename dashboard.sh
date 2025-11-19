#!/bin/bash
set -e

source build/.venv/bin/activate

# run dashboard and store its PID
python3 selfhealing/dashboard.py &
echo $! > /tmp/vanguard_dashboard.pid
