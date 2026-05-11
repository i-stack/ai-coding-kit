#!/bin/bash
# 启动蓝湖 MCP 服务器（使用项目内 .venv）
cd "$(dirname "$0")"

# Load env config if present (LANHU_COOKIE / SERVER_* etc.)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Creating .venv and installing dependencies..."
  python3 -m venv .venv
  if ! .venv/bin/pip install -r requirements.txt; then
    echo "Installing core dependencies without htmlmin (optional on Python 3.14+)..."
    .venv/bin/pip install fastmcp httpx beautifulsoup4 playwright lxml python-dotenv
  fi
fi
source .venv/bin/activate
python lanhu_mcp_server.py
