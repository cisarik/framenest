"""Administrator AI provider management API."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from framenest.infrastructure.ai.activity_lock import (
    AiActivityLockError,
    acquire_ai_activity_lock,
)
from framenest.infrastructure.ai.configuration import (
    AiConfigurationError,
    AiServerConfig,
    AiTestState,
    default_ai_config_path,
    default_ai_test_state_path,
    load_ai_server_config,
    load_ai_test_state,
    mutate_ai_server_config,
    now_ms,
    validate_model_id,
    validate_provider_id,
    write_ai_test_state,
)
from framenest.infrastructure.ai.constants import (
    BUILTIN_PROVIDER_IDS,
    VERCEL_AI_GATEWAY_PROVIDER_ID,
)
from framenest.infrastructure.ai.credentials import load_ai_credential
from framenest.infrastructure.ai.provider_activity import (
    PROVIDER_CATEGORY_SUCCESS,
    classify_provider_exception,
)
from framenest.infrastructure.ai.provider_records import (
    DECLARED_PROTOCOLS,
    MAX_AI_CONFIG_BYTES,
    MAX_DECLARED_MODELS_PER_PROVIDER,
    MAX_DECLARED_PROVIDERS,
    AiProviderRecord,
    AiProviderRecordError,
    parse_declared_provider_record,
    validate_declared_protocol,
    validate_provider_identifier,
)
from framenest.infrastructure.ai.registry import (
    AiProviderDefinition,
    DynamicAiProviderResolver,
    provider_definitions,
)
from framenest.infrastructure.ai.vision_probe import (
    EXPECTED_COLOR,
    VISION_PROBE_PROMPT,
    VisionProbeState,
    default_vision_probe_state_path,
    load_matching_vision_probe_state,
    load_vision_probe_fixture,
    match_expected_color,
    write_vision_probe_state,
)

NO_STORE_HEADERS = {"Cache-Control": "no-store"}

AI_CONFIG_UNAVAILABLE_CODE = "AI_CONFIG_UNAVAILABLE"
AI_CONFIG_UNAVAILABLE_MESSAGE = "The AI provider configuration could not be read or saved."
AI_PROVIDER_BUILTIN_CODE = "AI_PROVIDER_BUILTIN"
AI_PROVIDER_BUILTIN_MESSAGE = "Built-in AI providers cannot be modified or removed."
AI_PROVIDER_ACTIVE_CODE = "AI_PROVIDER_ACTIVE"
AI_PROVIDER_ACTIVE_MESSAGE = "The active AI provider cannot be removed; select another provider first."
AI_PROVIDER_ACTIVE_MODEL_MESSAGE = (
    "The active AI provider model must stay declared; select another model first."
)
AI_PROVIDER_INVALID_CODE = "AI_PROVIDER_INVALID"
AI_PROVIDER_INVALID_MESSAGE = "The AI provider request is invalid."
AI_PROVIDER_NOT_FOUND_CODE = "AI_PROVIDER_NOT_FOUND"
AI_PROVIDER_NOT_FOUND_MESSAGE = "AI provider was not found."
AI_PROVIDER_PROTOCOL_UNSUPPORTED_CODE = "AI_PROVIDER_PROTOCOL_UNSUPPORTED"
AI_PROVIDER_PROTOCOL_UNSUPPORTED_MESSAGE = "The declared AI provider protocol is not supported."
AI_MODEL_CAPABILITY_MISSING_CODE = "AI_MODEL_CAPABILITY_MISSING"
AI_MODEL_CAPABILITY_MISSING_MESSAGE = (
    "The selected model does not declare the vision_input capability."
)
AI_PROVIDER_NOT_CONFIGURED_CODE = "AI_PROVIDER_NOT_CONFIGURED"
AI_PROVIDER_NOT_CONFIGURED_MESSAGE = "The AI provider is not configured."
AI_PROVIDER_BUSY_CODE = "AI_PROVIDER_BUSY"
AI_PROVIDER_BUSY_MESSAGE = "Another AI provider operation is already running."
CLOUD_CONFIRMATION_REQUIRED_CODE = "CLOUD_CONFIRMATION_REQUIRED"
CLOUD_CONFIRMATION_REQUIRED_MESSAGE = "Explicit cloud upload confirmation is required."
AI_PROVIDER_AUTHENTICATION_FAILED_CODE = "AI_PROVIDER_AUTHENTICATION_FAILED"
AI_PROVIDER_AUTHENTICATION_FAILED_MESSAGE = (
    "The provider rejected the credential or the selected model is not included "
    "in the current subscription."
)
AI_PROVIDER_RATE_LIMITED_CODE = "AI_PROVIDER_RATE_LIMITED"
AI_PROVIDER_RATE_LIMITED_MESSAGE = "The AI provider rate limit was reached. Try again later."
AI_PROVIDER_MODEL_UNAVAILABLE_CODE = "AI_PROVIDER_MODEL_UNAVAILABLE"
AI_PROVIDER_MODEL_UNAVAILABLE_MESSAGE = "The configured AI provider model is not available."
AI_PROVIDER_UNAVAILABLE_CODE = "AI_PROVIDER_UNAVAILABLE"
AI_PROVIDER_UNAVAILABLE_MESSAGE = "The AI provider is not available."
AI_PROVIDER_INVALID_RESPONSE_CODE = "AI_PROVIDER_INVALID_RESPONSE"
AI_PROVIDER_INVALID_RESPONSE_MESSAGE = "The AI provider returned an invalid response."
AI_PROVIDER_FAILED_CODE = "AI_PROVIDER_FAILED"
AI_PROVIDER_FAILED_MESSAGE = "The AI provider request failed."

_PROVIDER_ERROR_RESPONSES = {
    "authentication_failed": (
        503,
        AI_PROVIDER_AUTHENTICATION_FAILED_CODE,
        AI_PROVIDER_AUTHENTICATION_FAILED_MESSAGE,
    ),
    "rate_limited_or_quota_exhausted": (
        429,
        AI_PROVIDER_RATE_LIMITED_CODE,
        AI_PROVIDER_RATE_LIMITED_MESSAGE,
    ),
    "model_unavailable": (
        503,
        AI_PROVIDER_MODEL_UNAVAILABLE_CODE,
        AI_PROVIDER_MODEL_UNAVAILABLE_MESSAGE,
    ),
    "provider_unreachable": (
        503,
        AI_PROVIDER_UNAVAILABLE_CODE,
        AI_PROVIDER_UNAVAILABLE_MESSAGE,
    ),
    "invalid_response": (
        502,
        AI_PROVIDER_INVALID_RESPONSE_CODE,
        AI_PROVIDER_INVALID_RESPONSE_MESSAGE,
    ),
    "provider_error": (
        502,
        AI_PROVIDER_FAILED_CODE,
        AI_PROVIDER_FAILED_MESSAGE,
    ),
}


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class AiProviderModelPutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    capabilities: list[str] = Field(default_factory=list)


class AiProviderPutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    protocol: str
    base_url: str
    credential_env: str
    models: dict[str, AiProviderModelPutRequest]


class AiActiveSelectionPutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str
    model_id: str


class AiPingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AiPongRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_cloud_upload: bool | None = None


class AiProviderModelResponse(BaseModel):
    model_id: str
    display_name: str
    capabilities: list[str]


class AiProviderSummaryResponse(BaseModel):
    provider_id: str
    display_name: str
    source: str
    protocol: str
    base_url: str
    credential_env: str
    credential_available: bool
    selected_model_id: str | None = None
    supports_vision: bool
    models: list[AiProviderModelResponse]
    last_test: dict[str, object] | None = None
    last_vision_probe: dict[str, object] | None = None


class AiProviderListResponse(BaseModel):
    active_provider_id: str | None = None
    active_model_id: str | None = None
    configuration_source: str
    providers: list[AiProviderSummaryResponse]
    supported_protocols: list[str]
    limits: dict[str, int]


class AiProviderRecordResponse(BaseModel):
    provider_id: str
    display_name: str
    source: str
    protocol: str
    base_url: str
    credential_env: str
    models: list[AiProviderModelResponse]


class AiActiveSelectionResponse(BaseModel):
    active_provider_id: str
    active_model_id: str


class AiPingResponse(BaseModel):
    status: str
    tested_at_ms: int
    provider_id: str
    model_id: str
    credential_available: bool


class AiPongResponse(BaseModel):
    status: str
    matched: bool
    expected_color: str
    observed_color: str | None = None
    probed_at_ms: int
    provider_id: str
    model_id: str


@dataclass(frozen=True, slots=True)
class AiAdminApiDependencies:
    """Injected dependencies for administrator AI provider routes."""

    resolver: DynamicAiProviderResolver
    environ: Mapping[str, str] | None = None
    config_path: Path | None = None


def create_ai_admin_api_router(dependencies: AiAdminApiDependencies) -> APIRouter:
    """Create the administrator AI provider router."""
    router = APIRouter()

    @router.get(
        "/api/admin/ai/providers",
        response_model=AiProviderListResponse,
        responses={503: {"model": ErrorResponse}},
    )
    def list_ai_providers() -> JSONResponse:
        config_path = _config_path(dependencies)
        try:
            resolved = dependencies.resolver.resolve()
            config = load_ai_server_config(config_path)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        definitions = provider_definitions(config)
        environ = _environ(dependencies)
        test_state_path = default_ai_test_state_path(config_path)
        vision_state_path = default_vision_probe_state_path(config_path)
        providers: list[AiProviderSummaryResponse] = []
        for provider_id, definition in definitions.items():
            credential = load_ai_credential(definition.credential_environment_name, environ)
            selected_model_id = (
                None if config is None else config.provider_models.get(provider_id)
            )
            reference_model_id = selected_model_id or definition.default_model_id
            last_test = _matching_test_state(
                test_state_path,
                provider_id=provider_id,
                model_id=reference_model_id,
            )
            providers.append(
                AiProviderSummaryResponse(
                    provider_id=provider_id,
                    display_name=definition.display_name,
                    source=definition.source,
                    protocol=definition.protocol,
                    base_url=definition.base_url,
                    credential_env=definition.credential_environment_name,
                    credential_available=credential is not None,
                    selected_model_id=selected_model_id,
                    supports_vision=_declares_vision(definition, reference_model_id),
                    models=[
                        AiProviderModelResponse(
                            model_id=model.model_id,
                            display_name=model.display_name,
                            capabilities=list(model.capabilities),
                        )
                        for model in definition.models
                    ],
                    last_test=_test_state_payload(last_test),
                    last_vision_probe=_vision_probe_payload(
                        load_matching_vision_probe_state(
                            vision_state_path,
                            provider_id=provider_id,
                            model_id=reference_model_id,
                        )
                    ),
                )
            )
        return _json(
            AiProviderListResponse(
                active_provider_id=resolved.provider_id,
                active_model_id=resolved.model_id,
                configuration_source=resolved.source,
                providers=providers,
                supported_protocols=sorted(DECLARED_PROTOCOLS),
                limits={
                    "max_declared_providers": MAX_DECLARED_PROVIDERS,
                    "max_models_per_provider": MAX_DECLARED_MODELS_PER_PROVIDER,
                    "max_config_bytes": MAX_AI_CONFIG_BYTES,
                },
            )
        )

    @router.put(
        "/api/admin/ai/providers/{provider_id}",
        response_model=AiProviderRecordResponse,
        responses={
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def put_ai_provider(
        provider_id: str,
        request: AiProviderPutRequest,
    ) -> JSONResponse:
        try:
            validated_provider_id = validate_provider_identifier(provider_id)
        except AiProviderRecordError:
            return _error(422, AI_PROVIDER_INVALID_CODE, AI_PROVIDER_INVALID_MESSAGE)
        if validated_provider_id in BUILTIN_PROVIDER_IDS:
            return _error(409, AI_PROVIDER_BUILTIN_CODE, AI_PROVIDER_BUILTIN_MESSAGE)
        try:
            validate_declared_protocol(request.protocol)
        except AiProviderRecordError:
            return _error(
                422,
                AI_PROVIDER_PROTOCOL_UNSUPPORTED_CODE,
                AI_PROVIDER_PROTOCOL_UNSUPPORTED_MESSAGE,
            )
        payload = {
            "name": request.name,
            "protocol": request.protocol,
            "base_url": request.base_url,
            "credential_env": request.credential_env,
            "models": {
                model_id: {
                    "name": model.name,
                    "capabilities": list(model.capabilities),
                }
                for model_id, model in request.models.items()
            },
        }
        try:
            record = parse_declared_provider_record(validated_provider_id, payload)
        except AiProviderRecordError as exc:
            return _error(422, AI_PROVIDER_INVALID_CODE, str(exc))
        config_path = _config_path(dependencies)
        try:
            current = load_ai_server_config(config_path)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if (
            current is not None
            and current.active_provider_id == validated_provider_id
            and current.provider_models.get(validated_provider_id)
            not in {model.model_id for model in record.models}
        ):
            return _error(409, AI_PROVIDER_ACTIVE_CODE, AI_PROVIDER_ACTIVE_MODEL_MESSAGE)

        def _upsert(current_config: AiServerConfig | None) -> AiServerConfig:
            base = current_config or _empty_config()
            providers = dict(base.providers)
            providers[validated_provider_id] = record
            return replace(base, providers=providers)

        try:
            updated = mutate_ai_server_config(config_path, _upsert)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        return _json(_record_response(updated.providers[validated_provider_id]))

    @router.delete(
        "/api/admin/ai/providers/{provider_id}",
        response_model=dict,
        responses={
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def delete_ai_provider(provider_id: str) -> JSONResponse:
        try:
            validated_provider_id = validate_provider_identifier(provider_id)
        except AiProviderRecordError:
            return _error(422, AI_PROVIDER_INVALID_CODE, AI_PROVIDER_INVALID_MESSAGE)
        if validated_provider_id in BUILTIN_PROVIDER_IDS:
            return _error(409, AI_PROVIDER_BUILTIN_CODE, AI_PROVIDER_BUILTIN_MESSAGE)
        config_path = _config_path(dependencies)
        try:
            current = load_ai_server_config(config_path)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if current is None or validated_provider_id not in current.providers:
            return _error(404, AI_PROVIDER_NOT_FOUND_CODE, AI_PROVIDER_NOT_FOUND_MESSAGE)
        if current.active_provider_id == validated_provider_id:
            return _error(409, AI_PROVIDER_ACTIVE_CODE, AI_PROVIDER_ACTIVE_MESSAGE)

        def _remove(current_config: AiServerConfig | None) -> AiServerConfig:
            assert current_config is not None
            providers = dict(current_config.providers)
            providers.pop(validated_provider_id, None)
            provider_models = {
                key: value
                for key, value in current_config.provider_models.items()
                if key != validated_provider_id
            }
            return replace(
                current_config,
                providers=providers,
                provider_models=provider_models,
            )

        try:
            mutate_ai_server_config(config_path, _remove)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        return _json({"removed_provider_id": validated_provider_id})

    @router.put(
        "/api/admin/ai/active-selection",
        response_model=AiActiveSelectionResponse,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def put_active_selection(request: AiActiveSelectionPutRequest) -> JSONResponse:
        try:
            selected_provider_id = validate_provider_id(request.provider_id)
            selected_model_id = validate_model_id(request.model_id)
        except AiConfigurationError as exc:
            return _error(422, AI_PROVIDER_INVALID_CODE, str(exc))
        config_path = _config_path(dependencies)
        try:
            current = load_ai_server_config(config_path)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        definitions = provider_definitions(current)
        definition = definitions.get(selected_provider_id)
        if definition is None:
            return _error(404, AI_PROVIDER_NOT_FOUND_CODE, AI_PROVIDER_NOT_FOUND_MESSAGE)
        if not definition.builtin and selected_model_id not in {
            model.model_id for model in definition.models
        }:
            return _error(422, AI_PROVIDER_INVALID_CODE, AI_PROVIDER_INVALID_MESSAGE)

        def _activate(current_config: AiServerConfig | None) -> AiServerConfig:
            base = current_config or _empty_config()
            provider_models = dict(base.provider_models)
            provider_models[selected_provider_id] = selected_model_id
            return replace(
                base,
                active_provider_id=selected_provider_id,
                provider_models=provider_models,
            )

        try:
            mutate_ai_server_config(config_path, _activate)
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        return _json(
            AiActiveSelectionResponse(
                active_provider_id=selected_provider_id,
                active_model_id=selected_model_id,
            )
        )

    @router.post(
        "/api/admin/ai/ping",
        response_model=AiPingResponse,
        responses={
            409: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def ping_ai_provider(request: AiPingRequest) -> JSONResponse:
        try:
            resolved = dependencies.resolver.resolve()
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if resolved.provider_id is None:
            return _error(503, AI_PROVIDER_NOT_CONFIGURED_CODE, AI_PROVIDER_NOT_CONFIGURED_MESSAGE)
        if resolved.provider is None or not resolved.credential_available:
            return _error(
                503,
                AI_PROVIDER_NOT_CONFIGURED_CODE,
                (
                    "The AI provider credential is not available. "
                    f"Required environment variable: {resolved.credential_environment_name}."
                ),
            )
        config_path = _config_path(dependencies)
        lock_path = default_ai_test_state_path(config_path).parent / ".test.lock"
        try:
            lock = acquire_ai_activity_lock(lock_path)
        except AiActivityLockError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if lock is None:
            return _error(409, AI_PROVIDER_BUSY_CODE, AI_PROVIDER_BUSY_MESSAGE)
        try:
            try:
                resolved.provider.test_connection()
                category = PROVIDER_CATEGORY_SUCCESS
            except Exception as exc:
                category = classify_provider_exception(exc)
            tested_at_ms = now_ms()
            try:
                write_ai_test_state(
                    AiTestState(
                        provider_id=resolved.provider_id,
                        model_id=resolved.model_id,
                        status=category,
                        tested_at_ms=tested_at_ms,
                    ),
                    default_ai_test_state_path(config_path),
                )
            except AiConfigurationError:
                return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
            if category != PROVIDER_CATEGORY_SUCCESS:
                return _provider_category_error(category)
            return _json(
                AiPingResponse(
                    status=category,
                    tested_at_ms=tested_at_ms,
                    provider_id=resolved.provider_id,
                    model_id=resolved.model_id or "",
                    credential_available=True,
                )
            )
        finally:
            lock.release()

    @router.post(
        "/api/admin/ai/pong",
        response_model=AiPongResponse,
        responses={
            409: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def pong_ai_provider(request: AiPongRequest) -> JSONResponse:
        if request.confirm_cloud_upload is not True:
            return _error(
                409,
                CLOUD_CONFIRMATION_REQUIRED_CODE,
                CLOUD_CONFIRMATION_REQUIRED_MESSAGE,
            )
        try:
            resolved = dependencies.resolver.resolve()
        except AiConfigurationError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if resolved.provider_id is None:
            return _error(503, AI_PROVIDER_NOT_CONFIGURED_CODE, AI_PROVIDER_NOT_CONFIGURED_MESSAGE)
        if resolved.provider is None or not resolved.credential_available:
            return _error(
                503,
                AI_PROVIDER_NOT_CONFIGURED_CODE,
                (
                    "The AI provider credential is not available. "
                    f"Required environment variable: {resolved.credential_environment_name}."
                ),
            )
        if "vision_input" not in resolved.capabilities_for(resolved.model_id or ""):
            return _error(
                409,
                AI_MODEL_CAPABILITY_MISSING_CODE,
                AI_MODEL_CAPABILITY_MISSING_MESSAGE,
            )
        config_path = _config_path(dependencies)
        state_path = default_vision_probe_state_path(config_path)
        lock_path = state_path.parent / ".vision-probe.lock"
        try:
            lock = acquire_ai_activity_lock(lock_path)
        except AiActivityLockError:
            return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
        if lock is None:
            return _error(409, AI_PROVIDER_BUSY_CODE, AI_PROVIDER_BUSY_MESSAGE)
        try:
            status = "provider_error"
            matched = False
            observed_color: str | None = None
            try:
                image_png = load_vision_probe_fixture()
                content_text = resolved.provider.probe_vision(
                    prompt=VISION_PROBE_PROMPT,
                    image_png=image_png,
                )
                matched, observed_color = match_expected_color(content_text)
                status = "success" if matched else "mismatch"
            except Exception as exc:
                status = classify_provider_exception(exc)
            probed_at_ms = now_ms()
            try:
                write_vision_probe_state(
                    VisionProbeState(
                        provider_id=resolved.provider_id,
                        model_id=resolved.model_id,
                        status=status,
                        matched=matched,
                        observed_color=observed_color,
                        probed_at_ms=probed_at_ms,
                    ),
                    state_path,
                )
            except AiConfigurationError:
                return _error(503, AI_CONFIG_UNAVAILABLE_CODE, AI_CONFIG_UNAVAILABLE_MESSAGE)
            if status != "success" and status != "mismatch":
                return _provider_category_error(status)
            return _json(
                AiPongResponse(
                    status=status,
                    matched=matched,
                    expected_color=EXPECTED_COLOR,
                    observed_color=observed_color,
                    probed_at_ms=probed_at_ms,
                    provider_id=resolved.provider_id,
                    model_id=resolved.model_id or "",
                )
            )
        finally:
            lock.release()

    return router


def _config_path(dependencies: AiAdminApiDependencies) -> Path:
    if dependencies.config_path is not None:
        return dependencies.config_path
    return default_ai_config_path(dependencies.environ)


def _environ(dependencies: AiAdminApiDependencies) -> Mapping[str, str]:
    return os.environ if dependencies.environ is None else dependencies.environ


def _empty_config() -> AiServerConfig:
    return AiServerConfig(
        active_provider_id=VERCEL_AI_GATEWAY_PROVIDER_ID,
        provider_models={},
        updated_at_ms=now_ms(),
    )


def _declares_vision(definition: AiProviderDefinition, model_id: str) -> bool:
    return any(
        model.model_id == model_id and "vision_input" in model.capabilities
        for model in definition.models
    )


def _matching_test_state(
    path: Path,
    *,
    provider_id: str,
    model_id: str,
) -> AiTestState | None:
    try:
        state = load_ai_test_state(path)
    except AiConfigurationError:
        return None
    if state is None:
        return None
    if state.provider_id != provider_id or state.model_id != model_id:
        return None
    return state


def _test_state_payload(state: AiTestState | None) -> dict[str, object] | None:
    if state is None:
        return None
    return {"status": state.status, "tested_at_ms": state.tested_at_ms}


def _vision_probe_payload(state: VisionProbeState | None) -> dict[str, object] | None:
    if state is None:
        return None
    return {
        "status": state.status,
        "matched": state.matched,
        "observed_color": state.observed_color,
        "probed_at_ms": state.probed_at_ms,
    }


def _record_response(record: AiProviderRecord) -> AiProviderRecordResponse:
    return AiProviderRecordResponse(
        provider_id=record.provider_id,
        display_name=record.display_name,
        source=record.source,
        protocol=record.protocol,
        base_url=record.base_url,
        credential_env=record.credential_env,
        models=[
            AiProviderModelResponse(
                model_id=model.model_id,
                display_name=model.display_name,
                capabilities=list(model.capabilities),
            )
            for model in record.models
        ],
    )


def _provider_category_error(category: str) -> JSONResponse:
    status_code, code, message = _PROVIDER_ERROR_RESPONSES.get(
        category,
        _PROVIDER_ERROR_RESPONSES["provider_error"],
    )
    return _error(status_code, code, message)


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=ErrorBody(code=code, message=message)).model_dump(),
        headers=NO_STORE_HEADERS,
    )


def _json(payload: BaseModel | dict) -> JSONResponse:
    content = payload.model_dump() if isinstance(payload, BaseModel) else payload
    return JSONResponse(status_code=200, content=content, headers=NO_STORE_HEADERS)
