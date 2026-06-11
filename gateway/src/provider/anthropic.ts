import Anthropic from "@anthropic-ai/sdk";
import type {
  Provider,
  ProviderResult,
  ProviderStreamChunk,
  ProviderChatOptions,
} from "./types.js";
import type {
  NormalizedMessage,
  NormalizedTool,
  ToolChoice,
} from "../types.js";

/**
 * Anthropic provider — connects to the Anthropic Messages API.
 *
 * Handles format translation between the gateway's NormalizedMessage
 * and Anthropic's own message format, including:
 *   - Extracting system messages into the separate `system` param
 *   - Translating `tool` role messages to `tool_result` content blocks
 *   - Translating assistant `tool_calls` to `tool_use` content blocks
 *   - Mapping tools schemas (Anthropic uses `input_schema` directly)
 *   - Mapping stop_reason to finishReason
 */
export class AnthropicProvider implements Provider {
  readonly name = "anthropic";
  private client: Anthropic;

  constructor(config: { anthropicApiKey: string; anthropicBaseUrl?: string }) {
    this.client = new Anthropic({
      apiKey: config.anthropicApiKey,
      baseURL: config.anthropicBaseUrl,
    });
  }

  // ── Format adapters ──────────────────────────────────────────────────

  /**
   * Convert NormalizedMessage[] to Anthropic's message format.
   *
   * Anthropic's API separates `system` from the messages array, and uses
   * content blocks for tool results and tool use rather than separate
   * message-level fields.
   */
  private toAnthropicParams(
    messages: NormalizedMessage[],
  ): {
    system?: string;
    messages: Anthropic.MessageParam[];
  } {
    let system: string | undefined;

    // Extract system message (first system role message, if any)
    const nonSystemMessages = messages.filter((m) => {
      if (m.role === "system" && !system) {
        system = typeof m.content === "string" ? m.content : JSON.stringify(m.content);
        return false;
      }
      return true;
    });

    const result: Anthropic.MessageParam[] = [];

    for (const m of nonSystemMessages) {
      if (m.role === "user") {
        // user messages → Anthropic user role
        if (typeof m.content === "string") {
          result.push({ role: "user", content: m.content });
        } else if (Array.isArray(m.content)) {
          // Check if any part is image_url
          const hasImage = m.content.some((p) => p.type === "image_url");
          if (hasImage) {
            const blocks: Anthropic.ContentBlockParam[] = m.content.map((p) => {
              if (p.type === "image_url") {
                return {
                  type: "image",
                  source: {
                    type: "url",
                    url: p.image_url!.url,
                  },
                } as Anthropic.ImageBlockParam;
              }
              return { type: "text", text: p.text ?? "" };
            });
            result.push({ role: "user", content: blocks });
          } else {
            const text = m.content.map((p) => p.text ?? "").join("\n");
            result.push({ role: "user", content: text });
          }
        } else {
          result.push({ role: "user", content: "" });
        }
      } else if (m.role === "tool") {
        // tool role → user role with tool_result content block
        result.push({
          role: "user",
          content: [
            {
              type: "tool_result",
              tool_use_id: m.tool_call_id ?? "",
              content: m.content
                ? typeof m.content === "string"
                  ? m.content
                  : JSON.stringify(m.content)
                : "",
            },
          ],
        });
      } else if (m.role === "assistant") {
        const blocks: Anthropic.ContentBlockParam[] = [];

        // Add text content if present
        if (m.content && typeof m.content === "string") {
          blocks.push({ type: "text", text: m.content });
        } else if (m.content && Array.isArray(m.content)) {
          const textParts = m.content.filter((p) => p.type === "text");
          if (textParts.length > 0) {
            blocks.push({
              type: "text",
              text: textParts.map((p) => p.text ?? "").join("\n"),
            });
          }
        }

        // Add tool_use blocks if there are tool calls
        if (m.tool_calls && m.tool_calls.length > 0) {
          for (const tc of m.tool_calls) {
            blocks.push({
              type: "tool_use",
              id: tc.id,
              name: tc.function.name,
              input: JSON.parse(tc.function.arguments),
            });
          }
        }

        result.push({ role: "assistant", content: blocks });
      }
    }

    return { system, messages: result };
  }

  /**
   * Convert NormalizedTool[] to Anthropic's Tool format.
   *
   * Anthropic uses `input_schema` directly instead of the OpenAI-style
   * `{ type: "function", function: { parameters } }` wrapper.
   */
  private toAnthropicTools(
    tools?: NormalizedTool[],
  ): Anthropic.Tool[] | undefined {
    if (!tools || tools.length === 0) return undefined;
    return tools.map((t) => ({
      name: t.function.name,
      description: t.function.description ?? "",
      input_schema: t.function.parameters as Anthropic.Tool["input_schema"],
    }));
  }

  /**
   * Convert ToolChoice to Anthropic tool_choice format.
   *
   * Anthropic uses { type: "auto" | "any" | "tool", name?: string }.
   * OpenAI-style { type: "function", function: { name } } maps to { type: "tool", name }.
   */
  private toAnthropicToolChoice(
    tc?: ToolChoice,
  ): Anthropic.MessageCreateParams["tool_choice"] {
    if (tc === undefined) return undefined;
    if (tc === "none") return { type: "none" };
    if (tc === "auto") return { type: "auto" };
    if (tc === "required") return { type: "any" };
    // { type: "function", function: { name } } → { type: "tool", name }
    if (typeof tc === "object" && "function" in tc) {
      return { type: "tool", name: tc.function.name };
    }
    return { type: "auto" };
  }

  /**
   * Map Anthropic stop_reason to a finishReason string.
   */
  private mapFinishReason(
    stopReason: string | null | undefined,
  ): string | null {
    switch (stopReason) {
      case "end_turn":
      case "stop_sequence":
        return "stop";
      case "tool_use":
        return "tool_calls";
      case "max_tokens":
        return "length";
      default:
        return stopReason ?? null;
    }
  }

  /**
   * Extract tool calls from Anthropic content blocks.
   */
  private extractToolCalls(
    content: Anthropic.ContentBlock[],
  ): ProviderResult["toolCalls"] {
    const toolCalls: ProviderResult["toolCalls"] = [];
    for (const block of content) {
      if (block.type === "tool_use") {
        toolCalls!.push({
          id: block.id,
          type: "function",
          function: {
            name: block.name,
            arguments: JSON.stringify(block.input),
          },
        });
      }
    }
    return toolCalls.length > 0 ? toolCalls : undefined;
  }

  /**
   * Extract text content from Anthropic content blocks.
   */
  private extractTextContent(
    content: Anthropic.ContentBlock[],
  ): string | null {
    const textParts: string[] = [];
    for (const block of content) {
      if (block.type === "text") {
        textParts.push(block.text);
      }
    }
    return textParts.length > 0 ? textParts.join("") : null;
  }

  // ── Provider interface implementation ────────────────────────────────

  async chat(
    model: string,
    messages: NormalizedMessage[],
    options?: ProviderChatOptions,
  ): Promise<ProviderResult> {
    const { system, messages: anthropicMessages } =
      this.toAnthropicParams(messages);
    const tools = this.toAnthropicTools(options?.tools);
    const toolChoice = this.toAnthropicToolChoice(options?.toolChoice);

    const response = await this.client.messages.create({
      model,
      system: system || undefined,
      messages: anthropicMessages,
      max_tokens: options?.maxTokens ?? 4096,
      temperature: options?.temperature,
      tools,
      tool_choice: toolChoice,
    });

    return {
      id: response.id,
      model: response.model,
      content: this.extractTextContent(response.content),
      finishReason: this.mapFinishReason(response.stop_reason),
      toolCalls: this.extractToolCalls(response.content),
      usage: {
        promptTokens: response.usage.input_tokens,
        completionTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens,
      },
    };
  }

  async *chatStreaming(
    model: string,
    messages: NormalizedMessage[],
    options?: ProviderChatOptions,
  ): AsyncGenerator<ProviderStreamChunk> {
    const { system, messages: anthropicMessages } =
      this.toAnthropicParams(messages);
    const tools = this.toAnthropicTools(options?.tools);
    const toolChoice = this.toAnthropicToolChoice(options?.toolChoice);

    const stream = this.client.messages.stream({
      model,
      system: system || undefined,
      messages: anthropicMessages,
      max_tokens: options?.maxTokens ?? 4096,
      temperature: options?.temperature,
      tools,
      tool_choice: toolChoice,
    });

    // Accumulated text content (for potential tool_use blocks found during streaming)
    let textContent = "";

    try {
      for await (const event of stream) {
        if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
          textContent += event.delta.text;
          yield {
            type: "delta",
            delta: event.delta.text,
          };
        } else if (event.type === "message_delta") {
          // Final message event — includes usage and stop_reason
          const usage = event.usage
            ? {
                promptTokens: event.usage.input_tokens ?? 0,
                completionTokens: event.usage.output_tokens,
                totalTokens: (event.usage.input_tokens ?? 0) + event.usage.output_tokens,
              }
            : undefined;

          yield {
            type: "done",
            finishReason: this.mapFinishReason(event.delta.stop_reason),
            usage,
          };
        }
      }
    } finally {
      // Ensure the underlying stream is cleaned up
      stream.controller.abort();
    }
  }
}