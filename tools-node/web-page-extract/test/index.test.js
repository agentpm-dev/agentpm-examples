import test from "node:test";
import assert from "node:assert/strict";
import { extractPageData, webPageExtract } from "../src/index.js";

const HTML = `<!doctype html>
<html>
  <head>
    <title>AgentPM Launch</title>
    <meta name="description" content="AgentPM makes tools portable.">
    <meta property="article:published_time" content="2026-04-12">
    <link rel="canonical" href="/blog/launch">
  </head>
  <body>
    <article>
      <h1>AgentPM Launch</h1>
      <p>Portable tools for agents.</p>
      <p>Install once, run anywhere.</p>
      <a href="/docs">Read docs</a>
    </article>
  </body>
</html>`;

test("extractPageData returns normalized metadata and markdown content", () => {
  const out = extractPageData(HTML, "https://example.com/post", "markdown", true, 1000);
  assert.equal(out.title, "AgentPM Launch");
  assert.equal(out.canonical_url, "https://example.com/blog/launch");
  assert.equal(out.published_at, "2026-04-12");
  assert.match(out.content, /Portable tools for agents/);
  assert.equal(out.links[0].href, "https://example.com/docs");
});

test("webPageExtract fetches and parses a page", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(HTML, {
      status: 200,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  try {
    const out = await webPageExtract({
      url: "https://example.com/article",
      format: "text",
      include_links: true,
    });
    assert.equal(out.url, "https://example.com/article");
    assert.equal(out.final_url, "");
    assert.equal(out.format, "text");
    assert.match(out.content, /Install once, run anywhere/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
