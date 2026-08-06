"""Settings for the Scrape capability."""

from pydantic import BaseModel, Field


class ScrapeSettings(BaseModel):
    """Runtime settings for HTML scraping."""

    prefer_trafilatura: bool = True
    extract_links: bool = True
    strip_scripts: bool = True
    max_text_length: int = Field(default=50_000, ge=1_000, le=500_000)
