import { load } from "cheerio";
import { request } from "undici";

class ToolError extends Error {
    code: string;
    details?: unknown;
    constructor(code: string, message: string, details?: unknown) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

/**
 * Pure function the AgentPM SDK will call.
 */
export async function scrape({ url }: { url: string }) {
    const res = await request(url, {
        headers: {
            "User-Agent": "AgentPM-WikipediaScrape/0.1 (+https://agentpackagemanager.com; contact: zack@example.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    });
    if (res.statusCode >= 400) {
        throw new ToolError("HTTP_ERROR", `HTTP ${res.statusCode} from target`, {
            status: res.statusCode,
        });
    }
    const html = await res.body.text();

    const $ = load(html);
    const title = $("#firstHeading").text().trim() || $("title").text().trim();
    const text = $("#mw-content-text")
        .find("p")
        .map((_, el) => $(el).text().trim())
        .get()
        .filter(Boolean)
        .join("\n\n")
        .slice(0, 50_000); // cap to keep memory sane

    const images = $("#mw-content-text img")
        .map((_, el) => $(el).attr("src"))
        .get()
        .filter(Boolean)
        .map((src) => (src!.startsWith("//") ? `https:${src}` : src!.startsWith("http") ? src! : new URL(src!, url).toString()))
        .slice(0, 20);

    return { title, text, images };
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
        const out = await scrape(input);
        process.stdout.write(JSON.stringify({ ok: true, result: out }));
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
