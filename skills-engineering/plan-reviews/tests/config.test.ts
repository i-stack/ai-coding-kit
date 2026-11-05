import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { discoverProjectRoot } from "../src/config.js";

const tempRoots: string[] = [];

afterEach(() => {
	for (const root of tempRoots.splice(0)) {
		fs.rmSync(root, { recursive: true, force: true });
	}
});

function makeTempDir(prefix: string): string {
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
	tempRoots.push(dir);
	return dir;
}

describe("discoverProjectRoot", () => {
	it("walks up to the directory that contains .plan-reviews", () => {
		const root = makeTempDir("plan-reviews-root-");
		fs.mkdirSync(path.join(root, ".plan-reviews"));
		const nested = path.join(root, "packages", "app");
		fs.mkdirSync(nested, { recursive: true });
		expect(discoverProjectRoot(nested)).toBe(root);
	});

	it("does not treat an ancestor .codebuddy directory as the project root", () => {
		const home = makeTempDir("plan-reviews-home-");
		const codebuddy = path.join(home, ".codebuddy");
		const drifted = path.join(codebuddy, "cwd-drift");
		fs.mkdirSync(drifted, { recursive: true });
		expect(discoverProjectRoot(drifted)).toBe(drifted);
		expect(discoverProjectRoot(codebuddy)).toBe(codebuddy);
	});

	it("returns startDir when no ancestor has .plan-reviews", () => {
		const start = makeTempDir("plan-reviews-orphan-");
		expect(discoverProjectRoot(start)).toBe(start);
	});
});
