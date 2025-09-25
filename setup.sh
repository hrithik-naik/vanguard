#!/bin/bash
set -e  # Exit on any error

# rm -rf .venv
# python3 -m venv .venv
echo "Activating virtual environment..."
pwd

source .venv/bin/activate
cd .. 
echo "Installing dependencies..."
#sudo apt-get update && sudo apt-get install -y llvm-17 clang-17
pip install -r requirments.txt
python -c "import tensorflow as tf; print('importing'); import tensorflow as tf"

echo "Setup complete."