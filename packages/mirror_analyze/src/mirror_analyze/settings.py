"""Settings for the Analyze capability."""

from pydantic import BaseModel, Field


class AnalyzeSettings(BaseModel):
    """Runtime settings for content analysis."""

    keyword_limit: int = Field(default=12, ge=1, le=100)
    summary_words: int = Field(default=32, ge=8, le=256)
    prefer_spacy: bool = True
