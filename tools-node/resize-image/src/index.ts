import {Agent, request, setGlobalDispatcher, getGlobalDispatcher } from "undici";
import Jimp, { MIME_JPEG } from "jimp";

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

export async function resize({
    url,
    width,
    height,
    keep_aspect = true,
}: {
    url: string;
    width: number;
    height: number;
    keep_aspect?: boolean;
}) {
    const ac = new AbortController();
    const tid = setTimeout(() => ac.abort(), 15000);

    try {
        if (!url) throw new ToolError("INPUT_INVALID", "`url` is required");
        if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
            throw new ToolError("INPUT_INVALID", "`width` and `height` must be positive numbers");
        }

        const res = await request(url, {
            headers: {
                "User-Agent": "AgentPM-WikipediaScrape/0.1 (+https://agentpackagemanager.com; contact: zack@example.com)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }).catch((e) => {
            throw new ToolError("FETCH_FAILED", "Network error", { cause: String(e) });
        });

        if (res.statusCode >= 400) {
            throw new ToolError("HTTP_ERROR", `HTTP ${res.statusCode}`, { status: res.statusCode });
        }

        const buf = Buffer.from(await res.body.arrayBuffer());
        const img = await Jimp.read(buf).catch((e) => {
            throw new ToolError("DECODE_FAILED", "Unsupported/invalid image", { cause: String(e) });
        });

        if (keep_aspect) {
            // keep aspect while fitting within width x height (letterboxed as needed)
            img.contain(width, height);
        } else {
            // exact size, no aspect preservation
            img.resize(width, height); // <-- positional args
        }

        // async variant that returns a Buffer
        const out: Buffer = await img.getBufferAsync(MIME_JPEG);

        return { image_base64_jpeg: out.toString("base64") };
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
        const out = await resize(input);
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

if (require.main === module) {
    runFromStdio();
}