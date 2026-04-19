from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

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

    def test_pick_operation(self) -> None:
        out = transform_json(
            input={"name": "Ada", "role": "admin", "active": True},
            operations=[{"op": "pick", "keys": ["name", "active"]}],
        )
        self.assertEqual(out["result"], {"name": "Ada", "active": True})

    def test_rename_operation(self) -> None:
        out = transform_json(
            input={"full_name": "Ada Lovelace", "role": "admin"},
            operations=[{"op": "rename", "from": "full_name", "to": "name"}],
        )
        self.assertEqual(out["result"], {"name": "Ada Lovelace", "role": "admin"})

    def test_delete_operation(self) -> None:
        out = transform_json(
            input={"user": {"name": "Ada", "role": "admin"}, "active": True},
            operations=[{"op": "delete", "path": "user.role"}],
        )
        self.assertEqual(out["result"], {"user": {"name": "Ada"}, "active": True})

    def test_flatten_operation(self) -> None:
        out = transform_json(
            input={"user": {"name": "Ada", "prefs": {"theme": "dark"}}, "active": True},
            operations=[{"op": "flatten"}],
        )
        self.assertEqual(
            out["result"],
            {"user.name": "Ada", "user.prefs.theme": "dark", "active": True},
        )


if __name__ == "__main__":
    unittest.main()
