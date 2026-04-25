class ToolError extends Error {
  constructor(code, message, details) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

function readStdin() {
  return new Promise((resolve, reject) => {
    const chunks = [];
    process.stdin.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
    process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    process.stdin.on("error", reject);
  });
}

function requireStartUrls(value) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new ToolError("INPUT_INVALID", "start_urls must be a non-empty array", {
      field: "start_urls"
    });
  }
  return value.map((entry) => {
    if (typeof entry !== "string") {
      throw new ToolError("INPUT_INVALID", "Each start URL must be a string", {
        field: "start_urls"
      });
    }
    return new URL(entry).toString();
  });
}

function decodeEntities(value) {
  return value
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
}

function stripTags(value) {
  return decodeEntities(value.replace(/<[^>]+>/g, " "));
}

function normalizeWhitespace(value) {
  return value.replace(/\s+/g, " ").trim();
}

function extractTitle(html) {
  const match = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return match ? normalizeWhitespace(stripTags(match[1])) : undefined;
}

function extractExcerpt(html) {
  const meta = html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i);
  if (meta) return decodeEntities(meta[1]);
  const paragraphs = [...html.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gi)];
  return paragraphs.length ? normalizeWhitespace(stripTags(paragraphs[0][1])).slice(0, 240) : undefined;
}

function extractLinks(html, baseUrl) {
  const links = [];
  const seen = new Set();
  const pattern = /<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gis;
  for (const match of html.matchAll(pattern)) {
    try {
      const href = new URL(match[1], baseUrl).toString();
      if (seen.has(href)) continue;
      seen.add(href);
      links.push({
        href,
        text: normalizeWhitespace(stripTags(match[2])) || undefined
      });
    } catch {
      continue;
    }
  }
  return links;
}

function shouldIncludeUrl(url, { allowedDomains, sameOriginOnly, seedOrigin, includePatterns, excludePatterns, isSeed }) {
  const parsed = new URL(url);
  if (sameOriginOnly && parsed.origin !== seedOrigin) {
    return { ok: false, reason: "outside_origin" };
  }
  if (allowedDomains.length > 0 && !allowedDomains.includes(parsed.hostname)) {
    return { ok: false, reason: "outside_allowed_domains" };
  }
  if (!isSeed && includePatterns.length > 0 && !includePatterns.some((pattern) => pattern.test(url))) {
    return { ok: false, reason: "missing_include_match" };
  }
  if (excludePatterns.some((pattern) => pattern.test(url))) {
    return { ok: false, reason: "matched_exclude_pattern" };
  }
  return { ok: true };
}

async function fetchRobots(origin, cache) {
  if (cache.has(origin)) return cache.get(origin);
  try {
    const response = await fetch(`${origin}/robots.txt`, {
      headers: { "user-agent": "agentpm-robots-aware-crawl/0.1" }
    });
    if (!response.ok) {
      cache.set(origin, []);
      return [];
    }
    const text = await response.text();
    const disallows = [];
    let applies = false;
    for (const rawLine of text.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) continue;
      const [field, ...rest] = line.split(":");
      if (!field || rest.length === 0) continue;
      const key = field.trim().toLowerCase();
      const value = rest.join(":").trim();
      if (key === "user-agent") {
        applies = value === "*" || value.toLowerCase() === "agentpm-robots-aware-crawl";
      } else if (applies && key === "disallow" && value) {
        disallows.push(value);
      }
    }
    cache.set(origin, disallows);
    return disallows;
  } catch {
    cache.set(origin, []);
    return [];
  }
}

function blockedByRobots(url, disallows) {
  const path = new URL(url).pathname;
  return disallows.find((rule) => path.startsWith(rule)) || null;
}

export async function robotsAwareCrawl(input) {
  const startUrls = requireStartUrls(input?.start_urls);
  const maxPages = Number.isInteger(input?.max_pages) ? input.max_pages : 10;
  const maxDepth = Number.isInteger(input?.max_depth) ? input.max_depth : 1;
  const sameOriginOnly = input?.same_origin_only === true;
  const respectRobots = input?.respect_robots !== false;
  const allowedDomains = Array.isArray(input?.allowed_domains)
    ? input.allowed_domains.filter((value) => typeof value === "string")
    : [];
  const includePatterns = Array.isArray(input?.include_patterns)
    ? input.include_patterns.map((value) => new RegExp(value))
    : [];
  const excludePatterns = Array.isArray(input?.exclude_patterns)
    ? input.exclude_patterns.map((value) => new RegExp(value))
    : [];

  const queue = startUrls.map((url) => ({
    url,
    depth: 0,
    seedOrigin: new URL(url).origin,
    isSeed: true
  }));
  const visited = new Set();
  const pages = [];
  const skipped = [];
  const errors = [];
  const robotsCache = new Map();

  while (queue.length > 0 && pages.length < maxPages) {
    const current = queue.shift();
    if (visited.has(current.url)) continue;

    const filterResult = shouldIncludeUrl(current.url, {
      allowedDomains,
      sameOriginOnly,
      seedOrigin: current.seedOrigin,
      includePatterns,
      excludePatterns,
      isSeed: current.isSeed === true
    });
    if (!filterResult.ok) {
      skipped.push({ url: current.url, reason: filterResult.reason, depth: current.depth });
      continue;
    }

    if (respectRobots) {
      const disallows = await fetchRobots(new URL(current.url).origin, robotsCache);
      const blockedRule = blockedByRobots(current.url, disallows);
      if (blockedRule) {
        skipped.push({ url: current.url, reason: "robots_disallow", rule: blockedRule, depth: current.depth });
        continue;
      }
    }

    visited.add(current.url);
    try {
      const response = await fetch(current.url, {
        headers: { "user-agent": "agentpm-robots-aware-crawl/0.1" }
      });
      if (!response.ok) {
        errors.push({ url: current.url, depth: current.depth, status: response.status, message: "Failed to fetch page" });
        continue;
      }
      const html = await response.text();
      const links = extractLinks(html, response.url || current.url);
      pages.push({
        url: current.url,
        final_url: response.url || current.url,
        depth: current.depth,
        title: extractTitle(html),
        excerpt: extractExcerpt(html),
        links
      });

      if (current.depth < maxDepth) {
        for (const link of links) {
          if (!visited.has(link.href)) {
            queue.push({
              url: link.href,
              depth: current.depth + 1,
              seedOrigin: current.seedOrigin,
              isSeed: false
            });
          }
        }
      }
    } catch (error) {
      errors.push({
        url: current.url,
        depth: current.depth,
        message: String(error?.message || error)
      });
    }
  }

  return {
    pages,
    visited_count: pages.length,
    skipped,
    errors,
    metadata: {
      max_pages: maxPages,
      max_depth: maxDepth,
      respect_robots: respectRobots
    }
  };
}

async function main() {
  try {
    const raw = await readStdin();
    const payload = raw.trim() ? JSON.parse(raw) : {};
    const output = await robotsAwareCrawl(payload);
    process.stdout.write(JSON.stringify({ ok: true, ...output }));
  } catch (error) {
    if (error instanceof ToolError) {
      process.stdout.write(JSON.stringify({
        ok: false,
        error: {
          code: error.code,
          message: error.message,
          ...(error.details ? { details: error.details } : {})
        }
      }));
      process.exitCode = 0;
      return;
    }
    process.stdout.write(JSON.stringify({
      ok: false,
      error: { code: "UNEXPECTED", message: String(error?.message || error) }
    }));
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
