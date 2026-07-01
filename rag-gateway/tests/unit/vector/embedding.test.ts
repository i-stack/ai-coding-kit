import { describe, it, expect, vi, beforeEach } from "vitest";
import { EmbeddingService } from "../../../src/vector/embedding.js";
import type { GatewayConfig } from "../../../src/config.js";

const mockConfig = { embeddingApiKey: "test-key", embeddingBaseUrl: "https://api.openai.com/v1", embeddingModel: "text-embedding-3-small" } as GatewayConfig;

describe("EmbeddingService", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it("should store config on construction", () => {
        const svc = new EmbeddingService(mockConfig);
        expect((svc as any).apiKey).toBe("test-key");
        expect((svc as any).baseUrl).toBe("https://api.openai.com/v1");
        expect((svc as any).model).toBe("text-embedding-3-small");
    });

    it("should call fetch and return embedding for single embed", async () => {
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({
                data: [
                    { embedding: [0.1, 0.2, 0.3], index: 0 },
                ],
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const svc = new EmbeddingService(mockConfig);
        const result = await svc.embed("hello world");

        expect(mockFetch).toHaveBeenCalledTimes(1);
        const callUrl = mockFetch.mock.calls[0][0];
        const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
        expect(callUrl).toBe("https://api.openai.com/v1/embeddings");
        expect(callBody.model).toBe("text-embedding-3-small");
        expect(callBody.input).toBe("hello world");
        expect(result).toEqual([0.1, 0.2, 0.3]);
    });

    it("should return embeddings for batch embed", async () => {
        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({
                data: [
                    { embedding: [0.1, 0.2], index: 0 },
                    { embedding: [0.3, 0.4], index: 1 },
                ],
            }),
        });
        vi.stubGlobal("fetch", mockFetch);

        const svc = new EmbeddingService(mockConfig);
        const result = await svc.embedBatch(["a", "b"]);

        expect(mockFetch).toHaveBeenCalledTimes(1);
        const callBody = JSON.parse(mockFetch.mock.calls[0][1].body);
        expect(callBody.input).toEqual(["a", "b"]);
        expect(result).toHaveLength(2);
        expect(result[0]).toEqual([0.1, 0.2]);
        expect(result[1]).toEqual([0.3, 0.4]);
    });

    it("should return empty for empty batch", async () => {
        const svc = new EmbeddingService(mockConfig);
        const result = await svc.embedBatch([]);
        expect(result).toEqual([]);
    });
});