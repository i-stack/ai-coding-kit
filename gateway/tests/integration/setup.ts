// Integration test setup: mock everything EXCEPT openai (so it actually calls our mock server)
import { vi } from "vitest";

vi.mock("@anthropic-ai/sdk", () => {
    class MockAnthropic {
        apiKey: string;
        messages: { create: ReturnType<typeof vi.fn>; stream: ReturnType<typeof vi.fn> };
        constructor(opts: { apiKey: string }) {
            this.apiKey = opts.apiKey;
            this.messages = {
                create: vi.fn().mockResolvedValue({
                    id: "msg_mock", model: "claude-sonnet-4",
                    content: [{ type: "text", text: "Mock response" }],
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
    class MockPool {
        query = vi.fn();
        connect = vi.fn().mockResolvedValue({ query: vi.fn(), release: vi.fn() });
        end = vi.fn();
    }
    return { default: { Pool: MockPool }, Pool: MockPool };
});

vi.mock("@modelcontextprotocol/sdk/client/index.js", () => ({
    Client: vi.fn(() => ({ connect: vi.fn(), close: vi.fn(), listTools: vi.fn(), callTool: vi.fn() })),
}));
vi.mock("@modelcontextprotocol/sdk/client/stdio.js", () => ({ StdioClientTransport: vi.fn() }));
vi.mock("@modelcontextprotocol/sdk/client/sse.js", () => ({ SSEClientTransport: vi.fn() }));
vi.mock("@modelcontextprotocol/sdk/server/index.js", () => ({ Server: vi.fn(() => ({ setRequestHandler: vi.fn(), connect: vi.fn() })) }));
vi.mock("@modelcontextprotocol/sdk/server/sse.js", () => ({ SSEServerTransport: vi.fn(() => ({ sessionId: "test", handlePostMessage: vi.fn() })) }));
vi.mock("@modelcontextprotocol/sdk/types.js", () => ({ ListToolsRequestSchema: {}, CallToolRequestSchema: {} }));
vi.mock("node:fs", () => {
    const m = { existsSync: vi.fn(() => false), readFileSync: vi.fn(() => "") };
    return { default: m, ...m };
});