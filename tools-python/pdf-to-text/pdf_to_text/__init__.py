from __future__ import annotations

import base64
import io
import re
from typing import Any, Dict, List, Optional

import httpx
from pypdf import PdfReader

class ToolError(Exception):
    def __init__(self, code: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.code = code
        self.details = details

def _normalize_whitespace(text: str) -> str:
    """
    Collapse excessive whitespace/newlines. Keeps things compact for LLMs.
    """
    return re.sub(r"\s+", " ", text).strip()

def _fetch_pdf_bytes_from_url(pdf_url: str, user_agent: Optional[str]) -> bytes:
    headers: Dict[str, str] = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    else:
        headers["User-Agent"] = "agentpm-pdf-to-text/0.1"

    try:
        resp = httpx.get(pdf_url, headers=headers, timeout=30.0)
    except Exception as e:
        raise ToolError(
            "FETCH_FAILED",
            f"Failed to fetch PDF from URL: {pdf_url}",
            details={"url": pdf_url, "error": str(e)},
        )

    if resp.status_code != 200:
        raise ToolError(
            "FETCH_FAILED",
            f"Unexpected status code {resp.status_code} when fetching PDF",
            details={"url": pdf_url, "status_code": resp.status_code},
        )

    content_type = resp.headers.get("content-type", "")
    # Not strictly required, but nice to sanity-check
    if "pdf" not in content_type.lower():
        # Don't hard-fail, but include in details
        return resp.content

    return resp.content

def _decode_pdf_base64(pdf_base64: str) -> bytes:
    try:
        return base64.b64decode(pdf_base64, validate=True)
    except Exception as e:
        raise ToolError(
            "INPUT_INVALID",
            "Invalid base64-encoded PDF data",
            details={"error": str(e)},
        )

def _chunk_text_from_pages(
        pages: List[Dict[str, Any]],
        max_chars: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Build contiguous text chunks across pages, roughly max_chars each.
    Each chunk records the page range that contributed to it.
    """
    chunks: List[Dict[str, Any]] = []
    current_parts: List[str] = []
    current_len = 0
    current_start_page: Optional[int] = None
    current_end_page: Optional[int] = None

    def flush_chunk() -> None:
        nonlocal current_parts, current_len, current_start_page, current_end_page
        if not current_parts:
            return
        index = len(chunks)
        chunks.append(
            {
                "index": index,
                "start_page": current_start_page,
                "end_page": current_end_page,
                "text": "".join(current_parts).strip(),
            }
        )
        current_parts = []
        current_len = 0
        current_start_page = None
        current_end_page = None

    for page in pages:
        page_num: int = page["page_number"]
        text: str = page["text"]
        if not text:
            continue

        # Ensure we at least attribute the page range correctly
        if current_start_page is None:
            current_start_page = page_num

        remaining = text
        while remaining:
            space_left = max_chars - current_len
            if space_left <= 0:
                current_end_page = page_num
                flush_chunk()
                current_start_page = page_num  # new chunk starts on this page

            take = remaining[:space_left] if space_left < len(remaining) else remaining
            current_parts.append(take)
            current_len += len(take)
            remaining = remaining[len(take) :]

            current_end_page = page_num

    flush_chunk()
    return chunks

def convert(
    *,
    pdf_url: Optional[str] = None,
    pdf_base64: Optional[str] = None,
    max_pages: Optional[int] = None,
    strip_whitespace: bool = True,
    user_agent: Optional[str] = None,
    split_by: str = "page",
) -> dict:
    """
    Core tool entrypoint. Called from __main__.py as convert(**payload).
    Returns a dict that gets merged into {"ok": True, ...} by __main__.
    """

    # Validate source
    if bool(pdf_url) == bool(pdf_base64):
        # Either both set or both None
        raise ToolError(
            "INPUT_INVALID",
            "Exactly one of 'pdf_url' or 'pdf_base64' must be provided",
            details={"pdf_url_provided": bool(pdf_url), "pdf_base64_provided": bool(pdf_base64)},
        )

    if split_by not in ("page", "chunk"):
        raise ToolError(
            "INPUT_INVALID",
            "split_by must be 'page' or 'chunk'",
            details={"split_by": split_by},
        )

    # Load bytes
    if pdf_url:
        pdf_bytes = _fetch_pdf_bytes_from_url(pdf_url, user_agent)
        source = "url"
        source_url = pdf_url
    else:
        pdf_bytes = _decode_pdf_base64(pdf_base64 or "")
        source = "base64"
        source_url = None

    # Parse PDF
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ToolError(
            "PARSE_FAILED",
            "Failed to read PDF",
            details={"error": str(e)},
        )

    page_count = len(reader.pages)
    # Determine page range
    if max_pages is not None:
        if max_pages <= 0:
            raise ToolError(
                "INPUT_INVALID",
                "max_pages must be a positive integer",
                details={"max_pages": max_pages},
            )
        limit = min(max_pages, page_count)
    else:
        limit = page_count

    pages: List[Dict[str, Any]] = []

    for idx in range(limit):
        page = reader.pages[idx]
        try:
            text = page.extract_text() or ""
        except Exception as e:
            raise ToolError(
                "PARSE_FAILED",
                f"Failed to extract text from page {idx + 1}",
                details={"page_number": idx + 1, "error": str(e)},
            )
        if strip_whitespace:
            text = _normalize_whitespace(text)
        pages.append(
            {
                "page_number": idx + 1,  # 1-based
                "text": text,
            }
        )

    raw_text = "\n\n".join(p["text"] for p in pages if p["text"])

    result: Dict[str, Any] = {
        "pages": pages,
        "raw_text": raw_text,
        "metadata": {
            "page_count": page_count,
            "truncated": limit < page_count,
            "source": source,
        },
    }
    if source_url is not None:
        result["metadata"]["url"] = source_url

    if split_by == "chunk":
        result["chunks"] = _chunk_text_from_pages(pages)

    return result