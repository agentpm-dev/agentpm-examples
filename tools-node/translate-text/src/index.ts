import OpenAI from "openai";

class ToolError extends Error {
    code: string;
    details?: unknown;
    constructor(code: string, message: string, details?: unknown) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function translate({ text, target_language }: { text: string; target_language: string }) {
    const sys = `You translate succinctly into the requested language. Keep meaning; preserve names; no explanations.`;
    const msg = `Translate into ${target_language}:\n\n${text}`;
    const resp = await client.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "system", content: sys }, { role: "user", content: msg }],
        temperature: 0.2
    });
    return { translated: resp.choices[0]?.message?.content ?? "" };
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
        const out = await translate(input);
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
