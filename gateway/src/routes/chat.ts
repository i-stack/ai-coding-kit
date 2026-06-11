import type { FastifyInstance } from "fastify";
import type { OpenAIProvider } from "../provider/openai.js";
import type { GatewayConfig } from "../config.js";
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

async function storeTranscript(
  store: TranscriptStore,
): Promise<void> {
  try {
    const { insertConversation, insertMessage, finalizeConversation, generateId } = await import(
      "../db/transcript.js"
    );
    const { getPool } = await import("../db/index.js");

    // Check if pool is available without throwing
    try {
      getPool();
    } catch {
      return; // DB not initialized, skip silently
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

    // Store each user message
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

    // Store assistant response
    await insertMessage({
      id: generateId(),
      conversationId,
      turnIndex: store.messages.length,
      role: "assistant",
      content: store.responseContent,
    });

    await finalizeConversation(conversationId, store.totalTokens);
  } catch (err) {
    // Transcript storage is best-effort — never fail the request
    console.error("Failed to store transcript:", (err as Error).message);
  }
}

/**
 * Schema for the incoming OpenAI-compatible chat completion request.
 * We only validate the fields we need; extra fields are passed through.
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
): void {
  // ── POST /v1/chat/completions ──────────────────────────────────────
  app.post("/v1/chat/completions", async (request, reply) => {
    const startTime = Date.now();
    const requestId = crypto.randomUUID();

    const body = request.body as ChatCompletionRequest;

    // 1. Normalize: extract fields with sensible defaults
    const model = body.model ?? config.openaiDefaultModel;
    const messages = body.messages;
    const stream = body.stream ?? false;

    // Telemetry snapshot (before processing)
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
    };

    // Ensure content is a string for transcript storage
    const flattenMessages = messages.map((m) => ({
      role: m.role,
      content:
        typeof m.content === "string" ? m.content : JSON.stringify(m.content),
    }));

    // Map tool_choice (OpenAI-compatible format → SDK format)
    const toolChoice = body.tool_choice as any;

    const options = {
      maxTokens: body.max_tokens,
      temperature: body.temperature,
      tools: body.tools as any,
      toolChoice,
    };

    try {
      if (stream) {
        // ── Streaming path ──────────────────────────────────────────
        reply.raw.writeHead(200, {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "x-request-id": requestId,
        });

        const chunkIter = provider.chatStreaming(model, messages as any, options);
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
          } else if (chunk.type === "done" && chunk.finishReason && !usageEmitted) {
            // Final chunk with finish reason but no usage
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

        // Store transcript after stream ends (fire-and-forget)
        storeTranscript({
          requestId,
          model,
          messages: flattenMessages,
          responseContent: contentParts.join(""),
          totalTokens,
          streaming: true,
        });
      } else {
        // ── Non-streaming path ──────────────────────────────────────
        const result = await provider.chat(model, messages as any, options);

        telemetry.providerLatencyMs = Date.now() - startTime;

        // Store transcript (fire-and-forget)
        storeTranscript({
          requestId,
          model,
          messages: flattenMessages,
          responseContent: result.content,
          totalTokens: result.usage?.totalTokens ?? 0,
          streaming: false,
        });

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

      // Do NOT return raw error details to client (avoid leaking API keys)
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

  // ── GET /v1/models (informational, returns configured model) ──────
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