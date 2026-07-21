"""Centralized FrameNest settings loading boundary."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
import tempfile
from typing import Any
import uuid

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from framenest.domain.media_analysis_runs import (
    DEFAULT_MAX_ANALYSIS_ATTEMPTS,
    MAX_CONFIGURED_ANALYSIS_ATTEMPTS,
)

DEFAULT_ENV_FILE = Path(".env")
DEVELOPMENT_DATABASE_DIRECTORY = "framenest-development"
DEVELOPMENT_DATABASE_FILENAME = "catalog.sqlite3"
DEVELOPMENT_GALLERY_PREVIEW_DIRECTORY = "gallery-previews"
DEFAULT_UPLOAD_MAX_TOTAL_BYTES = 1_073_741_824
DEFAULT_UPLOAD_MAX_PATCH_BYTES = 8_388_608
DEFAULT_UPLOAD_SESSION_TTL_SECONDS = 86_400
DEFAULT_UPLOAD_MIN_FREE_SPACE_RESERVE_BYTES = 67_108_864
SUPPORTED_AI_PROVIDER_IDS = frozenset({"nvidia-nim", "vercel-ai-gateway"})


def _default_database_path() -> Path:
    return _normalize_database_path(
        Path(tempfile.gettempdir())
        / DEVELOPMENT_DATABASE_DIRECTORY
        / DEVELOPMENT_DATABASE_FILENAME
    )


def _default_gallery_preview_cache_path() -> Path:
    return _normalize_absolute_path(
        Path(tempfile.gettempdir())
        / DEVELOPMENT_DATABASE_DIRECTORY
        / DEVELOPMENT_GALLERY_PREVIEW_DIRECTORY
    )


def _normalize_absolute_path(value: Any) -> Path:
    try:
        path = Path(value).expanduser()
    except (RuntimeError, TypeError, ValueError) as exc:
        raise ValueError("path must be an absolute path") from exc
    if not path.is_absolute():
        raise ValueError("path must be an absolute path")
    return path.resolve(strict=False)


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
    gallery_preview_cache_path: Path = Field(
        default_factory=_default_gallery_preview_cache_path,
        repr=False,
    )
    upload_quarantine_root: Path | None = Field(default=None, repr=False)
    upload_publication_library_id: str | None = Field(default=None, repr=False)
    upload_max_total_bytes: int = Field(default=DEFAULT_UPLOAD_MAX_TOTAL_BYTES, gt=0)
    upload_max_patch_bytes: int = Field(default=DEFAULT_UPLOAD_MAX_PATCH_BYTES, gt=0)
    upload_session_ttl_seconds: int = Field(
        default=DEFAULT_UPLOAD_SESSION_TTL_SECONDS,
        gt=0,
    )
    upload_min_free_space_reserve_bytes: int = Field(
        default=DEFAULT_UPLOAD_MIN_FREE_SPACE_RESERVE_BYTES,
        ge=0,
    )
    ai_provider_id: str | None = Field(default=None)
    ai_model_id: str | None = Field(default=None)
    automatic_media_analysis_enabled: bool = Field(default=False)
    automatic_media_analysis_max_attempts: int = Field(
        default=DEFAULT_MAX_ANALYSIS_ATTEMPTS,
        ge=1,
        le=MAX_CONFIGURED_ANALYSIS_ATTEMPTS,
    )

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

    @field_validator("gallery_preview_cache_path", mode="before")
    @classmethod
    def validate_gallery_preview_cache_path(cls, value: Any) -> Path:
        try:
            return _normalize_absolute_path(value)
        except ValueError as exc:
            raise ValueError("gallery preview cache path must be an absolute path") from exc

    @field_validator("upload_quarantine_root", mode="before")
    @classmethod
    def validate_upload_quarantine_root(cls, value: Any) -> Path | None:
        if value is None or value == "":
            return None
        try:
            return _normalize_absolute_path(value)
        except ValueError as exc:
            raise ValueError("upload quarantine root must be an absolute path") from exc

    @field_validator("upload_publication_library_id", mode="before")
    @classmethod
    def validate_upload_publication_library_id(cls, value: Any) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise ValueError("upload publication library id must be a UUIDv4")
        try:
            parsed = uuid.UUID(value)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("upload publication library id must be a UUIDv4") from exc
        if (
            str(parsed) != value
            or parsed.variant != uuid.RFC_4122
            or parsed.version != 4
        ):
            raise ValueError("upload publication library id must be a UUIDv4")
        return value

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
