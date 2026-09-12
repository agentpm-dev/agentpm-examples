# Harness M16 manual verification

Temporary/manual checklist for Milestone 16 MemoryRuntime providers.

Run commands from the `agentpm-examples` repo root unless a step says otherwise.

## 0. Shell setup

```bash
export EXAMPLES_ROOT="$(pwd)"
export APM="${APM:-$EXAMPLES_ROOT/../agentpm/target/debug/agentpm}"
export PROVIDERS="$EXAMPLES_ROOT/memory-packages/m16-reference-providers"
export MEMORY_PKG="$EXAMPLES_ROOT/memory-packages/m16-reference-memory"
export WORKSPACE="$PROVIDERS/harness-workspace"
export RUNS="$PROVIDERS/manual-runs"
mkdir -p "$RUNS"
```

If the local CLI has not been built yet:

```bash
(cd ../agentpm && cargo build)
```

For pre-publish SDK testing, use local SDKs.

Node:

```bash
(cd "$EXAMPLES_ROOT/../agentpm-sdk-node" && pnpm install && pnpm build)
(cd "$PROVIDERS" && pnpm install --ignore-workspace)
(cd "$PROVIDERS" && pnpm link ../../../agentpm-sdk-node)
```

The mocked Python tests do not need the local SDK. Python live provider commands below use `--with-editable ../../../agentpm-sdk-python` only where the unpublished `serve_memory_runtime_process` helper is needed.

Optional live provider checks need the local service containers:

```bash
(cd "$PROVIDERS" && docker compose -f docker-compose.memory.yml up -d)
export PGVECTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55433/postgres"
export REDIS_URL="redis://localhost:6380/0"
unset AGENTPM_MEMORY_PGVECTOR_SEMANTIC
unset AGENTPM_MEMORY_REDIS_STACK
```

For a completely clean provider data set, reset the test containers before starting:

```bash
(cd "$PROVIDERS" && docker compose -f docker-compose.memory.yml down -v)
(cd "$PROVIDERS" && docker compose -f docker-compose.memory.yml up -d)
```

## 1. Run mocked provider tests

These do not require PostgreSQL, Redis, or embedding credentials.

```bash
(cd "$PROVIDERS" && pnpm test:node)
(cd "$PROVIDERS" && uv run --python 3.13 --extra test pytest test/)
```

Expected:

- Node tests pass.
- Python tests pass without requiring the unpublished local SDK serving helper.
- Redis capabilities omit `semantic`; the unfinished Redis Stack semantic flag fails closed.
- The cross-backend conformance fixture runs the same direct Memory/filter/state/lifecycle scenario against SQLite, pgvector, and Redis fixtures, with Redis skipping lifecycle commit only because it advertises `atomic_batches: false`.

## 2. Lint and prepare the Memory package

```bash
(cd "$MEMORY_PKG" && "$APM" lint)
(cd "$WORKSPACE" && python3 scripts/prepare_workspace.py)
```

Expected:

- `agentpm lint` succeeds for `m16-reference-memory`.
- The workspace-local `.agentpm/memory/zack/m16-reference-memory/0.1.0` directory is recreated.

## 3. Run live provider process conformance

These commands start each provider process directly and run the same Node conformance scenario against it.

PostgreSQL/pgvector with the linked Node SDK:

```bash
export AGENTPM_MEMORY_RUNTIME_ID="pgvector-memory-reference"
export AGENTPM_MEMORY_PACKAGE="@zack/m16-reference-memory"
export AGENTPM_MEMORY_VERSION="0.1.0"
export PGVECTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55433/postgres"
unset AGENTPM_MEMORY_PGVECTOR_SEMANTIC
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=node
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["providers/node/pgvector-runtime.mjs"]'

(cd "$PROVIDERS" && pnpm test:node)
```

PostgreSQL/pgvector with the Python local SDK checkout:

```bash
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=uv
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["run","--with-editable","../../../agentpm-sdk-python","--extra","pgvector","python","providers/python/pgvector_runtime.py"]'

(cd "$PROVIDERS" && pnpm test:node)
```

Redis with the linked Node SDK:

```bash
export AGENTPM_MEMORY_RUNTIME_ID="redis-memory-reference"
export REDIS_URL="redis://localhost:6380/0"
unset AGENTPM_MEMORY_REDIS_STACK
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=node
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["providers/node/redis-runtime.mjs"]'

(cd "$PROVIDERS" && pnpm test:node)
```

Redis with the Python local SDK checkout:

```bash
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=uv
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["run","--with-editable","../../../agentpm-sdk-python","--extra","redis","python","providers/python/redis_runtime.py"]'

(cd "$PROVIDERS" && pnpm test:node)
```

Expected:

- Each live command reports the live provider test as running, not skipped.
- Direct write/read/count/filter and operation-state checks pass for every provider.
- pgvector providers also pass lifecycle commit checks because they advertise `atomic_batches: true`.
- Redis providers pass direct/state checks and skip lifecycle commit checks because they advertise `atomic_batches: false`.

Clear the live provider test env after this section so later `pnpm test:node` runs do not unexpectedly start a provider process:

```bash
unset AGENTPM_M16_LIVE_PROVIDER_COMMAND
unset AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON
```

## 4. Run pgvector Harness checks

Run preflight through both Harness configs:

```bash
export AGENTPM_MEMORY_RUNTIME_ID="pgvector-memory-reference"
export AGENTPM_MEMORY_PACKAGE="@zack/m16-reference-memory"
export AGENTPM_MEMORY_VERSION="0.1.0"
export PGVECTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55433/postgres"
unset AGENTPM_MEMORY_PGVECTOR_SEMANTIC

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --verbose \
  >"$RUNS/pgvector-preflight.stdout.txt" \
  2>"$RUNS/pgvector-preflight.stderr.txt")

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-python.local-dev.agentpm.harness.json \
  --verbose \
  >"$RUNS/pgvector-python-preflight.stdout.txt" \
  2>"$RUNS/pgvector-python-preflight.stderr.txt")
```

Expected:

- Both preflights report pending runtime activation for the mapped MemoryRuntime.
- No config or lockfile errors are reported.
- No local SQLite fallback is reported for the mapped package.

Run direct Memory through both Harness configs:

```bash
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --scope user=m16-user \
  --scope conversation=m16-conversation \
  --input "Write one M16 reference Memory note about launch readiness, then complete with outcome done." \
  --report "$RUNS/pgvector-write.report.json" \
  >"$RUNS/pgvector-write.stdout.txt" \
  2>"$RUNS/pgvector-write.stderr.txt")

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/pgvector-python.local-dev.agentpm.harness.json \
  --headless \
  --scope user=m16-user-python \
  --scope conversation=m16-conversation \
  --input "Write one M16 reference Memory note through the Python pgvector provider, then complete with outcome done." \
  --report "$RUNS/pgvector-python-write.report.json" \
  >"$RUNS/pgvector-python-write.stdout.txt" \
  2>"$RUNS/pgvector-python-write.stderr.txt")
```

Expected:

- Both runs end successfully.
- Both reports contain one completed direct Memory write.
- Both traces show `memory_write_started` and `memory_write_completed` for `@zack/m16-reference-memory/notes`.

## 5. Run Redis Harness checks

```bash
export AGENTPM_MEMORY_RUNTIME_ID="redis-memory-reference"
export AGENTPM_MEMORY_PACKAGE="@zack/m16-reference-memory"
export AGENTPM_MEMORY_VERSION="0.1.0"
export REDIS_URL="redis://localhost:6380/0"
unset AGENTPM_MEMORY_REDIS_STACK

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/redis-node.agentpm.harness.json \
  --verbose \
  >"$RUNS/redis-preflight.stdout.txt" \
  2>"$RUNS/redis-preflight.stderr.txt")

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/redis-python.local-dev.agentpm.harness.json \
  --verbose \
  >"$RUNS/redis-python-preflight.stdout.txt" \
  2>"$RUNS/redis-python-preflight.stderr.txt")
```

Expected:

- Redis initializes as a MemoryRuntime through both Harness configs.
- Spaces requiring only Redis-advertised modes remain available.
- Semantic-only surfaces are suppressed rather than falling back to local SQLite.
- The raw Redis capability descriptor is covered by the provider conformance tests above, where Redis advertises `durable_trigger_state: true` and `atomic_batches: false`.
- The Harness-observable check here is that lifecycle operations requiring atomic batch commits are suppressed; preflight does not print the raw capability flags.

Run Redis-backed direct Memory writes to verify ordinary Memory still works while lifecycle operations remain suppressed:

```bash
(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/redis-node.agentpm.harness.json \
  --headless \
  --scope user=m16-user \
  --scope conversation=m16-conversation \
  --input "Write one M16 reference Memory note about Redis ordinary Memory availability, then complete with outcome done." \
  --report "$RUNS/redis-write.report.json" \
  >"$RUNS/redis-write.stdout.txt" \
  2>"$RUNS/redis-write.stderr.txt")

(cd "$WORKSPACE" && "$APM" harness \
  --config ../harness-configs/redis-python.local-dev.agentpm.harness.json \
  --headless \
  --scope user=m16-redis-python \
  --scope conversation=m16-conversation \
  --input "Write one M16 reference Memory note through the Python Redis provider, then complete with outcome done." \
  --report "$RUNS/redis-python-write.report.json" \
  >"$RUNS/redis-python-write.stdout.txt" \
  2>"$RUNS/redis-python-write.stderr.txt")

export REDIS_TRACE="$(jq -r '.trace_path' "$RUNS/redis-write.report.json")"
jq -r '
  select(.event_type == "memory_surface_ready"
    or .event_type == "memory_write_completed"
    or .event_type == "memory_operation_failed"
    or .event_type == "memory_operation_started")
  | [
      .run_sequence,
      .event_type,
      (.payload.identity // .payload.fields.identity // .payload.fields.operation // ""),
      (.payload.status // .payload.fields.reason // "")
    ]
  | @tsv
' "$REDIS_TRACE" >"$RUNS/redis-write.memory-events.tsv"

export REDIS_PYTHON_TRACE="$(jq -r '.trace_path' "$RUNS/redis-python-write.report.json")"
jq -r '
  select(.event_type == "memory_surface_ready"
    or .event_type == "memory_write_completed"
    or .event_type == "memory_operation_failed"
    or .event_type == "memory_operation_started")
  | [
      .run_sequence,
      .event_type,
      (.payload.identity // .payload.fields.identity // .payload.fields.operation // ""),
      (.payload.status // .payload.fields.reason // "")
    ]
  | @tsv
' "$REDIS_PYTHON_TRACE" >"$RUNS/redis-python-write.memory-events.tsv"
```

Expected:

- Both runs end successfully.
- Both traces include `memory_surface_ready` for ordinary Redis-backed Memory spaces.
- Both traces include `memory_write_completed` for `@zack/m16-reference-memory/notes`.
- Both traces include lifecycle operation unavailability with `Memory lifecycle operations require atomic batch support`.
- Neither trace includes `memory_operation_started`.

## 6. Cleanup local SDK links before final handoff

Run these reminders from the `agentpm-examples` repo root after manual testing is complete.

```bash
cd "$EXAMPLES_ROOT"
```

Remove any temporary provider-local Node SDK link and reinstall against the declared dependency:

```bash
(cd memory-packages/m16-reference-providers && pnpm unlink @agentpm/sdk || true)
(cd memory-packages/m16-reference-providers && pnpm install --ignore-workspace)
```

Before review or publish, remove any temporary root-level SDK override/link that was added only for pre-publish M16 testing:

```bash
git diff -- package.json pnpm-workspace.yaml
```

Expected:

- `memory-packages/m16-reference-providers/package.json` depends on the published `@agentpm/sdk` range, not a local `link:` dependency.
- `agentpm-examples/package.json` and `agentpm-examples/pnpm-workspace.yaml` do not keep temporary M16 SDK link/override entries unless they are still intentionally needed for another active local test.
- Python live commands can keep using `--with-editable ../../../agentpm-sdk-python` in this manual file until the SDK release with `serve_memory_runtime_process` is published; that does not require committing a repo-local dependency override.
