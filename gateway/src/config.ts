import "dotenv/config";

export interface GatewayConfig {
	port: number;
	host: string;
	openaiApiKey: string;
	openaiBaseUrl: string;
	openaiDefaultModel: string;
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

export function loadConfig(): GatewayConfig {
	return {
		port: parseInt(optionalEnv("GATEWAY_PORT", "3000"), 10),
		host: optionalEnv("GATEWAY_HOST", "0.0.0.0"),
		openaiApiKey: requireEnv("OPENAI_API_KEY"),
		openaiBaseUrl: optionalEnv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
		openaiDefaultModel: optionalEnv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
		databaseUrl: optionalEnv("DATABASE_URL", ""),
		qdrantUrl: optionalEnv("QDRANT_URL", ""),
		graphRagEnabled: process.env.GRAPH_RAG_ENABLED === "true",
	};
}