import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpClientManager } from "../../../src/mcp/client.js";

describe("McpClientManager", () => {
    let manager: McpClientManager;

    beforeEach(() => {
        manager = new McpClientManager();
    });

    it("should be empty on construction", () => {
        expect(manager.count).toBe(0);
    });

    it("registerServers should add entries", () => {
        const configs = new Map();
        configs.set("test-server", { command: "npx", args: ["-y", "test"] });
        manager.registerServers(configs);
        expect(manager.count).toBe(1);
    });

    it("registerServers should skip duplicates", () => {
        const configs = new Map();
        configs.set("test-server", { command: "npx" });
        manager.registerServers(configs);
        manager.registerServers(configs);
        expect(manager.count).toBe(1);
    });

    it("getState should return disconnected for unknown server", () => {
        expect(manager.getState("unknown")).toBe("disconnected");
    });

    it("getClient should return undefined before connection", () => {
        const configs = new Map();
        configs.set("svr", { command: "npx" });
        manager.registerServers(configs);
        expect(manager.getClient("svr")).toBeUndefined();
    });

    it("closeAll should not throw when no servers", async () => {
        await manager.closeAll();
    });
});