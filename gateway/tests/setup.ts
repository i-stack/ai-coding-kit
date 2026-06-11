import { vi } from "vitest";

// ── Mock all external SDKs at module level ──────────────────────────────

// Use `beforeAll` hoisted mock factories — these must NOT reference outer scope `vi` after hoisting
vi.mock("openai", () => {
    class MockOpenAI {
        apiKey: string;
        baseURL: string;
        chat: { completions: { create: ReturnType<typeof vi.fn> } };
        embeddings: { create: ReturnType<typeof vi.fn> };

        constructor(opts: { apiKey: string; baseURL?: string }) {
            this.apiKey = opts.apiKey;
            this.baseURL = opts.baseURL ?? "https://api.openai.com/v1";
            this.chat = {
                completions: {
                    create: vi.fn().mockResolvedValue({
                        id: "chatcmpl-mock",
                        model: "gpt-4o",
                        choices: [{ message: { content: "Mock response" }, finish_reason: "stop" }],
                        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
                    }),
                },
            };
            this.embeddings = {
                create: vi.fn().mockResolvedValue({
                    data: [{ embedding: [0.1, 0.2, 0.3], index: 0 }],
                    model: "bge-m3",
                    usage: { prompt_tokens: 5, total_tokens: 5 },
                }),
            };
        }
    }

    return { default: MockOpenAI };
});

vi.mock("@anthropic-ai/sdk", () => {
    class MockAnthropic {
        apiKey: string;
        messages: { create: ReturnType<typeof vi.fn>; stream: ReturnType<typeof vi.fn> };

        constructor(opts: { apiKey: string }) {
            this.apiKey = opts.apiKey;
            this.messages = {
                create: vi.fn().mockResolvedValue({
                    id: "msg_mock",
                    model: "claude-sonnet-4",
                    content: [{ type: "text", text: "Mock Anthropic response" }],
                    stop_reason: "end_turn",
                    usage: { input_tokens: 10, output_tokens: 5 },
                }),
                stream: vi.fn(),
            };
        }
    }

    return { default: MockAnthropic };
});

vi.mock("pg", () => {
    const mockQuery = vi.fn();
    const mockConnect = vi.fn();
    const mockRelease = vi.fn();
    const mockClient = { query: mockQuery, release: mockRelease };

    mockConnect.mockResolvedValue(mockClient);

    class MockPool {
        query = mockQuery;
        connect = mockConnect;
        end = vi.fn();
    }

    return {
        default: { Pool: MockPool },
        Pool: MockPool,
    };
});

vi.mock("@modelcontextprotocol/sdk/client/index.js", () => {
    class MockClient {
        connect = vi.fn();
        close = vi.fn();
        listTools = vi.fn().mockResolvedValue({ tools: [] });
        callTool = vi.fn().mockResolvedValue({ content: [{ type: "text", text: "mock" }] });
    }

    return { Client: MockClient };
});

vi.mock("@modelcontextprotocol/sdk/client/stdio.js", () => {
    return { StdioClientTransport: vi.fn() };
});

vi.mock("@modelcontextprotocol/sdk/client/sse.js", () => {
    return { SSEClientTransport: vi.fn() };
});

vi.mock("@modelcontextprotocol/sdk/server/index.js", () => {
    class MockServer {
        setRequestHandler = vi.fn();
        connect = vi.fn();
    }

    return { Server: MockServer };
});

vi.mock("@modelcontextprotocol/sdk/server/sse.js", () => {
    const mockHandlePostMessage = vi.fn();
    class MockSSEServerTransport {
        sessionId = "test-session-id";
        handlePostMessage = mockHandlePostMessage;
    }

    return { SSEServerTransport: MockSSEServerTransport };
});

vi.mock("@modelcontextprotocol/sdk/types.js", () => {
    return {
        ListToolsRequestSchema: {},
        CallToolRequestSchema: {},
    };
});

// ── Mock node:fs for ToolRegistry / config loading tests ───────────────
vi.mock("node:fs", () => {
    const mockFs = {
        existsSync: vi.fn(() => false),
        readFileSync: vi.fn(() => ""),
        writeFileSync: vi.fn(),
        mkdirSync: vi.fn(),
    };

    return {
        default: mockFs,
        ...mockFs,
    };
});

// ── Global env vars ─────────────────────────────────────────────────────
process.env.OPENAI_API_KEY = "test-openai-key";
process.env.OPENAI_BASE_URL = "https://api.openai.com/v1";
process.env.OPENAI_DEFAULT_MODEL = "gpt-4o";
process.env.GATEWAY_PORT = "0";
process.env.GATEWAY_HOST = "127.0.0.1";