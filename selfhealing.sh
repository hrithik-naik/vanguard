#!/bin/bash
set -e

source build/.venv/bin/activate

# run AI service and store its PID
python3 selfhealing/ai_service.py &
echo $! > /tmp/vanguard_heal.pid
