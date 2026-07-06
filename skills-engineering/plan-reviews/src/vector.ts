/**
 * In-memory vector index for semantic search.
 *
 * Unlike rag-gateway which relies on a separate Qdrant service,
 * this index keeps all vectors in memory and computes cosine
 * similarity in-process. The data volume (.plan-reviews has
 * typically dozens to low hundreds of chunks) makes this
 * entirely feasible without external infrastructure.
 *
 * Vectors are loaded from the JSON cache (EmbeddedChunk[]) on init.
 */

import type { EmbeddedChunk } from "./types.js";

export interface VectorSearchResult {
	chunkId: string;
	planId: string;
	section: string;
	text: string;
	score: number;
}

interface IndexEntry {
	chunkId: string;
	planId: string;
	section: string;
	text: string;
	vector: number[];
}

export class VectorIndex {
	private entries: IndexEntry[] = [];

	/**
	 * Load vectors from the store's chunks into memory.
	 */
	load(chunks: EmbeddedChunk[]): void {
		this.entries = [];
		for (const chunk of chunks) {
			if (!chunk.embedding || chunk.embedding.length === 0) continue;
			this.entries.push({
				chunkId: chunk.id,
				planId: chunk.planId,
				section: chunk.section,
				text: chunk.text,
				vector: chunk.embedding,
			});
		}
	}

	/**
	 * Add a single entry to the index (used during incremental sync).
	 */
	add(chunkId: string, planId: string, section: string, text: string, vector: number[]): void {
		this.entries = this.entries.filter((e) => e.chunkId !== chunkId);
		this.entries.push({ chunkId, planId, section, text, vector });
	}

	/**
	 * Remove all entries for a given planId.
	 */
	removePlan(planId: string): void {
		this.entries = this.entries.filter((e) => e.planId !== planId);
	}

	/**
	 * Search for the top-k most similar chunks to the given query vector.
	 */
	search(queryVector: number[], options?: {
		limit?: number;
		planId?: string;
		scoreThreshold?: number;
	}): VectorSearchResult[] {
		const limit = options?.limit ?? 5;
		const threshold = options?.scoreThreshold ?? 0.0;
		const planId = options?.planId;

		const scored: Array<{ entry: IndexEntry; score: number }> = [];

		for (const entry of this.entries) {
			if (planId && entry.planId !== planId) continue;
			const score = cosineSimilarity(queryVector, entry.vector);
			if (score >= threshold) {
				scored.push({ entry, score });
			}
		}

		scored.sort((a, b) => b.score - a.score);
		return scored.slice(0, limit).map((s) => ({
			chunkId: s.entry.chunkId,
			planId: s.entry.planId,
			section: s.entry.section,
			text: s.entry.text,
			score: s.score,
		}));
	}

	get size(): number {
		return this.entries.length;
	}

	clear(): void {
		this.entries = [];
	}
}

/**
 * Compute cosine similarity between two vectors.
 */
export function cosineSimilarity(a: number[], b: number[]): number {
	if (a.length !== b.length) {
		throw new Error(`Vector dimension mismatch: ${a.length} vs ${b.length}`);
	}

	let dotProduct = 0;
	let normA = 0;
	let normB = 0;

	for (let i = 0; i < a.length; i++) {
		dotProduct += a[i] * b[i];
		normA += a[i] * a[i];
		normB += b[i] * b[i];
	}

	const denominator = Math.sqrt(normA) * Math.sqrt(normB);
	if (denominator === 0) return 0;

	return dotProduct / denominator;
}
