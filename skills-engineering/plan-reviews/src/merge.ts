/**
 * Memory metabolism layer for the plan-reviews knowledge base.
 *
 * Detects fragmented / duplicated knowledge across plans and consolidates
 * it into a single "project knowledge point". Without this, the same bug
 * discussed 3 times yields 3 independent summaries and bloats retrieval.
 *
 * Strategy:
 *   1. Load all embedded chunks (requires a configured Embedding API).
 *   2. Pairwise cosine similarity; union chunks >= MERGE_THRESHOLD into groups.
 *   3. For each group with >= 2 members, synthesize a MergedKnowledgePoint,
 *      de-duplicate the source texts, and persist to:
 *        - .plan-reviews/.kb-merged.json   (machine-readable)
 *        - .plan-reviews/MERGED-KNOWLEDGE.md (human-readable)
 *
 * Originals are NEVER deleted — merge only adds a consolidated view.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import crypto from "node:crypto";
import type { EmbeddedChunk, MergedKnowledgePoint } from "./types.js";
import type { PlanReviewsConfig } from "./config.js";
import type { PlanStore } from "./store.js";
import type { EmbeddingService } from "./embed.js";
import { cosineSimilarity } from "./vector.js";

/** Minimum cosine similarity for two chunks to be considered the "same" knowledge. */
export const DEFAULT_MERGE_THRESHOLD = 0.82;

/**
 * Build complete-link groups across different review artifacts.
 *
 * A candidate joins a group only when it is similar to every existing member.
 * This prevents single-link chains (A≈B, B≈C, A≉C) from collapsing unrelated
 * knowledge. A group also contains at most one chunk per artifact so merge does
 * not merely combine sections from the same review.
 */
export function clusterSimilarChunks(
	chunks: EmbeddedChunk[],
	threshold = DEFAULT_MERGE_THRESHOLD,
): number[][] {
	const groups: number[][] = [];

	for (let i = 0; i < chunks.length; i++) {
		const target = groups.find((group) => group.every((memberIndex) => {
			const member = chunks[memberIndex];
			return member.planId !== chunks[i].planId &&
				cosineSimilarity(member.embedding, chunks[i].embedding) >= threshold;
		}));

		if (target) {
			target.push(i);
		} else {
			groups.push([i]);
		}
	}

	return groups;
}

export class MergeEngine {
	private config: PlanReviewsConfig;
	private store: PlanStore;
	private embed: EmbeddingService;

	constructor(
		config: PlanReviewsConfig,
		store: PlanStore,
		embed: EmbeddingService,
	) {
		this.config = config;
		this.store = store;
		this.embed = embed;
	}

	/**
	 * Cluster cross-plan chunks by embedding similarity and consolidate duplicates.
	 * Returns the list of merged knowledge points (empty if embeddings unavailable
	 * or fewer than 2 chunks).
	 */
	async merge(options?: { threshold?: number }): Promise<MergedKnowledgePoint[]> {
		if (!this.embed.isAvailable) return [];

		const chunks = this.store.getAllChunks();
		if (chunks.length < 2) return [];

		const threshold = options?.threshold ?? DEFAULT_MERGE_THRESHOLD;

		const groups = clusterSimilarChunks(chunks, threshold);

		const points: MergedKnowledgePoint[] = [];
		const now = new Date().toISOString();

		for (const idxs of groups) {
			if (idxs.length < 2) continue; // skip singletons

			const members = idxs.map((i) => chunks[i]);

			// De-duplicate identical source texts.
			const seen = new Set<string>();
			const texts: string[] = [];
			for (const m of members) {
				const t = m.text.trim();
				if (t && !seen.has(t)) {
					seen.add(t);
					texts.push(t);
				}
			}

			const planIds = [...new Set(members.map((m) => m.planId))];
			const sourceSections = [...new Set(members.map((m) => m.section))];
			const titles = planIds.map((id) => this.store.getPlan(id)?.title ?? id);

			// Lowest pairwise similarity inside the group.
			let minSim = 1;
			for (let a = 0; a < members.length; a++) {
				for (let b = a + 1; b < members.length; b++) {
					const s = cosineSimilarity(members[a].embedding, members[b].embedding);
					if (s < minSim) minSim = s;
				}
			}

			points.push({
				id: crypto.randomUUID(),
				title: `合并知识点（${members.length} 条 · 来自 ${titles.join("、")}）`,
				memberCount: members.length,
				planIds,
				sourceSections,
				consolidatedText: texts.join("\n\n---\n\n"),
				minSimilarity: minSim,
				createdAt: now,
			});
		}

		this._persist(points, threshold);
		return points;
	}

	private _persist(points: MergedKnowledgePoint[], threshold: number): void {
		const dir = path.dirname(this.config.indexPath);
		const safeWrite = (file: string, content: string) => {
			try {
				fs.writeFileSync(path.join(dir, file), content, "utf-8");
			} catch (err) {
				console.warn(`[plan-reviews] Failed to write ${file}: ${(err as Error).message}`);
			}
		};

		safeWrite(
			".kb-merged.json",
			JSON.stringify({ generatedAt: new Date().toISOString(), threshold, points }, null, 2),
		);

		const md: string[] = [
			"# 合并后的项目知识点（去重 / 新陈代谢）\n",
			`> 由 \`plan-reviews merge\` 自动生成。相似度阈值：${threshold}。源片段已保留，本文件仅为去重后的 consolidated 视图。\n`,
		];
		if (points.length === 0) {
			md.push("\n暂无需要合并的重复知识点。\n");
		}
		for (const p of points) {
			md.push(`\n## ${p.title}\n`);
			md.push(`- 合并条目数：${p.memberCount}`);
			md.push(`- 来源 plan：${p.planIds.join(", ")}`);
			md.push(`- 来源 section：${p.sourceSections.join(", ")}`);
			md.push(`- 最低相似度：${p.minSimilarity.toFixed(2)}\n`);
			md.push(p.consolidatedText + "\n");
		}
		safeWrite("MERGED-KNOWLEDGE.md", md.join("\n"));
	}
}
