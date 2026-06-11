import { describe, it, expect } from "vitest";
import { detectIntent } from "../../../src/planner/intent.js";
import type { NormalizedMessage } from "../../../src/types.js";

describe("detectIntent", () => {
    it("should detect debug intent from error/crash keywords", () => {
        const messages: NormalizedMessage[] = [
            { role: "system", content: "You are a debugger." },
            { role: "user", content: "I'm getting a crash when loading the page. The stack trace shows a null pointer. Can you help me debug this?" },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("debug");
        expect(result.confidence).toBe("high");
        expect(result.signal).toContain("debug");
    });

    it("should detect debug intent from single keyword like 'bug'", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "There's a bug in the login flow." },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("debug");
        expect(result.confidence).toBe("medium");
    });

    it("should detect coding-edit intent from 'implement feature' pattern", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "Please implement a new feature for authentication." },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("coding-edit");
    });

    it("should detect coding-edit from 'refactor class' pattern", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "I need to refactor this class for better performance." },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("coding-edit");
    });

    it("should detect design intent from architecture/trade-off keywords", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "I am designing a microservices architecture. What caching strategy should I use for the trade-offs between consistency and performance?" },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("design");
    });

    it("should detect QA intent from question words", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "What is the difference between SQL and NoSQL databases? Can you explain how indexing works?" },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("qa");
        expect(result.confidence).toBe("high");
    });

    it("should return unknown when no patterns match", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "Just a random statement with no clear intent." },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("unknown");
        expect(result.confidence).toBe("low");
    });

    it("should return unknown with empty messages array", () => {
        const messages: NormalizedMessage[] = [];
        const result = detectIntent(messages);
        expect(result.intent).toBe("unknown");
        expect(result.confidence).toBe("low");
    });

    it("should fall back to system content when no user messages exist", () => {
        const messages: NormalizedMessage[] = [
            { role: "system", content: "Help the user debug their application issues." },
        ];
        const result = detectIntent(messages, "Help the user debug their application issues.");
        expect(result.intent).toBe("debug");
    });

    it("should handle NormalizedContentPart[] content type", () => {
        const messages: NormalizedMessage[] = [
            {
                role: "user",
                content: [
                    { type: "text", text: "Can you explain how caching works in a distributed system?" },
                ],
            },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("qa");
    });

    it("should return unknown for very short messages", () => {
        const messages: NormalizedMessage[] = [
            { role: "user", content: "OK" },
        ];
        const result = detectIntent(messages);
        expect(result.intent).toBe("unknown");
    });
});