"""Centralized FrameNest settings loading boundary."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
import tempfile
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_FILE = Path(".env")
DEVELOPMENT_DATABASE_DIRECTORY = "framenest-development"
DEVELOPMENT_DATABASE_FILENAME = "catalog.sqlite3"
SUPPORTED_AI_PROVIDER_IDS = frozenset({"nvidia-nim", "vercel-ai-gateway"})


def _default_database_path() -> Path:
    return _normalize_database_path(
        Path(tempfile.gettempdir())
        / DEVELOPMENT_DATABASE_DIRECTORY
        / DEVELOPMENT_DATABASE_FILENAME
    )


def _normalize_database_path(value: Any) -> Path:
    try:
        path = Path(value).expanduser()
    except (RuntimeError, TypeError, ValueError) as exc:
        raise ValueError("database path must be an absolute path") from exc
    if not path.is_absolute():
        raise ValueError("database path must be an absolute path")
    return path.resolve(strict=False)


class FrameNestSettings(BaseSettings):
    """Typed application settings loaded outside the domain layer."""

    model_config = SettingsConfigDict(
        env_prefix="FRAMENEST_",
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=0, le=65535)
    api_key: SecretStr | None = Field(default=None)
    database_path: Path = Field(default_factory=_default_database_path, repr=False)
    ai_provider_id: str | None = Field(default=None)
    ai_model_id: str | None = Field(default=None)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        try:
            ip_address(value)
        except ValueError as exc:
            raise ValueError("host must be a valid IP address") from exc
        return value

    @field_validator("database_path", mode="before")
    @classmethod
    def validate_database_path(cls, value: Any) -> Path:
        return _normalize_database_path(value)

    @field_validator("ai_provider_id")
    @classmethod
    def validate_ai_provider_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if normalized not in SUPPORTED_AI_PROVIDER_IDS:
            raise ValueError("ai provider id is not supported")
        return normalized

    @field_validator("ai_model_id")
    @classmethod
    def validate_ai_model_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized or len(normalized) > 200:
            raise ValueError("ai model id must be non-empty when provided")
        return normalized


def load_settings(
    *,
    env_file: Path | str | None = DEFAULT_ENV_FILE,
) -> FrameNestSettings:
    """Load settings with deterministic precedence for the given env file."""
    if env_file is None:
        return FrameNestSettings(_env_file=None)
    return FrameNestSettings(_env_file=env_file)
