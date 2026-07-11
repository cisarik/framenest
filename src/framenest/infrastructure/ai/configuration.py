"""Non-secret server AI configuration storage."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from framenest.infrastructure.ai.constants import (
    DEFAULT_MODEL_ID,
    DEFAULT_PROVIDER_ID,
    VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
    VERCEL_AI_GATEWAY_PROVIDER_ID,
)

AI_CONFIG_SCHEMA_VERSION = 1
AI_TEST_STATE_SCHEMA_VERSION = 1
AI_STATUS_SNAPSHOT_SCHEMA_VERSION = 1
AI_CONFIG_PATH_ENVIRONMENT_NAME = "FRAMENEST_AI_CONFIG_PATH"
SUPPORTED_PROVIDER_IDS = frozenset({DEFAULT_PROVIDER_ID, VERCEL_AI_GATEWAY_PROVIDER_ID})
SAFE_TEST_STATUSES = frozenset(
    {
        "success",
        "authentication_failed",
        "rate_limited_or_quota_exhausted",
        "model_unavailable",
        "provider_unreachable",
        "invalid_response",
        "provider_error",
    }
)


class AiConfigurationError(RuntimeError):
    """Sanitized AI configuration failure."""


@dataclass(frozen=True, slots=True)
class AiServerConfig:
    """Non-secret server AI provider configuration."""

    active_provider_id: str
    provider_models: dict[str, str]
    updated_at_ms: int
    schema_version: int = AI_CONFIG_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AiTestState:
    """Safe historical AI connection-test result."""

    provider_id: str
    model_id: str
    status: str
    tested_at_ms: int
    schema_version: int = AI_TEST_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AiStatusSnapshot:
    """Safe network-free AI status snapshot."""

    provider_id: str | None
    model_id: str | None
    configuration_state: str
    checked_at_ms: int
    schema_version: int = AI_STATUS_SNAPSHOT_SCHEMA_VERSION


def provider_default_model(provider_id: str) -> str:
    """Return the default model for one supported provider."""
    if provider_id == VERCEL_AI_GATEWAY_PROVIDER_ID:
        return VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    if provider_id == DEFAULT_PROVIDER_ID:
        return DEFAULT_MODEL_ID
    raise AiConfigurationError("AI provider is not supported.")


def validate_provider_id(provider_id: object) -> str:
    """Validate one provider identifier."""
    if not isinstance(provider_id, str):
        raise AiConfigurationError("AI provider is not supported.")
    normalized = provider_id.strip()
    if normalized not in SUPPORTED_PROVIDER_IDS:
        raise AiConfigurationError("AI provider is not supported.")
    return normalized


def validate_model_id(model_id: object) -> str:
    """Validate one bounded model identifier."""
    if not isinstance(model_id, str):
        raise AiConfigurationError("AI model is invalid.")
    normalized = model_id.strip()
    if not normalized or len(normalized) > 120:
        raise AiConfigurationError("AI model is invalid.")
    if any(character.isspace() for character in normalized):
        raise AiConfigurationError("AI model is invalid.")
    return normalized


def now_ms() -> int:
    return int(time.time() * 1000)


def default_ai_config_path(
    environ: Mapping[str, str] | None = None,
    *,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    """Return the configured or platform default non-secret AI config path."""
    source = os.environ if environ is None else environ
    override = source.get(AI_CONFIG_PATH_ENVIRONMENT_NAME)
    if override is not None and override.strip():
        return _validated_absolute_path(override)
    resolved_home = Path.home() if home is None else home
    resolved_platform = sys.platform if platform is None else platform
    if resolved_platform == "darwin":
        return (
            resolved_home
            / "Library"
            / "Application Support"
            / "FrameNest"
            / "ai"
            / "config.json"
        )
    xdg_config = source.get("XDG_CONFIG_HOME")
    config_home = _validated_absolute_path(xdg_config) if xdg_config else resolved_home / ".config"
    return config_home / "framenest" / "ai" / "config.json"


def default_ai_test_state_path(config_path: Path) -> Path:
    """Return the safe test-state path beside the non-secret config file."""
    return config_path.parent / "test-state.json"


def default_ai_status_snapshot_path(config_path: Path) -> Path:
    """Return the safe status snapshot path beside the non-secret config file."""
    return config_path.parent / "status-snapshot.json"


def load_ai_server_config(path: Path) -> AiServerConfig | None:
    """Load one optional non-secret server AI config file."""
    normalized = _prepare_existing_or_missing_path(path)
    if not normalized.exists():
        return None
    try:
        payload = json.loads(normalized.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AiConfigurationError("AI configuration is malformed.") from None
    if not isinstance(payload, dict) or payload.get("schema_version") != AI_CONFIG_SCHEMA_VERSION:
        raise AiConfigurationError("AI configuration version is unsupported.")
    provider_id = validate_provider_id(payload.get("active_provider_id"))
    provider_models_payload = payload.get("provider_models")
    if not isinstance(provider_models_payload, dict):
        raise AiConfigurationError("AI configuration is malformed.")
    provider_models: dict[str, str] = {}
    for key, value in provider_models_payload.items():
        provider_models[validate_provider_id(key)] = validate_model_id(value)
    provider_models.setdefault(provider_id, provider_default_model(provider_id))
    updated_at_ms = payload.get("updated_at_ms")
    if not isinstance(updated_at_ms, int) or updated_at_ms < 0:
        raise AiConfigurationError("AI configuration is malformed.")
    return AiServerConfig(
        active_provider_id=provider_id,
        provider_models=provider_models,
        updated_at_ms=updated_at_ms,
    )


def write_ai_server_config(config: AiServerConfig, path: Path) -> None:
    """Atomically write one non-secret server AI config file."""
    provider_id = validate_provider_id(config.active_provider_id)
    provider_models = {
        validate_provider_id(key): validate_model_id(value)
        for key, value in config.provider_models.items()
    }
    provider_models.setdefault(provider_id, provider_default_model(provider_id))
    payload = {
        "schema_version": AI_CONFIG_SCHEMA_VERSION,
        "active_provider_id": provider_id,
        "provider_models": provider_models,
        "updated_at_ms": config.updated_at_ms,
    }
    _atomic_write_json(path, payload)


def load_ai_test_state(path: Path) -> AiTestState | None:
    """Load optional safe historical AI test state."""
    normalized = _prepare_existing_or_missing_path(path)
    if not normalized.exists():
        return None
    try:
        payload = json.loads(normalized.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AiConfigurationError("AI test state is malformed.") from None
    if not isinstance(payload, dict) or payload.get("schema_version") != AI_TEST_STATE_SCHEMA_VERSION:
        raise AiConfigurationError("AI test state version is unsupported.")
    provider_id = validate_provider_id(payload.get("provider_id"))
    model_id = validate_model_id(payload.get("model_id"))
    status = payload.get("status")
    tested_at_ms = payload.get("tested_at_ms")
    if status not in SAFE_TEST_STATUSES or not isinstance(tested_at_ms, int) or tested_at_ms < 0:
        raise AiConfigurationError("AI test state is malformed.")
    return AiTestState(provider_id=provider_id, model_id=model_id, status=status, tested_at_ms=tested_at_ms)


def write_ai_test_state(state: AiTestState, path: Path) -> None:
    """Atomically write safe historical AI test state."""
    payload = {
        "schema_version": AI_TEST_STATE_SCHEMA_VERSION,
        "provider_id": validate_provider_id(state.provider_id),
        "model_id": validate_model_id(state.model_id),
        "status": state.status,
        "tested_at_ms": state.tested_at_ms,
    }
    if state.status not in SAFE_TEST_STATUSES:
        raise AiConfigurationError("AI test state is malformed.")
    _atomic_write_json(path, payload)


def load_ai_status_snapshot(path: Path) -> AiStatusSnapshot | None:
    """Load optional safe network-free AI status snapshot."""
    normalized = _prepare_existing_or_missing_path(path)
    if not normalized.exists():
        return None
    try:
        payload = json.loads(normalized.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AiConfigurationError("AI status snapshot is malformed.") from None
    if not isinstance(payload, dict) or payload.get("schema_version") != AI_STATUS_SNAPSHOT_SCHEMA_VERSION:
        raise AiConfigurationError("AI status snapshot version is unsupported.")
    configuration_state = payload.get("configuration_state")
    provider_id, model_id = _validate_status_snapshot_identity(
        provider_id=payload.get("provider_id"),
        model_id=payload.get("model_id"),
        configuration_state=configuration_state,
    )
    checked_at_ms = payload.get("checked_at_ms")
    if not isinstance(checked_at_ms, int) or checked_at_ms < 0:
        raise AiConfigurationError("AI status snapshot is malformed.")
    return AiStatusSnapshot(
        provider_id=provider_id,
        model_id=model_id,
        configuration_state=configuration_state,
        checked_at_ms=checked_at_ms,
    )


def write_ai_status_snapshot(snapshot: AiStatusSnapshot, path: Path) -> None:
    """Atomically write safe network-free AI status snapshot."""
    provider_id, model_id = _validate_status_snapshot_identity(
        provider_id=snapshot.provider_id,
        model_id=snapshot.model_id,
        configuration_state=snapshot.configuration_state,
    )
    payload = {
        "schema_version": AI_STATUS_SNAPSHOT_SCHEMA_VERSION,
        "provider_id": provider_id,
        "model_id": model_id,
        "configuration_state": snapshot.configuration_state,
        "checked_at_ms": snapshot.checked_at_ms,
    }
    _atomic_write_json(path, payload)


def _validate_status_snapshot_identity(
    *,
    provider_id: object,
    model_id: object,
    configuration_state: object,
) -> tuple[str | None, str | None]:
    if configuration_state not in {"configured", "not_configured"}:
        raise AiConfigurationError("AI status snapshot is malformed.")
    if provider_id is None and model_id is None:
        if configuration_state == "configured":
            raise AiConfigurationError("AI status snapshot is malformed.")
        return None, None
    if provider_id is None or model_id is None:
        raise AiConfigurationError("AI status snapshot is malformed.")
    return validate_provider_id(provider_id), validate_model_id(model_id)


def _validated_absolute_path(value: str | os.PathLike[str]) -> Path:
    try:
        path = Path(value).expanduser()
    except (RuntimeError, TypeError, ValueError):
        raise AiConfigurationError("AI configuration path must be absolute.") from None
    if not path.is_absolute():
        raise AiConfigurationError("AI configuration path must be absolute.")
    return path.resolve(strict=False)


def _prepare_existing_or_missing_path(path: Path) -> Path:
    original = Path(path).expanduser()
    if original.is_symlink():
        raise AiConfigurationError("AI configuration path must not be a symlink.")
    normalized = _validated_absolute_path(path)
    if normalized.is_symlink():
        raise AiConfigurationError("AI configuration path must not be a symlink.")
    parent = normalized.parent
    if parent.exists() and parent.is_symlink():
        raise AiConfigurationError("AI configuration directory must not be a symlink.")
    return normalized


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    normalized = _prepare_existing_or_missing_path(path)
    parent = normalized.parent
    if parent.exists() and not parent.is_dir():
        raise AiConfigurationError("AI configuration directory is invalid.")
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if parent.is_symlink():
        raise AiConfigurationError("AI configuration directory must not be a symlink.")
    try:
        os.chmod(parent, 0o700)
    except OSError:
        pass
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    fd = -1
    temp_name = ""
    temp_path: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{normalized.name}.", suffix=".tmp", dir=str(parent))
        temp_path = Path(temp_name)
        os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, normalized)
        try:
            os.chmod(normalized, 0o600)
        except OSError:
            pass
    except OSError:
        raise AiConfigurationError("AI configuration could not be written.") from None
    finally:
        if fd >= 0:
            os.close(fd)
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
