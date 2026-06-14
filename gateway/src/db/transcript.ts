import crypto from "node:crypto";
import { getPool } from "./index.js";

export interface StoredConversation {
    id: string;
    tenantId: string;
    projectId?: string;
    client: string;
    model: string;
    startedAt: Date;
}

export interface StoredMessage {
    id: string;
    conversationId: string;
    turnIndex: number;
    role: string;
    content: string | null;
    toolCallsJson?: unknown;
    toolCallId?: string;
    name?: string;
    tokenCount?: number;
}

/**
 * Insert a new conversation record.
 */
export async function insertConversation(
    conv: StoredConversation,
): Promise<void> {
    const pool = getPool();
    await pool.query(
        `INSERT INTO conversation (id, tenant_id, project_id, client, model, started_at)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (id) DO NOTHING`,
        [
            conv.id,
            conv.tenantId,
            conv.projectId ?? null,
            conv.client,
            conv.model,
            conv.startedAt,
        ],
    );
}

/**
 * Append a message to a conversation.
 */
export async function insertMessage(msg: StoredMessage): Promise<void> {
    const pool = getPool();
    await pool.query(
        `INSERT INTO message (id, conversation_id, turn_index, role, content, tool_calls_json, tool_call_id, name, token_count)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
        [
            msg.id,
            msg.conversationId,
            msg.turnIndex,
            msg.role,
            msg.content,
            msg.toolCallsJson ? JSON.stringify(msg.toolCallsJson) : null,
            msg.toolCallId ?? null,
            msg.name ?? null,
            msg.tokenCount ?? null,
        ],
    );
}

/**
 * Update the end timestamp and total token count on a conversation.
 */
export async function finalizeConversation(
    conversationId: string,
    totalTokens: number,
): Promise<void> {
    const pool = getPool();
    await pool.query(
        `UPDATE conversation SET ended_at = now(), token_count = $2 WHERE id = $1`,
        [conversationId, totalTokens],
    );
}

/**
 * Generate a UUID v4.
 */
export function generateId(): string {
    return crypto.randomUUID();
}