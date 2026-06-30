import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

import dotenv from "dotenv";
import OpenAI from "openai";
import { load, loadSkill, type JsonValue, type ToolMeta } from "@agentpm/sdk";

const DOTENV_LOCAL_PATH = resolve(process.cwd(), ".env.local");
const DOTENV_PATH = resolve(process.cwd(), ".env");

if (existsSync(DOTENV_LOCAL_PATH)) {
  dotenv.config({ path: DOTENV_LOCAL_PATH });
} else {
  dotenv.config({ path: DOTENV_PATH });
}

type LoadedTool = {
  spec: string;
  meta: ToolMeta;
  invoke: (input: JsonValue) => Promise<JsonValue>;
};

type LoadedSkill = {
  name: string;
  version: string;
  description?: string;
  entrypointContent: string;
  resolvedTools: Array<{ name: string; version: string }>;
};

type ConversationMessage =
  | { role: "system"; content: string }
  | { role: "user"; content: string }
  | { role: "assistant"; content: string };

type PackageReference = string | { name: string; version?: string };
type AgentManifest = {
  name: string;
  tools?: PackageReference[];
  skills?: PackageReference[];
};

const MAX_TOOL_RESULT_CHARS = 8000;
const MAX_LOG_RESULT_CHARS = 1800;
const MODEL = process.env.OPENAI_MODEL || "gpt-4o-mini";

function collectStringEnv(): Record<string, string> {
  return Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => typeof entry[1] === "string"),
  );
}

function refToSpec(ref: PackageReference): string {
  if (typeof ref === "string") {
    return ref;
  }
  return ref.version ? `${ref.name}@${ref.version}` : ref.name;
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
  console.log(`\nResearch Assistant: ${manifestName}`);
  console.log(`Model: ${MODEL}`);
  console.log(`Loaded tools: ${tools.length}`);
  for (const tool of tools) {
    console.log(`- ${tool.meta.name}@${tool.meta.version}: ${tool.meta.description ?? "No description"}`);
  }
  console.log("\nCommands: /help /tools /reset /quit\n");
}

function printBannerWithSkills(manifestName: string, skills: LoadedSkill[], tools: LoadedTool[]) {
  console.log(`\nResearch Assistant: ${manifestName}`);
  console.log(`Model: ${MODEL}`);
  console.log(`Loaded skills: ${skills.length}`);
  for (const skill of skills) {
    console.log(`- ${skill.name}@${skill.version}: ${skill.description ?? "No description"}`);
  }
  console.log(`Loaded tools: ${tools.length}`);
  for (const tool of tools) {
    console.log(`- ${tool.meta.name}@${tool.meta.version}: ${tool.meta.description ?? "No description"}`);
  }
  console.log("\nCommands: /help /tools /reset /quit\n");
}

async function readLocalManifest(): Promise<AgentManifest> {
  const manifestPath = resolve(process.cwd(), "agent.json");
  const raw = await readFile(manifestPath, "utf8");
  const parsed = JSON.parse(raw) as AgentManifest;
  if (!parsed || typeof parsed !== "object" || typeof parsed.name !== "string") {
    throw new Error("agent.json is missing a valid name field.");
  }
  return parsed;
}

function renderSkillManuals(skills: LoadedSkill[]): string {
  return skills
    .map((skill) => [`Skill: ${skill.name}@${skill.version}`, skill.entrypointContent.trim()].join("\n"))
    .join("\n\n");
}

async function loadToolsFromLocalManifest(): Promise<{ manifestName: string; skills: LoadedSkill[]; tools: LoadedTool[] }> {
  const manifest = await readLocalManifest();
  const env = collectStringEnv();
  const directRefs = manifest.tools ?? [];
  const skillRefs = manifest.skills ?? [];
  const tools: LoadedTool[] = [];
  const skills: LoadedSkill[] = [];
  const seenSpecs = new Set<string>();

  for (const ref of directRefs) {
    const spec = refToSpec(ref);
    seenSpecs.add(spec);
    const loaded = await load(spec, { withMeta: true, env });
    tools.push({
      spec,
      meta: loaded.meta,
      invoke: loaded.func,
    });
  }

  for (const ref of skillRefs) {
    const spec = refToSpec(ref);
    const loadedSkill = await loadSkill(spec);
    skills.push(loadedSkill);

    for (const entry of loadedSkill.resolvedTools) {
      const toolSpec = `${entry.name}@${entry.version}`;
      if (seenSpecs.has(toolSpec)) continue;
      seenSpecs.add(toolSpec);
      const loaded = await load(toolSpec, { withMeta: true, env });
      tools.push({
        spec: toolSpec,
        meta: loaded.meta,
        invoke: loaded.func,
      });
    }
  }

  return {
    manifestName: manifest.name,
    skills,
    tools,
  };
}

const SYSTEM_PROMPT_LINES = [
  "You are a pragmatic research assistant running inside a local AgentPM example app.",
  "Use tools when they materially improve the answer.",
  "Prefer direct evidence from fetched pages or documents over unsupported claims.",
  "Be concise but specific.",
  "When a user asks for research, use the available tools rather than pretending you already have the source material.",
  "After using tools, synthesize the result in plain language.",
];

async function runAgentTurn(
  client: OpenAI,
  tools: LoadedTool[],
  systemPrompt: string,
  history: ConversationMessage[],
  userPrompt: string,
): Promise<string> {
  const toolMap = new Map(tools.map((tool) => [tool.meta.name, tool]));
  const toolDefinitions = tools.map((tool) => formatToolParameters(tool.meta));

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: systemPrompt },
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
  const { manifestName, skills, tools } = await loadToolsFromLocalManifest();
  const skillManuals = renderSkillManuals(skills);
  const systemPrompt = skillManuals
    ? `${SYSTEM_PROMPT_LINES.join(" ")}\n\nFollow these packaged research procedures when they are relevant to the user's request:\n\n${skillManuals}`
    : SYSTEM_PROMPT_LINES.join(" ");
  const history: ConversationMessage[] = [];

  printBannerWithSkills(manifestName, skills, tools);

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
        printBannerWithSkills(manifestName, skills, tools);
        continue;
      }
      if (line === "/reset") {
        history.splice(1);
        console.log("Conversation history cleared.\n");
        continue;
      }

      console.log("\n[thinking]\n");
      try {
        const answer = await runAgentTurn(client, tools, systemPrompt, history, line);
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
