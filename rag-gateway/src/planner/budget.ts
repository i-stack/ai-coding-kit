/**
 * Context Budget Planner — allocates the prompt budget before retrieval.
 *
 * This is the first step in the gateway processing pipeline. Given the
 * incoming messages, the planner:
 *   1. Classifies the request intent (coding-edit, debug, design, qa)
 *   2. Sets token allocations per section of the final prompt
 *   3. Returns a ContextBudget that downstream stages (memory retrieval,
 *      tool injection, prompt assembly) use to constrain their output
 *
 * See docs/universal-rag-gateway.md §Context Budget Planner.
 */
import type { ContextBudget } from "../types.js";
import type { NormalizedMessage } from "../types.js";
import { detectIntent, type RequestIntent } from "./intent.js";

// ── Allocation profiles ────────────────────────────────────────────

/**
 * Per-intent token allocation profile.
 *
 * Each field represents a share of maxContextTokens that a given section
 * of the assembled prompt may consume. The sum of all fields should be
 * ≤ maxContextTokens; the planner reserves the difference for overhead.
 */
export interface BudgetProfile {
    maxContextTokens: number;
    staticPrefixTokens: number;
    ragTokens: number;
    recentHistoryTokens: number;
    toolSchemaTokens: number;
}

const DEFAULT_PROFILES: Record<RequestIntent, BudgetProfile> = {
    "coding-edit": {
        maxContextTokens: 16000,
        staticPrefixTokens: 4000,
        ragTokens: 2000, // small, high precision
        recentHistoryTokens: 6000,
        toolSchemaTokens: 2000,
    },
    debug: {
        maxContextTokens: 24000,
        staticPrefixTokens: 4000,
        ragTokens: 8000, // medium — logs, reproduction, recent changes
        recentHistoryTokens: 6000,
        toolSchemaTokens: 3000,
    },
    design: {
        maxContextTokens: 32000,
        staticPrefixTokens: 6000,
        ragTokens: 12000, // medium to large — decisions, constraints, proposals
        recentHistoryTokens: 8000,
        toolSchemaTokens: 3000,
    },
    qa: {
        maxContextTokens: 20000,
        staticPrefixTokens: 4000,
        ragTokens: 6000, // medium — source snippets and citations
        recentHistoryTokens: 5000,
        toolSchemaTokens: 3000,
    },
    // Fallback for unclassified intent — conservative but balanced
    unknown: {
        maxContextTokens: 16000,
        staticPrefixTokens: 4000,
        ragTokens: 4000,
        recentHistoryTokens: 5000,
        toolSchemaTokens: 2000,
    },
};

// ── Budget decision (audit trail) ──────────────────────────────────

/**
 * Full budget decision emitted to telemetry for auditability.
 *
 * Tracks both the allocation plan and the runtime signals that produced it.
 */
export interface BudgetDecision {
    /** Final allocated budget (ready to use) */
    budget: ContextBudget;
    /** Intent classification result */
    intentLabel: RequestIntent;
    intentConfidence: "high" | "medium" | "low";
    intentSignal: string;
    /** Profile used as the starting allocation */
    profile: BudgetProfile;
    /** Any adjustments applied on top of the profile */
    adjustments: string[];
    /** User message length in chars (heuristic signal) */
    userMessageLength: number;
    /** Number of messages in the request */
    messageCount: number;
}

// ── Planner class ──────────────────────────────────────────────────

export interface BudgetPlannerOptions {
    /** Override default profiles keyed by intent */
    profiles?: Partial<Record<RequestIntent, Partial<BudgetProfile>>>;
    /** Global max context token limit (capped by model context window) */
    globalMaxTokens?: number;
}

export class BudgetPlanner {
    private profiles: Record<RequestIntent, BudgetProfile>;
    private globalMaxTokens: number;

    constructor(opts?: BudgetPlannerOptions) {
        // Merge default profiles with overrides
        this.profiles = { ...DEFAULT_PROFILES };
        if (opts?.profiles) {
            for (const [intent, override] of Object.entries(opts.profiles)) {
                if (override) {
                    this.profiles[intent as RequestIntent] = {
                        ...this.profiles[intent as RequestIntent],
                        ...override,
                    };
                }
            }
        }
        this.globalMaxTokens = opts?.globalMaxTokens ?? 64000;
    }

    /**
     * Plan the context budget for a request.
     *
     * Steps:
     *   1. Detect intent from user messages
     *   2. Look up the allocation profile
     *   3. Cap by global max tokens
     *   4. Adjust based on message characteristics
     *   5. Return auditable BudgetDecision + ContextBudget
     */
    plan(
        messages: NormalizedMessage[],
        systemContent?: string,
    ): { decision: BudgetDecision; budget: ContextBudget } {
        // Step 1: Detect intent
        const intentResult = detectIntent(messages, systemContent);

        // Map "unknown" intent to a valid ContextBudget intent
        const validIntent =
            intentResult.intent === "unknown" ? "qa" : (intentResult.intent as ContextBudget["intent"]);

        // Step 2: Look up profile
        const profile = { ...this.profiles[intentResult.intent] };

        // Step 3: Cap by global max tokens
        const maxContext = Math.min(profile.maxContextTokens, this.globalMaxTokens);

        // Step 4: Adjust based on message characteristics
        const adjustments: string[] = [];
        const lastUserMsg = findLastUserText(messages);
        const userMessageLength = lastUserMsg?.length ?? 0;

        // Long user messages → reduce rag tokens since the query is self-contained
        if (userMessageLength > 2000) {
            const reduction = Math.min(profile.ragTokens, 2000);
            profile.ragTokens = Math.max(profile.ragTokens - reduction, 500);
            adjustments.push(
                `Long user message (${userMessageLength} chars): reduced ragTokens by ${reduction}`,
            );
        }

        // Short user messages → more room for context
        if (userMessageLength > 0 && userMessageLength < 80) {
            const extra = Math.min(profile.ragTokens + 1000, maxContext * 0.5);
            profile.ragTokens = Math.round(extra);
            adjustments.push(
                `Short user message (${userMessageLength} chars): increased ragTokens`,
            );
        }

        // Many messages → increase recent history budget
        const messageCount = messages.length;
        if (messageCount > 10) {
            const extraHistory = Math.min(2000, profile.recentHistoryTokens * 0.5);
            profile.recentHistoryTokens = Math.round(
                profile.recentHistoryTokens + extraHistory,
            );
            adjustments.push(
                `Many messages (${messageCount}): increased recentHistoryTokens by ${extraHistory}`,
            );
        }

        // Few messages → reduce history budget, give to rag
        if (messageCount <= 3 && userMessageLength > 0) {
            const transfer = Math.min(profile.recentHistoryTokens * 0.5, 3000);
            profile.recentHistoryTokens = Math.max(
                Math.round(profile.recentHistoryTokens - transfer),
                1000,
            );
            profile.ragTokens = Math.round(profile.ragTokens + transfer);
            adjustments.push(
                `Few messages (${messageCount}): transferred ${transfer} from history to rag`,
            );
        }

        // Compute reserve: tokens left after all allocations
        const reserveTokens = Math.max(
            0,
            maxContext -
            profile.staticPrefixTokens -
            profile.ragTokens -
            profile.recentHistoryTokens -
            profile.toolSchemaTokens,
        );

        // Step 5: Build output
        const budget: ContextBudget = {
            intent: validIntent,
            maxContextTokens: maxContext,
            staticPrefixTokens: profile.staticPrefixTokens,
            ragTokens: profile.ragTokens,
            recentHistoryTokens: profile.recentHistoryTokens,
            toolSchemaTokens: profile.toolSchemaTokens,
            reserveTokens,
        };

        const decision: BudgetDecision = {
            budget,
            intentLabel: intentResult.intent,
            intentConfidence: intentResult.confidence,
            intentSignal: intentResult.signal,
            profile: { ...profile, maxContextTokens: maxContext },
            adjustments,
            userMessageLength,
            messageCount,
        };

        return { decision, budget };
    }
}

// ── Downstream constraint helpers ──────────────────────────────────

/**
 * Rough token estimate: ~4 chars per token for English text.
 * Used to convert token budgets into actionable constraints.
 */
const CHARS_PER_TOKEN = 4;
/** Estimated tokens per retrieval chunk after embedding */
const ESTIMATED_TOKENS_PER_CHUNK = 250;
/** Estimated tokens per tool schema entry (before simplification) */
const ESTIMATED_TOKENS_PER_TOOL = 300;

/**
 * Compute retrieval constraints from a ContextBudget.
 *
 * Converts ragTokens budget into:
 *   - maxResults: how many chunks to retrieve from Qdrant
 *   - scoreThreshold: minimum relevance score (tighter when budget is small)
 */
export interface RetrievalConstraints {
    maxResults: number;
    scoreThreshold: number;
}

export function computeRetrievalConstraints(budget: ContextBudget): RetrievalConstraints {
    // Max chunks = ragToken budget divided by estimated tokens per chunk
    const raw = Math.floor(budget.ragTokens / ESTIMATED_TOKENS_PER_CHUNK);
    const maxResults = Math.max(1, Math.min(raw, 20));

    // Score threshold: tighter filter for smaller RAG budgets
    let scoreThreshold: number;
    if (budget.ragTokens <= 2000) {
        scoreThreshold = 0.65; // very selective — coding-edit
    } else if (budget.ragTokens <= 6000) {
        scoreThreshold = 0.55; // moderately selective
    } else if (budget.ragTokens <= 10000) {
        scoreThreshold = 0.45; // relaxed
    } else {
        scoreThreshold = 0.35; // permissive — design migrations
    }

    return { maxResults, scoreThreshold };
}

/**
 * Compute the maximum number of tools to inject based on toolSchemaTokens budget.
 *
 * Use alongside the per-model static cap: final = min(modelCap, budgetCap)
 */
export function computeToolBudgetLimit(budget: ContextBudget): number {
    const raw = Math.floor(budget.toolSchemaTokens / ESTIMATED_TOKENS_PER_TOOL);
    // Always allow at least 1 tool (unless budget is explicitly 0)
    return budget.toolSchemaTokens === 0 ? 0 : Math.max(1, raw);
}

/**
 * Compute the provider max_tokens value from the ContextBudget.
 *
 * Uses reserveTokens as the output budget — tokens that weren't allocated
 * to input sections (prefix, RAG, history, tools) are available for generation.
 * Falls back to a safe default if reserve is unreasonably small.
 */
export function computeOutputBudget(budget: ContextBudget): number {
    if (budget.reserveTokens >= 512) {
        return budget.reserveTokens;
    }
    // If reserve is tight, carve out 20% of maxContext as output budget
    return Math.max(512, Math.floor(budget.maxContextTokens * 0.2));
}

/**
 * Compute how many recent conversation messages should be kept in the prompt,
 * based on recentHistoryTokens.
 *
 * Used to trim the messages array before passing to the provider, keeping
 * the most recent messages that fit within budget.
 */
export function computeMessageTrimBudget(budget: ContextBudget): {
    /** Max characters the message history may consume */
    maxHistoryChars: number;
} {
    return {
        maxHistoryChars: budget.recentHistoryTokens * CHARS_PER_TOKEN,
    };
}

/**
 * Estimate how many tokens a tool schema entry consumes.
 * Useful for tool injection decisions.
 */
export const ESTIMATED_TOOL_TOKENS = ESTIMATED_TOKENS_PER_TOOL;

function findLastUserText(messages: NormalizedMessage[]): string | undefined {
    for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
            const content = messages[i].content;
            if (typeof content === "string" && content.trim().length > 0) {
                return content;
            }
            if (Array.isArray(content)) {
                const parts = content
                    .filter((p) => p.type === "text")
                    .map((p) => (p as { text?: string }).text ?? "")
                    .filter(Boolean);
                if (parts.length > 0) return parts.join(" ");
            }
        }
    }
    return undefined;
}