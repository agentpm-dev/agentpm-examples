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

function requireString(value, field) {
  if (typeof value !== "string" || !value.trim()) {
    throw new ToolError("INPUT_INVALID", `Missing or invalid '${field}' field`, { field });
  }
  return value.trim();
}

function getToken() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) {
    throw new ToolError("AUTH_MISSING", "Missing Slack bot token", {
      env_var: "SLACK_BOT_TOKEN",
    });
  }
  return token;
}

function getBaseUrl() {
  return (process.env.SLACK_API_BASE_URL || "https://slack.com/api").replace(/\/+$/, "");
}

function slackHeaders(token) {
  return {
    "authorization": `Bearer ${token}`,
    "content-type": "application/json; charset=utf-8",
  };
}

function normalizeSlackMessage(payload) {
  return {
    text: payload.message?.text ?? payload.text ?? "",
    blocks: payload.message?.blocks ?? payload.blocks ?? [],
    user: payload.message?.user ?? payload.user ?? null,
  };
}

async function slackRequest(endpoint, { token, body }) {
  const response = await fetch(`${getBaseUrl()}/${endpoint}`, {
    method: "POST",
    headers: slackHeaders(token),
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new ToolError("SLACK_API_ERROR", payload.error || `Slack API request failed with ${response.status}`, {
      endpoint,
      status: response.status,
    });
  }
  return payload;
}

export async function slackPostMessage(input) {
  const action = requireString(input?.action, "action");
  const channel = requireString(input?.channel, "channel");
  const text = requireString(input?.text, "text");
  const token = getToken();
  const blocks = Array.isArray(input?.blocks) ? input.blocks : undefined;

  switch (action) {
    case "post_message": {
      const payload = await slackRequest("chat.postMessage", {
        token,
        body: {
          channel,
          text,
          ...(input?.thread_ts ? { thread_ts: input.thread_ts } : {}),
          ...(blocks ? { blocks } : {}),
        },
      });
      return {
        action,
        channel: payload.channel,
        ts: payload.ts,
        message: normalizeSlackMessage(payload),
        metadata: { threaded: Boolean(input?.thread_ts) },
      };
    }
    case "update_message": {
      const ts = requireString(input?.ts, "ts");
      const payload = await slackRequest("chat.update", {
        token,
        body: {
          channel,
          ts,
          text,
          ...(blocks ? { blocks } : {}),
        },
      });
      return {
        action,
        channel: payload.channel,
        ts: payload.ts,
        message: normalizeSlackMessage(payload),
        metadata: { updated: true },
      };
    }
    default:
      throw new ToolError("INPUT_INVALID", `Unsupported action: ${action}`, { action });
  }
}

async function main() {
  try {
    const raw = await readStdin();
    const input = raw.trim() ? JSON.parse(raw) : {};
    const output = await slackPostMessage(input);
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
