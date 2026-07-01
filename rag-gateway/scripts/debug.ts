import { loadConfig } from "../src/config.js";
import { EmbeddingService } from "../src/vector/embedding.js";
import { QdrantStore } from "../src/vector/qdrant.js";

async function debug() {
  const config = loadConfig();
  console.log("Config:", JSON.stringify(config, null, 2));

  // Test embedding
  const embedding = new EmbeddingService(config);
  try {
    const vec = await embedding.embed("test query RAG gateway");
    console.log("Embedding OK, vector length:", vec.length, "first 5:", vec.slice(0, 5));
  } catch (e) {
    console.error("Embedding FAILED:", (e as Error).message);
  }

  // Test Qdrant direct search
  const qdrant = new QdrantStore(config.qdrantUrl!, { vectorSize: config.vectorSize });
  try {
    const vec = await embedding.embed("RAG gateway");
    const results = await qdrant.search(vec, { limit: 5, tenantId: "default" });
    console.log("Direct Qdrant search results:", results.length);
    for (const r of results) {
      console.log("  score:", r.score, "text:", r.payload.text?.substring(0, 100));
    }
  } catch (e) {
    console.error("Qdrant search FAILED:", (e as Error).message);
  }
}

debug();