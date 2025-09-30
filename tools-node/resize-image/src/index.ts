import { request } from "undici";
import Jimp, { MIME_JPEG } from "jimp";

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
        const out = await resize(input);
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

if (require.main === module) {
    runFromStdio();
}