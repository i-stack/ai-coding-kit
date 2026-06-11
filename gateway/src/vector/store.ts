import crypto from "node:crypto";
import type { EmbeddingService } from "./embedding.js";
import type { QdrantStore, QdrantSearchResult } from "./qdrant.js";

/**
 * A chunk of a message ready for vector storage.
 */
export interface ChunkedMessage {
    id: string;
    text: string;
    kind: "user_message" | "assistant_message" | "system_prompt" | "summary";
    tenantId: string;
    projectId?: string;
    sourceMessageId: string;
    conversationId: string;
}

/**
 * High-level store layer that embeds text chunks and indexes them in Qdrant.
 */
export class VectorStore {
    private embedding: EmbeddingService;
    private qdrant: QdrantStore;

    constructor(embedding: EmbeddingService, qdrant: QdrantStore) {
        this.embedding = embedding;
        this.qdrant = qdrant;
    }

    /**
     * Chunk a message into segments (simple split by newline or by token-budget).
     * For MVP: split on double-newlines, fall back to 500-char segments.
     */
    chunkMessage(
        message: ChunkedMessage,
        maxChunkLength = 500,
    ): Array<{ text: string; id: string }> {
        const segments: Array<{ text: string; id: string }> = [];

        // Try splitting by double-newline first (paragraph boundaries)
        const paragraphs = message.text.split(/\n\n+/);

        for (const para of paragraphs) {
            const trimmed = para.trim();
            if (!trimmed) continue;

            if (trimmed.length <= maxChunkLength) {
                segments.push({
                    id: crypto.randomUUID(),
                    text: trimmed,
                });
            } else {
                // Further split long paragraphs by sentence or char boundary
                let remaining = trimmed;
                while (remaining.length > 0) {
                    const chunk = remaining.slice(0, maxChunkLength);
                    segments.push({
                        id: crypto.randomUUID(),
                        text: chunk,
                    });
                    remaining = remaining.slice(maxChunkLength);
                }
            }
        }

        return segments;
    }

    /**
     * Index a single message: chunk → embed → upsert into Qdrant.
     */
    async indexMessage(chunked: ChunkedMessage): Promise<void> {
        const segments = this.chunkMessage(chunked);
        if (segments.length === 0) return;

        // Generate embeddings in batch
        const vectors = await this.embedding.embedBatch(
            segments.map((s) => s.text),
        );

        await this.qdrant.upsertBatch(
            segments.map((seg, i) => ({
                id: seg.id,
                vector: vectors[i],
                payload: {
                    text: seg.text,
                    tenantId: chunked.tenantId,
                    projectId: chunked.projectId ?? null,
                    sourceMessageId: chunked.sourceMessageId,
                    conversationId: chunked.conversationId,
                    kind: chunked.kind,
                    createdAt: new Date().toISOString(),
                },
            })),
        );
    }

    /**
     * Index multiple messages in batch.
     */
    async indexMessages(chunks: ChunkedMessage[]): Promise<void> {
        // Flatten all segments across all messages
        const allSegments: Array<{
            text: string;
            id: string;
            payload: Record<string, unknown>;
        }> = [];

        for (const chunk of chunks) {
            const segments = this.chunkMessage(chunk);
            for (const seg of segments) {
                allSegments.push({
                    id: seg.id,
                    text: seg.text,
                    payload: {
                        text: seg.text,
                        tenantId: chunk.tenantId,
                        projectId: chunk.projectId ?? null,
                        sourceMessageId: chunk.sourceMessageId,
                        conversationId: chunk.conversationId,
                        kind: chunk.kind,
                        createdAt: new Date().toISOString(),
                    },
                });
            }
        }

        if (allSegments.length === 0) return;

        // Batch embed all texts
        const vectors = await this.embedding.embedBatch(
            allSegments.map((s) => s.text),
        );

        await this.qdrant.upsertBatch(
            allSegments.map((seg, i) => ({
                id: seg.id,
                vector: vectors[i],
                payload: seg.payload,
            })),
        );
    }

    /**
     * Search for relevant memory chunks by query text.
     */
    async search(
        query: string,
        options?: {
            limit?: number;
            tenantId?: string;
        },
    ): Promise<QdrantSearchResult[]> {
        const vector = await this.embedding.embed(query);
        return this.qdrant.search(vector, {
            limit: options?.limit ?? 5,
            tenantId: options?.tenantId,
        });
    }
}