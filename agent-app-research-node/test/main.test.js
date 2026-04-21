import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

test("agent manifest references tools with versions", async () => {
  const raw = await readFile(resolve(process.cwd(), "agent.json"), "utf8");
  const manifest = JSON.parse(raw);
  assert.equal(manifest.kind, "agent");
  assert.ok(Array.isArray(manifest.tools));
  assert.ok(manifest.tools.length >= 4);
  for (const entry of manifest.tools) {
    if (typeof entry === "string") {
      assert.match(entry, /@.+@.+/);
    } else {
      assert.equal(typeof entry.name, "string");
      assert.equal(typeof entry.version, "string");
    }
  }
});
