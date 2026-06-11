import { describe, it, expect, beforeEach, vi } from "vitest";
import { AnthropicProvider } from "../../../src/provider/anthropic.js";
import type { NormalizedMessage, NormalizedTool, ToolChoice } from "../../../src/types.js";

const mockConfig = {
    anthropicApiKey: "test-anthropic-key",
    anthropicBaseUrl: "https://api.anthropic.com",
};

describe("AnthropicProvider", () => {
    let provider: AnthropicProvider;

    beforeEach(() => {
        provider = new AnthropicProvider(mockConfig);
    });

    it("should store config on construction", () => {
        expect((provider as any).client).toBeDefined();
    });

    it("should extract system message from the first system-role message", async () => {
        const messages: NormalizedMessage[] = [
            { role: "system", content: "You are a helpful assistant." },
            { role: "user", content: "Hello!" },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123",
            model: "claude-sonnet-4",
            content: [{ type: "text", text: "Hi!" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 15, output_tokens: 5 },
        });

        const result = await provider.chat("claude-sonnet-4", messages);
        expect(mockCreate).toHaveBeenCalledWith(
            expect.objectContaining({
                system: "You are a helpful assistant.",
            }),
        );
        expect(result.content).toBe("Hi!");
    });

    it("should handle absence of system message", async () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "Hello!" },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Hi!" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 10, output_tokens: 5 },
        });

        const result = await provider.chat("claude-sonnet-4", messages);
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.system).toBeUndefined();
    });

    it("should format user message correctly", async () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "Hello!" },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Hi!" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 10, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", messages);
        const callArg = mockCreate.mock.calls[0][0];
        const userMsg = callArg.messages[0];
        expect(userMsg.role).toBe("user");
        expect(userMsg.content).toBe("Hello!");
    });

    it("should convert tool role messages to tool_result content blocks", async () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "Check this." },
            { role: "tool", content: '{"result":"ok"}', tool_call_id: "call_123" },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Done." }],
            stop_reason: "end_turn",
            usage: { input_tokens: 10, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", messages);
        const callArg = mockCreate.mock.calls[0][0];
        // tool role becomes user with tool_result content block
        const toolMsg = callArg.messages[1];
        expect(toolMsg.role).toBe("user");
        expect(toolMsg.content[0].type).toBe("tool_result");
        expect(toolMsg.content[0].tool_use_id).toBe("call_123");
    });

    it("should convert assistant tool_calls to tool_use content blocks", async () => {
        const messages: NormalizedMessage[] = [
            {
                role: "assistant",
                content: "Let me look that up...",
                tool_calls: [
                    { id: "call_abc", type: "function", function: { name: "get_time", arguments: "{}" } },
                ],
            },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Done." }],
            stop_reason: "end_turn",
            usage: { input_tokens: 10, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", messages);
        const callArg = mockCreate.mock.calls[0][0];
        const assistantMsg = callArg.messages[0];
        expect(assistantMsg.content[0].type).toBe("text");
        expect(assistantMsg.content[1].type).toBe("tool_use");
        expect(assistantMsg.content[1].name).toBe("get_time");
    });

    it("should convert NormalizedTool[] to Anthropic tool format", async () => {
        const tools: NormalizedTool[] = [
            {
                type: "function",
                function: { name: "test_tool", description: "Test tool", parameters: { type: "object", properties: { x: { type: "string" } } } },
            },
        ];

        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Done." }],
            stop_reason: "end_turn",
            usage: { input_tokens: 10, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }], { tools });
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.tools[0].name).toBe("test_tool");
        expect(callArg.tools[0].input_schema).toBeDefined();
    });

    it("should map toolChoice 'none' → { type: 'none' }", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "OK" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 5, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }], { toolChoice: "none" });
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.tool_choice).toEqual({ type: "none" });
    });

    it("should map toolChoice 'required' → { type: 'any' }", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "OK" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 5, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }], { toolChoice: "required" });
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.tool_choice).toEqual({ type: "any" });
    });

    it("should map function object toolChoice → { type: 'tool', name }", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "OK" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 5, output_tokens: 5 },
        });

        await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }], {
            toolChoice: { type: "function", function: { name: "my_tool" } },
        });
        const callArg = mockCreate.mock.calls[0][0];
        expect(callArg.tool_choice).toEqual({ type: "tool", name: "my_tool" });
    });

    it("should map stop_reason correctly", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_123", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Hello" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 5, output_tokens: 5 },
        });

        const result = await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }]);
        expect(result.finishReason).toBe("stop");

        // tool_use → tool_calls
        mockCreate.mockResolvedValue({
            id: "msg_124", model: "claude-sonnet-4",
            content: [{ type: "tool_use", id: "tu_1", name: "get_time", input: {} }],
            stop_reason: "tool_use",
            usage: { input_tokens: 5, output_tokens: 5 },
        });

        const result2 = await provider.chat("claude-sonnet-4", [{ role: "user", content: "time?" }]);
        expect(result2.finishReason).toBe("tool_calls");
        expect(result2.toolCalls).toHaveLength(1);
    });

    it("should extract tool calls from content blocks", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_125", model: "claude-sonnet-4",
            content: [
                { type: "text", text: "Let me check..." },
                { type: "tool_use", id: "tu_1", name: "get_time", input: {} },
            ],
            stop_reason: "tool_use",
            usage: { input_tokens: 10, output_tokens: 8 },
        });

        const result = await provider.chat("claude-sonnet-4", [{ role: "user", content: "What time?" }]);
        expect(result.toolCalls).toHaveLength(1);
        expect(result.toolCalls![0].function.name).toBe("get_time");
        expect(result.content).toBe("Let me check...");
    });

    it("should return usage with input_tokens + output_tokens", async () => {
        const mockCreate = vi.fn();
        (provider as any).client = { messages: { create: mockCreate } };
        mockCreate.mockResolvedValue({
            id: "msg_126", model: "claude-sonnet-4",
            content: [{ type: "text", text: "Hello" }],
            stop_reason: "end_turn",
            usage: { input_tokens: 50, output_tokens: 25 },
        });

        const result = await provider.chat("claude-sonnet-4", [{ role: "user", content: "hi" }]);
        expect(result.usage!.promptTokens).toBe(50);
        expect(result.usage!.completionTokens).toBe(25);
        expect(result.usage!.totalTokens).toBe(75);
    });
});