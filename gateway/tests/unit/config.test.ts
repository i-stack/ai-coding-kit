import { describe, it, expect } from "vitest";
import { loadConfig, applySharedMappings, SHARED_MAPPINGS } from "../../src/config.js";

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

describe("applySharedMappings", () => {
    it("should set all mapped env vars from full shared config", () => {
        const shared = {
            ANTHROPIC_AUTH_TOKEN: "sk-abc123",
            ANTHROPIC_BASE_URL: "https://platform.example.com",
            ANTHROPIC_MODEL: "deepseek-v4",
        };
        const env: Record<string, string | undefined> = {};

        applySharedMappings(shared, env, SHARED_MAPPINGS);

        expect(env.OPENAI_API_KEY).toBe("sk-abc123");
        expect(env.ANTHROPIC_API_KEY).toBe("sk-abc123");
        expect(env.ANTHROPIC_BASE_URL).toBe("https://platform.example.com");
        expect(env.OPENAI_BASE_URL).toBe("https://platform.example.com/v1");
        expect(env.OPENAI_DEFAULT_MODEL).toBe("deepseek-v4");
    });

    it("should not override existing env vars", () => {
        const shared = {
            ANTHROPIC_AUTH_TOKEN: "sk-shared",
            ANTHROPIC_BASE_URL: "https://shared.com",
            ANTHROPIC_MODEL: "gpt-4o",
        };
        const env = {
            OPENAI_API_KEY: "sk-existing",
            ANTHROPIC_BASE_URL: "https://existing.com",
        };

        applySharedMappings(shared, env, SHARED_MAPPINGS);

        expect(env.OPENAI_API_KEY).toBe("sk-existing");
        expect(env.ANTHROPIC_BASE_URL).toBe("https://existing.com");
        expect(env.OPENAI_DEFAULT_MODEL).toBe("gpt-4o"); // was unset, so set
    });

    it("should skip missing shared keys gracefully", () => {
        const shared = { ANTHROPIC_AUTH_TOKEN: "sk-abc" };
        const env: Record<string, string | undefined> = {};

        applySharedMappings(shared, env, SHARED_MAPPINGS);

        expect(env.OPENAI_API_KEY).toBe("sk-abc");
        // ANTHROPIC_BASE_URL not in shared → OPENAI_BASE_URL / ANTHROPIC_BASE_URL stay unset
        expect(env.OPENAI_BASE_URL).toBeUndefined();
        expect(env.ANTHROPIC_BASE_URL).toBeUndefined();
        expect(env.OPENAI_DEFAULT_MODEL).toBeUndefined();
    });

    it("should apply /v1 transform to OPENAI_BASE_URL", () => {
        const shared = {
            ANTHROPIC_AUTH_TOKEN: "sk-abc",
            ANTHROPIC_BASE_URL: "https://api.test.com",
        };
        const env: Record<string, string | undefined> = {};

        applySharedMappings(shared, env, SHARED_MAPPINGS);

        expect(env.OPENAI_BASE_URL).toBe("https://api.test.com/v1");
    });

    it("should handle null values in shared config", () => {
        const shared: Record<string, string> = {
            ANTHROPIC_AUTH_TOKEN: "sk-abc",
            ANTHROPIC_BASE_URL: "", // empty but present — should still set
        };
        const env: Record<string, string | undefined> = {};

        applySharedMappings(shared, env, SHARED_MAPPINGS);

        expect(env.OPENAI_API_KEY).toBe("sk-abc");
        expect(env.ANTHROPIC_BASE_URL).toBe("");
        expect(env.OPENAI_BASE_URL).toBe("/v1"); // "" + "/v1" = "/v1"
        expect(env.OPENAI_DEFAULT_MODEL).toBeUndefined();
    });
});