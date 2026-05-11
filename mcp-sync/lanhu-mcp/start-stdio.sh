#!/bin/bash
# 启动蓝湖 MCP 服务器（stdio transport，用于无法访问 localhost 的环境，例如某些沙盒/IDE）
set -euo pipefail

cd "$(dirname "$0")"

# Ensure virtualenv exists (install deps on first run).
if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Creating .venv and installing dependencies..."
  python3 -m venv .venv
  if ! .venv/bin/pip install -r requirements.txt; then
    echo "Installing core dependencies without htmlmin (optional on Python 3.14+)..."
    .venv/bin/pip install fastmcp httpx beautifulsoup4 playwright lxml python-dotenv
  fi
fi

source .venv/bin/activate

# Load env config if present (LANHU_COOKIE / SERVER_* etc.)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec python lanhu_mcp_server.py --transport stdio
