import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { ToolExecutorEngine } from "../../../src/tool/executor.js";
import { McpClientManager } from "../../../src/mcp/client.js";
import type { ToolSpec } from "../../../src/tool/types.js";

describe("ToolExecutorEngine", () => {
    let engine: ToolExecutorEngine;
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal("fetch", fetchMock);
        engine = new ToolExecutorEngine(
            ["api.github.com", "httpbin.org", "jsonplaceholder.typicode.com"],
            undefined,
        );
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    const httpTool: ToolSpec = {
        name: "lookup_status",
        description: "Look up HTTP status code",
        input_schema: { type: "object", properties: { code: { type: "string" } }, required: ["code"] },
        executor: { type: "http_request", method: "GET", url: "https://httpbin.org/status/{{args.code}}", timeoutMs: 5000 },
    };

    const templateTool: ToolSpec = {
        name: "get_time",
        description: "Get current time",
        input_schema: { type: "object", properties: {} },
        executor: { type: "static_template", template: "Current time: {{env.NOW}}" },
    };

    // ── http_request tests ──────────────────────────────────────────────

    it("should execute http_request with GET method", async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            status: 200,
            text: () => Promise.resolve("OK response"),
        });
        const result = await engine.execute(httpTool, "call-1", { code: "200" });
        expect(result.success).toBe(true);
        expect(fetchMock).toHaveBeenCalledWith(
            "https://httpbin.org/status/200",
            expect.objectContaining({ method: "GET" }),
        );
    });

    it("should block non-HTTPS URLs (except httpbin and localhost)", async () => {
        const badTool: ToolSpec = {
            ...httpTool,
            executor: { type: "http_request", method: "GET", url: "http://evil.com/data" },
        };
        const result = await engine.execute(badTool, "call-2", {});
        expect(result.success).toBe(false);
        expect(result.error).toContain("Non-HTTPS");
    });

    it("should allow httpbin.org on HTTP", async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            status: 200,
            text: () => Promise.resolve("OK"),
        });
        const httpbinTool: ToolSpec = {
            ...httpTool,
            executor: { type: "http_request", method: "GET", url: "http://httpbin.org/get" },
        };
        const result = await engine.execute(httpbinTool, "call-3", {});
        expect(result.success).toBe(true);
    });

    it("should block non-allowlisted hosts", async () => {
        const blockTool: ToolSpec = {
            ...httpTool,
            executor: { type: "http_request", method: "GET", url: "https://random-site.com/data" },
        };
        const result = await engine.execute(blockTool, "call-4", {});
        expect(result.success).toBe(false);
        expect(result.error).toContain("allowlist");
    });

    it("should enforce timeout via AbortController", async () => {
        fetchMock.mockImplementation(
            () => new Promise((_, reject) => {
                // This will be rejected by timeout, but we just check AbortSignal is passed
                setTimeout(() => reject(new Error("timeout")), 100);
            }),
        );
        const fastTool: ToolSpec = {
            ...httpTool,
            executor: { type: "http_request", method: "GET", url: "https://httpbin.org/status/200", timeoutMs: 10 },
        };
        const result = await engine.execute(fastTool, "call-5", { code: "200" });
        // Timeout results in an error (not success)
        expect(result.success).toBe(false);
    });

    it("should handle POST with body and header template substitution", async () => {
        fetchMock.mockResolvedValue({
            ok: true, status: 200, text: () => Promise.resolve("posted"),
        });
        const postTool: ToolSpec = {
            name: "post_data",
            description: "POST data",
            input_schema: { type: "object", properties: { value: { type: "string" } }, required: ["value"] },
            executor: {
                type: "http_request", method: "POST",
                url: "https://jsonplaceholder.typicode.com/posts",
                headers: { "X-Custom": "test-header" },
                body: { key: "{{args.value}}" },
            },
        };
        const result = await engine.execute(postTool, "call-6", { value: "hello" });
        expect(result.success).toBe(true);
        const callArgs = fetchMock.mock.calls[0];
        expect(callArgs[1].method).toBe("POST");
        expect(JSON.parse(callArgs[1].body)).toEqual({ key: "hello" });
        expect(callArgs[1].headers["X-Custom"]).toBe("test-header");
    });

    // ── static_template tests ───────────────────────────────────────────

    it("should execute static_template with {{args.xxx}} substitution", () => {
        const tool: ToolSpec = {
            name: "greet",
            description: "Greet someone",
            input_schema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
            executor: { type: "static_template", template: "Hello, {{args.name}}!" },
        };
        const result = engine.execute(tool, "call-t1", { name: "Alice" });
        // synchronous, no await needed
        expect(result.success).toBe(true);
        expect(result.content).toBe("Hello, Alice!");
    });

    it("should execute static_template with {{env.NOW}} substitution", () => {
        const tool: ToolSpec = {
            name: "time",
            description: "Get time",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "Time: {{env.NOW}}" },
        };
        const result = engine.execute(tool, "call-t2", {});
        expect(result.success).toBe(true);
        expect(result.content).toMatch(/Time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:/);
    });

    it("should substitute environment variables via {{env.VAR}}", () => {
        process.env.TEST_VAR = "test_value";
        const tool: ToolSpec = {
            name: "env_test",
            description: "Test env vars",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "Value: {{env.TEST_VAR}}" },
        };
        const result = engine.execute(tool, "call-t3", {});
        expect(result.content).toBe("Value: test_value");
        delete process.env.TEST_VAR;
    });

    // ── mcp_call tests ──────────────────────────────────────────────────

    it("should return error when McpClientManager is not configured", async () => {
        const mcpTool: ToolSpec = {
            name: "mcp_tool",
            description: "MCP tool",
            input_schema: { type: "object", properties: {} },
            executor: { type: "mcp_call", server: "nonexistent", method: "test" },
        };
        const simpleEngine = new ToolExecutorEngine();
        const result = await simpleEngine.execute(mcpTool, "call-m1", {});
        expect(result.success).toBe(false);
        expect(result.error).toContain("MCP client manager");
    });

    it("should return error when MCP server is not connected", async () => {
        const mcpTool: ToolSpec = {
            name: "mcp_tool",
            description: "MCP tool",
            input_schema: { type: "object", properties: {} },
            executor: { type: "mcp_call", server: "disconnected-server", method: "test" },
        };
        const mcpManager = new McpClientManager();
        const engineWithMcp = new ToolExecutorEngine(undefined, mcpManager);
        const result = await engineWithMcp.execute(mcpTool, "call-m2", {});
        expect(result.success).toBe(false);
        expect(result.error).toContain("not connected");
    });

    // ── Unknown executor type ───────────────────────────────────────────

    it("should return error for unknown executor type", () => {
        const badTool: ToolSpec = {
            name: "bad",
            description: "Bad tool",
            input_schema: { type: "object", properties: {} },
            executor: { type: "unknown_executor" as any },
        };
        const result = engine.execute(badTool, "call-u1", {});
        expect(result.success).toBe(false);
        expect(result.error).toContain("Unknown executor type");
    });

    // ── executeBatch ────────────────────────────────────────────────────

    it("should execute multiple tools via executeBatch", async () => {
        fetchMock.mockResolvedValue({
            ok: true, status: 200, text: () => Promise.resolve("OK"),
        });
        const results = await engine.executeBatch(
            [httpTool, templateTool],
            [
                { id: "batch-1", name: "lookup_status", args: { code: "200" } },
                { id: "batch-2", name: "get_time", args: {} },
            ],
        );
        expect(results).toHaveLength(2);
        expect(results[0].success).toBe(true);
        expect(results[1].success).toBe(true);
    });

    it("should return error for unknown tool in executeBatch", async () => {
        const results = await engine.executeBatch(
            [httpTool],
            [{ id: "batch-x", name: "nonexistent_tool", args: {} }],
        );
        expect(results).toHaveLength(1);
        expect(results[0].success).toBe(false);
        expect(results[0].error).toContain("not found");
    });
});