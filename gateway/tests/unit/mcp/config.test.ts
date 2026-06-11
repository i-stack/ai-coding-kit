import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { loadMcpServerConfigs } from "../../../src/mcp/config.js";

vi.mock("node:fs");

describe("loadMcpServerConfigs", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should return empty Map for non-existent file", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(false);
        const result = loadMcpServerConfigs("/no/file.json");
        expect(result.size).toBe(0);
    });

    it("should parse valid config file correctly", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(JSON.stringify({
            mcpServers: {
                filesystem: { command: "npx", args: ["-y", "fs-server"] },
                web: { url: "https://example.com/mcp", headers: { Authorization: "Bearer token" } },
            },
        }));
        const result = loadMcpServerConfigs("/config.json");
        expect(result.size).toBe(2);
        expect(result.get("filesystem")!.command).toBe("npx");
        expect(result.get("web")!.url).toBe("https://example.com/mcp");
    });

    it("should skip entries missing command and url", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(JSON.stringify({
            mcpServers: {
                valid: { command: "npx" },
                invalid: {},
            },
        }));
        const result = loadMcpServerConfigs("/config.json");
        expect(result.size).toBe(1);
        expect(result.has("valid")).toBe(true);
    });
});