"""Server AI provider registry and composition boundary."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.ai.configuration import (
    AiConfigurationError,
    AiStatusSnapshot,
    AiTestState,
    default_ai_config_path,
    default_ai_status_snapshot_path,
    default_ai_test_state_path,
    load_ai_server_config,
    load_ai_status_snapshot,
    load_ai_test_state,
    provider_default_model,
    validate_model_id,
    validate_provider_id,
)
from framenest.infrastructure.ai.constants import (
    DEFAULT_PROVIDER_ID,
    VERCEL_AI_GATEWAY_PROVIDER_ID,
)
from framenest.infrastructure.ai.credentials import (
    NVIDIA_API_KEY_ENVIRONMENT_NAME,
    VERCEL_AI_GATEWAY_API_KEY_ENVIRONMENT_NAME,
    load_nvidia_api_credential,
    load_vercel_ai_gateway_credential,
)
from framenest.infrastructure.ai.nvidia_nim import JsonTransport, NvidiaNimMediaSuggestionProvider
from framenest.infrastructure.ai.vercel_gateway import VercelAiGatewayMediaSuggestionProvider


@dataclass(frozen=True, slots=True)
class AiProviderDefinition:
    provider_id: str
    display_name: str
    credential_environment_name: str


@dataclass(frozen=True, slots=True)
class ResolvedAiProvider:
    provider_id: str | None
    display_name: str | None
    model_id: str | None
    source: str
    credential_environment_name: str | None
    credential_available: bool
    provider: object | None
    last_test: AiTestState | None
    last_status: AiStatusSnapshot | None
    config_path: Path
    test_state_path: Path
    status_snapshot_path: Path

    @property
    def configured(self) -> bool:
        return self.provider is not None


PROVIDER_DEFINITIONS = {
    DEFAULT_PROVIDER_ID: AiProviderDefinition(
        provider_id=DEFAULT_PROVIDER_ID,
        display_name="NVIDIA NIM",
        credential_environment_name=NVIDIA_API_KEY_ENVIRONMENT_NAME,
    ),
    VERCEL_AI_GATEWAY_PROVIDER_ID: AiProviderDefinition(
        provider_id=VERCEL_AI_GATEWAY_PROVIDER_ID,
        display_name="Vercel AI Gateway",
        credential_environment_name=VERCEL_AI_GATEWAY_API_KEY_ENVIRONMENT_NAME,
    ),
}


def resolve_ai_provider(
    settings: FrameNestSettings,
    *,
    environ: Mapping[str, str] | None = None,
    config_path: Path | None = None,
    transport: JsonTransport | None = None,
) -> ResolvedAiProvider:
    """Resolve the active server AI provider and instantiate it when credentialed."""
    source = os.environ if environ is None else environ
    resolved_config_path = config_path or default_ai_config_path(source)
    provider_id: str | None = None
    model_id: str | None = None
    configuration_source = "unconfigured"
    if settings.ai_provider_id is not None:
        provider_id = validate_provider_id(settings.ai_provider_id)
        model_id = (
            validate_model_id(settings.ai_model_id)
            if settings.ai_model_id is not None
            else provider_default_model(provider_id)
        )
        configuration_source = "environment"
    else:
        persisted = load_ai_server_config(resolved_config_path)
        if persisted is not None:
            provider_id = persisted.active_provider_id
            model_id = persisted.provider_models.get(provider_id) or provider_default_model(provider_id)
            model_id = validate_model_id(model_id)
            configuration_source = "server config"
        elif source.get(NVIDIA_API_KEY_ENVIRONMENT_NAME, "").strip():
            provider_id = DEFAULT_PROVIDER_ID
            model_id = provider_default_model(provider_id)
            configuration_source = "legacy compatibility"
    if provider_id is None:
        definition = None
        credential_available = False
        provider = None
    else:
        assert model_id is not None
        definition = PROVIDER_DEFINITIONS[provider_id]
        credential_available = bool(source.get(definition.credential_environment_name, "").strip())
        provider = _build_provider(provider_id, model_id, source, transport=transport)
    test_state_path = default_ai_test_state_path(resolved_config_path)
    status_snapshot_path = default_ai_status_snapshot_path(resolved_config_path)
    last_test = None
    last_status = None
    if provider_id is not None and model_id is not None:
        last_test = _load_matching_test_state(test_state_path, provider_id=provider_id, model_id=model_id)
        last_status = _load_matching_status_snapshot(
            status_snapshot_path,
            provider_id=provider_id,
            model_id=model_id,
        )
    return ResolvedAiProvider(
        provider_id=provider_id,
        display_name=None if definition is None else definition.display_name,
        model_id=model_id,
        source=configuration_source,
        credential_environment_name=None if definition is None else definition.credential_environment_name,
        credential_available=credential_available,
        provider=provider,
        last_test=last_test,
        last_status=last_status,
        config_path=resolved_config_path,
        test_state_path=test_state_path,
        status_snapshot_path=status_snapshot_path,
    )


def _build_provider(
    provider_id: str,
    model_id: str,
    environ: Mapping[str, str],
    *,
    transport: JsonTransport | None,
) -> object | None:
    if provider_id == DEFAULT_PROVIDER_ID:
        credential = load_nvidia_api_credential(environ)
        if credential is None:
            return None
        return NvidiaNimMediaSuggestionProvider(credential, transport=transport, model_id=model_id)
    if provider_id == VERCEL_AI_GATEWAY_PROVIDER_ID:
        credential = load_vercel_ai_gateway_credential(environ)
        if credential is None:
            return None
        return VercelAiGatewayMediaSuggestionProvider(credential, transport=transport, model_id=model_id)
    raise AiConfigurationError("AI provider is not supported.")


def _load_matching_test_state(
    path: Path,
    *,
    provider_id: str,
    model_id: str,
) -> AiTestState | None:
    state = load_ai_test_state(path)
    if state is None:
        return None
    if state.provider_id != provider_id or state.model_id != model_id:
        return None
    return state


def _load_matching_status_snapshot(
    path: Path,
    *,
    provider_id: str,
    model_id: str,
) -> AiStatusSnapshot | None:
    snapshot = load_ai_status_snapshot(path)
    if snapshot is None:
        return None
    if snapshot.provider_id != provider_id or snapshot.model_id != model_id:
        return None
    return snapshot
