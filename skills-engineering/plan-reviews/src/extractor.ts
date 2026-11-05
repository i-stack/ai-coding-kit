/**
 * Entity & Relationship extractor for plan artifacts.
 *
 * Unlike rag-gateway's EntityExtractor (which calls an LLM with a
 * structured prompt), this extractor works on the pre-parsed
 * PlanSections from parser.ts. It applies heuristics to extract:
 *
 *   - Technologies/Services from Approach and Decisions sections
 *   - Decision entities from the Decisions section
 *   - Risk entities from the Risks section
 *   - Constraint entities from the Constraints section
 *   - Goal, OutOfScope entities
 *
 * Relationships are constructed between these entities based on
 * section co-occurrence and explicit mentions. Review-log flaws are
 * not extracted; they remain searchable as review_log chunks.
 *
 * Zero LLM calls. Zero external dependencies beyond node: crypto.
 */

import crypto from "node:crypto";
import type {
	PlanArtifact,
	PlanEntity,
	PlanRelation,
	PlanEntityType,
	PlanRelationType,
} from "./types.js";

// ─── Technology/Service detection patterns ───────────────────────────

/**
 * Known technologies and their common names/aliases.
 * Extracted from the Approach and Decisions sections.
 */
const TECH_PATTERNS: Array<{ regex: RegExp; name: string; type: PlanEntityType }> = [
	{ regex: /\bRedis\b/i, name: "Redis", type: "service" },
	{ regex: /\bPostgreSQL\b/i, name: "PostgreSQL", type: "service" },
	{ regex: /\bMySQL\b/i, name: "MySQL", type: "service" },
	{ regex: /\bSQLite\b/i, name: "SQLite", type: "service" },
	{ regex: /\bMongoDB\b/i, name: "MongoDB", type: "service" },
	{ regex: /\bKafka\b/i, name: "Kafka", type: "service" },
	{ regex: /\bRabbitMQ\b/i, name: "RabbitMQ", type: "service" },
	{ regex: /\bElasticsearch\b/i, name: "Elasticsearch", type: "service" },
	{ regex: /\bQdrant\b/i, name: "Qdrant", type: "service" },
	{ regex: /\bDocker\b/i, name: "Docker", type: "technology" },
	{ regex: /\bKubernetes\b/i, name: "Kubernetes", type: "technology" },
	{ regex: /\bGraphQL\b/i, name: "GraphQL", type: "technology" },
	{ regex: /\bREST\b/i, name: "REST", type: "technology" },
	{ regex: /\bWebSocket\b/i, name: "WebSocket", type: "technology" },
	{ regex: /\bTypeScript\b/i, name: "TypeScript", type: "technology" },
	{ regex: /\bJavaScript\b/i, name: "JavaScript", type: "technology" },
	{ regex: /\bPython\b/i, name: "Python", type: "technology" },
	{ regex: /\bRust\b/i, name: "Rust", type: "technology" },
	{ regex: /\bGo(lang)?\b/i, name: "Go", type: "technology" },
	{ regex: /\bSwift\b/i, name: "Swift", type: "technology" },
	{ regex: /\bKotlin\b/i, name: "Kotlin", type: "technology" },
	{ regex: /\bReact\b/i, name: "React", type: "technology" },
	{ regex: /\bVue(\.js)?\b/i, name: "Vue.js", type: "technology" },
	{ regex: /\bAngular\b/i, name: "Angular", type: "technology" },
	{ regex: /\bNext\.js\b/i, name: "Next.js", type: "technology" },
	{ regex: /\bNode\.js\b/i, name: "Node.js", type: "technology" },
	{ regex: /\bFastify\b/i, name: "Fastify", type: "technology" },
	{ regex: /\bExpress\b/i, name: "Express", type: "technology" },
	{ regex: /\bLua\b/i, name: "Lua", type: "technology" },
	{ regex: /\bHMAC\b/i, name: "HMAC", type: "technology" },
	{ regex: /\bCAPTCHA\b/i, name: "CAPTCHA", type: "technology" },
	{ regex: /\bMFA\b/i, name: "MFA", type: "technology" },
	{ regex: /\bJWT\b/i, name: "JWT", type: "technology" },
	{ regex: /\bOAuth2?\b/i, name: "OAuth", type: "technology" },
	{ regex: /\bgRPC\b/i, name: "gRPC", type: "technology" },
	{ regex: /\bPrometheus\b/i, name: "Prometheus", type: "technology" },
	{ regex: /\bGrafana\b/i, name: "Grafana", type: "technology" },
	{ regex: /\bNAT\b/i, name: "NAT", type: "technology" },
	{ regex: /\bIPv4\b|\bIPv6\b/i, name: "IP Networking", type: "technology" },
];

// ─── Decision extraction patterns ────────────────────────────────────

/**
 * Extract individual decision items from the Key Decisions section.
 * Format is typically:
 *   - <decision title>: <explanation>
 * or numbered items.
 */
const DECISION_PATTERN = /^[-*]\s+(.+?)(?::\s|;\s|。|\.\s|$)/gm;

// ─── Risk extraction patterns ────────────────────────────────────────

/**
 * Extract individual risk items from the Risks section.
 */
const RISK_PATTERN = /^[-*]\s+(.+?)(?::\s|;\s|。|\.\s|$)/gm;

// ─── Constraint extraction ───────────────────────────────────────────

/**
 * Extract individual constraint items from the Constraints section.
 */
const CONSTRAINT_PATTERN = /^[-*]\s+(.+?)(?::\s|;\s|。|\.\s|$)/gm;

// ─── Out-of-Scope extraction ─────────────────────────────────────────

const OUT_OF_SCOPE_PATTERN = /^[-*]\s+(.+?)(?::\s|;\s|。|\.\s|$)/gm;

// ─── Main extractor ──────────────────────────────────────────────────

export interface ExtractionOutput {
	entities: PlanEntity[];
	relations: PlanRelation[];
}

/**
 * Extract entities and relationships from a parsed PlanArtifact.
 */
export function extractFromArtifact(artifact: PlanArtifact): ExtractionOutput {
	const entities: PlanEntity[] = [];
	const relations: PlanRelation[] = [];
	const entityMap = new Map<string, PlanEntity>();
	const planId = artifact.id;
	const now = new Date().toISOString();

	function addEntity(
		type: PlanEntityType,
		name: string,
		description: string,
		properties: Record<string, string> = {},
	): PlanEntity {
		const key = `${type}:${name}:${planId}`;
		// Deduplicate within this plan
		const existing = entityMap.get(key);
		if (existing) return existing;

		const entity: PlanEntity = {
			id: crypto.randomUUID(),
			planId,
			type,
			name,
			description: description.slice(0, 500), // Cap description length
			properties,
			createdAt: now,
		};
		entities.push(entity);
		entityMap.set(key, entity);
		return entity;
	}

	function addRelation(
		fromEntity: PlanEntity,
		toEntity: PlanEntity,
		relation: PlanRelationType,
		properties: Record<string, string> = {},
	): void {
		// Avoid duplicate relations
		const key = `${fromEntity.id}:${toEntity.id}:${relation}`;
		if (relations.some(r => `${r.fromEntityId}:${r.toEntityId}:${r.relation}` === key)) return;

		relations.push({
			id: crypto.randomUUID(),
			planId,
			fromEntityId: fromEntity.id,
			toEntityId: toEntity.id,
			relation,
			properties,
			createdAt: now,
		});
	}

	// ── 1. Goal entity ──────────────────────────────────────────────
	const goalText = artifact.sections.goal;
	if (goalText) {
		addEntity("goal", artifact.sections.title, goalText);
	}

	// ── 2. Constraint entities ──────────────────────────────────────
	const constraintsText = artifact.sections.constraints;
	if (constraintsText) {
		const items = extractBulletItems(constraintsText, CONSTRAINT_PATTERN);
		if (items.length === 0) {
			// Whole section as one constraint if no bullets
			addEntity("constraint", `${artifact.id}-constraint`, constraintsText);
		} else {
			for (const item of items) {
				addEntity("constraint", limitName(item), item);
			}
		}
	}

	// ── 3. Decision entities ────────────────────────────────────────
	const decisionsText = artifact.sections.decisions;
	if (decisionsText) {
		const items = extractBulletItems(decisionsText, DECISION_PATTERN);
		if (items.length === 0) {
			addEntity("decision", `${artifact.id}-decision`, decisionsText);
		} else {
			for (const item of items) {
				addEntity("decision", limitName(item), item);
			}
		}
	}

	// ── 4. Risk entities ────────────────────────────────────────────
	const risksText = artifact.sections.risks;
	if (risksText) {
		const items = extractBulletItems(risksText, RISK_PATTERN);
		if (items.length === 0) {
			addEntity("risk", `${artifact.id}-risk`, risksText);
		} else {
			for (const item of items) {
				addEntity("risk", limitName(item), item);
			}
		}
	}

	// ── 5. Out-of-Scope entities ────────────────────────────────────
	const oosText = artifact.sections.outOfScope;
	if (oosText) {
		const items = extractBulletItems(oosText, OUT_OF_SCOPE_PATTERN);
		for (const item of items) {
			addEntity("out_of_scope", limitName(item), item);
		}
	}

	// ── 6. Technology/Service entities ──────────────────────────────
	const techTexts = [artifact.sections.approach, artifact.sections.decisions, artifact.diffText ?? ""].join("\n");
	const seenTech = new Set<string>();
	for (const pattern of TECH_PATTERNS) {
		pattern.regex.lastIndex = 0;
		if (pattern.regex.test(techTexts) && !seenTech.has(pattern.name)) {
			addEntity(pattern.type, pattern.name, `Mentioned in ${artifact.id}`);
			seenTech.add(pattern.name);
		}
	}

	// ── 7. Build relationships ──────────────────────────────────────
	buildRelationships(entities, relations, planId, now);

	return { entities, relations };
}

// ─── Helpers ─────────────────────────────────────────────────────────

function extractBulletItems(text: string, pattern: RegExp): string[] {
	pattern.lastIndex = 0;
	const items: string[] = [];
	let match;
	while ((match = pattern.exec(text)) !== null) {
		items.push(match[1].trim());
	}
	return items;
}

/**
 * Create a short name from the first ~80 chars of a text.
 */
function limitName(text: string): string {
	return text.length > 80 ? text.slice(0, 77) + "..." : text;
}

/**
 * Build implicit relationships between entities within the same plan.
 *
 * Heuristics:
 *   - Each decision "uses" technologies mentioned in its text
 *   - Each decision "addresses" the goal
 *   - Each risk "addresses" the goal (co-occurrence; not a threaten edge)
 *   - Each constraint "constrains" each decision
 */
function buildRelationships(
	entities: PlanEntity[],
	relations: PlanRelation[],
	planId: string,
	now: string,
): void {
	const byType = new Map<PlanEntityType, PlanEntity[]>();
	for (const e of entities) {
		const list = byType.get(e.type) ?? [];
		list.push(e);
		byType.set(e.type, list);
	}

	const goals = byType.get("goal") ?? [];
	const decisions = byType.get("decision") ?? [];
	const risks = byType.get("risk") ?? [];
	const techs = [...(byType.get("technology") ?? []), ...(byType.get("service") ?? [])];
	const constraints = byType.get("constraint") ?? [];

	function addRel(
		from: PlanEntity,
		to: PlanEntity,
		relation: PlanRelationType,
	): void {
		const key = `${from.id}:${to.id}:${relation}`;
		if (relations.some(r => `${r.fromEntityId}:${r.toEntityId}:${r.relation}` === key)) return;
		relations.push({
			id: crypto.randomUUID(),
			planId,
			fromEntityId: from.id,
			toEntityId: to.id,
			relation,
			properties: {},
			createdAt: now,
		});
	}

	// Decision → Technology (if tech appears in decision text)
	for (const dec of decisions) {
		for (const tech of techs) {
			if (dec.description.toLowerCase().includes(tech.name.toLowerCase())) {
				addRel(dec, tech, "uses");
			}
		}
	}

	// Goal ← Decision (decisions address the goal)
	for (const goal of goals) {
		for (const dec of decisions) {
			addRel(dec, goal, "addresses");
		}
	}

	// Risk → Goal (risks threaten the goal)
	for (const goal of goals) {
		for (const risk of risks) {
			addRel(risk, goal, "addresses");
		}
	}

	// Constraint → Decision (constraints constrain decisions)
	for (const con of constraints) {
		for (const dec of decisions) {
			addRel(con, dec, "constrains");
		}
	}

	// Decision → Technology (constrains tech choices)
	for (const dec of decisions) {
		for (const tech of techs) {
			if (dec.description.toLowerCase().includes(tech.name.toLowerCase())) {
				addRel(dec, tech, "uses");
			}
		}
	}
}

/**
 * Extract all text from a plan artifact suitable for embedding.
 * Returns chunks keyed by section name.
 */
export function planToChunks(artifact: PlanArtifact): Array<{
	section: string;
	text: string;
}> {
	const chunks: Array<{ section: string; text: string }> = [];

	if (artifact.sections.goal) {
		chunks.push({ section: "goal", text: artifact.sections.goal });
	}
	if (artifact.sections.approach) {
		chunks.push({ section: "approach", text: artifact.sections.approach });
	}
	if (artifact.sections.decisions) {
		chunks.push({ section: "decisions", text: artifact.sections.decisions });
	}
	if (artifact.sections.constraints) {
		chunks.push({ section: "constraints", text: artifact.sections.constraints });
	}
	if (artifact.sections.risks) {
		chunks.push({ section: "risks", text: artifact.sections.risks });
	}
	if (artifact.sections.validation) {
		chunks.push({ section: "validation", text: artifact.sections.validation });
	}
	if (artifact.architectureAnalysis) {
		chunks.push({ section: "architecture_analysis", text: artifact.architectureAnalysis });
	}
	// Code-review artifacts: index the raw diff + review log as searchable chunks.
	if (artifact.diffText) {
		chunks.push({ section: "diff", text: artifact.diffText });
	}
	if (artifact.reviewLogText) {
		chunks.push({ section: "review_log", text: artifact.reviewLogText });
	}
	if (artifact.responseText) {
		chunks.push({ section: "response", text: artifact.responseText });
	}
	if (artifact.summaryText) {
		chunks.push({ section: "summary", text: artifact.summaryText });
	}
	// Full plan text as one combined chunk for holistic search
	const fullText = [
		`Title: ${artifact.sections.title}`,
		`Goal: ${artifact.sections.goal}`,
		`Approach: ${artifact.sections.approach}`,
		`Decisions: ${artifact.sections.decisions}`,
		artifact.architectureAnalysis ? `Architecture analysis: ${artifact.architectureAnalysis}` : "",
		artifact.diffText ? `Diff:\n${artifact.diffText}` : "",
		artifact.reviewLogText ? `Review log:\n${artifact.reviewLogText}` : "",
		artifact.responseText ? `Response:\n${artifact.responseText}` : "",
		artifact.summaryText ? `Summary:\n${artifact.summaryText}` : "",
	].join("\n");
	chunks.push({ section: "full", text: fullText });

	return chunks;
}
