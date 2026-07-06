/**
 * Embedding API client for plan-reviews knowledge base.
 *
 * Directly ported from rag-gateway's src/vector/embedding.ts,
 * using the same OpenAI-compatible API pattern.
 *
 * Uses native fetch (no OpenAI SDK) to avoid the dimension misreporting
 * issues observed with bge-m3.
 */

import type { PlanReviewsConfig } from "./config.js";

export class EmbeddingService {
	private apiKey: string;
	private baseUrl: string;
	private model: string;

	constructor(config: PlanReviewsConfig) {
		this.apiKey = config.embeddingApiKey;
		this.baseUrl = config.embeddingBaseUrl.replace(/\/+$/, "");
		this.model = config.embeddingModel;
	}

	/**
	 * Whether this service is usable (API key is configured).
	 */
	get isAvailable(): boolean {
		return this.apiKey.length > 0;
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
	 * Sends all texts in a single API call for efficiency.
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
				Authorization: `Bearer ${this.apiKey}`,
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
