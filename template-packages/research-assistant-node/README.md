# research-assistant-node

`research-assistant-node` is a published AgentPM workflow template for bootstrapping a Node SDK research assistant project.

It generates a local project that:

- installs the declared research tools through AgentPM
- loads those installed tools with the Node SDK
- runs an interactive OpenAI-powered research console
- keeps the generated `agent.json` editable so users can change the tool set later

## Generated project shape

The scaffold includes:

- `README.md`
- `.env.example`
- `package.json`
- `tsconfig.json`
- `src/main.ts`
- `test/main.test.js`

The generated root `agent.json` is synthesized by `agentpm new` from the template dependency declarations.

## Tool set

This template currently installs:

- `@zack/web-page-extract`
- `@zack/robots-aware-crawl`
- `@zack/document-convert`
- `@zack/table-extract`
- `@zack/markdown-chunk`
- `@zack/summarize-text`
- `@zack/translate-text`

## Local development

From this template package directory:

```bash
agentpm lint
```

To verify the scaffold locally before publish:

```bash
agentpm new . ../research-assistant-node-test
```

After publish, generate a test project with:

```bash
agentpm new @zack/research-assistant-node my-research-app
```
