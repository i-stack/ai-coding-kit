import http from "node:http";

export interface RequestRecord {
    timestamp: string;
    method: string;
    path: string;
    body: any;
    inputCharCount: number;
    inputTokenEstimate: number;
}

/**
 * A mock HTTP server that records every request payload for token comparison.
 * Always returns a fixed success response.
 */
export class MockProviderServer {
    private server: http.Server;
    private _port: number = 0;
    private _recordedRequests: RequestRecord[] = [];
    private _responseOverrides: Array<{
        matchBody?: (body: any) => boolean;
        response: any;
    }> = [];

    constructor() {
        this.server = http.createServer((req, res) => {
            // Handle CORS preflight
            if (req.method === "OPTIONS") {
                res.writeHead(200, { "Access-Control-Allow-Origin": "*" });
                res.end();
                return;
            }

            const chunks: Buffer[] = [];
            req.on("data", (chunk: Buffer) => chunks.push(chunk));
            req.on("end", () => {
                const bodyStr = Buffer.concat(chunks).toString("utf-8");
                let body: any;
                try {
                    body = JSON.parse(bodyStr);
                } catch {
                    body = { raw: bodyStr };
                }

                const inputCharCount = this.countInputChars(body);
                const inputTokenEstimate = Math.ceil(inputCharCount / 4);

                this._recordedRequests.push({
                    timestamp: new Date().toISOString(),
                    method: req.method ?? "UNKNOWN",
                    path: req.url ?? "/",
                    body,
                    inputCharCount,
                    inputTokenEstimate,
                });

                // Check for override response
                const override = this._responseOverrides.find((o) =>
                    o.matchBody ? o.matchBody(body) : false,
                );

                const response = override?.response ?? {
                    id: "chatcmpl-mock",
                    object: "chat.completion",
                    created: Math.floor(Date.now() / 1000),
                    model: body?.model ?? "gpt-4o",
                    choices: [
                        {
                            index: 0,
                            message: {
                                role: "assistant",
                                content: "This is a simulated assistant response for testing purposes.",
                            },
                            finish_reason: "stop",
                        },
                    ],
                    usage: {
                        prompt_tokens: inputTokenEstimate,
                        completion_tokens: 50,
                        total_tokens: inputTokenEstimate + 50,
                    },
                };

                const responseBody = JSON.stringify(response);
                res.writeHead(200, {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                });
                res.end(responseBody);
            });
        });
    }

    private countInputChars(body: any): number {
        if (!body || !body.messages) return 0;
        return body.messages.reduce((sum: number, m: any) => {
            const content = typeof m.content === "string" ? m.content : JSON.stringify(m.content ?? "");
            return sum + content.length + 20; // +20 for role markers
        }, 0);
    }

    /**
     * Set a response override for a specific request.
     * Useful for simulating tool call responses during roundtrip tests.
     */
    setResponseOverride(
        matchFn: (body: any) => boolean,
        response: any,
    ): void {
        this._responseOverrides.push({ matchBody: matchFn, response });
    }

    get port(): number {
        return this._port;
    }

    get recordedRequests(): RequestRecord[] {
        return [...this._recordedRequests];
    }

    get lastRequest(): RequestRecord | undefined {
        return this._recordedRequests[this._recordedRequests.length - 1];
    }

    reset(): void {
        this._recordedRequests = [];
        this._responseOverrides = [];
    }

    start(): Promise<void> {
        return new Promise((resolve) => {
            this.server.listen(0, "127.0.0.1", () => {
                const addr = this.server.address();
                if (addr && typeof addr === "object") {
                    this._port = addr.port;
                }
                resolve();
            });
        });
    }

    stop(): Promise<void> {
        return new Promise((resolve) => {
            this.server.close(() => resolve());
        });
    }
}

/**
 * In-memory VectorStore mock for integration tests.
 * Stores indexed texts and returns them by keyword overlap on search.
 */
export class MockVectorStore {
    private chunks: Array<{ text: string; tenantId: string; kind: string }> = [];

    async indexMessage(msg: {
        id: string;
        text: string;
        kind: string;
        tenantId: string;
    }): Promise<void> {
        const segments = this.chunkText(msg.text, 500);
        for (const seg of segments) {
            this.chunks.push({
                text: seg,
                tenantId: msg.tenantId,
                kind: msg.kind,
            });
        }
    }

    async indexMessages(msgs: Array<{
        id: string;
        text: string;
        kind: string;
        tenantId: string;
    }>): Promise<void> {
        for (const msg of msgs) {
            await this.indexMessage(msg);
        }
    }

    async search(
        query: string,
        options?: { limit?: number; tenantId?: string },
    ): Promise<Array<{ score: number; payload: { text: string; tenantId: string; kind: string } }>> {
        const queryTokens = query.toLowerCase().split(/\s+/).filter((t) => t.length > 2);
        const scored = this.chunks
            .filter((c) => !options?.tenantId || c.tenantId === options.tenantId)
            .map((c) => {
                const textLower = c.text.toLowerCase();
                const matchCount = queryTokens.filter((t) => textLower.includes(t)).length;
                // Simulate real embedding similarity: any keyword overlap produces a high base score,
                // plus a boost proportional to overlap ratio. This mimics real semantic search
                // where related content reliably scores 0.6-0.95.
                const score = matchCount > 0
                    ? 0.6 + Math.min(matchCount / Math.max(queryTokens.length, 1), 0.35)
                    : 0;
                return { score, payload: c };
            })
            .filter((r) => r.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, options?.limit ?? 5);

        return scored;
    }

    reset(): void {
        this.chunks = [];
    }

    get chunkCount(): number {
        return this.chunks.length;
    }

    private chunkText(text: string, maxChunkLength: number): string[] {
        const segments: string[] = [];
        const paragraphs = text.split(/\n\n+/);
        for (const para of paragraphs) {
            const trimmed = para.trim();
            if (!trimmed) continue;
            if (trimmed.length <= maxChunkLength) {
                segments.push(trimmed);
            } else {
                let remaining = trimmed;
                while (remaining.length > 0) {
                    segments.push(remaining.slice(0, maxChunkLength));
                    remaining = remaining.slice(maxChunkLength);
                }
            }
        }
        return segments;
    }
}

/**
 * Estimate tokens from a text string.
 */
export function estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
}

/**
 * Count total estimated input tokens from a request body.
 */
export function countPayloadTokens(body: any): number {
    if (!body || !body.messages) return 0;
    return body.messages.reduce((sum: number, m: any) => {
        const content = typeof m.content === "string" ? m.content : JSON.stringify(m.content ?? "");
        return sum + estimateTokens(content) + 5; // +5 for role markers
    }, 0);
}

/**
 * Build a conversation history array from sequential messages.
 */
export function buildConversationHistory(messages: string[]): Array<{ role: string; content: string }> {
    const history: Array<{ role: string; content: string }> = [];
    history.push({ role: "system", content: "You are a helpful assistant." });
    for (let i = 0; i < messages.length; i++) {
        history.push({ role: i % 2 === 0 ? "user" : "assistant", content: messages[i] });
    }
    return history;
}