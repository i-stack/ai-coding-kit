import type { GatewayConfig } from "../config.js";

/**
 * Embedding service that converts text to vectors for Qdrant search.
 *
 * Uses native fetch instead of the OpenAI SDK because the SDK misreports
 * bge-m3 vector dimensions (returns 256-dim zeros instead of 1024-dim real).
 *
 * Configured via EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL.
 */
export class EmbeddingService {
    private apiKey: string;
    private baseUrl: string;
    private model: string;

    constructor(config: GatewayConfig, model?: string) {
        this.apiKey = config.embeddingApiKey;
        this.baseUrl = config.embeddingBaseUrl.replace(/\/+$/, "");
        this.model = model ?? config.embeddingModel;
    }

    /**
     * Generate an embedding vector for a single text string.
     */
    async embed(text: string): Promise<number[]> {
        const results = await this._create(text);
        return results[0];
    }

    /**
     * Generate embedding vectors for multiple texts (batched).
     */
    async embedBatch(texts: string[]): Promise<number[][]> {
        if (texts.length === 0) return [];
        return this._create(texts);
    }

    /**
     * Internal: call the OpenAI-compatible embeddings API via native fetch.
     */
    private async _create(input: string | string[]): Promise<number[][]> {
        const url = `${this.baseUrl}/embeddings`;
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${this.apiKey}`,
            },
            body: JSON.stringify({
                model: this.model,
                input,
            }),
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Embedding API ${response.status}: ${text}`);
        }

        const json = (await response.json()) as {
            data: Array<{ embedding: number[]; index: number }>;
        };

        // Sort by index to maintain order
        return json.data
            .sort((a, b) => a.index - b.index)
            .map((d) => d.embedding);
    }
}