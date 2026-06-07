# {{ project_name }}

{{ server_label }} is a local HTTP MCP server generated from the published `@zack/mcp-tool-server` workflow template.

It exposes the tools pinned in this project’s `agent.lock` through:

```bash
agentpm serve --mcp
```

## What this project does

This generated project gives you a ready-to-run MCP workspace for a curated AgentPM tool set:

- `@zack/document-convert`
- `@zack/summarize-text`
- `@zack/translate-text`

The server exposes exactly the tools pinned in `agent.lock`. Tool metadata comes from the installed manifests under `.agentpm/`, and tool execution uses the same shared runtime path as `agentpm run`.

## Setup

```bash
cp .env.example .env.local
agentpm install
```

Set:

- `OPENAI_API_KEY`

`OPENAI_API_KEY` is needed for the model-backed tools in this curated set, such as `summarize-text` and `translate-text`.

Before starting the server, make sure `OPENAI_API_KEY` is actually present in your shell environment. For example:

```bash
set -a
source .env.local
set +a
```

## Start the server

```bash
agentpm serve --mcp
```

By default, the MCP server:

- binds to `127.0.0.1`
- uses port `7331`
- exposes every tool pinned in `agent.lock`

The current MCP surface is HTTP-only.

## HTTP endpoints

The server accepts MCP JSON-RPC requests at:

- `POST /`
- `POST /mcp`

## Example MCP requests

### Initialize

```bash
curl -X POST http://127.0.0.1:7331/ \
  -H 'content-type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'
```

### List tools

```bash
curl -X POST http://127.0.0.1:7331/mcp \
  -H 'content-type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

### Call `document-convert`

For file-backed tools like `document-convert`, use an absolute local path in the MCP request.

```bash
curl -X POST http://127.0.0.1:7331/mcp \
  -H 'content-type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "zack__document_convert",
      "arguments": {
        "path": "/absolute/path/to/{{ sample_doc_path }}",
        "to_format": "markdown"
      }
    }
  }'
```

### Call `summarize-text`

```bash
curl -X POST http://127.0.0.1:7331/mcp \
  -H 'content-type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "zack__summarize_text",
      "arguments": {
        "text": "Summarize this short note about a deployment and the customer impact.",
        "max_words": 80
      }
    }
  }'
```

## Sample local document

The scaffold includes a sample local document at:

```text
{{ sample_doc_path }}
```

Use that file for local `document-convert` MCP calls before you switch to your own source files, but pass it as an absolute path in raw MCP requests.

## Connection guidance

If you want to point Claude, Cursor, or another MCP client at this workspace, the important pieces are:

- command:
  - `agentpm`
- args:
  - `serve --mcp`
- cwd:
  - this generated project directory

The exact client-side config format depends on the MCP client, so this scaffold documents the connection shape rather than checking in a fake universal config file.

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
