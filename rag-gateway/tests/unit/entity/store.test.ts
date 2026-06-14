/**
 * Integration tests for EntityStore + db/graph.ts — verifies that extractAndStore
 * correctly uses persisted IDs from upsertEntities when building edges.
 *
 * This is the critical P0 fix: previously, extractAndStore used in-memory UUIDs
 * for edges, causing FK violations when ON CONFLICT discarded those UUIDs.
 * Now it merges the DB-returned ids into the name→id map before constructing edges.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// vi.mock factories are hoisted — use vi.hoisted() for shared references
const { mockUpsertEntities, mockInsertEdges, mockSearchEntities, mockGetSubgraph } = vi.hoisted(() => ({
    mockUpsertEntities: vi.fn(),
    mockInsertEdges: vi.fn(),
    mockSearchEntities: vi.fn(),
    mockGetSubgraph: vi.fn(),
}));

vi.mock("../../../src/db/graph.js", () => ({
    upsertEntities: mockUpsertEntities,
    insertEdges: mockInsertEdges,
    searchEntities: mockSearchEntities,
    getSubgraph: mockGetSubgraph,
}));

const { mockExtract } = vi.hoisted(() => ({
    mockExtract: vi.fn(),
}));

vi.mock("../../../src/entity/extractor.js", () => ({
    EntityExtractor: class {
        extract = mockExtract;
    },
}));

import { EntityStore } from "../../../src/entity/store.js";
import type { GatewayConfig } from "../../../src/config.js";

const mockConfig = {
    openaiApiKey: "test-key",
    openaiBaseUrl: "https://api.openai.com/v1",
    openaiDefaultModel: "gpt-4o",
    graphRagEnabled: true,
} as unknown as GatewayConfig;

describe("EntityStore.extractAndStore [persisted ID forwarding]", () => {
    let store: EntityStore;

    beforeEach(() => {
        vi.clearAllMocks();
        store = new EntityStore(mockConfig);
    });

    it("uses persisted IDs from upsertEntities (not in-memory UUIDs) for edge refs", async () => {
        mockExtract.mockResolvedValue({
            entities: [
                { type: "project", name: "MyApp", properties: {} },
                { type: "technology", name: "PostgreSQL", properties: {} },
            ],
            relationships: [
                { from: "MyApp", to: "PostgreSQL", relation: "uses", properties: {} },
            ],
        });

        // Simulate ON CONFLICT: upsertEntities returns DIFFERENT IDs than the
        // in-memory ones — this is the scenario that used to cause FK violations.
        const persistedMyAppId = "11111111-1111-1111-1111-111111111111";
        const persistedPgId = "22222222-2222-2222-2222-222222222222";
        mockUpsertEntities.mockResolvedValue(
            new Map([
                ["MyApp", persistedMyAppId],
                ["PostgreSQL", persistedPgId],
            ]),
        );

        await store.extractAndStore("MyApp uses PostgreSQL", "tenant-1", "project-1");

        // insertEdges must be called with the PERSISTED IDs (not the random UUIDs
        // that extractAndStore generated in-memory before calling upsertEntities)
        expect(mockInsertEdges).toHaveBeenCalledTimes(1);
        const edgesArg = mockInsertEdges.mock.calls[0][0];
        expect(edgesArg).toHaveLength(1);

        const edge = edgesArg[0];
        expect(edge.fromEntityId).toBe(persistedMyAppId);
        expect(edge.toEntityId).toBe(persistedPgId);
    });

    it("does not insert edges when a relationship references an entity not in the batch", async () => {
        mockExtract.mockResolvedValue({
            entities: [
                { type: "project", name: "MyApp", properties: {} },
            ],
            relationships: [
                { from: "MyApp", to: "MissingEntity", relation: "depends_on", properties: {} },
            ],
        });

        mockUpsertEntities.mockResolvedValue(
            new Map([["MyApp", "persisted-myapp-id"]]),
        );

        await store.extractAndStore("MyApp depends on something missing", "tenant-1");
        expect(mockInsertEdges).not.toHaveBeenCalled();
    });

    it("does not insert edges when no entities were extracted", async () => {
        mockExtract.mockResolvedValue({
            entities: [],
            relationships: [],
        });

        await store.extractAndStore("Nothing useful", "tenant-1");
        expect(mockUpsertEntities).not.toHaveBeenCalled();
        expect(mockInsertEdges).not.toHaveBeenCalled();
    });

    it("skips duplicate entity names within the same batch", async () => {
        mockExtract.mockResolvedValue({
            entities: [
                { type: "project", name: "MyApp", properties: {} },
                { type: "project", name: "MyApp", properties: { note: "duplicate" } },
            ],
            relationships: [],
        });

        mockUpsertEntities.mockResolvedValue(new Map([["MyApp", "persisted-myapp-id"]]));

        await store.extractAndStore("MyApp mentioned twice", "tenant-1");
        expect(mockUpsertEntities).toHaveBeenCalledTimes(1);
        const upsertArg = mockUpsertEntities.mock.calls[0][0];
        expect(upsertArg).toHaveLength(1);
    });
});

describe("EntityStore.searchGraph", () => {
    let store: EntityStore;

    beforeEach(() => {
        vi.clearAllMocks();
        store = new EntityStore(mockConfig);
    });

    it("returns empty array when searchEntities returns nothing", async () => {
        mockSearchEntities.mockResolvedValue([]);

        const result = await store.searchGraph("query", "tenant-1");
        expect(result).toEqual([]);
        expect(mockGetSubgraph).not.toHaveBeenCalled();
    });

    it("searches with projectId filter when provided", async () => {
        mockSearchEntities.mockResolvedValue([]);

        await store.searchGraph("query", "tenant-1", { projectId: "proj-1" });
        expect(mockSearchEntities).toHaveBeenCalledWith(
            "query",
            "tenant-1",
            expect.objectContaining({ projectId: "proj-1", limit: 5 }),
        );
    });
});