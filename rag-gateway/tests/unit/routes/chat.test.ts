import { describe, it, expect } from "vitest";
import { BudgetPlanner } from "../../../src/planner/budget.js";
import type { NormalizedMessage } from "../../../src/types.js";

// Replicate chat.ts helper functions for testing
function trimMessagesByBudget(
    messages: any[],
    budget: { maxHistoryChars: number },
): any[] {
    if (messages.length <= 2) return messages;
    const systemMsg = messages[0].role === "system" ? messages[0] : undefined;
    const rest = systemMsg ? messages.slice(1) : messages;
    let totalChars = 0;
    const kept: any[] = [];
    for (let i = rest.length - 1; i >= 0; i--) {
        const m = rest[i];
        const charLen = typeof m.content === "string"
            ? m.content.length
            : JSON.stringify(m.content).length;
        const estimatedCost = charLen + 20;
        if (totalChars + estimatedCost > budget.maxHistoryChars) break;
        totalChars += estimatedCost;
        kept.unshift(rest[i]);
    }
    const result = systemMsg ? [systemMsg, ...kept] : kept;
    return result.length > 0 ? result : messages.slice(-2);
}

function mergeDedupedTools(clientTools: any[] | undefined, gatewayTools: any[]) {
    function normalizeClientTool(t: any) {
        return { type: "function", function: { name: t.function.name, description: t.function.description ?? "", parameters: t.function.parameters } };
    }
    if (!clientTools && gatewayTools.length === 0) return undefined;
    if (!clientTools) return gatewayTools;
    if (gatewayTools.length === 0) return clientTools.map(normalizeClientTool);
    const clientNormalized = clientTools.map(normalizeClientTool);
    const clientNames = new Set(clientNormalized.map((t: any) => t.function.name));
    const uniqueGateway = gatewayTools.filter((t) => !clientNames.has(t.function.name));
    return [...clientNormalized, ...uniqueGateway];
}

function maxToolsForModel(model: string): number {
    const lower = model.toLowerCase();
    if (lower.includes("gpt-3.5") || lower.includes("gpt-4-turbo")) return 10;
    if (lower.includes("claude-3-haiku") || lower.includes("claude-3-sonnet")) return 10;
    if (lower.includes("claude-3-opus") || lower.includes("claude-sonnet-4")) return 20;
    if (lower.includes("gpt-4o") || lower.includes("gpt-4.1")) return 20;
    return 20;
}

function normalizeClientTool(t: any) {
    return { type: "function", function: { name: t.function.name, description: t.function.description ?? "", parameters: t.function.parameters } };
}

describe("Chat route helpers", () => {
    // ── trimMessagesByBudget ─────────────────────────────────────────

    it("should keep system message when trimming", () => {
        const messages = [
            { role: "system", content: "You are helpful." },
            { role: "user", content: "Q1" },
            { role: "assistant", content: "A1" },
            { role: "user", content: "Q2" },
            { role: "assistant", content: "A2" },
        ];
        const trimmed = trimMessagesByBudget(messages, { maxHistoryChars: 50 });
        expect(trimmed).toHaveLength(3);
        expect(trimmed[0].role).toBe("system");
        expect(trimmed[trimmed.length - 1].role).toBe("assistant");
    });

    it("should return messages unchanged when <= 2", () => {
        const messages = [{ role: "user", content: "Hi" }];
        const result = trimMessagesByBudget(messages, { maxHistoryChars: 10 });
        expect(result).toBe(messages);
    });

    it("should never return fewer than 2 messages", () => {
        const messages = [
            { role: "system", content: "S" },
            { role: "user", content: "A".repeat(1000) },
        ];
        const trimmed = trimMessagesByBudget(messages, { maxHistoryChars: 10 });
        expect(trimmed.length).toBeGreaterThanOrEqual(2);
    });

    // ── mergeDedupedTools ────────────────────────────────────────────

    it("should deduplicate tools by name (client wins)", () => {
        const client = [{ type: "function", function: { name: "get_time", description: "Client time", parameters: {} } }];
        const gateway = [
            { type: "function", function: { name: "get_time", description: "Gateway time", parameters: {} } },
            { type: "function", function: { name: "other", description: "Other", parameters: {} } },
        ];
        const result = mergeDedupedTools(client, gateway);
        expect(result).toHaveLength(2);
        expect(result![0].function.name).toBe("get_time");
        expect(result![0].function.description).toBe("Client time");
        expect(result![1].function.name).toBe("other");
    });

    it("should return gateway tools when no client tools", () => {
        const gateway = [{ type: "function", function: { name: "t1", description: "T1", parameters: {} } }];
        const result = mergeDedupedTools(undefined, gateway);
        expect(result).toHaveLength(1);
        expect(result![0].function.name).toBe("t1");
    });

    it("should return normalized client tools when no gateway tools", () => {
        const client = [{ type: "function", function: { name: "ct", description: "CT", parameters: {} } }];
        const result = mergeDedupedTools(client, []);
        expect(result).toHaveLength(1);
        expect(result![0].function.name).toBe("ct");
    });

    it("should return undefined when both are empty", () => {
        expect(mergeDedupedTools(undefined, [])).toBeUndefined();
    });

    it("should fill missing client description with empty string", () => {
        const normalized = normalizeClientTool({ type: "function", function: { name: "nt", parameters: {} } });
        expect(normalized.function.description).toBe("");
    });

    // ── maxToolsForModel ─────────────────────────────────────────────

    it("should return correct caps per model", () => {
        expect(maxToolsForModel("gpt-4o")).toBe(20);
        expect(maxToolsForModel("gpt-3.5-turbo")).toBe(10);
        expect(maxToolsForModel("claude-sonnet-4-20250514")).toBe(20);
        expect(maxToolsForModel("claude-3-haiku-20240307")).toBe(10);
        expect(maxToolsForModel("unknown-model")).toBe(20);
    });
});