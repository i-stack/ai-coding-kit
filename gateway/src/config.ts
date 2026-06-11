import "dotenv/config";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

export interface GatewayConfig {
	port: number;
	host: string;
	openaiApiKey: string;
	openaiBaseUrl: string;
	openaiDefaultModel: string;
	anthropicApiKey: string;
	anthropicBaseUrl: string;
	databaseUrl?: string;
	qdrantUrl?: string;
	graphRagEnabled: boolean;
}

function requireEnv(key: string): string {
	const val = process.env[key];
	if (!val) {
		throw new Error(`Missing required environment variable: ${key}`);
	}
	return val;
}

function optionalEnv(key: string, fallback: string): string {
	return process.env[key] ?? fallback;
}

// ── Shared settings.json mapping ────────────────────────────────────────────

export interface SharedMapping {
	sharedKey: string;
	envKeys: string[];
	transform?: (value: string) => string;
}

/**
 * Mapping table: env/claude/settings.shared.json keys → process.env keys.
 *
 * ANTHROPIC_AUTH_TOKEN  →  OPENAI_API_KEY & ANTHROPIC_API_KEY
 * ANTHROPIC_BASE_URL     →  ANTHROPIC_BASE_URL  (identity)
 * ANTHROPIC_BASE_URL     →  OPENAI_BASE_URL     (append "/v1")
 * ANTHROPIC_MODEL        →  OPENAI_DEFAULT_MODEL
 *
 * Edit mappings here; values are set at process.env read-time.
 */
export const SHARED_MAPPINGS: SharedMapping[] = [
	{ sharedKey: "ANTHROPIC_AUTH_TOKEN", envKeys: ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"] },
	{ sharedKey: "ANTHROPIC_BASE_URL", envKeys: ["ANTHROPIC_BASE_URL"] },
	{ sharedKey: "ANTHROPIC_BASE_URL", envKeys: ["OPENAI_BASE_URL"], transform: (v) => `${v}/v1` },
	{ sharedKey: "ANTHROPIC_MODEL", envKeys: ["OPENAI_DEFAULT_MODEL"] },
];

/**
 * Apply shared-settings values to an env-like object, respecting priority:
 * existing env values are never overwritten.
 *
 * Pure function — no I/O, no side-effects on the outer process.env.
 *
 * @param shared  Parsed shared settings object (e.g. JSON.parse of settings.shared.json)
 * @param env     The env object to write into (pass process.env at call site)
 * @param mappings The mapping table
 */
export function applySharedMappings(
	shared: Record<string, string>,
	env: Record<string, string | undefined>,
	mappings: SharedMapping[],
): void {
	for (const { sharedKey, envKeys, transform } of mappings) {
		const value = shared[sharedKey];
		if (value === undefined || value === null) continue;
		for (const envKey of envKeys) {
			if (env[envKey] === undefined) {
				env[envKey] = transform ? transform(value) : value;
			}
		}
	}
}

// Resolve the canonical settings path relative to this source file.
// dist/config.js → ../../env/claude/settings.shared.json
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SHARED_SETTINGS_PATH = resolve(__dirname, "../../env/claude/settings.shared.json");

/**
 * Load env/claude/settings.shared.json and apply its mapped keys to process.env.
 * .env values take precedence (already loaded by `import "dotenv/config"` above).
 * Silently degrades to .env-only if the file is missing or malformed.
 */
function loadSharedJsonIntoEnv(): void {
	if (!existsSync(SHARED_SETTINGS_PATH)) {
		console.warn(`[config] Shared settings not found at ${SHARED_SETTINGS_PATH}; using .env only`);
		return;
	}
	try {
		const raw = readFileSync(SHARED_SETTINGS_PATH, "utf-8");
		const shared: Record<string, string> = JSON.parse(raw);
		applySharedMappings(shared, process.env, SHARED_MAPPINGS);
		console.info(`[config] Loaded shared settings from ${SHARED_SETTINGS_PATH}`);
	} catch (err) {
		console.warn(`[config] Failed to parse shared settings: ${(err as Error).message}; using .env only`);
	}
}

export function loadConfig(): GatewayConfig {
	// Phase 1: dotenv already ran at import-time (top of file).
	// Phase 2: apply shared.json defaults for any keys still unset.
	loadSharedJsonIntoEnv();

	return {
		port: parseInt(optionalEnv("GATEWAY_PORT", "3000"), 10),
		host: optionalEnv("GATEWAY_HOST", "0.0.0.0"),
		openaiApiKey: requireEnv("OPENAI_API_KEY"),
		openaiBaseUrl: optionalEnv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
		openaiDefaultModel: optionalEnv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
		anthropicApiKey: optionalEnv("ANTHROPIC_API_KEY", ""),
		anthropicBaseUrl: optionalEnv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
		databaseUrl: optionalEnv("DATABASE_URL", ""),
		qdrantUrl: optionalEnv("QDRANT_URL", ""),
		graphRagEnabled: process.env.GRAPH_RAG_ENABLED === "true",
	};
}