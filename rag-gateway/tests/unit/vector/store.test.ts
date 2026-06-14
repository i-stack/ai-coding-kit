import { describe, it, expect, vi, beforeEach } from "vitest";
import { VectorStore } from "../../../src/vector/store.js";
import type { ChunkedMessage } from "../../../src/vector/store.js";

describe("VectorStore", () => {
    let store: VectorStore;
    let mockEmbed: any;
    let mockQdrant: any;

    beforeEach(() => {
        mockEmbed = { embed: vi.fn(), embedBatch: vi.fn() };
        mockQdrant = { upsert: vi.fn(), upsertBatch: vi.fn(), search: vi.fn() };
        store = new VectorStore(mockEmbed as any, mockQdrant as any);
    });

    it("chunkMessage should split on double-newlines", () => {
        const msg: ChunkedMessage = {
            id: "1", text: "Para one.\n\nPara two.\n\nPara three.",
            kind: "user_message", tenantId: "default", sourceMessageId: "s1", conversationId: "c1",
        };
        const chunks = store.chunkMessage(msg);
        expect(chunks.length).toBe(3);
        expect(chunks[0].text).toBe("Para one.");
        expect(chunks[1].text).toBe("Para two.");
    });

    it("chunkMessage should split long paragraphs by char boundary", () => {
        const msg: ChunkedMessage = {
            id: "2", text: "A".repeat(1200),
            kind: "user_message", tenantId: "default", sourceMessageId: "s2", conversationId: "c2",
        };
        const chunks = store.chunkMessage(msg, 500);
        expect(chunks.length).toBe(3); // 500 + 500 + 200
    });

    it("chunkMessage empty text returns empty", () => {
        const msg: ChunkedMessage = {
            id: "3", text: "   ",
            kind: "user_message", tenantId: "default", sourceMessageId: "s3", conversationId: "c3",
        };
        expect(store.chunkMessage(msg)).toHaveLength(0);
    });

    it("chunkMessage short text returns single segment", () => {
        const msg: ChunkedMessage = {
            id: "4", text: "Short text",
            kind: "user_message", tenantId: "default", sourceMessageId: "s4", conversationId: "c4",
        };
        expect(store.chunkMessage(msg)).toHaveLength(1);
    });

    it("indexMessage should chunk, embed, and upsert", async () => {
        mockEmbed.embedBatch.mockResolvedValue([[0.1], [0.2]]);
        mockQdrant.upsertBatch.mockResolvedValue(undefined);

        const msg: ChunkedMessage = {
            id: "5", text: "Hello.\n\nWorld.", kind: "user_message",
            tenantId: "default", sourceMessageId: "s5", conversationId: "c5",
        };
        await store.indexMessage(msg);
        expect(mockEmbed.embedBatch).toHaveBeenCalledWith(["Hello.", "World."]);
        expect(mockQdrant.upsertBatch).toHaveBeenCalled();
        const upsertArg = mockQdrant.upsertBatch.mock.calls[0][0];
        expect(upsertArg).toHaveLength(2);
    });

    it("indexMessages should batch all segments across messages", async () => {
        mockEmbed.embedBatch.mockResolvedValue([[0.1]]);
        mockQdrant.upsertBatch.mockResolvedValue(undefined);

        await store.indexMessages([
            { id: "a", text: "Message A", kind: "user_message", tenantId: "default", sourceMessageId: "sa", conversationId: "ca" },
        ]);
        expect(mockEmbed.embedBatch).toHaveBeenCalled();
        expect(mockQdrant.upsertBatch).toHaveBeenCalled();
    });

    it("search should embed query then call qdrant.search", async () => {
        mockEmbed.embed.mockResolvedValue([0.1, 0.2]);
        mockQdrant.search.mockResolvedValue([{ id: "p1", score: 0.9, payload: { text: "test", tenantId: "default", kind: "user_message", createdAt: "now" } }]);

        const results = await store.search("test query", { limit: 3, tenantId: "default" });
        expect(mockEmbed.embed).toHaveBeenCalledWith("test query");
        expect(mockQdrant.search).toHaveBeenCalledWith([0.1, 0.2], { limit: 3, tenantId: "default" });
        expect(results).toHaveLength(1);
    });
});