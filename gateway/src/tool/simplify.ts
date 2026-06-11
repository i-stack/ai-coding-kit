/**
 * Schema simplification utility for models that struggle with complex JSON schemas.
 *
 * Given a ToolSpec and a model name, returns a simplified input_schema if the
 * model is in the spec's schemaSimplifyFor list. Simplification strategies:
 *
 * 1. Strip lengthy descriptions from properties (keep param names and types only)
 * 2. Change "array" type items to "string" if the items schema is deeply nested
 * 3. Cap `required` to the first 5 fields
 * 4. Flatten nested object properties to `"type": "string"` if depth > 2
 */

import type { ToolSpec } from "./types.js";

/**
 * Return the input_schema for a tool, simplified if the model is in the
 * spec's schemaSimplifyFor list.
 */
export function getSimplifiedSchema(
    spec: ToolSpec,
    model: string,
): ToolSpec["input_schema"] {
    const shouldSimplify =
        spec.schemaSimplifyFor &&
        spec.schemaSimplifyFor.some((p) => modelMatchesSimple(model, p));

    if (!shouldSimplify) return spec.input_schema;

    return simplifySchema(spec.input_schema);
}

function modelMatchesSimple(model: string, pattern: string): boolean {
    if (pattern === "*") return true;
    if (pattern.endsWith("-*")) return model.startsWith(pattern.slice(0, -2));
    return model === pattern;
}

function simplifySchema(input: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
}): {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
} {
    const simplified: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(input.properties)) {
        if (typeof value === "object" && value !== null) {
            const prop = value as Record<string, unknown>;

            if (prop.type === "object") {
                // Flatten nested objects — only keep type
                simplified[key] = { type: "object", properties: {}, description: simplifyDescription(prop.description) };
            } else if (prop.type === "array") {
                // Simplify array items
                const items = prop.items as Record<string, unknown> | undefined;
                if (items && typeof items === "object" && items.type === "object") {
                    simplified[key] = { type: "array", items: { type: "string" }, description: simplifyDescription(prop.description) };
                } else {
                    simplified[key] = { type: "array", description: simplifyDescription(prop.description) };
                }
            } else {
                // Keep scalar types, strip verbose descriptions
                simplified[key] = {
                    type: prop.type ?? "string",
                    description: simplifyDescription(prop.description),
                    ...(prop.enum ? { enum: prop.enum } : {}),
                };
            }
        } else {
            simplified[key] = value;
        }
    }

    const required = input.required ? input.required.slice(0, 5) : undefined;

    return {
        type: "object",
        properties: simplified,
        required,
    };
}

function simplifyDescription(
    desc: unknown,
): string | undefined {
    if (typeof desc !== "string") return undefined;
    // Keep only the first sentence (up to 80 chars)
    const trimmed = desc.split("\n")[0].trim();
    if (trimmed.length <= 80) return trimmed;
    return trimmed.slice(0, 77) + "...";
}