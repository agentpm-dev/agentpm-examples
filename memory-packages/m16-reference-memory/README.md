# M16 Reference Memory Blueprint

Small Memory Blueprint used by the Milestone 16 PostgreSQL/pgvector and Redis reference providers.

It intentionally covers the portability surface the providers must attest:

- `document`, `collection`, and `sequence` spaces;
- key, filter, chronological, and full-text retrieval declarations;
- archive/delete retention;
- scoped capacity;
- durable lifecycle trigger state and atomic lifecycle batches.

Semantic retrieval is intentionally left out of the default Blueprint so providers that do not advertise vector support can run the same fixture without suppression. Add `semantic` to the relevant spaces only when validating a provider with a prepared semantic/vector path.

Build/lint this package before using it in the provider harness workspace:

```bash
agentpm lint
```
