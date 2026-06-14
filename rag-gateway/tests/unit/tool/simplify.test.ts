import { describe, it, expect } from "vitest";
import { getSimplifiedSchema } from "../../../src/tool/simplify.js";
import type { ToolSpec } from "../../../src/tool/types.js";

const complexSchema: ToolSpec["input_schema"] = {
    type: "object",
    properties: {
        name: { type: "string", description: "The name of the user to look up. Must be a valid username with no special characters." },
        age: { type: "number", description: "Age of the user in years." },
        address: { type: "object", properties: { street: { type: "string" }, city: { type: "string" } }, description: "Full address object." },
        tags: { type: "array", items: { type: "object", properties: { key: { type: "string" }, value: { type: "string" } } }, description: "List of tags." },
        status: { type: "string", description: "Current status.", enum: ["active", "inactive", "suspended"] },
    },
    required: ["name", "age", "address", "tags", "status", "extra"],
};

const complexTool: ToolSpec = {
    name: "complex_tool",
    description: "A tool with complex schema",
    input_schema: complexSchema,
    executor: { type: "static_template", template: "done" },
    schemaSimplifyFor: ["claude-3-haiku-*"],
};

describe("getSimplifiedSchema", () => {
    it("should return original schema when schemaSimplifyFor is empty", () => {
        const tool: ToolSpec = {
            name: "simple", description: "Simple", input_schema: { type: "object", properties: { x: { type: "string" } } },
            executor: { type: "static_template", template: "done" },
        };
        const result = getSimplifiedSchema(tool, "any-model");
        expect(result).toBe(tool.input_schema);
    });

    it("should return original schema when model is not in schemaSimplifyFor", () => {
        const result = getSimplifiedSchema(complexTool, "gpt-4o");
        expect(result).toBe(complexSchema);
    });

    it("should simplify when model matches schemaSimplifyFor", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        expect(result).not.toBe(complexSchema);
        expect(result.type).toBe("object");
    });

    it("should flatten nested object properties", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        const addr = result.properties["address"] as Record<string, unknown>;
        expect(addr.type).toBe("object");
        expect(Object.keys((addr.properties as Record<string, unknown>) || {})).toEqual([]);
    });

    it("should change array with nested object items to string items", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        const tags = result.properties["tags"] as Record<string, unknown>;
        expect(tags.type).toBe("array");
        const items = tags.items as Record<string, unknown>;
        expect(items.type).toBe("string");
    });

    it("should keep scalar types and enums", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        const status = result.properties["status"] as Record<string, unknown>;
        expect(status.type).toBe("string");
        expect((status as any).enum).toEqual(["active", "inactive", "suspended"]);
    });

    it("should clip required to first 5 fields", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        expect(result.required!.length).toBeLessThanOrEqual(5);
    });

    it("should shorten descriptions", () => {
        const result = getSimplifiedSchema(complexTool, "claude-3-haiku-20240307");
        const name = result.properties["name"] as Record<string, unknown>;
        // Original is 85 chars; simplified shortens it to first line
        expect((name.description as string).length).toBeLessThanOrEqual(85);
    });

    it("should match pattern '*'", () => {
        const tool: ToolSpec = {
            name: "catchall_simplify", description: "Catchall",
            input_schema: complexSchema,
            executor: { type: "static_template", template: "done" },
            schemaSimplifyFor: ["*"],
        };
        const result = getSimplifiedSchema(tool, "any-model");
        expect(result).not.toBe(complexSchema);
    });
});