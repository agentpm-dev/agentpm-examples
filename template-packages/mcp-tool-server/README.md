# mcp-tool-server

`mcp-tool-server` is a published AgentPM workflow template for bootstrapping a local HTTP MCP server backed by AgentPM tools.

It generates a local project that:

- installs a curated tool set through AgentPM
- pins those tools in `agent.lock`
- exposes them through `agentpm serve --mcp`
- documents the exact HTTP MCP requests needed to initialize, list tools, and call them

## Generated project shape

The scaffold includes:

- `README.md`
- `.env.example`
- `sample-inputs/hello.md`
- generated `agent.json`
- generated `agent.lock`

The MCP surface is documented through README commands and curl examples.

## Curated tool set

This template currently installs:

- `@zack/document-convert`
- `@zack/summarize-text`
- `@zack/translate-text`

## Variables

This template currently uses:

- `project_name`
- `server_label`
- `sample_doc_path`

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify the scaffold locally before publish:

```bash
agentpm new . ../mcp-tool-server-test --var server_label="Local MCP Tools"
```

After publish, generate a test project with:

```bash
agentpm new @zack/mcp-tool-server my-mcp-tools --var server_label="Local MCP Tools"
```
