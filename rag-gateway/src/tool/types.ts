/**
 * Declarative tool spec — see docs/universal-rag-gateway.md §Declarative Tool Runtime.
 *
 * Tool specs are data, not code. Each executor type is a well-known capability
 * with its own security model.
 */

// ── Executor types ────────────────────────────────────────────────

export interface HttpRequestExecutor {
    type: "http_request";
    method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
    url: string;
    headers?: Record<string, string>;
    query?: Record<string, string>;
    body?: unknown;
    /** Timeout in ms (default 10000). Exceeding this fails the tool call. */
    timeoutMs?: number;
}

export interface StaticTemplateExecutor {
    type: "static_template";
    /** Template string with {{args.xxx}} and {{env.YYY}} placeholders. */
    template: string;
    /** Content-Type of the output */
    contentType?: string;
}

export type ToolExecutor = HttpRequestExecutor | StaticTemplateExecutor;

// ── Tool spec ─────────────────────────────────────────────────────

export interface ToolSpec {
    name: string;
    description: string;
    input_schema: {
        type: "object";
        properties: Record<string, unknown>;
        required?: string[];
    };
    executor: ToolExecutor;
    /** Per-model compatibility allowlist. Omit = available to all models. */
    compatibleModels?: string[];
    /** Per-model blocklist. If the model matches, the tool is excluded. */
    disableForModels?: string[];
    /** Per-model default tool_choice policy keyed by model name/glob. */
    toolChoicePolicy?: Record<string, "auto" | "any" | "none" | "required">;
    /** Models that should receive a simplified input_schema. */
    schemaSimplifyFor?: string[];
    /** If true, this tool is only injected when the request explicitly opts in. */
    internal?: boolean;
}

// ── Registry state ────────────────────────────────────────────────

export type ToolStatus = "active" | "candidate" | "retired";

export interface ToolRecord extends ToolSpec {
    id: string;
    status: ToolStatus;
    createdAt: string;
}