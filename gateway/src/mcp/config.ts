/**
 * MCP server configuration types and loader.
 *
 * Reads the same format as `mcp/servers.json`:
 *
 *   {
 *     "mcpServers": {
 *       "server-name": {
 *         "command": "npx",
 *         "args": ["-y", "some-server"],
 *         "env": { "KEY": "value" }
 *       }
 *     }
 *   }
 *
 * Or:
 *
 *   {
 *     "mcpServers": {
 *       "server-name": {
 *         "url": "https://example.com/mcp",
 *         "headers": { "Authorization": "Bearer ..." }
 *       }
 *     }
 *   }
 */

import fs from "node:fs";

export interface McpServerConfig {
    /** For stdio-based servers: executable to spawn */
    command?: string;
    /** Arguments passed to the command */
    args?: string[];
    /** Environment variables for the spawned process */
    env?: Record<string, string>;
    /** For URL-based servers: SSE endpoint */
    url?: string;
    /** HTTP headers for URL-based connections */
    headers?: Record<string, string>;
}

export interface McpServersFile {
    mcpServers: Record<string, McpServerConfig>;
}

/**
 * Load MCP server configurations from a JSON file.
 * Returns an empty map if the file doesn't exist or can't be parsed.
 */
export function loadMcpServerConfigs(filePath: string): Map<string, McpServerConfig> {
    const configs = new Map<string, McpServerConfig>();

    if (!fs.existsSync(filePath)) {
        console.warn(`⚠️  MCP servers file not found: ${filePath}`);
        return configs;
    }

    try {
        const raw = JSON.parse(fs.readFileSync(filePath, "utf-8")) as McpServersFile;

        if (!raw.mcpServers || typeof raw.mcpServers !== "object") {
            console.warn("⚠️  MCP servers file has unexpected format — expected { mcpServers: { ... } }");
            return configs;
        }

        for (const [name, config] of Object.entries(raw.mcpServers)) {
            if (!config.command && !config.url) {
                console.warn(`⚠️  MCP server "${name}" has no command or url — skipping`);
                continue;
            }
            configs.set(name, config);
        }

        console.log(`🔌 MCP server configs loaded: ${configs.size} servers`);
    } catch (err) {
        console.error("Failed to load MCP servers file:", (err as Error).message);
    }

    return configs;
}