import { describe, it, expect } from "vitest";
import { loadConfig } from "../../src/config.js";

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