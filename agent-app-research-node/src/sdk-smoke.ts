import { resolve } from "node:path";

import { load, loadAgent, loadSkill } from "@agentpm/sdk";

if (process.argv[2]) process.chdir(resolve(process.argv[2]));
const agent = await loadAgent("@zack/devwork-copilot@0.1.8");
const refs = [...agent.resolvedTools];
for (const entry of agent.resolvedSkills) {
  const skill = await loadSkill(`${entry.name}@${entry.version}`);
  refs.push(...skill.resolvedTools);
}
const summary = refs.find((ref) => ref.name === "@zack/summarize-text");
if (!summary)
  throw new Error(
    "Installed Agent does not reference summarize-text; reinstall the exact Agent version.",
  );
const spec = `${summary.name}@${summary.version}`;
const invoke = await load(spec, { env: { OPENAI_API_KEY: "" } });
const result = await invoke({ text: "SDK dependency smoke", max_words: 50 });
if (
  !result ||
  typeof result !== "object" ||
  Array.isArray(result) ||
  result.ok !== false ||
  !result.error ||
  typeof result.error !== "object" ||
  Array.isArray(result.error) ||
  result.error.code !== "INPUT_MISSING_API_KEY"
) {
  throw new Error("Expected the Tool's no-model validation result");
}
console.log(
  JSON.stringify({ agent: agent.manifest.version, tool: spec, output: result }),
);
