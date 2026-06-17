import { describe, it, expect } from "vitest";
import { loadConfig, applyGatewayConfigEnv, gatewayEnvFromConfig } from "../../src/config.js";

describe("loadConfig", () => {
    it("should read GATEWAY_PORT and GATEWAY_HOST from env", () => {
        process.env.GATEWAY_PORT = "4000";
        process.env.GATEWAY_HOST = "0.0.0.0";
        const config = loadConfig();
        expect(config.port).toBe(4000);
        expect(config.host).toBe("0.0.0.0");
    });

    it("should use default base URL for embeddings", () => {
        const config = loadConfig();
        expect(config.embeddingBaseUrl).toBe("https://api.openai.com/v1");
    });

    it("should use default embedding model", () => {
        const config = loadConfig();
        expect(config.embeddingModel).toBe("bge-m3");
    });

    it("should parse GRAPH_RAG_ENABLED as boolean", () => {
        process.env.GRAPH_RAG_ENABLED = "true";
        expect(loadConfig().graphRagEnabled).toBe(true);
        process.env.GRAPH_RAG_ENABLED = "false";
        expect(loadConfig().graphRagEnabled).toBe(false);
        process.env.GRAPH_RAG_ENABLED = "";
        expect(loadConfig().graphRagEnabled).toBe(false);
    });

    it("should return default value for optional vars", () => {
        // dotenv may set these from .env, so verify they exist at least
        const config = loadConfig();
        expect(typeof config.qdrantUrl).toBe("string");
        expect(typeof config.databaseUrl).toBe("string");
    });
});

describe("applyGatewayConfigEnv", () => {
    it("should set env vars from parsed JSON object", () => {
        const env: Record<string, string | undefined> = {};
        applyGatewayConfigEnv(
            { EMBEDDING_API_KEY: "sk-abc", EXTRACTION_MODEL: "gpt-4o" },
            env,
        );
        expect(env.EMBEDDING_API_KEY).toBe("sk-abc");
        expect(env.EXTRACTION_MODEL).toBe("gpt-4o");
    });

    it("should not override existing env vars", () => {
        const env = { EMBEDDING_API_KEY: "sk-existing" };
        applyGatewayConfigEnv({ EMBEDDING_API_KEY: "sk-abc" }, env);
        expect(env.EMBEDDING_API_KEY).toBe("sk-existing");
    });

    it("should skip null and non-string values", () => {
        const env: Record<string, string | undefined> = {};
        applyGatewayConfigEnv(
            { SKIP_NULL: null, SKIP_NUMBER: 42, KEEP_STRING: "ok" },
            env,
        );
        expect(env.SKIP_NULL).toBeUndefined();
        expect(env.SKIP_NUMBER).toBeUndefined();
        expect(env.KEEP_STRING).toBe("ok");
    });
});

describe("gatewayEnvFromConfig", () => {
    it("should get rag-gateway env from platforms config", () => {
        const values = gatewayEnvFromConfig({
            env: {},
            platforms: {
                "rag-gateway": {
                    env: {
                        EMBEDDING_BASE_URL: "https://rag-gateway.example",
                        EMBEDDING_API_KEY: "sk-rag-gateway",
                    },
                },
            },
        });

        expect(values.EMBEDDING_BASE_URL).toBe("https://rag-gateway.example");
        expect(values.EMBEDDING_API_KEY).toBe("sk-rag-gateway");
    });

    it("should keep legacy gateway env as a fallback", () => {
        const values = gatewayEnvFromConfig({
            platforms: {
                gateway: {
                    env: {
                        EMBEDDING_API_KEY: "sk-legacy",
                    },
                },
            },
        });

        expect(values.EMBEDDING_API_KEY).toBe("sk-legacy");
    });

    it("should let rag-gateway env override legacy gateway env", () => {
        const values = gatewayEnvFromConfig({
            platforms: {
                gateway: {
                    env: {
                        EMBEDDING_BASE_URL: "https://legacy.example",
                    },
                },
                "rag-gateway": {
                    env: {
                        EMBEDDING_BASE_URL: "https://rag-gateway.example",
                    },
                },
            },
        });

        expect(values.EMBEDDING_BASE_URL).toBe("https://rag-gateway.example");
    });
});
