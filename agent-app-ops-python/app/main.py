from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.callbacks import TriageVerboseHandler
from app.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.tooling import (
    AGENT_SPEC,
    describe_memory_contract,
    load_agent_loop_package,
    load_agent_memory_packages,
    load_agent_profile_packages,
    load_langchain_tools,
)


WORKER_LABEL = "zack-worker"
TEAM_NAME = "Operations"
DEFAULT_INPUT_PATH = "fixtures/incidents.csv"
FIXTURE_SCHEMA_HINT = (
    f"The CSV fixture at {DEFAULT_INPUT_PATH} uses exactly these columns: "
    "incident_id, service, severity, status, owner, opened_at, region, summary. "
    "Do not use alternate names like id, description, or created_at. "
    "For csv-query filters, use ops like eq, ne, gt, gte, lt, lte, or contains, not symbolic operators like =."
)


def print_banner(
    manifest_name: str,
    loaded_skills: list[dict],
    metas: list[dict],
    loop_package: dict | None,
    memory_packages: list[dict],
    profile_packages: list[dict],
    bindings: dict | None,
) -> None:
    print(f"\n{WORKER_LABEL}: {manifest_name}")
    print(f"Agent package: {AGENT_SPEC}")
    print(f"Team: {TEAM_NAME}")
    print(f"Default fixture: {DEFAULT_INPUT_PATH}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Loaded skills: {len(loaded_skills)}")
    for loaded_skill in loaded_skills:
        print(
            f"- {loaded_skill.get('name')}@{loaded_skill.get('version')}: "
            f"{loaded_skill.get('description') or 'No description'}"
        )
    print(f"Loaded tools: {len(metas)}")
    for meta in metas:
        print(f"- {meta.get('name')}@{meta.get('version')}: {meta.get('description') or 'No description'}")
    print(f"Loaded loop packages: {1 if loop_package else 0}")
    if loop_package:
        loaded_loop = loop_package["loaded"]
        loop = loaded_loop["loop"]
        print(f"- {loop_package['spec']}")
        print(f"  Entry phase: {loop['entry_phase']}")
        print(f"  Phases: {len(loop.get('phases', []))}")
        print(f"  Transitions: {len(loop.get('transitions', []))}")
    print(f"Loaded memory packages: {len(memory_packages)}")
    for package in memory_packages:
        loaded_memory = package["loaded"]
        memory = loaded_memory["memory"]
        print(f"- {package['spec']}")
        print(f"  Spaces: {', '.join(sorted(memory.get('spaces', {}).keys()))}")
        print(f"  Operations: {len(memory.get('operations', {}))}")
        print(f"  Contracts: {len(loaded_memory.get('contracts', []))}")
        required_fields = describe_memory_contract(
            loaded_memory,
            space="conversation_state",
            record_type="conversation_summary",
        )
        print("  Conversation summary contract required fields: " + ", ".join(required_fields))
    print(f"Loaded profile packages: {len(profile_packages)}")
    for package in profile_packages:
        loaded_profile = package["loaded"]
        profile = loaded_profile["profile"]
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
    print("\nCommands: /help /tools /reset /quit\n")


def print_help() -> None:
    print("\nCommands:")
    print("- /help  Show this help")
    print("- /tools List loaded tools")
    print("- /reset Clear conversation history")
    print("- /quit  Exit the app\n")


def augment_user_prompt(line: str) -> str:
    lowered = line.lower()
    if DEFAULT_INPUT_PATH.lower() in lowered or "incidents.csv" in lowered:
        return f"{line}\n\nSchema note: {FIXTURE_SCHEMA_HINT}"
    return line


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


def build_agent():
    loaded_agent, loaded_skills, tools, metas = load_langchain_tools()
    loop_package = load_agent_loop_package(loaded_agent)
    memory_packages = load_agent_memory_packages(loaded_agent)
    profile_packages = load_agent_profile_packages(loaded_agent)
    skill_manuals = render_skill_manuals(loaded_skills)
    system_prompt = (
        f"You are {WORKER_LABEL}, a pragmatic local triage assistant for the {TEAM_NAME} team. "
        f"Start with the local incident fixture at {DEFAULT_INPUT_PATH} when the user asks for triage or status review. "
        f"The local CSV fixture at {DEFAULT_INPUT_PATH} uses these columns: "
        "incident_id, service, severity, status, owner, opened_at, region, summary. "
        "When you query that file, use those exact column names rather than inventing alternates. "
        "Use tools when they materially improve the answer. "
        "Prefer reading the local CSV fixture, transforming structured data, and summarizing evidence over guessing. "
        "Do not post to Slack or modify GitHub state unless the user clearly asked you to do it and the required credentials are available. "
        "If the user asks for a draft or preview, do not perform the write action. "
        "Keep answers concise but operationally useful."
    )
    if skill_manuals:
        system_prompt += (
            "\n\nFollow these packaged operations manuals when they are relevant to the user's request:\n\n"
            f"{skill_manuals}"
        )
    if profile_packages:
        profile_sections: list[str] = []
        for package in profile_packages:
            loaded_profile = package["loaded"]
            profile = loaded_profile["profile"]
            identity = profile.get("identity", {})
            communication = profile.get("communication", {})
            section_lines = [
                f"Profile: {package['spec']}",
                f"Role: {identity.get('role', '')}",
            ]
            objectives = profile.get("objectives", [])
            if isinstance(objectives, list) and objectives:
                section_lines.append(
                    "Objectives: " + "; ".join(value for value in objectives if isinstance(value, str))
                )
            tone = communication.get("tone", [])
            if isinstance(tone, list) and tone:
                section_lines.append("Tone: " + ", ".join(value for value in tone if isinstance(value, str)))
            guidelines = communication.get("guidelines", [])
            if isinstance(guidelines, list) and guidelines:
                section_lines.append(
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
                    section_lines.append("Constraints: " + "; ".join(instructions))
            profile_sections.append("\n".join(line for line in section_lines if line.strip()))
        system_prompt += (
            "\n\nFollow these packaged Instruction Profiles when they are relevant to the user's request:\n\n"
            + "\n\n".join(profile_sections)
        )

    agent = create_agent(
        model=ChatOpenAI(model=OPENAI_MODEL, temperature=0.2, api_key=OPENAI_API_KEY),
        tools=tools,
        system_prompt=system_prompt,
    )
    return loaded_agent, loaded_skills, loop_package, memory_packages, profile_packages, agent, metas


def extract_final_text(result: dict) -> str:
    messages = result.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                content = message.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = [part for part in content if isinstance(part, str)]
                    if parts:
                        return "\n".join(parts)
    return str(result)


def main() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY. Create .env.local from .env.example and set the key.")

    loaded_agent, loaded_skills, loop_package, memory_packages, profile_packages, agent, metas = build_agent()
    history: list[BaseMessage] = []
    bindings = loaded_agent["manifest"].get("bindings")

    print_banner(
        loaded_agent["manifest"]["name"],
        loaded_skills,
        metas,
        loop_package,
        memory_packages,
        profile_packages,
        bindings if isinstance(bindings, dict) else None,
    )

    while True:
        try:
            line = input("triage> ").strip()
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
                metas,
                loop_package,
                memory_packages,
                profile_packages,
                bindings if isinstance(bindings, dict) else None,
            )
            continue
        if line == "/reset":
            history.clear()
            print("Conversation history cleared.\n")
            continue

        print("\n[thinking]\n")
        try:
            current_messages = [*history, HumanMessage(content=augment_user_prompt(line))]
            result = agent.invoke({"messages": current_messages}, config={"callbacks": [TriageVerboseHandler()]})
            output = extract_final_text(result)
            history.append(HumanMessage(content=line))
            history.append(AIMessage(content=output))
            print("\n[assistant]\n")
            print(output)
            print("")
        except Exception as exc:  # pragma: no cover - runtime path
            print("\n[error]")
            print(str(exc))
            print("")


if __name__ == "__main__":
    main()
