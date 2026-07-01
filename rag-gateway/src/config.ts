import "dotenv/config";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

export interface GatewayConfig {
	port: number;
	host: string;
	databaseUrl?: string;
	qdrantUrl?: string;
	graphRagEnabled: boolean;
	/** API key for embedding service (OpenAI-compatible) */
	embeddingApiKey: string;
	/** Base URL for embedding service */
	embeddingBaseUrl: string;
	/** Model name for embeddings (default: "bge-m3") */
	embeddingModel: string;
	/** Vector dimension for Qdrant collection. Must match the embedding model used.
	 *  bge-m3 = 1024, text-embedding-ada-002 = 1536, text-embedding-3-large = 3072 */
	vectorSize: number;
	/** API key for entity extraction LLM (falls back to embeddingApiKey) */
	extractionApiKey: string;
	/** Base URL for entity extraction LLM */
	extractionBaseUrl: string;
	/** Model for entity extraction */
	extractionModel: string;
}

function optionalEnv(key: string, fallback: string): string {
	return process.env[key] ?? fallback;
}

// ── env/config.json loading ─────────────────────────────────────────────────

/**
 * Apply parsed config env values to an env-like object.
 *
 * Keys in the JSON ARE the env var names directly (identity, no transform).
 * Existing env values are never overwritten (dotenv takes precedence).
 * Non-string values (null, numbers) are skipped.
 *
 * Pure function — no I/O, no side-effects on the outer process.env.
 */
export function applyGatewayConfigEnv(
	values: Record<string, unknown>,
	env: Record<string, string | undefined>,
): void {
	for (const [key, value] of Object.entries(values)) {
		if (typeof value === "string" && env[key] === undefined) {
			env[key] = value;
		}
	}
}

function objectRecord(value: unknown): Record<string, unknown> {
	return value !== null && typeof value === "object" && !Array.isArray(value)
		? (value as Record<string, unknown>)
		: {};
}

export function gatewayEnvFromConfig(values: Record<string, unknown>): Record<string, unknown> {
	const platforms = objectRecord(values.platforms);
	const ragGateway = objectRecord(platforms["rag-gateway"]);
	const legacyGateway = objectRecord(platforms.gateway);
	return {
				...objectRecord(legacyGateway.env),
		...objectRecord(ragGateway.env),
	};
}

// Resolve env/config.json relative to this source file.
// dist/config.js → ../../env/config.json
const CONFIG_JSON_PATH = resolve(
	dirname(fileURLToPath(import.meta.url)),
	"../../env/config.json",
);

/**
 * Load env/config.json and apply platforms["rag-gateway"].env keys to process.env.
 * .env values take precedence (already loaded by `import "dotenv/config"` above).
 * Silently degrades to .env-only if the file is missing or malformed.
 */
function loadConfigJson(): void {
	if (!existsSync(CONFIG_JSON_PATH)) {
		console.warn(`[config] env/config.json not found at ${CONFIG_JSON_PATH}; using .env only`);
		return;
	}
	try {
		const raw = readFileSync(CONFIG_JSON_PATH, "utf-8");
		const values: Record<string, unknown> = JSON.parse(raw);
		const gatewayEnv = gatewayEnvFromConfig(values);
		applyGatewayConfigEnv(gatewayEnv, process.env);
		console.info(`[config] Loaded env/config.json platforms["rag-gateway"].env (${Object.keys(gatewayEnv).length} keys)`);
	} catch (err) {
		console.warn(`[config] Failed to parse env/config.json: ${(err as Error).message}; using .env only`);
	}
}

export function loadConfig(): GatewayConfig {
	// Phase 1: dotenv already ran at import-time (top of file).
	// Phase 2: apply env/config.json defaults for any keys still unset.
	loadConfigJson();

	const embeddingModel = optionalEnv("EMBEDDING_MODEL", "bge-m3");

	// Infer vector dimension from model name when VECTOR_SIZE is not explicitly set
	const rawVectorSize = process.env.VECTOR_SIZE ?? "";
	const DEFAULT_VECTOR_SIZES: Record<string, number> = {
		"bge-m3": 1024,
		"text-embedding-ada-002": 1536,
		"text-embedding-3-large": 3072,
	};
	const vectorSize = rawVectorSize
		? parseInt(rawVectorSize, 10)
		: (DEFAULT_VECTOR_SIZES[embeddingModel] ?? 1024);

	return {
		port: parseInt(optionalEnv("GATEWAY_PORT", "3000"), 10),
		host: optionalEnv("GATEWAY_HOST", "127.0.0.1"),
		databaseUrl: optionalEnv("DATABASE_URL", ""),
		qdrantUrl: optionalEnv("QDRANT_URL", ""),
		graphRagEnabled: process.env.GRAPH_RAG_ENABLED === "true",
		embeddingApiKey: optionalEnv("EMBEDDING_API_KEY", ""),
		embeddingBaseUrl: optionalEnv("EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
		embeddingModel,
		vectorSize,
		extractionApiKey: optionalEnv("EXTRACTION_API_KEY", ""),
		extractionBaseUrl: optionalEnv("EXTRACTION_BASE_URL", ""),
		extractionModel: optionalEnv("EXTRACTION_MODEL", "gpt-4o-mini"),
	};
}
