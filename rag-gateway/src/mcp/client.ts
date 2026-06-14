/**
 * McpClientManager — manages outbound MCP client connections.
 *
 * Connects to external MCP servers (stdio subprocesses or SSE URL endpoints)
 * and exposes their tool lists for integration with the gateway's ToolRegistry.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { metricsCollector } from "../metrics.js";
import type { McpServerConfig } from "./config.js";

export type McpConnectionState = "connecting" | "connected" | "disconnected" | "failed";

interface McpServerEntry {
    config: McpServerConfig;
    client: Client;
    transport: StdioClientTransport | SSEClientTransport;
    state: McpConnectionState;
    tools: Tool[];
    error?: string;
}

/**
 * Managed outbound MCP client that handles lazy connection and lifecycle.
 */
export class McpClientManager {
    private servers: Map<string, McpServerEntry> = new Map();
    private started = false;

    constructor() { }

    /**
     * Register all servers from the config map. Call `startAll()` to connect.
     */
    registerServers(configs: Map<string, McpServerConfig>): void {
        for (const [name, config] of configs) {
            if (this.servers.has(name)) continue;

            const client = new Client(
                { name: "universal-rag-gateway", version: "0.1.0" },
                { capabilities: {} },
            );

            const entry: McpServerEntry = {
                config,
                client,
                transport: null as unknown as StdioClientTransport | SSEClientTransport,
                state: "disconnected",
                tools: [],
            };
            this.servers.set(name, entry);
        }
    }

    /**
     * Connect to all registered servers eagerly on startup.
     */
    async startAll(): Promise<void> {
        if (this.started) return;
        this.started = true;

        const results = await Promise.allSettled(
            Array.from(this.servers.entries()).map(async ([name]) => {
                await this.connect(name);
            }),
        );

        const connected = results.filter((r) => r.status === "fulfilled").length;
        const failed = results.filter((r) => r.status === "rejected").length;
        console.log(`🔌 MCP outbound: ${connected} connected, ${failed} failed`);

        // Record degradations for failed servers
        for (let i = 0; i < results.length; i++) {
            const entry = Array.from(this.servers.values())[i];
            if (results[i].status === "rejected" && entry) {
                const reason = (results[i] as PromiseRejectedResult).reason;
                entry.state = "failed";
                entry.error = String(reason);
                metricsCollector.recordDegradation("mcp-" + (entry.config.command || "url"), String(reason));
            }
        }
    }

    /**
     * Connect a single server by name.
     */
    async connect(name: string): Promise<void> {
        const entry = this.servers.get(name);
        if (!entry) throw new Error(`Unknown MCP server: ${name}`);
        if (entry.state === "connected") return;

        entry.state = "connecting";

        try {
            let transport: StdioClientTransport | SSEClientTransport;

            if (entry.config.command) {
                transport = new StdioClientTransport({
                    command: entry.config.command,
                    args: entry.config.args,
                    env: entry.config.env,
                });
            } else if (entry.config.url) {
                const url = new URL(entry.config.url);
                transport = new SSEClientTransport(url, {
                    requestInit: entry.config.headers
                        ? { headers: entry.config.headers as Record<string, string> }
                        : undefined,
                });
            } else {
                throw new Error(`MCP server "${name}" has neither command nor url`);
            }

            entry.transport = transport;
            await entry.client.connect(transport);

            // Cache tool list
            try {
                const result = await entry.client.listTools();
                entry.tools = result.tools ?? [];
                console.log(`  📋 MCP "${name}": ${entry.tools.length} tools available`);
            } catch {
                console.warn(`  ⚠️  MCP "${name}": could not list tools`);
                entry.tools = [];
            }

            entry.state = "connected";
            entry.error = undefined;
        } catch (err) {
            entry.state = "failed";
            entry.error = (err as Error).message;
            throw err;
        }
    }

    /**
     * Get a connected Client by server name.
     * Returns undefined if the server is not connected or doesn't exist.
     */
    getClient(name: string): Client | undefined {
        const entry = this.servers.get(name);
        if (!entry || entry.state !== "connected") return undefined;
        return entry.client;
    }

    /**
     * Get the connection state for a server.
     */
    getState(name: string): McpConnectionState {
        return this.servers.get(name)?.state ?? "disconnected";
    }

    /**
     * Get the cached tool list for a server.
     */
    getServerTools(name: string): Tool[] {
        return this.servers.get(name)?.tools ?? [];
    }

    /**
     * Get all tools from all connected servers, keyed by server name.
     * Returns { serverName: tool[] }.
     */
    getAllTools(): Map<string, Tool[]> {
        const result = new Map<string, Tool[]>();
        for (const [name, entry] of this.servers) {
            if (entry.state === "connected") {
                result.set(name, entry.tools);
            }
        }
        return result;
    }

    /**
     * Close all client connections.
     */
    async closeAll(): Promise<void> {
        for (const [name, entry] of this.servers) {
            try {
                await entry.client.close();
                entry.state = "disconnected";
            } catch (err) {
                console.error(`Error closing MCP client "${name}":`, (err as Error).message);
            }
        }
    }

    /**
     * Number of registered servers.
     */
    get count(): number {
        return this.servers.size;
    }

    /**
     * Number of connected servers.
     */
    get connectedCount(): number {
        let count = 0;
        for (const entry of this.servers.values()) {
            if (entry.state === "connected") count++;
        }
        return count;
    }
}