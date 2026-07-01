"""Unit tests for server AI provider resolution."""

from __future__ import annotations

from pathlib import Path

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.ai.configuration import (
    AiServerConfig,
    AiStatusSnapshot,
    default_ai_status_snapshot_path,
    write_ai_status_snapshot,
    write_ai_server_config,
)
from framenest.infrastructure.ai.constants import VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
from framenest.infrastructure.ai.registry import resolve_ai_provider


def _settings(tmp_path: Path, **kwargs: object) -> FrameNestSettings:
    return FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        _env_file=None,
        **kwargs,
    )


def test_environment_provider_model_override_has_precedence(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_ai_server_config(
        AiServerConfig(
            active_provider_id="nvidia-nim",
            provider_models={"nvidia-nim": "nvidia/example"},
            updated_at_ms=1,
        ),
        config_path,
    )

    resolved = resolve_ai_provider(
        _settings(tmp_path, ai_provider_id="vercel-ai-gateway", ai_model_id="google/custom"),
        environ={"AI_GATEWAY_API_KEY": "secret"},
        config_path=config_path,
    )

    assert resolved.provider_id == "vercel-ai-gateway"
    assert resolved.model_id == "google/custom"
    assert resolved.source == "environment"
    assert resolved.configured is True


def test_persisted_config_uses_vercel_default_model(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_ai_server_config(
        AiServerConfig(
            active_provider_id="vercel-ai-gateway",
            provider_models={},
            updated_at_ms=1,
        ),
        config_path,
    )

    resolved = resolve_ai_provider(
        _settings(tmp_path),
        environ={"AI_GATEWAY_API_KEY": "secret"},
        config_path=config_path,
    )

    assert resolved.provider_id == "vercel-ai-gateway"
    assert resolved.model_id == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    assert resolved.source == "server config"
    assert resolved.configured is True


def test_legacy_nvidia_credential_is_backward_compatible(tmp_path: Path) -> None:
    resolved = resolve_ai_provider(
        _settings(tmp_path),
        environ={"NVIDIA_API_KEY": "secret"},
        config_path=tmp_path / "missing.json",
    )

    assert resolved.provider_id == "nvidia-nim"
    assert resolved.source == "legacy compatibility"
    assert resolved.configured is True


def test_unconfigured_prefers_vercel_identity_without_provider(tmp_path: Path) -> None:
    resolved = resolve_ai_provider(
        _settings(tmp_path),
        environ={},
        config_path=tmp_path / "missing.json",
    )

    assert resolved.provider_id == "vercel-ai-gateway"
    assert resolved.source == "unconfigured"
    assert resolved.configured is False


def test_status_snapshot_is_loaded_only_for_matching_identity(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    status_path = default_ai_status_snapshot_path(config_path)
    write_ai_status_snapshot(
        AiStatusSnapshot(
            provider_id="vercel-ai-gateway",
            model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
            configuration_state="configured",
            checked_at_ms=123,
        ),
        status_path,
    )

    matching = resolve_ai_provider(
        _settings(tmp_path, ai_provider_id="vercel-ai-gateway"),
        environ={"AI_GATEWAY_API_KEY": "secret"},
        config_path=config_path,
    )
    stale = resolve_ai_provider(
        _settings(tmp_path, ai_provider_id="nvidia-nim"),
        environ={"NVIDIA_API_KEY": "secret"},
        config_path=config_path,
    )

    assert matching.last_status is not None
    assert matching.last_status.checked_at_ms == 123
    assert stale.last_status is None
