/**
 * Main entry point for the plan-reviews knowledge base.
 *
 * Provides a high-level API that mirrors rag-gateway's capabilities
 * but operates entirely in-process with zero external services:
 *
 *   - Single JSON file replaces SQLite/PostgreSQL
 *   - In-memory cosine similarity replaces Qdrant
 *   - Structural parsing replaces LLM entity extraction
 *   - Embedding API (optional) is the only retained external dependency
 *
 * Usage:
 *   ```typescript
 *   import { PlanReviewsKB } from "@i-stack/plan-reviews-kb";
 *
 *   const kb = await PlanReviewsKB.init();
 *   await kb.sync();
 *   const results = await kb.search({ query: "Redis rate limiting" });
 *   console.log(kb.formatResults(results));
 *   kb.close();
 *   ```
 */

import { loadConfig } from "./config.js";
import type { PlanReviewsConfig } from "./config.js";
import { PlanStore } from "./store.js";
import { EmbeddingService } from "./embed.js";
import { VectorIndex } from "./vector.js";
import { SearchEngine } from "./search.js";
import { SyncEngine } from "./sync.js";
import { MergeEngine } from "./merge.js";
import type { SearchQuery, SearchResponse, SyncStats, KbStats, MergedKnowledgePoint } from "./types.js";

export class PlanReviewsKB {
	private config: PlanReviewsConfig;
	store: PlanStore;
	embed: EmbeddingService;
	vector: VectorIndex;
	searchEngine: SearchEngine;
	syncEngine: SyncEngine;

	private constructor(config: PlanReviewsConfig) {
		this.config = config;
		this.store = new PlanStore(config.indexPath);
		this.embed = new EmbeddingService(config);
		this.vector = new VectorIndex();
		this.searchEngine = new SearchEngine(this.store, this.embed, this.vector);
		this.syncEngine = new SyncEngine(config, this.store, this.embed, this.vector);
	}

	/**
	 * Initialize the knowledge base from configuration.
	 * Loads existing chunks from JSON cache into the in-memory vector index.
	 * Call `kb.sync()` after initialization to index/update plans.
	 */
	static async init(
		overrides?: Partial<PlanReviewsConfig>,
	): Promise<PlanReviewsKB> {
		const config = loadConfig(overrides);
		const kb = new PlanReviewsKB(config);

		// Load existing vectors from cached chunks into memory
		const chunks = kb.store.getAllChunks();
		kb.vector.load(chunks);

		return kb;
	}

	/** Sync the knowledge base with .plan-reviews/ directory. */
	async sync(): Promise<SyncStats> {
		return this.syncEngine.sync();
	}

	/** Full reset and re-sync. */
	async reset(): Promise<SyncStats> {
		return this.syncEngine.reset();
	}

	/** Combined semantic + graph search. */
	async search(query: SearchQuery): Promise<SearchResponse> {
		return this.searchEngine.search(query);
	}

	/** Semantic-only search. */
	async semanticSearch(query: SearchQuery): Promise<SearchResponse["semantic"]> {
		return this.searchEngine.semanticSearch(query);
	}

	/** Graph-only search. */
	async graphSearch(query: SearchQuery): Promise<SearchResponse["graph"]> {
		return this.searchEngine.graphSearch(query);
	}

	/** Format search results as human-readable markdown. */
	formatResults(response: SearchResponse): string {
		return this.searchEngine.formatResults(response);
	}

	/**
	 * Retrieval-for-injection: run semantic + graph search on the user's
	 * question and return a compact, injection-ready markdown block.
	 * Returns an empty string when nothing relevant is found.
	 */
	async recall(query: string, limit = 5): Promise<string> {
		await this.sync();
		const res = await this.search({ query, limit });
		if (res.semantic.length === 0 && res.graph.length === 0) return "";
		return this.formatResults(res);
	}

	/** Run the memory-metabolism merge (de-dup / consolidate cross-plan knowledge). */
	async merge(options?: { threshold?: number }): Promise<MergedKnowledgePoint[]> {
		const engine = new MergeEngine(this.config, this.store, this.embed);
		return engine.merge(options);
	}

	/** Get knowledge base statistics. */
	get stats(): KbStats {
		return this.store.stats;
	}

	/** Persist current state (called automatically by sync, but can be manual). */
	save(): void {
		this.store.save();
	}

	/** Clean up (no-op in JSON mode, but kept for API compatibility). */
	close(): void {
		// State is already persisted to disk
	}
}

// Re-export types for consumers
export type { PlanReviewsConfig } from "./config.js";
export { CURRENT_SCHEMA_VERSION, detectPromptInjection, migrateIndex } from "./migrations.js";
export type {
	SearchQuery,
	SearchResponse,
	SyncStats,
	KbStats,
	PlanArtifact,
	PlanSections,
	PlanEntity,
	PlanRelation,
	PlanEntityType,
	PlanRelationType,
	GraphSearchResult,
	SemanticHit,
	PlanResolution,
	EmbeddedChunk,
	SyncEvent,
} from "./types.js";
