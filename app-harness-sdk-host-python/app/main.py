from __future__ import annotations

import os
import signal
import sys
import threading
from typing import Any

from agentpm import HarnessClient
from dotenv import load_dotenv

load_dotenv(".env.local")

ARGS = sys.argv[1:]
PREFLIGHT_ONLY = "--preflight-only" in ARGS
PROMPT = (
    " ".join(arg for arg in ARGS if arg != "--preflight-only").strip()
    or "Use the SDK-hosted Harness example to inspect this generated workspace."
)
AGENTPM_PATH = os.environ.get("AGENTPM") or "agentpm"
USER_SCOPE = os.environ.get("SDK_HOST_USER") or "python-sdk-user"

callbacks: list[str] = []
model_calls = 0
shutting_down = False

client = HarnessClient(
    agentpm_path=AGENTPM_PATH,
    cwd=os.getcwd(),
    config_path="agentpm.harness.json",
    scopes={"user": USER_SCOPE},
)


def model_provider(payload: dict[str, Any]) -> dict[str, Any]:
    # Replace this deterministic provider with your internal model gateway.
    global model_calls
    model_calls += 1
    request = payload.get("request", payload)
    phase = phase_id(request)

    if phase == "reason":
        return completion(
            "reason-complete",
            "act",
            {
                "summary": (
                    "The Python SDK host app is ready to proceed. It registered "
                    "a host model provider, before-model Hook, and approval controller."
                ),
                "next": "Proceed to the approved act phase.",
            },
        )

    if phase == "act":
        return {
            "id": f"python-host-act-{model_calls}",
            "assistant_content": (
                "The approved action phase ran through the Python SDK host. "
                "No external side effect was needed for this scaffold."
            ),
            "actions": [],
            "usage": usage(),
            "finish_reason": "stop",
            "provider_metadata": {"template": "harness-sdk-host-python", "phase": phase},
        }

    return completion(
        "reflect-complete",
        "complete",
        {
            "summary": (
                "The run completed through the Python SDK machine host with events, "
                "usage, checkpoint approval, and report generation."
            )
        },
    )


def before_model_request(input: dict[str, Any]) -> dict[str, Any]:
    phase = phase_id(input)
    callbacks.append(f"before_model_request:{phase}")
    return {
        "decision": "continue",
        "patch": {
            # Attach request-scoped UI, API, policy, or service context here.
            "context_sections": [
                {
                    "title": "Python SDK host note",
                    "content": (
                        "This run is using a Python-hosted model provider, "
                        "Hook, and approval callback."
                    ),
                }
            ]
        },
    }


def approval(request: dict[str, Any]) -> str:
    checkpoint = request.get("checkpoint") if isinstance(request, dict) else None
    checkpoint_id = checkpoint.get("id") if isinstance(checkpoint, dict) else "unknown"
    callbacks.append(f"approval:{checkpoint_id}")
    return "approve"


def handle_sigint(_signum: int, _frame: object) -> None:
    global shutting_down
    if shutting_down:
        return
    shutting_down = True
    try:
        client.cancel_run()
    except Exception:
        pass
    try:
        client.shutdown()
    except Exception:
        pass
    raise SystemExit(130)


signal.signal(signal.SIGINT, handle_sigint)

client.register_model_provider(
    "python-host-model",
    model_provider,
    {
        "model": "deterministic-python-host",
        "context_window_tokens": 8000,
    },
).on_before_model_request(
    before_model_request, registry_id="sdk-before-model"
).on_approval(approval)


def main() -> None:
    session = client.initialize()
    print_session(session)

    event_thread = threading.Thread(target=print_events, daemon=True)
    event_thread.start()

    preflight = client.preflight()
    status = known_or(preflight_status(preflight), preflight_status(session))
    print(f"Preflight status: {status}")
    if status not in {"ready", "ready_with_warnings"}:
        print(preflight_diagnostics(preflight, session))

    if PREFLIGHT_ONLY:
        registrations = client.host_service_registrations()
        print(f"Host services: {len(registrations)}")
        for registration in registrations:
            service = registration.get("service", {})
            print(
                f"- {service.get('role')}:{service.get('registry_id')} "
                f"active={registration.get('active')}"
            )
        client.shutdown()
        return

    try:
        # A web route, queue worker, or CLI command can call this same run boundary.
        result = client.run(
            PROMPT,
            metadata={"source": "harness-sdk-host-python-template"},
        )
        report = result.get("report") if isinstance(result.get("report"), dict) else {}
        print(f"Run terminal status: {result.get('status') or report.get('terminal_status', 'unknown')}")
        print(f"Callbacks: {', '.join(callbacks) if callbacks else 'none'}")
        print(f"Model calls: {model_calls}")
        print(f"Report returned: {'yes' if report else 'no'}")
        print(f"Trace path: {report.get('trace_path', 'not reported')}")
    finally:
        client.shutdown()


def print_events() -> None:
    for event in client.events():
        if interesting_event(event):
            run = f" {event.get('run_id')}" if event.get("run_id") else ""
            print(f"[event] {event.get('event_type')}{run}")


def completion(id_prefix: str, outcome: str, output: dict[str, str]) -> dict[str, Any]:
    return {
        "id": f"{id_prefix}-{model_calls}",
        "assistant_content": None,
        "actions": [
            {
                "id": f"{id_prefix}-action-{model_calls}",
                "action": {
                    "type": "phase_completion",
                    "outcome": outcome,
                    "output": output,
                },
            }
        ],
        "usage": usage(),
        "finish_reason": "tool_calls",
        "provider_metadata": {"template": "harness-sdk-host-python", "outcome": outcome},
    }


def usage() -> dict[str, int]:
    return {
        "input_tokens": 120,
        "output_tokens": 36,
        "total_tokens": 156,
    }


def phase_id(value: dict[str, Any]) -> str:
    phase = value.get("phase")
    if isinstance(phase, dict):
        if isinstance(phase.get("phase_id"), str):
            return phase["phase_id"]
        if isinstance(phase.get("id"), str):
            return phase["id"]
    if isinstance(value.get("phase_id"), str):
        return value["phase_id"]
    if model_calls <= 1:
        return "reason"
    if model_calls == 2:
        return "act"
    return "reflect"


def interesting_event(event: dict[str, Any]) -> bool:
    return event.get("event_type") in {
        "run_started",
        "phase_started",
        "approval_requested",
        "approval_approved",
        "phase_result_ready",
        "run_completed",
    }


def session_id(value: dict[str, Any]) -> str:
    nested = value.get("session")
    if isinstance(nested, dict) and isinstance(nested.get("session_id"), str):
        return nested["session_id"]
    current = value.get("session_id")
    return current if isinstance(current, str) else "unknown"


def print_session(value: dict[str, Any]) -> None:
    current = session_id(value)
    print("Harness session initialized" if current == "unknown" else f"Harness session {current}")


def preflight_status(value: dict[str, Any]) -> str:
    nested = value.get("preflight")
    if isinstance(nested, dict) and isinstance(nested.get("status"), str):
        return nested["status"]
    current = value.get("status")
    return current if isinstance(current, str) else "unknown"


def preflight_diagnostics(value: dict[str, Any], fallback: dict[str, Any]) -> list[Any]:
    nested = value.get("preflight")
    if isinstance(nested, dict) and isinstance(nested.get("diagnostics"), list):
        return nested["diagnostics"]
    current = value.get("diagnostics")
    if isinstance(current, list):
        return current
    fallback_nested = fallback.get("preflight")
    if isinstance(fallback_nested, dict) and isinstance(
        fallback_nested.get("diagnostics"), list
    ):
        return fallback_nested["diagnostics"]
    return []


def known_or(current: str, fallback: str) -> str:
    return fallback if current == "unknown" else current


if __name__ == "__main__":
    main()
