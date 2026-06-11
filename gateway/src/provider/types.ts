/**
 * Shared provider interfaces for the gateway.
 *
 * Each upstream backend (OpenAI, Anthropic, local model, etc.) implements
 * the Provider interface. The ProviderRouter dispatches by model name.
 */
import type { NormalizedMessage, NormalizedTool, ToolChoice } from "../types.js";

// ── Result types (moved from openai.ts) ───────────────────────────────

export interface ProviderResult {
  id: string;
  model: string;
  content: string | null;
  finishReason: string | null;
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

// ── Chat options with normalized types ────────────────────────────────

export interface ProviderChatOptions {
  maxTokens?: number;
  temperature?: number;
  tools?: NormalizedTool[];
  toolChoice?: ToolChoice;
}

// ── Provider interface ────────────────────────────────────────────────

export interface Provider {
  /** Human-readable provider name (e.g. "openai", "anthropic"). */
  readonly name: string;

  /** Non-streaming chat completion. */
  chat(
    model: string,
    messages: NormalizedMessage[],
    options?: ProviderChatOptions,
  ): Promise<ProviderResult>;

  /** Streaming chat completion. Yields delta/done chunks. */
  chatStreaming(
    model: string,
    messages: NormalizedMessage[],
    options?: ProviderChatOptions,
  ): AsyncGenerator<ProviderStreamChunk>;
}