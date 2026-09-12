import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { runMemoryRuntimeConformance } from "./support/conformance.mjs";

const command = process.env.AGENTPM_M16_LIVE_PROVIDER_COMMAND;
const args = process.env.AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON
  ? JSON.parse(process.env.AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON)
  : [];

test("live MemoryRuntime provider passes advertised conformance scenario", { skip: !command }, async () => {
  const child = spawn(command, args, {
    stdio: ["pipe", "pipe", "pipe"],
    env: process.env,
  });
  const stderr = [];
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk) => stderr.push(chunk));
  let exited = false;
  let exitCode = null;
  const lines = createInterface({ input: child.stdout });
  const pending = [];
  lines.on("line", (line) => {
    if (!line.trim()) return;
    const response = JSON.parse(line);
    const next = pending.shift();
    if (next) next(response);
  });
  child.on("exit", (code) => {
    exited = true;
    exitCode = code;
    while (pending.length) {
      pending.shift()(undefined);
    }
  });

  let requestId = 0;
  const send = (message) =>
    new Promise((resolve) => {
      if (exited) {
        resolve(undefined);
        return;
      }
      pending.push(resolve);
      child.stdin.write(`${JSON.stringify(message)}\n`);
    });
  const request = (method, payload) =>
    send({
      protocol: "agentpm-service",
      version: 1,
      kind: "request",
      id: `request-${++requestId}`,
      service: "memory",
      method,
      payload,
    });

  const initialized = await send({
    protocol: "agentpm-service",
    version: 1,
    kind: "initialize",
    id: "init",
    service: "memory",
    method: "initialize",
    payload: { role: "memory", registry_id: "live-memory-reference" },
  });
  assert(initialized, `provider exited before initialize response (${exitCode}): ${stderr.join("")}`);
  assert.equal(initialized.kind, "initialized");
  assert.equal(initialized.service, "memory");
  assert.equal(initialized.result.ready, true);

  const capabilities = memoryCapabilities(initialized.result);
  assert(capabilities.descriptor, JSON.stringify(initialized.result));
  await runMemoryRuntimeConformance("live", capabilities, async (method, payload) =>
    okResult(await request(method, payload)),
  );
  child.stdin.end();

  const exit = await new Promise((resolve) => {
    child.on("exit", (code) => resolve(code));
  });
  assert.equal(exit, 0, stderr.join(""));
});

function okResult(frame) {
  assert(frame, "provider exited before response");
  assert.equal(frame.kind, "response", JSON.stringify(frame));
  assert.equal(frame.result?.ok, true, JSON.stringify(frame));
  return frame.result;
}

function memoryCapabilities(result) {
  if (result?.capabilities?.descriptor) return result.capabilities;
  if (result?.descriptor) return result;
  return result?.capabilities || {};
}
