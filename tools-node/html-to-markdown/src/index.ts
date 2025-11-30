import { JSDOM } from "jsdom";
import { Readability } from "@mozilla/readability";
import TurndownService from "turndown";

class ToolError extends Error {
    code: string;
    details?: unknown;
    constructor(code: string, message: string, details?: unknown) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

interface HtmlToMarkdownInput {
    html: string;
    base_url?: string;
    main_content_only?: boolean;
    preserve_links?: boolean;
    preserve_images?: boolean;
}

interface HtmlToMarkdownOutput {
    markdown: string;
    text: string;
    metadata?: {
        content_length_markdown?: number;
        content_length_text?: number;
        main_content_extracted?: boolean;
        [key: string]: unknown;
    };
}

function resolveBaseUrl(inputBaseUrl?: string): string | undefined {
    const envBase = process.env.HTML2MD_DEFAULT_BASE_URL;
    const candidate = inputBaseUrl || envBase;
    if (!candidate) return undefined;
    try {
        return new URL(candidate).toString();
    } catch {
        // Invalid base URL; ignore rather than fail the whole tool.
        return undefined;
    }
}

export async function htmlToMarkdown(input: HtmlToMarkdownInput): Promise<HtmlToMarkdownOutput> {
    const {
        html,
        base_url,
        main_content_only = false,
        preserve_links = true,
        preserve_images = false,
    } = input;

    if (!html || typeof html !== "string") {
        throw new ToolError("INPUT_INVALID", "Missing or invalid 'html' field", { field: "html" });
    }

    const baseUrl = resolveBaseUrl(base_url);

    let dom: JSDOM;
    try {
        dom = new JSDOM(html, baseUrl ? { url: baseUrl } : undefined);
    } catch (e: any) {
        throw new ToolError("PARSE_FAILED", "Failed to parse HTML", {
            message: String(e?.message || e),
        });
    }

    let htmlForMarkdown = html;
    let plainText = "";
    let mainContentExtracted = false;

    if (main_content_only) {
        try {
            const reader = new Readability(dom.window.document);
            const article = reader.parse();
            if (article && article.content) {
                htmlForMarkdown = article.content;
                plainText = (article.textContent || "").trim();
                mainContentExtracted = true;
            } else {
                // Fallback to full document text if readability fails
                htmlForMarkdown = dom.serialize();
                plainText = (dom.window.document.body?.textContent || "").trim();
                mainContentExtracted = false;
            }
        } catch (e: any) {
            // Readability failed; fall back to full document instead of hard failing
            htmlForMarkdown = dom.serialize();
            plainText = (dom.window.document.body?.textContent || "").trim();
            mainContentExtracted = false;
        }
    } else {
        htmlForMarkdown = dom.serialize();
        plainText = (dom.window.document.body?.textContent || "").trim();
        mainContentExtracted = false;
    }

    // Configure Turndown
    const turndownService = new TurndownService({
        headingStyle: "atx",
        codeBlockStyle: "fenced",
        emDelimiter: "_",
        strongDelimiter: "**",
        bulletListMarker: "-",
    });

    if (!preserve_links) {
        // Replace links with just their text content
        turndownService.addRule("strip-links", {
            filter: "a",
            replacement(content) {
                return content;
            },
        });
    }

    if (!preserve_images) {
        // Replace images with their alt text (or nothing)
        turndownService.addRule("strip-images", {
            filter: "img",
            replacement(_content, node) {
                const alt = (node as HTMLElement).getAttribute?.("alt") || "";
                return alt;
            },
        });
    }

    let markdown: string;
    try {
        markdown = turndownService.turndown(htmlForMarkdown);
    } catch (e: any) {
        throw new ToolError("PARSE_FAILED", "Failed to convert HTML to Markdown", {
            message: String(e?.message || e),
        });
    }

    const text = plainText;

    return {
        markdown,
        text,
        metadata: {
            content_length_markdown: markdown.length,
            content_length_text: text.length,
            main_content_extracted: mainContentExtracted,
        },
    };
}

async function readStdin(): Promise<string> {
    const chunks: Buffer[] = [];
    for await (const chunk of process.stdin) chunks.push(chunk as Buffer);
    return Buffer.concat(chunks).toString('utf8');
}

async function runFromStdio() {
    try {
        const raw = await readStdin();
        const input = raw.trim() ? JSON.parse(raw) : {};
        const out = await htmlToMarkdown(input);
        process.stdout.write(JSON.stringify({ ok: true, ...out }));
    } catch (e: any) {
        if (e instanceof ToolError) {
            // Value-level error: ok:false, but exit code 0 so runtime doesn't mark it as a crash
            process.stdout.write(
                JSON.stringify({
                    ok: false,
                    error: {
                        code: e.code,
                        message: e.message,
                        ...(e.details !== undefined ? { details: e.details } : {})
                    }
                })
            );
            process.exitCode = 0;
        } else {
            // Unexpected/transport-ish error: still return the shape, but non-zero exit
            process.stdout.write(
                JSON.stringify({
                    ok: false,
                    error: {
                        code: "UNEXPECTED",
                        message: String(e?.message || e)
                    }
                })
            );
            process.exitCode = 1;
        }
    }
}

if (import.meta.url === `file://${process.argv[1]}`) runFromStdio();