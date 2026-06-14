/**
 * PostgreSQL CRUD for GraphRAG entity and entity_edge tables.
 *
 * Follows the same pattern as db/transcript.ts — one query module per domain,
 * using getPool() for the connection pool.
 */
import crypto from "node:crypto";
import { getPool } from "./index.js";
import type { GraphEntity, GraphRelation } from "../types.js";

// ── Stop words filtered out during entity search tokenization ──────
const STOP_WORDS = new Set([
	"what", "which", "where", "when", "why", "how", "the", "this", "that",
	"does", "is", "are", "was", "were", "will", "would", "could", "should",
	"have", "has", "had", "do", "did", "can", "has", "for", "and", "not",
	"with", "its", "use", "uses", "used", "using", "get", "got", "gets",
]);

export interface StoreEntity {
	id: string;
	tenantId: string;
	projectId?: string;
	type: string;
	name: string;
	properties: Record<string, unknown>;
}

export interface StoreEdge {
	id: string;
	tenantId: string;
	projectId?: string;
	fromEntityId: string;
	toEntityId: string;
	relation: string;
	properties: Record<string, unknown>;
}

/**
 * Upsert a single entity by (name, tenant_id).
 * If an entity with the same name + tenant exists, its type, project_id, and properties are updated.
 * Returns the real persisted ID (the existing one when a conflict occurs).
 */
export async function upsertEntity(entity: StoreEntity): Promise<string> {
	const pool = getPool();
	const result = await pool.query(
		`INSERT INTO entity (id, tenant_id, project_id, type, name, properties)
		 VALUES ($1, $2, $3, $4, $5, $6)
		 ON CONFLICT (name, tenant_id) DO UPDATE SET
		   type = COALESCE(NULLIF($4, ''), entity.type),
		   project_id = COALESCE(NULLIF($3, ''), entity.project_id),
		   properties = entity.properties || $6
		 RETURNING id`,
		[
			entity.id,
			entity.tenantId,
			entity.projectId ?? null,
			entity.type,
			entity.name,
			JSON.stringify(entity.properties),
		],
	);
	return result.rows[0].id as string;
}

/**
 * Batch upsert entities and return a map of name → persisted ID.
 *
 * Each entity that shares (name, tenant_id) with an existing row updates it
 * and returns the real (existing) ID. New entities return their inserted ID.
 * The returned map allows callers to build foreign-key references with the
 * correct IDs rather than in-memory-generated IDs that ON CONFLICT discarded.
 */
export async function upsertEntities(entities: StoreEntity[]): Promise<Map<string, string>> {
	if (entities.length === 0) return new Map();

	const pool = getPool();
	const client = await pool.connect();
	const nameToId = new Map<string, string>();
	try {
		await client.query("BEGIN");
		for (const e of entities) {
			const result = await client.query(
				`INSERT INTO entity (id, tenant_id, project_id, type, name, properties)
				 VALUES ($1, $2, $3, $4, $5, $6)
				 ON CONFLICT (name, tenant_id) DO UPDATE SET
				   type = COALESCE(NULLIF($4, ''), entity.type),
				   project_id = COALESCE(NULLIF($3, ''), entity.project_id),
				   properties = entity.properties || $6
				 RETURNING id, name`,
				[
					e.id,
					e.tenantId,
					e.projectId ?? null,
					e.type,
					e.name,
					JSON.stringify(e.properties),
				],
			);
			const row = result.rows[0];
			nameToId.set(row.name as string, row.id as string);
		}
		await client.query("COMMIT");
	} catch (err) {
		await client.query("ROLLBACK");
		throw err;
	} finally {
		client.release();
	}
	return nameToId;
}

/**
 * Insert a single edge (idempotent — skips on conflict by id).
 */
export async function insertEdge(edge: StoreEdge): Promise<void> {
	const pool = getPool();
	await pool.query(
		`INSERT INTO entity_edge (id, tenant_id, project_id, from_entity_id, to_entity_id, relation, properties)
		 VALUES ($1, $2, $3, $4, $5, $6, $7)
		 ON CONFLICT (id) DO NOTHING`,
		[
			edge.id,
			edge.tenantId,
			edge.projectId ?? null,
			edge.fromEntityId,
			edge.toEntityId,
			edge.relation,
			JSON.stringify(edge.properties),
		],
	);
}

/**
 * Batch insert edges.
 */
export async function insertEdges(edges: StoreEdge[]): Promise<void> {
	if (edges.length === 0) return;

	const pool = getPool();
	const client = await pool.connect();
	try {
		await client.query("BEGIN");
		for (const e of edges) {
			await client.query(
				`INSERT INTO entity_edge (id, tenant_id, project_id, from_entity_id, to_entity_id, relation, properties)
				 VALUES ($1, $2, $3, $4, $5, $6, $7)
				 ON CONFLICT (id) DO NOTHING`,
				[
					e.id,
					e.tenantId,
					e.projectId ?? null,
					e.fromEntityId,
					e.toEntityId,
					e.relation,
					JSON.stringify(e.properties),
				],
			);
		}
		await client.query("COMMIT");
	} catch (err) {
		await client.query("ROLLBACK");
		throw err;
	} finally {
		client.release();
	}
}

/**
 * Search entities by name or type (ILIKE matching).
 *
 * Tokenizes the query into individual words and searches each (OR'd).
 * This allows queries like "what technologies does MyApp use?" to match
 * entities named "MyApp" or "PostgreSQL".
 */
export async function searchEntities(
	query: string,
	tenantId: string,
	options?: { limit?: number; projectId?: string },
): Promise<GraphEntity[]> {
	const pool = getPool();
	const limit = options?.limit ?? 5;
	// Tokenize the query into individual words, filter short/common terms
	const tokens = query
		.toLowerCase()
		.replace(/[^a-z0-9_\-\s]/g, " ")
		.split(/\s+/)
		.filter((t) => t.length >= 2)
		.filter((t) => !STOP_WORDS.has(t));

	if (tokens.length === 0) return [];

	// Build a combined ILIKE pattern for each token
	const patterns = tokens.map((t) => `%${t}%`);

	let sql: string;
	const params: unknown[] = [tenantId];

	if (options?.projectId) {
		params.push(options.projectId);
		params.push(patterns);
		params.push(limit);
		sql = `SELECT id, tenant_id, project_id, type, name, properties, created_at
			 FROM entity
			 WHERE tenant_id = $1 AND project_id = $2
			   AND (name ILIKE ANY($3::text[]) OR type ILIKE ANY($3::text[]))
			 ORDER BY name
			 LIMIT $4`;
	} else {
		params.push(patterns);
		params.push(limit);
		sql = `SELECT id, tenant_id, project_id, type, name, properties, created_at
			 FROM entity
			 WHERE tenant_id = $1
			   AND (name ILIKE ANY($2::text[]) OR type ILIKE ANY($2::text[]))
			 ORDER BY name
			 LIMIT $3`;
	}

	const result = await pool.query(sql, params);

	return result.rows.map(rowToEntity);
}

/**
 * Get entities by type.
 */
export async function getEntitiesByType(
	type: string,
	tenantId: string,
	options?: { limit?: number },
): Promise<GraphEntity[]> {
	const pool = getPool();
	const limit = options?.limit ?? 20;

	const result = await pool.query(
		`SELECT id, tenant_id, project_id, type, name, properties, created_at
		 FROM entity
		 WHERE tenant_id = $1 AND type = $2
		 ORDER BY name
		 LIMIT $3`,
		[tenantId, type, limit],
	);

	return result.rows.map(rowToEntity);
}

/**
 * Get the subgraph around a set of entity IDs (1-2 hop traversal).
 *
 * Strategy:
 *   1. Fetch direct edges (1-hop) from/to the given entity IDs.
 *   2. Collect all neighboring entity IDs from direct edges.
 *   3. Fetch 2-hop edges from/to those neighbors (excluding already-seen edges).
 *   4. Return merged array of all reachable entities and edges.
 */
export async function getSubgraph(
	entityIds: string[],
	tenantId: string,
	options?: { maxHops?: number },
): Promise<{ entities: GraphEntity[]; edges: GraphRelation[] }> {
	if (entityIds.length === 0) return { entities: [], edges: [] };

	const maxHops = options?.maxHops ?? 2;
	const pool = getPool();

	// Step 1: Get direct edges (1-hop)
	const directEdges = await pool.query(
		`SELECT id, tenant_id, project_id, from_entity_id, to_entity_id, relation, properties, created_at
		 FROM entity_edge
		 WHERE tenant_id = $1
		   AND (from_entity_id = ANY($2::uuid[]) OR to_entity_id = ANY($2::uuid[]))`,
		[tenantId, entityIds],
	);

	const allEdges = [...directEdges.rows.map(rowToRelation)];

	if (maxHops >= 2) {
		// Collect neighbor entity IDs
		const neighborIds = new Set<string>();
		for (const row of directEdges.rows) {
			if (!entityIds.includes(row.from_entity_id)) neighborIds.add(row.from_entity_id);
			if (!entityIds.includes(row.to_entity_id)) neighborIds.add(row.to_entity_id);
		}

		if (neighborIds.size > 0) {
			const neighborArray = Array.from(neighborIds);

			// Step 2: Get 2-hop edges involving neighbors (excluding direct edges)
			const hop2Edges = await pool.query(
				`SELECT id, tenant_id, project_id, from_entity_id, to_entity_id, relation, properties, created_at
				 FROM entity_edge
				 WHERE tenant_id = $1
				   AND (from_entity_id = ANY($2::uuid[]) OR to_entity_id = ANY($2::uuid[]))
				   AND id <> ALL($3::uuid[])`,
				[
					tenantId,
					neighborArray,
					directEdges.rows.length > 0
						? directEdges.rows.map((r: { id: string }) => r.id)
						: ["00000000-0000-0000-0000-000000000000"],
				],
			);
			allEdges.push(...hop2Edges.rows.map(rowToRelation));
		}
	}

	// Collect all reachable entity IDs
	const reachableIds = new Set<string>(entityIds);
	for (const edge of allEdges) {
		reachableIds.add(edge.fromEntityId);
		reachableIds.add(edge.toEntityId);
	}

	if (reachableIds.size === 0) return { entities: [], edges: allEdges };

	// Fetch all reachable entities
	const entitiesResult = await pool.query(
		`SELECT id, tenant_id, project_id, type, name, properties, created_at
		 FROM entity
		 WHERE tenant_id = $1 AND id = ANY($2::uuid[])`,
		[tenantId, Array.from(reachableIds)],
	);

	return {
		entities: entitiesResult.rows.map(rowToEntity),
		edges: allEdges,
	};
}

/**
 * Generate a UUID v4.
 */
export function generateId(): string {
	return crypto.randomUUID();
}

// ── Row mappers ─────────────────────────────────────────────────────

function rowToEntity(row: Record<string, unknown>): GraphEntity {
	return {
		id: row.id as string,
		tenantId: row.tenant_id as string,
		projectId: (row.project_id as string) ?? undefined,
		type: row.type as string,
		name: row.name as string,
		properties: typeof row.properties === "string"
			? JSON.parse(row.properties as string)
			: (row.properties as Record<string, unknown>),
		createdAt: new Date(row.created_at as string),
	};
}

function rowToRelation(row: Record<string, unknown>): GraphRelation {
	return {
		id: row.id as string,
		tenantId: row.tenant_id as string,
		projectId: (row.project_id as string) ?? undefined,
		fromEntityId: row.from_entity_id as string,
		toEntityId: row.to_entity_id as string,
		relation: row.relation as string,
		properties: typeof row.properties === "string"
			? JSON.parse(row.properties as string)
			: (row.properties as Record<string, unknown>),
		createdAt: new Date(row.created_at as string),
	};
}