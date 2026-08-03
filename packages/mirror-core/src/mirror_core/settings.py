"""Configuration engine with deterministic precedence.

Precedence (later wins):
    1. Model defaults
    2. Package defaults (set by individual packages)
    3. Configuration file (YAML/TOML/JSON)
    4. Environment variables (MIRROR_*)
    5. Runtime overrides
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MirrorSettings(BaseSettings):
    """Root settings for Mirror application.

    Environment variables are read with prefix "MIRROR_".
    Nested keys use double underscore: MIRROR_COMPONENTS__FETCH__PROVIDER
    """

    model_config = SettingsConfigDict(
        env_prefix="MIRROR_",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
    )

    # Core application metadata
    application_name: str = "mirror"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Component selection: capability → provider name
    components: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Mapping of capability name to provider config",
    )

    # Component settings: capability → provider → settings dict
    component_settings: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Provider-specific settings",
    )

    # Middleware selection: capability → list of middleware names
    middleware: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Per-capability middleware list",
    )

    # Global middleware applied to all capabilities
    global_middleware: list[str] = Field(
        default_factory=list,
        description="Middleware applied to every capability",
    )

    # Secrets (redacted from repr/dumps)
    secrets: dict[str, SecretStr] = Field(
        default_factory=dict,
        description="Secrets redacted from logs",
    )

    @field_validator("secrets", mode="before")
    @classmethod
    def coerce_secrets(cls, v: Any) -> dict[str, SecretStr]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return {k: SecretStr(str(vv)) for k, vv in v.items()}
        raise ValueError("secrets must be a dict")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to redact secrets."""
        data = super().model_dump(**kwargs)
        if "secrets" in data:
            data["secrets"] = {k: "***REDACTED***" for k in data["secrets"]}
        return data

    def model_dump_json(self, **kwargs: Any) -> str:
        """Override to redact secrets in JSON output."""
        return super().model_dump_json(**kwargs)

    @classmethod
    def from_file(cls, path: Path | str) -> MirrorSettings:
        """Load settings from YAML, TOML, or JSON file."""
        import json

        import tomllib

        path = Path(path)
        with open(path, "rb") as f:
            if path.suffix in (".yaml", ".yml"):
                import yaml

                data = yaml.safe_load(f)
            elif path.suffix == ".toml":
                data = tomllib.load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        return cls.model_validate(data)

    @classmethod
    def from_env(cls) -> MirrorSettings:
        """Load from environment variables only (no file)."""
        return cls()

    @classmethod
    def merge(cls, *overrides: MirrorSettings) -> MirrorSettings:
        """Merge multiple settings instances (later wins)."""
        merged: dict[str, Any] = {}
        for settings in overrides:
            merged.update(settings.model_dump())
        return cls.model_validate(merged)
