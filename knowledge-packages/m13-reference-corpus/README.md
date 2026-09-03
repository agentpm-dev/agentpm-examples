# m13-reference-corpus

Unpublished vector Knowledge package used by the Harness Milestone 13 Pinecone/pgvector reference providers.

The corpus is intentionally small and generated for this milestone. It uses real OpenAI `text-embedding-3-small` vectors when prepared locally, but no API keys or provider data are committed.

## Build locally

From this directory:

```bash
export OPENAI_API_KEY=...
python3 scripts/embed_openai.py
agentpm knowledge build
agentpm knowledge inspect .
```

The embedding script reads `knowledge/chunks.jsonl` and writes `knowledge/embeddings/default.f32`. `agentpm knowledge build` then writes local index/build metadata from the installed package artifacts.

## External provider setup

Use this package with the sibling [`m13-reference-providers`](../m13-reference-providers/) examples. The providers expect external rows/vectors to carry this package identity:

- package: `@zack/m13-reference-corpus`
- version: `0.1.0`
- corpus hash: the `knowledge.corpus.content_hash` value after `agentpm knowledge build`

If `agentpm knowledge build` updates that corpus hash, update provider environment/configuration before launching Harness. The Harness should suppress a mapped custom Knowledge surface when the provider cannot attest the exact installed package/corpus identity.
