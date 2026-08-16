from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.callbacks import DevworkVerboseHandler
from app.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.tooling import (
    AGENT_SPEC,
    describe_memory_contract,
    load_agent_loop_package,
    load_langchain_tools,
)
from app.workflow import DevworkState, build_graph


def print_banner(
    manifest_name: str,
    loaded_skills: list[dict],
    loop_package: dict | None,
    loaded_knowledge: list[dict],
    loaded_memory: list[dict],
    loaded_profiles: list[dict],
    metas: list[dict],
    bindings: dict | None,
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
    print(f"Loaded loop packages: {1 if loop_package else 0}")
    if loop_package:
        loaded_loop = loop_package["loaded"]
        loop = loaded_loop["loop"]
        print(f"- {loop_package['spec']}")
        print(f"  Entry phase: {loop['entry_phase']}")
        print(f"  Phases: {len(loop.get('phases', []))}")
        print(f"  Transitions: {len(loop.get('transitions', []))}")
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
    print(f"Loaded profile packages: {len(loaded_profiles)}")
    for package in loaded_profiles:
        loaded_item = package["loaded"]
        profile = loaded_item["profile"]
        identity = profile.get("identity", {})
        communication = profile.get("communication", {})
        print(f"- {package['spec']}")
        print(f"  Role: {identity.get('role', 'unknown')}")
        print(f"  Objectives: {len(profile.get('objectives', []))}")
        print(f"  Constraints: {len(profile.get('constraints', []))}")
        tone = communication.get("tone", [])
        if isinstance(tone, list) and tone:
            print("  Tone: " + ", ".join(value for value in tone if isinstance(value, str)))
    if isinstance(bindings, dict):
        print("Authored bindings:")
        consumer_context = bindings.get("consumer_context")
        if isinstance(consumer_context, dict) and isinstance(consumer_context.get("file"), str):
            print(f"- Consumer context: {consumer_context['file']}")
        global_bindings = bindings.get("global")
        if isinstance(global_bindings, dict):
            global_profiles = global_bindings.get("profiles")
            if isinstance(global_profiles, list) and global_profiles:
                print(f"- Global profiles: {', '.join(value for value in global_profiles if isinstance(value, str))}")
            global_memory = global_bindings.get("memory")
            if isinstance(global_memory, list) and global_memory:
                print(f"- Global memory bindings: {len(global_memory)}")
        phase_bindings = bindings.get("phases")
        if isinstance(phase_bindings, dict) and phase_bindings:
            print(f"- Phase bindings: {', '.join(sorted(phase_bindings.keys()))}")
        mcp_bindings = bindings.get("mcp")
        if isinstance(mcp_bindings, list) and mcp_bindings:
            mcp_ids = [
                item.get("id")
                for item in mcp_bindings
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            ]
            if mcp_ids:
                print(f"- MCP surfaces: {', '.join(mcp_ids)}")
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


def render_profile_guidance(loaded_profiles: list[dict]) -> str:
    sections: list[str] = []
    for package in loaded_profiles:
        loaded_profile = package["loaded"]
        profile = loaded_profile.get("profile", {})
        identity = profile.get("identity", {})
        communication = profile.get("communication", {})
        lines = [
            f"Profile: {package['spec']}",
            f"Role: {identity.get('role', '')}",
        ]
        objectives = profile.get("objectives", [])
        if isinstance(objectives, list) and objectives:
            lines.append(
                "Objectives: " + "; ".join(value for value in objectives if isinstance(value, str))
            )
        tone = communication.get("tone", [])
        if isinstance(tone, list) and tone:
            lines.append("Tone: " + ", ".join(value for value in tone if isinstance(value, str)))
        guidelines = communication.get("guidelines", [])
        if isinstance(guidelines, list) and guidelines:
            lines.append(
                "Guidelines: " + "; ".join(value for value in guidelines if isinstance(value, str))
            )
        constraints = profile.get("constraints", [])
        if isinstance(constraints, list) and constraints:
            instructions = [
                item.get("instruction")
                for item in constraints
                if isinstance(item, dict) and isinstance(item.get("instruction"), str)
            ]
            if instructions:
                lines.append("Constraints: " + "; ".join(instructions))
        sections.append("\n".join(line for line in lines if line.strip()))
    return "\n\n".join(sections)


def main() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY. Create .env.local from .env.example and set the key.")

    (
        loaded_agent,
        loaded_skills,
        loaded_knowledge,
        loaded_memory,
        loaded_profiles,
        tools,
        metas,
    ) = load_langchain_tools()
    loop_package = load_agent_loop_package(loaded_agent)
    graph = build_graph(
        tools,
        render_skill_manuals(loaded_skills),
        render_profile_guidance(loaded_profiles),
    )
    state: DevworkState = {"messages": [], "pending_tool_calls": None}
    bindings = loaded_agent["manifest"].get("bindings")

    print_banner(
        loaded_agent["manifest"]["name"],
        loaded_skills,
        loop_package,
        loaded_knowledge,
        loaded_memory,
        loaded_profiles,
        metas,
        bindings if isinstance(bindings, dict) else None,
    )

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
            print_banner(
                loaded_agent["manifest"]["name"],
                loaded_skills,
                loop_package,
                loaded_knowledge,
                loaded_memory,
                loaded_profiles,
                metas,
                bindings if isinstance(bindings, dict) else None,
            )
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
