import type {
    NormalizedMessage,
    NormalizedTool,
    ToolChoice,
    ContextBudget,
    ExtractionResult,
    GraphEntity,
    GraphRelation,
    GatewayRequest,
    RequestTelemetry,
} from "../../src/types.js";
import type { ToolSpec, HttpRequestExecutor, StaticTemplateExecutor } from "../../src/tool/types.js";
import type { BudgetProfile, RetrievalConstraints } from "../../src/planner/budget.js";

// ── Messages ────────────────────────────────────────────────────────────

export const systemMessage: NormalizedMessage = {
    role: "system",
    content: "You are a helpful assistant.",
};

export const userMessage: NormalizedMessage = {
    role: "user",
    content: "Hello, how are you?",
};

export const assistantMessage: NormalizedMessage = {
    role: "assistant",
    content: "I'm doing well, thank you!",
};

export const toolResultMessage: NormalizedMessage = {
    role: "tool",
    content: '{"result": "success"}',
    tool_call_id: "call_123",
};

export const assistantWithToolCalls: NormalizedMessage = {
    role: "assistant",
    content: "Let me look that up...",
    tool_calls: [
        {
            id: "call_abc",
            type: "function",
            function: { name: "get_current_time", arguments: "{}" },
        },
    ],
};

export const multiParagraphMessage: NormalizedMessage = {
    role: "user",
    content: "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three, which is intentionally kept long to test chunking behavior at boundaries.",
};

export const contentPartMessage: NormalizedMessage = {
    role: "user",
    content: [
        { type: "text", text: "What's in this image?" },
        { type: "image_url", image_url: { url: "https://example.com/image.png", detail: "auto" } },
    ],
};

// ── Intent-focused messages ─────────────────────────────────────────────

export const debugMessage: NormalizedMessage = {
    role: "user",
    content: "I'm getting an error when I try to load the page. The stack trace shows a null pointer exception. Can you help me debug this?",
};

export const codingEditMessage: NormalizedMessage = {
    role: "user",
    content: "Please implement a new function that handles user authentication. I need to refactor the login module.",
};

export const designMessage: NormalizedMessage = {
    role: "user",
    content: "I'm designing a microservices architecture for our platform. Should we use event-driven or request-driven communication between services?",
};

export const qaMessage: NormalizedMessage = {
    role: "user",
    content: "What is the difference between SQL and NoSQL databases? Can you explain how indexing works?",
};

export const shortMessage: NormalizedMessage = {
    role: "user",
    content: "Hi",
};

export const longMessage: NormalizedMessage = {
    role: "user",
    content: "A".repeat(2500),
};

// ── Tool specs ──────────────────────────────────────────────────────────

export const httpToolSpec: ToolSpec = {
    name: "lookup_http_status",
    description: "Look up the meaning of an HTTP status code.",
    input_schema: {
        type: "object",
        properties: {
            code: { type: "string", description: "HTTP status code" },
        },
        required: ["code"],
    },
    executor: {
        type: "http_request",
        method: "GET",
        url: "https://httpbin.org/status/{{args.code}}",
        timeoutMs: 5000,
    } as HttpRequestExecutor,
};

export const templateToolSpec: ToolSpec = {
    name: "get_current_time",
    description: "Get the current date and time.",
    input_schema: {
        type: "object",
        properties: {},
        required: [],
    },
    executor: {
        type: "static_template",
        template: "Current time: {{env.NOW}}",
    } as StaticTemplateExecutor,
};

export const modelFilteredTool: ToolSpec = {
    name: "premium_analyzer",
    description: "Premium analysis tool for capable models only.",
    input_schema: {
        type: "object",
        properties: {
            data: { type: "string" },
        },
        required: ["data"],
    },
    executor: {
        type: "static_template",
        template: "Analysis: {{args.data}}",
    } as StaticTemplateExecutor,
    compatibleModels: ["claude-*", "gpt-4*"],
    disableForModels: ["gpt-3.5*"],
    schemaSimplifyFor: ["claude-3-haiku*"],
};

// ── Budget profiles ─────────────────────────────────────────────────────

export const budgetProfileDefaults: Record<string, BudgetProfile> = {
    "coding-edit": { maxContextTokens: 16000, staticPrefixTokens: 4000, ragTokens: 2000, recentHistoryTokens: 6000, toolSchemaTokens: 2000 },
    debug: { maxContextTokens: 24000, staticPrefixTokens: 4000, ragTokens: 8000, recentHistoryTokens: 6000, toolSchemaTokens: 3000 },
    design: { maxContextTokens: 32000, staticPrefixTokens: 6000, ragTokens: 12000, recentHistoryTokens: 8000, toolSchemaTokens: 3000 },
    qa: { maxContextTokens: 20000, staticPrefixTokens: 4000, ragTokens: 6000, recentHistoryTokens: 5000, toolSchemaTokens: 3000 },
};

// ── Entity fixtures ─────────────────────────────────────────────────────

export const mockExtractionResult: ExtractionResult = {
    entities: [
        { type: "project", name: "MyApp", properties: { language: "TypeScript" } },
        { type: "database", name: "PostgreSQL", properties: { version: "16" } },
        { type: "technology", name: "Redis", properties: { purpose: "caching" } },
    ],
    relationships: [
        { from: "MyApp", to: "PostgreSQL", relation: "uses", properties: {} },
        { from: "MyApp", to: "Redis", relation: "uses", properties: { context: "caching" } },
    ],
};

export const mockGraphEntity: GraphEntity = {
    id: "entity-1",
    tenantId: "default",
    type: "project",
    name: "MyApp",
    properties: { language: "TypeScript" },
    createdAt: new Date(),
};

export const mockGraphRelation: GraphRelation = {
    id: "edge-1",
    tenantId: "default",
    fromEntityId: "entity-1",
    toEntityId: "entity-2",
    relation: "uses",
    properties: {},
    createdAt: new Date(),
};

// ── OpenAI-style request/response ───────────────────────────────────────

export const openaiRequestBody = {
    model: "gpt-4o",
    messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: "Hello!" },
    ],
    stream: false,
};

export const openaiChatResponse = {
    id: "chatcmpl-123",
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: "gpt-4o",
    choices: [
        {
            index: 0,
            message: {
                role: "assistant",
                content: "Hello! How can I help you today?",
            },
            finish_reason: "stop",
        },
    ],
    usage: {
        prompt_tokens: 25,
        completion_tokens: 10,
        total_tokens: 35,
    },
};

// ── Telemetry ───────────────────────────────────────────────────────────

export const mockTelemetry: RequestTelemetry = {
    requestId: "req-123",
    tenantId: "default",
    client: "test",
    model: "gpt-4o",
    messageCount: 2,
    toolCount: 0,
    injectedTools: 0,
    toolCallsExecuted: 0,
    retrievalHits: 0,
    stream: false,
    providerLatencyMs: 100,
    skippedComponents: [],
    createdAt: new Date(),
};

// ── MCP ─────────────────────────────────────────────────────────────────

export const mockMcpServerConfigStdio = {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem"],
    env: { DEBUG: "true" },
};

export const mockMcpServerConfigUrl = {
    url: "https://example.com/mcp",
    headers: { Authorization: "Bearer test-token" },
};