import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

test("research assistant loads direct tools and local skills from the generated manifest", async () => {
  const source = await readFile(resolve(process.cwd(), "src/main.ts"), "utf8");
  assert.match(source, /readLocalManifest/);
  assert.match(source, /manifest\.tools \?\? \[\]/);
  assert.match(source, /manifest\.skills \?\? \[\]/);
  assert.match(source, /await load\(spec, \{ withMeta: true, env \}\)/);
  assert.match(source, /await loadSkill\(spec\)/);
  assert.match(source, /Follow these packaged research procedures/);
  assert.doesNotMatch(source, /loadAgent\(/);
});
