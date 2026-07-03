# rag-gateway

基于 TypeScript / Fastify 的通用 RAG（检索增强生成）网关，提供 OpenAI 兼容 API，可作为本地 RAG 服务的自托管替代方案。

## 核心能力

- **OpenAI 兼容 API** — 标准 `/v1/chat/completions` 接口，可接入任何 OpenAI 客户端
- **语义记忆** — 基于 Qdrant 向量数据库的持久化对话记忆检索
- **GraphRAG** — 实体关系图，从对话中提取结构化知识
- **声明式工具系统** — 通过 `tools.json` 定义工具，无需编写代码即可扩展
- **MCP 接口** — 通过 SSE 暴露 `tools/list` 和 `tools/call`

## 快速开始

```bash
cd rag-gateway
cp .env.example .env
# 编辑 .env 填写 embedding API key / Qdrant URL 等
$EDITOR .env
npm install
npm run dev
```

## 目录结构

```text
rag-gateway/
├── src/
│   ├── index.ts          ← Fastify 服务器入口
│   ├── config.ts         ← 配置加载（.env + rag-gateway.json）
│   ├── db/               ← PostgreSQL 持久化（转录、图谱）
│   ├── vector/           ← Embedding + Qdrant 向量存储
│   ├── entity/           ← 实体关系提取
│   ├── tool/             ← 声明式工具注册与执行
│   ├── mcp/              ← MCP 服务器与客户端
│   └── metrics.ts        ← 指标收集
├── tests/                ← Vitest 单元/集成测试
├── scripts/              ← 调试和数据填充脚本
├── tools.json            ← 声明式工具定义
└── .env.example          ← 环境变量模板
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `GATEWAY_PORT` | 服务端口（默认 3000） |
| `EMBEDDING_API_KEY` | Embedding 服务 API Key |
| `EMBEDDING_BASE_URL` | Embedding 服务地址 |
| `EMBEDDING_MODEL` | Embedding 模型名称 |
| `EXTRACTION_LLM_API_KEY` | 实体提取用 LLM Key |
| `POSTGRES_URL` | PostgreSQL 连接串（可选） |
| `QDRANT_URL` | Qdrant 向量库地址（可选） |
| `GRAPHRAG_ENABLED` | 是否启用 GraphRAG（`true`/`false`） |

配置也可从 `env/platforms/rag-gateway.json` 自动加载默认值（`.env` 优先）。
