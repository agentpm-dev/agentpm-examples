from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from document_convert import convert_document


class DocumentConvertTests(unittest.TestCase):
    def test_converts_html_to_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "sample.html"
            path.write_text("<html><body><h1>Doc</h1><p>Hello <a href='https://example.com'>world</a></p></body></html>")
            out = convert_document(path=str(path), to_format="markdown")
            self.assertIn("# Doc", out["content"])
            self.assertIn("(https://example.com)", out["content"])

    def test_converts_csv_to_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "sample.csv"
            path.write_text("name,score\nAda,5\nBen,7\n")
            out = convert_document(path=str(path), to_format="text")
            self.assertIn("name, score", out["content"])
            self.assertEqual(out["media_type"], "text/csv")

    def test_includes_metadata_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "sample.md"
            path.write_text("# Title\n\nLine one.\nLine two.\n")
            out = convert_document(path=str(path), to_format="markdown", extract_metadata=True)
            self.assertEqual(out["metadata"]["file_name"], "sample.md")
            self.assertEqual(out["metadata"]["line_count"], 4)
            self.assertEqual(out["metadata"]["output_format"], "markdown")
            self.assertGreater(out["metadata"]["size_bytes"], 0)

    def test_converts_json_to_markdown_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "sample.json"
            path.write_text('{"name":"Ada","score":5}')

            markdown_out = convert_document(path=str(path), to_format="markdown")
            text_out = convert_document(path=str(path), to_format="text")

            self.assertIn("```json", markdown_out["content"])
            self.assertIn('"name": "Ada"', markdown_out["content"])
            self.assertEqual(text_out["media_type"], "application/json")
            self.assertIn('"score": 5', text_out["content"])


if __name__ == "__main__":
    unittest.main()
