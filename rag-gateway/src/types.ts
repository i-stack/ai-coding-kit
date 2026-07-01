/**
 * Persisted types for the gateway — graph entities, relationships, extraction.
 */

// ─── Graph Entity/Relation types (GraphRAG) ─────────────────────────

export interface GraphEntity {
	id: string;
	tenantId: string;
	projectId?: string;
	type: string;
	name: string;
	properties: Record<string, unknown>;
	createdAt: Date;
}

export interface GraphRelation {
	id: string;
	tenantId: string;
	projectId?: string;
	fromEntityId: string;
	toEntityId: string;
	relation: string;
	properties: Record<string, unknown>;
	createdAt: Date;
}

/**
 * Result of a graph search: matched entity plus its 1-2 hop neighborhood.
 */
export interface GraphSearchResult {
	entity: GraphEntity;
	relations: Array<{
		relation: GraphRelation;
		fromEntity: GraphEntity;
		toEntity: GraphEntity;
	}>;
}

/**
 * Structured output from the LLM extraction prompt.
 */
export interface ExtractionResult {
	entities: Array<{
		type: string;
		name: string;
		properties: Record<string, unknown>;
	}>;
	relationships: Array<{
		from: string;
		to: string;
		relation: string;
		properties: Record<string, unknown>;
	}>;
}