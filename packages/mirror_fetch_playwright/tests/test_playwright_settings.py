"""Tests for Playwright-style settings."""

from mirror_fetch_playwright.settings import PlaywrightSettings


def test_defaults() -> None:
    """Default settings should be stable."""
    settings = PlaywrightSettings()
    assert settings.default_timeout == 30.0
    assert settings.user_agent == "Mirror/0.1"
    assert settings.wait_until == "load"
    assert settings.headless is True
    assert settings.viewport_width == 1280
    assert settings.viewport_height == 720
