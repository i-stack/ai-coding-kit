/**
 * Inbound MCP server adapter — exposes the gateway as an MCP server.
 *
 * Uses SSE transport for broad client compatibility (Cursor, VS Code MCP support).
 *
 * Routes:
 *   GET  /mcp/sse      → establishes SSE stream
 *   POST /mcp/message  → receives JSON-RPC messages
 *
 * Handlers:
 *   tools/list  → returns all active tools from ToolRegistry
 *   tools/call  → delegates to ToolExecutorEngine
 */

import type { FastifyInstance } from "fastify";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
    ListToolsRequestSchema,
    CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import type { ToolRegistry } from "../tool/registry.js";
import type { ToolExecutorEngine } from "../tool/executor.js";

/**
 * Register MCP server routes on a Fastify instance using SSE transport.
 *
 * Each SSE connection creates its own Server + transport pair so that
 * concurrent clients do not collide on the SDK's single-transport limit.
 */
export function registerMcpServer(
    app: FastifyInstance,
    toolRegistry: ToolRegistry,
    toolExecutor: ToolExecutorEngine,
): void {
    const sessions = new Map<string, SSEServerTransport>();

    // ── Fastify route: GET /mcp/sse (establish SSE stream) ──────────
    app.get("/mcp/sse", async (_request, reply) => {
        const transport = new SSEServerTransport("/mcp/message", reply.raw);
        sessions.set(transport.sessionId, transport);

        // Create a fresh Server instance per connection
        const mcpServer = new Server(
            { name: "universal-rag-gateway", version: "0.1.0" },
            { capabilities: { tools: {} } },
        );

        // ── tools/list handler ─────────────────────────────────────────────
        mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
            const specs = toolRegistry.getActiveTools();
            const tools = specs.map((s) => ({
                name: s.name,
                description: s.description,
                inputSchema: s.input_schema as {
                    type: "object";
                    properties: Record<string, unknown>;
                    required?: string[];
                },
            }));
            return { tools };
        });

        // ── tools/call handler ─────────────────────────────────────────────
        mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            const spec = toolRegistry.get(name);
            if (!spec) {
                return {
                    content: [{ type: "text" as const, text: `Unknown tool: ${name}` }],
                    isError: true,
                };
            }

            const result = await toolExecutor.execute(
                spec,
                "mcp-inbound",
                (args ?? {}) as Record<string, unknown>,
            );

            return {
                content: [
                    {
                        type: "text" as const,
                        text: result.success
                            ? result.content
                            : `Error: ${result.error ?? result.content}`,
                    },
                ],
                isError: !result.success,
            };
        });

        reply.raw.on("close", () => {
            sessions.delete(transport.sessionId);
        });

        await mcpServer.connect(transport);
    });

    // ── Fastify route: POST /mcp/message (receive JSON-RPC messages) ─
    app.post("/mcp/message", async (request, reply) => {
        const query = request.query as Record<string, string>;
        const sessionId = query.sessionId;

        const transport = sessionId ? sessions.get(sessionId) : undefined;
        if (!transport) {
            return reply.status(404).send({
                error: `No MCP session found${sessionId ? `: ${sessionId}` : ""}`,
            });
        }

        await transport.handlePostMessage(
            request.raw,
            reply.raw,
            request.body as Record<string, unknown>,
        );
    });

    app.log.info("MCP inbound server registered at GET /mcp/sse and POST /mcp/message");
}