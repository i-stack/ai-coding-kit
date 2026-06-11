/**
 * Minimal Qdrant REST client using native fetch.
 *
 * Replaces @qdrant/js-client-rest which is incompatible with Node.js 26's undici v8.
 * Implements only the subset of the Qdrant API needed by the gateway:
 *   - createCollection (if not exists)
 *   - upsert points
 *   - search
 *   - getCollections
 *   - deleteCollection
 */

const DEFAULT_COLLECTION = "memory_chunks";
const VECTOR_SIZE = 256; // bge-m3 via OpenAI SDK returns 256-dim

export interface QdrantSearchResult {
	id: string;
	score: number;
	payload: {
		text: string;
		tenantId: string;
		projectId?: string;
		sourceMessageId?: string;
		kind: string;
		createdAt: string;
	};
}

interface QdrantPoint {
	id: string;
	vector: number[];
	payload: Record<string, unknown>;
}

export class QdrantStore {
	private baseUrl: string;
	private collectionName: string;

	constructor(url: string, collectionName = DEFAULT_COLLECTION) {
		// Strip trailing slash from base URL
		this.baseUrl = url.replace(/\/+$/, "");
		this.collectionName = collectionName;
	}

	private async request<T>(
		method: string,
		path: string,
		body?: unknown,
	): Promise<T> {
		const url = `${this.baseUrl}${path}`;
		const res = await fetch(url, {
			method,
			headers: { "Content-Type": "application/json" },
			body: body ? JSON.stringify(body) : undefined,
		});
		if (!res.ok) {
			const text = await res.text();
			throw new Error(`Qdrant ${method} ${path}: ${res.status} ${text}`);
		}
		const json = (await res.json()) as { result: T; status: string };
		return json.result;
	}

	/**
	 * Ensure the collection exists (create if missing). Idempotent.
	 */
	async ensureCollection(): Promise<void> {
		const result = await this.request<{ collections: { name: string }[] }>("GET", "/collections");
		const exists = result.collections.some((c) => c.name === this.collectionName);

		if (!exists) {
			await this.request("PUT", `/collections/${this.collectionName}`, {
				vectors: {
					size: VECTOR_SIZE,
					distance: "Cosine",
				},
			});
			console.log(
				`📦 Qdrant collection "${this.collectionName}" created (size=${VECTOR_SIZE})`,
			);
		}
	}

	/**
	 * Upsert a single point (vector + payload).
	 */
	async upsert(
		id: string,
		vector: number[],
		payload: Record<string, unknown>,
	): Promise<void> {
		await this.upsertBatch([{ id, vector, payload }]);
	}

	/**
	 * Upsert multiple points in one batch.
	 */
	async upsertBatch(points: QdrantPoint[]): Promise<void> {
		if (points.length === 0) return;
		await this.request("PUT", `/collections/${this.collectionName}/points`, {
			points: points.map((p) => ({
				id: p.id,
				vector: p.vector,
				payload: p.payload,
			})),
		});
	}

	/**
	 * Ensure payload indexes exist for filterable fields (tenantId, projectId).
	 *
	 * Without these, Qdrant does a full scan of all points when filtering,
	 * which degrades to O(n) per search.
	 */
	async ensurePayloadIndexes(): Promise<void> {
		const indexDefs = [
			{ field_name: "tenantId", field_type: "keyword" },
			{ field_name: "projectId", field_type: "keyword" },
		];
		for (const idx of indexDefs) {
			try {
				await this.request("PUT", `/collections/${this.collectionName}/index`, idx);
				console.log(`📦 Qdrant payload index "${idx.field_name}" created`);
			} catch {
				// Index already exists — fine
			}
		}
	}

	/**
	 * Search for similar vectors by query vector.
	 */
	async search(
		vector: number[],
		options?: {
			limit?: number;
			tenantId?: string;
			projectId?: string;
		},
	): Promise<QdrantSearchResult[]> {
		const must: Array<Record<string, unknown>> = [];
		if (options?.tenantId) {
			must.push({
				key: "tenantId",
				match: { value: options.tenantId },
			});
		}
		if (options?.projectId) {
			must.push({
				key: "projectId",
				match: { value: options.projectId },
			});
		}
		const filter = must.length > 0 ? { must } : undefined;

		const result = await this.request<{
			id: string;
			score: number;
			payload: QdrantSearchResult["payload"];
		}[]>("POST", `/collections/${this.collectionName}/points/search`, {
			vector,
			limit: options?.limit ?? 5,
			filter,
			with_payload: true,
		});

		return result.map((r) => ({
			id: String(r.id),
			score: r.score ?? 0,
			payload: r.payload,
		}));
	}

	/**
	 * Delete a collection (for testing / reset).
	 */
	async deleteCollection(): Promise<void> {
		await this.request("DELETE", `/collections/${this.collectionName}`);
	}
}