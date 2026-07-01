"""Contract tests for server AI provider composition."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings


def _client(tmp_path: Path, *, provider_id: str) -> TestClient:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        ai_provider_id=provider_id,
        _env_file=None,
    )
    return TestClient(create_app(settings=settings))


def test_server_composition_reports_vercel_configured_with_gateway_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-gateway-key")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    response = _client(tmp_path, provider_id="vercel-ai-gateway").get(
        "/api/ai/media-suggestion-capability"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    assert payload["configured"] is True
    assert payload["provider_id"] == "vercel-ai-gateway"
    assert payload["model_id"] == "google/gemini-3.1-flash-lite"
    assert "synthetic" not in response.text


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"AI_GATEWAY_API_KEY": "   "},
        {"NVIDIA_API_KEY": "synthetic-nvidia-key"},
    ],
)
def test_server_composition_reports_vercel_not_configured_without_gateway_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    environ: dict[str, str],
) -> None:
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    for key, value in environ.items():
        monkeypatch.setenv(key, value)

    response = _client(tmp_path, provider_id="vercel-ai-gateway").get(
        "/api/ai/media-suggestion-capability"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert payload["configured"] is False
    assert payload["provider_id"] == "vercel-ai-gateway"
    assert "synthetic" not in response.text


def test_server_composition_reports_nvidia_configured_with_nvidia_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-nvidia-key")
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)

    response = _client(tmp_path, provider_id="nvidia-nim").get(
        "/api/ai/media-suggestion-capability"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    assert payload["configured"] is True
    assert payload["provider_id"] == "nvidia-nim"
    assert "synthetic" not in response.text
