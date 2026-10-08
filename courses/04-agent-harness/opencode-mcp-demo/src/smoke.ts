import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const client = new Client({
  name: "opencode-mcp-demo-smoke",
  version: "1.0.0"
});

const transport = new StdioClientTransport({
  command: "npm",
  args: ["run", "start", "--silent"]
});

try {
  await client.connect(transport);

  const { tools } = await client.listTools();
  console.log("tools:", tools.map((tool) => tool.name).join(", "));

  const explanation = await client.callTool({
    name: "explain_mcp_concept",
    arguments: { concept: "tools/list" }
  });
  console.log("explain_mcp_concept:", JSON.stringify(explanation.structuredContent));

  const sum = await client.callTool({
    name: "sum_numbers",
    arguments: { numbers: [12, 30.5, 7.5] }
  });
  console.log("sum_numbers:", JSON.stringify(sum.structuredContent));
} finally {
  await client.close();
}
