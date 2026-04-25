import test from "node:test";
import assert from "node:assert/strict";

import { slackPostMessage } from "../src/index.js";

function withMockedFetch(mock, fn) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = mock;
  return Promise.resolve(fn()).finally(() => {
    globalThis.fetch = originalFetch;
  });
}

test("post_message returns normalized Slack message data", async () => {
  process.env.SLACK_BOT_TOKEN = "xoxb-test";
  await withMockedFetch(async (_url, options) => {
    const body = JSON.parse(options.body);
    assert.equal(body.channel, "C123");
    assert.equal(body.thread_ts, "123.456");
    return new Response(
      JSON.stringify({
        ok: true,
        channel: "C123",
        ts: "111.222",
        message: {
          text: body.text,
          blocks: body.blocks,
          user: "U123",
        },
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }, async () => {
    const out = await slackPostMessage({
      action: "post_message",
      channel: "C123",
      text: "AgentPM milestone 2",
      thread_ts: "123.456",
      blocks: [{ type: "section", text: { type: "mrkdwn", text: "Milestone 2" } }],
    });
    assert.equal(out.channel, "C123");
    assert.equal(out.ts, "111.222");
    assert.equal(out.metadata.threaded, true);
  });
});

test("update_message requires ts and returns normalized output", async () => {
  process.env.SLACK_BOT_TOKEN = "xoxb-test";
  await withMockedFetch(async (_url, options) => {
    const body = JSON.parse(options.body);
    assert.equal(body.ts, "111.222");
    return new Response(
      JSON.stringify({
        ok: true,
        channel: "C123",
        ts: "111.222",
        message: { text: body.text, blocks: [], user: "U123" },
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  }, async () => {
    const out = await slackPostMessage({
      action: "update_message",
      channel: "C123",
      ts: "111.222",
      text: "Updated status",
    });
    assert.equal(out.metadata.updated, true);
    assert.equal(out.message.text, "Updated status");
  });
});

test("missing token raises an auth error", async () => {
  delete process.env.SLACK_BOT_TOKEN;
  await assert.rejects(
    () =>
      slackPostMessage({
        action: "post_message",
        channel: "C123",
        text: "hello",
      }),
    /Missing Slack bot token/,
  );
});
