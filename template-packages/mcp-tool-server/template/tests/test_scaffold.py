from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_readme_documents_real_mcp_surface(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("agentpm serve --mcp", readme)
        self.assertIn("HTTP-only", readme)
        self.assertIn('"method": "initialize"', readme)
        self.assertIn('"method": "tools/list"', readme)
        self.assertIn('"method": "tools/call"', readme)

    def test_readme_references_curated_tool_names(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("@zack/document-convert", readme)
        self.assertIn("@zack/summarize-text", readme)
        self.assertIn("@zack/translate-text", readme)
        self.assertIn("zack__document_convert", readme)

    def test_sample_doc_exists(self) -> None:
        self.assertTrue((ROOT / "sample-inputs" / "hello.md").exists())


if __name__ == "__main__":
    unittest.main()
