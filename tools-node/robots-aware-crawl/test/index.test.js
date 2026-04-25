import test from "node:test";
import assert from "node:assert/strict";

import { robotsAwareCrawl } from "../src/index.js";

function withMockedFetch(map, fn) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    const key = typeof url === "string" ? url : url.toString();
    if (!(key in map)) {
      return new Response("missing", { status: 404 });
    }
    const entry = map[key];
    return new Response(entry.body, {
      status: entry.status ?? 200,
      headers: { "content-type": entry.contentType ?? "text/html; charset=utf-8" }
    });
  };
  return Promise.resolve(fn()).finally(() => {
    globalThis.fetch = originalFetch;
  });
}

test("robotsAwareCrawl follows links within limits", async () => {
  await withMockedFetch(
    {
      "https://example.com/robots.txt": { body: "User-agent: *\nDisallow:\n", contentType: "text/plain" },
      "https://example.com/start": {
        body: '<html><head><title>Start</title></head><body><p>Hello</p><a href="/docs">Docs</a></body></html>'
      },
      "https://example.com/docs": {
        body: '<html><head><title>Docs</title><meta name="description" content="Docs page"></head><body><p>Docs body</p></body></html>'
      }
    },
    async () => {
      const out = await robotsAwareCrawl({
        start_urls: ["https://example.com/start"],
        max_pages: 5,
        max_depth: 1,
        respect_robots: true,
        same_origin_only: true
      });
      assert.equal(out.visited_count, 2);
      assert.equal(out.pages[0].title, "Start");
      assert.equal(out.pages[1].title, "Docs");
    }
  );
});

test("robotsAwareCrawl skips disallowed URLs", async () => {
  await withMockedFetch(
    {
      "https://example.com/robots.txt": { body: "User-agent: *\nDisallow: /private\n", contentType: "text/plain" },
      "https://example.com/start": {
        body: '<html><body><a href="/private/report">Report</a></body></html>'
      }
    },
    async () => {
      const out = await robotsAwareCrawl({
        start_urls: ["https://example.com/start"],
        max_pages: 5,
        max_depth: 1,
        respect_robots: true
      });
      assert.equal(out.visited_count, 1);
      assert.equal(out.skipped[0].reason, "robots_disallow");
    }
  );
});

test("robotsAwareCrawl honors include_patterns", async () => {
  await withMockedFetch(
    {
      "https://example.com/robots.txt": { body: "User-agent: *\nDisallow:\n", contentType: "text/plain" },
      "https://example.com/start": {
        body: '<html><body><a href="/docs/intro">Docs</a><a href="/blog/post">Blog</a></body></html>'
      },
      "https://example.com/docs/intro": {
        body: "<html><head><title>Docs Intro</title></head><body><p>Allowed</p></body></html>"
      }
    },
    async () => {
      const out = await robotsAwareCrawl({
        start_urls: ["https://example.com/start"],
        max_pages: 5,
        max_depth: 1,
        respect_robots: true,
        include_patterns: ["\\/docs\\/"]
      });
      assert.equal(out.visited_count, 2);
      assert.equal(out.pages[1].title, "Docs Intro");
      assert.equal(out.skipped[0].reason, "missing_include_match");
      assert.equal(out.skipped[0].url, "https://example.com/blog/post");
    }
  );
});

test("robotsAwareCrawl honors exclude_patterns", async () => {
  await withMockedFetch(
    {
      "https://example.com/robots.txt": { body: "User-agent: *\nDisallow:\n", contentType: "text/plain" },
      "https://example.com/start": {
        body: '<html><body><a href="/docs/intro">Docs</a><a href="/private/report">Private</a></body></html>'
      },
      "https://example.com/docs/intro": {
        body: "<html><head><title>Docs Intro</title></head><body><p>Allowed</p></body></html>"
      }
    },
    async () => {
      const out = await robotsAwareCrawl({
        start_urls: ["https://example.com/start"],
        max_pages: 5,
        max_depth: 1,
        respect_robots: true,
        exclude_patterns: ["\\/private\\/"]
      });
      assert.equal(out.visited_count, 2);
      assert.equal(out.pages[1].title, "Docs Intro");
      assert.equal(out.skipped[0].reason, "matched_exclude_pattern");
      assert.equal(out.skipped[0].url, "https://example.com/private/report");
    }
  );
});
