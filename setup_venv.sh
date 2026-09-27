#!/usr/bin/env bash
# Create (or update) the project's .venv and install requirements.
# Usage: ./setup_venv.sh   then: source .venv/bin/activate
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r requirements.txt

echo
echo "to run: source $VENV_DIR/bin/activate"
