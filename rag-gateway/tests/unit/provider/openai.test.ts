import { describe, it, expect, vi, beforeEach } from "vitest";
import { OpenAIProvider } from "../../../src/provider/openai.js";
import type { NormalizedMessage, NormalizedTool, ToolChoice } from "../../../src/types.js";
import type { GatewayConfig } from "../../../src/config.js";

const mockConfig = {
    openaiApiKey: "test-key",
    openaiBaseUrl: "https://api.openai.com/v1",
    openaiDefaultModel: "gpt-4o",
} as unknown as GatewayConfig;

describe("OpenAIProvider", () => {
    let provider: OpenAIProvider;

    beforeEach(() => {
        provider = new OpenAIProvider(mockConfig);
    });

    it("should store config on construction", () => {
        expect((provider as any).client).toBeDefined();
    });

    it("should format system message correctly via chat()", async () => {
        const messages: NormalizedMessage[] = [
            { role: "system", content: "You are a helpful assistant." },
            { role: "user", content: "Hello!" },
        ];

        // Mock the OpenAI SDK client response
        const mockCreate = vi.fn();
        (provider as any).client = {
            chat: { completions: { create: mockCreate } },
        };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123",
            model: "gpt-4o",
            choices: [{ message: { content: "Hello!" }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        const result = await provider.chat("gpt-4o", messages);

        expect(mockCreate).toHaveBeenCalledWith(
            expect.objectContaining({
                messages: expect.arrayContaining([
                    expect.objectContaining({ role: "system", content: "You are a helpful assistant." }),
                    expect.objectContaining({ role: "user", content: "Hello!" }),
                ]),
            }),
        );
        expect(result.content).toBe("Hello!");
    });

    it("should format user message with content parts including image_url", async () => {
        const messages: NormalizedMessage[] = [
            {
                role: "user",
                content: [
                    { type: "text", text: "What's in this image?" },
                    { type: "image_url", image_url: { url: "https://example.com/img.png", detail: "auto" } },
                ],
            },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123", model: "gpt-4o",
            choices: [{ message: { content: "An image." }, finish_reason: "stop" }],
            usage: { prompt_tokens: 20, completion_tokens: 5, total_tokens: 25 },
        });

        await provider.chat("gpt-4o", messages);
        const callArg = mockCreate.mock.calls[0][0];
        const userMsg = callArg.messages[0];
        expect(userMsg.role).toBe("user");
        expect(Array.isArray(userMsg.content)).toBe(true);
        expect(userMsg.content[0].type).toBe("text");
        expect(userMsg.content[1].type).toBe("image_url");
        expect(userMsg.content[1].image_url.url).toBe("https://example.com/img.png");
    });

    it("should format tool message correctly", async () => {
        const messages: NormalizedMessage[] = [
            { role: "tool", content: '{"result":"ok"}', tool_call_id: "call_123" },
        ];
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123", model: "gpt-4o",
            choices: [{ message: { content: "Done." }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        await provider.chat("gpt-4o", messages);
        const callArg = mockCreate.mock.calls[0][0];
        const toolMsg = callArg.messages[0];
        expect(toolMsg.role).toBe("tool");
        expect(toolMsg.tool_call_id).toBe("call_123");
    });

    it("should format assistant message with tool_calls", async () => {
        const messages: NormalizedMessage[] = [
            {
                role: "assistant",
                content: "Let me check...",
                tool_calls: [
                    { id: "call_abc", type: "function", function: { name: "get_time", arguments: "{}" } },
                ],
            },
        ];
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123", model: "gpt-4o",
            choices: [{ message: { content: "Done." }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        await provider.chat("gpt-4o", messages);
        const callArg = mockCreate.mock.calls[0][0];
        const assistantMsg = callArg.messages[0];
        expect(assistantMsg.role).toBe("assistant");
        expect(assistantMsg.tool_calls).toHaveLength(1);
    });

    it("should convert NormalizedTool[] to OpenAI tool format", async () => {
        const tools: NormalizedTool[] = [
            {
                type: "function",
                function: { name: "test_tool", description: "A test tool", parameters: { type: "object", properties: {} } },
            },
        ];
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123", model: "gpt-4o",
            choices: [{ message: { content: "Done." }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        await provider.chat("gpt-4o", [{ role: "user", content: "hi" }], { tools });
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.tools[0].function.name).toBe("test_tool");
    });

    it("should pass through toolChoice 'none', 'auto', 'required' and function choice", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123", model: "gpt-4o",
            choices: [{ message: { content: "Done." }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        // Test each tool_choice type
        for (const tc of ["none", "auto", "required", { type: "function", function: { name: "test" } }] as ToolChoice[]) {
            await provider.chat("gpt-4o", [{ role: "user", content: "hi" }], { toolChoice: tc });
            const callArg = mockCreate.mock.calls[mockCreate.mock.calls.length - 1][0];
            expect(callArg.tool_choice).toBeDefined();
        }
    });

    it("should return correct ProviderResult shape", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123",
            model: "gpt-4o",
            choices: [{ message: { content: "Hello!", tool_calls: undefined }, finish_reason: "stop" }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        const result = await provider.chat("gpt-4o", [{ role: "user", content: "hi" }]);
        expect(result).toHaveProperty("id");
        expect(result).toHaveProperty("model");
        expect(result).toHaveProperty("content");
        expect(result).toHaveProperty("finishReason");
        expect(result.usage).toBeDefined();
        expect(result.usage!.totalTokens).toBe(15);
    });

    it("should parse tool_calls from response", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { chat: { completions: { create: mockCreate } } };
        mockCreate.mockResolvedValue({
            id: "chatcmpl-123",
            model: "gpt-4o",
            choices: [{
                message: {
                    content: null,
                    tool_calls: [{ id: "call_1", type: "function", function: { name: "get_time", arguments: "{}" } }],
                },
                finish_reason: "tool_calls",
            }],
            usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        });

        const result = await provider.chat("gpt-4o", [{ role: "user", content: "What time is it?" }]);
        expect(result.toolCalls).toBeDefined();
        expect(result.toolCalls).toHaveLength(1);
        expect(result.toolCalls![0].function.name).toBe("get_time");
        expect(result.finishReason).toBe("tool_calls");
    });
});