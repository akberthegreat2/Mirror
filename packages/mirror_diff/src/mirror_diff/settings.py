"""Settings for the Diff capability."""

from pydantic import BaseModel, Field


class DiffSettings(BaseModel):
    """Runtime settings for document diffing."""

    ignore_whitespace: bool = True
    ignore_case: bool = False
    context_lines: int = Field(default=3, ge=0, le=20)
