# Universal RAG Gateway Architecture

This note turns the pasted V2.0 idea into a repository-level design target. It is intentionally implementation-oriented, but it is not yet a claim that the components below already exist in this repo.

## Goal

Build a local or private-cloud gateway that lets multiple IDEs, model providers, and agent runtimes share the same long-term memory, retrieval, and declarative tool layer.

The key boundary is:

```text
IDE / agent client / model runtime
        |
        | OpenAI-compatible API, Anthropic-compatible API, MCP, or direct REST
        v
Universal RAG Gateway
        |
        | retrieval, memory, tool registry, policy, telemetry
        v
Qdrant / PostgreSQL / Redis / model provider APIs / internal services
```

This should reduce lock-in to one client or one model family. It should not require every host to implement the same protocol natively.

## Corrections To The Raw Proposal

The attached proposal has the right direction, but several claims should be treated as design assumptions rather than facts:

- "Open MCP" is not a sufficient product boundary by itself. Use an adapter layer with explicit protocol modules: MCP, OpenAI-compatible chat completions or responses, Anthropic-compatible messages, and plain REST.
- Prompt-cache savings are provider-specific and input-order-sensitive. The gateway can optimize for stable prefixes, but it must measure cache hit rate instead of assuming a fixed 90% saving.
- Tool calling behavior varies by model and host. The gateway must support tool-choice policies, model-specific schema simplification, and text fallback, rather than assuming every model reliably calls JSON tools.
- "Perfect support" across Cursor, VS Code extensions, hosted models, and local models is too strong. Treat each client as a tested integration profile with its own compatibility matrix.
- Self-learning tools must not generate executable code by default. New capabilities should start as declarative specs reviewed, tested, and permission-scoped before activation.

## Architecture

```text
Clients
  Cursor, VS Code extensions, Codex, Claude Code, local scripts
        |
Protocol adapters
  OpenAI-compatible / Anthropic-compatible / MCP / REST
        |
Gateway core
  request normalization
  tenant and project policy
  context budget planner
  retrieval router
  tool registry and injection
  provider routing
  observability
        |
Fast loop
  hybrid search
  context compression
  declarative tool execution
        |
Slow loop
  transcript mining
  pattern extraction
  candidate tool generation
  offline tests and approval
        |
Storage and services
  PostgreSQL, Qdrant, Redis or queue backend, object storage, provider APIs
```

## Core Components

### Protocol Adapters

Each adapter should translate client-specific requests into a normalized internal request:

```ts
type GatewayRequest = {
  tenantId: string
  projectId?: string
  client: "cursor" | "vscode" | "codex" | "claude-code" | "script" | "unknown"
  protocol: "openai-compatible" | "anthropic-compatible" | "mcp" | "rest"
  model: string
  messages: NormalizedMessage[]
  tools?: NormalizedTool[]
  budget?: ContextBudget
  metadata: Record<string, unknown>
}
```

Adapter responsibilities:

- Authenticate the caller.
- Normalize messages, tools, images, files, and streaming events.
- Preserve the original request for fallback pass-through.
- Map gateway tool results back into the client's expected wire format.

### Context Budget Planner

The planner allocates the prompt budget before retrieval:

| Workload | Default intent | Retrieval budget |
| --- | --- | --- |
| coding edit | preserve current task and nearby code | small, high precision |
| debug or root cause | preserve logs, reproduction, recent changes | medium |
| design or migration | preserve decisions, constraints, prior proposals | medium to large |
| question answering | preserve source snippets and citations | medium |

The planner should emit an auditable budget decision:

```json
{
  "intent": "debug",
  "max_context_tokens": 24000,
  "static_prefix_tokens": 4000,
  "rag_tokens": 8000,
  "recent_history_tokens": 6000,
  "tool_schema_tokens": 3000,
  "reserve_tokens": 3000
}
```

### Hybrid Retrieval

Use two retrieval paths in parallel:

- Qdrant for semantic search over message chunks, summaries, code notes, and skill usage records.
- PostgreSQL for structured facts: project, branch, file, task, decision, tool, user preference, and entity relationships.

Initial schema direction:

```text
conversation(id, tenant_id, project_id, client, started_at)
message(id, conversation_id, role, content, token_count, created_at)
memory_chunk(id, tenant_id, project_id, source_message_id, text, kind, created_at)
entity(id, tenant_id, project_id, type, name, properties)
entity_edge(id, tenant_id, project_id, from_entity_id, to_entity_id, relation)
tool_spec(id, tenant_id, project_id, name, status, schema_json, executor_json, created_at)
tool_run(id, tool_spec_id, conversation_id, args_json, result_json, status, created_at)
```

### Prompt Assembly

Prefer stable ordering for cacheability, but do not depend on cache behavior for correctness:

```text
1. Gateway system policy
2. Stable project policy and active tool schemas
3. Retrieved memory, sorted by relevance and source quality
4. Recent conversation, newest last
5. Current user request
```

Cache-sensitive providers can reuse the stable prefix. Providers without prompt caching should still get the same semantic payload.

### Declarative Tool Runtime

Self-learned tools should be data, not arbitrary code. A tool spec has three parts:

```json
{
  "name": "query_project_deploy_status",
  "description": "Query production deployment status for one project.",
  "input_schema": {
    "type": "object",
    "properties": {
      "app_id": { "type": "string" }
    },
    "required": ["app_id"]
  },
  "executor": {
    "type": "http_request",
    "method": "GET",
    "url": "https://api.internal.example/deploy/status",
    "headers": {
      "Authorization": "Bearer {{env.DEPLOY_STATUS_TOKEN}}"
    },
    "query": {
      "app_id": "{{args.app_id}}"
    }
  }
}
```

Supported executor types should start small:

- `http_request` with allowlisted hosts, methods, headers, and timeouts.
- `sql_query` with read-only connections, parameterized queries, and row limits.
- `mcp_call` with allowlisted server and method names.
- `static_template` for deterministic snippets or checklists.

Do not add shell execution to the self-learning path unless it is separately permissioned, audited, and isolated.

### Slow Loop

The reflection worker should produce candidate improvements, not directly mutate production behavior.

Flow:

1. Select transcript windows with high repetition or manual tool-like actions.
2. Extract candidate skill or tool patterns.
3. Generate a declarative `tool_spec` or memory rule.
4. Run offline replay tests against historical examples.
5. Store as `candidate`.
6. Promote to `active` only after approval or a policy-defined automated gate.

Promotion gates:

- Input schema validates.
- Executor is within the allowlist.
- Tests cover at least one positive and one negative example.
- Secrets are referenced by environment name, never stored in the spec.
- Rollback is one database status change.

## Failure Modes

The gateway should degrade by capability, not by availability:

| Failure | Behavior |
| --- | --- |
| Qdrant unavailable | skip semantic memory, keep structured facts and pass-through |
| PostgreSQL unavailable | skip persistent memory and tools, pass through original request |
| compression service unavailable | use uncompressed top-k snippets with stricter token cap |
| provider unavailable | route to configured fallback provider if allowed |
| tool execution denied | return denial as tool result, let model continue |
| schema injection too large | rank tools and inject only the smallest useful subset |

Every degradation should emit telemetry, because silent fallback can hide that the memory layer is not working.

## MVP Scope

The first implementation should be deliberately narrow:

1. ✅ **Fastify gateway with one OpenAI-compatible endpoint** — [`gateway/`](../gateway/) 目录，Fastify 5 + OpenAI SDK，支持 `stream: true/false`，SSE 输出。[/v1/chat/completions](../gateway/src/routes/chat.ts) + [/health](../gateway/src/index.ts#L25-L28) + [/v1/models](../gateway/src/routes/chat.ts#L181-L194)。
2. ✅ **Multi-provider request routing** — [`types.ts`](../gateway/src/types.ts) 定义了 `GatewayRequest`、`NormalizedMessage`、`ContextBudget` 等内部类型；[`provider/`](../gateway/src/provider/) 模块实现了多 Provider 路由架构：
    - **[`types.ts`](../gateway/src/provider/types.ts)** — 定义了 `Provider` 接口（`chat` / `chatStreaming`），输入统一使用 `NormalizedMessage[]` / `NormalizedTool` / `ToolChoice`，所有 Provider 实现此接口。
    - **[`openai.ts`](../gateway/src/provider/openai.ts)** — `OpenAIProvider` 实现 Provider 接口，封装 OpenAI SDK 流式/非流式，内部将 Normalized 类型转换为 OpenAI SDK 类型。
    - **[`anthropic.ts`](../gateway/src/provider/anthropic.ts)** — `AnthropicProvider` 实现 Provider 接口，连接 Anthropic Messages API，包含完整的格式适配（system 提取、`tool` 角色 → `tool_result` 转换、`tool_calls` → `tool_use` 转换、`stop_reason` 映射、`@anthropic-ai/sdk` 流式事件包装为 AsyncGenerator）。
    - **[`router.ts`](../gateway/src/provider/router.ts)** — `ProviderRouter` 自身实现 `Provider` 接口（委托模式），根据模型名前缀路由：`claude-*` → Anthropic，其余 → OpenAI；Anthropic 调用失败时自动 fallback 到 OpenAI；支持请求级 `X-Provider` 头部覆盖路由。
    - 配置：`.env` 中 `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` 可选设置，未配置时只注册 OpenAIProvider。
3. ✅ **PostgreSQL transcript storage** — [`db/`](../gateway/src/db/) 模块，启动时自动建表（conversation + message），每次请求结束后 fire-and-forget 保存 transcript，DB 不可用时降级跳过。
4. ✅ **Qdrant semantic memory for message chunks** — [`vector/`](../gateway/src/vector/) 模块：[`embedding.ts`](../gateway/src/vector/embedding.ts) 用同上游 provider 的 `bge-m3` 模型生成 256 维向量；[`qdrant.ts`](../gateway/src/vector/qdrant.ts) 基于原生 fetch 的 REST 客户端（集合创建 / upsert / search）；[`store.ts`](../gateway/src/vector/store.ts) 在消息后自动 chunk 并索引。启动时 index.ts 初始化 Qdrant 连接并创建集合，chat route 中在响应后 fire-and-forget 索引本次对话内容，下次相似请求自动注入相关记忆到 system message。
5. ✅ **Static declarative tool registry loaded from JSON** — [`tool/`](../gateway/src/tool/) 模块：[`types.ts`](../gateway/src/tool/types.ts) 定义 `ToolSpec` 和 `HttpRequestExecutor` / `StaticTemplateExecutor` 等类型；[`registry.ts`](../gateway/src/tool/registry.ts) 从 `tools.json` 加载并按模型+状态过滤；[`executor.ts`](../gateway/src/tool/executor.ts) 支持声明式执行（HTTP 请求带 allowlist+超时、静态模板带 `{{args}}`/`{{env}}` 替换）。示例工具见 [`tools.json`](../gateway/tools.json)（当前包含：`get_current_time`、`lookup_http_status`、`get_definition`）。
6. ✅ **Tool injection with per-model compatibility flags** — [`types.ts`](../gateway/src/tool/types.ts) 新增 `toolChoicePolicy` / `schemaSimplifyFor` / `disableForModels`；[`registry.ts`](../gateway/src/tool/registry.ts) 新增 `resolveToolChoicePolicy()` / `shouldInjectTool()`，支持 glob 模式匹配；新增 [`simplify.ts`](../gateway/src/tool/simplify.ts) 实现按模型阶段简化 schema；[`chat.ts`](../gateway/src/routes/chat.ts) 集成去重合并、per-model tool_choice 链式解析（client→policy→auto→undefined）、模型/工具数量上限。
7. ✅ **Observability** — 新增 [`telemetry.ts`](../gateway/src/telemetry.ts) 集中管理遥测工厂/降级追踪/结构化 LogEmitter；新增 [`metrics.ts`](../gateway/src/metrics.ts) 提供进程内内存指标采集 + `GET /metrics` JSON 端点（请求计数、延迟直方图、工具调用统计、检索命中、降级事件）；[`index.ts`](../gateway/src/index.ts) 全局使用 Fastify/pino logger；每次请求结束后通过 `emitTelemetry()` 输出结构化遥测日志；provider 错误、数据库/Qdrant 不可用时自动记录降级原因。
8. ✅ **Full MCP server implementation** — 双向 MCP 支持：
    - **出站（outbound `mcp_call`）** — [`mcp/config.ts`](../gateway/src/mcp/config.ts) 定义 `McpServerConfig` 并加载 `mcp/servers.json`（支持 command+args 和 url+headers 两种模式）；[`mcp/client.ts`](../gateway/src/mcp/client.ts) `McpClientManager` 管理生命周期，通过 `StdioClientTransport` / `SSEClientTransport` 连接外部 MCP 服务器并缓存工具列表；[`executor.ts`](../gateway/src/tool/executor.ts) 实现 `mcp_call` case，合并 args 与 executor 默认值，调用 `client.callTool()` 并解析返回的 `ContentBlock[]`；启动时自动连接 8 个已配置 MCP 服务器（成功 5 个，降级 3 个），连接失败通过 `metricsCollector` 记录降级事件。
    - **入站（inbound protocol adapter）** — [`mcp/server.ts`](../gateway/src/mcp/server.ts) 在 Fastify 上注册 `GET /mcp/sse`（建立 SSE 流）和 `POST /mcp/message?sessionId=xxx`（接收 JSON-RPC 消息），通过 `SSEServerTransport` 暴露 `tools/list` 和 `tools/call` 端点，将所有 `ToolRegistry` 中的工具以 MCP 格式暴露给 MCP 原生客户端（Cursor、VS Code 等）。
9. ✅ **Context Budget Planner with intent-based allocation** — [`planner/`](../gateway/src/planner/) 模块，在每次请求的处理管线第一步执行：
    - **[`intent.ts`](../gateway/src/planner/intent.ts)** — 基于关键词/模式匹配的意图检测器，从最后一条用户消息推断请求类型（`coding-edit` / `debug` / `design` / `qa` / `unknown`），按模式命中数量输出 `high / medium / low` 置信度。无第三方依赖，支持后续升级为 ML 分类器。
    - **[`budget.ts`](../gateway/src/planner/budget.ts)** — `BudgetPlanner` 类根据意图查找 token 分配 profile（详见下方 profile 表），并根据消息长度和数量动态调整；输出可审计的 `BudgetDecision`（含意图标签、置信度、调整原因、原始 profile）。
    - **下游约束函数**（同一文件导出）：`computeRetrievalConstraints()` 将 `ragTokens` 转为 `maxResults` + `scoreThreshold`；`computeToolBudgetLimit()` 将 `toolSchemaTokens` 转为最大工具注入数（~300 tokens/tool 估算）；`computeOutputBudget()` 从 `reserveTokens` 推导 provider `max_tokens`；`computeMessageTrimBudget()` 将 `recentHistoryTokens` 转为消息保留长度。
    - **集成到 [`chat.ts`](../gateway/src/routes/chat.ts)**：Step 0 执行 `planner.plan()` → 预算决策写入 telemetry + debug 日志；Step 1 用 `computeRetrievalConstraints` 约束检索（动态 top-k + score 阈值过滤）；Step 2 用 `toolBudgetLimit` 与模型上限取 min 裁剪工具列表；Step 3 用 `computeMessageTrimBudget` 从尾部裁剪消息历史、用 `computeOutputBudget` 设置 provider `max_tokens`。所有 constraint 变更均通过 `request.log.debug` 输出，支持运行时诊断。

    | Profile | maxContext | staticPrefix | rag | history | tools |
    |---|---|---|---|---|---|
    | coding-edit | 16K | 4K | 2K (0.65) | 6K | 2K |
    | debug | 24K | 4K | 8K (0.55) | 6K | 3K |
    | design | 32K | 6K | 12K (0.35) | 8K | 3K |
    | qa | 20K | 4K | 6K (0.45) | 5K | 3K |
    | unknown | 16K | 4K | 4K (0.55) | 5K | 2K |

    rag 列括号内为对应 `scoreThreshold`，小预算选更严格的阈值。

10. ✅ **GraphRAG — Entity-Relationship Memory** — [`entity/`](../gateway/src/entity/) + [`db/graph.ts`](../gateway/src/db/graph.ts) 模块，在 Qdrant 语义搜索之上，使用 PostgreSQL entity/entity_edge 表存储结构化关系图：
    - **[`db/graph.ts`](../gateway/src/db/graph.ts)** — PostgreSQL CRUD：`upsertEntities()` 基于唯一索引 `(name, tenant_id)` 去重合并，`insertEdges()` 批量写入，`searchEntities()` 对用户查询做 token 化 ILIKE 匹配（过滤停用词），`getSubgraph()` 做 1-2 hop 图遍历（应用层循环查询），`getEntitiesByType()` 按类型过滤。
    - **[`entity/extractor.ts`](../gateway/src/entity/extractor.ts)** — `EntityExtractor` 类，复用同一 `OpenAI` 客户端（`openaiApiKey` / `openaiBaseUrl`），使用 `response_format: { type: "json_object" }` + `temperature: 0.1` 做结构化实体/关系提取。预定义实体类型池（`project` / `api` / `service` / `database` / `technology` / `decision` 等）和关系类型池（`uses` / `depends_on` / `implements` / `references` 等）。
    - **[`entity/store.ts`](../gateway/src/entity/store.ts)** — `EntityStore` 编排器：`extractAndStore()` 在每次响应后 fire-and-forget 调用 LLM 提取 → 批量 upsert entities → insert edges；`searchGraph()` 在 Step 2 检索中并行查询实体子图；`formatContext()` 将结果格式化为 `[entity-relationship] "A" —[uses]→ "B"` 注入 system prompt。
    - **集成到 [`chat.ts`](../gateway/src/routes/chat.ts)**：Step 2 在图检索后合并 Qdrant + Graph 上下文；Step 3 统一注入；响应后在 `indexToQdrant()` 之后 fire-and-forget 调用 `extractAndStore()`。
    - **配置与降级**：环境变量 `GRAPH_RAG_ENABLED=true` 启用；需要 `DATABASE_URL` 存在 + 配置标志；DB 不可用或提取失败时记录 `"entity-extraction"` 降级事件，chat 请求不受影响。
    - **指标**：`/metrics` 端点新增 `entitiesExtractedTotal` 计数器。

11. ✅ **Multi-level tenant → project isolation** — 2025-06 将全链路 `"default"` 硬编码重构为真正的多级隔离结构：

    **隔离层级：**
    ```text
    tenant (组织/团队) ─── 安全墙，所有搜索按 tenant 强制过滤
        └── project (代码库/产品) ─── 可选搜索范围，不传则跨 project 搜索
    ```

    **存储层：**
    - Qdrant 单 collection `memory_chunks` + payload 字段 `tenantId` / `projectId` / `conversationId`
    - 已创建 **payload indexes**（`tenantId` + `projectId`），确保 Qdrant 走 **pre-filter** 模式（先过滤出 tenant 子集再 ANN 搜索，非 post-filter）
    - PG `conversation`, `entity`, `entity_edge` 表均有 `tenant_id` / `project_id` 列 + 复合索引 `(tenant_id, project_id)`

    **请求入口 ([`ChatCompletionRequest`](../gateway/src/routes/chat.ts#L133))：**
    ```typescript
    interface ChatCompletionRequest {
        // ... 原有字段
        tenant_id?: string;   // 组织/团队，不传 fallback "default"（向后兼容）
        project_id?: string;  // 代码库/产品，可选
    }
    ```

    **搜索隔离逻辑：**
    | 组件 | tenantId | projectId |
    |------|----------|-----------|
    | Qdrant vector search | ✅ 必选过滤 | ✅ 可选过滤 |
    | GraphRAG `searchEntities` | ✅ 必选过滤 | ✅ 可选过滤（缩小初始匹配范围） |
    | GraphRAG 2-hop 子图遍历 | ✅ 必选过滤 | ❌ 跨 project（实体关系本身就是跨项目的知识连接） |
    | PG transcript | ✅ 携带写入 | ✅ 携带写入 |

    **调用链（以 streaming 路径为例）：**
    ```text
    POST body.tenant_id, body.project_id
      → storeTranscript({ tenantId, projectId, ... })       // PG 存储
      → vectorStore.search(query, { tenantId, projectId })  // Qdrant 搜索
      → entityStore.searchGraph(query, tenantId, { projectId }) // GraphRAG
      → indexToQdrant(..., tenantId, projectId)             // Qdrant 索引
      → entityStore.extractAndStore(..., tenantId, projectId) // 实体抽取存储
    ```

    **硬编码移除：** 10 处 `"default"` 全部替换为运行时参数传递（入口保留 `?? "default"` 向后兼容 fallback）。涉及文件：[qdrant.ts](../gateway/src/vector/qdrant.ts) / [store.ts](../gateway/src/vector/store.ts) / [graph.ts](../gateway/src/db/graph.ts) / [store.ts](../gateway/src/entity/store.ts) / [index.ts](../gateway/src/db/index.ts) / [index.ts](../gateway/src/index.ts) / [chat.ts](../gateway/src/routes/chat.ts)。

Defer these until the MVP is stable:

- Automated candidate tool promotion.
- LLM-Lingua or local compression service.
- ~~Multi-provider cost optimizer.~~ ✅ **Multi-provider request routing** — 已实现 `ProviderRouter` 根据模型名前缀自动路由，支持 Anthropic / OpenAI-compatible 后端切换，含 Anthropic 失败 fallback 链。成本优化（权重/成本感知路由）仍为 defer 项。

## Acceptance Criteria

The gateway is useful only if these can be demonstrated:

- ✅ [已验证] A client can send an OpenAI-compatible request through the gateway and receive a streamed model response.
- ✅ [已验证] The gateway stores the transcript in PostgreSQL (fire-and-forget, DB unavailable → graceful degradation with telemetry).
- ✅ [已验证] Semantic memory via Qdrant: previous messages are indexed as vector chunks, and relevant memories are retrieved and injected as context in subsequent requests.
- ✅ [已验证] Context Budget Planner: intent-based token allocation profiles are applied on every request, producing auditable BudgetDecision; retrieval results, tool injection count, message history, and provider max_tokens are all constrained by the budget — each with debug-log visibility.
- The gateway stores the transcript and retrieves a relevant prior memory in a later request.
- ✅ [已验证] Tool schemas are injected only when policy and budget allow. The model calls the tool and the result is fed back in a second roundtrip.
- ✅ [已验证] GraphRAG entity extraction: after a chat response, entities and relationships are extracted via LLM, stored in PostgreSQL entity/entity_edge tables, and persisted across conversations.
- ✅ [已验证] Graph-enhanced retrieval: a follow-up query matching stored entity names triggers subgraph traversal; structured `[entity-relationship]` context is injected alongside Qdrant chunks, enabling the model to answer cross-conversation relation questions ("What APIs does MyApp use?").
- ✅ [已验证] Multi-provider routing: model name `claude-*` routes to AnthropicProvider (if `ANTHROPIC_API_KEY` set) or falls back to OpenAIProvider; `gpt-*`/`deepseek-*` routes to OpenAIProvider; `X-Provider` header allows per-request override.
- A declarative HTTP tool can run with mocked credentials in tests.
- If Qdrant is stopped, the same request still reaches the provider and telemetry records the fallback.
- Cache hit rate, retrieval latency, and tool-call success rate are measured rather than assumed.

## Relationship To This Repository

This repo already solves adjacent distribution problems:

- `mcp/` keeps MCP server configuration as a local single source of truth.
- `sync/` propagates MCP and Codex/Claude shared configuration across clients.
- `skills-engineering/` keeps agent behavior rules synchronized across runtimes.

The universal gateway would be a new subsystem, not a replacement for those pieces. The clean integration point is:

- keep `mcp/servers.json` as a source for gateway MCP upstream definitions;
- keep skills as policy inputs or retrieval documents;
- add the gateway as a separate top-level package only after the MVP contract above is accepted.
