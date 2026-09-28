import { serve } from './service-io.mjs';

const RUNTIME_ID = 'reference-knowledge';
const PACKAGE = '@zack/devwork-maintainer-guide';
const VERSION = '0.1.0';
const CORPUS =
  'sha256:164e1bccccf6809bc1a1ef2051ce88970e51a6d58b6cd0050bdf8c5e0710d440';

await serve('knowledge', {
  initialize() {
    return {
      registry_id: process.env.PROVIDER_LAB_KNOWLEDGE_RUNTIME_ID || RUNTIME_ID,
      ready: true,
      capabilities: {
        modes: ['vector_query'],
        features: ['citations'],
        packages: [
          {
            package: PACKAGE,
            version: VERSION,
            corpus: CORPUS,
            ready: true,
          },
        ],
      },
    };
  },
  retrieve(payload) {
    const request = payload.request ?? payload;
    validateRequest(request);
    const results = [
      {
        rank: 1,
        score: 0.91,
        chunk_id: 'provider-lab-reference-1',
        source_id: 'provider-lab-maintainer-guide',
        source_title: 'Devwork Maintainer Guide Provider Pattern',
        source_uri: 'agentpm://examples/devwork-maintainer-guide',
        text:
          'External KnowledgeRuntime providers answer Harness retrieve requests using the package, version, corpus, mode, query, and citation contract.',
        chunk_metadata: {
          package: PACKAGE,
          version: VERSION,
          corpus: CORPUS,
        },
      },
    ].slice(0, request.top_k || 1);

    return {
      ok: true,
      package: request.package,
      version: request.version,
      mode: request.mode,
      query: request.query,
      results,
      citations: request.return_citations === false ? [] : results.map(toCitation),
    };
  },
});

function validateRequest(request) {
  if (request.package !== PACKAGE) {
    throw new Error(`request package ${request.package} does not match ${PACKAGE}`);
  }
  if (request.version !== VERSION) {
    throw new Error(`request version ${request.version} does not match ${VERSION}`);
  }
  if (request.mode !== 'vector_query') {
    throw new Error(`unsupported Knowledge mode ${request.mode}`);
  }
  if (!request.query || typeof request.query !== 'string') {
    throw new Error('vector_query request requires query');
  }
}

function toCitation(result) {
  return {
    chunk_id: result.chunk_id,
    source_id: result.source_id,
    title: result.source_title,
    uri: result.source_uri,
  };
}
