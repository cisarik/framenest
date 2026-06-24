"""Centralized FrameNest settings loading boundary."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_FILE = Path(".env")


class FrameNestSettings(BaseSettings):
    """Typed application settings loaded outside the domain layer."""

    model_config = SettingsConfigDict(
        env_prefix="FRAMENEST_",
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1")
    api_key: SecretStr | None = Field(default=None)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        try:
            ip_address(value)
        except ValueError as exc:
            raise ValueError("host must be a valid IP address") from exc
        return value


def load_settings(
    *,
    env_file: Path | str | None = DEFAULT_ENV_FILE,
) -> FrameNestSettings:
    """Load settings with deterministic precedence for the given env file."""
    if env_file is None:
        return FrameNestSettings(_env_file=None)
    return FrameNestSettings(_env_file=env_file)
