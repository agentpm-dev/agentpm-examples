# agentpm-docs

`agentpm-docs` is a publishable AgentPM Knowledge package built from the public AgentPM documentation corpus.

It is intentionally the larger, pipeline-driven Knowledge example in this repo. The point of this package is to show how real content can be copied, normalized, chunked, sourced, embedded, and then packaged into the AgentPM `mode: "vector"` shape.

This package includes:
- copied source docs under `knowledge/source-docs/v0.1/`
- generated `knowledge/chunks.jsonl`
- generated `knowledge/sources.jsonl`
- generated `knowledge/provenance/sources-manifest.json`
- a canonical raw float32 vectors file at `knowledge/embeddings/default.f32`
- build-generated local index metadata after `agentpm knowledge build`

## Corpus prep workflow

The scripts in `scripts/` are the reproducible corpus-prep pipeline for this package:

- `scripts/build_corpus.py`
  - copies `agentpm-api/docs/v0.1/**/*.mdx`
  - strips frontmatter for chunk text
  - uses `langchain-text-splitters` for header-aware Markdown splitting plus recursive chunking
  - preserves source traceability
  - emits AgentPM-compatible `chunks.jsonl`, `sources.jsonl`, and provenance metadata
- `scripts/openai_embeddings.py`
  - generates `text-embedding-3-small` vectors for the chunk corpus
  - can also generate query JSON or act as an `--embedding-command` adapter for `agentpm knowledge query`

## Local development

From this directory:

```bash
uv pip install langchain-text-splitters
python3 scripts/build_corpus.py
export OPENAI_API_KEY=...
python3 scripts/openai_embeddings.py chunks-to-f32 \
  --chunks knowledge/chunks.jsonl \
  --output knowledge/embeddings/default.f32
agentpm knowledge build
agentpm knowledge inspect .
agentpm publish --dry-run
```

If you are not using `uv`, the equivalent install step is:

```bash
python3 -m pip install langchain-text-splitters
```

This keeps the final package in AgentPM's expected JSONL/vector shape, while showing a corpus-prep workflow that is closer to what many teams already use in retrieval pipelines.

## Query demo

After build, you can generate a matching query vector:

```bash
export OPENAI_API_KEY=...
  python3 scripts/openai_embeddings.py query-to-json \
    --text "How do I scaffold and test an AgentPM template package?" \
    --output knowledge/query.json

agentpm knowledge query . --vector-json knowledge/query.json --top-k 5 --include-text
```

Or use the adapter path:

```bash
agentpm knowledge query . "How do I scaffold and test an AgentPM template package?" \
  --embedding-command "python3 scripts/openai_embeddings.py adapter" \
  --top-k 5 \
  --include-text
```

The source for this Knowledge package can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/knowledge-packages/agentpm-docs).
