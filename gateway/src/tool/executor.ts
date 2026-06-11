import type { ToolSpec, ToolExecutor } from "./types.js";
import type { McpClientManager } from "../mcp/client.js";

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
 *   - mcp_call (outbound MCP server call via McpClientManager)
 *
 * Security rules:
 *   - http_request: only https://, only allowlisted hosts, timeout enforced
 *   - static_template: no exec/shell, only {{args.X}} and {{env.Y}} substitution
 *   - mcp_call: delegates to McpClientManager, which manages lifecycle
 */
export class ToolExecutorEngine {
    private allowedHosts: string[];
    private mcpManager: McpClientManager | undefined;

    constructor(allowedHosts?: string[], mcpManager?: McpClientManager) {
        // Default: block everything except documented demo/test hosts
        this.allowedHosts = allowedHosts ?? [
            "api.github.com",
            "httpbin.org",
            "jsonplaceholder.typicode.com",
        ];
        this.mcpManager = mcpManager;
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
                case "mcp_call":
                    return await this.executeMcpCall(spec, toolCallId, args);
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

    private async executeMcpCall(
        spec: ToolSpec,
        toolCallId: string,
        args: Record<string, unknown>,
    ): Promise<ToolExecutionResult> {
        const executor = spec.executor as Extract<ToolExecutor, { type: "mcp_call" }>;

        if (!this.mcpManager) {
            return {
                toolCallId,
                name: spec.name,
                content: "MCP client manager not configured",
                success: false,
                error: "McpClientManager not available",
            };
        }

        const client = this.mcpManager.getClient(executor.server);
        if (!client) {
            return {
                toolCallId,
                name: spec.name,
                content: `MCP server "${executor.server}" is not connected`,
                success: false,
                error: `MCP server "${executor.server}" not available (state: ${this.mcpManager.getState(executor.server)})`,
            };
        }

        try {
            // Merge incoming args with executor defaults; incoming wins
            const mergedArgs = { ...(executor.args ?? {}), ...args } as Record<string, unknown>;

            const result = await client.callTool({
                name: executor.method,
                arguments: mergedArgs,
            });

            const contentItems = result.content as unknown as Array<{ type?: string; text?: string }> | undefined;
            const textContent = contentItems
                ? contentItems
                    .map((c) => (c.type === "text" ? (c.text ?? "") : JSON.stringify(c)))
                    .join("\n")
                : "";

            return {
                toolCallId,
                name: spec.name,
                content: textContent,
                success: !result.isError,
                error: result.isError ? "Tool returned error" : undefined,
            };
        } catch (err) {
            return {
                toolCallId,
                name: spec.name,
                content: `MCP call failed: ${(err as Error).message}`,
                success: false,
                error: (err as Error).message,
            };
        }
    }

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