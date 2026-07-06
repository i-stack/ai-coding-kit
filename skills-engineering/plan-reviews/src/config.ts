import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Configuration for the plan-reviews knowledge base.
 *
 * Sources (in priority order):
 *   1. Programmatic overrides
 *   2. Environment variables (EMBEDDING_API_KEY, EMBEDDING_BASE_URL)
 *   3. env/secrets.json → embedding.key / embedding.url
 *   4. Defaults
 *
 * The only external dependency is the Embedding API.
 */

export interface PlanReviewsConfig {
	/** Root directory containing .plan-reviews/ (defaults to auto-detected) */
	projectRoot: string;
	/** Path to the JSON cache file (.plan-reviews/.kb-index.json) */
	indexPath: string;
	/** Embedding API key */
	embeddingApiKey: string;
	/** Embedding API base URL (OpenAI-compatible) */
	embeddingBaseUrl: string;
	/** Embedding model name */
	embeddingModel: string;
	/** Vector dimension (must match embedding model) */
	vectorSize: number;
	/** Whether semantic search is enabled (requires embeddingApiKey) */
	semanticEnabled: boolean;
}

const DEFAULT_VECTOR_SIZES: Record<string, number> = {
	"bge-m3": 1024,
	"text-embedding-ada-002": 1536,
	"text-embedding-3-large": 3072,
	"text-embedding-3-small": 1536,
};

function optionalEnv(key: string, fallback: string): string {
	return process.env[key] ?? fallback;
}

interface EmbeddingSecrets {
	key: string;
	url: string;
}

/**
 * Read the `embedding` field from env/secrets.json.
 * Falls back to empty values if the file or field is missing.
 */
function loadEmbeddingSecrets(projectRoot: string): EmbeddingSecrets {
	try {
		const secretsPath = resolve(projectRoot, "env", "secrets.json");
		if (!existsSync(secretsPath)) return { key: "", url: "" };
		const raw = readFileSync(secretsPath, "utf-8");
		const secrets = JSON.parse(raw);
		const embedding = secrets?.embedding;
		if (!embedding || typeof embedding !== "object") return { key: "", url: "" };
		return {
			key: typeof embedding.key === "string" ? embedding.key : "",
			url: typeof embedding.url === "string" ? embedding.url : "",
		};
	} catch {
		return { key: "", url: "" };
	}
}

export function loadConfig(overrides?: Partial<PlanReviewsConfig>): PlanReviewsConfig {
	const projectRoot = overrides?.projectRoot ?? discoverProjectRoot();
	const embeddingModel = overrides?.embeddingModel
		?? optionalEnv("EMBEDDING_MODEL", "bge-m3");
	const rawVectorSize = process.env.VECTOR_SIZE ?? "";
	const vectorSize = rawVectorSize
		? parseInt(rawVectorSize, 10)
		: (DEFAULT_VECTOR_SIZES[embeddingModel] ?? 1024);

	const secrets = loadEmbeddingSecrets(projectRoot);
	const embeddingApiKey = overrides?.embeddingApiKey
		?? (optionalEnv("EMBEDDING_API_KEY", "") || secrets.key);
	const embeddingBaseUrl = overrides?.embeddingBaseUrl
		?? (optionalEnv("EMBEDDING_BASE_URL", "") || secrets.url || "https://api.openai.com/v1");

	return {
		projectRoot,
		indexPath: overrides?.indexPath
			?? `${projectRoot}/.plan-reviews/.kb-index.json`,
		embeddingApiKey,
		embeddingBaseUrl,
		embeddingModel,
		vectorSize,
		semanticEnabled: embeddingApiKey.length > 0,
	};
}

/**
 * Walk upward from cwd to find the project root by locating
 * the .plan-reviews/ or .codebuddy/ directory.
 */
function discoverProjectRoot(): string {
	let dir = process.cwd();

	for (let i = 0; i < 10; i++) {
		if (
			existsSync(`${dir}/.plan-reviews`)
			|| existsSync(`${dir}/.codebuddy`)
		) {
			return dir;
		}
		const parent = dir.substring(0, dir.lastIndexOf("/"));
		if (parent === dir || parent === "") break;
		dir = parent;
	}

	// Fallback to cwd
	return process.cwd();
}
