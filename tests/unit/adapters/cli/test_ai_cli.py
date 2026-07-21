"""Unit tests for the server-operated AI CLI."""

from __future__ import annotations

from pathlib import Path
import stat

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
from framenest.infrastructure.ai.constants import DEFAULT_PROVIDER_ID, VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID


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


def test_status_fully_unconfigured_exits_zero_without_fabricated_provider(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "ai" / "config.json"
    lines: list[str] = []

    assert ai.status_command(ai._CliContext(config_path=config_path), output=lines.append) == 0

    output = "\n".join(lines)
    assert "Active provider: none" in output
    assert "Model: none" in output
    assert "Configuration source: unconfigured" in output
    assert "Credential available to this process: no" in output
    assert "Analysis state: not configured" in output
    assert "Last connection test: not tested" in output
    assert "Vercel" not in output
    assert "NVIDIA" not in output
    snapshot = load_ai_status_snapshot(tmp_path / "ai" / "status-snapshot.json")
    assert snapshot is not None
    assert snapshot.provider_id is None
    assert snapshot.model_id is None
    assert snapshot.configuration_state == "not_configured"


def test_status_no_write_parser_behavior(tmp_path: Path) -> None:
    parser = ai.build_parser()

    args = parser.parse_args(
        [
            "--config-path",
            str(tmp_path / "config.json"),
            "status",
            "--no-write",
        ]
    )

    assert args.command == "status"
    assert args.no_write is True


def test_status_no_write_fully_unconfigured_exits_zero_without_writes(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "missing" / "config.json"
    lines: list[str] = []

    assert ai.status_command(ai._CliContext(config_path=config_path), output=lines.append, write_snapshot=False) == 0

    output = "\n".join(lines)
    assert "Active provider: none" in output
    assert "Model: none" in output
    assert "Analysis state: not configured" in output
    assert not config_path.parent.exists()


def test_status_no_write_does_not_modify_existing_snapshot(tmp_path: Path) -> None:
    config_path = tmp_path / "ai" / "config.json"
    snapshot_path = tmp_path / "ai" / "status-snapshot.json"
    snapshot_path.parent.mkdir()
    snapshot_path.write_text('{"existing":true}\n', encoding="utf-8")
    before = snapshot_path.stat().st_mtime_ns

    lines: list[str] = []

    assert ai.status_command(ai._CliContext(config_path=config_path), output=lines.append, write_snapshot=False) == 0

    assert snapshot_path.read_text(encoding="utf-8") == '{"existing":true}\n'
    assert snapshot_path.stat().st_mtime_ns == before


def test_status_no_write_works_with_unwritable_state_directory(tmp_path: Path) -> None:
    config_path = tmp_path / "ai" / "config.json"
    config_path.parent.mkdir()
    config_path.parent.chmod(stat.S_IREAD | stat.S_IEXEC)

    try:
        lines: list[str] = []

        assert ai.status_command(ai._CliContext(config_path=config_path), output=lines.append, write_snapshot=False) == 0
    finally:
        config_path.parent.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)


def test_status_no_write_main_exits_zero_when_fully_unconfigured(tmp_path: Path) -> None:
    config_path = tmp_path / "missing" / "config.json"

    assert ai.main(["--config-path", str(config_path), "status", "--no-write"]) == 0

    assert not config_path.parent.exists()


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


def test_status_selected_provider_without_credential_writes_selected_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    resolved = ai.ResolvedAiProvider(
        provider_id="vercel-ai-gateway",
        display_name="Vercel AI Gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        source="server config",
        credential_environment_name="AI_GATEWAY_API_KEY",
        credential_available=False,
        provider=None,
        last_test=None,
        last_status=None,
        config_path=tmp_path / "config.json",
        test_state_path=tmp_path / "test-state.json",
        status_snapshot_path=tmp_path / "status-snapshot.json",
    )
    monkeypatch.setattr(ai, "_resolve", lambda _context: resolved)
    lines: list[str] = []

    assert ai.status_command(ai._CliContext(config_path=tmp_path / "config.json"), output=lines.append) == 0

    snapshot = load_ai_status_snapshot(tmp_path / "status-snapshot.json")
    assert snapshot is not None
    assert snapshot.provider_id == "vercel-ai-gateway"
    assert snapshot.model_id == VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID
    assert snapshot.configuration_state == "not_configured"


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
    raw_state = (tmp_path / "test-state.json").read_text(encoding="utf-8")
    assert category in raw_state
    assert "raw" not in raw_state
    output = "\n".join(lines)
    assert category in output
    assert "raw" not in output


def test_still_frame_smoke_requires_confirmation(tmp_path: Path) -> None:
    assert (
        ai.main(
            [
                "--config-path",
                str(tmp_path / "config.json"),
                "still-frame-smoke",
                "--image",
                str(tmp_path / "a.jpg"),
            ]
        )
        == 2
    )


def test_still_frame_smoke_performs_one_suggest_without_persistence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from PIL import Image

    from framenest.application.media_suggestion import MediaSuggestion, PROMPT_VERSION

    image_path = tmp_path / "frame.jpg"
    Image.new("RGB", (48, 32), (12, 34, 56)).save(image_path, format="JPEG")

    class _Provider:
        calls = 0
        last_request = None

        def suggest(self, request):  # noqa: ANN001
            self.calls += 1
            self.last_request = request
            return MediaSuggestion(
                title="Synthetic smoke",
                description="Bounded still-frame smoke suggestion.",
                collection="Smoke",
                tags=("synthetic",),
                suggested_filename="still-frame-smoke.jpg",
                confidence=0.5,
                evidence=("flat color frame",),
                uncertainties=("synthetic input",),
                provider_id=DEFAULT_PROVIDER_ID,
                model_id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                prompt_version=PROMPT_VERSION,
            )

        def test_connection(self) -> None:
            raise AssertionError("text-only test must not run")

    provider = _Provider()
    resolved = ai.ResolvedAiProvider(
        provider_id=DEFAULT_PROVIDER_ID,
        display_name="NVIDIA NIM",
        model_id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        source="server config",
        credential_environment_name="NVIDIA_API_KEY",
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

    result = ai.still_frame_smoke_command(
        ai._CliContext(config_path=tmp_path / "config.json"),
        image_paths=(image_path,),
        confirm_cloud_upload=True,
        output=lines.append,
    )

    assert result == 0
    assert provider.calls == 1
    assert provider.last_request is not None
    assert len(provider.last_request.representative_frames) == 1
    assert not (tmp_path / "test-state.json").exists()
    output = "\n".join(lines)
    assert "AI still-frame smoke: success" in output
    assert "Sent frames: 1" in output
    assert "secret" not in output.lower()


def test_still_frame_smoke_rejects_non_nvidia_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    resolved = ai.ResolvedAiProvider(
        provider_id="vercel-ai-gateway",
        display_name="Vercel AI Gateway",
        model_id=VERCEL_AI_GATEWAY_DEFAULT_MODEL_ID,
        source="server config",
        credential_environment_name="AI_GATEWAY_API_KEY",
        credential_available=True,
        provider=object(),
        last_test=None,
        last_status=None,
        config_path=tmp_path / "config.json",
        test_state_path=tmp_path / "test-state.json",
        status_snapshot_path=tmp_path / "status-snapshot.json",
    )
    monkeypatch.setattr(ai, "_resolve", lambda _context: resolved)
    lines: list[str] = []
    result = ai.still_frame_smoke_command(
        ai._CliContext(config_path=tmp_path / "config.json"),
        image_paths=(tmp_path / "missing.jpg",),
        confirm_cloud_upload=True,
        output=lines.append,
    )
    assert result == 2
    assert "unsupported_provider" in "\n".join(lines)
