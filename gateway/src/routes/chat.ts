import type { FastifyInstance } from "fastify";
import type { OpenAIProvider } from "../provider/openai.js";
import type { GatewayConfig } from "../config.js";
import type { VectorStore } from "../vector/store.js";
import crypto from "node:crypto";

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
    // Index each user message as a chunk
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

    // Index assistant response
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

/**
 * Schema for the incoming OpenAI-compatible chat completion request.
 */
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

export function registerChatRoutes(
  app: FastifyInstance,
  provider: OpenAIProvider,
  config: GatewayConfig,
  vectorStore?: VectorStore,
): void {
  // ── POST /v1/chat/completions ──────────────────────────────────────
  app.post("/v1/chat/completions", async (request, reply) => {
    const startTime = Date.now();
    const requestId = crypto.randomUUID();

    const body = request.body as ChatCompletionRequest;

    const model = body.model ?? config.openaiDefaultModel;
    const messages = body.messages;
    const stream = body.stream ?? false;

    const telemetry = {
      requestId,
      tenantId: "default",
      client: "unknown" as const,
      model,
      messageCount: messages.length,
      toolCount: body.tools?.length ?? 0,
      stream,
      providerLatencyMs: 0,
      createdAt: new Date(),
      retrievalHits: 0,
    };

    const flattenMessages = messages.map((m) => ({
      role: m.role,
      content:
        typeof m.content === "string" ? m.content : JSON.stringify(m.content),
    }));

    const toolChoice = body.tool_choice as any;

    const options = {
      maxTokens: body.max_tokens,
      temperature: body.temperature,
      tools: body.tools as any,
      toolChoice,
    };

    try {
      // ── Optional: retrieve relevant memories from Qdrant ─────────────
      let retrievedContext: string | undefined;
      if (vectorStore) {
        try {
          // Use the last user message as the query
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
            }
          }
        } catch (err) {
          console.error("Qdrant search error:", (err as Error).message);
        }
      }

      // ── Build enriched messages ─────────────────────────────────────
      let enrichedMessages = messages;
      if (retrievedContext) {
        enrichedMessages = [
          {
            role: "system" as const,
            content: `Relevant context from previous conversations:\n\n${retrievedContext}`,
          },
          ...messages,
        ];
      }

      if (stream) {
        // ── Streaming path ──────────────────────────────────────────
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

        for await (const chunk of chunkIter) {
          if (chunk.type === "delta") {
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

        // Fire-and-forget: transcript + Qdrant index
        const fullContent = contentParts.join("");
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
        // ── Non-streaming path ──────────────────────────────────────
        const result = await provider.chat(
          model,
          enrichedMessages as any,
          options,
        );

        telemetry.providerLatencyMs = Date.now() - startTime;

        // Fire-and-forget: transcript + Qdrant index
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
          _telemetry: telemetry,
        };
      }
    } catch (error) {
      const err = error as Error;
      console.error(`[${requestId}] provider error:`, err.message);

      const statusCode = err.message.includes("401") ? 502 : 502;
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