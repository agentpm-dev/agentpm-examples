import test from "node:test";
import assert from "node:assert/strict";

import { githubIssues } from "../src/index.js";

function withMockedFetch(mock, fn) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = mock;
  return Promise.resolve(fn()).finally(() => {
    globalThis.fetch = originalFetch;
  });
}

test("list_issues returns normalized issue data", async () => {
  process.env.GITHUB_TOKEN = "test-token";
  await withMockedFetch(async () => {
    return new Response(
      JSON.stringify([
        {
          number: 42,
          title: "Fix docs",
          state: "open",
          body: "docs body",
          html_url: "https://github.com/acme/repo/issues/42",
          labels: [{ name: "docs" }],
          assignees: [{ login: "zack" }],
          user: { login: "alice" },
          created_at: "2026-04-19T00:00:00Z",
          updated_at: "2026-04-20T00:00:00Z"
        }
      ]),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }, async () => {
    const out = await githubIssues({
      action: "list_issues",
      owner: "acme",
      repo: "repo",
      state: "open",
    });
    assert.equal(out.repository, "acme/repo");
    assert.equal(out.issues[0].title, "Fix docs");
    assert.deepEqual(out.issues[0].labels, ["docs"]);
  });
});

test("create_issue sends title, body, and labels", async () => {
  process.env.GITHUB_TOKEN = "test-token";
  let requestBody = null;
  await withMockedFetch(async (_url, options) => {
    requestBody = JSON.parse(options.body);
    return new Response(
      JSON.stringify({
        number: 7,
        title: requestBody.title,
        state: "open",
        body: requestBody.body,
        html_url: "https://github.com/acme/repo/issues/7",
        labels: requestBody.labels.map((name) => ({ name })),
        assignees: [],
        user: { login: "bot" },
      }),
      { status: 201, headers: { "content-type": "application/json" } },
    );
  }, async () => {
    const out = await githubIssues({
      action: "create_issue",
      owner: "acme",
      repo: "repo",
      title: "AgentPM milestone",
      body: "Ship it",
      labels: ["agentpm", "m2"],
    });
    assert.equal(requestBody.title, "AgentPM milestone");
    assert.deepEqual(out.issue.labels, ["agentpm", "m2"]);
  });
});

test("comment_issue normalizes comment output", async () => {
  process.env.GITHUB_TOKEN = "test-token";
  await withMockedFetch(async () => {
    return new Response(
      JSON.stringify({
        id: 99,
        body: "Looks good",
        html_url: "https://github.com/acme/repo/issues/7#issuecomment-99",
        user: { login: "reviewer" },
        created_at: "2026-04-19T00:00:00Z",
        updated_at: "2026-04-19T00:00:00Z",
      }),
      { status: 201, headers: { "content-type": "application/json" } },
    );
  }, async () => {
    const out = await githubIssues({
      action: "comment_issue",
      owner: "acme",
      repo: "repo",
      issue_number: 7,
      body: "Looks good",
    });
    assert.equal(out.comment.author, "reviewer");
    assert.equal(out.metadata.issue_number, 7);
  });
});

test("missing token raises an auth error", async () => {
  delete process.env.GITHUB_TOKEN;
  await assert.rejects(
    () =>
      githubIssues({
        action: "list_issues",
        owner: "acme",
        repo: "repo",
      }),
    /Missing GitHub token/,
  );
});
