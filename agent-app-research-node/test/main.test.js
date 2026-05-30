import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { access } from "node:fs/promises";

test("research app uses the published research-console agent package", async () => {
  const source = await readFile(resolve(process.cwd(), "src/main.ts"), "utf8");
  assert.match(source, /const AGENT_SPEC = "@zack\/research-console@0\.1\.1"/);
  assert.match(source, /loadAgent\(agentSpec\)/);
  assert.match(source, /agent\.resolvedTools/);
  assert.match(source, /load\(spec, \{ withMeta: true, env \}\)/);
});

test("research app no longer expects a local agent.json", async () => {
  await assert.rejects(() => access(resolve(process.cwd(), "agent.json")));
});
