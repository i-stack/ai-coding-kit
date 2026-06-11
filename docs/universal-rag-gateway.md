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

1. Fastify gateway with one OpenAI-compatible endpoint.
2. Request normalization and pass-through to one configured provider.
3. PostgreSQL transcript storage.
4. Qdrant semantic memory for message chunks.
5. Static declarative tool registry loaded from PostgreSQL or local JSON.
6. Tool injection with per-model compatibility flags.
7. Observability: request id, retrieval hits, injected tools, fallback reason, provider latency.

Defer these until the MVP is stable:

- GraphRAG beyond simple relational edges.
- Automated candidate tool promotion.
- LLM-Lingua or local compression service.
- Multi-provider cost optimizer.
- Full MCP server implementation.

## Acceptance Criteria

The gateway is useful only if these can be demonstrated:

- A client can send an OpenAI-compatible request through the gateway and receive a streamed model response.
- The gateway stores the transcript and retrieves a relevant prior memory in a later request.
- Tool schemas are injected only when policy and budget allow.
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
