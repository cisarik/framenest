"""X request API router behavior with a fake service."""

from __future__ import annotations

import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

from framenest.adapters.api.tailscale_ingress import SCOPE_IDENTITY
from framenest.adapters.api.x_request_api import (
    XRequestApiDependencies,
    create_x_request_api_router,
)
from framenest.domain.identity_access import (
    CAPABILITY_X_REQUEST,
    IdentityContext,
)


def _identity(login: str) -> IdentityContext:
    capabilities = frozenset({CAPABILITY_X_REQUEST, "gallery.read"})
    return IdentityContext(
        login=login,
        login_key=login,
        display_name=login,
        role="user",
        capabilities=capabilities,
        provenance="tailscale-serve",
    )


def _app(service) -> FastAPI:
    router = create_x_request_api_router(
        XRequestApiDependencies(service=service, audit_recorder=None, enabled=True)
    )
    app = FastAPI()
    app.include_router(router)

    @app.middleware("http")
    async def _inject_identity(request, call_next):
        request.scope[SCOPE_IDENTITY] = _identity("alice")
        return await call_next(request)

    return app


def _snapshot(claim_id: object, state: str = "submitted") -> types.SimpleNamespace:
    claim_id = str(claim_id)
    return types.SimpleNamespace(
        claim_id=claim_id,
        request_id=claim_id,
        phase="queued" if state == "submitted" else "completed",
        state=state,
        x_post_id="123",
        submitted_url="https://x.com/a/status/123",
        canonical_url="https://x.com/a/status/123",
        title=None,
        failure_code=None,
        retry_of_claim_id=None,
        created_at_ms=1,
        updated_at_ms=1,
        completed_at_ms=None,
        assets=[],
    )


_VALID_ID = "00000000-0000-4000-8000-000000000001"


def _service_fake():
    return types.SimpleNamespace(
        submit=lambda url, login_key: types.SimpleNamespace(
            request_id=_VALID_ID, submission_result="new"
        ),
        list_owned=lambda login_key, limit, cursor: types.SimpleNamespace(
            items=[_snapshot(_VALID_ID)], next_cursor=None
        ),
        get_owned=lambda cid, login_key: _snapshot(cid),
        retry=lambda cid, login_key: _snapshot(cid, state="queued"),
    )


def test_submit_x_request_returns_item() -> None:
    client = TestClient(_app(_service_fake()))
    response = client.post("/api/x/requests", json={"url": "https://x.com/a/status/123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == _VALID_ID
    assert payload["phase"] == "queued"


def test_missing_identity_fails_closed() -> None:
    router = create_x_request_api_router(
        XRequestApiDependencies(service=_service_fake(), audit_recorder=None, enabled=True)
    )
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post(
        "/api/x/requests", json={"url": "https://x.com/a/status/123"}
    )
    assert response.status_code == 401
