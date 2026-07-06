import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { PlanReviewsKB } from "../src/index.js";

const tempRoots: string[] = [];

afterEach(() => {
	for (const root of tempRoots.splice(0)) {
		fs.rmSync(root, { recursive: true, force: true });
	}
});

describe("PlanReviewsKB search", () => {
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
