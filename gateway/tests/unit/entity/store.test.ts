import { describe, it, expect, vi, beforeEach } from "vitest";
import { EntityStore } from "../../../src/entity/store.js";
import type { GatewayConfig } from "../../../src/config.js";

vi.mock("../../../src/db/graph.js", () => ({
    upsertEntities: vi.fn(),
    insertEdges: vi.fn(),
    searchEntities: vi.fn(),
    getSubgraph: vi.fn(),
}));

const mockConfig = { openaiApiKey: "test-key", openaiBaseUrl: "https://api.openai.com/v1", openaiDefaultModel: "gpt-4o", graphRagEnabled: true } as unknown as GatewayConfig;

describe("EntityStore", () => {
    let store: EntityStore;

    beforeEach(() => {
        vi.clearAllMocks();
        store = new EntityStore(mockConfig);
    });

    it("should be enabled when graphRagEnabled is true", () => {
        expect(store.isEnabled).toBe(true);
    });

    it("should return early when disabled", async () => {
        const disabledStore = new EntityStore({ ...mockConfig, graphRagEnabled: false } as unknown as GatewayConfig);
        expect(disabledStore.isEnabled).toBe(false);
        await disabledStore.extractAndStore("text", "default");
        await disabledStore.searchGraph("query", "default");
        // No exception thrown = early return worked
    });

    it("formatContext should produce correct output", () => {
        const lines = store.formatContext([{
            entity: { id: "e1", tenantId: "default", type: "project", name: "MyApp", properties: {}, createdAt: new Date() },
            relations: [{
                relation: { id: "r1", tenantId: "default", fromEntityId: "e1", toEntityId: "e2", relation: "uses", properties: {}, createdAt: new Date() },
                fromEntity: { id: "e1", tenantId: "default", type: "project", name: "MyApp", properties: {}, createdAt: new Date() },
                toEntity: { id: "e2", tenantId: "default", type: "technology", name: "Redis", properties: {}, createdAt: new Date() },
            }],
        }]);
        expect(lines[0]).toContain('[entity] "MyApp"');
        expect(lines[1]).toContain('[entity-relationship] "MyApp"');
        expect(lines[1]).toContain("uses");
        expect(lines[1]).toContain("Redis");
    });

    it("formatContext should deduplicate relations", () => {
        const lines = store.formatContext([{
            entity: { id: "e1", tenantId: "default", type: "project", name: "MyApp", properties: {}, createdAt: new Date() },
            relations: [
                {
                    relation: { id: "r1", tenantId: "default", fromEntityId: "e1", toEntityId: "e2", relation: "uses", properties: {}, createdAt: new Date() },
                    fromEntity: { id: "e1", tenantId: "default", type: "project", name: "MyApp", properties: {}, createdAt: new Date() },
                    toEntity: { id: "e2", tenantId: "default", type: "technology", name: "Redis", properties: {}, createdAt: new Date() },
                },
                {
                    relation: { id: "r1", tenantId: "default", fromEntityId: "e1", toEntityId: "e2", relation: "uses", properties: {}, createdAt: new Date() },
                    fromEntity: { id: "e1", tenantId: "default", type: "project", name: "MyApp", properties: {}, createdAt: new Date() },
                    toEntity: { id: "e2", tenantId: "default", type: "technology", name: "Redis", properties: {}, createdAt: new Date() },
                },
            ],
        }]);
        // Same relation.id + from + to combination should be deduplicated
        const relationLines = lines.filter((l) => l.includes("[entity-relationship]"));
        expect(relationLines).toHaveLength(1);
    });
});