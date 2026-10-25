import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx
from openai import OpenAI
import pydantic_core

from summarize_text import ToolError, summarize


class SummarizeTests(unittest.TestCase):
    def test_real_client_parses_response_without_network(self):
        requests = []

        def respond(request):
            requests.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-fixture",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "gpt-4o-mini",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "A short summary.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

        with httpx.Client(transport=httpx.MockTransport(respond)) as http:
            with OpenAI(api_key="test-not-a-real-key", http_client=http) as client:
                with patch.dict(os.environ, OPENAI_API_KEY="test-not-a-real-key"):
                    with patch("summarize_text.OpenAI", return_value=client):
                        self.assertEqual(
                            summarize("Fixture text", max_words=60),
                            {"summary": "A short summary."},
                        )
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["model"], "gpt-4o-mini")
        self.assertIn("<= 60 words", requests[0]["messages"][1]["content"])
        # Import and use the compiled dependency instead of trusting a manifest claim.
        self.assertEqual(pydantic_core.from_json(b'{"native":true}'), {"native": True})

    def test_missing_key_is_value_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ToolError) as error:
                summarize("Fixture text")
        self.assertEqual(error.exception.code, "INPUT_MISSING_API_KEY")

    def test_empty_summary_is_value_error(self):
        with patch.dict(os.environ, OPENAI_API_KEY="test-not-a-real-key"):
            with patch("summarize_text.OpenAI") as factory:
                factory.return_value.chat.completions.create.return_value = (
                    SimpleNamespace(choices=[])
                )
                with self.assertRaises(ToolError) as error:
                    summarize("Fixture text")
        self.assertEqual(error.exception.code, "EMPTY_SUMMARY")

    def test_provider_failure_keeps_error_contract(self):
        with patch.dict(os.environ, OPENAI_API_KEY="test-not-a-real-key"):
            with patch("summarize_text.OpenAI") as factory:
                factory.return_value.chat.completions.create.side_effect = RuntimeError(
                    "fixture failure"
                )
                with self.assertRaises(ToolError) as error:
                    summarize("Fixture text")
        self.assertEqual(error.exception.code, "MODEL_CALL_FAILED")
        self.assertEqual(error.exception.details, {"cause": "fixture failure"})

    def test_entrypoint_json_contract(self):
        environment = dict(os.environ)
        environment.pop("OPENAI_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "-u", "-m", "summarize_text"],
            input=json.dumps({"text": "Fixture text", "max_words": 60}),
            text=True,
            capture_output=True,
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "INPUT_MISSING_API_KEY")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
