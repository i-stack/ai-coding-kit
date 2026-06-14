/**
 * Unit tests for db/graph.ts — entity upsert with RETURNING and project_id update.
 *
 * These verify the two P0/P2 fixes:
 *   1. upsertEntities returns a Map of name → persisted ID (the real DB id after
 *      ON CONFLICT, not the in-memory-generated UUID that may have been discarded).
 *   2. The ON CONFLICT UPDATE SET clause includes project_id so cross-project
 *      entity search works correctly.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mock db/index.ts so getPool() returns a controllable pool ────────
// graph.ts calls getPool() which checks a module-level pool variable.
// We mock the module to return a pool whose .connect and .query we control.

const mockQuery = vi.fn();
const mockConnect = vi.fn();
const mockRelease = vi.fn();
const mockClient = { query: mockQuery, release: mockRelease };

vi.mock("../../../src/db/index.js", () => ({
    getPool: vi.fn(() => ({
        query: mockQuery,
        connect: mockConnect,
        end: vi.fn(),
    })),
}));

// Static import — vitest hoists vi.mock above this, so graph.ts sees the mocked getPool
import * as graphDb from "../../../src/db/graph.js";
import type { StoreEntity } from "../../../src/db/graph.js";

beforeEach(() => {
    vi.clearAllMocks();
    mockConnect.mockResolvedValue(mockClient);
    mockRelease.mockResolvedValue(undefined);
});

// ── Test helpers ──────────────────────────────────────────────────────

const baseEntity: StoreEntity = {
    id: "550e8400-e29b-41d4-a716-446655440000",
    tenantId: "tenant-1",
    projectId: "project-1",
    type: "technology",
    name: "PostgreSQL",
    properties: { lang: "SQL" },
};

// ── upsertEntities batch ──────────────────────────────────────────────

describe("upsertEntities [RETURNING fix]", () => {
    it("returns a Map of name → persisted id for new entities", async () => {
        // BEGIN → INSERT … ON CONFLICT … RETURNING → COMMIT
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: baseEntity.id, name: baseEntity.name }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        const result = await graphDb.upsertEntities([baseEntity]);
        expect(result).toBeInstanceOf(Map);
        expect(result.size).toBe(1);
        expect(result.get("PostgreSQL")).toBe("550e8400-e29b-41d4-a716-446655440000");
    });

    it("returns the EXISTING (persisted) id when ON CONFLICT triggers UPDATE", async () => {
        // rows[0].id differs from what we passed in — ON CONFLICT preserved the old id
        const existingId = "a1a1a1a1-b2b2-c3c3-d4d4-e5e5e5e5e5e5";
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: existingId, name: "PostgreSQL" }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        const result = await graphDb.upsertEntities([baseEntity]);
        expect(result.get("PostgreSQL")).toBe(existingId);
        expect(result.get("PostgreSQL")).not.toBe(baseEntity.id);
    });

    it("returns persisted id for each entity in a batch (some new, some existing)", async () => {
        const entities: StoreEntity[] = [
            { ...baseEntity, name: "Redis", id: "id-redis-new" },
            { ...baseEntity, name: "PostgreSQL", id: "id-pg-new" },
            { ...baseEntity, name: "Docker", id: "id-docker-new" },
        ];

        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: "id-redis-new", name: "Redis" }] })
            .mockResolvedValueOnce({ rows: [{ id: "existing-pg-uuid", name: "PostgreSQL" }] })
            .mockResolvedValueOnce({ rows: [{ id: "id-docker-new", name: "Docker" }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        const result = await graphDb.upsertEntities(entities);
        expect(result.size).toBe(3);
        expect(result.get("Redis")).toBe("id-redis-new");
        expect(result.get("PostgreSQL")).toBe("existing-pg-uuid");
        expect(result.get("Docker")).toBe("id-docker-new");
    });

    it("returns an empty Map for an empty array (no SQL run)", async () => {
        const result = await graphDb.upsertEntities([]);
        expect(result).toBeInstanceOf(Map);
        expect(result.size).toBe(0);
        expect(mockQuery).not.toHaveBeenCalled();
        expect(mockConnect).not.toHaveBeenCalled();
    });

    it("handles projectId = undefined by passing null to SQL", async () => {
        const entityNoProject: StoreEntity = { ...baseEntity, projectId: undefined };
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: baseEntity.id, name: baseEntity.name }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        const result = await graphDb.upsertEntities([entityNoProject]);
        expect(result.get(entityNoProject.name)).toBe(baseEntity.id);
    });

    it("rolls back on error and rethrows", async () => {
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockRejectedValueOnce(new Error("FK violation")); // INSERT fails

        await expect(graphDb.upsertEntities([baseEntity])).rejects.toThrow("FK violation");
        expect(mockRelease).toHaveBeenCalled();
    });

    it("includes RETURNING id, name in the SQL", async () => {
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: baseEntity.id, name: baseEntity.name }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        await graphDb.upsertEntities([baseEntity]);

        // The INSERT is the second call (after BEGIN)
        const insertCall = mockQuery.mock.calls[1];
        const sql = insertCall[0] as string;
        expect(sql).toMatch(/RETURNING\s+id\s*,\s*name/i);
    });
});

// ── upsertEntity single ───────────────────────────────────────────────

describe("upsertEntity [single entity, RETURNING fix]", () => {
    it("returns the persisted id string (not void)", async () => {
        mockQuery.mockResolvedValue({ rows: [{ id: baseEntity.id }] });

        const id = await graphDb.upsertEntity(baseEntity);
        expect(id).toBe(baseEntity.id);
    });

    it("returns the existing id on conflict", async () => {
        const existingId = "99999999-8888-7777-6666-555555555555";
        mockQuery.mockResolvedValue({ rows: [{ id: existingId }] });

        const id = await graphDb.upsertEntity(baseEntity);
        expect(id).toBe(existingId);
        expect(id).not.toBe(baseEntity.id);
    });

    it("includes RETURNING id in the SQL", async () => {
        mockQuery.mockResolvedValue({ rows: [{ id: baseEntity.id }] });
        await graphDb.upsertEntity(baseEntity);

        const sql = mockQuery.mock.calls[0][0] as string;
        expect(sql).toMatch(/RETURNING\s+id\b/i);
    });
});

// ── project_id in UPDATE SET (both functions) ─────────────────────────

describe("project_id is updated on ON CONFLICT", () => {
    it("upsertEntity SQL includes project_id = COALESCE(...)", async () => {
        mockQuery.mockResolvedValue({ rows: [{ id: baseEntity.id }] });
        await graphDb.upsertEntity(baseEntity);

        const sql = mockQuery.mock.calls[0][0] as string;
        expect(sql).toMatch(/project_id\s*=/i);
    });

    it("upsertEntities SQL includes project_id = COALESCE(...)", async () => {
        mockQuery
            .mockResolvedValueOnce(undefined) // BEGIN
            .mockResolvedValueOnce({ rows: [{ id: baseEntity.id, name: baseEntity.name }] })
            .mockResolvedValueOnce(undefined); // COMMIT

        await graphDb.upsertEntities([baseEntity]);
        const sql = mockQuery.mock.calls[1][0] as string;
        expect(sql).toMatch(/project_id\s*=/i);
    });
});