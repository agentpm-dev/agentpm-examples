from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.callbacks import DevworkVerboseHandler
from app.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.tooling import AGENT_SPEC, describe_memory_contract, load_langchain_tools
from app.workflow import DevworkState, build_graph


def print_banner(
    manifest_name: str,
    loaded_skills: list[dict],
    loaded_knowledge: list[dict],
    loaded_memory: list[dict],
    metas: list[dict],
) -> None:
    print(f"\nDevwork Copilot: {manifest_name}")
    print(f"Agent package: {AGENT_SPEC}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Loaded skills: {len(loaded_skills)}")
    for loaded_skill in loaded_skills:
        print(
            f"- {loaded_skill.get('name')}@{loaded_skill.get('version')}: "
            f"{loaded_skill.get('description') or 'No description'}"
        )
    print(f"Loaded knowledge packages: {len(loaded_knowledge)}")
    for loaded_item in loaded_knowledge:
        mode = loaded_item.get("knowledge", {}).get("mode") or "unknown"
        chunks_path = loaded_item.get("chunksPath")
        vectors_path = loaded_item.get("vectorsPath")
        detail = f"mode={mode}"
        if chunks_path and vectors_path:
            detail += f", chunks={chunks_path}, vectors={vectors_path}"
        print(
            f"- {loaded_item.get('name')}@{loaded_item.get('version')}: "
            f"{loaded_item.get('description') or 'No description'} ({detail})"
        )
    print(f"Loaded memory packages: {len(loaded_memory)}")
    for package in loaded_memory:
        loaded_item = package["loaded"]
        memory = loaded_item["memory"]
        print(f"- {package['spec']}")
        print(f"  Spaces: {', '.join(sorted(memory.get('spaces', {}).keys()))}")
        print(f"  Operations: {len(memory.get('operations', {}))}")
        print(f"  Contracts: {len(loaded_item.get('contracts', []))}")
        required_fields = describe_memory_contract(
            loaded_item,
            space="active_work_threads",
            record_type="work_thread",
        )
        print("  Work-thread contract required fields: " + ", ".join(required_fields))
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


def render_skill_manuals(loaded_skills: list[dict]) -> str:
    sections: list[str] = []
    for loaded_skill in loaded_skills:
        content = loaded_skill.get("entrypointContent")
        if not isinstance(content, str) or not content.strip():
            continue
        sections.append(
            "\n".join(
                [
                    f"Skill: {loaded_skill.get('name')}@{loaded_skill.get('version')}",
                    content.strip(),
                ]
            )
        )
    return "\n\n".join(sections)


def main() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY. Create .env.local from .env.example and set the key.")

    loaded_agent, loaded_skills, loaded_knowledge, loaded_memory, tools, metas = load_langchain_tools()
    graph = build_graph(tools, render_skill_manuals(loaded_skills))
    state: DevworkState = {"messages": [], "pending_tool_calls": None}

    print_banner(loaded_agent["manifest"]["name"], loaded_skills, loaded_knowledge, loaded_memory, metas)

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
            print_banner(loaded_agent["manifest"]["name"], loaded_skills, loaded_knowledge, loaded_memory, metas)
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
