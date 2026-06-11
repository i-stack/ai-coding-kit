import OpenAI from "openai";
import type { GatewayConfig } from "../config.js";

export interface ProviderResult {
  id: string;
  model: string;
  content: string | null;
  finishReason: OpenAI.Chat.Completions.ChatCompletion.Choice["finish_reason"];
  toolCalls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface ProviderStreamChunk {
  type: "delta" | "done";
  delta?: string;
  finishReason?: string | null;
  usage?: ProviderResult["usage"];
}

/**
 * Thin wrapper over the OpenAI SDK for the MVP.
 *
 * In later iterations, this will be generalised into a ProviderRouter
 * that handles multiple upstream backends (Anthropic, local models, etc.).
 */
export class OpenAIProvider {
  private client: OpenAI;

  constructor(config: GatewayConfig) {
    this.client = new OpenAI({
      apiKey: config.openaiApiKey,
      baseURL: config.openaiBaseUrl,
    });
  }

  /**
   * Non-streaming chat completion.
   */
  async chat(
    model: string,
    messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
    options?: {
      maxTokens?: number;
      temperature?: number;
      tools?: OpenAI.Chat.Completions.ChatCompletionTool[];
      toolChoice?: OpenAI.Chat.Completions.ChatCompletionToolChoiceOption;
    },
  ): Promise<ProviderResult> {
    const response = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: options?.maxTokens,
      temperature: options?.temperature,
      tools: options?.tools as any,
      tool_choice: options?.toolChoice,
      stream: false,
    });

    const choice = response.choices[0];
    const toolCalls = choice.message.tool_calls?.map((tc) => ({
      id: tc.id,
      type: "function" as const,
      function: {
        name: tc.function.name,
        arguments: tc.function.arguments,
      },
    }));

    return {
      id: response.id,
      model: response.model,
      content: choice.message.content,
      finishReason: choice.finish_reason ?? null,
      toolCalls,
      usage: response.usage
        ? {
            promptTokens: response.usage.prompt_tokens,
            completionTokens: response.usage.completion_tokens,
            totalTokens: response.usage.total_tokens,
          }
        : undefined,
    };
  }

  /**
   * Streaming chat completion. Yields ProviderStreamChunk.
   */
  async *chatStreaming(
    model: string,
    messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
    options?: {
      maxTokens?: number;
      temperature?: number;
      tools?: OpenAI.Chat.Completions.ChatCompletionTool[];
      toolChoice?: OpenAI.Chat.Completions.ChatCompletionToolChoiceOption;
    },
  ): AsyncGenerator<ProviderStreamChunk> {
    const stream = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: options?.maxTokens,
      temperature: options?.temperature,
      tools: options?.tools as any,
      tool_choice: options?.toolChoice,
      stream: true,
      stream_options: { include_usage: true },
    });

    for await (const chunk of stream) {
      const choice = chunk.choices?.[0];
      if (choice?.delta?.content) {
        yield {
          type: "delta",
          delta: choice.delta.content,
          finishReason: choice.finish_reason ?? null,
        };
      } else if (choice?.finish_reason) {
        yield {
          type: "done",
          finishReason: choice.finish_reason,
        };
      }

      // Usage comes in the final chunk for streaming
      if (chunk.usage) {
        yield {
          type: "done",
          finishReason: "stop",
          usage: {
            promptTokens: chunk.usage.prompt_tokens,
            completionTokens: chunk.usage.completion_tokens,
            totalTokens: chunk.usage.total_tokens,
          },
        };
      }
    }
  }
}