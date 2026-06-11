import { describe, it, expect, beforeEach, vi } from "vitest";
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

    it("should load tools from a valid JSON array", () => {
        const json = JSON.stringify([
            { name: "tool1", description: "Tool 1", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "hello" } },
            { name: "tool2", description: "Tool 2", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "world" } },
        ]);
        vi.spyOn(require("node:fs"), "existsSync").mockReturnValue(true);
        vi.spyOn(require("node:fs"), "readFileSync").mockReturnValue(json);
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(2);
    });

    it("should load tools from { tools: [...] } format", () => {
        const json = JSON.stringify({
            tools: [
                { name: "tool1", description: "Tool 1", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "hello" } },
            ],
        });
        vi.spyOn(require("node:fs"), "existsSync").mockReturnValue(true);
        vi.spyOn(require("node:fs"), "readFileSync").mockReturnValue(json);
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(1);
    });

    it("should skip invalid tool specs missing name", () => {
        const json = JSON.stringify([
            { description: "No name", input_schema: { type: "object", properties: {} }, executor: { type: "static_template", template: "test" } },
        ]);
        vi.spyOn(require("node:fs"), "existsSync").mockReturnValue(true);
        vi.spyOn(require("node:fs"), "readFileSync").mockReturnValue(json);
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(0);
    });

    it("should skip invalid tool specs missing executor", () => {
        const json = JSON.stringify([
            { name: "no_executor", description: "Missing executor", input_schema: { type: "object", properties: {} } },
        ]);
        vi.spyOn(require("node:fs"), "existsSync").mockReturnValue(true);
        vi.spyOn(require("node:fs"), "readFileSync").mockReturnValue(json);
        registry.loadFromFile("/fake/path.json");
        expect(registry.count).toBe(0);
    });

    it("should register a tool programmatically", () => {
        registry.register({
            name: "test_tool",
            description: "Test tool",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
        });
        expect(registry.count).toBe(1);
    });

    it("getActiveTools should return only non-internal active tools", () => {
        registry.register({
            name: "public_tool", description: "Public", input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
        });
        registry.register({
            name: "internal_tool", description: "Internal", input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "internal" },
            internal: true,
        });
        const active = registry.getActiveTools();
        expect(active.length).toBe(1);
        expect(active[0].name).toBe("public_tool");
    });

    it("shouldInjectTool with blocklist should exclude matching models", () => {
        const spec: ToolSpec = {
            name: "blocked_tool", description: "Blocked for some models",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
            disableForModels: ["gpt-3.5*"],
        };
        expect(registry.shouldInjectTool(spec, "gpt-3.5-turbo")).toBe(false);
        expect(registry.shouldInjectTool(spec, "gpt-4o")).toBe(true);
    });

    it("shouldInjectTool with allowlist should only match compatible models", () => {
        const spec: ToolSpec = {
            name: "premium_tool", description: "Only for premium models",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "premium" },
            compatibleModels: ["claude-*", "gpt-4*"],
        };
        expect(registry.shouldInjectTool(spec, "claude-sonnet-4")).toBe(true);
        expect(registry.shouldInjectTool(spec, "gpt-4o")).toBe(true);
        expect(registry.shouldInjectTool(spec, "gpt-3.5-turbo")).toBe(false);
    });

    it("shouldInjectTool with no allowlist or blocklist should always allow", () => {
        const spec: ToolSpec = {
            name: "universal_tool", description: "Available everywhere",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
        };
        expect(registry.shouldInjectTool(spec, "any-model")).toBe(true);
    });

    it("should match glob pattern '*' to all models", () => {
        const spec: ToolSpec = {
            name: "catchall", description: "Catches all",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
            disableForModels: ["*"],
        };
        expect(registry.shouldInjectTool(spec, "anything")).toBe(false);
    });

    it("resolveToolChoicePolicy should return matching policy", () => {
        registry.register({
            name: "policy_tool", description: "Has tool choice policy",
            input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "test" },
            toolChoicePolicy: { "claude-sonnet-4*": "any" },
        });
        expect(registry.resolveToolChoicePolicy("claude-sonnet-4-20250514")).toBe("any");
        expect(registry.resolveToolChoicePolicy("gpt-4o")).toBeUndefined();
    });

    it("toOpenAITool should produce correct OpenAI-compatible shape", () => {
        const openaiTool = registry.toOpenAITool({
            name: "my_tool",
            description: "My tool description",
            input_schema: { type: "object", properties: { x: { type: "string" } }, required: ["x"] },
            executor: { type: "static_template", template: "test" },
        });
        expect(openaiTool.type).toBe("function");
        expect(openaiTool.function.name).toBe("my_tool");
        expect(openaiTool.function.parameters).toEqual({ type: "object", properties: { x: { type: "string" } }, required: ["x"] });
    });

    it("get should return a tool by name", () => {
        registry.register({
            name: "find_me", description: "Find me", input_schema: { type: "object", properties: {} },
            executor: { type: "static_template", template: "found" },
        });
        const tool = registry.get("find_me");
        expect(tool).toBeDefined();
        expect(tool!.name).toBe("find_me");
    });
});