import { describe, it, expect, vi, afterEach } from "vitest";
import { QdrantStore } from "../../../src/vector/qdrant.js";

describe("QdrantStore", () => {
    let store: QdrantStore;
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal("fetch", fetchMock);
        store = new QdrantStore("http://localhost:6333");
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    function mockJsonResponse(result: any, status = 200) {
        fetchMock.mockResolvedValue({
            ok: status < 400,
            status,
            text: () => Promise.resolve(status >= 400 ? "error" : ""),
            json: () => Promise.resolve({ result, status: "ok" }),
        });
    }

    it("should strip trailing slash from URL", () => {
        const s = new QdrantStore("http://localhost:6333/");
        expect((s as any).baseUrl).toBe("http://localhost:6333");
    });

    it("ensureCollection should create collection if missing", async () => {
        fetchMock.mockResolvedValueOnce({
            ok: true, status: 200,
            text: () => Promise.resolve(""),
            json: () => Promise.resolve({ result: { collections: [] }, status: "ok" }),
        });
        fetchMock.mockResolvedValueOnce({
            ok: true, status: 200,
            text: () => Promise.resolve(""),
            json: () => Promise.resolve({ result: {}, status: "ok" }),
        });

        await store.ensureCollection();
        // First call: GET /collections
        expect(fetchMock).toHaveBeenCalledWith(
            "http://localhost:6333/collections",
            expect.objectContaining({ method: "GET" }),
        );
        // Second call: PUT to create collection
        const secondCall = fetchMock.mock.calls[1];
        expect(secondCall[0]).toBe("http://localhost:6333/collections/memory_chunks");
        expect(JSON.parse(secondCall[1].body).vectors.size).toBe(256);
    });

    it("ensureCollection should skip creation if exists", async () => {
        fetchMock.mockResolvedValueOnce({
            ok: true, status: 200,
            text: () => Promise.resolve(""),
            json: () => Promise.resolve({ result: { collections: [{ name: "memory_chunks" }] }, status: "ok" }),
        });
        await store.ensureCollection();
        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("upsert should send correct payload", async () => {
        mockJsonResponse({});
        await store.upsert("id-1", [0.1, 0.2], { text: "hello", tenantId: "default" });
        expect(fetchMock).toHaveBeenCalledWith(
            "http://localhost:6333/collections/memory_chunks/points",
            expect.objectContaining({ method: "PUT" }),
        );
        const body = JSON.parse(fetchMock.mock.calls[0][1].body);
        expect(body.points[0].id).toBe("id-1");
        expect(body.points[0].vector).toEqual([0.1, 0.2]);
    });

    it("search should POST with vector and filter", async () => {
        mockJsonResponse([
            { id: "p1", score: 0.9, payload: { text: "test", tenantId: "default", kind: "user_message", createdAt: "now" } },
        ]);
        const result = await store.search([0.1, 0.2], { limit: 5, tenantId: "default" });
        expect(fetchMock).toHaveBeenCalledWith(
            "http://localhost:6333/collections/memory_chunks/points/search",
            expect.objectContaining({ method: "POST" }),
        );
        const body = JSON.parse(fetchMock.mock.calls[0][1].body);
        expect(body.vector).toEqual([0.1, 0.2]);
        expect(body.filter.must).toBeDefined();
        expect(result).toHaveLength(1);
        expect(result[0].score).toBe(0.9);
    });

    it("search without tenantId should omit filter", async () => {
        mockJsonResponse([]);
        await store.search([0.1], { limit: 3 });
        const body = JSON.parse(fetchMock.mock.calls[0][1].body);
        expect(body.filter).toBeUndefined();
    });

    it("deleteCollection should send DELETE", async () => {
        mockJsonResponse({});
        await store.deleteCollection();
        expect(fetchMock).toHaveBeenCalledWith(
            "http://localhost:6333/collections/memory_chunks",
            expect.objectContaining({ method: "DELETE" }),
        );
    });

    it("should throw on non-ok response", async () => {
        fetchMock.mockResolvedValue({
            ok: false,
            status: 500,
            text: () => Promise.resolve("Internal error"),
        });
        await expect(store.search([0.1])).rejects.toThrow("Qdrant POST");
    });
});