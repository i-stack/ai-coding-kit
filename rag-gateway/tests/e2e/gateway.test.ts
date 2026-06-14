/**
 * End-to-end gateway tests using Fastify's inject() method.
 *
 * Tests validate route registration and response shapes for non-provider
 * endpoints. Provider-dependent POST routes require a real upstream and
 * are covered in the integration tests.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import Fastify from "fastify";
import { ProviderRouter } from "../../src/provider/router.js";
import { ToolRegistry } from "../../src/tool/registry.js";
import { ToolExecutorEngine } from "../../src/tool/executor.js";
import { registerChatRoutes } from "../../src/routes/chat.js";
import { registerMcpServer } from "../../src/mcp/server.js";

async function createTestApp(opts?: { withAnthropic?: boolean }) {
    const app = Fastify({ logger: false });

    const config = {
        openaiApiKey: "test-key",
        openaiBaseUrl: "http://127.0.0.1:9999",
        openaiDefaultModel: "gpt-4o",
        anthropicApiKey: opts?.withAnthropic ? "ant-key" : "",
        anthropicBaseUrl: "https://api.anthropic.com",
        graphRagEnabled: false,
    } as any;

    const provider = new ProviderRouter(config);
    const toolRegistry = new ToolRegistry();
    const toolExecutor = new ToolExecutorEngine([], undefined);

    registerChatRoutes(app, provider, config, undefined, undefined, toolRegistry, toolExecutor);
    registerMcpServer(app, toolRegistry, toolExecutor);

    app.get("/health", async () => ({ status: "ok", timestamp: new Date().toISOString() }));
    app.get("/metrics", async () => ({ requestsTotal: 0, uptimeMs: 0 }));

    return app;
}

describe("Gateway E2E", () => {
    let app: Awaited<ReturnType<typeof createTestApp>>;

    beforeAll(async () => {
        app = await createTestApp();
        await app.ready();
    });

    afterAll(async () => {
        await app.close();
    });

    it("GET /health should return 200 with status ok", async () => {
        const res = await app.inject({ method: "GET", url: "/health" });
        expect(res.statusCode).toBe(200);
        const body = JSON.parse(res.body);
        expect(body.status).toBe("ok");
        expect(body.timestamp).toBeDefined();
    });

    it("GET /v1/models should return model list", async () => {
        const res = await app.inject({ method: "GET", url: "/v1/models" });
        expect(res.statusCode).toBe(200);
        const body = JSON.parse(res.body);
        expect(body.object).toBe("list");
        expect(body.data).toBeInstanceOf(Array);
        expect(body.data.length).toBeGreaterThanOrEqual(1);
        expect(body.data[0]).toHaveProperty("id");
        expect(body.data[0]).toHaveProperty("object", "model");
    });

    it("GET /v1/models should include Anthropic models when configured", async () => {
        const appAnthropic = await createTestApp({ withAnthropic: true });
        await appAnthropic.ready();
        const res = await appAnthropic.inject({ method: "GET", url: "/v1/models" });
        const body = JSON.parse(res.body);
        const hasClaude = body.data.some((m: any) => m.id.includes("claude"));
        expect(hasClaude).toBe(true);
        await appAnthropic.close();
    });

    it("GET /metrics should return metrics snapshot", async () => {
        const res = await app.inject({ method: "GET", url: "/metrics" });
        expect(res.statusCode).toBe(200);
        const body = JSON.parse(res.body);
        expect(body).toHaveProperty("requestsTotal");
    });

    it("GET /mcp/sse endpoint should be registered (not 404)", async () => {
        const res = await app.inject({ method: "GET", url: "/mcp/sse" });
        expect(res.statusCode).not.toBe(404);
    });

    it("POST /mcp/message without sessionId should return 404", async () => {
        const res = await app.inject({ method: "POST", url: "/mcp/message" });
        expect(res.statusCode).toBe(404);
    });
});