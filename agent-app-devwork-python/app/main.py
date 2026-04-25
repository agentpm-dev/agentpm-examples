from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.callbacks import DevworkVerboseHandler
from app.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.tooling import load_langchain_tools, read_agent_manifest
from app.workflow import DevworkState, build_graph


def print_banner(manifest_name: str, metas: list[dict]) -> None:
    print(f"\nDevwork Copilot: {manifest_name}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Loaded tools: {len(metas)}")
    for meta in metas:
        print(f"- {meta.get('name')}@{meta.get('version')}: {meta.get('description') or 'No description'}")
    print("\nCommands: /help /tools /approve /cancel /reset /quit\n")


def print_help() -> None:
    print("\nCommands:")
    print("- /help     Show this help")
    print("- /tools    List loaded tools")
    print("- /approve  Execute the pending GitHub write action")
    print("- /cancel   Discard the pending GitHub write action")
    print("- /reset    Clear conversation history and pending actions")
    print("- /quit     Exit the app\n")


def extract_assistant_text(messages: list[BaseMessage], prior_count: int) -> str:
    new_messages = messages[prior_count:]
    parts: list[str] = []
    for message in new_messages:
        if isinstance(message, AIMessage) and not message.tool_calls:
            if isinstance(message.content, str) and message.content.strip():
                parts.append(message.content)
    return "\n\n".join(parts).strip()


def main() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY. Create .env.local from .env.example and set the key.")

    manifest = read_agent_manifest()
    tools, metas = load_langchain_tools()
    graph = build_graph(tools)
    state: DevworkState = {"messages": [], "pending_tool_calls": None}

    print_banner(manifest["name"], metas)

    while True:
        try:
            line = input("devwork> ").strip()
        except EOFError:
            print("")
            break

        if not line:
            continue
        if line == "/quit":
            break
        if line == "/help":
            print_help()
            continue
        if line == "/tools":
            print_banner(manifest["name"], metas)
            continue
        if line == "/reset":
            state = {"messages": [], "pending_tool_calls": None}
            print("Conversation history and pending actions cleared.\n")
            continue

        print("\n[thinking]\n")
        try:
            prior_count = len(state["messages"])
            next_state = graph.invoke(
                {
                    "messages": [*state["messages"], HumanMessage(content=line)],
                    "pending_tool_calls": state.get("pending_tool_calls"),
                },
                config={"callbacks": [DevworkVerboseHandler()]},
            )
            state = {
                "messages": next_state["messages"],
                "pending_tool_calls": next_state.get("pending_tool_calls"),
            }
            output = extract_assistant_text(state["messages"], prior_count)
            if output:
                print("\n[assistant]\n")
                print(output)
                print("")
        except Exception as exc:  # pragma: no cover - runtime path
            print("\n[error]")
            print(str(exc))
            print("")


if __name__ == "__main__":
    main()
