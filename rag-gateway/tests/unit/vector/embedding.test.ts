import { describe, it, expect, vi, beforeEach } from "vitest";
import { EmbeddingService } from "../../../src/vector/embedding.js";
import type { GatewayConfig } from "../../../src/config.js";

const mockConfig = { openaiApiKey: "test-key", openaiBaseUrl: "https://api.openai.com/v1" } as GatewayConfig;

describe("EmbeddingService", () => {
    it("should store config on construction", () => {
        const svc = new EmbeddingService(mockConfig);
        expect((svc as any).client).toBeDefined();
    });

    it("should call embeddings.create for single embed", async () => {
        const svc = new EmbeddingService(mockConfig);
        const mockCreate = vi.fn().mockResolvedValue({
            data: [{ embedding: [0.1, 0.2, 0.3], index: 0 }],
            model: "bge-m3",
        });
        (svc as any).client = { embeddings: { create: mockCreate } };

        const result = await svc.embed("hello world");
        expect(mockCreate).toHaveBeenCalledWith({ model: "bge-m3", input: "hello world" });
        expect(result).toEqual([0.1, 0.2, 0.3]);
    });

    it("should call embeddings.create for batch embed", async () => {
        const svc = new EmbeddingService(mockConfig);
        const mockCreate = vi.fn().mockResolvedValue({
            data: [
                { embedding: [0.1, 0.2], index: 0 },
                { embedding: [0.3, 0.4], index: 1 },
            ],
            model: "bge-m3",
        });
        (svc as any).client = { embeddings: { create: mockCreate } };

        const result = await svc.embedBatch(["a", "b"]);
        expect(mockCreate).toHaveBeenCalledWith({ model: "bge-m3", input: ["a", "b"] });
        expect(result).toHaveLength(2);
    });

    it("should return empty for empty batch", async () => {
        const svc = new EmbeddingService(mockConfig);
        const result = await svc.embedBatch([]);
        expect(result).toEqual([]);
    });
});