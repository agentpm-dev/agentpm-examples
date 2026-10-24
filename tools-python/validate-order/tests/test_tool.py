import json
import subprocess
import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

from tool import calculate


class ValidateOrderTests(unittest.TestCase):
    def test_calculates_using_validated_input(self):
        self.assertEqual(calculate('{"quantity":2,"unit_price":4.5}'), {"total": 9.0})

    def test_rejects_invalid_inputs(self):
        for payload in [
            '{"quantity":0,"unit_price":4.5}',
            '{"quantity":"2","unit_price":4.5}',
            '{"quantity":2,"unit_price":-1}',
            '{"quantity":2,"unit_price":true}',
            '{"quantity":2,"unit_price":4.5,"extra":true}',
            '{"quantity":2,"unit_price":NaN}',
            "not JSON",
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                calculate(payload)

    def test_public_json_stdin_stdout_protocol(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "tool.py")],
            input='{"quantity":2,"unit_price":4.5}',
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), {"total": 9.0})
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
