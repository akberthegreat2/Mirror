"""HTTPX provider settings."""

from pydantic import BaseModel, Field


class HTTPXSettings(BaseModel):
    """Provider-specific settings for HTTPX.

    Attributes:
        default_timeout: Default timeout in seconds.
        user_agent: User-Agent header to send.
        follow_redirects: Automatically follow redirects.
        max_redirects: Maximum number of redirects to follow.
        max_response_size: Maximum response size in bytes (None = unlimited).
    """

    default_timeout: float = Field(default=30.0, gt=0.0)
    user_agent: str = "Mirror/0.1"
    follow_redirects: bool = True
    max_redirects: int = Field(default=20, ge=1, le=100)
    max_response_size: int | None = Field(default=None, gt=0)
