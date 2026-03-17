#!/bin/bash
# Start the LangGraph dev server for LangSmith Studio. Ctrl+C to stop.
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    echo "No .venv found. Run ./scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate
pip install "langgraph-cli[inmem]" -q 2>&1 | tail -1
langgraph dev
