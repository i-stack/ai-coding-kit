import type { FastifyInstance } from "fastify";
import type { Provider } from "../provider/types.js";
import type { GatewayConfig } from "../config.js";
import type { VectorStore } from "../vector/store.js";
import type { EntityStore } from "../entity/store.js";
import type { ToolRegistry } from "../tool/registry.js";
import type { ToolExecutorEngine } from "../tool/executor.js";
import { getSimplifiedSchema } from "../tool/simplify.js";
import { BudgetPlanner } from "../planner/budget.js";
import {
    computeRetrievalConstraints,
    computeToolBudgetLimit,
    computeOutputBudget,
    computeMessageTrimBudget,
} from "../planner/budget.js";
import {
    createTelemetry,
    recordDegradation,
    emitTelemetry,
    telemetrySummary,
} from "../telemetry.js";
import { metricsCollector } from "../metrics.js";
import crypto from "node:crypto";

// ── Type alias for OpenAI-compatible tool definitions ──────────────
type OpenAICompatibleTool = {
    type: "function";
    function: {
        name: string;
        description: string;
        parameters: Record<string, unknown>;
    };
};

// ── Optional transcript storage ────────────────────────────────────
interface TranscriptStore {
    requestId: string;
    tenantId: string;
    projectId?: string;
    model: string;
    messages: Array<{ role: string; content: string | null }>;
    responseContent: string | null;
    totalTokens: number;
    streaming: boolean;
}

async function storeTranscript(store: TranscriptStore): Promise<void> {
    try {
        const { insertConversation, insertMessage, finalizeConversation, generateId } =
            await import("../db/transcript.js");
        const { getPool } = await import("../db/index.js");

        try {
            getPool();
        } catch {
            return;
        }

        const conversationId = store.requestId;
        const now = new Date();

        await insertConversation({
            id: conversationId,
            tenantId: store.tenantId,
            projectId: store.projectId,
            client: "unknown",
            model: store.model,
            startedAt: now,
        });

        for (let i = 0; i < store.messages.length; i++) {
            const msg = store.messages[i];
            await insertMessage({
                id: generateId(),
                conversationId,
                turnIndex: i,
                role: msg.role,
                content: msg.content,
            });
        }

        await insertMessage({
            id: generateId(),
            conversationId,
            turnIndex: store.messages.length,
            role: "assistant",
            content: store.responseContent,
        });

        await finalizeConversation(conversationId, store.totalTokens);
    } catch (err) {
        console.error("Failed to store transcript:", (err as Error).message);
    }
}

// ── Optional Qdrant indexing ───────────────────────────────────────
async function indexToQdrant(
    vectorStore: VectorStore | undefined,
    requestId: string,
    _model: string,
    userMessages: Array<{ role: string; content: string | null }>,
    responseContent: string | null,
    tenantId: string,
    projectId?: string,
): Promise<void> {
    if (!vectorStore) return;

    try {
        for (const msg of userMessages) {
            if (!msg.content) continue;
            await vectorStore.indexMessage({
                id: crypto.randomUUID(),
                text: msg.content,
                kind: "user_message",
                tenantId,
                projectId,
                sourceMessageId: crypto.randomUUID(),
                conversationId: requestId,
            });
        }

        if (responseContent) {
            await vectorStore.indexMessage({
                id: crypto.randomUUID(),
                text: responseContent,
                kind: "assistant_message",
                tenantId,
                projectId,
                sourceMessageId: crypto.randomUUID(),
                conversationId: requestId,
            });
        }
    } catch (err) {
        console.error("Failed to index to Qdrant:", (err as Error).message);
    }
}

// ── Schema for incoming request ────────────────────────────────────
interface ChatCompletionRequest {
    model?: string;
    messages: Array<{
        role: string;
        content: string | Array<Record<string, unknown>>;
        name?: string;
        tool_call_id?: string;
        tool_calls?: unknown[];
    }>;
    tools?: Array<{
        type: string;
        function: {
            name: string;
            description?: string;
            parameters: Record<string, unknown>;
        };
    }>;
    tool_choice?: unknown;
    stream?: boolean;
    max_tokens?: number;
    temperature?: number;
    tenant_id?: string;
    project_id?: string;
}

// ── Tool deduplication: client tools win, gateway tools fill gaps ──
function mergeDedupedTools(
    clientTools: ChatCompletionRequest["tools"] | undefined,
    gatewayTools: OpenAICompatibleTool[],
): OpenAICompatibleTool[] | undefined {
    if (!clientTools && gatewayTools.length === 0) return undefined;
    if (!clientTools) return gatewayTools;
    if (gatewayTools.length === 0) return clientTools.map(normalizeClientTool);

    const clientNormalized = clientTools.map(normalizeClientTool);
    const clientNames = new Set(clientNormalized.map((t) => t.function.name));
    const uniqueGateway = gatewayTools.filter(
        (t) => !clientNames.has(t.function.name),
    );
    return [...clientNormalized, ...uniqueGateway];
}

function normalizeClientTool(t: {
    type: string;
    function: { name: string; description?: string; parameters: Record<string, unknown> };
}): OpenAICompatibleTool {
    return {
        type: "function",
        function: {
            name: t.function.name,
            description: t.function.description ?? "",
            parameters: t.function.parameters,
        },
    };
}

/**
 * Compute max tool count for a model.
 * Used as an upper bound alongside the budget-derived limit.
 */
function maxToolsForModel(model: string): number {
    const lower = model.toLowerCase();
    if (lower.includes("gpt-3.5") || lower.includes("gpt-4-turbo")) return 10;
    if (lower.includes("claude-3-haiku") || lower.includes("claude-3-sonnet")) return 10;
    if (lower.includes("claude-3-opus") || lower.includes("claude-sonnet-4")) return 20;
    if (lower.includes("gpt-4o") || lower.includes("gpt-4.1")) return 20;
    return 20; // default generous cap
}

/**
 * Trim the messages array to fit within the recent history budget.
 * Keeps the system message (first) + most recent user/assistant messages.
 */
function trimMessagesByBudget(
    messages: ChatCompletionRequest["messages"],
    budget: ReturnType<typeof computeMessageTrimBudget>,
): ChatCompletionRequest["messages"] {
    if (messages.length <= 2) return messages; // nothing worth trimming

    // The first system message is always kept for stable cache prefix
    const systemMsg = messages[0].role === "system" ? messages[0] : undefined;
    const rest = systemMsg ? messages.slice(1) : messages;

    // Estimate: count chars of each message
    let totalChars = 0;
    const kept: typeof messages = [];
    for (let i = rest.length - 1; i >= 0; i--) {
        const m = rest[i];
        const charLen = typeof m.content === "string"
            ? m.content.length
            : JSON.stringify(m.content).length;
        // Add a bit of overhead per message for role markers
        const estimatedCost = charLen + 20;
        if (totalChars + estimatedCost > budget.maxHistoryChars) break;
        totalChars += estimatedCost;
        kept.unshift(rest[i]);
    }

    const result = systemMsg ? [systemMsg, ...kept] : kept;
    return result.length > 0 ? result : messages.slice(-2); // never fewer than last 2
}

export function registerChatRoutes(
    app: FastifyInstance,
    provider: Provider,
    config: GatewayConfig,
    vectorStore?: VectorStore,
    entityStore?: EntityStore,
    toolRegistry?: ToolRegistry,
    toolExecutor?: ToolExecutorEngine,
): void {
    // ── Context Budget Planner (per-server instance) ──────────────────
    const planner = new BudgetPlanner();

    // ── POST /v1/chat/completions ──────────────────────────────────────
    app.post("/v1/chat/completions", async (request, reply) => {
        const startTime = Date.now();
        const requestId = crypto.randomUUID();

        const body = request.body as ChatCompletionRequest;
        const model = body.model ?? config.openaiDefaultModel;
        const messages = body.messages;
        const stream = body.stream ?? false;
        const tenantId = body.tenant_id ?? "default";
        const projectId = body.project_id;

        const telemetry = createTelemetry({
            requestId,
            tenantId,
            model,
            messageCount: messages.length,
            toolCount: body.tools?.length ?? 0,
            stream,
        });

        const flattenMessages = messages.map((m) => ({
            role: m.role,
            content:
                typeof m.content === "string" ? m.content : JSON.stringify(m.content),
        }));

        try {
            // ── Step 0: Context Budget Planning ──────────────────────────
            const systemMessage = messages.find((m) => m.role === "system");
            const systemContent = typeof systemMessage?.content === "string"
                ? systemMessage.content
                : undefined;
            const normalizedForPlanner = messages.map((m) => ({
                role: m.role as "system" | "user" | "assistant" | "tool",
                content: typeof m.content === "string"
                    ? m.content
                    : JSON.stringify(m.content),
                tool_call_id: m.tool_call_id,
            }));

            const { decision, budget } = planner.plan(normalizedForPlanner, systemContent);

            // Derive downstream constraints from the budget
            const retrievalConstraint = computeRetrievalConstraints(budget);
            const toolBudgetLimit = computeToolBudgetLimit(budget);
            const outputTokens = computeOutputBudget(budget);
            const trimBudget = computeMessageTrimBudget(budget);

            // Record budget in telemetry for auditability
            telemetry.budget = {
                intent: budget.intent,
                maxContextTokens: budget.maxContextTokens,
                ragTokens: budget.ragTokens,
                reserveTokens: budget.reserveTokens,
            };

            // Log the full decision for debugging
            request.log.debug({ budgetDecision: decision }, "context budget planned");

            // ── Step 1: Message history trim by budget ─────────────────────
            // Trim messages to fit recentHistoryTokens before retrieval/providing.
            const trimmedMessages = trimMessagesByBudget(messages, trimBudget);
            const trimmedCount = messages.length - trimmedMessages.length;
            if (trimmedCount > 0) {
                request.log.debug({ trimmedCount }, "history trimmed by budget");
            }

            // ── Step 2: Retrieve relevant memories from Qdrant + Graph ─────
            let memorySnippets: Array<{ relevance: string; preview: string }> | undefined;
            let retrievedContext: string | undefined;
            let graphContext: string | undefined;
            let lastUserMsg: string | undefined;

            // Find the last user message once, used by both retrievals
            const lastUserMsgObj = [...flattenMessages]
                .reverse()
                .find((m) => m.role === "user");
            lastUserMsg = lastUserMsgObj?.content as string | undefined;

            // Qdrant semantic search
            if (vectorStore && retrievalConstraint.maxResults > 0 && lastUserMsg) {
                try {
                    // Fetch slightly more than limit so we can filter by score
                    const searchLimit = Math.min(retrievalConstraint.maxResults * 2, 20);
                    const results = await vectorStore.search(lastUserMsg, {
                        limit: searchLimit,
                        tenantId,
                        projectId,
                    });
                    // Filter by score threshold derived from budget
                    const filteredResults = results.filter(
                        (r) => r.score >= retrievalConstraint.scoreThreshold,
                    );
                    // Apply final count limit
                    const cappedResults = filteredResults.slice(0, retrievalConstraint.maxResults);
                    if (cappedResults.length > 0) {
                        retrievedContext = cappedResults
                            .map(
                                (r) => `[memory (relevance=${r.score.toFixed(2)})] ${r.payload.text}`,
                            )
                            .join("\n\n");
                        telemetry.retrievalHits = cappedResults.length;
                        metricsCollector.recordRetrievalHits(cappedResults.length);
                        memorySnippets = cappedResults.map((r) => ({
                            relevance: r.score.toFixed(2),
                            preview: r.payload.text.slice(0, 200),
                        }));
                    }
                    request.log.debug(
                        {
                            searchResults: results.length,
                            filteredByScore: filteredResults.length,
                            finalCapped: cappedResults.length,
                            threshold: retrievalConstraint.scoreThreshold,
                        },
                        "retrieval constrained by budget",
                    );
                } catch (err) {
                    recordDegradation(telemetry, "memory-retrieval", (err as Error).message);
                    console.error("Qdrant search error:", (err as Error).message);
                }
            }

            // Graph (entity-relationship) search
            if (entityStore && lastUserMsg) {
                try {
                    const graphResults = await entityStore.searchGraph(
                        lastUserMsg,
                        tenantId,
                        { limit: retrievalConstraint.maxResults, projectId },
                    );
                    if (graphResults.length > 0) {
                        const contextLines = entityStore.formatContext(graphResults);
                        graphContext = contextLines.join("\n");
                        telemetry.retrievalHits += graphResults.length;
                        if (!memorySnippets) memorySnippets = [];
                        for (const r of graphResults) {
                            memorySnippets.push({
                                relevance: "0.50",
                                preview: r.entity.name.slice(0, 200),
                            });
                        }
                        request.log.debug(
                            { graphHits: graphResults.length },
                            "graph-enhanced retrieval",
                        );
                    }
                } catch (err) {
                    recordDegradation(telemetry, "memory-retrieval", (err as Error).message);
                    console.error("Graph search error:", (err as Error).message);
                }
            }

            // ── Step 3: Inject tools + retrieved context from Qdrant and Graph ─
            let enrichedMessages: any[] = trimmedMessages;
            // Deduplicate memory snippets by lowercased preview (graph extraction
            // may store same entity under different casing, Qdrant + graph may overlap)
            if (memorySnippets) {
                const seen = new Set<string>();
                memorySnippets = memorySnippets.filter((s) => {
                    const key = s.preview.toLowerCase();
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }
            const memoryContext = [retrievedContext, graphContext]
                .filter(Boolean)
                .join("\n\n");
            if (memoryContext) {
                enrichedMessages = [
                    {
                        role: "system" as const,
                        content: `Relevant context from previous conversations:\n\n${memoryContext}`,
                    },
                    ...trimmedMessages,
                ];
            }

            // Resolve tool_choice: client → registry policy → "auto" → undefined
            const policyChoice = toolRegistry?.resolveToolChoicePolicy(model);
            const clientToolChoice = body.tool_choice as any;
            let resolvedToolChoice: any;
            if (clientToolChoice !== undefined) {
                resolvedToolChoice = clientToolChoice;
            } else if (policyChoice) {
                resolvedToolChoice = policyChoice;
            }

            // Build gateway tools with per-model schema simplification
            const rawGatewayTools: OpenAICompatibleTool[] = toolRegistry
                ? toolRegistry.toOpenAITools(model)
                : [];
            const simplifiedGatewayTools: OpenAICompatibleTool[] = rawGatewayTools.map((gt) => {
                const spec = toolRegistry?.get(gt.function.name);
                if (spec) {
                    return {
                        type: "function" as const,
                        function: {
                            name: gt.function.name,
                            description: gt.function.description,
                            parameters: getSimplifiedSchema(spec, model) as unknown as Record<string, unknown>,
                        },
                    };
                }
                return gt;
            });

            // Deduplicate: client tools win, gateway fills gaps
            const clientTools = body.tools as any[] | undefined;
            const allTools = mergeDedupedTools(clientTools, simplifiedGatewayTools);

            // Cap tools by both model limit AND budget limit
            const modelToolCap = maxToolsForModel(model);
            const effectiveToolCap = Math.min(modelToolCap, toolBudgetLimit);
            const finalTools: OpenAICompatibleTool[] | undefined = allTools
                ? allTools.slice(0, effectiveToolCap)
                : undefined;
            telemetry.injectedTools = finalTools
                ? finalTools.length - (clientTools?.length ?? 0)
                : 0;

            // Compute provider max_tokens: client explicit > budget derived
            const providerMaxTokens = body.max_tokens ?? outputTokens;

            request.log.debug(
                {
                    retrievalConstraint,
                    toolBudgetLimit,
                    effectiveToolCap,
                    outputTokens,
                    providerMaxTokens,
                    trimmedCount,
                },
                "budget constraints applied",
            );

            // ── Step 4: Main completion (with potential tool roundtrip) ───
            if (stream) {
                const options = {
                    maxTokens: providerMaxTokens,
                    temperature: body.temperature,
                    tools: finalTools && finalTools.length > 0 ? finalTools : undefined,
                    toolChoice: resolvedToolChoice ?? (finalTools && finalTools.length > 0 ? "auto" : undefined),
                };

                reply.raw.writeHead(200, {
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    Connection: "keep-alive",
                    "x-request-id": requestId,
                    "x-gateway-retrieval-hits": String(telemetry.retrievalHits),
                });

                const chunkIter = provider.chatStreaming(
                    model,
                    enrichedMessages as any,
                    options,
                );
                let usageEmitted = false;
                const contentParts: string[] = [];
                let totalTokens = 0;
                let firstChunkTime = 0;

                for await (const chunk of chunkIter) {
                    if (chunk.type === "delta") {
                        if (firstChunkTime === 0) firstChunkTime = Date.now();
                        contentParts.push(chunk.delta ?? "");
                        const sseData = {
                            id: requestId,
                            object: "chat.completion.chunk",
                            created: Math.floor(Date.now() / 1000),
                            model,
                            choices: [
                                {
                                    index: 0,
                                    delta: { content: chunk.delta },
                                    finish_reason: null,
                                },
                            ],
                        };
                        reply.raw.write(`data: ${JSON.stringify(sseData)}\n\n`);
                    } else if (chunk.type === "done" && chunk.usage && !usageEmitted) {
                        usageEmitted = true;
                        totalTokens = chunk.usage?.totalTokens ?? 0;
                        const sseData = {
                            id: requestId,
                            object: "chat.completion.chunk",
                            created: Math.floor(Date.now() / 1000),
                            model,
                            choices: [
                                {
                                    index: 0,
                                    delta: {},
                                    finish_reason: chunk.finishReason,
                                },
                            ],
                            usage: chunk.usage,
                        };
                        reply.raw.write(`data: ${JSON.stringify(sseData)}\n\n`);
                    } else if (
                        chunk.type === "done" &&
                        chunk.finishReason &&
                        !usageEmitted
                    ) {
                        const sseData = {
                            id: requestId,
                            object: "chat.completion.chunk",
                            created: Math.floor(Date.now() / 1000),
                            model,
                            choices: [
                                {
                                    index: 0,
                                    delta: {},
                                    finish_reason: chunk.finishReason,
                                },
                            ],
                        };
                        reply.raw.write(`data: ${JSON.stringify(sseData)}\n\n`);
                    }
                }

                reply.raw.write("data: [DONE]\n\n");
                reply.raw.end();

                // Track streaming latency: time-to-first-token
                const streamLatencyMs = firstChunkTime > 0
                    ? firstChunkTime - startTime
                    : Date.now() - startTime;
                telemetry.providerLatencyMs = streamLatencyMs;
                metricsCollector.recordRequest(model, streamLatencyMs, "200");

                const fullContent = contentParts.join("");
                emitTelemetry(telemetry, request.log);
                storeTranscript({
                    requestId,
                    tenantId,
                    projectId,
                    model,
                    messages: flattenMessages,
                    responseContent: fullContent,
                    totalTokens,
                    streaming: true,
                });
                indexToQdrant(vectorStore, requestId, model, flattenMessages, fullContent, tenantId, projectId);

                // Fire-and-forget: entity extraction (GraphRAG)
                if (entityStore) {
                    const conversationText = [
                        ...flattenMessages.map((m) => m.content),
                        fullContent,
                    ]
                        .filter(Boolean)
                        .join("\n\n");
                    entityStore.extractAndStore(conversationText, tenantId, projectId).catch((err: Error) => {
                        console.error("Entity extraction failed:", err.message);
                        recordDegradation(telemetry, "entity-extraction", err.message);
                    });
                }
            } else {
                // ── Non-streaming: support tool call roundtrip ─────────────
                const options = {
                    maxTokens: providerMaxTokens,
                    temperature: body.temperature,
                    tools: finalTools && finalTools.length > 0 ? finalTools : undefined,
                    toolChoice: resolvedToolChoice ?? (finalTools && finalTools.length > 0 ? "auto" : undefined),
                };

                // First call to the model
                let result = await provider.chat(
                    model,
                    enrichedMessages as any,
                    options,
                );

                // ── Tool call roundtrip ───────────────────────────────────
                let toolRoundtripCount = 0;
                const maxRoundtrips = 5; // safety limit

                while (
                    result.toolCalls &&
                    result.toolCalls.length > 0 &&
                    toolRoundtripCount < maxRoundtrips
                ) {
                    telemetry.toolCallsExecuted += result.toolCalls.length;
                    metricsCollector.recordToolCall(result.toolCalls.length);
                    toolRoundtripCount++;

                    // Execute each tool call
                    const toolResults = toolExecutor
                        ? await toolExecutor.executeBatch(
                            toolRegistry?.getActiveTools(model) ?? [],
                            result.toolCalls.map((tc) => ({
                                id: tc.id,
                                name: tc.function.name,
                                args: JSON.parse(tc.function.arguments),
                            })),
                        )
                        : [];

                    // Check for tool execution failures
                    const failedResults = toolResults.filter((tr) => !tr.success);
                    if (failedResults.length > 0) {
                        recordDegradation(
                            telemetry,
                            "tool-execution",
                            `${failedResults.length} tool(s) failed: ${failedResults.map((f) => f.name).join(", ")}`,
                        );
                    }

                    // Append assistant message with tool_calls to the history
                    const assistantMsg: any = {
                        role: "assistant",
                        content: result.content ?? null,
                        tool_calls: result.toolCalls,
                    };
                    enrichedMessages = [...enrichedMessages, assistantMsg];

                    // Append each tool result as a tool-role message
                    const toolMsgMap = new Map(toolResults.map((tr) => [tr.toolCallId, tr]));
                    for (const tc of result.toolCalls) {
                        const tr = toolMsgMap.get(tc.id);
                        enrichedMessages = [
                            ...enrichedMessages,
                            {
                                role: "tool" as const,
                                tool_call_id: tc.id,
                                content: tr
                                    ? tr.success
                                        ? tr.content
                                        : `Error: ${tr.error}`
                                    : "Tool execution failed: no result",
                            },
                        ];
                    }

                    // Second call to model with tool results — use same tool_choice resolution
                    result = await provider.chat(model, enrichedMessages as any, {
                        maxTokens: providerMaxTokens,
                        temperature: body.temperature,
                        tools: finalTools,
                        toolChoice: resolvedToolChoice ?? ("auto" as any),
                    });
                }

                telemetry.providerLatencyMs = Date.now() - startTime;
                metricsCollector.recordRequest(model, telemetry.providerLatencyMs, "200");

                // Fire-and-forget: transcript + Qdrant index
                emitTelemetry(telemetry, request.log);
                storeTranscript({
                    requestId,
                    tenantId,
                    projectId,
                    model,
                    messages: flattenMessages,
                    responseContent: result.content,
                    totalTokens: result.usage?.totalTokens ?? 0,
                    streaming: false,
                });
                indexToQdrant(
                    vectorStore,
                    requestId,
                    model,
                    flattenMessages,
                    result.content,
                    tenantId,
                    projectId,
                );

                // Fire-and-forget: entity extraction (GraphRAG)
                if (entityStore) {
                    const conversationText = [
                        ...flattenMessages.map((m) => m.content),
                        result.content,
                    ]
                        .filter(Boolean)
                        .join("\n\n");
                    entityStore.extractAndStore(conversationText, tenantId, projectId).catch((err: Error) => {
                        console.error("Entity extraction failed:", err.message);
                        recordDegradation(telemetry, "entity-extraction", err.message);
                    });
                }

                return {
                    id: result.id,
                    object: "chat.completion",
                    created: Math.floor(Date.now() / 1000),
                    model: result.model,
                    choices: [
                        {
                            index: 0,
                            message: {
                                role: "assistant",
                                content: result.content,
                            },
                            finish_reason: result.finishReason,
                        },
                    ],
                    usage: result.usage,
                    _telemetrySumary: telemetrySummary(telemetry),
                    _memoryContext: memorySnippets
                        ? {
                              hitCount: telemetry.retrievalHits,
                              snippets: memorySnippets,
                          }
                        : null,
                };
            }
        } catch (error) {
            const err = error as Error;
            console.error(`[${requestId}] provider error:`, err.message);

            const statusCode = err.message.includes("401") ? 502 : 502;
            metricsCollector.recordRequest(model, Date.now() - startTime, String(statusCode));
            recordDegradation(telemetry, "provider", err.message);

            return reply.status(statusCode).send({
                error: {
                    message: "Upstream provider error",
                    type: "upstream_error",
                    request_id: requestId,
                },
            });
        }
    });

    // ── GET /v1/models ─────────────────────────────────────────────────
    app.get("/v1/models", async (_request, _reply) => {
        const models: Array<{ id: string; object: string; created: number; owned_by: string }> = [
            {
                id: config.openaiDefaultModel,
                object: "model",
                created: Math.floor(Date.now() / 1000),
                owned_by: "system",
            },
        ];

        // Add Anthropic models if that provider is configured
        if (config.anthropicApiKey) {
            models.push(
                {
                    id: "claude-sonnet-4-20250514",
                    object: "model",
                    created: Math.floor(Date.now() / 1000),
                    owned_by: "anthropic",
                },
                {
                    id: "claude-3-5-haiku-20241022",
                    object: "model",
                    created: Math.floor(Date.now() / 1000),
                    owned_by: "anthropic",
                },
                {
                    id: "claude-opus-4-20250514",
                    object: "model",
                    created: Math.floor(Date.now() / 1000),
                    owned_by: "anthropic",
                },
            );
        }

        return {
            object: "list",
            data: models,
        };
    });
}