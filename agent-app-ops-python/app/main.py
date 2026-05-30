from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.callbacks import OpsVerboseHandler
from app.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.tooling import AGENT_SPEC, load_langchain_tools


def print_banner(manifest_name: str, metas: list[dict]) -> None:
    print(f"\nOps Console: {manifest_name}")
    print(f"Agent package: {AGENT_SPEC}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Loaded tools: {len(metas)}")
    for meta in metas:
        print(f"- {meta.get('name')}@{meta.get('version')}: {meta.get('description') or 'No description'}")
    print("\nCommands: /help /tools /reset /quit\n")


def print_help() -> None:
    print("\nCommands:")
    print("- /help  Show this help")
    print("- /tools List loaded tools")
    print("- /reset Clear conversation history")
    print("- /quit  Exit the app\n")


def build_agent():
    loaded_agent, tools, metas = load_langchain_tools()
    system_prompt = (
        "You are a pragmatic operations assistant running inside a local AgentPM example app. "
        "Use tools when they materially improve the answer. "
        "Prefer reading live GitHub issue data, CSV files, or JSON data over guessing. "
        "Do not post to Slack or modify GitHub state unless the user clearly asked you to do it. "
        "If the user asks for a draft or preview, do not perform the write action. "
        "Keep answers concise but operationally useful."
    )

    agent = create_agent(
        model=ChatOpenAI(model=OPENAI_MODEL, temperature=0.2, api_key=OPENAI_API_KEY),
        tools=tools,
        system_prompt=system_prompt,
    )
    return loaded_agent, agent, metas


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

    loaded_agent, agent, metas = build_agent()
    history: list[BaseMessage] = []

    print_banner(loaded_agent["manifest"]["name"], metas)

    while True:
        try:
            line = input("ops> ").strip()
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
            print_banner(loaded_agent["manifest"]["name"], metas)
            continue
        if line == "/reset":
            history.clear()
            print("Conversation history cleared.\n")
            continue

        print("\n[thinking]\n")
        try:
            current_messages = [*history, HumanMessage(content=line)]
            result = agent.invoke({"messages": current_messages}, config={"callbacks": [OpsVerboseHandler()]})
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
