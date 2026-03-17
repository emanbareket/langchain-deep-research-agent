#!/bin/bash
# Start the research agent UI locally. Ctrl+C to stop.
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    echo "No .venv found. Run ./scripts/setup.sh first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "No .env found. Copy .env.example to .env and add your API keys."
    exit 1
fi

source .venv/bin/activate
echo "→ http://127.0.0.1:8123"
python ui/server.py
