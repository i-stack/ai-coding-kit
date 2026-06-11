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

    it("should use defaults for optional values", () => {
        // Save and clear env vars that .env might set
        const savedQdrant = process.env.QDRANT_URL;
        const savedDb = process.env.DATABASE_URL;
        delete process.env.QDRANT_URL;
        delete process.env.DATABASE_URL;
        // dotenv was already loaded at import time — re-read config
        const config = loadConfig();
        expect(config.openaiBaseUrl).toBe("https://api.openai.com/v1");
        expect(config.qdrantUrl).toBe("");
        expect(config.databaseUrl).toBe("");
        if (savedQdrant) process.env.QDRANT_URL = savedQdrant;
        if (savedDb) process.env.DATABASE_URL = savedDb;
    });

    it("should parse GRAPH_RAG_ENABLED as boolean", () => {
        process.env.GRAPH_RAG_ENABLED = "true";
        expect(loadConfig().graphRagEnabled).toBe(true);
        process.env.GRAPH_RAG_ENABLED = "false";
        expect(loadConfig().graphRagEnabled).toBe(false);
        process.env.GRAPH_RAG_ENABLED = "";
        expect(loadConfig().graphRagEnabled).toBe(false);
    });
});