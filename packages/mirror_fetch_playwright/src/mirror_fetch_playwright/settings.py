"""Settings for the Playwright Fetch provider."""

from typing import Literal

from pydantic import BaseModel, Field


class PlaywrightSettings(BaseModel):
    default_timeout: float = Field(default=30.0, gt=0.0)
    user_agent: str = "Mirror/0.1"
    wait_until: Literal["load", "domcontentloaded", "networkidle", "commit"] = "load"
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    viewport_width: int = Field(default=1280, ge=320)
    viewport_height: int = Field(default=720, ge=240)
