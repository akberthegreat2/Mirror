"""Deterministic, immutable configuration for Mirror applications."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mirror_core.exceptions import ConfigurationError
from mirror_core.toml import load as toml_load


class MirrorSettings(BaseSettings):
    """Root settings resolved from environment, files, and runtime values."""

    model_config = SettingsConfigDict(
        env_prefix="MIRROR_",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
    )

    application_name: str = "mirror"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    max_concurrency: int = Field(default=10, ge=1)
    components: dict[str, dict[str, Any]] = Field(default_factory=dict)
    component_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    middleware: dict[str, list[str]] = Field(default_factory=dict)
    middleware_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    global_middleware: list[str] = Field(default_factory=list)
    worker_backend: str = "inline"
    worker_settings: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, SecretStr] = Field(default_factory=dict)

    @field_validator("secrets", mode="before")
    @classmethod
    def coerce_secrets(cls, value: Any) -> dict[str, SecretStr]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {key: secret if isinstance(secret, SecretStr) else SecretStr(str(secret)) for key, secret in value.items()}
        raise ValueError("secrets must be a mapping")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize settings with secret values redacted."""
        data = super().model_dump(**kwargs)
        if "secrets" in data:
            data["secrets"] = {key: "***REDACTED***" for key in self.secrets}
        return data

    def model_dump_json(self, **kwargs: Any) -> str:
        """Serialize settings as JSON with secret values redacted."""
        return json.dumps(self.model_dump(mode="json"), **kwargs)

    def raw_dump(self) -> dict[str, Any]:
        """Return internal Python values without redacting secrets."""
        return BaseSettings.model_dump(self, mode="python")

    @classmethod
    def from_file(cls, path: Path | str) -> MirrorSettings:
        """Load settings from YAML, TOML, or JSON."""
        path = Path(path)
        try:
            if path.suffix in {".yaml", ".yml"}:
                try:
                    import yaml
                except ImportError as exc:
                    raise ConfigurationError("YAML configuration requires the 'yaml' extra") from exc
                with path.open("r", encoding="utf-8") as stream:
                    data = yaml.safe_load(stream) or {}
            elif path.suffix == ".toml":
                with path.open("rb") as stream:
                    data = toml_load(stream)
            elif path.suffix == ".json":
                with path.open("r", encoding="utf-8") as stream:
                    data = json.load(stream)
            else:
                raise ConfigurationError(f"Unsupported configuration format: {path.suffix}")
        except OSError as exc:
            raise ConfigurationError(f"Unable to read configuration file: {path}") from exc
        return cls.model_validate(data)

    @classmethod
    def from_env(cls) -> MirrorSettings:
        """Resolve settings from model defaults and environment variables."""
        return cls()

    @classmethod
    def merge(cls, *overrides: MirrorSettings) -> MirrorSettings:
        """Deep-merge settings instances with later values taking precedence."""
        merged: dict[str, Any] = {}
        for settings in overrides:
            merged = _deep_merge(merged, settings.raw_dump())
        return cls.model_validate(merged)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
