import { describe, it, expect, vi } from "vitest";
import { ToolRegistry } from "../../../src/tool/registry.js";
import type { ToolSpec } from "../../../src/tool/types.js";

describe("ToolRegistry", () => {
    let registry: ToolRegistry;

    beforeEach(() => {
        registry = new ToolRegistry();
    });

    it("should be empty on construction", () => {
        expect(registry.count).toBe(0);
    });

    it("should load tools from a valid JSON array", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(
            JSON.stringify([
                { name: "t1", description: "T1", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "h" } },
                { name: "t2", description: "T2", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "w" } },
            ]),
        );
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(2);
    });

    it("should load tools from { tools: [...] } format", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(
            JSON.stringify({ tools: [{ name: "t1", description: "T1", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "h" } }] }),
        );
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(1);
    });

    it("should skip specs missing name", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(
            JSON.stringify([{ description: "No name", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" } }]),
        );
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(0);
    });

    it("should skip specs missing executor", async () => {
        const fs = await import("node:fs");
        (fs.existsSync as ReturnType<typeof vi.fn>).mockReturnValue(true);
        (fs.readFileSync as ReturnType<typeof vi.fn>).mockReturnValue(
            JSON.stringify([{ name: "no_exec", description: "ME", input_schema: { type: "object", properties: {} } }]),
        );
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(0);
    });

    it("should register a tool programmatically", () => {
        registry.register({ name: "test_tool", description: "Test tool", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "test" } });
        expect(registry.count).toBe(1);
    });

    it("getActiveTools should return only non-internal active tools", () => {
        registry.register({ name: "public", description: "P", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "x" } });
        registry.register({ name: "internal", description: "I", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "y" }, internal: true });
        expect(registry.getActiveTools().map((t) => t.name)).toEqual(["public"]);
    });

    it("shouldInjectTool with blocklist", () => {
        const spec: ToolSpec = { name: "b", description: "b", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" }, disableForModels: ["gpt-3.5-*"] };
        expect(registry.shouldInjectTool(spec, "gpt-3.5-turbo")).toBe(false);
        expect(registry.shouldInjectTool(spec, "gpt-4o")).toBe(true);
    });

    it("shouldInjectTool with allowlist", () => {
        const spec: ToolSpec = { name: "p", description: "p", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" }, compatibleModels: ["claude-*", "gpt-4-*"] };
        expect(registry.shouldInjectTool(spec, "claude-sonnet-4")).toBe(true);
        expect(registry.shouldInjectTool(spec, "gpt-4-turbo")).toBe(true);
        expect(registry.shouldInjectTool(spec, "gpt-3.5-turbo")).toBe(false);
    });

    it("shouldInjectTool no allowlist or blocklist → always true", () => {
        const spec: ToolSpec = { name: "u", description: "u", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" } };
        expect(registry.shouldInjectTool(spec, "any-model")).toBe(true);
    });

    it("glob '*' matches all models", () => {
        const spec: ToolSpec = { name: "c", description: "c", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" }, disableForModels: ["*"] };
        expect(registry.shouldInjectTool(spec, "anything")).toBe(false);
    });

    it("resolveToolChoicePolicy", () => {
        registry.register({ name: "pt", description: "p", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "t" }, toolChoicePolicy: { "claude-sonnet-4-*": "any" } });
        expect(registry.resolveToolChoicePolicy("claude-sonnet-4-20250514")).toBe("any");
        expect(registry.resolveToolChoicePolicy("gpt-4o")).toBeUndefined();
    });

    it("toOpenAITool shape", () => {
        const r = registry.toOpenAITool({ name: "mt", description: "MT", input_schema: { type: "object", properties: { x: { type: "string" } }, required: ["x"] }, executor: { type: "static_template", template: "t" } });
        expect(r.type).toBe("function");
        expect(r.function.name).toBe("mt");
        expect(r.function.parameters).toEqual({ type: "object", properties: { x: { type: "string" } }, required: ["x"] });
    });

    it("get by name", () => {
        registry.register({ name: "find_me", description: "FM", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "f" } });
        expect(registry.get("find_me")).toBeDefined();
    });
});