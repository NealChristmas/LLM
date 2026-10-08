/**
 * s01_agent_loop.ts - The Agent Loop
 *
 * The entire secret of an AI coding agent in one pattern:
 *
 *   while (true) {
 *     const response = await LLM(messages, tools);
 *     if (response contains no tool_use) break;
 *     execute tools;
 *     append results;
 *   }
 *
 *   +----------+      +-------+      +---------+
 *   |   User   | ---> |  LLM  | ---> |  Tool   |
 *   |  prompt  |      |       |      | execute |
 *   +----------+      +---+---+      +----+----+
 *                         ^               |
 *                         |   tool_result |
 *                         +---------------+
 *                         (loop continues)
 *
 * This is the core loop: feed tool results back to the model
 * until the model decides to stop. Later chapters add policy,
 * hooks, and lifecycle controls around it.
 */

import Anthropic from "@anthropic-ai/sdk";
import type {
  ContentBlockParam,
  MessageParam,
  Tool,
  ToolResultBlockParam,
  ToolUseBlock,
} from "@anthropic-ai/sdk/resources/messages/messages";
import { execSync } from "node:child_process";
import { createInterface } from "node:readline/promises";
import { pathToFileURL } from "node:url";
import { config as load_dotenv } from "dotenv";

load_dotenv({ override: true, quiet: true });

if (process.env.ANTHROPIC_BASE_URL) {
  delete process.env.ANTHROPIC_AUTH_TOKEN;
}

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
  baseURL: process.env.ANTHROPIC_BASE_URL,
});
const MODEL = process.env.MODEL_ID as string;

if (!MODEL) {
  throw new Error("Missing MODEL_ID in .env");
}

const SYSTEM = `You are a coding agent at ${process.cwd()}. Use bash to solve tasks. Act, don't explain.`;

// -- Tool definition: just bash --
const TOOLS: Tool[] = [
  {
    name: "bash",
    description: "Run a shell command.",
    input_schema: {
      type: "object",
      properties: { command: { type: "string" } },
      required: ["command"],
    },
  },
];

// -- Tool execution --
export function run_bash(command: string): string {
  const dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"];
  if (dangerous.some((d) => command.includes(d))) {
    return "Error: Dangerous command blocked";
  }
  try {
    const out = execSync(command, {
      cwd: process.cwd(),
      encoding: "utf8",
      timeout: 120_000,
      maxBuffer: 10 * 1024 * 1024,
      windowsHide: true,
    }).trim();
    return out ? out.slice(0, 50_000) : "(no output)";
  } catch (error) {
    const e = error as Error & {
      code?: string;
      stdout?: string | Buffer;
      stderr?: string | Buffer;
    };
    if (e.code === "ETIMEDOUT") {
      return "Error: Timeout (120s)";
    }
    const out = `${e.stdout?.toString() ?? ""}${e.stderr?.toString() ?? ""}`.trim();
    return `Error: ${out || e.message}`;
  }
}

// -- The core pattern: a while loop that calls tools until the model stops --
export async function agent_loop(messages: MessageParam[]): Promise<void> {
  while (true) {
    const response = await client.messages.create({
      model: MODEL,
      system: SYSTEM,
      messages,
      tools: TOOLS,
      max_tokens: 8_000,
    });

    // Append assistant turn
    messages.push({
      role: "assistant",
      content: response.content as ContentBlockParam[],
    });

    // If the model didn't call a tool, we're done
    const tool_calls = response.content.filter(
      (block): block is ToolUseBlock => block.type === "tool_use",
    );
    if (tool_calls.length === 0) {
      return;
    }

    // Execute each tool call, collect results
    const results: ToolResultBlockParam[] = [];
    for (const block of tool_calls) {
      console.log(
        `\u001b[33m$ ${(block.input as { command: string }).command}\u001b[0m`,
      );
      const output = run_bash((block.input as { command: string }).command);
      console.log(output.slice(0, 200));
      results.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: output,
      });
    }

    // Feed tool results back, loop continues
    messages.push({ role: "user", content: results });
  }
}

// -- Entry point --
const entry_url = process.argv[1] ? pathToFileURL(process.argv[1]).href : undefined;
if (entry_url === import.meta.url) {
  console.log("s01: Agent Loop");
  console.log("Enter a question, press Enter to send. Type q to quit.\n");

  const terminal = createInterface({ input: process.stdin, output: process.stdout });
  const history: MessageParam[] = [];
  while (true) {
    let query: string;
    try {
      query = await terminal.question("\u001b[36ms01 >> \u001b[0m");
    } catch {
      break;
    }
    if (["q", "exit", ""].includes(query.trim().toLowerCase())) {
      break;
    }
    history.push({ role: "user", content: query });
    await agent_loop(history);
    // Print the model's final text response
    const response_content = history.at(-1)?.content;
    if (Array.isArray(response_content)) {
      for (const block of response_content) {
        if (block.type === "text") {
          console.log(block.text);
        }
      }
    }
    console.log();
  }
  terminal.close();
}
