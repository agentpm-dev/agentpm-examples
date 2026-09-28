import { serve } from './service-io.mjs';

await serve('approval', {
  initialize() {
    return {
      registry_id: 'controller',
      ready: true,
      capabilities: {
        request_approval: true,
        cancellation: false,
      },
    };
  },
  request_approval(payload) {
    return {
      decision: 'approve',
      reason: `MCP bridge auto-approved ${payload.checkpoint?.id || 'checkpoint'}.`,
    };
  },
});
