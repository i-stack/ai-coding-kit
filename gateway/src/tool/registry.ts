import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ToolSpec, ToolRecord, ToolStatus } from "./types.js";
import crypto from "node:crypto";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Check if a model name matches a pattern (supports glob: "claude-*", or exact match).
 */
function modelMatches(model: string, pattern: string): boolean {
  if (pattern === "*") return true;
  if (pattern.endsWith("-*")) {
    return model.startsWith(pattern.slice(0, -2));
  }
  return model === pattern;
}

/**
 * ToolRegistry loads declarative tool specs from a JSON file and
 * provides filtered views for injection into requests.
 *
 * In later iterations, this will also load from PostgreSQL.
 */
export class ToolRegistry {
  private tools: Map<string, ToolRecord> = new Map();

  constructor() {}

  /**
   * Load tool specs from a JSON file.
   * File format: { "tools": ToolSpec[] } or ToolSpec[].
   */
  loadFromFile(filePath?: string): void {
    const resolvedPath = filePath ?? path.resolve(__dirname, "../../tools.json");
    if (!fs.existsSync(resolvedPath)) {
      console.log(`⚠️  Tool registry file not found: ${resolvedPath} — no tools loaded`);
      return;
    }

    const raw = JSON.parse(fs.readFileSync(resolvedPath, "utf-8"));
    const specs: ToolSpec[] = Array.isArray(raw) ? raw : raw.tools;

    if (!Array.isArray(specs)) {
      console.warn("⚠️  tools.json has unexpected format — expected array or { tools: [] }");
      return;
    }

    for (const spec of specs) {
      if (!spec.name || !spec.executor) {
        console.warn(`⚠️  Skipping invalid tool spec: missing name or executor`);
        continue;
      }
      const record: ToolRecord = {
        ...spec,
        id: crypto.randomUUID(),
        status: "active",
        createdAt: new Date().toISOString(),
      };
      this.tools.set(spec.name, record);
    }

    console.log(`🔧 Tool registry loaded: ${this.tools.size} tools`);
  }

  /**
   * Register a single tool spec programmatically.
   */
  register(spec: ToolSpec): void {
    const record: ToolRecord = {
      ...spec,
      id: crypto.randomUUID(),
      status: "active",
      createdAt: new Date().toISOString(),
    };
    this.tools.set(spec.name, record);
  }

  /**
   * Get all active tools, optionally filtered by model compatibility.
   */
  getActiveTools(model?: string): ToolSpec[] {
    const results: ToolSpec[] = [];
    for (const tool of this.tools.values()) {
      if (tool.status !== "active") continue;
      if (tool.internal) continue;
      if (model && !this.shouldInjectTool(tool, model)) continue;
      results.push(tool);
    }
    return results;
  }

  /**
   * Check whether a tool should be injected for a given model.
   * Blocklist (disableForModels) is checked first; then allowlist (compatibleModels).
   * No allowlist = available to all unblocked models.
   */
  shouldInjectTool(spec: ToolSpec, model: string): boolean {
    // Blocklist check — if any pattern matches, exclude immediately
    if (spec.disableForModels) {
      for (const pattern of spec.disableForModels) {
        if (modelMatches(model, pattern)) return false;
      }
    }

    // Allowlist: if compatibleModels exists, model must match one
    if (spec.compatibleModels && spec.compatibleModels.length > 0) {
      for (const pattern of spec.compatibleModels) {
        if (modelMatches(model, pattern)) return true;
      }
      return false;
    }

    // No allowlist = available to all models (that aren't blocked)
    return true;
  }

  /**
   * Resolve a per-model tool_choice policy by checking all active tools'
   * toolChoicePolicy maps. First matching policy wins.
   */
  resolveToolChoicePolicy(
    model: string,
  ): "auto" | "any" | "none" | "required" | undefined {
    for (const tool of this.tools.values()) {
      if (tool.status !== "active") continue;
      if (!tool.toolChoicePolicy) continue;
      for (const [pattern, choice] of Object.entries(tool.toolChoicePolicy)) {
        if (modelMatches(model, pattern)) return choice;
      }
    }
    return undefined;
  }

  /**
   * Get a tool spec by name.
   */
  get(name: string): ToolSpec | undefined {
    return this.tools.get(name);
  }

  /**
   * Convert ToolSpec to OpenAI-compatible tool definition.
   */
  toOpenAITool(spec: ToolSpec): {
    type: "function";
    function: {
      name: string;
      description: string;
      parameters: Record<string, unknown>;
    };
  } {
    return {
      type: "function",
      function: {
        name: spec.name,
        description: spec.description,
        parameters: spec.input_schema as unknown as Record<string, unknown>,
      },
    };
  }

  /**
   * Convert all active tools to OpenAI-compatible format.
   */
  toOpenAITools(model?: string): Array<{
    type: "function";
    function: { name: string; description: string; parameters: Record<string, unknown> };
  }> {
    return this.getActiveTools(model).map((t) => this.toOpenAITool(t));
  }

  /**
   * Total count of registered tools.
   */
  get count(): number {
    return this.tools.size;
  }
}