import crypto from "node:crypto";
import { loadConfig } from "../src/config.js";
import { EmbeddingService } from "../src/vector/embedding.js";
import { QdrantStore } from "../src/vector/qdrant.js";
import { VectorStore } from "../src/vector/store.js";

async function seed() {
  const config = loadConfig();
  if (!config.qdrantUrl) {
    console.error("QDRANT_URL not set");
    process.exit(1);
  }
  const embedding = new EmbeddingService(config);
  const qdrant = new QdrantStore(config.qdrantUrl);
  await qdrant.ensureCollection();
  await qdrant.ensurePayloadIndexes();
  const store = new VectorStore(embedding, qdrant);

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
}

seed().catch(console.error);