from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Any

_analyzer = SentimentIntensityAnalyzer()

class ToolError(Exception):
    def __init__(self, code: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.code = code
        self.details = details


def analyze(text: str) -> dict:
    scores = _analyzer.polarity_scores(text)
    label = "positive" if scores["compound"] > 0.05 else "negative" if scores["compound"] < -0.05 else "neutral"
    return {"label": label, "scores": scores}