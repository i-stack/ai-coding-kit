import { describe, it, expect, vi, beforeEach } from "vitest";
import { EntityExtractor } from "../../../src/entity/extractor.js";
import type { GatewayConfig } from "../../../src/config.js";

const mockConfig = { openaiApiKey: "test-key", openaiBaseUrl: "https://api.openai.com/v1", openaiDefaultModel: "gpt-4o" } as unknown as GatewayConfig;

describe("EntityExtractor", () => {
    let extractor: EntityExtractor;

    beforeEach(() => {
        extractor = new EntityExtractor(mockConfig);
    });

    it("should return null for text < 20 chars", async () => {
        expect(await extractor.extract("short")).toBeNull();
    });

    it("should send correct prompt and parse JSON response", async () => {
        const mockCreate = vi.fn().mockResolvedValue({
            choices: [{
                message: {
                    content: JSON.stringify({
                        entities: [{ type: "project", name: "MyApp", properties: {} }],
                        relationships: [{ from: "MyApp", to: "DB", relation: "uses", properties: {} }],
                    }),
                },
            }],
        });
        (extractor as any).client = { chat: { completions: { create: mockCreate } } };

        const result = await extractor.extract("MyApp uses PostgreSQL as its database.");
        expect(mockCreate).toHaveBeenCalledWith(
            expect.objectContaining({
                response_format: { type: "json_object" },
                temperature: 0.1,
            }),
        );
        expect(result).not.toBeNull();
        expect(result!.entities).toHaveLength(1);
        expect(result!.relationships).toHaveLength(1);
    });

    it("should return null on invalid JSON response", async () => {
        const mockCreate = vi.fn().mockResolvedValue({
            choices: [{ message: { content: "not json" } }],
        });
        (extractor as any).client = { chat: { completions: { create: mockCreate } } };
        expect(await extractor.extract("Some valid text that is long enough for entity extraction.")).toBeNull();
    });

    it("should return null when entities/relationships are missing", async () => {
        const mockCreate = vi.fn().mockResolvedValue({
            choices: [{ message: { content: '{"foo":"bar"}' } }],
        });
        (extractor as any).client = { chat: { completions: { create: mockCreate } } };
        expect(await extractor.extract("Some valid text for the purpose of testing entity extraction behavior.")).toBeNull();
    });

    it("should return null on API error (catch and log)", async () => {
        const mockCreate = vi.fn().mockRejectedValue(new Error("API Error"));
        (extractor as any).client = { chat: { completions: { create: mockCreate } } };
        expect(await extractor.extract("Some valid text that is long enough for entity extraction purposes.")).toBeNull();
    });
});