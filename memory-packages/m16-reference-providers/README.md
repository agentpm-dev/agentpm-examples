# Harness M16 MemoryRuntime reference providers

Reference process providers for Harness Milestone 16:

- PostgreSQL/pgvector `MemoryRuntime`
- Redis/Redis Stack `MemoryRuntime`

These examples intentionally live outside Harness core. They speak the public `agentpm-service` JSONL process protocol through SDK helpers and can be launched from `agentpm.harness.json` as custom Memory runtimes.

## Shared contract

Both providers:

- accept normalized MemoryRuntime primitive requests for `read`, `write`, `count`, `load_operation_state`, `store_operation_state`, and `commit_lifecycle`;
- advertise a normalized live descriptor plus exact package/version readiness during process initialization;
- require explicit `memory.packages` mapping in Harness config;
- do not fall back to SQLite when the external runtime fails;
- keep provider credentials in the provider process environment;
- treat Harness as the only Blueprint interpreter. The provider stores records, counts, operation state, and advertised lifecycle batch primitives, but it does not reinterpret portable lifecycle operations.

Common package env:

```bash
export AGENTPM_MEMORY_PACKAGE=@zack/m16-reference-memory
export AGENTPM_MEMORY_VERSION=0.1.0
```

## SDK setup

Use the published Python and Node SDK **0.1.17 or newer**, which include the
MemoryRuntime process helpers. Use AgentPM CLI **0.1.43 or newer** for the Harness
workspace. From this provider directory, install the dependencies:

```bash
pnpm install
uv sync --upgrade-package agentpm
```

The explicitly named `*.local-dev.agentpm.harness.json` configs and historical
manual-testing commands still select a sibling SDK checkout for SDK development.
Use the commands below for published-SDK provider execution.

## Capability advertisement

The PostgreSQL/pgvector provider advertises the M16 reference primitive record/state/batch capabilities and persists Memory records in `agentpm_memory_records`, lifecycle state in `agentpm_memory_operation_state`, and sequence counters in `agentpm_memory_ordinals`. Direct writes and lifecycle commits run inside PostgreSQL transactions. It omits `semantic` in M16; setting `AGENTPM_MEMORY_PGVECTOR_SEMANTIC=true` fails closed until real embedding storage and cosine ranking are implemented.

The Redis provider uses Redis hashes for records, active-set indexes for scoped spaces, string counters for sequence ordinals, and JSON operation-state keys. It advertises durable trigger state, but not `atomic_batches`: `WATCH`/`MULTI` protects against stale writes, but Redis `EXEC` does not roll back earlier queued commands if a later queued command fails. The provider still exposes a happy-path `commit_lifecycle` primitive for smoke coverage; Harness must suppress lifecycle operations that require atomic batches against this provider. It omits `semantic` in M16; setting `AGENTPM_MEMORY_REDIS_STACK=true` fails closed until real Redis Stack vector storage and ranking are implemented. Unsupported capabilities must be omitted so Harness can suppress incompatible spaces/operations during preflight.

The fixed lifecycle failure cooldown remains Harness-owned portable behavior for M16. Providers return typed primitive failures; Harness applies the same operation failure state/backoff regardless of backend.

## Harness workspace

Optional local live infrastructure:

```bash
export APM="${APM:-$(pwd)/../../../agentpm/target/debug/agentpm}"
docker compose -f docker-compose.memory.yml up -d
export PGVECTOR_DATABASE_URL=postgresql://postgres:postgres@localhost:55433/postgres
export REDIS_URL=redis://localhost:6380/0
unset AGENTPM_MEMORY_PGVECTOR_SEMANTIC
```

To launch a provider process directly from this directory after the service env is set:

```bash
export AGENTPM_MEMORY_RUNTIME_ID=pgvector-memory-reference
uv run --extra pgvector python providers/python/pgvector_runtime.py
```

```bash
export AGENTPM_MEMORY_RUNTIME_ID=redis-memory-reference
uv run --extra redis python providers/python/redis_runtime.py
```

The `harness-workspace/` directory is a local agent workspace for end-to-end Harness checks. It contains:

- `agent.json`, a local Agent that binds `@zack/m16-reference-memory`;
- `loops/m16-reference-loop/agent.json`, a small local loop with Memory access;
- `scripts/prepare_workspace.py`, which installs the reference Memory package and loop into the workspace-local `.agentpm/` layout.

Prepare it after linting the Memory package:

```bash
cd ../m16-reference-memory
"$APM" lint

cd ../m16-reference-providers/harness-workspace
python3 scripts/prepare_workspace.py
```

Harness config examples live in `harness-configs/`:

| Config                                           | Runtime                                                       |
| ------------------------------------------------ | ------------------------------------------------------------- |
| `pgvector-node.agentpm.harness.json`             | PostgreSQL/pgvector Node provider with published/local SDK    |
| `pgvector-python.local-dev.agentpm.harness.json` | PostgreSQL/pgvector Python provider with sibling SDK checkout |
| `redis-node.agentpm.harness.json`                | Redis Node provider with published/local SDK                  |
| `redis-python.local-dev.agentpm.harness.json`    | Redis Python provider with sibling SDK checkout               |

Harness projects only the variable names listed in each runtime `env` array from the Harness process environment into the provider process. Do not put literal secret values in `agentpm.harness.json`.

Run preflight from `harness-workspace/`:

```bash
export APM="${APM:-$(pwd)/../../../../agentpm/target/debug/agentpm}"
"$APM" harness --config ../harness-configs/pgvector-node.agentpm.harness.json --verbose
```

Run a headless smoke test:

```bash
export APM="${APM:-$(pwd)/../../../../agentpm/target/debug/agentpm}"
"$APM" harness --config ../harness-configs/pgvector-node.agentpm.harness.json \
  --headless \
  --scope user=m16-user \
  --scope conversation=m16-conversation \
  --input "Write one M16 reference Memory note about launch readiness, then complete with outcome done."
```

## Tests

Mocked mapping tests do not require PostgreSQL, Redis, or embedding credentials:

```bash
cd ../m16-reference-providers
pnpm test:node
uv run --python 3.13 --extra test pytest test/
```

Live provider verification is environment-dependent. Run it only after preparing the external store, indexes, and any embedding configuration required by the capabilities being advertised. The live test initializes a provider process and runs the same conformance scenario used by the mocked SQLite/pgvector/Redis fixtures. Lifecycle commit checks run only when the provider advertises `atomic_batches`.

```bash
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=node
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["providers/node/pgvector-runtime.mjs"]'
pnpm test:node
```

For pre-publish Python SDK verification:

```bash
export AGENTPM_M16_LIVE_PROVIDER_COMMAND=uv
export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["run","--extra","pgvector","python","providers/python/pgvector_runtime.py"]'
pnpm test:node

export AGENTPM_M16_LIVE_PROVIDER_ARGS_JSON='["run","--extra","redis","python","providers/python/redis_runtime.py"]'
pnpm test:node
```
