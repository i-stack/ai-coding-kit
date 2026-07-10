/**
 * In-memory store for plan-reviews knowledge base backed by a single JSON file.
 *
 * Replaces the SQLite/better-sqlite3 dependency. All data lives in memory;
 * the .kb-index.json file is a pure cache — always rebuildable from
 * the authoritative .plan-reviews/ Markdown files.
 *
 * Schema (KbIndexData):
 *   plans       — KbPlan[] metadata per plan directory
 *   entities    — PlanEntity[] extracted from plan sections
 *   relations   — PlanRelation[] between entities
 *   chunks      — EmbeddedChunk[] with optional embedding vectors
 *   syncState   — Record<planId, KbSyncState> mtime tracking
 */

import * as fs from "node:fs";
import * as path from "node:path";
import type {
	KbIndexData,
	KbPlan,
	KbSyncState,
	KbStats,
	PlanEntity,
	PlanRelation,
	EmbeddedChunk,
	PlanEntityType,
	SearchQuery,
} from "./types.js";

// ─── Empty state factory ──────────────────────────────────────────────

function emptyIndex(): KbIndexData {
	return {
		plans: [],
		entities: [],
		relations: [],
		chunks: [],
		syncState: {},
	};
}

// ─── Store ────────────────────────────────────────────────────────────

export class PlanStore {
	private indexPath: string;
	private data: KbIndexData;

	constructor(indexPath: string) {
		this.indexPath = indexPath;
		this.data = this._load();
	}

	// ── Persistence ─────────────────────────────────────────────────

	private _load(): KbIndexData {
		try {
			if (fs.existsSync(this.indexPath)) {
				const raw = fs.readFileSync(this.indexPath, "utf-8");
				const parsed = JSON.parse(raw);
				// Cautious hydration: ensure all keys exist
				return {
					plans: Array.isArray(parsed.plans) ? parsed.plans.map(normalizePlan) : [],
					entities: Array.isArray(parsed.entities) ? parsed.entities : [],
					relations: Array.isArray(parsed.relations) ? parsed.relations : [],
					chunks: Array.isArray(parsed.chunks) ? parsed.chunks : [],
					syncState: parsed.syncState && typeof parsed.syncState === "object" ? parsed.syncState : {},
				};
			}
		} catch (err) {
			console.warn(`[plan-reviews] Failed to load index, starting fresh: ${(err as Error).message}`);
		}
		return emptyIndex();
	}

	save(): void {
		const dir = path.dirname(this.indexPath);
		if (!fs.existsSync(dir)) {
			fs.mkdirSync(dir, { recursive: true });
		}
		// Atomic write: write to temp file, then rename
		const tmp = `${this.indexPath}.tmp`;
		fs.writeFileSync(tmp, JSON.stringify(this.data, null, 2), "utf-8");
		fs.renameSync(tmp, this.indexPath);
	}

	// ── Plans ────────────────────────────────────────────────────────

	upsertPlan(plan: KbPlan): void {
		const idx = this.data.plans.findIndex((p) => p.id === plan.id);
		if (idx >= 0) {
			this.data.plans[idx] = plan;
		} else {
			this.data.plans.push(plan);
		}
	}

	deletePlan(planId: string): void {
		this.data.plans = this.data.plans.filter((p) => p.id !== planId);
		this.data.entities = this.data.entities.filter((e) => e.planId !== planId);
		this.data.relations = this.data.relations.filter((r) => r.planId !== planId);
		this.data.chunks = this.data.chunks.filter((c) => c.planId !== planId);
		delete this.data.syncState[planId];
	}

	getPlan(planId: string): KbPlan | undefined {
		return this.data.plans.find((p) => p.id === planId);
	}

	listPlans(): KbPlan[] {
		return [...this.data.plans].sort(
			(a, b) => b.createdAt.localeCompare(a.createdAt),
		);
	}

	// ── Entities ─────────────────────────────────────────────────────

	clearPlanEntities(planId: string): void {
		this.data.entities = this.data.entities.filter((e) => e.planId !== planId);
		this.data.relations = this.data.relations.filter((r) => r.planId !== planId);
	}

	upsertEntities(entities: PlanEntity[]): void {
		for (const e of entities) {
			const idx = this.data.entities.findIndex(
				(ex) => ex.id === e.id,
			);
			if (idx >= 0) {
				this.data.entities[idx] = e;
			} else {
				this.data.entities.push(e);
			}
		}
	}

	upsertRelations(relations: PlanRelation[]): void {
		for (const r of relations) {
			const idx = this.data.relations.findIndex(
				(rx) => rx.id === r.id,
			);
			if (idx >= 0) {
				this.data.relations[idx] = r;
			} else {
				this.data.relations.push(r);
			}
		}
	}

	/**
	 * Search entities by name or description (substring match, case-insensitive).
	 * Returns PlanEntity objects directly (no row mapping needed).
	 */
	searchEntities(
		query: string,
		options?: { limit?: number; entityType?: string; planId?: string },
	): PlanEntity[] {
		const lower = query.toLowerCase();
		const limit = options?.limit ?? 10;

		let results = this.data.entities.filter(
			(e) =>
				e.name.toLowerCase().includes(lower) ||
				e.description.toLowerCase().includes(lower),
		);

		if (options?.entityType) {
			results = results.filter((e) => e.type === options.entityType);
		}
		if (options?.planId) {
			results = results.filter((e) => e.planId === options.planId);
		}

		// Sort by relevance: exact name match first, then substring
		results.sort((a, b) => {
			const aNameMatch = a.name.toLowerCase() === lower ? 0 : 1;
			const bNameMatch = b.name.toLowerCase() === lower ? 0 : 1;
			return aNameMatch - bNameMatch;
		});

		return results.slice(0, limit);
	}

	/**
	 * Get the 1-hop subgraph around given entity IDs.
	 */
	getSubgraph(entityIds: string[]): {
		entities: PlanEntity[];
		edges: PlanRelation[];
	} {
		if (entityIds.length === 0) return { entities: [], edges: [] };

		const edges = this.data.relations.filter(
			(r) => entityIds.includes(r.fromEntityId) || entityIds.includes(r.toEntityId),
		);

		const reachableIds = new Set(entityIds);
		for (const edge of edges) {
			reachableIds.add(edge.fromEntityId);
			reachableIds.add(edge.toEntityId);
		}

		const entities = this.data.entities.filter((e) => reachableIds.has(e.id));

		return { entities, edges };
	}

	// ── Chunks ──────────────────────────────────────────────────────

	clearPlanChunks(planId: string): void {
		this.data.chunks = this.data.chunks.filter((c) => c.planId !== planId);
	}

	upsertChunks(chunks: EmbeddedChunk[]): void {
		for (const c of chunks) {
			const idx = this.data.chunks.findIndex((cx) => cx.id === c.id);
			if (idx >= 0) {
				this.data.chunks[idx] = c;
			} else {
				this.data.chunks.push(c);
			}
		}
	}

	getAllChunks(): EmbeddedChunk[] {
		return this.data.chunks.filter((c) => c.embedding.length > 0);
	}

	searchChunksText(query: string, options?: { limit?: number; planId?: string }): EmbeddedChunk[] {
		const terms = query
			.toLowerCase()
			.split(/\s+/)
			.map((term) => term.trim())
			.filter(Boolean);
		if (terms.length === 0) return [];

		const limit = options?.limit ?? 5;
		const scored = this.data.chunks
			.filter((chunk) => !options?.planId || chunk.planId === options.planId)
			.map((chunk) => {
				const text = chunk.text.toLowerCase();
				const score = terms.reduce((sum, term) => sum + countOccurrences(text, term), 0);
				return { chunk, score };
			})
			.filter((item) => item.score > 0)
			.sort((a, b) => b.score - a.score || a.chunk.planId.localeCompare(b.chunk.planId));

		return scored.slice(0, limit).map((item) => item.chunk);
	}

	// ── Sync state ──────────────────────────────────────────────────

	upsertSyncState(planId: string, planMtime: number, reviewMtime: number): void {
		this.data.syncState[planId] = {
			planMtime,
			reviewMtime,
			lastSyncedAt: new Date().toISOString(),
		};
	}

	getSyncState(planId: string): KbSyncState | undefined {
		return this.data.syncState[planId];
	}

	getAllSyncStates(): Record<string, KbSyncState> {
		return { ...this.data.syncState };
	}

	// ── Lifecycle ───────────────────────────────────────────────────

	truncateAll(): void {
		this.data = emptyIndex();
	}

	get stats(): KbStats {
		return {
			plans: this.data.plans.length,
			entities: this.data.entities.length,
			relations: this.data.relations.length,
			chunks: this.data.chunks.length,
		};
	}
}

function normalizePlan(plan: KbPlan & { kind?: KbPlan["kind"] }): KbPlan {
	return {
		...plan,
		kind: plan.kind ?? "plan",
	};
}

function countOccurrences(text: string, term: string): number {
	let count = 0;
	let index = text.indexOf(term);
	while (index !== -1) {
		count++;
		index = text.indexOf(term, index + term.length);
	}
	return count;
}
