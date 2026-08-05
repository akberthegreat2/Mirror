"""Settings for the Playwright-style fetch provider."""

from pydantic import BaseModel, Field


class PlaywrightSettings(BaseModel):
    """Configuration for the Playwright-style fetch provider.

    Attributes:
        default_timeout: Default timeout in seconds.
        user_agent: User-Agent header to send when fetching resources.
        wait_until: Browser-style navigation wait hint retained for future parity.
        headless: Whether a browser backend should run headless when enabled.
        viewport_width: Default viewport width retained for future browser parity.
        viewport_height: Default viewport height retained for future browser parity.
    """

    default_timeout: float = Field(default=30.0, gt=0.0)
    user_agent: str = "Mirror/0.1"
    wait_until: str = Field(default="load", pattern=r"^(load|domcontentloaded|networkidle)$")
    headless: bool = True
    viewport_width: int = Field(default=1280, ge=320)
    viewport_height: int = Field(default=720, ge=240)
