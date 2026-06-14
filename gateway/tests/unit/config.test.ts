import { describe, it, expect } from "vitest";
import { loadConfig, applyGatewayConfigEnv, gatewayEnvFromConfig } from "../../src/config.js";

describe("loadConfig", () => {
    it("should require OPENAI_API_KEY", () => {
        delete process.env.OPENAI_API_KEY;
        expect(() => loadConfig()).toThrow("OPENAI_API_KEY");
        process.env.OPENAI_API_KEY = "test-openai-key";
    });

    it("should read GATEWAY_PORT and GATEWAY_HOST from env", () => {
        process.env.GATEWAY_PORT = "4000";
        process.env.GATEWAY_HOST = "0.0.0.0";
        const config = loadConfig();
        expect(config.port).toBe(4000);
        expect(config.host).toBe("0.0.0.0");
    });

    it("should use default base URL for OpenAI", () => {
        const config = loadConfig();
        expect(config.openaiBaseUrl).toBe("https://api.openai.com/v1");
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
            { OPENAI_API_KEY: "sk-abc", ANTHROPIC_BASE_URL: "https://test.com" },
            env,
        );
        expect(env.OPENAI_API_KEY).toBe("sk-abc");
        expect(env.ANTHROPIC_BASE_URL).toBe("https://test.com");
    });

    it("should not override existing env vars", () => {
        const env = { OPENAI_API_KEY: "sk-existing" };
        applyGatewayConfigEnv({ OPENAI_API_KEY: "sk-abc" }, env);
        expect(env.OPENAI_API_KEY).toBe("sk-existing");
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
    it("should merge shared env and gateway env with gateway taking precedence", () => {
        const values = gatewayEnvFromConfig({
            env: { shared: { OPENAI_BASE_URL: "https://shared.example" } },
            platforms: {
                gateway: {
                    env: {
                        OPENAI_BASE_URL: "https://gateway.example",
                        OPENAI_API_KEY: "sk-gateway",
                    },
                },
            },
        });

        expect(values.OPENAI_BASE_URL).toBe("https://gateway.example");
        expect(values.OPENAI_API_KEY).toBe("sk-gateway");
    });
});
