import OpenAI from "openai";
import type { GatewayConfig } from "../config.js";

/**
 * Embedding service that uses the same upstream provider as the chat endpoint.
 *
 * Configured via the existing OPENAI_API_KEY and OPENAI_BASE_URL.
 * Uses the "bge-m3" model (256-dim via OpenAI SDK, 1024-dim native).
 */
export class EmbeddingService {
  private client: OpenAI;
  private model: string;

  constructor(config: GatewayConfig, model = "bge-m3") {
    this.client = new OpenAI({
      apiKey: config.openaiApiKey,
      baseURL: config.openaiBaseUrl,
    });
    this.model = model;
  }

  /**
   * Generate an embedding vector for a single text string.
   */
  async embed(text: string): Promise<number[]> {
    const response = await this.client.embeddings.create({
      model: this.model,
      input: text,
    });
    return response.data[0].embedding;
  }

  /**
   * Generate embedding vectors for multiple texts (batched).
   */
  async embedBatch(texts: string[]): Promise<number[][]> {
    if (texts.length === 0) return [];

    const response = await this.client.embeddings.create({
      model: this.model,
      input: texts,
    });

    // Sort by index to maintain order
    const sorted = response.data.sort((a, b) => a.index - b.index);
    return sorted.map((d) => d.embedding);
  }
}