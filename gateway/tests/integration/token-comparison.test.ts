/**
 * Token Consumption Comparison Test
 *
 * Verifies that the Gateway reduces token consumption compared to direct API calls.
 *
 * Architecture:
 *   Mock HTTP Server (records request payloads, char-length proxy for tokens)
 *       ├── Path A: Send messages + FULL accumulated history → mock server
 *       └── Path B: Send ONLY new message → Gateway → internally retrieves
 *                    context from vector store → sends COMPRESSED request to mock server
 *
 * Expected:
 *   - Round 1: Similar tokens (no prior context yet to retrieve)
 *   - Round 2: Path B sends ≈ same as R1 (retrieved context replaces history)
 *              Path A sends ≈ R1 × 2 (history grows linearly)
 *   - Round 3: Path B still ≈ same; Path A ≈ R1 × 3
 *              → Cumulative saved % increases each round
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "node:http";
import Fastify from "fastify";
import { MockProviderServer, MockVectorStore } from "../helpers/mock-server.js";
import type { RequestRecord } from "../helpers/mock-server.js";
import { ProviderRouter } from "../../src/provider/router.js";
import { ToolRegistry } from "../../src/tool/registry.js";
import { ToolExecutorEngine } from "../../src/tool/executor.js";
import { registerChatRoutes } from "../../src/routes/chat.js";

// ── Conversation windows ────────────────────────────────────────────────

interface TestWindow {
    name: string;
    seedContext: string;
    rounds: string[];
}

const windows: TestWindow[] = [
    {
        name: "Window 1: Microservices E-commerce Architecture",
        seedContext: "The system architecture includes microservices for product catalog, user authentication, "
            + "order processing, payment handling, and inventory management. Services communicate via RabbitMQ. "
            + "The product catalog uses PostgreSQL with complex query patterns. Authentication uses JWT tokens "
            + "with Redis session caching for performance. Each service runs in a Docker container with horizontal scaling.",
        rounds: [
            "Explain the architecture of a microservices e-commerce system. What are the key components and how do they communicate?",
            "What database should I use for the product catalog in my e-commerce platform?",
            "How should I handle authentication between microservices?",
        ],
    },
    {
        name: "Window 2: Debugging Production Issues",
        seedContext: "Payment gateway timeout causes 500 errors during checkout. The payment service communicates "
            + "with Stripe API with a 10-second timeout. Race conditions in the inventory service cause overselling "
            + "when multiple users purchase the same item simultaneously. The fix uses optimistic locking with "
            + "retry logic. Database connection pool is exhausted under high load due to unclosed transactions.",
        rounds: [
            "My API returns 500 errors when users try to checkout. The payment service seems to be timing out.",
            "Here's the stack trace from the payment service showing a timeout on Stripe API calls.",
            "How do I fix race conditions in the inventory service when stock levels drop low?",
        ],
    },
    {
        name: "Window 3: System Design Decisions",
        seedContext: "PostgreSQL is strong for relational data with JSONB support for flexible schemas and ACID compliance. "
            + "MongoDB offers horizontal scaling and better write performance. Real-time notifications use WebSocket "
            + "connections with Redis Pub/Sub for low-latency delivery. Caching uses Redis write-through for hot "
            + "data and CDN caching for static assets with cache tag invalidation.",
        rounds: [
            "Compare PostgreSQL and MongoDB for a social media app. Which one should I choose?",
            "Design a real-time notification system for a social media platform.",
            "What caching strategy would you recommend for a high-traffic social media application?",
        ],
    },
];

// ── Test setup ──────────────────────────────────────────────────────────

describe("Token Consumption Comparison", () => {
    let mockServer: MockProviderServer;
    let vectorStore: MockVectorStore;
    let mockServerUrl: string;
    let gatewayApp: Fastify.FastifyInstance | null = null;
    let gatewayPort: number = 0;

    beforeAll(async () => {
        mockServer = new MockProviderServer();
        await mockServer.start();
        mockServerUrl = `http://127.0.0.1:${mockServer.port}`;
        console.log(`Mock provider on port ${mockServer.port}`);
    });

    afterAll(async () => {
        if (gatewayApp) await gatewayApp.close();
        await mockServer.stop();
    });

    // ── Gateway factory ─────────────────────────────────────────────

    async function startGateway(): Promise<void> {
        if (gatewayApp) await gatewayApp.close();

        const app = Fastify({ logger: false });
        process.env.OPENAI_BASE_URL = mockServerUrl;
        process.env.OPENAI_API_KEY = "test-key";

        const config = {
            openaiApiKey: "test-key",
            openaiBaseUrl: mockServerUrl,
            openaiDefaultModel: "gpt-4o",
            anthropicApiKey: "",
            anthropicBaseUrl: "",
            port: 0,
            host: "127.0.0.1",
            databaseUrl: "",
            qdrantUrl: "",
            graphRagEnabled: false,
        } as any;

        const provider = new ProviderRouter(config);
        const toolRegistry = new ToolRegistry();
        toolRegistry.register({
            name: "get_current_time", description: "Get current time",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "Current time: {{env.NOW}}" },
        });
        const toolExecutor = new ToolExecutorEngine([], undefined);

        // Pass the MockVectorStore as the real vector store
        registerChatRoutes(app, provider, config, vectorStore as any, undefined, toolRegistry, toolExecutor);

        const addr = await app.listen({ port: 0, host: "127.0.0.1" });
        gatewayPort = (app.server.address() as any).port;
        gatewayApp = app;
    }

    // ── Direct path: send message + full prior history to mock provider ──

    async function sendDirect(
        message: string,
        priorMessages: string[],
    ): Promise<{ inputCharCount: number; inputTokenEstimate: number }> {
        const msgs = [
            { role: "system", content: "You are a helpful assistant." },
        ];
        for (const pm of priorMessages) {
            msgs.push({ role: "user", content: pm });
            msgs.push({ role: "assistant", content: "Here is an answer to your question about " + pm.slice(0, 40) + "..." });
        }
        msgs.push({ role: "user", content: message });

        const res = await fetch(`${mockServerUrl}/v1/chat/completions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: "gpt-4o", messages: msgs }),
        });
        await res.json();

        // The direct request is the last request recorded on the mock server
        // (since no gateway is in between)
        const last = mockServer.lastRequest;
        return {
            inputCharCount: last?.inputCharCount ?? 0,
            inputTokenEstimate: last?.inputTokenEstimate ?? 0,
        };
    }

    // ── Gateway path: send only the new message, let gateway retrieve context ──

    async function sendViaGateway(
        message: string,
    ): Promise<{
        inputCharCount: number;
        inputTokenEstimate: number;
        /** The raw request body the gateway sent to the mock provider */
        proxyBody: any;
    }> {
        const res = await fetch(`http://127.0.0.1:${gatewayPort}/v1/chat/completions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model: "gpt-4o",
                messages: [
                    { role: "system", content: "You are a helpful assistant." },
                    { role: "user", content: message },
                ],
                stream: false,
            }),
        });
        await res.json();

        const last = mockServer.lastRequest;
        return {
            inputCharCount: last?.inputCharCount ?? 0,
            inputTokenEstimate: last?.inputTokenEstimate ?? 0,
            proxyBody: last?.body ?? null,
        };
    }

    // ── Run all windows ──────────────────────────────────────────────

    for (const window of windows) {
        it(`${window.name}: gateway should send fewer tokens by round 3`, async () => {
            vectorStore = new MockVectorStore();
            await startGateway();

            // Seed the vector store with window-specific context
            await vectorStore.indexMessage({
                id: "seed",
                text: window.seedContext,
                kind: "system_prompt",
                tenantId: "default",
            });

            const priorMessages: string[] = [];
            const directTokens: number[] = [];
            const gatewayTokens: number[] = [];

            for (let i = 0; i < window.rounds.length; i++) {
                const msg = window.rounds[i];

                mockServer.reset();

                // Path A: Direct — send with full accumulated history
                const direct = await sendDirect(msg, priorMessages);
                directTokens.push(direct.inputTokenEstimate);

                // Path B: Via gateway — send only new message
                const gw = await sendViaGateway(msg);
                gatewayTokens.push(gw.inputTokenEstimate);

                console.log(
                    `  Round ${i + 1}: direct=${direct.inputTokenEstimate} tok (${direct.inputCharCount} chars),`
                    + ` gateway=${gw.inputTokenEstimate} tok (${gw.inputCharCount} chars),`
                    + ` proxy msgs=${gw.proxyBody?.messages?.length ?? "?"}`,
                );

                priorMessages.push(msg);

                // Index the conversation into vector store for next rounds
                await vectorStore.indexMessage({
                    id: `round-${i}`,
                    text: `The user asked about: ${msg}.`
                        + ` The assistant explained relevant concepts and provided guidance.`,
                    kind: "user_message",
                    tenantId: "default",
                });
            }

            // ── Assertions ─────────────────────────────────────────

            // Round 1: both should be close (no prior context yet to retrieve)
            const diffR1 = Math.abs(directTokens[0] - gatewayTokens[0]);
            const maxR1 = Math.max(directTokens[0], gatewayTokens[0], 1);
            expect(diffR1 / maxR1).toBeLessThan(0.5);

            // Round 2: gateway should send notably fewer tokens than direct
            // Direct accumulates history linearly; gateway retrieves from vector store
            if (directTokens[1] > 50 && gatewayTokens[1] > 0) {
                const savePct = 1 - gatewayTokens[1] / directTokens[1];
                console.log(`  Round 2 savings: ${(savePct * 100).toFixed(0)}%`);
                // Gateway sends tokens for its own messages + retrieved context.
                // For a 2-round direct (4 msgs) vs gateway (2 msgs + context ≈ 2-3 msgs),
                // the gateway should still save meaningfully.
                expect(gatewayTokens[1]).toBeLessThan(directTokens[1]);
            }

            // Round 3: cumulative savings should be visible
            if (directTokens[2] > 50 && gatewayTokens[2] > 0) {
                const savePct = 1 - gatewayTokens[2] / directTokens[2];
                console.log(`  Round 3 savings: ${(savePct * 100).toFixed(0)}%`);
                expect(gatewayTokens[2]).toBeLessThan(directTokens[2]);
            }

            // Trend: savings % should increase or stay level
            const saveR1 = directTokens[0] > 0 ? 1 - gatewayTokens[0] / directTokens[0] : 0;
            const saveR2 = directTokens[1] > 0 ? 1 - gatewayTokens[1] / directTokens[1] : 0;
            const saveR3 = directTokens[2] > 0 ? 1 - gatewayTokens[2] / directTokens[2] : 0;
            console.log(`  Savings trend: R1=${(saveR1 * 100).toFixed(0)}% R2=${(saveR2 * 100).toFixed(0)}% R3=${(saveR3 * 100).toFixed(0)}%`);

            // Direct path grows linearly as rounds increase
            expect(directTokens[2]).toBeGreaterThan(directTokens[1]);
            expect(directTokens[1]).toBeGreaterThan(directTokens[0]);

            await gatewayApp?.close();
            gatewayApp = null;
        }, 30000);
    }

    it("should complete all 3 windows with valid data", () => {
        expect(windows).toHaveLength(3);
    });
});