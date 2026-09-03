# Harness M13 manual verification

This is a temporary/manual checklist for validating the Milestone 13 Pinecone and pgvector reference `KnowledgeRuntime` providers end to end.

Run commands from the `agentpm-examples` repo root unless a step explicitly says otherwise.

## 0. Shell setup

```bash
export APM="${APM:-$(pwd)/../agentpm/target/debug/agentpm}"
export PROVIDERS="knowledge-packages/m13-reference-providers"
export CORPUS="knowledge-packages/m13-reference-corpus"
export WORKSPACE="$PROVIDERS/harness-workspace"
export RUNS="$PROVIDERS/manual-runs"
mkdir -p "$RUNS"
```

If the local CLI has not been built yet:

```bash
(cd ../agentpm && cargo build)
```

For pre-publish SDK testing, use the local SDKs.

Node:

```bash
(cd ../agentpm-sdk-node && pnpm build)
(cd "$PROVIDERS" && pnpm install && pnpm link ../../../agentpm-sdk-node)
```

Python commands below use `--with-editable ../../../agentpm-sdk-python` for provider runtime configs where needed.

## 1. Run mocked provider tests

These do not require OpenAI, Pinecone, or PostgreSQL.

```bash
(cd "$PROVIDERS" && pnpm test:node)
(cd "$PROVIDERS" && uv run pytest test/)
```

Expected:

- Node tests pass, with the live provider test skipped unless `AGENTPM_M13_LIVE_PROVIDER_COMMAND` is set.
- Python tests collect and pass without requiring the unpublished SDK helper at import time.

## 2. Build the real vector corpus

Requires `OPENAI_API_KEY`.

```bash
export OPENAI_API_KEY="..."

(cd "$CORPUS" && python3 scripts/embed_openai.py)
(cd "$CORPUS" && "$APM" knowledge build)

export AGENTPM_KNOWLEDGE_PACKAGE="@zack/m13-reference-corpus"
export AGENTPM_KNOWLEDGE_VERSION="0.1.0"
export AGENTPM_KNOWLEDGE_CORPUS_HASH="$(jq -r '.knowledge.corpus.content_hash' "$CORPUS/agent.json")"
export AGENTPM_KNOWLEDGE_RETURN_CITATIONS="true"
export AGENTPM_EMBEDDING_PROVIDER="openai"
export AGENTPM_EMBEDDING_MODEL="text-embedding-3-small"
export AGENTPM_EMBEDDING_DIMENSIONS="1536"

echo "$AGENTPM_KNOWLEDGE_CORPUS_HASH"
```

Expected:

- `agent.json` has `knowledge.corpus.content_hash`.
- `knowledge/indexes/default/metadata.json` has the same value in `source_corpus_hash`.
- Do not use `knowledge.embedding.vectors_hash` as the corpus attestation hash.

Optional check:

```bash
test "$AGENTPM_KNOWLEDGE_CORPUS_HASH" = "$(jq -r '.source_corpus_hash' "$CORPUS/knowledge/indexes/default/metadata.json")"
```

## 3. Load Pinecone

Skip this load step if you have already upserted the current built corpus into Pinecone. In that case, just confirm these env vars are set before continuing:

```bash
export PINECONE_API_KEY="..."
export PINECONE_INDEX_HOST="https://YOUR_INDEX_HOST"
export PINECONE_NAMESPACE="agentpm-m13"
```

Prerequisites:

- Pinecone index exists.
- Index dimensions are `1536`.
- Metric is compatible with the corpus embedding space.
- `PINECONE_INDEX_HOST` is the index host URL, not the console URL.

```bash
export PINECONE_API_KEY="..."
export PINECONE_INDEX_HOST="https://YOUR_INDEX_HOST"
export PINECONE_NAMESPACE="agentpm-m13"

python3 "$PROVIDERS/scripts/upsert_pinecone.py" "$CORPUS"
```

Expected:

- Script prints `Upserted 4 vectors into Pinecone`.
- Pinecone namespace may be created implicitly by upsert.

## 4. Load pgvector

Skip this load step if you have already loaded the current built corpus into pgvector. In that case, just confirm this env var is set before continuing:

```bash
export PGVECTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55432/postgres"
```

The compose file uses host port `55432` to avoid colliding with the AgentPM API development database.

```bash
(cd "$PROVIDERS" && docker compose -f docker-compose.pgvector.yml up -d)
export PGVECTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55432/postgres"

(cd "$PROVIDERS" && uv run --extra pgvector python scripts/load_pgvector.py ../m13-reference-corpus --create-schema)
```

Expected:

- Script prints `Loaded 4 chunks into agentpm_m13_knowledge_chunks`.

Optional database check:

```bash
(cd "$PROVIDERS" && docker compose -f docker-compose.pgvector.yml exec -T postgres \
  psql -U postgres -d postgres \
  -c "select package_name, package_version, corpus_hash, count(*) from agentpm_m13_knowledge_chunks group by 1,2,3;")
```

## 5. Prepare the Harness workspace

```bash
(cd "$WORKSPACE" && python3 scripts/prepare_workspace.py)
```

Expected:

- Corpus installed under `$WORKSPACE/.agentpm/knowledge/zack/m13-reference-corpus/0.1.0`.
- Loop installed under `$WORKSPACE/.agentpm/loops/zack/m13-reference-loop/0.1.0`.
- `$WORKSPACE/agent.lock` regenerated.

## 6. Preflight each runtime config

The Node configs use the locally linked Node SDK if you ran the link step above. The Python `.local-dev` configs inject the sibling Python SDK checkout.

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$WORKSPACE" && "$APM" harness --config ../harness-configs/pinecone-node.agentpm.harness.json --verbose) \
  | tee "$RUNS/preflight-pinecone-node.txt"

export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$WORKSPACE" && "$APM" harness --config ../harness-configs/pinecone-python.local-dev.agentpm.harness.json --verbose) \
  | tee "$RUNS/preflight-pinecone-python.txt"

export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness --config ../harness-configs/pgvector-node.agentpm.harness.json --verbose) \
  | tee "$RUNS/preflight-pgvector-node.txt"

export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness --config ../harness-configs/pgvector-python.local-dev.agentpm.harness.json --verbose) \
  | tee "$RUNS/preflight-pgvector-python.txt"
```

Expected:

- Status is `Ready`.
- Static capabilities include `available: knowledge @zack/m13-reference-corpus` for `phase:research`.
- Static capabilities include pending activation for the configured model provider and Knowledge runtime.
- Preflight-only output does not enter a phase, activate the runtime, or print `knowledge_surface_ready` events.
- Package readiness, external runtime identity, and no-fallback behavior are verified in the live process and headless Harness tests below.

## 7. Live SDK process smoke tests

These bypass the model and talk to the provider process using the JSONL service protocol. They verify SDK process serving, provider initialization, retrieval, normalized results, and citations.

Pinecone Node:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$PROVIDERS" && \
  AGENTPM_M13_LIVE_PROVIDER_COMMAND="node" \
  AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON='["providers/node/pinecone-runtime.mjs"]' \
  pnpm test:node)
```

Pinecone Python:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$PROVIDERS" && \
  AGENTPM_M13_LIVE_PROVIDER_COMMAND="uv" \
  AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON='["run","--with-editable","../../../agentpm-sdk-python","python","providers/python/pinecone_runtime.py"]' \
  pnpm test:node)
```

pgvector Node:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$PROVIDERS" && \
  AGENTPM_M13_LIVE_PROVIDER_COMMAND="node" \
  AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON='["providers/node/pgvector-runtime.mjs"]' \
  pnpm test:node)
```

pgvector Python:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$PROVIDERS" && \
  AGENTPM_M13_LIVE_PROVIDER_COMMAND="uv" \
  AGENTPM_M13_LIVE_PROVIDER_ARGS_JSON='["run","--with-editable","../../../agentpm-sdk-python","--extra","pgvector","python","providers/python/pgvector_runtime.py"]' \
  pnpm test:node)
```

Expected:

- The test named `live KnowledgeRuntime process returns normalized results` passes instead of being skipped.
- The test summary shows `fail 0` and `skipped 0`.
- Internally, that live test asserts provider initialization, a successful `retrieve` response, non-empty `results`, and non-empty `citations`.

## 8. Harness headless retrieval smoke tests

These exercise the full Harness path: model action selection, external runtime dispatch, provider retrieval, trace/report output, and phase completion.

Use the same prompt for each runtime:

```bash
cat > "$RUNS/input-vector-query.txt" <<'EOF'
Use @zack/m13-reference-corpus Knowledge. Run a vector_query for "passing smoke test severity-one incidents communications owner rollback command" with top_k 1 and citations. Answer with the returned chunk id and source title. Do not use external knowledge.
EOF
```

Pinecone Node:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pinecone-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pinecone-node.json" \
  > "../manual-runs/stdout-pinecone-node.txt" \
  2> "../manual-runs/stderr-pinecone-node.txt")
```

Pinecone Python:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pinecone-python.local-dev.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pinecone-python.json" \
  > "../manual-runs/stdout-pinecone-python.txt" \
  2> "../manual-runs/stderr-pinecone-python.txt")
```

pgvector Node:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pgvector-node.json" \
  > "../manual-runs/stdout-pgvector-node.txt" \
  2> "../manual-runs/stderr-pgvector-node.txt")
```

pgvector Python:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-python.local-dev.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pgvector-python.json" \
  > "../manual-runs/stdout-pgvector-python.txt" \
  2> "../manual-runs/stderr-pgvector-python.txt")
```

Expected:

- Terminal status is `ended`.
- Output identifies `chunk_release_gate` from `Alpha Operations Playbook`.
- The report has `knowledge_requests >= 1`.
- Trace has `knowledge_request_started` and `knowledge_retrieved`.
- `knowledge_retrieved` result has exactly one result, because the request should include `top_k: 1`.
- The single result is `chunk_release_gate` from `Alpha Operations Playbook`.
- `knowledge_retrieved` result has non-empty `citations`.
- `knowledge_surface_ready.fields.runtime` is the external runtime id, not `local`.

Quick report/trace inspection:

```bash
for report in "$RUNS"/report-*.json; do
  echo "$report"
  jq '{terminal_status, output: .terminal_output, knowledge_requests: .usage.knowledge_requests, trace_path}' "$report"
done
```

Inspect one trace:

```bash
TRACE="$(jq -r '.trace_path' "$RUNS/report-pinecone-node.json")"
jq -c 'select(.event_type | test("knowledge_surface_ready|knowledge_request_started|knowledge_retrieved|knowledge_request_failed"))' "$TRACE"
```

Inspect the rank-1 result from one trace:

```bash
TRACE="$(jq -r '.trace_path' "$RUNS/report-pgvector-node.json")"
jq -c 'select(.event_type=="knowledge_retrieved") | .payload.fields.result.results[0] | {rank, chunk_id, source_title, score}' "$TRACE"
```

Strict trace assertion for one report:

```bash
TRACE="$(jq -r '.trace_path' "$RUNS/report-pgvector-node.json")"
jq -e 'select(.event_type=="knowledge_retrieved")
  | .payload.fields.result as $result
  | ($result.results | length == 1)
    and ($result.results[0].chunk_id == "chunk_release_gate")
    and ($result.results[0].source_title == "Alpha Operations Playbook")
    and ($result.citations | length >= 1)' "$TRACE"
```

## 9. Verify top_k and score_threshold behavior

Use a low `top_k` prompt:

```bash
cat > "$RUNS/input-top-k-1.txt" <<'EOF'
Use @zack/m13-reference-corpus Knowledge. Run a vector_query for "alpha launch checklist" with top_k 1 and citations. Answer with the number of returned results, the top chunk id, and source title.
EOF
```

Run it against at least one Pinecone config and one pgvector config:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pinecone-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-top-k-1.txt" \
  --report "../manual-runs/report-top-k-pinecone-node.json")

export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-top-k-1.txt" \
  --report "../manual-runs/report-top-k-pgvector-node.json")
```

Expected:

- The retrieved result has exactly one row when the model sends `top_k: 1`.

Use a high threshold prompt:

```bash
cat > "$RUNS/input-threshold.txt" <<'EOF'
Use @zack/m13-reference-corpus Knowledge. Run a vector_query for "alpha launch checklist" with top_k 4, score_threshold 0.95, and citations. Answer with every returned chunk id and score.
EOF
```

Run one provider:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-threshold.txt" \
  --report "../manual-runs/report-threshold-pgvector-node.json")
```

Expected:

- Returned results all have `score >= 0.95`.
- If no rows meet the threshold, the provider returns a successful Knowledge result with an empty `results` array rather than silently ignoring the threshold.

Trace helper:

```bash
TRACE="$(jq -r '.trace_path' "$RUNS/report-threshold-pgvector-node.json")"
jq -c 'select(.event_type=="knowledge_retrieved") | .payload.fields.result.results[]? | {chunk_id, score}' "$TRACE"
```

## 10. Verify no local fallback on external runtime failure

Temporarily break the external runtime environment and confirm the mapped package does not fall back to local Knowledge.

Pinecone example:

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pinecone-reference"
export PINECONE_INDEX_HOST="https://invalid.invalid"

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pinecone-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pinecone-broken.json" \
  > "../manual-runs/stdout-pinecone-broken.txt" \
  2> "../manual-runs/stderr-pinecone-broken.txt" || true)
```

Expected:

- The surface remains mapped to `pinecone-reference`.
- There is no `knowledge_surface_ready` event for `@zack/m13-reference-corpus` with runtime `local`.
- Failure is a typed provider/Knowledge failure, not a silent local result.
- The model/phase may complete with an error-aware answer depending on repair behavior; the key check is no fallback.

Restore the valid value after this test:

```bash
export PINECONE_INDEX_HOST="https://YOUR_INDEX_HOST"
```

## 11. Verify corpus attestation mismatch

Temporarily set a wrong corpus hash and run preflight/retrieval.

```bash
export AGENTPM_KNOWLEDGE_RUNTIME_ID="pgvector-reference"
export AGENTPM_KNOWLEDGE_CORPUS_HASH="sha256:wrong"

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --input-file "../manual-runs/input-vector-query.txt" \
  --report "../manual-runs/report-pgvector-wrong-corpus.json" \
  > "../manual-runs/stdout-pgvector-wrong-corpus.txt" \
  2> "../manual-runs/stderr-pgvector-wrong-corpus.txt" || true)
```

Expected:

- The runtime should not successfully return rows for the installed package/corpus mismatch.
- The trace/report should contain an explicit readiness, attestation, or provider failure reason.
- There should be no local fallback.

Restore the real corpus hash:

```bash
export AGENTPM_KNOWLEDGE_CORPUS_HASH="$(jq -r '.knowledge.corpus.content_hash' "$CORPUS/agent.json")"
```

## 12. Redaction checks

The checked-in harness configs use:

```json
{
  "trace": {
    "enabled": true,
    "level": "verbose",
    "content": "redacted"
  }
}
```

After a headless run, inspect the trace:

```bash
TRACE="$(jq -r '.trace_path' "$RUNS/report-pinecone-node.json")"
rg -n "OPENAI_API_KEY|PINECONE_API_KEY|alpha launch checklist|release gate|source document" "$TRACE" || true
```

Expected:

- Secrets never appear.
- Content-like fields should be redacted according to Harness trace policy.
- Non-sensitive structural metadata such as package identity, runtime id, mode, top_k, and event type remains inspectable.

## 13. Acceptance summary

Mark M13 manual verification complete when these are true:

- Mocked Node and Python provider tests pass.
- Corpus builds with OpenAI `text-embedding-3-small`.
- Pinecone and pgvector are loaded with the same corpus hash as the built package.
- Harness preflight reports the external runtime surface as ready.
- Harness headless retrieval succeeds for Pinecone Node, Pinecone Python, pgvector Node, and pgvector Python local-dev configs.
- Results preserve package/version, chunk id, source id/title/URI, scores, and citations consistently across providers/languages.
- `top_k` and `score_threshold` are honored.
- Provider/backend failure returns an explicit failure and does not fall back to local Knowledge.
- Corpus attestation mismatch is explicit and does not fall back to local Knowledge.
- Trace redaction does not leak prompt/query/document content or secrets.

Known scope note:

- Generic caller-driven metadata filters are intentionally not tested because the current `KnowledgeRuntimeRequest` contract has no metadata-filter field. The reference providers therefore do not advertise `metadata_filter`.
