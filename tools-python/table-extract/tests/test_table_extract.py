from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from table_extract import extract_tables


HTML = """
<html>
  <body>
    <table>
      <tr><th>Name</th><th>Score</th></tr>
      <tr><td>Ada</td><td>5</td></tr>
      <tr><td>Ben</td><td>7</td></tr>
    </table>
  </body>
</html>
"""


class TableExtractTests(unittest.TestCase):
    def test_extracts_html_table(self) -> None:
        out = extract_tables(source_type="html", html_text=HTML, table_index=0)
        self.assertEqual(out["detected_count"], 1)
        self.assertEqual(out["tables"][0]["columns"], ["Name", "Score"])
        self.assertEqual(out["tables"][0]["rows"][0]["Name"], "Ada")

    def test_extracts_csv_as_single_table(self) -> None:
        out = extract_tables(source_type="csv", csv_text="name,score\nAda,5\nBen,7\n")
        self.assertEqual(out["tables"][0]["rows"][1]["score"], "7")
        self.assertEqual(out["metadata"]["source_type"], "csv")

    def test_auto_source_type_with_path_detects_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "sample.csv"
            path.write_text("name,score\nAda,5\nBen,7\n")
            out = extract_tables(source_type="auto", path=str(path))
            self.assertEqual(out["detected_count"], 1)
            self.assertEqual(out["tables"][0]["columns"], ["name", "score"])

    def test_table_index_selects_second_html_table(self) -> None:
        html = """
        <html><body>
          <table>
            <tr><th>Name</th></tr>
            <tr><td>Ada</td></tr>
          </table>
          <table>
            <tr><th>Team</th><th>Lead</th></tr>
            <tr><td>Docs</td><td>Ben</td></tr>
          </table>
        </body></html>
        """
        out = extract_tables(source_type="html", html_text=html, table_index=1)
        self.assertEqual(out["detected_count"], 2)
        self.assertEqual(out["tables"][0]["columns"], ["Team", "Lead"])
        self.assertEqual(out["tables"][0]["rows"][0]["Lead"], "Ben")

    def test_header_row_false_generates_default_columns(self) -> None:
        out = extract_tables(
            source_type="csv",
            csv_text="Ada,5\nBen,7\n",
            header_row=False,
        )
        self.assertEqual(out["tables"][0]["columns"], ["column_1", "column_2"])
        self.assertEqual(out["tables"][0]["rows"][0]["column_1"], "Ada")

    def test_returns_warning_when_no_html_tables_are_found(self) -> None:
        out = extract_tables(source_type="html", html_text="<html><body><p>No tables here</p></body></html>")
        self.assertEqual(out["detected_count"], 0)
        self.assertEqual(out["tables"], [])
        self.assertIn("No HTML tables were detected.", out["warnings"])


if __name__ == "__main__":
    unittest.main()
