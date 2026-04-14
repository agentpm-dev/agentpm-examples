from __future__ import annotations

import unittest

from csv_query import query_csv


CSV = """name,team,score
Ada,red,3
Ben,blue,7
Cara,red,5
"""


class CsvQueryTests(unittest.TestCase):
    def test_filters_and_selects_rows(self) -> None:
        out = query_csv(
            csv_text=CSV,
            filter=[{"column": "score", "op": "gte", "value": "5"}],
            select=["name", "score"],
            sort=[{"column": "score", "direction": "desc"}],
        )
        self.assertEqual(out["row_count"], 2)
        self.assertEqual(out["rows"][0]["name"], "Ben")

    def test_groups_and_aggregates(self) -> None:
        out = query_csv(
            csv_text=CSV,
            group_by=["team"],
            aggregations=[{"op": "count", "as": "members"}, {"op": "sum", "column": "score", "as": "total_score"}],
        )
        red = next(row for row in out["rows"] if row["team"] == "red")
        self.assertEqual(red["members"], 2)
        self.assertEqual(red["total_score"], 8)


if __name__ == "__main__":
    unittest.main()
