/**
 * Entity Extractor — uses the LLM to extract structured entities and
 * relationships from conversation text.
 *
 * Runs as a fire-and-forget background step after each chat response.
 * Gracefully degrades: on failure, returns null and the caller logs
 * the degradation but does not block the response path.
 */
import OpenAI from "openai";
import type { GatewayConfig } from "../config.js";
import type { ExtractionResult } from "../types.js";

const EXTRACTION_PROMPT = `You are an entity and relationship extractor for a software architecture knowledge graph.

Analyze the conversation text below and extract:

1. ENTITIES: Named things that represent a distinct concept in the conversation.
   Entity types: "project", "api", "service", "database", "technology", "decision", "file", "module", "tool", "person", "pattern", "config"

   Each entity must have:
   - type: one of the listed types
   - name: the canonical name or identifier
   - properties: key-value pairs of relevant attributes (e.g. {"language":"TypeScript", "version":"2.0"})

2. RELATIONSHIPS: Directed connections between entities.
   Relationship types: "uses", "depends_on", "implements", "extends", "references", "applies_to", "mentions", "installed", "configured", "deployed_on"

   Each relationship must have:
   - from: the name of the source entity
   - to: the name of the target entity
   - relation: one of the listed relationship types
   - properties: key-value pairs (e.g. {"context": "production deployment"})

Rules:
- Only extract entities that are explicitly mentioned or clearly implied by the text.
- Deduplicate by name: if the same entity name appears multiple times, include it once.
- Skip generic terms like "the app", "the database", "the project" unless given a specific name.
- Properties should only contain factual attributes stated in the text.
- If no entities are found, return {"entities": [], "relationships": []}.

Output strictly as JSON with no other text:
{
  "entities": [
    {"type": "...", "name": "...", "properties": {}}
  ],
  "relationships": [
    {"from": "...", "to": "...", "relation": "...", "properties": {}}
  ]
}`;

/**
 * Extracts entities and relationships from conversation text using the LLM.
 */
export class EntityExtractor {
	private client: OpenAI;
	private model: string;

	constructor(config: GatewayConfig) {
		this.client = new OpenAI({
			apiKey: config.openaiApiKey,
			baseURL: config.openaiBaseUrl,
		});
		this.model = config.openaiDefaultModel;
	}

	/**
	 * Extract structured entities and relationships from text.
	 * Returns null on failure (parse error, API error, empty response).
	 */
	async extract(text: string): Promise<ExtractionResult | null> {
		// Skip very short text — unlikely to contain meaningful entities
		if (!text || text.length < 20) return null;

		try {
			const response = await this.client.chat.completions.create({
				model: this.model,
				messages: [
					{ role: "system", content: EXTRACTION_PROMPT },
					{ role: "user", content: text },
				],
				response_format: { type: "json_object" },
				max_tokens: 1000,
				temperature: 0.1,
			});

			const content = response.choices[0]?.message?.content;
			if (!content) return null;

			const parsed = JSON.parse(content) as ExtractionResult;

			// Validate shape
			if (!Array.isArray(parsed.entities) || !Array.isArray(parsed.relationships)) {
				return null;
			}

			return parsed;
		} catch (err) {
			console.error("Entity extraction error:", (err as Error).message);
			return null;
		}
	}
}