/**
 * Incremental sync engine for .plan-reviews/ → in-memory knowledge base.
 *
 * Scans the .plan-reviews/ directory, diffs against stored sync state,
 * and updates only changed plans. Results persist to .kb-index.json.
 */

import * as path from "node:path";
import crypto from "node:crypto";
import type { PlanReviewsConfig } from "./config.js";
import type { PlanArtifact, EmbeddedChunk, SyncStats, KbPlan } from "./types.js";
import { scanPlansDir, getPlanMtime } from "./parser.js";
import { extractFromArtifact, planToChunks } from "./extractor.js";
import type { PlanStore } from "./store.js";
import type { EmbeddingService } from "./embed.js";
import type { VectorIndex } from "./vector.js";

export class SyncEngine {
	private config: PlanReviewsConfig;
	private store: PlanStore;
	private embed: EmbeddingService;
	private vector: VectorIndex;

	constructor(
		config: PlanReviewsConfig,
		store: PlanStore,
		embed: EmbeddingService,
		vector: VectorIndex,
	) {
		this.config = config;
		this.store = store;
		this.embed = embed;
		this.vector = vector;
	}

	async sync(): Promise<SyncStats> {
		const stats: SyncStats = { added: 0, modified: 0, removed: 0, skipped: 0, errors: [] };
		const now = new Date().toISOString();

		const artifacts = scanPlansDir(this.config.projectRoot);
		const fsPlanIds = new Set(artifacts.map((a) => a.id));

		const plansToIndex: PlanArtifact[] = [];

		for (const artifact of artifacts) {
			const state = this.store.getSyncState(artifact.id);
			const planMtime = getPlanMtime(artifact.path);

			if (!state) {
				plansToIndex.push(artifact);
				stats.added++;
			} else if (planMtime > state.planMtime || planMtime > state.reviewMtime) {
				this._removePlan(artifact.id);
				plansToIndex.push(artifact);
				stats.modified++;
			} else {
				stats.skipped++;
			}
		}

		// Detect removed plans
		const dbPlanIds = new Set(this.store.listPlans().map((p) => p.id));
		for (const dbId of dbPlanIds) {
			if (!fsPlanIds.has(dbId)) {
				this._removePlan(dbId);
				stats.removed++;
			}
		}

		for (const artifact of plansToIndex) {
			try {
				await this._indexArtifact(artifact, now);
			} catch (err) {
				const msg = `Failed to index ${artifact.id}: ${(err as Error).message}`;
				stats.errors.push(msg);
				console.warn(`[plan-reviews] ${msg}`);
			}
		}

		// Persist to JSON file
		this.store.save();

		return stats;
	}

	async reset(): Promise<SyncStats> {
		this.store.truncateAll();
		this.vector.clear();
		return this.sync();
	}

	private _removePlan(planId: string): void {
		this.store.deletePlan(planId);
		this.vector.removePlan(planId);
	}

	private async _indexArtifact(artifact: PlanArtifact, now: string): Promise<void> {
		// 1. Upsert plan metadata
		const kbPlan: KbPlan = {
			id: artifact.id,
			title: artifact.sections.title,
			path: artifact.path,
			goal: artifact.sections.goal,
			resolution: artifact.resolution,
			hasReview: artifact.hasReview,
			reviewers: artifact.reviewers,
			createdAt: artifact.createdAt,
			syncedAt: now,
			kind: artifact.kind,
		};
		this.store.upsertPlan(kbPlan);

		// 2. Clear and re-extract entities/relations
		this.store.clearPlanEntities(artifact.id);
		const { entities, relations } = extractFromArtifact(artifact);
		this.store.upsertEntities(entities);
		this.store.upsertRelations(relations);

		// 3. Generate chunks and (optionally) embeddings
		const rawChunks = planToChunks(artifact);
		const embeddedChunks: EmbeddedChunk[] = [];

		if (this.embed.isAvailable && rawChunks.length > 0) {
			const texts = rawChunks.map((c) => c.text);
			try {
				const vectors = await this.embed.embedBatch(texts);
				for (let i = 0; i < rawChunks.length; i++) {
					const chunkId = crypto.randomUUID();
					const chunk: EmbeddedChunk = {
						id: chunkId,
						planId: artifact.id,
						section: rawChunks[i].section,
						text: rawChunks[i].text,
						embedding: vectors[i],
					};
					embeddedChunks.push(chunk);
					this.vector.add(chunkId, artifact.id, rawChunks[i].section, rawChunks[i].text, vectors[i]);
				}
			} catch (err) {
				console.warn(
					`[plan-reviews] Embedding failed for ${artifact.id}: ${(err as Error).message}`,
				);
				for (const c of rawChunks) {
					embeddedChunks.push({
						id: crypto.randomUUID(),
						planId: artifact.id,
						section: c.section,
						text: c.text,
						embedding: [],
					});
				}
			}
		} else if (rawChunks.length > 0) {
			for (const c of rawChunks) {
				embeddedChunks.push({
					id: crypto.randomUUID(),
					planId: artifact.id,
					section: c.section,
					text: c.text,
					embedding: [],
				});
			}
		}

		if (embeddedChunks.length > 0) {
			this.store.clearPlanChunks(artifact.id);
			this.store.upsertChunks(embeddedChunks);
		}

		// 4. Track sync state
		const mtime = getPlanMtime(artifact.path);
		this.store.upsertSyncState(artifact.id, mtime, mtime);
	}
}
