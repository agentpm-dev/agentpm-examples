import { readFileSync } from "node:fs";

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
  return value
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]+/g, " ")
    .replace(/[ \t]*\n[ \t]*/g, "\n")
    .trim();
}

function extractFirst(html, regex) {
  const match = html.match(regex);
  return match ? decodeEntities(match[1].trim()) : undefined;
}

function extractMeta(html, names) {
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const patterns = [
      new RegExp(`<meta[^>]+(?:name|property)=["']${escaped}["'][^>]+content=["']([^"']+)["'][^>]*>`, "i"),
      new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["']${escaped}["'][^>]*>`, "i"),
    ];
    for (const pattern of patterns) {
      const value = extractFirst(html, pattern);
      if (value) return value;
    }
  }
  return undefined;
}

function absolutizeUrl(baseUrl, href) {
  if (!href) return undefined;
  try {
    return new URL(href, baseUrl).toString();
  } catch {
    return undefined;
  }
}

export function extractLinks(html, baseUrl) {
  const links = [];
  const seen = new Set();
  const pattern = /<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gis;
  for (const match of html.matchAll(pattern)) {
    const href = absolutizeUrl(baseUrl, match[1]);
    if (!href || seen.has(href)) continue;
    seen.add(href);
    links.push({
      text: normalizeWhitespace(stripTags(match[2])) || undefined,
      href,
    });
  }
  return links;
}

function htmlToText(html) {
  const withoutNoise = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<noscript\b[\s\S]*?<\/noscript>/gi, " ");
  const withBreaks = withoutNoise
    .replace(/<\/?(p|div|section|article|main|aside|header|footer|h[1-6]|li|ul|ol|br|tr|table)\b[^>]*>/gi, "\n");
  return normalizeWhitespace(stripTags(withBreaks));
}

function htmlToMarkdown(html, baseUrl) {
  let body = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<noscript\b[\s\S]*?<\/noscript>/gi, " ");

  body = body.replace(/<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gis, (_m, href, text) => {
    const absolute = absolutizeUrl(baseUrl, href) || href;
    const label = normalizeWhitespace(stripTags(text)) || absolute;
    return `[${label}](${absolute})`;
  });

  for (let level = 6; level >= 1; level -= 1) {
    const hashes = "#".repeat(level);
    const regex = new RegExp(`<h${level}\\b[^>]*>([\\s\\S]*?)<\\/h${level}>`, "gi");
    body = body.replace(regex, (_m, text) => `\n\n${hashes} ${normalizeWhitespace(stripTags(text))}\n\n`);
  }

  body = body
    .replace(/<li\b[^>]*>([\s\S]*?)<\/li>/gi, (_m, text) => `\n- ${normalizeWhitespace(stripTags(text))}`)
    .replace(/<\/?(p|div|section|article|main|aside|header|footer|ul|ol|br|tr|table)\b[^>]*>/gi, "\n");

  return normalizeWhitespace(stripTags(body).replace(/\[([^\]]+)\]\(([^)]+)\)/g, "[$1]($2)"));
}

export function extractPageData(html, pageUrl, format = "markdown", includeLinks = true, maxChars = 40000) {
  const title =
    extractMeta(html, ["og:title", "twitter:title"]) ||
    extractFirst(html, /<title[^>]*>([\s\S]*?)<\/title>/i);
  const excerpt =
    extractMeta(html, ["description", "og:description", "twitter:description"]);
  const canonicalUrl =
    absolutizeUrl(pageUrl, extractFirst(html, /<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["'][^>]*>/i)) ||
    pageUrl;
  const publishedAt = extractMeta(html, [
    "article:published_time",
    "og:published_time",
    "publication_date",
    "date",
  ]);
  const byline = extractMeta(html, ["author", "article:author"]);

  const contentRaw = format === "text" ? htmlToText(html) : htmlToMarkdown(html, pageUrl);
  const content = contentRaw.slice(0, maxChars);
  return {
    title,
    canonical_url: canonicalUrl,
    published_at: publishedAt,
    byline,
    excerpt,
    format,
    content,
    links: includeLinks ? extractLinks(html, pageUrl) : [],
    metadata: {
      truncated: contentRaw.length > content.length,
      content_chars: content.length,
      source_bytes: Buffer.byteLength(html, "utf8"),
    },
  };
}

export async function webPageExtract(input) {
  if (!input || typeof input.url !== "string" || !input.url) {
    throw new ToolError("INPUT_INVALID", "Missing or invalid 'url' field", { field: "url" });
  }
  const format = input.format === "text" ? "text" : "markdown";
  const timeoutMs = Number.isInteger(input.timeout_ms) ? input.timeout_ms : 15000;
  const includeLinks = input.include_links !== false;
  const maxChars = Number.isInteger(input.max_chars) ? input.max_chars : 40000;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input.url, {
      signal: controller.signal,
      headers: { "user-agent": "agentpm-web-page-extract/0.1" },
    });
    if (!response.ok) {
      throw new ToolError("FETCH_FAILED", `Request failed with status ${response.status}`, {
        status: response.status,
        url: input.url,
      });
    }
    const html = await response.text();
    const extracted = extractPageData(html, response.url, format, includeLinks, maxChars);
    return {
      url: input.url,
      final_url: response.url,
      ...extracted,
    };
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw new ToolError("TIMEOUT", "Request timed out", {
        timeout_ms: timeoutMs,
        url: input.url,
      });
    }
    if (error instanceof ToolError) throw error;
    throw new ToolError("FETCH_FAILED", String(error?.message || error), { url: input.url });
  } finally {
    clearTimeout(timeout);
  }
}

async function main() {
  try {
    const raw = await readStdin();
    const payload = raw.trim() ? JSON.parse(raw) : {};
    const output = await webPageExtract(payload);
    process.stdout.write(JSON.stringify({ ok: true, ...output }));
  } catch (error) {
    if (error instanceof ToolError) {
      process.stdout.write(
        JSON.stringify({
          ok: false,
          error: {
            code: error.code,
            message: error.message,
            ...(error.details ? { details: error.details } : {}),
          },
        }),
      );
      process.exitCode = 0;
      return;
    }
    process.stdout.write(
      JSON.stringify({
        ok: false,
        error: {
          code: "UNEXPECTED",
          message: String(error?.message || error),
        },
      }),
    );
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
