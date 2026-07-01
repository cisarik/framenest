"""Unit tests for non-secret server AI configuration storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from framenest.infrastructure.ai.configuration import (
    AiConfigurationError,
    AiServerConfig,
    AiStatusSnapshot,
    AiTestState,
    default_ai_config_path,
    load_ai_status_snapshot,
    load_ai_server_config,
    load_ai_test_state,
    now_ms,
    write_ai_status_snapshot,
    write_ai_server_config,
    write_ai_test_state,
)
from framenest.infrastructure.ai.constants import VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID


def test_config_path_override_is_absolute(tmp_path: Path) -> None:
    path = tmp_path / "ai" / "config.json"

    assert default_ai_config_path({"FRAMENEST_AI_CONFIG_PATH": str(path)}) == path

    with pytest.raises(AiConfigurationError):
        default_ai_config_path({"FRAMENEST_AI_CONFIG_PATH": "relative.json"})


def test_write_and_load_config_persists_no_secret(tmp_path: Path) -> None:
    path = tmp_path / "config" / "ai.json"

    write_ai_server_config(
        AiServerConfig(
            active_provider_id="vercel-ai-gateway",
            provider_models={"vercel-ai-gateway": VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID},
            updated_at_ms=now_ms(),
        ),
        path,
    )

    loaded = load_ai_server_config(path)
    assert loaded is not None
    assert loaded.active_provider_id == "vercel-ai-gateway"
    assert loaded.provider_models["vercel-ai-gateway"] == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    raw = path.read_text(encoding="utf-8")
    assert "API_KEY" not in raw
    assert "Authorization" not in raw
    assert "data:" not in raw


def test_malformed_config_is_sanitized(tmp_path: Path) -> None:
    path = tmp_path / "ai.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(AiConfigurationError, match="malformed"):
        load_ai_server_config(path)


def test_symlink_config_path_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    symlink = tmp_path / "config.json"
    symlink.symlink_to(target)

    with pytest.raises(AiConfigurationError, match="symlink"):
        write_ai_server_config(
            AiServerConfig(
                active_provider_id="vercel-ai-gateway",
                provider_models={"vercel-ai-gateway": VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID},
                updated_at_ms=now_ms(),
            ),
            symlink,
        )


def test_safe_test_state_contains_only_category_and_identity(tmp_path: Path) -> None:
    path = tmp_path / "test-state.json"

    write_ai_test_state(
        AiTestState(
            provider_id="vercel-ai-gateway",
            model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
            status="success",
            tested_at_ms=123,
        ),
        path,
    )

    assert load_ai_test_state(path) == AiTestState(
        provider_id="vercel-ai-gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        status="success",
        tested_at_ms=123,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(payload) == [
        "model_id",
        "provider_id",
        "schema_version",
        "status",
        "tested_at_ms",
    ]


def test_safe_status_snapshot_contains_only_config_state_and_identity(tmp_path: Path) -> None:
    path = tmp_path / "status-snapshot.json"

    write_ai_status_snapshot(
        AiStatusSnapshot(
            provider_id="vercel-ai-gateway",
            model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
            configuration_state="configured",
            checked_at_ms=456,
        ),
        path,
    )

    assert load_ai_status_snapshot(path) == AiStatusSnapshot(
        provider_id="vercel-ai-gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        configuration_state="configured",
        checked_at_ms=456,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(payload) == [
        "checked_at_ms",
        "configuration_state",
        "model_id",
        "provider_id",
        "schema_version",
    ]
