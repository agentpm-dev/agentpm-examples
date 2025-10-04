import { load } from "cheerio";
import {Agent, request, setGlobalDispatcher, getGlobalDispatcher} from "undici";

// 1) keep-alive off (prevents hanging)
setGlobalDispatcher(new Agent({ keepAliveTimeout: 1, keepAliveMaxTimeout: 1, pipelining: 0 }));

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
    const ac = new AbortController();
    const tid = setTimeout(() => ac.abort(), 15000);
    try {
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
    } catch (e:any) {
        if (e.name === "AbortError") throw new ToolError("TIMEOUT", "Resize timed out");
        if (e instanceof ToolError) throw e;
        throw new ToolError("RESIZE_FAILED", "Network error", { cause: String(e?.message || e) });
    } finally {
        clearTimeout(tid);
        // 2) release undici sockets
        await getGlobalDispatcher().close().catch(()=>{});
    }
}

async function readStdin(ms = 15000): Promise<string> {
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        const t = setTimeout(() => resolve(Buffer.concat(chunks).toString("utf8")), ms);
        process.stdin.setEncoding("utf8");
        process.stdin.on("data", (c) => chunks.push(Buffer.from(c)));
        process.stdin.on("end", () => { clearTimeout(t); resolve(Buffer.concat(chunks).toString("utf8")); });
        process.stdin.on("error", reject);
    });
}

async function runFromStdio() {
    try {
        const raw = await readStdin();
        const input = raw.trim() ? JSON.parse(raw) : {};
        const out = await scrape(input);
        process.stdout.write(JSON.stringify({ ok: true, ...out }));
        process.stdout.end(() => process.exit(0)); // 3) exit deterministically
    } catch (e:any) {
        const err = e instanceof ToolError
            ? { code: e.code, message: String(e.message), ...(e.details?{details:e.details}:{}) }
            : { code: "UNEXPECTED", message: String(e?.message || e) };
        process.stdout.write(JSON.stringify({ ok: false, error: err }));
        process.stdout.end(() => process.exit(e instanceof ToolError ? 0 : 1));
    }
}

if (import.meta.url === `file://${process.argv[1]}`) runFromStdio();
