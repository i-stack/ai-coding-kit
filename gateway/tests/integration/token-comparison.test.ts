/**
 * Token Consumption Comparison Test
 *
 * Validates the core claim: Gateway sends FEWER upstream tokens than direct calls
 * after accumulating conversation history, because it replaces full history with
 * compact retrieved context.
 *
 * Path A (Direct client→provider):      system + [all prior rounds]      + new_msg
 * Path B (Client→Gateway→proxy→provider): system + [retrieved_context]    + new_msg
 *
 * Key insight: Retrieved context stays ~constant while prior history grows linearly.
 * After enough rounds: retrieved_context << prior_rounds → savings.
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import Fastify from "fastify";
import { MockProviderServer, MockVectorStore } from "../helpers/mock-server.js";
import { ProviderRouter } from "../../src/provider/router.js";
import { ToolRegistry } from "../../src/tool/registry.js";
import { ToolExecutorEngine } from "../../src/tool/executor.js";
import { registerChatRoutes } from "../../src/routes/chat.js";

// ── 3 windows × 3 rounds ───────────────────────────────────────────────

interface TestWindow {
    name: string;
    /** Short seed known to the gateway (system prompt replacement, not history) */
    seedContext: string;
    /** 3 user messages */
    rounds: string[];
    /** Realistic-length assistant responses (800–1200 chars, simulating real AI answers) */
    responses: string[];
}

const windows: TestWindow[] = [
    {
        name: "Window 1: E-commerce Architecture",
        seedContext: "Microservices e-commerce: product catalog (PostgreSQL), auth (JWT+Redis),"
            + " order processing (RabbitMQ), payment (Stripe), inventory management.",
        rounds: [
            "Explain the architecture of a microservices e-commerce system. What are the key components?",
            "What database should I use for the product catalog in my e-commerce platform?",
            "How should I handle authentication between microservices?",
        ],
        responses: [
            "Microservices e-commerce architecture consists of several independently deployable services: "
            + "the product catalog service manages inventory data and search indexing using PostgreSQL for reliable ACID transactions. "
            + "The user authentication service handles registration, login, and session management via JWT tokens with Redis caching. "
            + "The order processing service orchestrates checkout workflows including payment validation and inventory reservation. "
            + "The payment service integrates with Stripe or similar gateways for secure transaction processing. "
            + "Services communicate asynchronously through RabbitMQ message queues for event-driven workflows and synchronously through REST APIs for query operations. "
            + "Each service runs in its own Docker container with horizontal auto-scaling based on CPU and memory utilization metrics. "
            + "API Gateway handles request routing, rate limiting, and authentication at the edge layer before forwarding to internal services. "
            + "Service discovery via Consul ensures dynamic routing as instances scale up and down based on traffic patterns.",
            "For the product catalog, PostgreSQL is the recommended choice for several important reasons. "
            + "First, it provides full ACID compliance which is essential for maintaining data integrity across product updates, inventory changes, and pricing modifications. "
            + "Second, JSONB columns allow storing flexible product attributes like specifications, variants, and metadata without rigid schema migrations. "
            + "Third, PostgreSQL's powerful indexing capabilities including B-tree, GIN, and GiST indexes enable fast full-text search across product descriptions and categories. "
            + "Fourth, materialized views can precompute complex reporting queries like category aggregations and inventory summaries. "
            + "Fifth, PostgreSQL supports partial indexes, covering indexes, and index-only scans that dramatically reduce query latency for high-traffic catalog pages. "
            + "For read-heavy workloads, you can add read replicas and use connection pooling via PgBouncer. "
            + "MongoDB could be considered if you need horizontal sharding and document flexibility, but for an e-commerce catalog with complex relational queries and transactions, PostgreSQL is the safer choice.",
            "JWT-based authentication with Redis caching is the most practical approach for microservices. "
            + "Each service independently validates JWT tokens by verifying the signature using a shared public key, eliminating the need for central auth lookups on every request. "
            + "JWTs carry claims about user identity, roles, and permissions encoded in the payload, which services can use directly for authorization decisions. "
            + "Redis caches token revocation lists with TTL-based expiration, providing near-instant invalidation when users log out or permissions change. "
            + "For inter-service communication, use scoped service accounts with limited permissions rather than user tokens. "
            + "Implement token refresh flows where short-lived access tokens (15 minutes) are paired with longer-lived refresh tokens (7 days) stored securely in Redis. "
            + "The API Gateway should validate tokens at the edge and pass verified claims via HTTP headers to internal services, avoiding duplicate validation overhead.",
        ],
    },
    {
        name: "Window 2: Debugging Issues",
        seedContext: "Production issues: payment gateway timeout causing 500 checkout errors,"
            + " inventory race conditions causing overselling under concurrent load.",
        rounds: [
            "My API returns 500 errors when users try to checkout. The payment service seems to be timing out.",
            "Here's the stack trace from the payment service showing a timeout on Stripe API calls.",
            "How do I fix race conditions in the inventory service when stock levels drop low?",
        ],
        responses: [
            "The 500 errors during checkout strongly suggest the payment gateway timeout is being exceeded. "
            + "Start by examining the Stripe API timeout configuration in your payment service deployment. "
            + "The typical symptom is that the HTTP client configured with a 5-10 second timeout is too aggressive for payment processing, which can take longer during peak hours or when Stripe's infrastructure experiences latency spikes. "
            + "First, increase the Stripe API timeout to 30 seconds as recommended by Stripe's official documentation for production workloads. "
            + "Second, implement a circuit breaker pattern using a library like opossum or a custom state machine that tracks failure rates and temporarily stops calling Stripe when errors exceed a threshold. "
            + "Third, add retry logic with exponential backoff starting at 1 second and doubling up to 16 seconds for transient network failures. "
            + "Fourth, ensure your database connection pool in the payment service is properly sized for concurrent checkout requests. "
            + "Fifth, add structured logging around the Stripe API calls to capture request duration, error codes, and response payloads for faster debugging of future incidents. "
            + "Sixth, consider moving payment processing to a background job queue so the user gets an immediate confirmation and the payment settles asynchronously, which dramatically improves user experience.",
            "The stack trace you shared shows a 10-second timeout on the Stripe charge API call, which confirms the timeout configuration is the primary issue. "
            + "However, there are several additional improvements you should make beyond just increasing the timeout value. "
            + "Implement a retry strategy with exponential backoff: first retry after 1 second, then 2 seconds, then 4 seconds, up to a maximum of 4 retries. "
            + "Use Stripe's idempotency keys to ensure that retries don't result in duplicate charges by including a unique idempotency key in each request. "
            + "Add a bulkhead pattern that limits the number of concurrent Stripe API calls to prevent cascading failures under load. "
            + "Set up monitoring alerts for payment service latency at the 50th, 95th, and 99th percentiles so you can detect degradation before it impacts users. "
            + "Also implement a fallback payment provider that can be activated via a feature flag in case Stripe experiences a prolonged outage. "
            + "Document your incident response runbook for payment failures including exact steps for triage, escalation, and communication with stakeholders during payment service disruptions.",
            "For inventory race conditions under concurrent load, optimistic locking is the most effective solution. "
            + "Add a version column to your inventory table that increments on every successful update. "
            + "When two users try to purchase the same item simultaneously, the UPDATE statement includes a WHERE version = :old_version clause. "
            + "Only the first transaction's update succeeds; the second receives zero affected rows and must retry. "
            + "This approach works well for low-to-moderate contention scenarios where conflicts are relatively rare. "
            + "For high-contention items like limited edition products, implement a Redis-based distributed lock using SETNX with an appropriate TTL before attempting the inventory reservation. "
            + "Use Lua scripts in Redis for atomic inventory deduction operations. "
            + "Alternatively, implement a queue-based inventory reservation system where each purchase request goes into a FIFO queue and a single consumer processes reservations sequentially. "
            + "Monitor inventory contention metrics in production to tune the approach based on actual traffic patterns and stock levels.",
        ],
    },
    {
        name: "Window 3: System Design",
        seedContext: "Social media platform tech: PostgreSQL (relational+JSONB),"
            + " MongoDB (horizontal scaling), Redis Pub/Sub (real-time notifications), CDN caching.",
        rounds: [
            "Compare PostgreSQL and MongoDB for a social media app. Which one should I choose?",
            "Design a real-time notification system for a social media platform.",
            "What caching strategy would you recommend for a high-traffic social media application?",
        ],
        responses: [
            "PostgreSQL and MongoDB serve different purposes in a social media architecture, and often you will use both. "
            + "PostgreSQL excels at user profile storage with ACID-compliant transactions for account creation, email verification, and password resets. "
            + "Its JSONB columns allow flexible profile metadata like preferences and settings without schema migrations. "
            + "Powerful JOIN operations make it ideal for social graph queries like friend-of-friend recommendations and group membership lookups. "
            + "PostgreSQL's recursive CTEs enable efficient tree traversals for comment threads and nested replies. "
            + "MongoDB, on the other hand, excels at write-heavy workloads like activity feeds, notification history, and messaging where horizontal sharding is necessary for scale. "
            + "Its document model maps naturally to denormalized data patterns like embedding post content with associated comments for fast reads. "
            + "MongoDB's change streams provide real-time data synchronization for features like live feed updates. "
            + "Practical recommendation: use PostgreSQL as the primary database for user accounts, relationships, and structured content. "
            + "Use MongoDB for high-volume write streams like activity logging, analytics events, and messaging history. "
            + "This hybrid approach leverages each database's strengths while minimizing their weaknesses.",
            "A real-time notification system at social media scale requires careful architectural planning across multiple layers. "
            + "At the connection layer, WebSocket servers behind a load balancer with sticky sessions maintain persistent connections to millions of concurrent users. "
            + "Each WebSocket server can handle approximately 10,000 concurrent connections on moderate hardware, so you need a horizontal cluster sized based on your peak concurrent user estimates. "
            + "For the message distribution layer, Redis Pub/Sub provides a lightweight publish-subscribe pattern where the notification service publishes events to channels named after user IDs and WebSocket servers subscribe to the channels for their connected users. "
            + "Redis Sentinel or Cluster ensures high availability for the Pub/Sub infrastructure. "
            + "For notification durability, store delivery history in MongoDB or PostgreSQL with appropriate indexing on user_id and created_at for efficient querying. "
            + "Implement backpressure handling by queuing notifications when users are offline and delivering them on reconnection via a FIFO queue. "
            + "Add rate limiting to prevent notification spamming and allow users to configure notification preferences through a centralized settings service. "
            + "Monitor delivery latency metrics at p50, p95, and p99 to detect degradation and scale WebSocket server pools proactively based on connection count trends.",
            "A multi-level caching strategy is essential for social media performance at scale. "
            + "Level 1: Browser caching with appropriate Cache-Control headers for static assets like images, CSS, and JavaScript bundles that rarely change. "
            + "Level 2: CDN caching at edge locations for static assets and API responses that can be cached for short durations, using cache tags for granular invalidation when content updates. "
            + "Level 3: Redis cache for hot data including user sessions, trending topics, recent posts from followed users, and frequently accessed profiles. "
            + "Use write-through caching for consistency-critical data like user sessions where stale data would cause login issues. "
            + "Use write-behind caching for less critical data like post view counts where eventual consistency is acceptable. "
            + "Level 4: Application-level caching with stale-while-revalidate pattern for frequently accessed API responses - serve stale data immediately while asynchronously refreshing from the database. "
            + "Implement cache warming for known high-traffic events like product launches or celebrity posts by pre-populating the cache with expected content. "
            + "Monitor cache hit rates at each level separately and set up alerts when rates drop below acceptable thresholds. "
            + "Use cache stampede protection with probabilistic early expiration to prevent thundering herd problems on cache misses.",
        ],
    },
];

// ── Test ────────────────────────────────────────────────────────────────

describe("Token Consumption Comparison", () => {
    let mockServer: MockProviderServer;

    beforeAll(async () => {
        mockServer = new MockProviderServer();
        await mockServer.start();
    });

    afterAll(async () => {
        await mockServer.stop();
    });

    function countPromptTokens(messages: any[]): number {
        return messages.reduce((sum: number, m: any) => {
            const c = typeof m.content === "string" ? m.content : JSON.stringify(m.content ?? "");
            return sum + Math.ceil(c.length / 4) + 5;
        }, 0);
    }

    async function startGateway(vs: MockVectorStore): Promise<Fastify.FastifyInstance> {
        const app = Fastify({ logger: false });
        process.env.OPENAI_BASE_URL = `http://127.0.0.1:${mockServer.port}`;
        process.env.OPENAI_API_KEY = "test-key";

        const config = {
            openaiApiKey: "test-key",
            openaiBaseUrl: `http://127.0.0.1:${mockServer.port}`,
            openaiDefaultModel: "gpt-4o",
            anthropicApiKey: "",
            anthropicBaseUrl: "",
            port: 0, host: "127.0.0.1", databaseUrl: "", qdrantUrl: "", graphRagEnabled: false,
        } as any;

        const provider = new ProviderRouter(config);
        const tr = new ToolRegistry();
        const te = new ToolExecutorEngine([], undefined);
        registerChatRoutes(app, provider, config, vs as any, undefined, tr, te);
        await app.listen({ port: 0, host: "127.0.0.1" });
        return app;
    }

    for (const window of windows) {
        it(`${window.name}: gateway sends fewer upstream tokens than direct by round 3`, async () => {
            const vs = new MockVectorStore();
            vs.reset();

            // Seed short domain context
            await vs.indexMessage({
                id: "seed", text: window.seedContext,
                kind: "system_prompt", tenantId: "default",
            });

            const app = await startGateway(vs);
            const port = (app.server.address() as any).port;

            const directTokens: number[] = [];
            const gatewayTokens: number[] = [];
            const directHistory: Array<{ role: string; content: string }> = [
                { role: "system", content: "You are a helpful assistant." },
            ];

            for (let r = 0; r < window.rounds.length; r++) {
                const userMsg = window.rounds[r];
                const assistantResp = window.responses[r];
                const roundNum = r + 1;

                // ── PATH A: Direct (full accumulated history) ────────
                const directMessages: any[] = JSON.parse(JSON.stringify(directHistory));
                directMessages.push({ role: "user", content: userMsg });
                const directTok = countPromptTokens(directMessages);
                directTokens.push(directTok);

                // ── PATH B: Gateway ──────────────────────────────────
                mockServer.reset();
                const gwRes = await fetch(`http://127.0.0.1:${port}/v1/chat/completions`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        model: "gpt-4o",
                        messages: [
                            { role: "system", content: "You are a helpful assistant." },
                            { role: "user", content: userMsg },
                        ],
                        stream: false,
                    }),
                });
                await gwRes.json();

                const lastReq = mockServer.lastRequest;
                const gwTok = lastReq?.inputTokenEstimate ?? 0;
                gatewayTokens.push(gwTok);

                // Absolute savings vs direct (positive = gateway saved tokens)
                const saved = directTok - gwTok;

                console.log(
                    `  Round ${roundNum}: direct=${directTok} tok,`
                    + ` gateway=${gwTok} tok,`
                    + ` saved=${saved > 0 ? "+" : ""}${saved} tok`
                    + ` (${saved > 0 ? (saved / directTok * 100).toFixed(0) : (Math.abs(saved) / directTok * 100).toFixed(0)}%)`,
                );

                // Accumulate full realistic history into the direct path
                directHistory.push({ role: "user", content: userMsg } as any);
                directHistory.push({ role: "assistant", content: assistantResp } as any);

                // Index compact summary into vector store for next round retrieval
                await vs.indexMessage({
                    id: `round-${r}`,
                    text: `Prior conversation: user asked about ${userMsg.slice(0, 50)}. `
                        + `Key topics: ${assistantResp.slice(0, 500)}`,
                    kind: "user_message",
                    tenantId: "default",
                });
            }

            // ── Assertions ───────────────────────────────────────────
            expect(directTokens).toHaveLength(3);
            expect(gatewayTokens).toHaveLength(3);

            // Direct token count grows each round (accumulates history)
            expect(directTokens[2]).toBeGreaterThan(directTokens[1]);
            expect(directTokens[1]).toBeGreaterThan(directTokens[0]);

            // Direct path's total tokens include the full realistic assistant responses
            // Gateway's total tokens include injected context (from vector store)
            // The key claim: direct path grows faster because it carries the FULL history,
            // while gateway's injected context is a compressed summary
            const directGrowth = directTokens[2] - directTokens[0];
            const gatewayGrowth = gatewayTokens[2] - gatewayTokens[0];
            console.log(`  Growth: direct=${directGrowth} tok, gateway=${gatewayGrowth} tok`);

            // Core claim: by round 3, gateway sends fewer upstream tokens
            // than the direct path because it retrieves compressed context
            // instead of sending the full conversation history
            console.log(`  Round 3: direct=${directTokens[2]} vs gateway=${gatewayTokens[2]}`);
            expect(gatewayTokens[2]).toBeLessThan(directTokens[2]);

            await app.close();
        }, 30000);
    }
});