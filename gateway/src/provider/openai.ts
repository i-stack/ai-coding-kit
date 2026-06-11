import OpenAI from "openai";
import type { GatewayConfig } from "../config.js";
import type { Provider, ProviderResult, ProviderStreamChunk, ProviderChatOptions } from "./types.js";
import type { NormalizedMessage, NormalizedTool, ToolChoice } from "../types.js";

/**
 * OpenAI-compatible provider.
 *
 * Handles both direct OpenAI API calls and any OpenAI-compatible proxy
 * (DeepSeek, local LLM, etc.) via configurable base URL.
 */
export class OpenAIProvider implements Provider {
    readonly name = "openai";
    private client: OpenAI;

    constructor(config: GatewayConfig) {
        this.client = new OpenAI({
            apiKey: config.openaiApiKey,
            baseURL: config.openaiBaseUrl,
        });
    }

    // ── Format adapters ──────────────────────────────────────────────────

    private toOpenAIMessages(messages: NormalizedMessage[]): OpenAI.Chat.Completions.ChatCompletionMessageParam[] {
        return messages.map((m) => {
            const content: string | OpenAI.Chat.Completions.ChatCompletionContentPart[] =
                typeof m.content === "string"
                    ? m.content
                    : Array.isArray(m.content)
                        ? m.content.map((p) => {
                            if (p.type === "image_url") {
                                return { type: "image_url", image_url: p.image_url! } as OpenAI.Chat.Completions.ChatCompletionContentPart;
                            }
                            return { type: "text", text: p.text ?? "" } as OpenAI.Chat.Completions.ChatCompletionContentPart;
                        })
                        : "";

            if (m.role === "system") {
                return { role: "system", content: content as string, name: m.name } satisfies OpenAI.Chat.Completions.ChatCompletionSystemMessageParam;
            }
            if (m.role === "user") {
                return { role: "user", content, name: m.name } satisfies OpenAI.Chat.Completions.ChatCompletionUserMessageParam;
            }
            if (m.role === "tool") {
                return {
                    role: "tool",
                    content: content as string,
                    tool_call_id: m.tool_call_id ?? "",
                } satisfies OpenAI.Chat.Completions.ChatCompletionToolMessageParam;
            }
            // assistant
            return {
                role: "assistant",
                content: content as string | null,
                tool_calls: m.tool_calls as OpenAI.Chat.Completions.ChatCompletionMessageToolCall[] | undefined,
            } satisfies OpenAI.Chat.Completions.ChatCompletionAssistantMessageParam;
        });
    }

    private toOpenAITools(tools?: NormalizedTool[]): OpenAI.Chat.Completions.ChatCompletionTool[] | undefined {
        if (!tools || tools.length === 0) return undefined;
        return tools.map((t) => ({
            type: "function" as const,
            function: {
                name: t.function.name,
                description: t.function.description ?? "",
                parameters: t.function.parameters,
            },
        }));
    }

    private toToolChoice(tc?: ToolChoice): OpenAI.Chat.Completions.ChatCompletionToolChoiceOption | undefined {
        if (tc === undefined) return undefined;
        if (typeof tc === "string") {
            // "none" | "auto" | "required" → already OpenAI-compatible
            return tc;
        }
        // { type: "function", function: { name } }
        return tc as OpenAI.Chat.Completions.ChatCompletionToolChoiceOption;
    }

    // ── Provider interface implementation ────────────────────────────────

    async chat(
        model: string,
        messages: NormalizedMessage[],
        options?: ProviderChatOptions,
    ): Promise<ProviderResult> {
        const openaiMessages = this.toOpenAIMessages(messages);
        const tools = this.toOpenAITools(options?.tools);
        const toolChoice = this.toToolChoice(options?.toolChoice);

        const response = await this.client.chat.completions.create({
            model,
            messages: openaiMessages,
            max_tokens: options?.maxTokens,
            temperature: options?.temperature,
            tools: tools as any,
            tool_choice: toolChoice,
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

    async *chatStreaming(
        model: string,
        messages: NormalizedMessage[],
        options?: ProviderChatOptions,
    ): AsyncGenerator<ProviderStreamChunk> {
        const openaiMessages = this.toOpenAIMessages(messages);
        const tools = this.toOpenAITools(options?.tools);
        const toolChoice = this.toToolChoice(options?.toolChoice);

        const stream = await this.client.chat.completions.create({
            model,
            messages: openaiMessages,
            max_tokens: options?.maxTokens,
            temperature: options?.temperature,
            tools: tools as any,
            tool_choice: toolChoice,
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