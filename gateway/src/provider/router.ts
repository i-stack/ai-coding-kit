import type { Provider, ProviderResult, ProviderStreamChunk, ProviderChatOptions } from "./types.js";
import type { NormalizedMessage } from "../types.js";
import { OpenAIProvider } from "./openai.js";
import { AnthropicProvider } from "./anthropic.js";
import type { GatewayConfig } from "../config.js";

/**
 * ProviderRouter — dispatches requests to the appropriate upstream provider
 * based on the model name.
 *
 * Routing rules use prefix matching (e.g. "claude-" → Anthropic).
 * Supports per-request provider override via resolveProvider(model, override?).
 * Falls back from Anthropic to OpenAI on failure.
 */
export class ProviderRouter implements Provider {
    readonly name = "router";
    private providers: Map<string, Provider> = new Map();
    private routes: Array<{ prefix: string; providerName: string }> = [];
    private defaultProviderName = "openai";
    private _providerNames: string[] = [];

    constructor(config: GatewayConfig) {
        // Always register OpenAI
        this.providers.set("openai", new OpenAIProvider(config));
        this._providerNames.push("openai");

        // Optionally register Anthropic
        if (config.anthropicApiKey) {
            this.providers.set("anthropic", new AnthropicProvider(config));
            this._providerNames.push("anthropic");
        }

        // Routing rules (order matters: first match wins)
        this.addRoute("claude-", "anthropic");
    }

    /** Return list of registered provider names. */
    get providerNames(): string[] {
        return [...this._providerNames];
    }

    private addRoute(prefix: string, providerName: string): void {
        if (this.providers.has(providerName)) {
            this.routes.push({ prefix, providerName });
        }
    }

    /**
     * Resolve which provider to use for a given model.
     *
     * @param model - The model name string (e.g. "claude-sonnet-4-20250514")
     * @param override - Optional provider name override (e.g. "openai")
     */
    resolveProvider(model: string, override?: string): Provider {
        if (override && this.providers.has(override)) {
            return this.providers.get(override)!;
        }

        const lower = model.toLowerCase();
        for (const route of this.routes) {
            if (lower.startsWith(route.prefix)) {
                return this.providers.get(route.providerName)!;
            }
        }

        // Default fallback
        return this.providers.get(this.defaultProviderName)!;
    }

    // ── Provider interface implementation ────────────────────────────────

    async chat(
        model: string,
        messages: NormalizedMessage[],
        options?: ProviderChatOptions,
    ): Promise<ProviderResult> {
        const provider = this.resolveProvider(model, options?.providerOverride);
        try {
            return await provider.chat(model, messages, options);
        } catch (err) {
            // On Anthropic failure, fall back to OpenAI
            if (provider.name === "anthropic" && this.providers.has("openai")) {
                console.warn(
                    `[ProviderRouter] Anthropic failed for ${model}, falling back to OpenAI: ${(err as Error).message}`,
                );
                const fallback = this.providers.get("openai")!;
                return await fallback.chat(model, messages, options);
            }
            throw err;
        }
    }

    async *chatStreaming(
        model: string,
        messages: NormalizedMessage[],
        options?: ProviderChatOptions,
    ): AsyncGenerator<ProviderStreamChunk> {
        const provider = this.resolveProvider(model, options?.providerOverride);
        try {
            yield* provider.chatStreaming(model, messages, options);
        } catch (err) {
            if (provider.name === "anthropic" && this.providers.has("openai")) {
                console.warn(
                    `[ProviderRouter] Anthropic streaming failed for ${model}, falling back to OpenAI: ${(err as Error).message}`,
                );
                const fallback = this.providers.get("openai")!;
                yield* fallback.chatStreaming(model, messages, options);
                return; // fallback completed successfully — don't throw original error
            }
            throw err;
        }
    }
}