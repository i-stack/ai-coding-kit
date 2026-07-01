import crypto from "node:crypto";
import { loadConfig } from "../src/config.js";
import { EmbeddingService } from "../src/vector/embedding.js";
import { QdrantStore } from "../src/vector/qdrant.js";
import { VectorStore } from "../src/vector/store.js";
import { initDb } from "../src/db/index.js";
import * as graphDb from "../src/db/graph.js";

async function seed() {
  const config = loadConfig();
  if (!config.qdrantUrl) {
    console.error("QDRANT_URL not set");
    process.exit(1);
  }

  // ── PostgreSQL init (for GraphRAG) ───────────────────────────────────
  if (config.databaseUrl) {
    initDb(config.databaseUrl);
    console.log("PostgreSQL pool initialized");
  } else {
    console.warn("DATABASE_URL not set — skipping GraphRAG entity seeding");
  }

  const embedding = new EmbeddingService(config);
  const qdrant = new QdrantStore(config.qdrantUrl, { vectorSize: config.vectorSize });
  await qdrant.ensureCollection();
  await qdrant.ensurePayloadIndexes();
  const store = new VectorStore(embedding, qdrant);

  // ── Qdrant semantic documents ────────────────────────────────────────
  const docs = [
    "The RAG gateway is an MCP server that provides semantic memory search and entity graph retrieval.",
    "Qdrant is used as the vector store for semantic memory in the RAG gateway.",
    "The gateway connects to Claude via MCP SSE transport at /mcp/sse.",
    "GraphRAG stores entities and relationships in PostgreSQL for knowledge graph search.",
    "Tools are defined declaratively in tools.json and executed by ToolExecutorEngine.",
    "The embedding service converts text to vectors using the bge-m3 model.",
    "Entity extraction uses an LLM to extract structured entities from conversation text.",
    "The gateway supports multi-tenant isolation via tenant_id and project_id parameters.",
    "MCP clients discover available tools via tools/list and invoke them via tools/call.",
  ];

  for (const text of docs) {
    await store.indexMessage({
      id: crypto.randomUUID(),
      text,
      kind: "system_prompt",
      tenantId: "default",
      sourceMessageId: crypto.randomUUID(),
      conversationId: "seed-init",
    });
  }
  console.log(`Seeded ${docs.length} documents into Qdrant`);

  // ── GraphRAG entities and edges ──────────────────────────────────────
  if (config.databaseUrl) {
    const tenantId = "default";

    // Define entities: [name, type, properties]
    const entityDefs: Array<{ name: string; type: string; properties: Record<string, unknown> }> = [
      { name: "MyApp", type: "project", properties: {} },
      { name: "PostgreSQL", type: "database", properties: { type: "Relational Database", purpose: "Primary data storage" } },
      { name: "Redis", type: "database", properties: { type: "In-memory data store", purpose: "Caching and session management" } },
      { name: "AuthService API", type: "api", properties: { purpose: "Handles authentication and token validation" } },
      { name: "EC2", type: "technology", properties: {} },
      { name: "Kafka", type: "technology", properties: {} },
      { name: "LogService", type: "service", properties: { description: "Centralized logging service" } },
    ];

    // In-memory name → generated UUID mapping for edge construction
    const nameToId = new Map<string, string>();
    for (const def of entityDefs) {
      const id = crypto.randomUUID();
      nameToId.set(def.name, id);
    }

    // Upsert entities
    const entities = entityDefs.map((def) => ({
      id: nameToId.get(def.name)!,
      tenantId,
      type: def.type,
      name: def.name,
      properties: def.properties,
    }));
    const persistedIds = await graphDb.upsertEntities(entities);
    console.log(`Seeded ${persistedIds.size} entities into PostgreSQL`);

    // Define edges: [from, to, relation]
    const edgeDefs: Array<{ from: string; to: string; relation: string }> = [
      { from: "MyApp", to: "PostgreSQL", relation: "uses" },
      { from: "MyApp", to: "Redis", relation: "uses" },
      { from: "MyApp", to: "AuthService API", relation: "uses" },
    ];

    // Resolve actual DB IDs (ON CONFLICT may have returned different IDs than in-memory)
    const resolvedNameToId = new Map(nameToId);
    for (const [name, id] of persistedIds) {
      resolvedNameToId.set(name, id);
    }

    const edges = edgeDefs
      .filter((e) => resolvedNameToId.has(e.from) && resolvedNameToId.has(e.to))
      .map((e) => ({
        id: crypto.randomUUID(),
        tenantId,
        fromEntityId: resolvedNameToId.get(e.from)!,
        toEntityId: resolvedNameToId.get(e.to)!,
        relation: e.relation,
        properties: {},
      }));

    if (edges.length > 0) {
      await graphDb.insertEdges(edges);
      console.log(`Seeded ${edges.length} edges into PostgreSQL`);
    }

    console.log(`GraphRAG seed complete — ${entityDefs.length} entities, ${edgeDefs.length} edges`);
  }
}

seed().catch(console.error);