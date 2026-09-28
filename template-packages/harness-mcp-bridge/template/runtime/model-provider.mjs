import { serve } from './service-io.mjs';

const MCP_IDENTITY = 'mcp:bridge-search/lookup';

await serve('model', {
  initialize(payload) {
    return {
      registry_id: 'mcp-bridge-model',
      model: payload.model?.model || 'deterministic-mcp-bridge',
      ready: true,
      capabilities: {
        semantic_actions: true,
        structured_output: true,
        multimodal_input: false,
        context_window_tokens: 16000,
        usage_reporting: true,
      },
    };
  },
  generate(payload) {
    const request = payload.request ?? {};
    const phase = request.phase_id || 'reason';
    const transcript = request.transcript || [];

    if (phase === 'reason') {
      return turn('The imported MCP lookup is scoped to act, so move into the action phase.', [
        proposal('complete-reason', {
          type: 'phase_completion',
          outcome: 'act',
          output: {
            plan: 'Call the scoped MCP import lookup tool in act.',
          },
        }),
      ]);
    }

    if (phase === 'act' && !hasActionResult(transcript, 'external_mcp_tool', MCP_IDENTITY)) {
      return turn('Call the imported MCP lookup tool.', [
        proposal('call-bridge-lookup', {
          type: 'external_mcp_tool',
          server: 'bridge-search',
          tool: 'lookup',
          arguments: {
            query: summarizeInput(request.run_input) || 'AgentPM Harness MCP bridge',
            include_context: true,
          },
        }),
      ]);
    }

    if (phase === 'act') {
      return turn('The imported MCP tool returned successfully.', [
        proposal('complete-act', {
          type: 'phase_completion',
          outcome: 'complete',
          output: {
            summary: 'Imported MCP lookup completed through bridge-search/lookup.',
          },
        }),
      ]);
    }

    return turn('The MCP bridge run is complete.', [
      proposal('complete-reflect', {
        type: 'phase_completion',
        outcome: 'complete',
        output: {
          final:
            'MCP bridge completed: AgentPM authored tools are exportable outward, and the scoped HTTP MCP import ran inside Harness.',
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
      mcp_bridge: true,
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
      content.result.ok !== false
    );
  });
}

function summarizeInput(input) {
  if (typeof input !== 'string') return '';
  return input.trim().slice(0, 180);
}
