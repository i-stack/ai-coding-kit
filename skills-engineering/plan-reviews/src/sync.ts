/**
 * Incremental sync engine for .plan-reviews/ → in-memory knowledge base.
 *
 * Scans the .plan-reviews/ directory, diffs against stored sync state,
 * and updates only changed plans. Results persist to .kb-index.json.
 */

import * as path from "node:path";
import * as fs from "node:fs";
import crypto from "node:crypto";
import type { PlanReviewsConfig } from "./config.js";
import type { PlanArtifact, EmbeddedChunk, SyncStats, KbPlan } from "./types.js";
import { scanPlansDir, getPlanMtime } from "./parser.js";
import { extractFromArtifact, planToChunks } from "./extractor.js";
import type { PlanStore } from "./store.js";
import type { EmbeddingService } from "./embed.js";
import type { VectorIndex } from "./vector.js";
import { annotateChunk } from "./migrations.js";

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
		const lockPath = `${this.config.indexPath}.lock`;
		await acquireLock(lockPath);
		try {
			this.store.reload();
			this.vector.clear();
			this.vector.load(this.store.getAllChunks());
			return await this._syncLocked();
		} finally {
			fs.rmSync(lockPath, { recursive: true, force: true });
		}
	}

	private async _syncLocked(): Promise<SyncStats> {
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

		if (stats.added > 0 || stats.modified > 0 || stats.removed > 0) {
			this.store.setMergedKnowledge([]);
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
					const chunk: EmbeddedChunk = annotateChunk({
						id: chunkId,
						planId: artifact.id,
						section: rawChunks[i].section,
						text: rawChunks[i].text,
						embedding: vectors[i],
						sourcePath: artifact.path,
						trustLevel: "untrusted-history",
					});
					embeddedChunks.push(chunk);
					this.vector.add(chunkId, artifact.id, rawChunks[i].section, rawChunks[i].text, vectors[i]);
				}
			} catch (err) {
				console.warn(
					`[plan-reviews] Embedding failed for ${artifact.id}: ${(err as Error).message}`,
				);
				for (const c of rawChunks) {
					embeddedChunks.push(annotateChunk({
						id: crypto.randomUUID(),
						planId: artifact.id,
						section: c.section,
						text: c.text,
						embedding: [],
						sourcePath: artifact.path,
						trustLevel: "untrusted-history",
					}));
				}
			}
		} else if (rawChunks.length > 0) {
			for (const c of rawChunks) {
				embeddedChunks.push(annotateChunk({
					id: crypto.randomUUID(),
					planId: artifact.id,
					section: c.section,
					text: c.text,
					embedding: [],
					sourcePath: artifact.path,
					trustLevel: "untrusted-history",
				}));
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

async function acquireLock(lockPath: string, timeoutMs = 5000): Promise<void> {
	const deadline = Date.now() + timeoutMs;
	while (true) {
		try {
			fs.mkdirSync(lockPath);
			fs.writeFileSync(path.join(lockPath, "owner.json"), JSON.stringify({ pid: process.pid, acquiredAt: new Date().toISOString() }));
			return;
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
			const owner = readLockOwner(lockPath);
			if (owner !== undefined && !isProcessAlive(owner)) {
				fs.rmSync(lockPath, { recursive: true, force: true });
				continue;
			}
			if (Date.now() >= deadline) throw new Error(`Timed out acquiring knowledge-base lock: ${lockPath}`);
			await new Promise((resolve) => setTimeout(resolve, 50));
		}
	}
}

function readLockOwner(lockPath: string): number | undefined {
	try {
		const value = JSON.parse(fs.readFileSync(path.join(lockPath, "owner.json"), "utf-8"));
		return Number.isInteger(value.pid) ? value.pid : undefined;
	} catch {
		return undefined;
	}
}

function isProcessAlive(pid: number): boolean {
	try {
		process.kill(pid, 0);
		return true;
	} catch (error) {
		return (error as NodeJS.ErrnoException).code === "EPERM";
	}
}
