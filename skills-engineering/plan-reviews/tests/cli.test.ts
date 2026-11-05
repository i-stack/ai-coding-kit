import { execFile } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { CURRENT_SCHEMA_VERSION } from "../src/migrations.js";

const pkgRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const tsxBin = path.join(pkgRoot, "node_modules/tsx/dist/cli.mjs");
const cliSrc = path.join(pkgRoot, "src/cli.ts");
const tempRoots: string[] = [];

afterEach(() => {
	for (const root of tempRoots.splice(0)) {
		fs.rmSync(root, { recursive: true, force: true });
	}
});

function makeTempProject(): string {
	const root = fs.mkdtempSync(path.join(os.tmpdir(), "plan-reviews-cli-"));
	tempRoots.push(root);
	fs.mkdirSync(path.join(root, ".plan-reviews"), { recursive: true });
	return root;
}

function writeUnsupportedIndex(root: string): void {
	fs.writeFileSync(
		path.join(root, ".plan-reviews", ".kb-index.json"),
		JSON.stringify({
			schemaVersion: CURRENT_SCHEMA_VERSION + 1,
			plans: [],
			entities: [],
			relations: [],
			chunks: [],
			syncState: {},
			mergedKnowledge: [],
		}),
		"utf-8",
	);
}

function runCli(args: string[], cwd: string): Promise<{ status: number; stdout: string; stderr: string }> {
	const env = { ...process.env };
	delete env.EMBEDDING_API_KEY;
	return new Promise((resolve) => {
		execFile(
			process.execPath,
			[tsxBin, cliSrc, ...args],
			{ cwd, env, timeout: 15_000 },
			(err, stdout, stderr) => {
				const status = err && typeof err.code === "number" ? err.code : err ? 1 : 0;
				resolve({ status, stdout: stdout ?? "", stderr: stderr ?? "" });
			},
		);
	});
}

describe("plan-reviews CLI exit codes", () => {
	it("exits 0 and prints stderr when recall init fails", async () => {
		const root = makeTempProject();
		writeUnsupportedIndex(root);
		const result = await runCli(["recall", "login rate limit"], root);
		expect(result.status).toBe(0);
		expect(result.stderr).toContain("[plan-reviews] recall failed:");
		expect(result.stderr).toMatch(/Unsupported knowledge-base schema/);
	});

	it("exits non-zero when a non-recall command hits the same init failure", async () => {
		const root = makeTempProject();
		writeUnsupportedIndex(root);
		const result = await runCli(["search", "login rate limit"], root);
		expect(result.status).not.toBe(0);
		expect(result.stderr).toContain("Error:");
		expect(result.stderr).not.toContain("[plan-reviews] recall failed:");
	});

	it("exits 0 on a successful recall without a failure banner", async () => {
		const root = makeTempProject();
		const result = await runCli(["recall", "login rate limit"], root);
		expect(result.status).toBe(0);
		expect(result.stderr).not.toContain("[plan-reviews] recall failed:");
		expect(result.stdout).toMatch(/Recalling context for|no relevant prior knowledge found/);
	});
});
