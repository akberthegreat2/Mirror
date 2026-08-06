"""Settings for the Monitor capability."""

from pydantic import BaseModel, Field


class MonitorSettings(BaseModel):
    """Runtime settings for content monitoring."""

    user_agent: str = "MirrorWebInfra/1.0"
    timeout_seconds: float = Field(default=20.0, gt=0.0)
    persist_state: bool = True
