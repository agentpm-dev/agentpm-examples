from __future__ import annotations

import unittest

from json_transform import transform_json


class JsonTransformTests(unittest.TestCase):
    def test_object_transform_pipeline(self) -> None:
        out = transform_json(
            input={"user": {"name": "Ada", "role": "admin"}, "active": True},
            operations=[
                {"op": "pluck", "path": "user.name", "as": "name"},
                {"op": "set", "path": "source", "value": "agentpm"},
            ],
        )
        self.assertEqual(out["result"]["name"], "Ada")
        self.assertEqual(out["result"]["source"], "agentpm")
        self.assertEqual(out["validation_errors"], [])

    def test_filter_array_operation(self) -> None:
        out = transform_json(
            input=[{"id": 1, "status": "open"}, {"id": 2, "status": "closed"}],
            operations=[{"op": "filter_array", "path": "status", "equals": "open"}],
        )
        self.assertEqual(out["result"], [{"id": 1, "status": "open"}])


if __name__ == "__main__":
    unittest.main()
