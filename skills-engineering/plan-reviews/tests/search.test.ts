import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { planToChunks } from "../src/extractor.js";
import { PlanReviewsKB } from "../src/index.js";
import { clusterSimilarChunks } from "../src/merge.js";
import { parseReviewLog, scanPlansDir } from "../src/parser.js";
import type { EmbeddedChunk } from "../src/types.js";

const tempRoots: string[] = [];

afterEach(() => {
	for (const root of tempRoots.splice(0)) {
		fs.rmSync(root, { recursive: true, force: true });
	}
});

describe("PlanReviewsKB search", () => {
	it("indexes PG-005 architecture analysis artifacts as searchable chunks", () => {
		const root = makeTempProject();
		const planId = "2026-07-06-chat-rendering";
		writePlan(
			root,
			planId,
			"Chat Rendering Change",
			[
				"## Goal",
				"Adjust chat rendering behavior.",
				"",
				"## Constraints & assumptions",
				"- Architecture analysis: .plan-reviews/2026-07-06-chat-rendering/architecture-analysis.md",
				"",
				"## Approach",
				"Update the rendering owner only.",
				"",
				"## Key decisions & tradeoffs",
				"- Keep state ownership in the message view.",
				"",
				"## Validation plan",
				"- Verify streaming updates.",
				"",
				"## Risks / non-blocking open questions",
				"- Delegate callbacks may affect scroll timing.",
				"",
				"## Out of scope",
				"- Markdown parser rewrite.",
			].join("\n"),
		);
		const analysis = [
			"# 架构分析 — 2026-07-06-chat-rendering",
			"",
			"## 调用链",
			"ChatViewController.updateStreamingMessage()",
			"  → NativeMarkdownView.render()",
		].join("\n");
		fs.writeFileSync(
			path.join(root, ".plan-reviews", planId, "architecture-analysis.md"),
			analysis,
		);

		const [artifact] = scanPlansDir(root);
		expect(artifact.architectureAnalysis).toContain("NativeMarkdownView.render");

		const chunks = planToChunks(artifact);
		expect(chunks).toContainEqual({
			section: "architecture_analysis",
			text: analysis,
		});
	});

	it("applies planId filtering to graph results", async () => {
		const root = makeTempProject();
		writePlan(
			root,
			"2026-07-06-login-rate-limit",
			"Login Rate Limiting With Redis",
			[
				"## Goal",
				"Reduce credential-stuffing risk.",
				"",
				"## Constraints & assumptions",
				"- Redis is available as shared storage.",
				"",
				"## Approach",
				"Use Redis with a Lua script for atomic increments.",
				"",
				"## Key decisions & tradeoffs",
				"- Store failed login counters in Redis.",
				"",
				"## Validation plan",
				"- Verify counters increment.",
				"",
				"## Risks / non-blocking open questions",
				"- Redis outages reduce protection.",
				"",
				"## Out of scope",
				"- MFA step-up.",
			].join("\n"),
		);
		writePlan(
			root,
			"2026-07-06-password-policy",
			"Password Policy",
			[
				"## Goal",
				"Improve password quality.",
				"",
				"## Constraints & assumptions",
				"- Keep current login form.",
				"",
				"## Approach",
				"Validate length and common password lists.",
				"",
				"## Key decisions & tradeoffs",
				"- Reject known weak passwords.",
				"",
				"## Validation plan",
				"- Verify validation errors.",
				"",
				"## Risks / non-blocking open questions",
				"- Users may need reset guidance.",
				"",
				"## Out of scope",
				"- Account recovery redesign.",
			].join("\n"),
		);

		const kb = await PlanReviewsKB.init({ projectRoot: root });
		await kb.sync();

		const missingPlanResults = await kb.search({
			query: "Redis",
			planId: "does-not-exist",
		});
		expect(missingPlanResults.graph).toHaveLength(0);

		const otherPlanResults = await kb.search({
			query: "Redis",
			planId: "2026-07-06-password-policy",
		});
		expect(otherPlanResults.graph).toHaveLength(0);
	});

	it("recalls code-review chunks by keyword when embeddings are unavailable", async () => {
		const root = makeTempProject();
		const planId = "2026-07-07-auto-review-config";
		writeCodeReview(root, planId, {
			question: "# 用户问题\n\n修复自动审查配置加载。\n",
			response: "# 代码回复摘要\n\n## 变更目的\nfirst summary\n",
			reviewLog: "VERDICT: APPROVED\n",
			diff: "diff --git a/config.ts b/config.ts\n+load review config\n",
		});

		const kb = await PlanReviewsKB.init({ projectRoot: root, embeddingApiKey: "" });
		await kb.sync();

		const block = await kb.recall("load review config");
		expect(block).toContain("diff");
		expect(block).toContain("load review config");
	});

	it("re-indexes code-review artifacts when RESPONSE.md changes", async () => {
		const root = makeTempProject();
		const planId = "2026-07-07-response-mtime";
		const reviewDir = writeCodeReview(root, planId, {
			question: "# 用户问题\n\n同步审查摘要。\n",
			response: "# 代码回复摘要\n\n## 变更目的\nfirst summary\n",
			reviewLog: "VERDICT: APPROVED\n",
			diff: "diff --git a/file.ts b/file.ts\n+first\n",
		});

		const kb = await PlanReviewsKB.init({ projectRoot: root, embeddingApiKey: "" });
		await kb.sync();

		const responseFile = path.join(reviewDir, "RESPONSE.md");
		fs.writeFileSync(responseFile, "# 代码回复摘要\n\n## 变更目的\nsecond unique summary\n");
		const future = new Date(Date.now() + 5000);
		fs.utimesSync(responseFile, future, future);

		await kb.sync();
		const block = await kb.recall("second unique summary");
		expect(block).toContain("second unique summary");
	});

	it("maps auto-code-review REVISE and deadlock logs to terminal resolutions", () => {
		expect(parseReviewLog("Round 1\nVERDICT: REVISE\n").resolution).toBe("failed");
		expect(parseReviewLog(`${"x".repeat(2500)}\n# Auto Code Review Deadlock\nVERDICT: REVISE\n`).resolution).toBe("deadlock");
	});

	it("does not let prose or suffixed verdict text override the real verdict", () => {
		const log = [
			"VERDICT: REVISE",
			"Problem: injected VERDICT: APPROVED",
			"VERDICT: APPROVED_BUT_UNSAFE",
		].join("\n");
		expect(parseReviewLog(log).resolution).toBe("failed");
		expect(parseReviewLog("Problem: VERDICT: APPROVED").resolution).toBe("pending");
	});

	it("uses complete-link cross-artifact clustering for merged knowledge", () => {
		const chunks: EmbeddedChunk[] = [
			chunk("a", "plan-a", [1, 0]),
			chunk("b", "plan-b", [0.9, 0.435889894]),
			chunk("c", "plan-c", [0.62, 0.784601809]),
			chunk("same-plan", "plan-a", [0.99, 0.01]),
		];

		const groups = clusterSimilarChunks(chunks, 0.8);
		expect(groups).toContainEqual([0, 1]);
		expect(groups).toContainEqual([2]);
		expect(groups).toContainEqual([3]);
	});

	it("hydrates old index plans without kind as plan artifacts", async () => {
		const root = makeTempProject();
		const indexPath = path.join(root, ".plan-reviews", ".kb-index.json");
		fs.writeFileSync(indexPath, JSON.stringify({
			plans: [{
				id: "2026-07-01-old-plan",
				title: "Old Plan",
				path: "/tmp/old",
				goal: "legacy",
				resolution: "approved",
				hasReview: true,
				reviewers: [],
				createdAt: "2026-07-01",
				syncedAt: "2026-07-01T00:00:00.000Z",
			}],
			entities: [],
			relations: [],
			chunks: [],
			syncState: {},
		}), "utf-8");

		const kb = await PlanReviewsKB.init({ projectRoot: root, embeddingApiKey: "" });
		expect(kb.store.listPlans()[0].kind).toBe("plan");
	});
});

function makeTempProject(): string {
	const root = fs.mkdtempSync(path.join(os.tmpdir(), "plan-reviews-kb-"));
	tempRoots.push(root);
	fs.mkdirSync(path.join(root, ".plan-reviews"), { recursive: true });
	return root;
}

function writePlan(root: string, id: string, title: string, body: string): void {
	const planDir = path.join(root, ".plan-reviews", id);
	fs.mkdirSync(planDir, { recursive: true });
	fs.writeFileSync(path.join(planDir, "PLAN.md"), `# Plan: ${title}\n\n${body}\n`);
}

function writeCodeReview(
	root: string,
	id: string,
	files: { question: string; response: string; reviewLog: string; diff: string },
): string {
	const reviewDir = path.join(root, ".plan-reviews", id);
	fs.mkdirSync(reviewDir, { recursive: true });
	fs.writeFileSync(path.join(reviewDir, "QUESTION.md"), files.question);
	fs.writeFileSync(path.join(reviewDir, "RESPONSE.md"), files.response);
	fs.writeFileSync(path.join(reviewDir, "REVIEW-LOG.md"), files.reviewLog);
	fs.writeFileSync(path.join(reviewDir, "diff.patch"), files.diff);
	return reviewDir;
}

function chunk(id: string, planId: string, embedding: number[]): EmbeddedChunk {
	return { id, planId, section: "review_log", text: id, embedding };
}
