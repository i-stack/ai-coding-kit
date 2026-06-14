import pg from "pg";

const { Pool } = pg;

let pool: pg.Pool | null = null;

export function getPool(): pg.Pool {
    if (!pool) {
        throw new Error("Database not initialized. Call initDb() first.");
    }
    return pool;
}

export function initDb(databaseUrl: string): pg.Pool {
    pool = new Pool({ connectionString: databaseUrl });
    return pool;
}

export async function closeDb(): Promise<void> {
    if (pool) {
        await pool.end();
        pool = null;
    }
}

/**
 * Run schema migrations on startup (idempotent).
 *
 * We create the tables if they don't exist, and add any missing columns
 * via DO $$ blocks so this is safe to run on every boot during development.
 */
export async function migrateSchema(): Promise<void> {
    const client = await getPool().connect();
    try {
        await client.query("BEGIN");

        // ── conversations ─────────────────────────────────────────────
        await client.query(
            `CREATE TABLE IF NOT EXISTS conversation (
                id          UUID PRIMARY KEY,
                tenant_id   TEXT NOT NULL DEFAULT 'default',
                project_id  TEXT,
                client      TEXT NOT NULL DEFAULT 'unknown',
                model       TEXT NOT NULL,
                started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                ended_at    TIMESTAMPTZ,
                token_count INTEGER DEFAULT 0
            );`
        );

        // ── messages ──────────────────────────────────────────────────
        await client.query(
            `CREATE TABLE IF NOT EXISTS message (
                id                UUID PRIMARY KEY,
                conversation_id   UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
                turn_index        INTEGER NOT NULL DEFAULT 0,
                role              TEXT NOT NULL,
                content           TEXT,
                tool_calls_json   JSONB,
                tool_call_id      TEXT,
                name              TEXT,
                token_count       INTEGER DEFAULT 0,
                created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
            );`
        );

        // ── indexes (idempotent via IF NOT EXISTS in PG 9.5+) ─────────
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_message_conversation ON message(conversation_id, turn_index);`
        );

        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_conversation_tenant_started ON conversation(tenant_id, started_at DESC);`
        );

        // ── entity (GraphRAG) ───────────────────────────────────────────
        await client.query(
            `CREATE TABLE IF NOT EXISTS entity (
                id          UUID PRIMARY KEY,
                tenant_id   TEXT NOT NULL DEFAULT 'default',
                project_id  TEXT,
                type        TEXT NOT NULL,
                name        TEXT NOT NULL,
                properties  JSONB NOT NULL DEFAULT '{}',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );`
        );

        // ── entity_edge (GraphRAG) ──────────────────────────────────────
        await client.query(
            `CREATE TABLE IF NOT EXISTS entity_edge (
                id              UUID PRIMARY KEY,
                tenant_id       TEXT NOT NULL DEFAULT 'default',
                project_id      TEXT,
                from_entity_id  UUID NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
                to_entity_id    UUID NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
                relation        TEXT NOT NULL,
                properties      JSONB NOT NULL DEFAULT '{}',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            );`
        );

        // ── GraphRAG indexes ────────────────────────────────────────────
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_name ON entity(name);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_type ON entity(type);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_tenant ON entity(tenant_id);`
        );
        await client.query(
            `CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_name_tenant ON entity(name, tenant_id);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_tenant_project ON entity(tenant_id, project_id);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_edge_from ON entity_edge(from_entity_id);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_edge_to ON entity_edge(to_entity_id);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_entity_edge_relation ON entity_edge(relation);`
        );
        await client.query(
            `CREATE INDEX IF NOT EXISTS idx_edge_tenant_project ON entity_edge(tenant_id, project_id);`
        );

        await client.query("COMMIT");
    } catch (err) {
        await client.query("ROLLBACK");
        throw err;
    } finally {
        client.release();
    }
}