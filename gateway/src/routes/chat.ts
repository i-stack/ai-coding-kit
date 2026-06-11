import type { FastifyInstance } from "fastify";
import type { OpenAIProvider } from "../provider/openai.js";
import type { GatewayConfig } from "../config.js";
import type { VectorStore } from "../vector/store.js";
import type { ToolRegistry } from "../tool/registry.js";
import type { ToolExecutorEngine } from "../tool/executor.js";
import { getSimplifiedSchema } from "../tool/simplify.js";
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
      tenantId: "default",
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
): Promise<void> {
  if (!vectorStore) return;

  try {
    for (const msg of userMessages) {
      if (!msg.content) continue;
      await vectorStore.indexMessage({
        id: crypto.randomUUID(),
        text: msg.content,
        kind: "user_message",
        tenantId: "default",
        sourceMessageId: crypto.randomUUID(),
        conversationId: requestId,
      });
    }

    if (responseContent) {
      await vectorStore.indexMessage({
        id: crypto.randomUUID(),
        text: responseContent,
        kind: "assistant_message",
        tenantId: "default",
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

// ── Model-specific tool count cap ──────────────────────────────────
function maxToolsForModel(model: string): number {
  const lower = model.toLowerCase();
  if (lower.includes("gpt-3.5") || lower.includes("gpt-4-turbo")) return 10;
  if (lower.includes("claude-3-haiku") || lower.includes("claude-3-sonnet")) return 10;
  if (lower.includes("claude-3-opus") || lower.includes("claude-sonnet-4")) return 20;
  if (lower.includes("gpt-4o") || lower.includes("gpt-4.1")) return 20;
  return 20; // default generous cap
}

export function registerChatRoutes(
  app: FastifyInstance,
  provider: OpenAIProvider,
  config: GatewayConfig,
  vectorStore?: VectorStore,
  toolRegistry?: ToolRegistry,
  toolExecutor?: ToolExecutorEngine,
): void {
  // ── POST /v1/chat/completions ──────────────────────────────────────
  app.post("/v1/chat/completions", async (request, reply) => {
    const startTime = Date.now();
    const requestId = crypto.randomUUID();

    const body = request.body as ChatCompletionRequest;
    const model = body.model ?? config.openaiDefaultModel;
    const messages = body.messages;
    const stream = body.stream ?? false;

    const telemetry = createTelemetry({
      requestId,
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
      // ── Step 1: Retrieve relevant memories from Qdrant ─────────────
      let retrievedContext: string | undefined;
      if (vectorStore) {
        try {
          const lastUserMsg = [...flattenMessages]
            .reverse()
            .find((m) => m.role === "user");
          if (lastUserMsg?.content) {
            const results = await vectorStore.search(lastUserMsg.content, {
              limit: 3,
              tenantId: "default",
            });
            if (results.length > 0) {
              retrievedContext = results
                .map(
                  (r) => `[memory (relevance=${r.score.toFixed(2)})] ${r.payload.text}`,
                )
                .join("\n\n");
              telemetry.retrievalHits = results.length;
              metricsCollector.recordRetrievalHits(results.length);
            }
          }
        } catch (err) {
          recordDegradation(telemetry, "memory-retrieval", (err as Error).message);
          console.error("Qdrant search error:", (err as Error).message);
        }
      }

      // ── Step 2: Inject tools from the registry ─────────────────────
      let enrichedMessages: any[] = messages;
      if (retrievedContext) {
        enrichedMessages = [
          {
            role: "system" as const,
            content: `Relevant context from previous conversations:\n\n${retrievedContext}`,
          },
          ...messages,
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

      // Cap tools per model
      const toolCap = maxToolsForModel(model);
      const finalTools: OpenAICompatibleTool[] | undefined = allTools
        ? allTools.slice(0, toolCap)
        : undefined;
      telemetry.injectedTools = finalTools
        ? finalTools.length - (clientTools?.length ?? 0)
        : 0;

      // ── Step 3: Main completion (with potential tool roundtrip) ───
      if (stream) {
        // Streaming path: inject tools with per-model tool_choice
        const options = {
          maxTokens: body.max_tokens,
          temperature: body.temperature,
          tools: finalTools && finalTools.length > 0 ? finalTools : undefined,
          toolChoice: resolvedToolChoice ?? (finalTools && finalTools.length > 0 ? "auto" : undefined),
        };

        reply.raw.writeHead(200, {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "x-request-id": requestId,
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
          model,
          messages: flattenMessages,
          responseContent: fullContent,
          totalTokens,
          streaming: true,
        });
        indexToQdrant(vectorStore, requestId, model, flattenMessages, fullContent);
      } else {
        // ── Non-streaming: support tool call roundtrip ─────────────
        const options = {
          maxTokens: body.max_tokens,
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
            maxTokens: body.max_tokens,
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
        );

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
    return {
      object: "list",
      data: [
        {
          id: config.openaiDefaultModel,
          object: "model",
          created: Math.floor(Date.now() / 1000),
          owned_by: "system",
        },
      ],
    };
  });
}