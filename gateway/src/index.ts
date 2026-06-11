import Fastify from "fastify";
import cors from "@fastify/cors";
import { loadConfig } from "./config.js";
import { ProviderRouter } from "./provider/router.js";
import { registerChatRoutes } from "./routes/chat.js";
import { initDb, migrateSchema } from "./db/index.js";
import { EmbeddingService } from "./vector/embedding.js";
import { QdrantStore } from "./vector/qdrant.js";
import { VectorStore } from "./vector/store.js";
import { ToolRegistry } from "./tool/registry.js";
import { ToolExecutorEngine } from "./tool/executor.js";
import { EntityStore } from "./entity/store.js";
import { metricsCollector } from "./metrics.js";
import { registerMcpServer } from "./mcp/server.js";

async function main() {
	const config = loadConfig();

	const app = Fastify({
		logger: {
			level: "info",
		},
	});

	// -- CORS (permissive for MVP; tighten in production) --------------------
	await app.register(cors, {
		origin: true,
	});

	// Track startup degradations
	const startupDegradations: string[] = [];

	// -- Database (optional - degrade gracefully) ---------------------------
	if (config.databaseUrl) {
		try {
			initDb(config.databaseUrl);
			await migrateSchema();
			app.log.info("PostgreSQL connected and schema migrated");
		} catch (err) {
			const msg = (err as Error).message;
			app.log.warn({ err }, "PostgreSQL unavailable - transcripts will not be stored");
			startupDegradations.push("postgres");
			metricsCollector.recordDegradation("postgres", msg);
		}
	} else {
		app.log.info("DATABASE_URL not set - transcripts will not be stored");
	}

	// -- Qdrant semantic memory (optional - degrade gracefully) -------------
	let vectorStore: VectorStore | undefined;
	if (config.qdrantUrl) {
		try {
			const embedding = new EmbeddingService(config);
			const qdrant = new QdrantStore(config.qdrantUrl);
			await qdrant.ensureCollection();
			await qdrant.ensurePayloadIndexes();
			vectorStore = new VectorStore(embedding, qdrant);
			app.log.info("Qdrant semantic memory ready");
		} catch (err) {
			const msg = (err as Error).message;
			app.log.warn({ err }, "Qdrant unavailable - semantic memory disabled");
			startupDegradations.push("qdrant");
			metricsCollector.recordDegradation("qdrant", msg);
		}
	} else {
		app.log.info("QDRANT_URL not set - semantic memory disabled");
	}

	// -- Entity store / GraphRAG (optional - requires DB + config flag) -----
	let entityStore: EntityStore | undefined;
	if (config.databaseUrl && config.graphRagEnabled) {
		try {
			entityStore = new EntityStore(config);
			app.log.info("GraphRAG entity store ready");
		} catch (err) {
			const msg = (err as Error).message;
			app.log.warn({ err }, "GraphRAG unavailable - entity extraction disabled");
			startupDegradations.push("entity-extraction");
			metricsCollector.recordDegradation("entity-extraction", msg);
		}
	} else {
		app.log.info(
			config.graphRagEnabled
				? "DATABASE_URL not set - GraphRAG disabled"
				: "GRAPH_RAG_ENABLED not set - GraphRAG disabled",
		);
	}

	// -- Declarative tool registry -----------------------------------------
	const toolRegistry = new ToolRegistry();
	toolRegistry.loadFromFile();
	app.log.info(`Tool registry: ${toolRegistry.count} tools loaded`);

	// -- Tool executor ------------------------------------------------
	const toolExecutor = new ToolExecutorEngine(undefined);

	// -- Health check -------------------------------------------------------
	app.get("/health", async () => {
		return { status: "ok", timestamp: new Date().toISOString() };
	});

	// -- Metrics endpoint ---------------------------------------------------
	app.get("/metrics", async () => {
		return metricsCollector.snapshot();
	});

	// -- Provider (multi-provider router) -----------------------------------
	const provider = new ProviderRouter(config);
	app.log.info(`Provider router: ${provider.providerNames.join(" + ")}`);

	// -- Routes -------------------------------------------------------------
	registerChatRoutes(app, provider, config, vectorStore, entityStore, toolRegistry, toolExecutor);
	registerMcpServer(app, toolRegistry, toolExecutor);

	// -- Start --------------------------------------------------------------
	const address = await app.listen({ port: config.port, host: config.host });
	app.log.info({ address, degradations: startupDegradations }, "Gateway started");

	// -- Graceful shutdown --------------------------------------------------
	const shutdown = async () => {
		app.log.info("Shutting down...");
		await app.close();
	};
	process.on("SIGTERM", shutdown);
	process.on("SIGINT", shutdown);
}

main().catch((err) => {
	console.error("Failed to start gateway:", err);
	process.exit(1);
});