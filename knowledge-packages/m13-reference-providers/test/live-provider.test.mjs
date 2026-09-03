import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { createInterface } from "node:readline";

const command = process.env.AGENTPM_M13_LIVE_PROVIDER_COMMAND;
const args = process.env.AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON
  ? JSON.parse(process.env.AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON)
  : [];

test(
  "live KnowledgeRuntime process returns normalized results",
  { skip: !command },
  async () => {
    const child = spawn(command, args, {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["pipe", "pipe", "inherit"],
    });
    const rl = createInterface({ input: child.stdout });
    const frames = [];
    rl.on("line", (line) => frames.push(JSON.parse(line)));

    child.stdin.write(
      `${JSON.stringify({
        protocol: "agentpm-service",
        version: 1,
        kind: "initialize",
        id: "init-live",
        service: "knowledge",
        method: "initialize",
        payload: {
          role: "knowledge",
          registry_id: process.env.AGENTPM_KNOWLEDGE_RUNTIME_ID,
        },
      })}\n`,
    );
    child.stdin.write(
      `${JSON.stringify({
        protocol: "agentpm-service",
        version: 1,
        kind: "request",
        id: "retrieve-live",
        service: "knowledge",
        method: "retrieve",
        payload: {
          request: {
            package: process.env.AGENTPM_KNOWLEDGE_PACKAGE,
            version: process.env.AGENTPM_KNOWLEDGE_VERSION,
            mode: "vector_query",
            query:
              process.env.AGENTPM_M13_LIVE_QUERY || "alpha launch release gate",
            top_k: 2,
            return_citations: true,
          },
        },
      })}\n`,
    );
    child.stdin.end();

    await once(child, "exit");

    const initialized = frames.find((frame) => frame.id === "init-live");
    const retrieved = frames.find((frame) => frame.id === "retrieve-live");
    assert.equal(initialized?.kind, "initialized");
    assert.equal(retrieved?.kind, "response");
    assert.equal(retrieved.result.ok, true);
    assert.equal(
      retrieved.result.package,
      process.env.AGENTPM_KNOWLEDGE_PACKAGE,
    );
    assert.ok(Array.isArray(retrieved.result.results));
    assert.ok(retrieved.result.results.length > 0);
    assert.ok(Array.isArray(retrieved.result.citations));
  },
);
