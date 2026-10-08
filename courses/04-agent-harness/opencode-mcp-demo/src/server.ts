import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import * as z from "zod/v4";

const concepts = {
  host: "Host 是用户直接使用的 AI 应用，负责模型、上下文、权限和 MCP Client。",
  client: "MCP Client 位于 Host 内，负责连接 Server、发现能力并转发调用。",
  server: "MCP Server 对外暴露工具、资源或提示，并执行真正的业务逻辑。",
  "tools/list": "tools/list 用于取得 Server 当前暴露的工具名称、说明和输入 Schema。",
  "tools/call": "tools/call 用于按工具名和参数调用工具，并取得内容或结构化结果。"
} as const;

const conceptNames = Object.keys(concepts) as [keyof typeof concepts, ...(keyof typeof concepts)[]];

function createServer(): McpServer {
  const server = new McpServer({
    name: "opencode-mcp-demo",
    version: "1.0.0"
  });

  server.registerTool(
    "explain_mcp_concept",
    {
      title: "解释 MCP 概念",
      description: "解释一个 MCP 核心概念，适合验证 OpenCode 是否发现并调用了本 Server 的工具。",
      inputSchema: z.object({
        concept: z.enum(conceptNames).describe("要解释的 MCP 概念")
      }),
      outputSchema: z.object({
        concept: z.string(),
        explanation: z.string()
      })
    },
    async ({ concept }) => {
      const output = {
        concept,
        explanation: concepts[concept]
      };

      return {
        content: [{ type: "text", text: `${concept}: ${output.explanation}` }],
        structuredContent: output
      };
    }
  );

  server.registerTool(
    "sum_numbers",
    {
      title: "数字求和",
      description: "计算一组有限数字的总和，用于演示 MCP 的参数 Schema 和结构化结果。",
      inputSchema: z.object({
        numbers: z.array(z.number()).min(1).max(20).describe("1 到 20 个待求和数字")
      }),
      outputSchema: z.object({
        count: z.number().int(),
        sum: z.number()
      })
    },
    async ({ numbers }) => {
      const output = {
        count: numbers.length,
        sum: numbers.reduce((total, value) => total + value, 0)
      };

      return {
        content: [
          {
            type: "text",
            text: `${output.count} 个数字的总和是 ${output.sum}`
          }
        ],
        structuredContent: output
      };
    }
  );

  return server;
}

void serveStdio(createServer);

// stdout 是 MCP 协议通道，诊断信息必须写入 stderr。
console.error("opencode-mcp-demo started over stdio");
