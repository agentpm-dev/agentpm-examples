import { fetch, ProxyAgent } from "undici";

class ToolError extends Error {
    code: string;
    details?: unknown;
    constructor(code: string, message: string, details?: unknown) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

type ResponseType = "auto" | "text" | "json" | "bytes";

interface HttpFetchInput {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    body?: string;
    timeout_ms?: number;
    follow_redirects?: boolean;
    max_bytes?: number;
    response_type?: ResponseType;
}

interface HttpFetchOutput {
    status: number;
    status_text?: string;
    url_final?: string;
    headers: Record<string, string>;
    content_type?: string;
    body_text?: string;
    body_json?: unknown;
    body_base64?: string;
    truncated?: boolean;
}

function normalizeMethod(method?: string): string {
    return (method || "GET").toUpperCase();
}

function normalizeHeaders(headers?: Record<string, string>): Record<string, string> {
    const out: Record<string, string> = {};
    if (!headers) return out;
    for (const [k, v] of Object.entries(headers)) {
        if (typeof v === "string") {
            out[k] = v;
        } else if (v != null) {
            out[k] = String(v);
        }
    }
    return out;
}

function guessResponseKind(responseType: ResponseType, contentType: string | null): ResponseType {
    if (responseType !== "auto") return responseType;
    const ct = (contentType || "").toLowerCase();
    if (ct.includes("application/json") || ct.endsWith("+json")) return "json";
    if (
        ct.startsWith("text/") ||
        ct.includes("application/xml") ||
        ct.includes("application/xhtml") ||
        ct.includes("application/javascript") ||
        ct.includes("application/x-javascript")
    ) {
        return "text";
    }
    return "bytes";
}

export async function httpFetch(input: HttpFetchInput): Promise<HttpFetchOutput> {
    const {
        url,
        method,
        headers,
        body,
        timeout_ms = 30_000,
        follow_redirects = true,
        max_bytes = 1_048_576,
        response_type = "auto",
    } = input;

    if (!url || typeof url !== "string") {
        throw new ToolError("INPUT_INVALID", "Missing or invalid 'url' field", { field: "url" });
    }

    let parsedUrl: URL;
    try {
        parsedUrl = new URL(url);
    } catch {
        throw new ToolError("INPUT_INVALID", "Invalid URL", { url });
    }

    if (typeof timeout_ms !== "number" || timeout_ms <= 0) {
        throw new ToolError("INPUT_INVALID", "timeout_ms must be a positive integer", { timeout_ms });
    }
    if (typeof max_bytes !== "number" || max_bytes <= 0) {
        throw new ToolError("INPUT_INVALID", "max_bytes must be a positive integer", { max_bytes });
    }

    const methodNorm = normalizeMethod(method);
    const headersNorm = normalizeHeaders(headers);

    // Default User-Agent if not provided
    if (!Object.keys(headersNorm).some(k => k.toLowerCase() === "user-agent")) {
        const ua = process.env.HTTP_FETCH_DEFAULT_USER_AGENT || "agentpm-http-fetch/0.1";
        headersNorm["User-Agent"] = ua;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeout_ms);

    let dispatcher: ProxyAgent | undefined;
    const proxyUrl = process.env.HTTP_FETCH_PROXY_URL;
    if (proxyUrl) {
        dispatcher = new ProxyAgent(proxyUrl);
    }

    try {
        const res = await fetch(parsedUrl.toString(), {
            method: methodNorm,
            headers: headersNorm,
            body: body !== undefined ? body : undefined,
            redirect: follow_redirects ? "follow" : "manual",
            signal: controller.signal,
            dispatcher,
        });

        const headersObj: Record<string, string> = {};
        for (const [k, v] of res.headers) {
            headersObj[k] = v;
        }

        const contentType = res.headers.get("content-type") || undefined;

        const arrayBuf = await res.arrayBuffer();
        let buf = Buffer.from(arrayBuf);
        let truncated = false;
        if (buf.length > max_bytes) {
            buf = buf.subarray(0, max_bytes);
            truncated = true;
        }

        const kind = guessResponseKind(response_type, contentType || null);
        const out: HttpFetchOutput = {
            status: res.status,
            status_text: res.statusText || undefined,
            url_final: res.url || undefined,
            headers: headersObj,
            content_type: contentType,
            truncated: truncated || undefined,
        };

        if (kind === "bytes") {
            out.body_base64 = buf.toString("base64");
        } else {
            // Try to decode as UTF-8 text
            const text = buf.toString("utf8");
            if (kind === "json") {
                try {
                    out.body_json = text ? JSON.parse(text) : null;
                } catch (e) {
                    throw new ToolError("RESPONSE_NOT_JSON", "Response was not valid JSON", {
                        url,
                        status: res.status,
                        content_type: contentType,
                        parse_error: String((e as any)?.message || e),
                    });
                }
            } else {
                out.body_text = text;
            }
        }

        return out;
    } catch (e: any) {
        if (e?.name === "AbortError") {
            throw new ToolError("TIMEOUT", "Request timed out", { url, timeout_ms });
        }
        throw new ToolError("REQUEST_FAILED", "HTTP request failed", {
            url,
            method: methodNorm,
            message: String(e?.message || e),
        });
    } finally {
        clearTimeout(timeout);
    }
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
        const out = await httpFetch(input);
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