import { serve } from './service-io.mjs';

const MODEL_PROVIDER = 'provider-lab-model';
const MODEL_ID = 'deterministic-provider-lab';
const DOCS_KNOWLEDGE = '@zack/agentpm-docs';
const EXTERNAL_KNOWLEDGE = '@zack/devwork-maintainer-guide';
const EXTERNAL_MEMORY = '@zack/support-customer-state';

await serve('model', {
  initialize(payload) {
    return {
      registry_id: process.env.PROVIDER_LAB_MODEL_ID || MODEL_PROVIDER,
      model: payload.model?.model || MODEL_ID,
      ready: true,
      capabilities: {
        semantic_actions: true,
        structured_output: true,
        multimodal_input: false,
        context_window_tokens: 32000,
        usage_reporting: true,
      },
    };
  },
  generate(payload) {
    const request = payload.request ?? {};
    const phase = request.phase_id || 'reason';
    const transcript = request.transcript || [];

    if (phase === 'reason') {
      if (!hasActionResult(transcript, 'knowledge_request', DOCS_KNOWLEDGE)) {
        return turn('Read the installed AgentPM docs through local vector Knowledge.', [
          proposal('read-docs-knowledge', {
            type: 'knowledge_request',
            package: DOCS_KNOWLEDGE,
            mode: 'vector_query',
            query: summarizeInput(request.run_input) || 'Harness provider bridge contracts',
            top_k: 2,
            return_citations: true,
          }),
        ]);
      }

      if (!hasActionResult(transcript, 'knowledge_request', EXTERNAL_KNOWLEDGE)) {
        return turn('Read the published maintainer guide through the custom KnowledgeRuntime.', [
          proposal('read-reference-knowledge', {
            type: 'knowledge_request',
            package: EXTERNAL_KNOWLEDGE,
            mode: 'vector_query',
            query: 'external provider bridge reference runtime',
            top_k: 2,
            return_citations: true,
          }),
        ]);
      }

      if (!hasActionResult(transcript, 'memory_write', `${EXTERNAL_MEMORY}/customer_state`)) {
        return turn('Persist the provider-lab observation through the custom MemoryRuntime.', [
          proposal('write-reference-memory', {
            type: 'memory_write',
            package: EXTERNAL_MEMORY,
            space: 'customer_state',
            operation: 'create',
            record_type: 'customer_state',
            content: {
              display_name: 'Provider Lab',
              support_tier: 'standard',
              preferred_contact_channel: 'email',
              preferred_response_tone: 'concise',
              known_constraints: [
                'Provider lab exercised local Knowledge embeddings, external KnowledgeRuntime retrieval, and external MemoryRuntime persistence.',
              ],
            },
          }),
        ]);
      }

      return turn('The provider bridges were exercised; move to the approval-gated action phase.', [
        proposal('complete-reason', {
          type: 'phase_completion',
          outcome: 'act',
          output: {
            summary:
              'Provider lab verified the process ModelRuntime, local EmbeddingProvider-backed Knowledge retrieval, external KnowledgeRuntime retrieval, and external MemoryRuntime write.',
            providers_exercised: [
              'model:provider-lab-model',
              'embedding:local-openai-embeddings',
              'knowledge:reference-knowledge',
              'memory:reference-memory',
            ],
          },
        }),
      ]);
    }

    if (phase === 'act') {
      return turn('No further external action is needed after the provider bridge checks.', [
        proposal('complete-act', {
          type: 'phase_completion',
          outcome: 'complete',
          output: {
            action: 'provider bridge smoke run completed',
          },
        }),
      ]);
    }

    return turn('The provider lab result is complete.', [
      proposal('complete-reflect', {
        type: 'phase_completion',
        outcome: 'complete',
        output: {
          final:
            'Harness provider lab completed: model, embedding, external Knowledge, external Memory, and approval controller paths all ran.',
        },
      }),
    ]);
  },
});

function turn(assistantContent, actions) {
  return {
    assistant_content: assistantContent,
    actions,
    usage: {
      model_calls: 1,
      accepted_semantic_actions: 0,
      tool_calls: 0,
      tool_retries: 0,
      knowledge_requests: 0,
      memory_requests: 0,
      embedding_requests: 0,
    },
    finish_reason: 'stop',
    provider_metadata: {
      provider_lab: true,
    },
  };
}

function proposal(id, action) {
  return { id, action };
}

function hasActionResult(transcript, kind, identity) {
  return transcript.some((entry) => {
    if (entry.kind !== 'action_result') return false;
    const content = entry.content || {};
    return (
      content.action_kind === kind &&
      content.identity === identity &&
      content.result &&
      content.result.ok === true
    );
  });
}

function summarizeInput(input) {
  if (typeof input !== 'string') return '';
  return input.trim().slice(0, 180);
}
