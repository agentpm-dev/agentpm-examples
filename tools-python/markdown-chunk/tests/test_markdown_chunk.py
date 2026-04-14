from __future__ import annotations

import unittest

from markdown_chunk import chunk_markdown


SAMPLE = """# Intro

AgentPM packages reusable agent primitives.

## Install

Install the tool once.

Install it everywhere.

## Use

Use the same artifact across runtimes.
"""


class MarkdownChunkTests(unittest.TestCase):
    def test_heading_context_is_preserved(self) -> None:
        out = chunk_markdown(text=SAMPLE, strategy="hybrid", max_chars=120, overlap=10, source_id="doc-1")
        self.assertGreaterEqual(len(out["chunks"]), 2)
        self.assertEqual(out["chunks"][0]["heading_path"], ["Intro"])
        self.assertEqual(out["chunks"][1]["heading_path"], ["Intro", "Install"])

    def test_offsets_and_ids_exist(self) -> None:
        out = chunk_markdown(text=SAMPLE, strategy="paragraph", max_chars=120, overlap=0)
        chunk = out["chunks"][0]
        self.assertIn("id", chunk)
        self.assertGreaterEqual(chunk["start_offset"], 0)
        self.assertGreater(chunk["end_offset"], chunk["start_offset"])


if __name__ == "__main__":
    unittest.main()
