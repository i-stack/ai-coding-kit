import Fastify from "fastify";
import cors from "@fastify/cors";
import { loadConfig } from "./config.js";
import { OpenAIProvider } from "./provider/openai.js";
import { registerChatRoutes } from "./routes/chat.js";
import { initDb, migrateSchema } from "./db/index.js";

async function main() {
  const config = loadConfig();

  const app = Fastify({
    logger: {
      level: "info",
    },
  });

  // ── CORS (permissive for MVP; tighten in production) ───────────────
  await app.register(cors, {
    origin: true,
  });

  // ── Database (optional — degrade gracefully) ────────────────────────
  if (config.databaseUrl) {
    try {
      initDb(config.databaseUrl);
      await migrateSchema();
      console.log("📦 PostgreSQL connected and schema migrated");
    } catch (err) {
      console.error(
        "⚠️  PostgreSQL unavailable — transcripts will not be stored:",
        (err as Error).message,
      );
    }
  } else {
    console.log("⚠️  DATABASE_URL not set — transcripts will not be stored");
  }

  // ── Health check ────────────────────────────────────────────────────
  app.get("/health", async () => {
    return { status: "ok", timestamp: new Date().toISOString() };
  });

  // ── Provider ────────────────────────────────────────────────────────
  const provider = new OpenAIProvider(config);

  // ── Routes ──────────────────────────────────────────────────────────
  registerChatRoutes(app, provider, config);

  // ── Start ───────────────────────────────────────────────────────────
  const address = await app.listen({ port: config.port, host: config.host });
  console.log(`🚀 Gateway listening on ${address}`);
}

main().catch((err) => {
  console.error("Failed to start gateway:", err);
  process.exit(1);
});