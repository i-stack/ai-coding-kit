/**
 * Intent detector — infers request workload type from message patterns.
 *
 * Uses lightweight keyword/pattern analysis on the last user message.
 * No external dependencies; designed for deterministic first-pass intent
 * classification. In future iterations, this can be upgraded to an ML-based
 * classifier or delegated to the model itself via a structured prompt.
 *
 * See docs/universal-rag-gateway.md §Context Budget Planner.
 */
import { NormalizedMessage } from "../types.js";

export type RequestIntent =
    | "coding-edit"
    | "debug"
    | "design"
    | "qa"
    | "unknown";

export interface IntentResult {
    intent: RequestIntent;
    confidence: "high" | "medium" | "low";
    /** Human-readable reason for this classification */
    signal: string;
}

// ── Pattern definitions ────────────────────────────────────────────

interface IntentRule {
    intent: RequestIntent;
    priority: number; // higher = matches first
    patterns: RegExp[];
}

const RULES: IntentRule[] = [
    {
        intent: "debug",
        priority: 40,
        patterns: [
            /\b(debug|bug|error|crash|exception|traceback|stack.?trace|fatal|fix|broken|issue|fail(ing|ed|s)?|wrong|incorrect|unexpected)\b/i,
            /\b(why|root.?cause|reason|explain)\b.*\b(fail|error|crash|broken|bug)\b/i,
            /\b(reproduce|repro|logs?|console)\b/i,
        ],
    },
    {
        intent: "coding-edit",
        priority: 30,
        patterns: [
            /\b(refactor|rewrite|change|modify|update|add|implement|create|build|write|code|implement)\b.*\b(funct|class|file|module|method|impl|feature)\b/i,
            /\b(implement|write|add)\b.*\b(test|spec|unit)\b/i,
            /\b(pr|pull.?request|merge|review)\b/i,
            /\b(commit|push|branch)\b.*\b(code|change|fix)\b/i,
        ],
    },
    {
        intent: "design",
        priority: 20,
        patterns: [
            /\b(design|architecture|migrate|migration|plan|proposal|decision|trade.?off|strategy)\b/i,
            /\b(how\s+should|should\s+we|option|alternative|compare|vs\.?)\b/i,
            /\b(diagram|schema|flow|pipeline|component|module)\b/i,
        ],
    },
    {
        intent: "qa",
        priority: 10,
        patterns: [
            /\b(what|how|why|when|where|who|which)\b.*\?$/im,
            /\b(explain|describe|tell me|define|mean|understand|clarify)\b/i,
            /\b(difference|example|overview|introduction|tutorial|guide)\b/i,
        ],
    },
];

// ── Default fallback ───────────────────────────────────────────────

const DEFAULT_INTENT: RequestIntent = "unknown";

/**
 * Detect the request intent from the message history.
 *
 * Strategy:
 * 1. Extract the last user message (strongest signal).
 * 2. If the last user message is short or absent, look at the system prompt.
 * 3. Apply pattern rules in priority order.
 * 4. Fall back to "unknown".
 */
export function detectIntent(
    messages: NormalizedMessage[],
    systemContent?: string,
): IntentResult {
    // Find the last user message
    const lastUserMsg = findLastUserMessage(messages);

    // Try rules against last user message (strongest signal)
    if (lastUserMsg) {
        const result = classifyByRules(lastUserMsg, RULES);
        if (result && result.confidence !== "low") {
            return result;
        }
    }

    // If no strong signal from user, try system prompt
    if (systemContent) {
        const result = classifyByRules(systemContent, RULES);
        if (result) return result;
    }

    // Fallback: if there's a user message but no rule matched
    if (lastUserMsg) {
        return {
            intent: DEFAULT_INTENT,
            confidence: "low",
            signal: "No intent pattern matched last user message",
        };
    }

    return {
        intent: DEFAULT_INTENT,
        confidence: "low",
        signal: "No user message found",
    };
}

// ── Helpers ────────────────────────────────────────────────────────

function findLastUserMessage(
    messages: NormalizedMessage[],
): string | undefined {
    for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
            const content = messages[i].content;
            if (typeof content === "string" && content.trim().length > 0) {
                return content;
            }
            // ContentPart arrays — join text parts
            if (Array.isArray(content)) {
                const textParts = content
                    .filter((p): p is { type: "text"; text?: string } => p.type === "text")
                    .map((p) => p.text ?? "")
                    .filter(Boolean);
                if (textParts.length > 0) {
                    return textParts.join(" ");
                }
            }
        }
    }
    return undefined;
}

function classifyByRules(
    text: string,
    rules: IntentRule[],
): IntentResult | undefined {
    // Sort by priority descending
    const sorted = [...rules].sort((a, b) => b.priority - a.priority);

    for (const rule of sorted) {
        let matchCount = 0;
        for (const pattern of rule.patterns) {
            if (pattern.test(text)) {
                matchCount++;
            }
        }

        if (matchCount > 0) {
            const confidence: "high" | "medium" | "low" =
                matchCount >= 2 ? "high" : matchCount === 1 ? "medium" : "low";

            return {
                intent: rule.intent,
                confidence,
                signal: `Matched ${matchCount} pattern(s) for "${rule.intent}"`,
            };
        }
    }

    return undefined;
}