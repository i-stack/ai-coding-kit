/**
 * Entity Store — high-level orchestrator for GraphRAG entity extraction,
 * graph search, and context formatting.
 *
 * Connects the EntityExtractor (LLM), db/graph.ts (PostgreSQL), and
 * metrics pipeline into a single interface used by the chat route.
 */
import type { GatewayConfig } from "../config.js";
import { EntityExtractor } from "./extractor.js";
import * as graphDb from "../db/graph.js";
import { metricsCollector } from "../metrics.js";
import type { GraphSearchResult, GraphEntity, GraphRelation } from "../types.js";
import crypto from "node:crypto";

export class EntityStore {
	private extractor: EntityExtractor;
	private enabled: boolean;

	constructor(config: GatewayConfig) {
		this.extractor = new EntityExtractor(config);
		this.enabled = config.graphRagEnabled;
	}

	get isEnabled(): boolean {
		return this.enabled;
	}

	/**
	 * Extract entities and relationships from conversation text and store
	 * them in the PostgreSQL graph.
	 *
	 * This is intended to be called fire-and-forget — errors are logged
	 * but never propagated to the caller.
	 *
	 * Steps:
	 *   1. Call the LLM extractor to get structured entities + relationships.
	 *   2. Deduplicate entities by name within this batch.
	 *   3. Upsert entities (ON CONFLICT handles cross-batch dedup by name+tenant).
	 *   4. Insert edges between resolved entities.
	 */
	async extractAndStore(
		text: string,
		tenantId: string,
		projectId?: string,
	): Promise<void> {
		if (!this.enabled) return;

		try {
			const result = await this.extractor.extract(text);
			if (!result || result.entities.length === 0) return;

			// Deduplicate entities by name within this batch
			const nameToId = new Map<string, string>();

			const entities = result.entities
				.filter((e) => e.name && e.name.length > 0)
				.map((e) => {
					const normalizedName = e.name.trim();
					const existingId = nameToId.get(normalizedName);
					if (existingId) {
						// Duplicate within batch — skip
						return null;
					}
					const id = crypto.randomUUID();
					nameToId.set(normalizedName, id);
					return {
						id,
						tenantId,
						projectId,
						type: e.type,
						name: normalizedName,
						properties: e.properties,
					};
				})
				.filter((e): e is NonNullable<typeof e> => e !== null);

			let persistedIds: Map<string, string> | undefined;
			if (entities.length > 0) {
				persistedIds = await graphDb.upsertEntities(entities);
			}

			// Merge persisted IDs so ON CONFLICT-updated entities use their real DB id,
			// preventing FK violations when the in-memory id was discarded by ON CONFLICT.
			const resolvedNameToId = new Map(nameToId);
			if (persistedIds) {
				for (const [name, id] of persistedIds) {
					resolvedNameToId.set(name, id);
				}
			}

			// Insert edges only where both endpoints are resolved in this batch
			const edges = result.relationships
				.filter((r) => {
					const fromId = resolvedNameToId.get(r.from.trim());
					const toId = resolvedNameToId.get(r.to.trim());
					return fromId && toId && r.relation && r.relation.length > 0;
				})
				.map((r) => ({
					id: crypto.randomUUID(),
					tenantId,
					projectId,
					fromEntityId: resolvedNameToId.get(r.from.trim())!,
					toEntityId: resolvedNameToId.get(r.to.trim())!,
					relation: r.relation,
					properties: r.properties,
				}));

			if (edges.length > 0) {
				await graphDb.insertEdges(edges);
			}

			metricsCollector.recordEntityExtraction(entities.length);
		} catch (err) {
			console.error("Entity extraction/storage error:", (err as Error).message);
		}
	}

	/**
	 * Search the entity graph: find entities matching the query text,
	 * then retrieve their 1-2 hop neighborhood.
	 *
	 * Returns GraphSearchResult objects, each containing the matched entity
	 * and its connected relations (with both endpoint entities resolved).
	 */
	async searchGraph(
		query: string,
		tenantId: string,
		options?: { limit?: number; projectId?: string },
	): Promise<GraphSearchResult[]> {
		if (!this.enabled) return [];
		if (!query || query.length === 0) return [];

		try {
			// Step 1: Find matching entities by name/type ILIKE
			const entities = await graphDb.searchEntities(query, tenantId, {
				limit: options?.limit ?? 5,
				projectId: options?.projectId,
			});

			if (entities.length === 0) return [];

			// Step 2: Get the 1-2 hop subgraph around these entities
			const subgraph = await graphDb.getSubgraph(
				entities.map((e) => e.id),
				tenantId,
			);

			// Step 3: Build a lookup map for all entities in the subgraph
			const entityMap = new Map<string, GraphEntity>();
			for (const e of subgraph.entities) {
				entityMap.set(e.id, e);
			}
			// Ensure the matched entities are in the map (they should be)
			for (const e of entities) {
				if (!entityMap.has(e.id)) {
					entityMap.set(e.id, e);
				}
			}

			// Step 4: Build GraphSearchResult for each matched entity
			return entities.map((entity) => ({
				entity,
				relations: subgraph.edges
					.filter(
						(e) => e.fromEntityId === entity.id || e.toEntityId === entity.id,
					)
					.map((edge) => ({
						relation: edge,
						fromEntity:
							entityMap.get(edge.fromEntityId) ?? createPlaceholderEntity(edge.fromEntityId),
						toEntity:
							entityMap.get(edge.toEntityId) ?? createPlaceholderEntity(edge.toEntityId),
					})),
			}));
		} catch (err) {
			console.error("Graph search error:", (err as Error).message);
			return [];
		}
	}

	/**
	 * Format graph search results as structured context strings
	 * for injection into the system prompt.
	 *
	 * Output format:
	 *   [entity] "EntityName" (type)
	 *   [entity-relationship] "FromEntity" —[relation]→ "ToEntity"
	 */
	formatContext(results: GraphSearchResult[]): string[] {
		const lines: string[] = [];
		const seenRelations = new Set<string>();

		for (const r of results) {
			lines.push(`[entity] "${r.entity.name}" (${r.entity.type})`);

			for (const rel of r.relations) {
				const key = `${rel.relation.id}:${rel.fromEntity.name}:${rel.toEntity.name}`;
				if (seenRelations.has(key)) continue;
				seenRelations.add(key);

				lines.push(
					`[entity-relationship] "${rel.fromEntity.name}" —[${rel.relation.relation}]→ "${rel.toEntity.name}"`,
				);
			}
		}

		return lines;
	}
}

/**
 * Create a minimal placeholder entity for an ID that exists in an edge
 * but wasn't returned in the subgraph query. This should not normally occur
 * given FK constraints, but guards against edge cases during data migration.
 */
function createPlaceholderEntity(id: string): GraphEntity {
	return {
		id,
		tenantId: "unknown",
		type: "unknown",
		name: id,
		properties: {},
		createdAt: new Date(),
	};
}