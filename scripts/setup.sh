#!/bin/bash
# One-time setup: create venv, install deps, create .env from template.
set -e
cd "$(dirname "$0")/.."

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing dependencies..."
pip install -e . 2>&1 | tail -1

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env from template. Please add your API keys:"
    echo "  OPENAI_API_KEY=..."
    echo "  TAVILY_API_KEY=..."
    echo ""
    echo "Then run: ./scripts/start.sh"
else
    echo ""
    echo "Setup complete. Run: ./scripts/start.sh"
fi
