"""Server-operated AI configuration and diagnostics CLI."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from framenest.application.media_suggestion import (
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderModelUnavailableError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
)
from framenest.configuration import load_settings
from framenest.infrastructure.ai.configuration import (
    AiConfigurationError,
    AiServerConfig,
    AiStatusSnapshot,
    AiTestState,
    default_ai_config_path,
    load_ai_server_config,
    now_ms,
    provider_default_model,
    validate_model_id,
    validate_provider_id,
    write_ai_server_config,
    write_ai_status_snapshot,
    write_ai_test_state,
)
from framenest.infrastructure.ai.constants import DEFAULT_PROVIDER_ID, VERCEL_AI_GATEWAY_PROVIDER_ID
from framenest.infrastructure.ai.registry import PROVIDER_DEFINITIONS, ResolvedAiProvider, resolve_ai_provider

Input = Callable[[str], str]
Output = Callable[[str], None]

PROVIDER_ORDER = (VERCEL_AI_GATEWAY_PROVIDER_ID, DEFAULT_PROVIDER_ID)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise SystemExit(2)


@dataclass(frozen=True, slots=True)
class _CliContext:
    config_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="framenest-ai", add_help=True)
    parser.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help="Override the non-secret server AI configuration path.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    status = subcommands.add_parser("status", help="Show network-free AI configuration status.")
    status.add_argument(
        "--no-write",
        action="store_true",
        help="Resolve status without writing a local status snapshot.",
    )
    configure = subcommands.add_parser(
        "configure",
        help="Configure non-secret AI provider state.",
    )
    configure.add_argument("--provider-id", default=None, help="Non-interactive provider ID.")
    configure.add_argument("--model-id", default=None, help="Non-interactive model ID.")
    configure.add_argument(
        "--yes",
        action="store_true",
        help="Confirm a non-interactive provider/model configuration.",
    )
    subcommands.add_parser("test", help="Run one explicit text-only provider connection test.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = args.config_path or default_ai_config_path()
    context = _CliContext(config_path=config_path)
    try:
        if args.command == "status":
            return status_command(context, write_snapshot=not args.no_write)
        if args.command == "configure":
            if args.provider_id is not None or args.model_id is not None or args.yes:
                if args.provider_id is None or args.model_id is None or not args.yes:
                    raise AiConfigurationError(
                        "Non-interactive AI configuration requires provider, model, and confirmation."
                    )
                return configure_non_interactive_command(
                    context,
                    provider_id=args.provider_id,
                    model_id=args.model_id,
                )
            return configure_command(context)
        if args.command == "test":
            return test_command(context)
    except AiConfigurationError as exc:
        print(f"AI configuration error: {exc}", file=sys.stderr)
        return 2
    return 2


def status_command(
    context: _CliContext,
    *,
    output: Output = print,
    write_snapshot: bool = True,
) -> int:
    """Print sanitized network-free AI status."""
    resolved = _resolve(context)
    if write_snapshot:
        write_ai_status_snapshot(
            AiStatusSnapshot(
                provider_id=resolved.provider_id,
                model_id=resolved.model_id,
                configuration_state="configured" if resolved.configured else "not_configured",
                checked_at_ms=now_ms(),
            ),
            resolved.status_snapshot_path,
        )
    output("AI status")
    output(f"Active provider: {_optional_text(resolved.display_name)}")
    output(f"Model: {_optional_text(resolved.model_id)}")
    output(f"Configuration source: {resolved.source}")
    output(f"Credential available to this process: {_yes_no(resolved.credential_available)}")
    output(f"Analysis state: {'configured' if resolved.configured else 'not configured'}")
    output(f"Last connection test: {_last_test_text(resolved)}")
    return 0


def configure_command(
    context: _CliContext,
    *,
    prompt: Input = input,
    output: Output = print,
) -> int:
    """Interactively write non-secret provider/model selection."""
    existing = load_ai_server_config(context.config_path)
    provider_models = {} if existing is None else dict(existing.provider_models)
    default_provider = existing.active_provider_id if existing is not None else VERCEL_AI_GATEWAY_PROVIDER_ID
    output("AI provider configuration")
    for index, provider_id in enumerate(PROVIDER_ORDER, start=1):
        definition = PROVIDER_DEFINITIONS[provider_id]
        marker = " [default]" if provider_id == default_provider else ""
        output(f"{index}. {definition.display_name} ({provider_id}){marker}")
    selection = prompt("Select provider [1]: ").strip()
    if selection.lower() in {"q", "quit", "cancel"}:
        output("Cancelled. No configuration was changed.")
        return 1
    provider_id = _selected_provider(selection, default_provider)
    provider_definition = PROVIDER_DEFINITIONS[provider_id]
    proposed_model = provider_models.get(provider_id) or provider_default_model(provider_id)
    output(f"Proposed model: {proposed_model}")
    model_input = prompt("Model ID [default above]: ").strip()
    if model_input.lower() in {"q", "quit", "cancel"}:
        output("Cancelled. No configuration was changed.")
        return 1
    model_id = validate_model_id(model_input or proposed_model)
    output("")
    output(f"Provider: {provider_definition.display_name} ({provider_id})")
    output(f"Model: {model_id}")
    confirm = prompt("Activate this non-secret server AI configuration? [y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        output("Cancelled. No configuration was changed.")
        return 1
    provider_models[provider_id] = model_id
    config = AiServerConfig(
        active_provider_id=provider_id,
        provider_models=provider_models,
        updated_at_ms=now_ms(),
    )
    write_ai_server_config(config, context.config_path)
    output("AI configuration saved.")
    output(f"Active provider: {provider_definition.display_name}")
    output(f"Model: {model_id}")
    output(f"Configuration path: {context.config_path}")
    output(f"Required credential environment variable: {provider_definition.credential_environment_name}")
    return 0


def configure_non_interactive_command(
    context: _CliContext,
    *,
    provider_id: str,
    model_id: str,
    output: Output = print,
) -> int:
    """Write non-secret provider/model selection for automation."""
    selected_provider_id = validate_provider_id(provider_id)
    selected_model_id = validate_model_id(model_id)
    existing = load_ai_server_config(context.config_path)
    provider_models = {} if existing is None else dict(existing.provider_models)
    provider_models[selected_provider_id] = selected_model_id
    config = AiServerConfig(
        active_provider_id=selected_provider_id,
        provider_models=provider_models,
        updated_at_ms=now_ms(),
    )
    write_ai_server_config(config, context.config_path)
    definition = PROVIDER_DEFINITIONS[selected_provider_id]
    output("AI configuration saved.")
    output(f"Active provider: {definition.display_name}")
    output(f"Model: {selected_model_id}")
    output(f"Configuration path: {context.config_path}")
    output(f"Required credential environment variable: {definition.credential_environment_name}")
    return 0


def test_command(context: _CliContext, *, output: Output = print) -> int:
    """Run one explicit text-only provider connection test."""
    resolved = _resolve(context)
    if resolved.source == "unconfigured":
        output("AI test: not configured")
        output("Configure server AI provider state before testing.")
        return 2
    if not resolved.credential_available or resolved.provider is None:
        output("AI test: authentication_failed")
        output("Credential available to this process: no")
        output(f"Required credential environment variable: {resolved.credential_environment_name}")
        return 2
    lock_path = resolved.test_state_path.parent / ".test.lock"
    lock_fd = _acquire_test_lock(lock_path)
    if lock_fd is None:
        output("AI test: provider_error")
        output("Another AI connection test is already running.")
        return 2
    try:
        category = "success"
        exit_code = 0
        try:
            resolved.provider.test_connection()
        except MediaSuggestionProviderAuthError:
            category = "authentication_failed"
            exit_code = 2
        except MediaSuggestionProviderRateLimitedError:
            category = "rate_limited_or_quota_exhausted"
            exit_code = 2
        except MediaSuggestionProviderModelUnavailableError:
            category = "model_unavailable"
            exit_code = 2
        except MediaSuggestionProviderUnavailableError:
            category = "provider_unreachable"
            exit_code = 2
        except MediaSuggestionProviderInvalidResponseError:
            category = "invalid_response"
            exit_code = 2
        except MediaSuggestionProviderFailedError:
            category = "provider_error"
            exit_code = 2
        except Exception:
            category = "provider_error"
            exit_code = 2
        write_ai_test_state(
            AiTestState(
                provider_id=resolved.provider_id,
                model_id=resolved.model_id,
                status=category,
                tested_at_ms=now_ms(),
            ),
            resolved.test_state_path,
        )
        output(f"AI test: {category}")
        output(f"Provider: {resolved.display_name}")
        output(f"Model: {resolved.model_id}")
        return exit_code
    finally:
        os.close(lock_fd)
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


def _resolve(context: _CliContext) -> ResolvedAiProvider:
    settings = load_settings()
    return resolve_ai_provider(settings, config_path=context.config_path)


def _selected_provider(selection: str, default_provider: str) -> str:
    if not selection:
        return validate_provider_id(default_provider)
    if selection in {"1", VERCEL_AI_GATEWAY_PROVIDER_ID}:
        return VERCEL_AI_GATEWAY_PROVIDER_ID
    if selection in {"2", DEFAULT_PROVIDER_ID}:
        return DEFAULT_PROVIDER_ID
    return validate_provider_id(selection)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _optional_text(value: str | None) -> str:
    return "none" if value is None else value


def _last_test_text(resolved: ResolvedAiProvider) -> str:
    if resolved.last_test is None:
        return "not tested"
    if resolved.last_test.status == "success":
        return "success"
    return f"safe failure ({resolved.last_test.status})"


def _acquire_test_lock(lock_path: Path) -> int | None:
    lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        return os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return None
    except OSError as exc:
        raise AiConfigurationError("AI test lock could not be created.") from exc


if __name__ == "__main__":
    raise SystemExit(main())
