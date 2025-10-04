import {Agent, request, setGlobalDispatcher, getGlobalDispatcher } from "undici";
import Jimp, { MIME_JPEG } from "jimp";

process.stderr.write(`[resize] start pid=${process.pid}\n`);
process.on("beforeExit", () => {
    // helps catch lingering handles that keep the loop alive
    const handles = (process as any)._getActiveHandles?.() || [];
    const kinds = handles.map((h: any) => h?.constructor?.name || typeof h);
    process.stderr.write(`[resize] beforeExit activeHandles=${JSON.stringify(kinds)}\n`);
});

function mark(msg: string) { process.stderr.write(`[resize] ${msg}\n`); }

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
            signal: ac.signal,
            headers: {
                "User-Agent": "AgentPM-WikipediaScrape/0.1 (+https://agentpackagemanager.com; contact: zack@example.com)",
                "Accept": "*/*",
            },
        }).catch((e) => {
            throw new ToolError("FETCH_FAILED", "Network error", { cause: String(e) });
        });
        mark(`fetched status=${res.statusCode}`);

        if (res.statusCode >= 400) {
            throw new ToolError("HTTP_ERROR", `HTTP ${res.statusCode}`, { status: res.statusCode });
        }

        const buf = Buffer.from(await res.body.arrayBuffer());
        mark(`downloaded bytes=${buf.length}`);
        const img = await Jimp.read(buf).catch((e) => {
            throw new ToolError("DECODE_FAILED", "Unsupported/invalid image", { cause: String(e) });
        });
        mark(`decoded w=${img.getWidth()} h=${img.getHeight()}`);

        if (keep_aspect) {
            // keep aspect while fitting within width x height (letterboxed as needed)
            img.contain(width, height);
        } else {
            // exact size, no aspect preservation
            img.resize(width, height); // <-- positional args
        }
        mark(`resized`);

        // async variant that returns a Buffer
        const out: Buffer = await img.getBufferAsync(MIME_JPEG);
        mark(`encoded bytes=${out.length}`);
        return { image_base64_jpeg: out.toString("base64") };
    } catch (e:any) {
        if (e.name === "AbortError") throw new ToolError("TIMEOUT", "Resize timed out");
        if (e instanceof ToolError) throw e;
        throw new ToolError("RESIZE_FAILED", "Network error", { cause: String(e?.message || e) });
    } finally {
        clearTimeout(tid);
        // 2) release undici sockets
        try { void getGlobalDispatcher().close(); } catch {}
    }
}

function writeJsonAndExit(obj: any, codeOk = 0) {
    const s = JSON.stringify(obj);
    let i = 0;
    function pump() {
        while (i < s.length) {
            const chunk = s.slice(i, i + 65536); // 64 KB chunks
            i += chunk.length;
            if (!process.stdout.write(chunk)) {
                // buffer is full, wait for drain and resume
                process.stdout.once("drain", pump);
                return;
            }
        }
        // all flushed; exit on next tick
        hardExit(codeOk)
    }
    pump();
}

async function readStdin(ms = 15000): Promise<string> {
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        const timer = setTimeout(() => { cleanup(); resolve(Buffer.concat(chunks).toString("utf8")); }, ms);
        const onData = (c: string | Buffer) => chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(c));
        const onEnd  = () => { clearTimeout(timer); cleanup(); resolve(Buffer.concat(chunks).toString("utf8")); };
        const onErr  = (e: any) => { clearTimeout(timer); cleanup(); reject(e); };
        const cleanup = () => {
            process.stdin.off("data", onData);
            process.stdin.off("end", onEnd);
            process.stdin.off("error", onErr);
            try { process.stdin.pause(); } catch {}
        };
        process.stdin.setEncoding("utf8");
        process.stdin.on("data", onData);
        process.stdin.on("end", onEnd);
        process.stdin.on("error", onErr);
    });
}

function hardExit(code = 0) {
    try { process.stdin.pause(); } catch {}
    setImmediate(() => process.exit(code));
}

async function runFromStdio() {
    try {
        const raw = await readStdin();
        const input = raw.trim() ? JSON.parse(raw) : {};
        const out = await resize(input);
        writeJsonAndExit({ ok: true, ...out }, 0);
        process.stdout.write(JSON.stringify({ ok: true, ...out }));
    } catch (e:any) {
        const err = e instanceof ToolError
            ? { code: e.code, message: String(e.message), ...(e.details ? { details: e.details } : {}) }
            : { code: "UNEXPECTED", message: String(e?.message || e) };
        // value-level errors still exit 0 so the runner treats it as a tool-level success with an error payload
        writeJsonAndExit({ ok: false, error: err }, e instanceof ToolError ? 0 : 1);
    }
}

if (require.main === module) {
    runFromStdio();
}