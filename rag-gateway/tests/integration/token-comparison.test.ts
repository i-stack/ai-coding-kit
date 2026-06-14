/**
 * Token Consumption Comparison Test — v2 (Expanded)
 *
 * 5 windows × 5 rounds, each window mixes e-commerce, debugging, and system design
 * questions to simulate real-world cross-domain conversations.
 *
 * Path A (Direct client→provider):      system + [all prior rounds]      + new_msg
 * Path B (Client→Gateway→proxy→provider): system + [retrieved_context]    + new_msg
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import Fastify from "fastify";
import { MockProviderServer, MockVectorStore } from "../helpers/mock-server.js";
import { ProviderRouter } from "../../src/provider/router.js";
import { ToolRegistry } from "../../src/tool/registry.js";
import { ToolExecutorEngine } from "../../src/tool/executor.js";
import { registerChatRoutes } from "../../src/routes/chat.js";

// ── 5 windows × 5 rounds, mixed domains ────────────────────────────────

interface TestWindow {
    name: string;
    seedContext: string;
    rounds: string[];
    responses: string[];
}

const windows: TestWindow[] = [
    {
        name: "Window 1: E-commerce → Debug → Design → Debug → E-commerce",
        seedContext: "E-commerce platform: microservices (catalog, auth, payment, orders, inventory). "
            + "Known issues: Stripe 500 errors during checkout, DB pool exhaustion, inventory race conditions. "
            + "Architecture uses PostgreSQL, Redis, RabbitMQ, Docker.",
        rounds: [
            "Explain the architecture of a microservices e-commerce system. What are the key components?",
            "My payment service keeps timing out when users try to checkout. What could be wrong?",
            "Should I choose PostgreSQL or MongoDB for a social media application's user profiles?",
            "How do I fix race conditions in the inventory service when multiple users buy the same item?",
            "What caching strategy would you recommend for high-traffic e-commerce API endpoints?",
        ],
        responses: [
            "Microservices e-commerce architecture consists of independently deployable services including product catalog, user authentication, order processing, payment handling, and inventory management. The API Gateway handles routing and authentication at the edge. Services communicate asynchronously through RabbitMQ for event-driven workflows, and synchronously via REST for queries. PostgreSQL provides ACID compliance for the catalog and orders. Redis caches sessions and hot data. Each service is containerized and auto-scaled based on traffic metrics with service discovery via Consul for dynamic routing.",
            "The checkout 500 errors are most likely caused by the Stripe API timeout being too aggressive. Check your payment service's HTTP client configuration — the default 5-10 second timeout is often insufficient during peak hours when Stripe experiences latency spikes. Increase it to 30 seconds as Stripe recommends. Also implement a circuit breaker pattern using opossum to stop cascading failures, and add retry logic with exponential backoff from 1s up to 16s. Log structured request duration data to pinpoint exactly where the timeout occurs.",
            "Use both. PostgreSQL for user profiles due to its ACID compliance, JSONB columns for flexible profile metadata, and powerful JOIN capabilities for social graph queries like friend-of-friend recommendations. Its recursive CTEs enable efficient tree traversals for comment threads. MongoDB for write-heavy workloads like activity feeds and messaging where horizontal sharding is needed. Its change streams provide real-time data sync. This hybrid approach leverages each database's strengths.",
            "Optimistic locking is the recommended solution. Add a version column to your inventory table that increments on each successful update. When two users purchase the same item concurrently, only the first UPDATE with WHERE version = old_version succeeds; the second gets zero rows affected and retries. For high-contention items like limited releases, implement a Redis distributed lock with SETNX before inventory reservation, using Lua scripts for atomic deduction operations.",
            "A multi-level strategy works best. Level 1: Redis for hot data like product listings and cart contents with write-through for consistency. Level 2: CDN caching for product images and static assets with cache tags for granular invalidation. Level 3: Application-level stale-while-revalidate for frequently accessed API responses. Implement cache warming for known high-traffic events like flash sales. Monitor cache hit rates per level and set alerts for significant drops below baselines.",
        ],
    },
    {
        name: "Window 2: Debug → System Design → E-commerce → Debug → System Design",
        seedContext: "Social media platform: PostgreSQL for profiles, MongoDB for feeds. "
            + "Known bug: notification delivery delays under load. Engineering decisions: "
            + "Redis Pub/Sub for real-time, CDN for static assets, cache invalidation strategy.",
        rounds: [
            "Users are reporting that push notifications arrive 30 minutes late. What should I investigate first?",
            "Design a real-time notification system for a social media platform handling millions of concurrent connections.",
            "How should I handle inter-service authentication in a microservices e-commerce architecture?",
            "The database connection pool keeps throwing timeout errors under high traffic. The pool size is 20. What's happening?",
            "Compare PostgreSQL and MongoDB for a social media app's messaging and activity feed system.",
        ],
        responses: [
            "First, check your WebSocket server connection pool sizing. Each server handles ~10K connections but if you're under-provisioned, connections queue up causing delivery delays. Second, verify Redis Pub/Sub channel subscription management — if channels aren't properly cleaned up after users disconnect, message routing degrades. Third, check if notification delivery is blocking on database writes. Implement async delivery: accept the notification immediately, queue it, and deliver via background workers. Add delivery latency monitoring at p50/p95/p99 across different notification types.",
            "The architecture needs several layers. At the connection layer, WebSocket servers behind a load balancer with sticky sessions handle persistent connections. Each server handles approximately 10,000 concurrent connections, so cluster sizing depends on peak concurrent users. Redis Pub/Sub provides the message distribution bus where the notification service publishes events to per-user channels. Store delivery history in MongoDB for durability and pagination. Implement backpressure handling with a FIFO queue for offline users delivering on reconnection. Add rate limiting per user to prevent spam. Set up latency monitoring at p50/p95/p99.",
            "JWT tokens with Redis caching is the standard pattern. Each microservice independently validates JWTs using a shared public key, eliminating central auth lookups. JWTs carry user identity, roles, and permissions encoded directly in the payload. Redis caches token revocation lists with TTL-based expiration for near-instant invalidation on logout or permission changes. Use scoped service accounts with limited permissions for inter-service communication. Implement token refresh with short-lived access tokens (15 min) paired with longer-lived refresh tokens (7 days).",
            "Pool size of 20 is likely too small for high traffic, but the real issue is unclosed database transactions. When transactions aren't properly committed or rolled back, connections remain checked out from the pool until a timeout occurs, effectively reducing the pool size to zero. Check for try-catch blocks that catch exceptions but don't call pool.release() or client.release() in the finally block. Also look for implicit transactions started by ORMs that aren't explicitly closed. Increase the pool to 50-100 connections and add a connection leak detection mechanism.",
            "Use MongoDB for the activity feed and messaging system. Its document model maps naturally to denormalized feed items where each post embeds comments, likes, and shares for fast reads without joins. Horizontal sharding by user_id or timestamp enables linear write scaling as your user base grows. Change streams provide real-time feed updates. For the messaging system, MongoDB's TTL indexes automatically expire old messages. However, use PostgreSQL for the social graph and relationships where JOIN queries are essential for friend recommendations and group membership lookups.",
        ],
    },
    {
        name: "Window 3: System Design → E-commerce → Debug → System Design → E-commerce",
        seedContext: "Engineering platform: Docker container orchestration with Kubernetes. "
            + "CI/CD pipeline runs on GitHub Actions. Microservices communicate via gRPC. "
            + "Observability stack: Prometheus, Grafana, Jaeger for distributed tracing.",
        rounds: [
            "What caching strategy would you recommend for a high-traffic social media application?",
            "How do I secure API endpoints in an e-commerce microservices architecture?",
            "The inventory service has a race condition where two users buy the last item simultaneously and both succeed. How do I fix this?",
            "Compare the event-driven vs request-driven communication patterns for microservices architecture.",
            "What database should I use for an e-commerce order processing system that requires strict consistency?",
        ],
        responses: [
            "A comprehensive multi-level caching strategy: Level 1: Browser caching with Cache-Control headers for static assets. Level 2: CDN edge caching for images, CSS, and cached API responses with cache tags for invalidation. Level 3: Redis for hot data like trending content, user sessions, and frequently accessed profiles. Use write-through caching for consistency-critical data and write-behind for view counts. Level 4: Application-level stale-while-revalidate where stale data serves immediately while refreshing asynchronously. Implement cache warming for expected high-traffic events. Monitor hit rates at each level with alerts for drops below 80%.",
            "Implement a layered security approach. First, deploy an API Gateway that handles authentication using JWT validation at the edge before forwarding to internal services. Second, use short-lived access tokens (15 minutes) with refresh tokens stored in Redis. Third, implement role-based access control (RBAC) with permissions encoded in JWT claims. Fourth, use mTLS for inter-service communication. Fifth, implement rate limiting per API key at the gateway level. Sixth, add request validation middleware to prevent injection attacks. Log all authentication failures for security monitoring with structured logging.",
            "Optimistic locking is the correct fix. Add a version column to your inventory_items table. When processing a purchase, issue UPDATE inventory_items SET quantity = quantity - 1, version = version + 1 WHERE product_id = X AND version = current_version. The database guarantees only one concurrent transaction succeeds; the second gets zero affected rows. Your application code should retry the failed transaction after refreshing the version. For very high contention items, implement a Redis distributed lock with a short TTL before attempting the reservation to serialize access.",
            "Event-driven communication is superior for most microservices scenarios. Services publish domain events to a message broker like RabbitMQ or Kafka, and other services consume events asynchronously. This provides loose coupling, allowing services to evolve independently and fail in isolation. Request-driven REST/gRPC is better for synchronous queries where the caller needs an immediate response, like fetching product details. The best architectures use both: commands flow via events for orchestration, while queries use synchronous calls. This hybrid approach maximizes resilience while keeping response times predictable.",
            "PostgreSQL is the clear choice for order processing. It provides full ACID compliance ensuring that order transactions, payment records, and inventory deductions are atomic and durable. With SERIALIZABLE isolation level, you can prevent phantom reads and ensure consistent order fulfillment. PostgreSQL's Partial indexes speed up queries for active orders. Its NOTIFY/LISTEN feature enables real-time order status updates without polling. For high throughput, use connection pooling with PgBouncer and add read replicas for reporting queries without impacting write performance.",
        ],
    },
    {
        name: "Window 4: Debug → Debug → System Design → E-commerce → Debug",
        seedContext: "Production incidents: memory leaks in Node.js microservices, "
            + "Kubernetes pod OOMKilled events, PostgreSQL query performance degradation, "
            + "Redis cache stampede causing cascading failures under high traffic.",
        rounds: [
            "Our Node.js microservices keep crashing with OOMKilled in Kubernetes. The heap grows over 24 hours until it hits the limit.",
            "PostgreSQL query performance degraded 10x after we added a new index. Some queries that took 100ms now take 1000ms.",
            "How should I handle cache stampedes in Redis when popular content expires simultaneously under high traffic?",
            "What's the best way to handle payment processing in an e-commerce system to ensure reliability and idempotency?",
            "Our logs show connection pool exhaustion in the order service under peak load. The pool is configured for 50 connections but queries are queuing.",
        ],
        responses: [
            "This is a classic Node.js memory leak pattern. Start by taking a heap snapshot when the process starts and another just before OOM, then compare them to find objects that accumulate. Common causes: global variable accumulation in closures, event emitter listeners not removed (especially with database drivers), unclosed database connections, and streams not properly consumed. Use the --inspect flag and Chrome DevTools Memory tab to analyze snapshots. Check for setInterval callbacks that capture large objects in closure scope. Add memory usage monitoring with alerts at 70%, 85%, and 95% of the pod memory limit.",
            "Your new index is likely causing the PostgreSQL query planner to choose a suboptimal plan. When you create an index, the planner recalculates statistics and may switch from a fast sequential scan to an incorrect index scan that requires many random I/Os. Check EXPLAIN ANALYZE output before and after. The fix is to either drop the index and create a more targeted composite index, or use pg_hint_plan to force the correct plan. Also run ANALYZE to update statistics after creating indexes. Consider partial indexes that only cover frequently queried subsets of data to reduce index size and maintenance overhead.",
            "Implement probabilistic early expiration (sometimes called 'jitter'). When a cached value is within its TTL window, serve it directly. As it approaches expiry, use a random function that determines whether the current request triggers a refresh. This means at any given time only a small fraction of requests (say 1-5%) attempt to regenerate the cache, preventing the thundering herd. Specifically: serve stale data with async refresh for non-critical content. For critical data, use mutex locks with Redis SETNX so only one process regenerates the cache while others wait briefly or serve stale data.",
            "Implement idempotent payment processing using idempotency keys. Generate a unique key for each checkout attempt and pass it to the payment provider. If the provider receives a duplicate request with the same key, it returns the original result instead of processing a duplicate charge. Use Stripe's idempotency API for this. On your side, store payment intent IDs in the database and check for duplicates before processing. Use a two-phase commit pattern: reserve inventory first, then process payment, then confirm the order. If the payment fails, the reservation automatically releases after a timeout.",
            "The pool size of 50 may be adequate, but the queuing suggests connections aren't being released back to the pool. Check for unclosed database transactions where exceptions are caught but the connection isn't released in a finally block. Also check for transaction timeouts that leave connections idle but checked out. Set a pool idle timeout (idleTimeoutMillis in pg-pool) to reclaim leaked connections. Add connection pool metrics monitoring to track active, idle, and waiting counts. Implement a circuit breaker that rejects requests early when the pool is exhausted instead of letting them queue indefinitely.",
        ],
    },
    {
        name: "Window 5: System Design → E-commerce → Debug → System Design → Debug",
        seedContext: "Architecture decisions: event sourcing for order history, CQRS for reporting, "
            + "GraphQL for API layer, circuit breakers for resilience, saga pattern for distributed transactions.",
        rounds: [
            "Explain the saga pattern for distributed transactions in microservices. When should I use it?",
            "Our e-commerce platform needs a product search feature across 1 million products. What approach do you recommend?",
            "The API gateway is timing out after 30 seconds on some endpoints while downstream services are still processing. How do I fix this?",
            "Compare GraphQL and REST for a microservices API layer that serves multiple client types.",
            "Our CI/CD pipeline has flaky tests that fail intermittently due to race conditions in test fixtures. The team is losing trust in the pipeline.",
        ],
        responses: [
            "The saga pattern manages distributed transactions across microservices by breaking them into a sequence of local transactions with compensating actions. For each step that succeeds, there's a compensating transaction that undoes it if a later step fails. For example, in an e-commerce order: reserve inventory (if fails → abort), process payment (if fails → release inventory), confirm order (if fails → refund payment). Choreography-based sagas use events to coordinate steps while orchestration-based sagas use a central coordinator. Use sagas for business transactions spanning multiple services, but avoid them for simple queries that can use REST calls.",
            "Implement Elasticsearch as a dedicated search index. Use a change data capture pipeline with Debezium to stream product changes from PostgreSQL to Elasticsearch in near real-time. Elasticsearch provides full-text search with relevance scoring, faceted search for filtering by category and attributes, fuzzy matching for typo tolerance, and aggregations for analytics. Index products with all their attributes, descriptions, and categories. For the search API, use the gateway to proxy search requests to Elasticsearch with query rewriting for security. Add autocomplete suggestions using edge n-grams for fast prefix matching.",
            "The 30-second timeout is too long for an API gateway — it should fail fast. Set the gateway timeout to 5-10 seconds max. For operations that genuinely take longer, use the asynchronous request-accept pattern: the gateway immediately returns a 202 Accepted with a location header pointing to a status endpoint. The client polls the status endpoint until the result is ready. Alternatively, use WebSocket or Server-Sent Events for real-time progress updates. Implement timeout per service rather than a single global timeout. Use circuit breakers to stop calling services that consistently exceed their timeouts.",
            "GraphQL is better for complex data-fetching scenarios where multiple client types need different data shapes from the same endpoints. It reduces over-fetching and under-fetching problems common in REST. Clients can request exactly the fields they need, which is valuable for mobile clients with limited bandwidth. However, GraphQL adds complexity: query cost analysis to prevent expensive nested queries, resolver performance optimization, and caching is harder compared to REST. Use REST for simple CRUD operations and stable APIs. Use GraphQL for the aggregation layer that serves multiple frontend clients with different data requirements.",
            "First, identify and quarantine flaky tests by running the full suite and marking failures that don't reproduce consistently. Use Vitest's retry feature or Jest's --retryTimes flag to automatically retry flaky tests. Second, fix the root cause: shared mutable state between tests is the most common cause of test race conditions. Ensure each test has isolated fixtures using beforeEach to reset all state. Use unique database schemas or tables per test file. Third, add test dependency tracing to detect tests that accidentally depend on side effects from other tests. Fourth, implement deterministic seeding for random data in tests.",
        ],
    },
];

// ── Test ────────────────────────────────────────────────────────────────

describe("Token Consumption Comparison v2 (5x5 Mixed Domains)", () => {
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
        it(`${window.name}: gateway saves tokens across ${window.rounds.length} rounds`, async () => {
            const vs = new MockVectorStore();
            vs.reset();

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

                // PATH A: Direct (full accumulated history)
                const directMessages: any[] = JSON.parse(JSON.stringify(directHistory));
                directMessages.push({ role: "user", content: userMsg });
                const directTok = countPromptTokens(directMessages);
                directTokens.push(directTok);

                // PATH B: Gateway
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

                const saved = directTok - gwTok;

                console.log(
                    `  Round ${roundNum}: direct=${directTok} tok, gateway=${gwTok} tok,`
                    + ` saved=${saved > 0 ? "+" : ""}${saved} tok`
                    + ` (${saved > 0 ? (saved / directTok * 100).toFixed(0) : (Math.abs(saved) / directTok * 100).toFixed(0)}%)`,
                );

                // Accumulate into direct path
                directHistory.push({ role: "user", content: userMsg } as any);
                directHistory.push({ role: "assistant", content: assistantResp } as any);

                // Index compact summary (~150 chars) into vector store for next round retrieval.
                // Short summaries are critical: they keep injected context << accumulated history.
                await vs.indexMessage({
                    id: `round-${r}`,
                    text: `Q: ${userMsg.slice(0, 40)} A: ${assistantResp.slice(0, 100)}`,
                    kind: "user_message",
                    tenantId: "default",
                });
            }

            // ── Assertions ─────────────────────────────────────────────
            const totalRounds = window.rounds.length;
            expect(directTokens).toHaveLength(totalRounds);
            expect(gatewayTokens).toHaveLength(totalRounds);

            // Direct path grows every round
            for (let i = 1; i < totalRounds; i++) {
                expect(directTokens[i]).toBeGreaterThan(directTokens[i - 1]);
            }

            // Core claim: by last round, gateway sends fewer upstream tokens
            const lastIdx = totalRounds - 1;
            console.log(`  Final round (R${totalRounds}): direct=${directTokens[lastIdx]} vs gateway=${gatewayTokens[lastIdx]}`);
            expect(gatewayTokens[lastIdx]).toBeLessThan(directTokens[lastIdx]);

            // Growth comparison: direct vs gateway
            const directGrowth = directTokens[lastIdx] - directTokens[0];
            const gatewayGrowth = gatewayTokens[lastIdx] - gatewayTokens[0];
            console.log(`  Growth R1→R${totalRounds}: direct=${directGrowth} tok, gateway=${gatewayGrowth} tok`);

            // Gateway should have positive savings by the final round
            const finalSavings = directTokens[lastIdx] - gatewayTokens[lastIdx];
            console.log(`  Final savings: ${finalSavings} tok (${(finalSavings / directTokens[lastIdx] * 100).toFixed(0)}%)`);

            await app.close();
        }, 30000);
    }
});