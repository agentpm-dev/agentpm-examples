import "dotenv/config";

import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import OpenAI from "openai";
import { load, type JsonValue, type ToolMeta } from "@agentpm/sdk";

type AgentToolSpec = string | { name: string; version?: string };

type AgentManifest = {
  name: string;
  tools: AgentToolSpec[];
};

type LoadedTool = {
  spec: string;
  meta: ToolMeta;
  invoke: (input: JsonValue) => Promise<JsonValue>;
};

type ConversationMessage =
  | { role: "system"; content: string }
  | { role: "user"; content: string }
  | { role: "assistant"; content: string };

const MAX_TOOL_RESULT_CHARS = 8000;
const MAX_LOG_RESULT_CHARS = 1800;
const MODEL = process.env.OPENAI_MODEL || "gpt-4o-mini";

function collectStringEnv(): Record<string, string> {
  return Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => typeof entry[1] === "string"),
  );
}

function specFromEntry(entry: AgentToolSpec): string {
  if (typeof entry === "string") return entry;
  if (!entry.version) return entry.name;
  return `${entry.name}@${entry.version}`;
}

function formatToolParameters(meta: ToolMeta) {
  const parameters = (meta.inputs && typeof meta.inputs === "object" ? meta.inputs : { type: "object", properties: {} }) as Record<string, unknown>;
  return {
    type: "function" as const,
    function: {
      name: meta.name,
      description: meta.description || `AgentPM tool ${meta.name}`,
      parameters,
    },
  };
}

function stringifyForLog(value: unknown, maxChars = MAX_LOG_RESULT_CHARS): string {
  const raw = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return raw.length <= maxChars ? raw : `${raw.slice(0, maxChars)}\n...<truncated>`;
}

function stringifyForModel(value: unknown, maxChars = MAX_TOOL_RESULT_CHARS): string {
  const raw = typeof value === "string" ? value : JSON.stringify(value);
  if (raw.length <= maxChars) return raw;
  return JSON.stringify({
    truncated: true,
    result_preview: raw.slice(0, maxChars),
  });
}

function printBanner(manifestName: string, tools: LoadedTool[]) {
  console.log(`\nResearch Console: ${manifestName}`);
  console.log(`Model: ${MODEL}`);
  console.log(`Loaded tools: ${tools.length}`);
  for (const tool of tools) {
    console.log(`- ${tool.meta.name}@${tool.meta.version}: ${tool.meta.description ?? "No description"}`);
  }
  console.log("\nCommands: /help /tools /reset /quit\n");
}

async function readAgentManifest(): Promise<AgentManifest> {
  const manifestPath = resolve(process.cwd(), "agent.json");
  const raw = await readFile(manifestPath, "utf8");
  return JSON.parse(raw) as AgentManifest;
}

async function loadToolsFromManifest(manifest: AgentManifest): Promise<LoadedTool[]> {
  const env = collectStringEnv();
  const tools: LoadedTool[] = [];

  for (const entry of manifest.tools) {
    const spec = specFromEntry(entry);
    const loaded = await load(spec, { withMeta: true, env });
    tools.push({
      spec,
      meta: loaded.meta,
      invoke: loaded.func,
    });
  }

  return tools;
}

const SYSTEM_PROMPT = [
  "You are a pragmatic research assistant running inside a local AgentPM example app.",
  "Use tools when they materially improve the answer.",
  "Prefer direct evidence from fetched pages or documents over unsupported claims.",
  "Be concise but specific.",
  "When a user asks for research, use the available tools rather than pretending you already have the source material.",
  "After using tools, synthesize the result in plain language.",
].join(" ");

async function runAgentTurn(
  client: OpenAI,
  tools: LoadedTool[],
  history: ConversationMessage[],
  userPrompt: string,
): Promise<string> {
  const toolMap = new Map(tools.map((tool) => [tool.meta.name, tool]));
  const toolDefinitions = tools.map((tool) => formatToolParameters(tool.meta));

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    ...history.map((message) => ({ role: message.role, content: message.content })),
    { role: "user", content: userPrompt },
  ];

  for (let step = 0; step < 8; step += 1) {
    const completion = await client.chat.completions.create({
      model: MODEL,
      messages,
      tools: toolDefinitions,
      tool_choice: "auto",
      temperature: 0.2,
    });

    const choice = completion.choices[0];
    const message = choice?.message;
    if (!message) {
      throw new Error("Model returned no message.");
    }

    if (message.tool_calls && message.tool_calls.length > 0) {
      messages.push({
        role: "assistant",
        content: message.content ?? "",
        tool_calls: message.tool_calls,
      });

      for (const toolCall of message.tool_calls) {
        const tool = toolMap.get(toolCall.function.name);
        if (!tool) {
          throw new Error(`Unknown tool requested by model: ${toolCall.function.name}`);
        }

        const toolArgs = toolCall.function.arguments ? JSON.parse(toolCall.function.arguments) : {};
        console.log(`\n[tool selected] ${tool.meta.name}`);
        console.log("[tool args]");
        console.log(stringifyForLog(toolArgs, 1200));

        let toolResult: JsonValue;
        try {
          toolResult = await tool.invoke(toolArgs);
        } catch (error) {
          toolResult = {
            ok: false,
            error: {
              message: String((error as Error)?.message || error),
            },
          };
        }

        console.log("[tool result]");
        console.log(stringifyForLog(toolResult));

        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: stringifyForModel(toolResult),
        });
      }

      continue;
    }

    const finalText = message.content ?? "";
    history.push({ role: "user", content: userPrompt });
    history.push({ role: "assistant", content: finalText });
    return finalText;
  }

  throw new Error("Agent exceeded maximum tool-calling steps.");
}

function printHelp() {
  console.log("\nCommands:");
  console.log("- /help  Show this help");
  console.log("- /tools List loaded tools");
  console.log("- /reset Clear conversation history");
  console.log("- /quit  Exit the app\n");
}

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("Missing OPENAI_API_KEY. Create .env.local from .env.example and set the key.");
  }

  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const manifest = await readAgentManifest();
  const tools = await loadToolsFromManifest(manifest);
  const history: ConversationMessage[] = [{ role: "system", content: SYSTEM_PROMPT }];

  printBanner(manifest.name, tools);

  const rl = createInterface({ input, output });
  try {
    while (true) {
      const line = (await rl.question("research> ")).trim();
      if (!line) continue;

      if (line === "/quit") break;
      if (line === "/help") {
        printHelp();
        continue;
      }
      if (line === "/tools") {
        printBanner(manifest.name, tools);
        continue;
      }
      if (line === "/reset") {
        history.splice(1);
        console.log("Conversation history cleared.\n");
        continue;
      }

      console.log("\n[thinking]\n");
      try {
        const answer = await runAgentTurn(client, tools, history, line);
        console.log("\n[assistant]\n");
        console.log(answer);
        console.log("");
      } catch (error) {
        console.error("\n[error]");
        console.error(String((error as Error)?.message || error));
        console.error("");
      }
    }
  } finally {
    rl.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
