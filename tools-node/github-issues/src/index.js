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

function requireIssueNumber(value) {
  if (!Number.isInteger(value) || value < 1) {
    throw new ToolError("INPUT_INVALID", "issue_number must be a positive integer", {
      field: "issue_number",
    });
  }
  return value;
}

function getBaseUrl() {
  return (process.env.GITHUB_API_BASE_URL || "https://api.github.com").replace(/\/+$/, "");
}

function getToken(inputToken) {
  const token = inputToken || process.env.GITHUB_TOKEN;
  if (!token) {
    throw new ToolError("AUTH_MISSING", "Missing GitHub token", {
      env_var: "GITHUB_TOKEN",
    });
  }
  return token;
}

function githubHeaders(token) {
  return {
    "accept": "application/vnd.github+json",
    "authorization": `Bearer ${token}`,
    "user-agent": "agentpm-github-issues/0.1",
    "x-github-api-version": "2022-11-28",
    "content-type": "application/json",
  };
}

function normalizeIssue(issue) {
  return {
    number: issue.number,
    title: issue.title,
    state: issue.state,
    body: issue.body ?? null,
    url: issue.html_url,
    labels: Array.isArray(issue.labels)
      ? issue.labels.map((label) => (typeof label === "string" ? label : label.name)).filter(Boolean)
      : [],
    assignees: Array.isArray(issue.assignees) ? issue.assignees.map((assignee) => assignee.login) : [],
    author: issue.user?.login ?? null,
    created_at: issue.created_at ?? null,
    updated_at: issue.updated_at ?? null,
  };
}

function normalizeComment(comment) {
  return {
    id: comment.id,
    body: comment.body ?? "",
    url: comment.html_url,
    author: comment.user?.login ?? null,
    created_at: comment.created_at ?? null,
    updated_at: comment.updated_at ?? null,
  };
}

async function githubRequest(path, { method = "GET", body, token }) {
  const response = await fetch(`${getBaseUrl()}${path}`, {
    method,
    headers: githubHeaders(token),
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { message: text };
    }
  }

  if (!response.ok) {
    throw new ToolError("GITHUB_API_ERROR", payload?.message || `GitHub API request failed with ${response.status}`, {
      status: response.status,
      path,
    });
  }

  return payload;
}

export async function githubIssues(input) {
  const action = requireString(input?.action, "action");
  const owner = requireString(input?.owner, "owner");
  const repo = requireString(input?.repo, "repo");
  const token = getToken(input?.token);
  const repository = `${owner}/${repo}`;

  switch (action) {
    case "list_issues": {
      const state = input?.state || "open";
      const perPage = Number.isInteger(input?.per_page) ? input.per_page : 20;
      const payload = await githubRequest(
        `/repos/${owner}/${repo}/issues?state=${encodeURIComponent(state)}&per_page=${perPage}`,
        { token },
      );
      return {
        action,
        repository,
        issues: Array.isArray(payload) ? payload.map(normalizeIssue) : [],
        metadata: { state, per_page: perPage },
      };
    }
    case "get_issue": {
      const issueNumber = requireIssueNumber(input?.issue_number);
      const payload = await githubRequest(`/repos/${owner}/${repo}/issues/${issueNumber}`, { token });
      return {
        action,
        repository,
        issue: normalizeIssue(payload),
        metadata: { issue_number: issueNumber },
      };
    }
    case "create_issue": {
      const title = requireString(input?.title, "title");
      const body = typeof input?.body === "string" ? input.body : "";
      const labels = Array.isArray(input?.labels) ? input.labels.filter((label) => typeof label === "string") : [];
      const payload = await githubRequest(`/repos/${owner}/${repo}/issues`, {
        method: "POST",
        body: { title, body, labels },
        token,
      });
      return {
        action,
        repository,
        issue: normalizeIssue(payload),
        metadata: { labels },
      };
    }
    case "comment_issue": {
      const issueNumber = requireIssueNumber(input?.issue_number);
      const body = requireString(input?.body, "body");
      const payload = await githubRequest(`/repos/${owner}/${repo}/issues/${issueNumber}/comments`, {
        method: "POST",
        body: { body },
        token,
      });
      return {
        action,
        repository,
        comment: normalizeComment(payload),
        metadata: { issue_number: issueNumber },
      };
    }
    case "update_issue_state": {
      const issueNumber = requireIssueNumber(input?.issue_number);
      const state = requireString(input?.state, "state");
      if (!["open", "closed"].includes(state)) {
        throw new ToolError("INPUT_INVALID", "state must be open or closed", { field: "state" });
      }
      const payload = await githubRequest(`/repos/${owner}/${repo}/issues/${issueNumber}`, {
        method: "PATCH",
        body: { state },
        token,
      });
      return {
        action,
        repository,
        issue: normalizeIssue(payload),
        metadata: { issue_number: issueNumber, state },
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
    const output = await githubIssues(input);
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
