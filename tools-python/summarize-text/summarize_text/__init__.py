import os
from openai import OpenAI
from typing import Any

class ToolError(Exception):
    def __init__(self, code: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.code = code
        self.details = details

def summarize(text: str, max_words: int = 200) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ToolError("INPUT_MISSING_API_KEY", "OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)

    try:
        sys = "You are a precise technical summarizer. Output within the requested word budget."
        user = f"Summarize in <= {max_words} words:\n\n{text}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            temperature=0.2,
        )
    except Exception as e:
        raise ToolError("MODEL_CALL_FAILED", "OpenAI request failed", {"cause": str(e)})

    content = resp.choices[0].message.content if resp.choices else ""
    if not content:
        raise ToolError("EMPTY_SUMMARY", "Model returned empty content")
    return {"summary": content}
