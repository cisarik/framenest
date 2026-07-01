"""Unit tests for temporary NVIDIA credential loading."""

from __future__ import annotations

import pytest

from framenest.infrastructure.ai.credentials import (
    CREDENTIAL_MISSING_MESSAGE,
    NvidiaApiCredential,
    VercelAiGatewayCredential,
    load_nvidia_api_credential,
    load_vercel_ai_gateway_credential,
)


def test_missing_key_returns_none() -> None:
    assert load_nvidia_api_credential({}) is None


def test_blank_key_returns_none() -> None:
    assert load_nvidia_api_credential({"NVIDIA_API_KEY": "   "}) is None


def test_non_empty_key_returns_credential_without_exposing_value() -> None:
    credential = load_nvidia_api_credential({"NVIDIA_API_KEY": "test-secret-value"})

    assert isinstance(credential, NvidiaApiCredential)
    assert "test-secret-value" not in repr(credential)
    assert repr(credential) == "NvidiaApiCredential(<redacted>)"


def test_injected_mapping_is_used_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "process-secret")

    assert load_nvidia_api_credential({}) is None
    credential = load_nvidia_api_credential({"NVIDIA_API_KEY": "mapped-secret"})

    assert isinstance(credential, NvidiaApiCredential)
    assert credential.authorization_header() == "Bearer mapped-secret"


def test_key_is_absent_from_errors_and_repr() -> None:
    with pytest.raises(ValueError) as exc_info:
        NvidiaApiCredential(" ")

    assert str(exc_info.value) == CREDENTIAL_MISSING_MESSAGE
    assert "real-secret-value" not in str(exc_info.value)
    assert "secret" not in repr(NvidiaApiCredential("real-secret-value"))


def test_unrelated_environment_values_are_ignored() -> None:
    assert load_nvidia_api_credential({"OTHER_API_KEY": "unrelated-secret"}) is None


def test_vercel_gateway_key_uses_unprefixed_environment_name() -> None:
    credential = load_vercel_ai_gateway_credential({"AI_GATEWAY_API_KEY": "gateway-secret"})

    assert isinstance(credential, VercelAiGatewayCredential)
    assert credential.authorization_header() == "Bearer gateway-secret"
    assert "gateway-secret" not in repr(credential)


def test_vercel_gateway_missing_key_returns_none() -> None:
    assert load_vercel_ai_gateway_credential({}) is None
    assert load_vercel_ai_gateway_credential({"FRAMENEST_AI_GATEWAY_API_KEY": "wrong"}) is None
