import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

test("research assistant loads tools from the generated local manifest", async () => {
  const source = await readFile(resolve(process.cwd(), "src/main.ts"), "utf8");
  assert.match(source, /readLocalManifest/);
  assert.match(source, /manifest\.tools \?\? \[\]/);
  assert.match(source, /await load\(spec, \{ withMeta: true, env \}\)/);
  assert.doesNotMatch(source, /loadAgent\(/);
});
