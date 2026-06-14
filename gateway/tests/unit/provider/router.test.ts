import { describe, it, expect, vi } from "vitest";
import { ProviderRouter } from "../../../src/provider/router.js";
import type { GatewayConfig } from "../../../src/config.js";

describe("ProviderRouter", () => {
    it("should register OpenAI only when no Anthropic key", () => {
        const config = {
            openaiApiKey: "test-key",
            openaiBaseUrl: "https://api.openai.com/v1",
            openaiDefaultModel: "gpt-4o",
            anthropicApiKey: "",
            anthropicBaseUrl: "https://api.anthropic.com",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        expect(router.providerNames).toEqual(["openai"]);
    });

    it("should register both providers when Anthropic key is set", () => {
        const config = {
            openaiApiKey: "test-key",
            openaiBaseUrl: "https://api.openai.com/v1",
            openaiDefaultModel: "gpt-4o",
            anthropicApiKey: "ant-key",
            anthropicBaseUrl: "https://api.anthropic.com",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        expect(router.providerNames).toContain("openai");
        expect(router.providerNames).toContain("anthropic");
    });

    it("should resolve claude-* models to Anthropic provider", () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const provider = router.resolveProvider("claude-sonnet-4-20250514");
        expect(provider.name).toBe("anthropic");
    });

    it("should resolve non-claude models to OpenAI provider", () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const provider = router.resolveProvider("gpt-4o");
        expect(provider.name).toBe("openai");
    });

    it("should resolve unknown models to OpenAI (default fallback)", () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const provider = router.resolveProvider("unknown-model");
        expect(provider.name).toBe("openai");
    });

    it("should support per-request provider override", () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const provider = router.resolveProvider("claude-sonnet-4", "openai");
        expect(provider.name).toBe("openai");
    });

    it("should delegate chat() to resolved provider", async () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);

        const mockResult = {
            id: "test", model: "gpt-4o", content: "test", finishReason: "stop",
            usage: { promptTokens: 10, completionTokens: 5, totalTokens: 15 },
        };

        // Mock the OpenAI provider's chat method
        const openaiProvider = (router as any).providers.get("openai");
        vi.spyOn(openaiProvider, "chat").mockResolvedValue(mockResult);

        const result = await router.chat("gpt-4o", [{ role: "user", content: "hi" }]);
        expect(result.content).toBe("test");
    });

    it("should fall back from Anthropic to OpenAI on failure", async () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "ant-key",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const anthropicProvider = (router as any).providers.get("anthropic");
        const openaiProvider = (router as any).providers.get("openai");

        vi.spyOn(anthropicProvider, "chat").mockRejectedValue(new Error("Anthropic down"));
        const mockResult = {
            id: "test", model: "gpt-4o", content: "fallback", finishReason: "stop",
            usage: { promptTokens: 10, completionTokens: 5, totalTokens: 15 },
        };
        vi.spyOn(openaiProvider, "chat").mockResolvedValue(mockResult);

        const result = await router.chat("claude-sonnet-4", [{ role: "user", content: "hi" }]);
        expect(result.content).toBe("fallback");
    });

    it("should throw on OpenAI failure (no fallback available)", async () => {
        const config = {
            openaiApiKey: "test-key",
            anthropicApiKey: "",
        } as unknown as GatewayConfig;

        const router = new ProviderRouter(config);
        const openaiProvider = (router as any).providers.get("openai");
        vi.spyOn(openaiProvider, "chat").mockRejectedValue(new Error("OpenAI down"));

        await expect(
            router.chat("gpt-4o", [{ role: "user", content: "hi" }]),
        ).rejects.toThrow("OpenAI down");
    });
});