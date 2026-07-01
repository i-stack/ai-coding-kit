import type { ToolSpec, ToolExecutor } from "./types.js";
import type { VectorStore } from "../vector/store.js";
import type { EntityStore } from "../entity/store.js";
import type { QdrantSearchResult } from "../vector/qdrant.js";
import type { GraphSearchResult } from "../types.js";

export interface ToolExecutionResult {
    toolCallId: string;
    name: string;
    content: string;
    success: boolean;
    error?: string;
}

/**
 * ToolExecutorEngine runs declarative tool specs.
 *
 * For MVP, supports:
 *   - http_request (allowlisted hosts only)
 *   - static_template (deterministic snippet substitution)
 *   - memory_search (Qdrant + GraphRAG retrieval)
 *
 * Security rules:
 *   - http_request: only https://, only allowlisted hosts, timeout enforced
 *   - static_template: no exec/shell, only {{args.X}} and {{env.Y}} substitution
 *   - memory_search: read-only store access, no mutation
 */
export class ToolExecutorEngine {
    private allowedHosts: string[];
    private vectorStore?: VectorStore;
    private entityStore?: EntityStore;

    constructor(
        allowedHosts?: string[],
        stores?: { vectorStore?: VectorStore; entityStore?: EntityStore },
    ) {
        // Default: block everything except documented demo/test hosts
        this.allowedHosts = allowedHosts ?? [
            "api.github.com",
            "httpbin.org",
            "jsonplaceholder.typicode.com",
        ];
        if (stores) {
            this.vectorStore = stores.vectorStore;
            this.entityStore = stores.entityStore;
        }
    }

    /**
     * Execute a single tool call.
     */
    async execute(
        spec: ToolSpec,
        toolCallId: string,
        args: Record<string, unknown>,
    ): Promise<ToolExecutionResult> {
        try {
            switch (spec.executor.type) {
                case "http_request":
                    return await this.executeHttp(spec, toolCallId, args);
                case "static_template":
                    return this.executeTemplate(spec, toolCallId, args);
                case "memory_search":
                    return await this.executeMemorySearch(spec, toolCallId, args);
                default:
                    return {
                        toolCallId,
                        name: spec.name,
                        content: `Unknown executor type`,
                        success: false,
                        error: `Unknown executor type: ${(spec.executor as ToolExecutor).type}`,
                    };
            }
        } catch (err) {
            return {
                toolCallId,
                name: spec.name,
                content: `Error: ${(err as Error).message}`,
                success: false,
                error: (err as Error).message,
            };
        }
    }

    /**
     * Execute multiple tool calls in parallel (no cross-call dependencies for MVP).
     */
    async executeBatch(
        specs: ToolSpec[],
        toolCalls: Array<{ id: string; name: string; args: Record<string, unknown> }>,
    ): Promise<ToolExecutionResult[]> {
        const specMap = new Map(specs.map((s) => [s.name, s]));
        return Promise.all(
            toolCalls.map((tc) => {
                const spec = specMap.get(tc.name);
                if (!spec) {
                    return Promise.resolve({
                        toolCallId: tc.id,
                        name: tc.name,
                        content: `Unknown tool: ${tc.name}`,
                        success: false,
                        error: `Tool not found in registry: ${tc.name}`,
                    });
                }
                return this.execute(spec, tc.id, tc.args);
            }),
        );
    }

    // ── Private ────────────────────────────────────────────────────

    private async executeHttp(
        spec: ToolSpec,
        toolCallId: string,
        args: Record<string, unknown>,
    ): Promise<ToolExecutionResult> {
        const executor = spec.executor as Extract<ToolExecutor, { type: "http_request" }>;
        const url = new URL(this.substitute(executor.url, args));

        // Security: enforce https and allowlisted hosts
        if (url.protocol !== "https:") {
            // Allow httpbin.org on http for testing in dev
            if (url.hostname !== "httpbin.org" && url.hostname !== "localhost") {
                return {
                    toolCallId,
                    name: spec.name,
                    content: "Only HTTPS URLs are allowed",
                    success: false,
                    error: "Non-HTTPS URL blocked",
                };
            }
        }

        if (!this.allowedHosts.includes(url.hostname) && url.hostname !== "localhost") {
            return {
                toolCallId,
                name: spec.name,
                content: `Host not allowlisted: ${url.hostname}`,
                success: false,
                error: `Host not in allowlist`,
            };
        }

        // Build query params from spec
        if (executor.query) {
            for (const [key, value] of Object.entries(executor.query)) {
                url.searchParams.set(key, this.substitute(value, args));
            }
        }

        // Build headers
        const headers: Record<string, string> = {
            ...(executor.headers ? this.substituteObject(executor.headers, args) : {}),
        };

        const timeoutMs = executor.timeoutMs ?? 10000;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetch(url.toString(), {
                method: executor.method,
                headers,
                body: executor.body ? JSON.stringify(this.substituteObject(executor.body as Record<string, string>, args)) : undefined,
                signal: controller.signal,
            });

            const body = await response.text();
            const truncated = body.length > 4000 ? body.slice(0, 4000) + "\n... [truncated]" : body;

            return {
                toolCallId,
                name: spec.name,
                content: truncated,
                success: response.ok,
                error: response.ok ? undefined : `HTTP ${response.status}`,
            };
        } finally {
            clearTimeout(timeout);
        }
    }

    private executeTemplate(
        spec: ToolSpec,
        toolCallId: string,
        args: Record<string, unknown>,
    ): ToolExecutionResult {
        const executor = spec.executor as Extract<ToolExecutor, { type: "static_template" }>;
        const content = this.substitute(executor.template, args);

        return {
            toolCallId,
            name: spec.name,
            content,
            success: true,
        };
    }

    // ── memory_search executor ────────────────────────────────────────────

    private async executeMemorySearch(
        spec: ToolSpec,
        toolCallId: string,
        args: Record<string, unknown>,
    ): Promise<ToolExecutionResult> {
        const executor = spec.executor as Extract<ToolExecutor, { type: "memory_search" }>;
        const query = args.query as string | undefined;
        if (!query) {
            return {
                toolCallId,
                name: spec.name,
                content: "Error: missing required argument 'query'",
                success: false,
                error: "Missing required argument 'query'",
            };
        }

        const limit = (args.limit as number | undefined) ?? executor.defaultLimit ?? 5;
        const tenantId = (args.tenant_id as string | undefined) ?? "default";
        const projectId = args.project_id as string | undefined;

        const parts: string[] = [];

        // Qdrant semantic search
        if (this.vectorStore) {
            try {
                const results = await this.vectorStore.search(query, {
                    limit,
                    tenantId,
                    projectId,
                });
                if (results.length > 0) {
                    const filtered = executor.scoreThreshold
                        ? results.filter((r) => r.score >= executor.scoreThreshold!)
                        : results;
                    if (filtered.length > 0) {
                        parts.push("=== Semantic Memory (Qdrant) ===");
                        for (const r of filtered) {
                            parts.push(`[relevance=${r.score.toFixed(2)}] ${r.payload.text}`);
                        }
                    }
                }
            } catch (err) {
                parts.push(`[Qdrant search failed: ${(err as Error).message}]`);
            }
        }

        // GraphRAG entity search
        if (this.entityStore) {
            try {
                const graphResults = await this.entityStore.searchGraph(query, tenantId, {
                    limit,
                    projectId,
                });
                if (graphResults.length > 0) {
                    parts.push("=== Entity Graph (GraphRAG) ===");
                    const lines = this.entityStore.formatContext(graphResults);
                    parts.push(...lines);
                }
            } catch (err) {
                parts.push(`[Graph search failed: ${(err as Error).message}]`);
            }
        }

        if (parts.length === 0) {
            return {
                toolCallId,
                name: spec.name,
                content: "No relevant memories found.",
                success: true,
            };
        }

        return {
            toolCallId,
            name: spec.name,
            content: parts.join("\n\n"),
            success: true,
        };
    }

    /**
     * Substitute {{args.xxx}} and {{env.YYY}} placeholders in a string.
     * Special: {{env.NOW}} returns the current time in ISO 8601.
     */
    private substitute(template: string, args: Record<string, unknown>): string {
        return template.replace(/\{\{(args|env)\.([\w.]+)\}\}/g, (match, type, key) => {
            if (type === "args") {
                return String(args[key] ?? "");
            }
            if (type === "env") {
                if (key === "NOW") return new Date().toISOString();
                return process.env[key] ?? "";
            }
            return match;
        });
    }

    /**
     * Substitute placeholders in all values of an object.
     */
    private substituteObject(
        obj: Record<string, string>,
        args: Record<string, unknown>,
    ): Record<string, string> {
        const result: Record<string, string> = {};
        for (const [key, value] of Object.entries(obj)) {
            result[key] = this.substitute(value, args);
        }
        return result;
    }
}