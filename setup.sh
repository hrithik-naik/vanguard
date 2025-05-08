#!/bin/bash
set -e  # Exit on any error

rm -rf .venv
python3 -m venv .venv
echo "Activating virtual environment..."
pwd

source .venv/bin/activate
cd .. 
echo "Installing dependencies..."
pip install -r requirments.txt

echo "Setup complete."