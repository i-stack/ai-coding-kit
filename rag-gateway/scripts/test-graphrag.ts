/**
 * MCP GraphRAG test script — connects to the running gateway via MCP SSE,
 * calls search_memory, and checks whether GraphRAG entity search results appear.
 *
 * Run: npx tsx scripts/test-graphrag.ts
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const GATEWAY_URL = "http://localhost:3000";

async function main() {
  console.log(`\n🔌 Connecting to MCP gateway at ${GATEWAY_URL}/mcp/sse...`);

  const transport = new SSEClientTransport(new URL(`${GATEWAY_URL}/mcp/sse`));
  const client = new Client(
    { name: "graphrag-test", version: "0.1.0" },
    { capabilities: {} },
  );

  await client.connect(transport);
  console.log("✅ Connected!");

  // Step 1: list tools
  const toolsResult = await client.listTools();
  const toolNames = toolsResult.tools.map((t: { name: string }) => t.name);
  console.log(`📋 Available tools: ${toolNames.join(", ")}`);

  if (!toolNames.includes("search_memory")) {
    console.error("❌ search_memory tool not found!");
    await client.close();
    process.exit(1);
  }

  // Step 2: Test search_memory with various queries targeting existing graph data
  const queries = [
    { label: "entity search: MyApp (should hit entity graph)", query: "MyApp" },
    { label: "entity search: PostgreSQL (should hit entity graph)", query: "PostgreSQL" },
    { label: "entity search: Redis (should hit entity graph)", query: "Redis" },
    { label: "entity search: AuthService (should hit entity graph)", query: "AuthService" },
    { label: "entity search: Kafka+EC2 (should hit entity graph)", query: "Kafka EC2 LogService" },
    { label: "semantic search: semantic memory about RAG gateway", query: "RAG gateway MCP server" },
  ];

  for (const q of queries) {
    console.log(`\n🔍 [${q.label}]`);
    console.log(`   Query: "${q.query}"`);

    const result = await client.callTool({
      name: "search_memory",
      arguments: {
        query: q.query,
        limit: 5,
        tenant_id: "default",
      },
    });

    const content = result.content as Array<{ type: string; text: string }>;
    const text = content.map((c: { text: string }) => c.text).join("\n");
    console.log(`   Result:\n${text}`);

    // Check if GraphRAG content is present
    if (text.includes("Entity Graph")) {
      console.log("   ✅ GraphRAG entity search RETURNED results!");
    } else {
      console.log("   ⚠️  No GraphRAG results (entity graph may not contain this)");
    }
  }

  await client.close();
  console.log("\n✅ Test complete.");
}

main().catch((err) => {
  console.error("❌ Test failed:", err);
  process.exit(1);
});
