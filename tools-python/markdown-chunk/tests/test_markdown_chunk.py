from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

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

    def test_overlap_is_applied_when_a_chunk_overflows(self) -> None:
        paragraphs = "\n\n".join(
            [
                "AgentPM makes tools portable across runtimes.",
                "Install once and reuse the same artifact in multiple agents.",
                "Chunking should preserve some context across chunk boundaries.",
            ]
        )
        text = f"# Intro\n\n{paragraphs}"
        out = chunk_markdown(text=text, strategy="paragraph", max_chars=140, overlap=12)
        self.assertGreaterEqual(len(out["chunks"]), 2)

        first_text = out["chunks"][0]["text"]
        second_text = out["chunks"][1]["text"]
        overlap_text = first_text[-12:]

        self.assertEqual(second_text[:12], overlap_text)
        self.assertIn(overlap_text.strip(), second_text)

    def test_single_oversized_paragraph_is_split_with_fallbacks(self) -> None:
        long_paragraph = " ".join(["portable"] * 40)
        text = f"# Intro\n\n{long_paragraph}"
        out = chunk_markdown(text=text, strategy="paragraph", max_chars=120, overlap=8)

        self.assertGreaterEqual(len(out["chunks"]), 2)
        for chunk in out["chunks"]:
            self.assertLessEqual(chunk["char_count"], 120)

    def test_metadata_reports_fallback_order(self) -> None:
        out = chunk_markdown(text=SAMPLE, strategy="hybrid", max_chars=120, overlap=10)
        self.assertEqual(out["metadata"]["fallback_order"], ["heading", "paragraph", "sentence", "window"])


if __name__ == "__main__":
    unittest.main()
