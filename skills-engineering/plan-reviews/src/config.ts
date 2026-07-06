import { existsSync } from "node:fs";

/**
 * Configuration for the plan-reviews knowledge base.
 *
 * Sources:
 *   1. Environment variables (dotenv from caller or .env)
 *   2. Defaults
 *
 * All heavy-service dependencies from rag-gateway are removed.
 * The only external dependency retained is the Embedding API.
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

export function loadConfig(overrides?: Partial<PlanReviewsConfig>): PlanReviewsConfig {
	const projectRoot = overrides?.projectRoot ?? discoverProjectRoot();
	const embeddingModel = overrides?.embeddingModel
		?? optionalEnv("EMBEDDING_MODEL", "bge-m3");
	const rawVectorSize = process.env.VECTOR_SIZE ?? "";
	const vectorSize = rawVectorSize
		? parseInt(rawVectorSize, 10)
		: (DEFAULT_VECTOR_SIZES[embeddingModel] ?? 1024);
	const embeddingApiKey = overrides?.embeddingApiKey
		?? optionalEnv("EMBEDDING_API_KEY", "");

	return {
		projectRoot,
		indexPath: overrides?.indexPath
			?? `${projectRoot}/.plan-reviews/.kb-index.json`,
		embeddingApiKey,
		embeddingBaseUrl: overrides?.embeddingBaseUrl
			?? optionalEnv("EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
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
