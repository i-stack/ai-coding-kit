#!/usr/bin/env node
/**
 * CLI for plan-reviews knowledge base.
 *
 * Usage:
 *   npx tsx src/cli.ts sync           # Sync .plan-reviews/ to KB
 *   npx tsx src/cli.ts search "query"  # Search the KB
 *   npx tsx src/cli.ts stats           # Show KB statistics
 *   npx tsx src/cli.ts reset           # Full reset and re-sync
 */

import { PlanReviewsKB } from "./index.js";
import { generateKnowledgeGraph } from "./visualize.js";

const args = process.argv.slice(2);
const command = args[0] ?? "help";
const query = args.slice(1).join(" ") || args[0] || "";

// Parse --output flag
function parseOutputFlag(): string | undefined {
	const idx = args.indexOf("--output");
	return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : undefined;
}



async function main() {
	const kb = await PlanReviewsKB.init();

	switch (command) {
		case "sync": {
			console.log("Syncing .plan-reviews/ to knowledge base...");
			const stats = await kb.sync();
			console.log(
				`Done: ${stats.added} added, ${stats.modified} modified, ` +
				`${stats.removed} removed, ${stats.skipped} skipped`,
			);
			if (stats.errors.length > 0) {
				console.log(`\nErrors (${stats.errors.length}):`);
				for (const err of stats.errors) console.log(`  - ${err}`);
			}
			break;
		}

		case "search": {
			if (!query || query === "search") {
				console.log("Usage: cli.ts search <query>");
				break;
			}
			console.log(`Searching: "${query}"\n`);
			const results = await kb.search({ query });
			console.log(kb.formatResults(results));
			break;
		}

		case "recall": {
			if (!query || query === "recall") {
				console.log("Usage: cli.ts recall <query>");
				break;
			}
			console.log(`Recalling context for: "${query}"\n`);
			const block = await kb.recall(query);
			if (!block) {
				console.log("(no relevant prior knowledge found)");
			} else {
				console.log(block);
			}
			break;
		}

		case "merge": {
			console.log("Running memory-metabolism merge (de-dup cross-plan knowledge)...");
			if (!kb.stats.chunks) {
				console.log("No chunks indexed yet. Run `sync` first.");
				break;
			}
			const points = await kb.merge();
			if (points.length === 0) {
				console.log("No duplicate knowledge points found (or embedding API not configured).");
			} else {
				console.log(`Merged ${points.length} knowledge point(s):`);
				for (const p of points) {
					console.log(`  - ${p.title} [minSim=${p.minSimilarity.toFixed(2)}]`);
				}
				console.log("Written to .plan-reviews/.kb-merged.json and .plan-reviews/MERGED-KNOWLEDGE.md");
			}
			break;
		}

		case "stats": {
			const s = kb.stats;
			console.log("Knowledge Base Statistics:");
			console.log(`  Plans:     ${s.plans}`);
			console.log(`  Entities:  ${s.entities}`);
			console.log(`  Relations: ${s.relations}`);
			console.log(`  Chunks:    ${s.chunks}`);
			break;
		}

		case "reset": {
			console.log("Resetting knowledge base...");
			const stats = await kb.reset();
			console.log(
				`Done: ${stats.added} added, ${stats.modified} modified, ` +
				`${stats.removed} removed, ${stats.skipped} skipped`,
			);
			break;
		}

		case "visualize": {
			const output = parseOutputFlag();
			const outputPath = generateKnowledgeGraph({ output });
			console.log(`Knowledge graph generated: ${outputPath}`);
			console.log("Open it in your browser to explore.");
			break;
		}

		default:
			console.log("plan-reviews knowledge base CLI");
			console.log("");
			console.log("Commands:");
			console.log("  sync             Sync .plan-reviews/ to knowledge base");
			console.log("  search <query>   Search the knowledge base");
			console.log("  recall <query>   Search and print injection-ready context block");
			console.log("  merge            De-dup / consolidate cross-plan knowledge (metabolism)");
			console.log("  stats            Show KB statistics");
			console.log("  reset            Full reset and re-sync");
			console.log("  visualize        Generate interactive knowledge graph HTML");
			console.log("    --output <path>  Custom output path (default: .plan-reviews/knowledge-graph.html)");

			console.log("");
			console.log("Environment:");
			console.log("  EMBEDDING_API_KEY   Embedding API key (optional)");
			console.log("  EMBEDDING_BASE_URL  Embedding API base URL");
			console.log("  EMBEDDING_MODEL     Embedding model name");
			break;
	}

	kb.close();
}

main().catch((err) => {
	console.error("Error:", err.message);
	process.exit(1);
});
