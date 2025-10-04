## Node Agent

### What it does
A **LangChain (Node)** agent that loads tools from AgentPM and orchestrates a “research assistant” flow:
1) Scrape Wikipedia
2) Summarize (OpenAI)
3) Translate (OpenAI)
4) Sentiment
5) Resize first image


### Key differences vs Python agent
- Uses **OpenAI Tools Agent** (function calling) + **StructuredTool** wrappers.
- Tool **schemas are dynamic**: converts each tool’s `meta.inputs` (JSON Schema) → **Zod** at runtime so the LLM always emits valid JSON args.

### AgentPM & tools
- `"kind": "agent"`
- Tools are **installed via AgentPM** and loaded dynamically in code (see `agent.json` and `src/main.ts`).
- Tools are loaded and run via the Node SDK `"@agentpm/sdk": "^0.1.2",`

Example install:
```bash
agentpm install @zack/wikipedia-scrape@0.1.1
agentpm install @zack/summarize-text@0.1.3
agentpm install @zack/translate-text@0.1.0
agentpm install @zack/sentiment-analysis@0.1.1
agentpm install @zack/resize-image@0.1.4
```
or
```bash
# tools already defined in agent.json
agentpm install
```

### Quirks
- Requires `@langchain/core@^0.2`, `langchain@^0.2`, `@langchain/openai@^0.3`, and `zod`.
- The SDK runner streams child output, detects first JSON, and applies a **graceful TERM→KILL** if the child doesn’t exit quickly.
- Python tool subprocesses are run with `-u` (unbuffered) to reduce lag.

### Setup & run
```bash
pnpm --dir agent-app-node install

pnpm -w add langchain@^0.2 @langchain/core@^0.2 @langchain/openai@^0.3 -F agent-app-node

pnpm --dir agent-app-node add -D dotenv-cli

# load env inline and run
pnpm --dir agent-app-node exec dotenv -e .env.local -- pnpm  dev
```

### Example output
```text
Loading tools from AgentPM…
🔗 Agent start (b2064983-168f-4d38-bf3f-559e54f8911f)
🔗 Agent start (b2064983-168f-4d38-bf3f-559e54f8911f)
🤖 LLM start: System: You are a helpful assistant
Human: Given this Wikipedia URL, scrape it, summarize in <= 150 words, translate the summary to Spanish,…
🤖 LLM end
🛠️ wikipedia-scrape ← {"url":"https://en.wikipedia.org/wiki/Alan_Turing"}
✅ tool → {"ok":true,"title":"Alan Turing","text":"Alan Mathison Turing (/ˈtjʊərɪŋ/; 23 June 1912 – 7 June 1954) was an English mathematician, computer scientist, logician, cryptanalyst, philosopher and theoretical biologist.[6] He was highly influen (697ms)
🤖 LLM start: System: You are a helpful assistant
Human: Given this Wikipedia URL, scrape it, summarize in <= 150 words, translate the summary to Spanish,…
🤖 LLM end
🛠️ sentiment-analysis ← {"text":"Alan Mathison Turing (23 June 1912 – 7 June 1954) was an English mathematician, computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist. He was highly influential i
🛠️ summarize-text ← {"text":"Alan Mathison Turing (23 June 1912 – 7 June 1954) was an English mathematician, computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist. He was highly influential i
🛠️ translate-text ← {"text":"Alan Mathison Turing (23 June 1912 – 7 June 1954) was an English mathematician, computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist. He was highly influential i
🛠️ resize-image ← {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Alan_turing_header.jpg/250px-Alan_turing_header.jpg","width":32,"height":32}
✅ tool → {"ok":true,"label":"negative","scores":{"neg":0.135,"neu":0.768,"pos":0.097,"compound":-0.791}} (114ms)
✅ tool → {"ok":true,"image_base64_jpeg":"/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAf/A (480ms)
✅ tool → {"ok":true,"summary":"Alan Turing (23 June 1912 – 7 June 1954) was a pivotal English mathematician and computer scientist known for his foundational work in theoretical computer science. He introduced the concepts of algorithms and computat (5635ms)
✅ tool → {"ok":true,"translated":"Alan Mathison Turing (23 de junio de 1912 – 7 de junio de 1954) fue un matemático, científico de la computación, lógico, criptanalista, filósofo y biólogo teórico inglés. Tuvo una gran influencia en el desarrollo de (8718ms)
🤖 LLM start: System: You are a helpful assistant
Human: Given this Wikipedia URL, scrape it, summarize in <= 150 words, translate the summary to Spanish,…

🤖 LLM end
🔗 Agent end (b2064983-168f-4d38-bf3f-559e54f8911f)
🔗 Agent end (b2064983-168f-4d38-bf3f-559e54f8911f)

=== FINAL ANSWER ===
 ```json
{
  "title": "Alan Turing",
  "summary_en": "Alan Turing (23 June 1912 – 7 June 1954) was a pivotal English mathematician and computer scientist ... the injustices he faced during his lifetime.",
  "summary_es": "Alan Mathison Turing (23 de junio de 1912 – 7 de junio de 1954) fue un matemático, científico de la computación, ... o póstumo del gobierno británico por su condena por indecencia grave.",
  "sentiment_label": "negative",
  "resized_image_base64_prefix": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCE.../2Q=="
}
```