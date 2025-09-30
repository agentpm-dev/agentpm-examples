from langchain_core.callbacks import BaseCallbackHandler

class VerboseHandler(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, **kwargs):
        name = serialized.get("id") or serialized.get("name") or "chain"
        print(f"\n▶️  Chain start: {name}")
        print(f"   Inputs: {inputs}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"🛠️  Tool start: {serialized.get('name')}")
        print(f"   Args: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"✅ Tool output (trunc): {str(output)[:240]}")

    def on_chain_end(self, outputs, **kwargs):
        print(f"⏹️  Chain end. Outputs: {outputs}")
