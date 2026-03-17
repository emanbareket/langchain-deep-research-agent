#!/bin/bash
# Bootstrap the local environment and start the research agent UI. Ctrl+C to stop.
set -e
cd "$(dirname "$0")/.."

has_env_var() {
    local var_name="$1"
    [ -f .env ] && grep -q "^${var_name}=.\+" .env
}

require_env_var() {
    local var_name="$1"
    local prompt_text="$2"
    local secret_value=""

    if has_env_var "$var_name"; then
        return
    fi

    while [ -z "$secret_value" ]; do
        echo ""
        read -rsp "$prompt_text: " secret_value
        echo ""
        if [ -z "$secret_value" ]; then
            echo "$var_name cannot be empty."
        fi
    done

    if [ ! -f .env ]; then
        touch .env
    fi

    if grep -q "^${var_name}=" .env 2>/dev/null; then
        python3 - "$var_name" "$secret_value" <<'PY'
from pathlib import Path
import sys

key = sys.argv[1]
value = sys.argv[2]
env_path = Path(".env")
lines = env_path.read_text().splitlines() if env_path.exists() else []
updated = []
replaced = False
for line in lines:
    if line.startswith(f"{key}="):
        updated.append(f"{key}={value}")
        replaced = True
    else:
        updated.append(line)
if not replaced:
    updated.append(f"{key}={value}")
env_path.write_text("\n".join(updated) + "\n")
PY
    else
        echo "${var_name}=${secret_value}" >> .env
    fi
}

echo "Bootstrapping Deep Research Agent..."

if [ ! -d .venv ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
python -m pip install -e .

if has_env_var "OPENAI_API_KEY" && has_env_var "TAVILY_API_KEY"; then
    echo "Found existing .env with required API keys."
else
    require_env_var "OPENAI_API_KEY" "Enter your OpenAI API key"
    require_env_var "TAVILY_API_KEY" "Enter your Tavily API key"
fi

echo ""
echo "Starting Deep Research Agent UI:"
echo "→ http://127.0.0.1:8123"
python ui/server.py
