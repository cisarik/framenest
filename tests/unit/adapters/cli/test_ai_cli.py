"""Unit tests for the server-operated AI CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from framenest.adapters.cli import ai
from framenest.application.media_suggestion import (
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderModelUnavailableError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
)
from framenest.infrastructure.ai.configuration import (
    load_ai_server_config,
    load_ai_status_snapshot,
    load_ai_test_state,
)
from framenest.infrastructure.ai.constants import VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID


def test_configure_can_cancel_without_mutation(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    lines: list[str] = []

    result = ai.configure_command(
        ai._CliContext(config_path=config_path),
        prompt=lambda _prompt: "cancel",
        output=lines.append,
    )

    assert result == 1
    assert not config_path.exists()
    assert any("No configuration was changed" in line for line in lines)


def test_configure_persists_provider_model_but_no_secret(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    answers = iter(["1", "", "yes"])
    lines: list[str] = []

    result = ai.configure_command(
        ai._CliContext(config_path=config_path),
        prompt=lambda _prompt: next(answers),
        output=lines.append,
    )

    assert result == 0
    config = load_ai_server_config(config_path)
    assert config is not None
    assert config.active_provider_id == "vercel-ai-gateway"
    assert config.provider_models["vercel-ai-gateway"] == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    raw = config_path.read_text(encoding="utf-8")
    assert "secret" not in raw
    assert "API_KEY" not in raw
    assert any("AI_GATEWAY_API_KEY" in line for line in lines)


def test_configure_non_interactive_persists_provider_model_but_no_secret(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    lines: list[str] = []

    result = ai.configure_non_interactive_command(
        ai._CliContext(config_path=config_path),
        provider_id="vercel-ai-gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        output=lines.append,
    )

    assert result == 0
    config = load_ai_server_config(config_path)
    assert config is not None
    assert config.active_provider_id == "vercel-ai-gateway"
    assert config.provider_models["vercel-ai-gateway"] == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    raw = config_path.read_text(encoding="utf-8")
    assert "secret" not in raw
    assert "API_KEY" not in raw
    assert any("AI configuration saved" in line for line in lines)


def test_configure_parser_accepts_explicit_non_interactive_provider_model(tmp_path: Path) -> None:
    parser = ai.build_parser()

    args = parser.parse_args(
        [
            "--config-path",
            str(tmp_path / "config.json"),
            "configure",
            "--provider-id",
            "vercel-ai-gateway",
            "--model-id",
            VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
            "--yes",
        ]
    )

    assert args.command == "configure"
    assert args.provider_id == "vercel-ai-gateway"
    assert args.model_id == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    assert args.yes is True


def test_configure_non_interactive_requires_complete_arguments(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"

    assert (
        ai.main(
            [
                "--config-path",
                str(config_path),
                "configure",
                "--provider-id",
                "vercel-ai-gateway",
                "--yes",
            ]
        )
        == 2
    )
    assert not config_path.exists()


def test_configure_non_interactive_rejects_invalid_model(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"

    assert (
        ai.main(
            [
                "--config-path",
                str(config_path),
                "configure",
                "--provider-id",
                "vercel-ai-gateway",
                "--model-id",
                "bad model",
                "--yes",
            ]
        )
        == 2
    )
    assert not config_path.exists()


def test_status_uses_resolver_without_provider_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class _Provider:
        def test_connection(self) -> None:
            raise AssertionError("status must not test provider connections")

    resolved = ai.ResolvedAiProvider(
        provider_id="vercel-ai-gateway",
        display_name="Vercel AI Gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        source="server config",
        credential_environment_name="AI_GATEWAY_API_KEY",
        credential_available=True,
        provider=_Provider(),
        last_test=None,
        last_status=None,
        config_path=tmp_path / "config.json",
        test_state_path=tmp_path / "test-state.json",
        status_snapshot_path=tmp_path / "status-snapshot.json",
    )
    monkeypatch.setattr(ai, "_resolve", lambda _context: resolved)
    lines: list[str] = []

    assert ai.status_command(ai._CliContext(config_path=tmp_path / "config.json"), output=lines.append) == 0

    output = "\n".join(lines)
    assert "AI status" in output
    assert "Credential available to this process: yes" in output
    assert "secret" not in output
    snapshot = load_ai_status_snapshot(tmp_path / "status-snapshot.json")
    assert snapshot is not None
    assert snapshot.provider_id == "vercel-ai-gateway"
    assert snapshot.model_id == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    assert snapshot.configuration_state == "configured"
    assert not (tmp_path / "test-state.json").exists()


def test_test_command_performs_one_text_only_provider_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class _Provider:
        calls = 0

        def test_connection(self) -> None:
            self.calls += 1

    provider = _Provider()
    resolved = ai.ResolvedAiProvider(
        provider_id="vercel-ai-gateway",
        display_name="Vercel AI Gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        source="server config",
        credential_environment_name="AI_GATEWAY_API_KEY",
        credential_available=True,
        provider=provider,
        last_test=None,
        last_status=None,
        config_path=tmp_path / "config.json",
        test_state_path=tmp_path / "test-state.json",
        status_snapshot_path=tmp_path / "status-snapshot.json",
    )
    monkeypatch.setattr(ai, "_resolve", lambda _context: resolved)
    lines: list[str] = []

    assert ai.test_command(ai._CliContext(config_path=tmp_path / "config.json"), output=lines.append) == 0

    assert provider.calls == 1
    state = load_ai_test_state(tmp_path / "test-state.json")
    assert state is not None
    assert state.status == "success"
    assert "AI test: success" in "\n".join(lines)


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (MediaSuggestionProviderAuthError("raw secret"), "authentication_failed"),
        (MediaSuggestionProviderRateLimitedError("raw quota"), "rate_limited_or_quota_exhausted"),
        (MediaSuggestionProviderModelUnavailableError("raw model"), "model_unavailable"),
        (MediaSuggestionProviderUnavailableError("raw network"), "provider_unreachable"),
        (MediaSuggestionProviderInvalidResponseError("raw provider response"), "invalid_response"),
        (MediaSuggestionProviderFailedError("raw failure"), "provider_error"),
    ],
)
def test_test_command_categorizes_safe_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    error: Exception,
    category: str,
) -> None:
    class _Provider:
        def test_connection(self) -> None:
            raise error

    resolved = ai.ResolvedAiProvider(
        provider_id="vercel-ai-gateway",
        display_name="Vercel AI Gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        source="server config",
        credential_environment_name="AI_GATEWAY_API_KEY",
        credential_available=True,
        provider=_Provider(),
        last_test=None,
        last_status=None,
        config_path=tmp_path / "config.json",
        test_state_path=tmp_path / "test-state.json",
        status_snapshot_path=tmp_path / "status-snapshot.json",
    )
    monkeypatch.setattr(ai, "_resolve", lambda _context: resolved)
    lines: list[str] = []

    assert ai.test_command(ai._CliContext(config_path=tmp_path / "config.json"), output=lines.append) == 2

    assert load_ai_test_state(tmp_path / "test-state.json").status == category  # type: ignore[union-attr]
    output = "\n".join(lines)
    assert category in output
    assert "raw" not in output
