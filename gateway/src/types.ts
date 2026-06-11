/**
 * Internal normalized types for the gateway — see docs/universal-rag-gateway.md.
 *
 * The adapter layer maps incoming client-format requests (OpenAI-compatible,
 * Anthropic-compatible, MCP, REST) into GatewayRequest.
 */

// ─── Messages ────────────────────────────────────────────────────────

export type NormalizedRole = "system" | "user" | "assistant" | "tool";

export interface NormalizedMessage {
	role: NormalizedRole;
	content: string | NormalizedContentPart[];
	name?: string;
	tool_call_id?: string;
	tool_calls?: NormalizedToolCall[];
}

export interface NormalizedContentPart {
	type: "text" | "image_url";
	text?: string;
	image_url?: { url: string; detail?: "low" | "high" | "auto" };
}

export interface NormalizedToolCall {
	id: string;
	type: "function";
	function: {
		name: string;
		arguments: string;
	};
}

// ─── Tools ───────────────────────────────────────────────────────────

export interface NormalizedTool {
	type: "function";
	function: {
		name: string;
		description?: string;
		parameters: Record<string, unknown>;
	};
}

export type ToolChoice =
	| "none"
	| "auto"
	| "required"
	| { type: "function"; function: { name: string } };

// ─── Context Budget (from Context Budget Planner) ────────────────────

export interface ContextBudget {
	intent: "coding-edit" | "debug" | "design" | "qa";
	maxContextTokens: number;
	staticPrefixTokens: number;
	ragTokens: number;
	recentHistoryTokens: number;
	toolSchemaTokens: number;
	reserveTokens: number;
}

// ─── Gateway Request ─────────────────────────────────────────────────

export interface GatewayRequest {
	tenantId: string;
	projectId?: string;
	client: "cursor" | "vscode" | "codex" | "claude-code" | "script" | "unknown";
	protocol: "openai-compatible" | "anthropic-compatible" | "mcp" | "rest";
	model: string;
	messages: NormalizedMessage[];
	tools?: NormalizedTool[];
	toolChoice?: ToolChoice;
	stream: boolean;
	maxTokens?: number;
	temperature?: number;
	budget?: ContextBudget;
	metadata: Record<string, unknown>;
}

// ─── Observability ───────────────────────────────────────────────────

export interface RequestTelemetry {
	requestId: string;
	tenantId: string;
	client: string;
	model: string;
	messageCount: number;
	toolCount: number;
	injectedTools: number;
	toolCallsExecuted: number;
	retrievalHits: number;
	stream: boolean;
	providerLatencyMs: number;
	fallbackReason?: string;
	skippedComponents: DegradedComponent[];
	budget?: {
		intent: string;
		maxContextTokens: number;
		ragTokens: number;
		reserveTokens: number;
	};
	createdAt: Date;
}

export type DegradedComponent =
	| "qdrant"
	| "postgres"
	| "tool-registry"
	| "embedding"
	| "provider"
	| "memory-retrieval"
	| "tool-execution"
	| "entity-extraction";

export interface GatewayFallback {
	degraded: boolean;
	reason?: string;
	skippedComponents: DegradedComponent[];
}

// ─── Graph Entity/Relation types (GraphRAG) ─────────────────────────

export interface GraphEntity {
	id: string;
	tenantId: string;
	projectId?: string;
	type: string;
	name: string;
	properties: Record<string, unknown>;
	createdAt: Date;
}

export interface GraphRelation {
	id: string;
	tenantId: string;
	projectId?: string;
	fromEntityId: string;
	toEntityId: string;
	relation: string;
	properties: Record<string, unknown>;
	createdAt: Date;
}

/**
 * Result of a graph search: matched entity plus its 1-2 hop neighborhood.
 */
export interface GraphSearchResult {
	entity: GraphEntity;
	relations: Array<{
		relation: GraphRelation;
		fromEntity: GraphEntity;
		toEntity: GraphEntity;
	}>;
}

/**
 * Structured output from the LLM extraction prompt.
 */
export interface ExtractionResult {
	entities: Array<{
		type: string;
		name: string;
		properties: Record<string, unknown>;
	}>;
	relationships: Array<{
		from: string;
		to: string;
		relation: string;
		properties: Record<string, unknown>;
	}>;
}