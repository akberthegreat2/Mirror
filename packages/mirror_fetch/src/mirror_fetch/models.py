"""Request and response models for the Fetch capability."""

from pydantic import BaseModel, Field, HttpUrl


class FetchRequest(BaseModel):
    """Input for a fetch operation.

    Attributes:
        url: The URL to fetch.
        timeout: Request timeout in seconds. Provider may override.
        headers: Additional headers to include in the request.
        method: HTTP method to use.
        body: Optional request body for POST/PUT requests.
    """

    url: HttpUrl
    timeout: float | None = Field(default=None, gt=0.0)
    headers: dict[str, str] = Field(default_factory=dict)
    method: str = Field(
        default="GET",
        pattern=r"^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)$",
    )
    body: bytes | None = None


class FetchResult(BaseModel):
    """Output of a fetch operation.

    Attributes:
        url: The final URL after redirects.
        status_code: HTTP status code.
        headers: Response headers.
        content: Raw response body.
        encoding: Detected or declared character encoding.
        content_type: Content-Type header value.
        content_length: Content-Length header value (if present).
        fetch_duration: Time in seconds for the fetch operation.
        timestamp: ISO 8601 timestamp of when the fetch completed.
    """

    url: str
    status_code: int = Field(..., ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    content: bytes
    encoding: str = "utf-8"
    content_type: str | None = None
    content_length: int | None = None
    fetch_duration: float = Field(..., ge=0.0)
    timestamp: str  # ISO 8601
