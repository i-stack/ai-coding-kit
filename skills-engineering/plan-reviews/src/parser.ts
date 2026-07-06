/**
 * Structured parser for PLAN.md and review artifacts.
 *
 * Unlike rag-gateway's entity extractor (which uses an LLM to extract
 * entities from unstructured conversation text), this parser operates
 * on the well-known structure of PLAN.md files:
 *
 *   # Plan: <title>
 *   ## Goal
 *   ## Constraints & assumptions
 *   ## Approach
 *   ## Key decisions & tradeoffs
 *   ## Validation plan
 *   ## Risks / non-blocking open questions
 *   ## Out of scope
 *
 * And PLAN-REVIEW-LOG.md:
 *   - MAX_ROUNDS, Reviewers
 *   - Round N - <reviewer> → Flaws → VERDICT
 *   - Orchestrator response: Accepted / Rejected
 *   - Resolution
 *
 * No LLM calls needed — pure structural parsing.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import type {
	PlanSections,
	PlanArtifact,
	PlanResolution,
} from "./types.js";

// ─── PLAN.md parser ──────────────────────────────────────────────────

const SECTION_PATTERNS: Array<{
	key: keyof PlanSections;
	regex: RegExp;
}> = [
	{ key: "goal", regex: /^##\s+Goal\s*$/im },
	{ key: "constraints", regex: /^##\s+Constraints\s*[&]\s*assumptions\s*$/im },
	{ key: "approach", regex: /^##\s+Approach\s*$/im },
	{ key: "decisions", regex: /^##\s+Key\s+decisions\s*[&]\s*tradeoffs\s*$/im },
	{ key: "validation", regex: /^##\s+Validation\s+plan\s*$/im },
	{ key: "risks", regex: /^##\s+Risks\s*\/\s*non-blocking\s+open\s+questions\s*$/im },
	{ key: "outOfScope", regex: /^##\s+Out\s+of\s+scope\s*$/im },
];

/**
 * Extract the title from the first H1 heading in PLAN.md content.
 */
function extractTitle(content: string): string {
	const match = content.match(/^#\s+(.+?)(?:\s*\{[^}]*\})?\s*$/m);
	return match ? match[1].trim() : "Untitled Plan";
}

/**
 * Parse a PLAN.md file into structured sections.
 */
export function parsePlan(content: string): PlanSections {
	const title = extractTitle(content);

	// Normalize line endings
	const normalized = content.replace(/\r\n/g, "\n");

	// Find section boundaries
	const sections = new Map<keyof PlanSections, { start: number; end: number }>();

	for (const { key, regex } of SECTION_PATTERNS) {
		const match = normalized.match(regex);
		if (match && match.index !== undefined) {
			sections.set(key, { start: match.index + match[0].length, end: Infinity });
		}
	}

	// Sort sections by their position in the document
	const sorted = Array.from(sections.entries())
		.sort((a, b) => a[1].start - b[1].start);

	// Set end of each section to the start of the next one (or end of doc)
	for (let i = 0; i < sorted.length; i++) {
		if (i + 1 < sorted.length) {
			sections.get(sorted[i][0])!.end = sorted[i + 1][1].start;
		}
	}

	function getSection(key: keyof PlanSections): string {
		const range = sections.get(key);
		if (!range) return "";
		const text = normalized.slice(range.start, range.end).trim();
		// Remove trailing section header lines that leaked in
		return cleanupSection(text);
	}

	return {
		title,
		goal: getSection("goal"),
		constraints: getSection("constraints"),
		approach: getSection("approach"),
		decisions: getSection("decisions"),
		validation: getSection("validation"),
		risks: getSection("risks"),
		outOfScope: getSection("outOfScope"),
	};
}

/**
 * Clean up a section body: remove any trailing section headers from other sections.
 */
function cleanupSection(text: string): string {
	// Remove any remaining H2 headers that might have leaked in
	return text.replace(/^##\s+.+$/gm, "").trim();
}

// ─── PLAN-REVIEW-LOG.md parser ──────────────────────────────────────

/** Parsed review metadata from PLAN-REVIEW-LOG.md. */
export interface ReviewMetadata {
	resolution: PlanResolution;
	reviewers: string[];
}

/**
 * Parse PLAN-REVIEW-LOG.md to extract review metadata (resolution, reviewers).
 * Handles the multi-round format with retries.
 */
export function parseReviewLog(content: string): ReviewMetadata {
	const resolution = extractResolution(content);
	const reviewers = extractReviewers(content);
	return { resolution, reviewers };
}

function extractResolution(content: string): PlanResolution {
	// Find the LAST ## Resolution section (after retries)
	const resolutionMatches = [...content.matchAll(/^##\s+(?:Retry\s+\d+\s+)?Resolution\s*$/gim)];
	if (resolutionMatches.length === 0) return "pending";

	// Look at content after the last resolution header
	const lastMatch = resolutionMatches[resolutionMatches.length - 1];
	const afterResolution = content.slice((lastMatch.index ?? 0) + lastMatch[0].length);

	if (/approved/i.test(afterResolution.slice(0, 500))) return "approved";
	if (/deadlock/i.test(afterResolution.slice(0, 500))) return "deadlock";
	if (/failed/i.test(afterResolution.slice(0, 500))) return "failed";

	return "pending";
}

function extractReviewers(content: string): string[] {
	const reviewers: string[] = [];

	// Match the Reviewers: section near the top
	const reviewerSection = content.match(/^Reviewers:\s*\n((?:^-\s+.+\n?)+)/m);
	if (reviewerSection) {
		for (const line of reviewerSection[1].split("\n")) {
			const name = line.match(/^-\s+(\S+)/);
			if (name) reviewers.push(name[1].toLowerCase());
		}
	}

	return reviewers;
}

// ─── Directory scanner ───────────────────────────────────────────────

/**
 * Scan the .plan-reviews/ directory and return metadata for all plans.
 */
export function scanPlansDir(rootDir: string): PlanArtifact[] {
	const plansDir = path.join(rootDir, ".plan-reviews");
	if (!fs.existsSync(plansDir)) return [];

	const artifacts: PlanArtifact[] = [];
	const entries = fs.readdirSync(plansDir, { withFileTypes: true });

	for (const entry of entries) {
		if (!entry.isDirectory()) continue;
		// Skip the .knowledge-base.db file and any hidden dirs
		if (entry.name.startsWith(".")) continue;

		const planPath = path.join(plansDir, entry.name);
		const planFile = path.join(planPath, "PLAN.md");
		const reviewFile = path.join(planPath, "PLAN-REVIEW-LOG.md");

		if (!fs.existsSync(planFile)) continue;

		try {
			const planContent = fs.readFileSync(planFile, "utf-8");
			const sections = parsePlan(planContent);

			let reviewers: string[] = [];
			let resolution: PlanResolution = "pending";

			if (fs.existsSync(reviewFile)) {
				const reviewContent = fs.readFileSync(reviewFile, "utf-8");
				const meta = parseReviewLog(reviewContent);
				reviewers = meta.reviewers;
				resolution = meta.resolution;
			}

			artifacts.push({
				id: entry.name,
				path: planPath,
				sections,
				hasReview: fs.existsSync(reviewFile),
				resolution,
				reviewers,
				createdAt: extractDateFromId(entry.name),
			});
		} catch (err) {
			console.warn(`[plan-reviews] Failed to parse ${entry.name}: ${(err as Error).message}`);
		}
	}

	// Sort by date, newest first
	artifacts.sort((a, b) => b.createdAt.localeCompare(a.createdAt));

	return artifacts;
}

/**
 * Extract ISO date from plan directory name prefix (e.g. "2026-07-06-login-rate-limit").
 */
function extractDateFromId(id: string): string {
	const match = id.match(/^(\d{4}-\d{2}-\d{2})/);
	return match ? match[1] : "unknown";
}

/**
 * Check if a plan file has been modified since the given timestamp.
 */
export function getPlanMtime(planPath: string): number {
	const planFile = path.join(planPath, "PLAN.md");
	const reviewFile = path.join(planPath, "PLAN-REVIEW-LOG.md");

	let mtime = 0;
	if (fs.existsSync(planFile)) {
		mtime = Math.max(mtime, fs.statSync(planFile).mtimeMs);
	}
	if (fs.existsSync(reviewFile)) {
		mtime = Math.max(mtime, fs.statSync(reviewFile).mtimeMs);
	}
	return mtime;
}
