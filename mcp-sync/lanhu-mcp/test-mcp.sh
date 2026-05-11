#!/bin/bash
# 测试蓝湖 MCP 服务是否可用
# 用法：先在一个终端启动服务 ./start.sh，再在另一个终端运行本脚本

set -e
MCP_URL="${MCP_URL:-http://localhost:8000/mcp}"

echo "=========================================="
echo "1. 检查 MCP 服务是否在运行..."
echo "=========================================="
# 能连上即可（GET 可能返回 405，也算服务在跑）
CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$MCP_URL" 2>/dev/null || echo "000")
if [ "$CODE" = "000" ]; then
    echo "❌ 无法连接到 $MCP_URL"
    echo "请先在另一个终端运行: cd $(dirname "$0") && ./start.sh"
    exit 1
fi
echo "✅ 端点可访问: $MCP_URL"
echo ""

echo "=========================================="
echo "2. 发送 MCP initialize 请求..."
echo "=========================================="
INIT_RESP=$(curl -s -i -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>/dev/null) || true

if echo "$INIT_RESP" | grep -q "Mcp-Session-Id"; then
    SESSION_ID=$(echo "$INIT_RESP" | grep -i "Mcp-Session-Id" | sed 's/.*: *//' | tr -d '\r')
    echo "✅ 初始化成功，Session ID: ${SESSION_ID:0:20}..."
else
    echo "⚠️ 未获取到 Mcp-Session-Id（部分 MCP 实现可能使用不同方式）"
    echo "若 Cursor 能连接并列出工具，则说明 MCP 正常。"
fi
echo ""

echo "=========================================="
echo "3. 在 Cursor 中验证"
echo "=========================================="
echo "在 Cursor 中："
echo "  1. 设置 → MCP → 添加 lanhu，URL: $MCP_URL?role=Developer&name=Test"
echo "  2. 在对话中尝试：\"列出蓝湖相关工具\" 或 \"用 lanhu 列出我的项目\""
echo ""
echo "✅ 若上述步骤无报错，说明 MCP 已可用。"
