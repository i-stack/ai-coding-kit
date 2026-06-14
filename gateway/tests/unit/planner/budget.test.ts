import { describe, it, expect } from "vitest";
import { BudgetPlanner, computeRetrievalConstraints, computeToolBudgetLimit, computeOutputBudget, computeMessageTrimBudget } from "../../../src/planner/budget.js";
import type { ContextBudget, NormalizedMessage } from "../../../src/types.js";

describe("BudgetPlanner", () => {
    const planner = new BudgetPlanner();

    function makeMessages(text: string, count = 2): NormalizedMessage[] {
        const msgs: NormalizedMessage[] = [
            { role: "system", content: "You are a helpful assistant." },
            { role: "user", content: text },
        ];
        while (msgs.length < count) {
            msgs.push({ role: "assistant", content: "Response." });
            if (msgs.length < count) {
                msgs.push({ role: "user", content: "Follow up question?" });
            }
        }
        return msgs;
    }

    it("should produce BudgetDecision with all fields", () => {
        const result = planner.plan(makeMessages("What is the capital of France?"));
        expect(result.decision).toBeDefined();
        expect(result.decision.budget).toBeDefined();
        expect(result.decision.intentLabel).toBeDefined();
        expect(result.decision.intentConfidence).toBeDefined();
        expect(result.decision.intentSignal).toBeDefined();
        expect(result.decision.profile).toBeDefined();
        expect(result.decision.adjustments).toBeDefined();
        expect(result.budget).toBeDefined();
        expect(result.budget.intent).toBeDefined();
        expect(result.budget.maxContextTokens).toBeGreaterThan(0);
        expect(result.budget.ragTokens).toBeGreaterThan(0);
        expect(result.budget.reserveTokens).toBeGreaterThanOrEqual(0);
    });

    it("should select coding-edit profile for edit requests", () => {
        const msgs = makeMessages("Please implement a new feature for authentication.");
        const result = planner.plan(msgs);
        expect(result.decision.intentLabel).toBe("coding-edit");
    });

    it("should map 'unknown' intent to 'qa' in ContextBudget", () => {
        const msgs = makeMessages("Random statement with no clear intent here.");
        const result = planner.plan(msgs);
        // If unknown is returned, it maps to "qa"
        if (result.decision.intentLabel === "unknown") {
            expect(result.budget.intent).toBe("qa");
        }
    });

    it("should reduce ragTokens for long user messages (>2000 chars)", () => {
        const longText = "A".repeat(2500);
        const result = planner.plan(makeMessages(longText));
        const adjustments = result.decision.adjustments;
        const hasReduction = adjustments.some((a) => a.includes("reduced ragTokens"));
        expect(hasReduction).toBe(true);
    });

    it("should increase ragTokens for short user messages (<80 chars)", () => {
        const shortText = "Hi there!";
        const result = planner.plan(makeMessages(shortText));
        const adjustments = result.decision.adjustments;
        const hasIncrease = adjustments.some((a) => a.includes("increased ragTokens"));
        expect(hasIncrease).toBe(true);
    });

    it("should increase recentHistoryTokens when there are many messages (>10)", () => {
        const msgs = makeMessages("Hello.", 12);
        const result = planner.plan(msgs);
        const adjustments = result.decision.adjustments;
        const hasIncrease = adjustments.some((a) => a.includes("increased recentHistoryTokens"));
        expect(hasIncrease).toBe(true);
    });

    it("should transfer from history to rag when there are few messages (<=3)", () => {
        const msgs = makeMessages("A question about architecture.", 2);
        const result = planner.plan(msgs);
        const adjustments = result.decision.adjustments;
        const hasTransfer = adjustments.some((a) => a.includes("transferred"));
        expect(hasTransfer).toBe(true);
    });

    it("should cap by global max tokens", () => {
        const cappedPlanner = new BudgetPlanner({ globalMaxTokens: 8000 });
        const msgs = makeMessages("Design question with many details.");
        const result = cappedPlanner.plan(msgs, "System: design helper.");
        expect(result.budget.maxContextTokens).toBe(8000);
    });

    it("should apply custom profile overrides", () => {
        const customPlanner = new BudgetPlanner({
            profiles: {
                "qa": { maxContextTokens: 10000, ragTokens: 2000 },
            },
        });
        const msgs = makeMessages("Could you explain the difference between relational and NoSQL database systems?");
        const result = customPlanner.plan(msgs);
        expect(result.budget.maxContextTokens).toBeLessThanOrEqual(10000);
        // ragTokens starts at 2000 but adjustments (few messages transfer) may increase it
        expect(result.budget.ragTokens).toBeGreaterThanOrEqual(2000);
    });

    it("should handle empty messages array gracefully", () => {
        const result = planner.plan([]);
        expect(result.budget).toBeDefined();
        expect(result.budget.maxContextTokens).toBeGreaterThan(0);
    });

    it("should accumulate adjustments as an array of strings", () => {
        const msgs = makeMessages("A".repeat(2500), 12);
        const result = planner.plan(msgs);
        expect(Array.isArray(result.decision.adjustments)).toBe(true);
    });
});

describe("computeRetrievalConstraints", () => {
    function makeBudget(ragTokens: number): ContextBudget {
        return {
            intent: "qa",
            maxContextTokens: 20000,
            staticPrefixTokens: 4000,
            ragTokens,
            recentHistoryTokens: 5000,
            toolSchemaTokens: 3000,
            reserveTokens: 3000,
        };
    }

    it("should return strict threshold for small RAG budget (<=2000)", () => {
        const budget = makeBudget(2000);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.scoreThreshold).toBe(0.65);
        expect(constraints.maxResults).toBeGreaterThanOrEqual(1);
    });

    it("should return moderate threshold for medium RAG budget (<=6000)", () => {
        const budget = makeBudget(4000);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.scoreThreshold).toBe(0.55);
    });

    it("should return relaxed threshold for larger RAG budget (<=10000)", () => {
        const budget = makeBudget(8000);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.scoreThreshold).toBe(0.45);
    });

    it("should return most permissive threshold for large RAG budget (>10000)", () => {
        const budget = makeBudget(12000);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.scoreThreshold).toBe(0.35);
    });

    it("should cap maxResults at 20", () => {
        const budget = makeBudget(100000);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.maxResults).toBeLessThanOrEqual(20);
    });

    it("should floor maxResults at 1", () => {
        const budget = makeBudget(1);
        const constraints = computeRetrievalConstraints(budget);
        expect(constraints.maxResults).toBeGreaterThanOrEqual(1);
    });
});

describe("computeToolBudgetLimit", () => {
    it("should return 0 when toolSchemaTokens is 0", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 4000, toolSchemaTokens: 0, reserveTokens: 4000,
        };
        expect(computeToolBudgetLimit(budget)).toBe(0);
    });

    it("should return at least 1 for positive budget", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 4000, toolSchemaTokens: 100, reserveTokens: 4000,
        };
        expect(computeToolBudgetLimit(budget)).toBeGreaterThanOrEqual(1);
    });

    it("should compute based on ESTIMATED_TOKENS_PER_TOOL (300)", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 4000, toolSchemaTokens: 3000, reserveTokens: 4000,
        };
        expect(computeToolBudgetLimit(budget)).toBe(10); // 3000 / 300 = 10
    });
});

describe("computeOutputBudget", () => {
    it("should return reserveTokens when >= 512", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 4000, toolSchemaTokens: 2000, reserveTokens: 1000,
        };
        expect(computeOutputBudget(budget)).toBe(1000);
    });

    it("should fall back to 20% of maxContext when reserve is small", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 4000, toolSchemaTokens: 2000, reserveTokens: 100,
        };
        const output = computeOutputBudget(budget);
        expect(output).toBeGreaterThanOrEqual(512);
        expect(output).toBeLessThanOrEqual(3200); // 20% of 16000 = 3200
    });
});

describe("computeMessageTrimBudget", () => {
    it("should return maxHistoryChars as recentHistoryTokens * 4", () => {
        const budget: ContextBudget = {
            intent: "qa", maxContextTokens: 16000, staticPrefixTokens: 4000,
            ragTokens: 4000, recentHistoryTokens: 5000, toolSchemaTokens: 2000, reserveTokens: 1000,
        };
        const trim = computeMessageTrimBudget(budget);
        expect(trim.maxHistoryChars).toBe(20000); // 5000 * 4
    });
});