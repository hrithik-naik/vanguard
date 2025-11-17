#!/bin/bash

cd "$(dirname "$0")" || exit

if [ ! -d "build/.venv" ]; then
    echo "Virtual environment missing: build/.venv"
    exit 1
fi

source build/.venv/bin/activate

if [ ! -f "selfhealing/selfhealing.py" ]; then
    echo "Entry script not found: selfhealing/selfhealing.py"
    exit 1
fi

python3 selfhealing/selfhealing.py
