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
import type {
	PlanArtifact,
	EmbeddedChunk,
	SyncStats,
	KbPlan,
	PlanEntity,
	PlanRelation,
} from "./types.js";
import { scanPlansDir, getPlanMtime } from "./parser.js";
import { extractFromArtifact, planToChunks } from "./extractor.js";
import type { PlanStore } from "./store.js";
import type { EmbeddingService } from "./embed.js";
import type { VectorIndex } from "./vector.js";
import { annotateChunk } from "./migrations.js";

export const INDEX_LOCK_WAIT_MS = 5_000;

interface PreparedArtifact {
	artifact: PlanArtifact;
	entities: PlanEntity[];
	relations: PlanRelation[];
	chunks: EmbeddedChunk[];
	snapshotMtime: number;
}

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

	async sync(options?: { full?: boolean }): Promise<SyncStats> {
		const full = options?.full === true;
		const artifacts = scanPlansDir(this.config.projectRoot);
		const snapshotById = new Map(
			artifacts.map((artifact) => [artifact.id, getPlanMtime(artifact.path)]),
		);

		const toIndex = await withIndexLock(this.config.indexPath, async () => {
			this.store.reload();
			return full
				? artifacts
				: artifacts.filter((artifact) => this._staleReason(artifact) !== null);
		});

		const prepared: PreparedArtifact[] = [];
		const errors: string[] = [];
		for (const artifact of toIndex) {
			try {
				prepared.push(await this._prepareArtifact(artifact, snapshotById.get(artifact.id) ?? 0));
			} catch (err) {
				const msg = `Failed to index ${artifact.id}: ${(err as Error).message}`;
				errors.push(msg);
				console.warn(`[plan-reviews] ${msg}`);
			}
		}

		return withIndexLock(this.config.indexPath, async () => {
			if (full) {
				this.store.truncateAll();
				this.vector.clear();
			} else {
				this.store.reload();
				this.vector.clear();
				this.vector.load(this.store.getAllChunks());
			}
			const stats = this._commitPrepared(artifacts, prepared, full);
			stats.errors.push(...errors);
			this.store.save();
			return stats;
		});
	}

	async reset(): Promise<SyncStats> {
		return this.sync({ full: true });
	}

	private _removePlan(planId: string): void {
		this.store.deletePlan(planId);
		this.vector.removePlan(planId);
	}

	private _staleReason(artifact: PlanArtifact): "added" | "modified" | null {
		const state = this.store.getSyncState(artifact.id);
		const planMtime = getPlanMtime(artifact.path);
		if (!state) return "added";
		if (planMtime > state.planMtime || planMtime > state.reviewMtime) return "modified";
		return null;
	}

	private _commitPrepared(
		artifacts: PlanArtifact[],
		prepared: PreparedArtifact[],
		full: boolean,
	): SyncStats {
		const stats: SyncStats = { added: 0, modified: 0, removed: 0, skipped: 0, errors: [] };
		const now = new Date().toISOString();
		const preparedById = new Map(prepared.map((item) => [item.artifact.id, item]));
		const fsPlanIds = new Set(artifacts.map((artifact) => artifact.id));

		if (!full) {
			for (const dbId of this.store.listPlans().map((plan) => plan.id)) {
				if (!fsPlanIds.has(dbId)) {
					this._removePlan(dbId);
					stats.removed++;
				}
			}
		}

		for (const artifact of artifacts) {
			const reason = full ? "added" : this._staleReason(artifact);
			if (reason === null) {
				stats.skipped++;
				continue;
			}
			const item = preparedById.get(artifact.id);
			if (!item) continue;
			if (getPlanMtime(artifact.path) !== item.snapshotMtime) {
				continue;
			}
			if (reason === "modified") {
				this._removePlan(artifact.id);
				stats.modified++;
			} else {
				stats.added++;
			}
			this._writePrepared(item, now);
		}

		if (stats.added > 0 || stats.modified > 0 || stats.removed > 0) {
			this.store.setMergedKnowledge([]);
		}
		return stats;
	}

	private _writePrepared(item: PreparedArtifact, now: string): void {
		const { artifact, entities, relations, chunks } = item;
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
		this.store.clearPlanEntities(artifact.id);
		this.store.upsertEntities(entities);
		this.store.upsertRelations(relations);
		if (chunks.length > 0) {
			this.store.clearPlanChunks(artifact.id);
			this.store.upsertChunks(chunks);
			for (const chunk of chunks) {
				if (chunk.embedding.length > 0) {
					this.vector.add(chunk.id, chunk.planId, chunk.section, chunk.text, chunk.embedding);
				}
			}
		}
		this.store.upsertSyncState(artifact.id, item.snapshotMtime, item.snapshotMtime);
	}

	private async _prepareArtifact(
		artifact: PlanArtifact,
		snapshotMtime: number,
	): Promise<PreparedArtifact> {
		const { entities, relations } = extractFromArtifact(artifact);
		const rawChunks = planToChunks(artifact);
		const chunks = await this._embedChunks(artifact, rawChunks);
		return { artifact, entities, relations, chunks, snapshotMtime };
	}

	private async _embedChunks(
		artifact: PlanArtifact,
		rawChunks: Array<{ section: string; text: string }>,
	): Promise<EmbeddedChunk[]> {
		const embeddedChunks: EmbeddedChunk[] = [];
		if (rawChunks.length === 0) return embeddedChunks;

		if (this.embed.isAvailable) {
			try {
				const vectors = await this.embed.embedBatch(rawChunks.map((chunk) => chunk.text));
				for (let i = 0; i < rawChunks.length; i++) {
					embeddedChunks.push(annotateChunk({
						id: crypto.randomUUID(),
						planId: artifact.id,
						section: rawChunks[i].section,
						text: rawChunks[i].text,
						embedding: vectors[i],
						sourcePath: artifact.path,
						trustLevel: "untrusted-history",
					}));
				}
				return embeddedChunks;
			} catch (err) {
				console.warn(
					`[plan-reviews] Embedding failed for ${artifact.id}: ${(err as Error).message}`,
				);
			}
		}

		for (const chunk of rawChunks) {
			embeddedChunks.push(annotateChunk({
				id: crypto.randomUUID(),
				planId: artifact.id,
				section: chunk.section,
				text: chunk.text,
				embedding: [],
				sourcePath: artifact.path,
				trustLevel: "untrusted-history",
			}));
		}
		return embeddedChunks;
	}
}

export async function withIndexLock<T>(indexPath: string, fn: () => Promise<T>): Promise<T> {
	const lockPath = `${indexPath}.lock`;
	await acquireLock(lockPath);
	try {
		return await fn();
	} finally {
		fs.rmSync(lockPath, { recursive: true, force: true });
	}
}

async function acquireLock(lockPath: string, timeoutMs = INDEX_LOCK_WAIT_MS): Promise<void> {
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
