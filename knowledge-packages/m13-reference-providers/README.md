# Harness M13 KnowledgeRuntime reference providers

Reference process providers for Harness Milestone 13:

- Pinecone full `KnowledgeRuntime`
- PostgreSQL/pgvector full `KnowledgeRuntime`

These examples intentionally live outside Harness core. They speak the public `agentpm-service` JSONL process protocol through SDK helpers and can be launched from `agentpm.harness.json` as custom Knowledge runtimes.

## Shared contract

Both providers:

- accept normalized AgentPM `KnowledgeRuntimeRequest` objects;
- advertise `modes`, `features`, and exact package/version/corpus attestations during process initialization;
- return normalized AgentPM `KnowledgeRuntimeResult` objects;
- require explicit `knowledge.packages` mapping in Harness config;
- do not fall back to local Knowledge when the external runtime fails;
- keep provider credentials in the provider process environment.

The providers advertise only caller-exercisable capabilities. They use fixed package/version/corpus filters internally to enforce attestation, but they do not advertise a generic `metadata_filter` feature because the current KnowledgeRuntime request contract has no caller metadata-filter field.

Required shared env:

```bash
export AGENTPM_KNOWLEDGE_PACKAGE=@zack/m13-reference-corpus
export AGENTPM_KNOWLEDGE_VERSION=0.1.0
export AGENTPM_KNOWLEDGE_CORPUS_HASH=sha256:... # from agent.json knowledge.corpus.content_hash after build
# Optional. Defaults to true to match this corpus's knowledge.retrieval.return_citations.
export AGENTPM_KNOWLEDGE_RETURN_CITATIONS=true
export AGENTPM_EMBEDDING_PROVIDER=openai
export AGENTPM_EMBEDDING_MODEL=text-embedding-3-small
export OPENAI_API_KEY=...
```

Set `AGENTPM_KNOWLEDGE_RUNTIME_ID` to the runtime you are launching:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID=pinecone-reference
# or
export AGENTPM_KNOWLEDGE_RUNTIME_ID=pgvector-reference
```

## Prepare the example corpus

```bash
cd ../m13-reference-corpus
export OPENAI_API_KEY=...
python3 scripts/embed_openai.py
agentpm knowledge build
jq -r '.knowledge.corpus.content_hash' agent.json
```

Use the built `knowledge.corpus.content_hash` value from `agent.json` as `AGENTPM_KNOWLEDGE_CORPUS_HASH`. As an optional cross-check, the same value should appear as `source_corpus_hash` in `knowledge/indexes/default/metadata.json`.

Do not use the `Vectors hash` shown by `agentpm knowledge inspect`; that identifies the vector artifact bytes, not the corpus identity used for provider attestation.

## Local SDK before publish

These providers are written against the real public SDK packages. While Milestone 13 is still unpublished, the published npm package may not yet include `serveKnowledgeRuntimeProcess`. From this directory, build and link the sibling SDK checkout for local pre-publish testing:

```bash
cd ../../../agentpm-sdk-node
pnpm build

cd ../agentpm-examples/knowledge-packages/m13-reference-providers
pnpm link ../../../agentpm-sdk-node
```

The published Python package may also not yet include `serve_knowledge_runtime_process`. From this directory, run Python provider commands with the sibling SDK checkout injected by `uv`:

```bash
uv run --with-editable ../../../agentpm-sdk-python python providers/python/pinecone_runtime.py
uv run --with-editable ../../../agentpm-sdk-python --extra pgvector python providers/python/pgvector_runtime.py
```

After the SDK release that includes `serveKnowledgeRuntimeProcess` is published, remove the local link and install normally:

```bash
pnpm install
uv sync
```

## Harness workspace

The `harness-workspace/` directory is a local agent workspace for end-to-end Harness checks. It contains:

- `agent.json`, a local Agent that binds `@zack/m13-reference-corpus`;
- `loops/m13-reference-loop/agent.json`, a small local loop with Knowledge access;
- `scripts/prepare_workspace.py`, which installs the built corpus and loop into the workspace-local `.agentpm/` layout.

Prepare it after building the corpus. From this directory:

```bash
cd harness-workspace
python3 scripts/prepare_workspace.py
```

Harness config examples live in `harness-configs/`:

| Config                                           | Runtime                                                         |
| ------------------------------------------------ | --------------------------------------------------------------- |
| `pinecone-node.agentpm.harness.json`             | Pinecone Node provider with published/local-linked Node SDK     |
| `pinecone-python.agentpm.harness.json`           | Pinecone Python provider with published Python SDK              |
| `pinecone-python.local-dev.agentpm.harness.json` | Pinecone Python provider with sibling local Python SDK checkout |
| `pgvector-node.agentpm.harness.json`             | pgvector Node provider with published/local-linked Node SDK     |
| `pgvector-python.agentpm.harness.json`           | pgvector Python provider with published Python SDK              |
| `pgvector-python.local-dev.agentpm.harness.json` | pgvector Python provider with sibling local Python SDK checkout |

Harness projects only the variable names listed in each runtime `env` array from the Harness process environment into the provider process. Do not put literal secret values in `agentpm.harness.json`.

Run preflight from `harness-workspace/`:

```bash
agentpm harness --config ../harness-configs/pinecone-node.agentpm.harness.json --verbose
```

Run a headless smoke test:

```bash
agentpm harness --config ../harness-configs/pinecone-node.agentpm.harness.json \
  --headless \
  --input "Use @zack/m13-reference-corpus Knowledge. Run a vector query for alpha launch checklist and answer with the top chunk id and source title."
```

## Pinecone

Prepare an index outside Harness, then upsert the built corpus:

```bash
cd ../m13-reference-providers
export PINECONE_API_KEY=...
export PINECONE_INDEX_HOST=https://YOUR_INDEX_HOST
export PINECONE_NAMESPACE=agentpm-m13
python3 scripts/upsert_pinecone.py ../m13-reference-corpus
```

Run the Node process provider:

```bash
pnpm install
pnpm pinecone:node
```

If you are testing before the SDK release containing `serveKnowledgeRuntimeProcess` is published, use the local Node SDK link commands from [Local SDK before publish](#local-sdk-before-publish) first.

Run the Python process provider:

```bash
uv run python providers/python/pinecone_runtime.py
```

If you are testing before the SDK release containing `serve_knowledge_runtime_process` is published, use the local Python SDK override command from [Local SDK before publish](#local-sdk-before-publish) instead.

Use the Pinecone configs in `harness-configs/` for full Harness runs.

## pgvector

The local compose file uses host port `55432` to avoid colliding with the AgentPM API development database.

```bash
docker compose -f docker-compose.pgvector.yml up -d
export PGVECTOR_DATABASE_URL=postgresql://postgres:postgres@localhost:55432/postgres
uv run --extra pgvector python scripts/load_pgvector.py ../m13-reference-corpus --create-schema
```

Run the Node process provider:

```bash
pnpm install
pnpm pgvector:node
```

If you are testing before the SDK release containing `serveKnowledgeRuntimeProcess` is published, use the local Node SDK link commands from [Local SDK before publish](#local-sdk-before-publish) first.

Run the Python process provider:

```bash
uv run python providers/python/pgvector_runtime.py
```

If you are testing before the SDK release containing `serve_knowledge_runtime_process` is published, use the local Python SDK override command from [Local SDK before publish](#local-sdk-before-publish) instead.

Use the pgvector configs in `harness-configs/` for full Harness runs. Add `PGVECTOR_TABLE` to the matching config `env` only if you used a non-default table name.

## Tests

Mocked mapping tests do not require OpenAI, Pinecone, or PostgreSQL:

```bash
pnpm test:node
uv run pytest
```

Live provider tests are intentionally environment-gated; run them only after preparing external infrastructure.

```bash
export AGENTPM_M13_LIVE_PROVIDER_COMMAND=node
export AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON='["providers/node/pgvector-runtime.mjs"]'
pnpm test:node
```
