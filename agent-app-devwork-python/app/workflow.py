from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from app.settings import OPENAI_API_KEY, OPENAI_MODEL


WRITE_ACTIONS = {"create_issue", "comment_issue", "update_issue_state"}


class DevworkState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    pending_tool_calls: list[dict[str, Any]] | None


def is_write_tool_call(tool_call: dict[str, Any]) -> bool:
    if tool_call.get("name") != "github-issues":
        return False
    args = tool_call.get("args")
    if not isinstance(args, dict):
        return False
    return args.get("action") in WRITE_ACTIONS


def latest_user_text(state: DevworkState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            if isinstance(message.content, str):
                return message.content.strip()
            return str(message.content).strip()
    return ""


def build_graph(tools: list[Any], skill_manuals: str = "", profile_guidance: str = ""):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.2, api_key=OPENAI_API_KEY).bind_tools(tools)
    tool_node = ToolNode(tools)

    def assistant_node(state: DevworkState) -> dict[str, Any]:
        print("[node] assistant")
        system_content = (
            "You are a pragmatic GitHub maintainer copilot running inside a local AgentPM example app. "
            "Use tools when they materially improve the answer. "
            "Prefer reading GitHub issue data instead of guessing. "
            "If the user seems to want a draft comment or tentative plan, prepare the draft but do not execute a write action. "
            "GitHub write actions must be explicitly approved before execution."
        )
        if skill_manuals:
            system_content += (
                "\n\nFollow these packaged maintainer procedures when they are relevant to the user's request:\n\n"
                f"{skill_manuals}"
            )
        if profile_guidance:
            system_content += (
                "\n\nFollow these packaged Instruction Profiles when they are relevant to the user's request:\n\n"
                f"{profile_guidance}"
            )
        system = AIMessage(
            content=system_content
        )
        response = llm.invoke([system, *state["messages"]])
        return {"messages": [response]}

    def approval_node(state: DevworkState) -> dict[str, Any]:
        print("[node] approval")
        ai_msg = state["messages"][-1]
        assert isinstance(ai_msg, AIMessage)
        tool_calls = ai_msg.tool_calls
        lines = ["A GitHub write action is ready but not executed yet."]
        for call in tool_calls:
            args = call.get("args", {})
            lines.append(f"- {call.get('name')} {args}")
        lines.append("Type /approve to execute it or /cancel to discard it.")
        approval_messages: list[BaseMessage] = []
        if ai_msg.id:
            approval_messages.append(RemoveMessage(id=ai_msg.id))
        approval_messages.append(AIMessage(content="\n".join(lines)))
        return {
            "pending_tool_calls": tool_calls,
            "messages": approval_messages,
        }

    def execute_pending_node(state: DevworkState) -> dict[str, Any]:
        print("[node] execute_pending")
        pending = state.get("pending_tool_calls") or []
        return {
            "pending_tool_calls": None,
            "messages": [AIMessage(content="Executing approved action.", tool_calls=pending)],
        }

    def cancel_pending_node(state: DevworkState) -> dict[str, Any]:
        print("[node] cancel_pending")
        return {
            "pending_tool_calls": None,
            "messages": [AIMessage(content="Pending GitHub write action cancelled.")],
        }

    def route_from_start(state: DevworkState) -> str:
        text = latest_user_text(state).lower()
        if state.get("pending_tool_calls") and text == "/approve":
            return "execute_pending"
        if state.get("pending_tool_calls") and text == "/cancel":
            return "cancel_pending"
        return "assistant"

    def route_after_assistant(state: DevworkState) -> str:
        last = state["messages"][-1]
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return END
        if any(is_write_tool_call(call) for call in last.tool_calls):
            return "approval"
        return "tools"

    graph = StateGraph(DevworkState)
    graph.add_node("assistant", assistant_node)
    graph.add_node("approval", approval_node)
    graph.add_node("tools", tool_node)
    graph.add_node("execute_pending", execute_pending_node)
    graph.add_node("cancel_pending", cancel_pending_node)

    graph.add_conditional_edges(START, route_from_start)
    graph.add_conditional_edges("assistant", route_after_assistant)
    graph.add_edge("approval", END)
    graph.add_edge("cancel_pending", END)
    graph.add_edge("execute_pending", "tools")
    graph.add_edge("tools", "assistant")

    return graph.compile()
