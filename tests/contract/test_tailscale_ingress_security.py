"""Contract tests for the Tailscale trusted-ingress security boundary.

These tests bind the production ``tailscale_uds`` ingress mode to its
invariants: Serve-injected identity is the only remote identity source,
capabilities are enforced server-side, browser mutations require the exact
external Origin plus the FrameNest mutation header, privileged actions are
audited, and the local channel stays narrowly operational.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.adapters.api.tailscale_ingress import (
    ROUTE_POLICIES,
    _AUTHENTICATED_FALLBACK_POLICY,
    find_route_policy,
)
from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.engine import (
    create_sqlite_engine,
    dispose_engine,
)
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

EXTERNAL_ORIGIN = "https://nuc-1.example.ts.net"
EXTERNAL_HOST = "nuc-1.example.ts.net"
ADMIN_LOGIN = "admin@example.com"
USER_LOGIN = "user@example.com"
STRANGER_LOGIN = "stranger@example.com"

ADMIN_CAPABILITY_SAMPLE = "metadata.canonical.write"
USER_CAPABILITIES = {"gallery.read", "media.original.read", "media.download"}


def _serve_headers(
    login: str = ADMIN_LOGIN,
    name: str = "Admin User",
) -> dict[str, str]:
    return {
        "Tailscale-User-Login": login,
        "Tailscale-User-Name": name,
        "X-Forwarded-Proto": "https",
        "X-Forwarded-Host": EXTERNAL_HOST,
    }


def _mutation_headers(login: str = ADMIN_LOGIN) -> dict[str, str]:
    return {
        **_serve_headers(login),
        "Origin": EXTERNAL_ORIGIN,
        "X-FrameNest-Request": "1",
    }


@pytest.fixture
def tailscale_client(tmp_path: Path):
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        gallery_preview_cache_path=tmp_path / "previews",
        ingress_mode="tailscale_uds",
        uds_path=tmp_path / "framenest.sock",
        external_origin=EXTERNAL_ORIGIN,
        identity_map={ADMIN_LOGIN: "admin", USER_LOGIN: "user"},
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client, settings


def _audit_rows(database_path: Path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            "SELECT request_id, actor_login, actor_key, identity_provenance, role,"
            " capability, action, target_type, target_id, outcome, http_status"
            " FROM security_audit_events ORDER BY occurred_at_ms, id"
        ).fetchall()
    finally:
        connection.close()


def _error_code(response) -> str:
    payload = response.json()
    return payload["error"]["code"]


# --- Trusted ingress and identity ---------------------------------------


def test_valid_serve_identity_parses_admin_identity(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get("/api/identity/me", headers=_serve_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["login"] == ADMIN_LOGIN
    assert payload["display_name"] == "Admin User"
    assert payload["role"] == "admin"
    assert payload["provenance"] == "tailscale-serve"
    assert ADMIN_CAPABILITY_SAMPLE in payload["capabilities"]
    assert payload["capabilities"] == sorted(payload["capabilities"])


def test_missing_identity_login_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _serve_headers()
    del headers["Tailscale-User-Login"]
    response = client.get("/api/media", headers=headers)
    assert response.status_code == 401
    assert _error_code(response) == "IDENTITY_REQUIRED"


def test_tagged_device_without_user_login_fails_closed(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = {
        "Tailscale-User-Name": "Tagged Device",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-Host": EXTERNAL_HOST,
    }
    response = client.get("/api/media", headers=headers)
    assert response.status_code == 401
    assert _error_code(response) == "IDENTITY_REQUIRED"


def test_malformed_identity_login_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get(
        "/api/media", headers=_serve_headers(login="bad login@example.com")
    )
    assert response.status_code == 401
    assert _error_code(response) == "IDENTITY_REQUIRED"


def test_duplicate_identity_header_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get(
        "/api/media",
        headers=[
            ("Tailscale-User-Login", ADMIN_LOGIN),
            ("Tailscale-User-Login", USER_LOGIN),
            ("X-Forwarded-Proto", "https"),
            ("X-Forwarded-Host", EXTERNAL_HOST),
        ],
    )
    assert response.status_code == 400
    assert _error_code(response) == "INGRESS_HEADERS_CONFLICT"


def test_conflicting_forwarded_proto_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _serve_headers()
    headers["X-Forwarded-Proto"] = "http"
    response = client.get("/api/media", headers=headers)
    assert response.status_code == 403
    assert _error_code(response) == "INGRESS_HEADERS_FORBIDDEN"


def test_conflicting_forwarded_host_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _serve_headers()
    headers["X-Forwarded-Host"] = "other-host.example.ts.net"
    response = client.get("/api/media", headers=headers)
    assert response.status_code == 403
    assert _error_code(response) == "INGRESS_HEADERS_FORBIDDEN"


def test_unmarked_local_channel_keeps_only_narrow_health(tailscale_client) -> None:
    client, _ = tailscale_client
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    for path in ("/", "/api/media", "/api/identity/me", "/api/status/cloud"):
        response = client.get(path)
        assert response.status_code == 401
        assert _error_code(response) == "IDENTITY_REQUIRED"


def test_tcp_mode_has_no_identity_api_and_ignores_spoofed_headers(
    tmp_path: Path,
) -> None:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        gallery_preview_cache_path=tmp_path / "previews",
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        identity = client.get("/api/identity/me", headers=_serve_headers())
        assert identity.status_code == 404
        cloud = client.get("/api/status/cloud", headers=_serve_headers())
        assert cloud.status_code == 200
        assert cloud.json()["connection"] == "loopback"
        media = client.get("/api/media", headers=_serve_headers(STRANGER_LOGIN))
        assert media.status_code == 200


def test_display_name_change_never_alters_privilege(tailscale_client) -> None:
    client, _ = tailscale_client
    first = client.get(
        "/api/identity/me", headers=_serve_headers(USER_LOGIN, "First Name")
    )
    second = client.get(
        "/api/identity/me", headers=_serve_headers(USER_LOGIN, "Renamed")
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["role"] == second.json()["role"] == "user"
    assert first.json()["capabilities"] == second.json()["capabilities"]
    assert second.json()["display_name"] == "Renamed"
    denied = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(USER_LOGIN),
        json={"key": "alpha", "display_name": "Alpha"},
    )
    assert denied.status_code == 403


def test_login_normalization_maps_case_and_whitespace_variants(
    tailscale_client,
) -> None:
    client, _ = tailscale_client
    response = client.get(
        "/api/identity/me", headers=_serve_headers(login=" Admin@Example.COM ")
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "admin"
    assert payload["login"] == "Admin@Example.COM"


def test_unknown_identity_is_denied_closed(tailscale_client) -> None:
    client, settings = tailscale_client
    response = client.get("/api/media", headers=_serve_headers(STRANGER_LOGIN))
    assert response.status_code == 403
    assert _error_code(response) == "IDENTITY_NOT_AUTHORIZED"
    identity = client.get("/api/identity/me", headers=_serve_headers(STRANGER_LOGIN))
    assert identity.status_code == 403
    assert _audit_rows(settings.database_path) == []


def test_remote_health_stays_sanitized(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get("/health", headers=_serve_headers(USER_LOGIN))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    unmapped = client.get("/health", headers=_serve_headers(STRANGER_LOGIN))
    assert unmapped.status_code == 403


# --- Mapping and authorization ------------------------------------------


def test_ordinary_user_identity_payload(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get("/api/identity/me", headers=_serve_headers(USER_LOGIN))
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "user"
    assert set(payload["capabilities"]) == USER_CAPABILITIES


def test_ordinary_user_reads_succeed(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _serve_headers(USER_LOGIN)
    assert client.get("/", headers=headers).status_code == 200
    assert client.get("/api/media", headers=headers).status_code == 200
    assert client.get("/api/libraries", headers=headers).status_code == 200
    assert client.get("/api/canonical-tags", headers=headers).status_code == 200


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("POST", "/api/canonical-tags", {"key": "alpha", "display_name": "Alpha"}),
        ("PUT", f"/api/media/{uuid.uuid4()}/metadata", {}),
        ("POST", "/api/uploads", {}),
        ("GET", "/api/uploads/capability", None),
        ("POST", f"/api/libraries/{uuid.uuid4()}/scan-preview", None),
        ("POST", f"/api/libraries/{uuid.uuid4()}/media-imports", {}),
        ("POST", f"/api/libraries/{uuid.uuid4()}/media-analysis-preview", {}),
        ("POST", f"/api/libraries/{uuid.uuid4()}/media-suggestion-preview", {}),
        ("GET", "/api/ai/media-suggestion-capability", None),
        ("GET", "/api/ai/automatic-analysis-capability", None),
    ],
)
def test_ordinary_user_direct_privileged_calls_fail(
    tailscale_client, method: str, path: str, body: dict | None
) -> None:
    client, _ = tailscale_client
    headers = _mutation_headers(USER_LOGIN)
    if method == "GET":
        response = client.get(path, headers=_serve_headers(USER_LOGIN))
    elif method == "PUT":
        response = client.put(path, headers=headers, json=body)
    else:
        response = client.post(path, headers=headers, json=body)
    assert response.status_code == 403
    assert _error_code(response) == "CAPABILITY_DENIED"


def test_admin_privileged_operation_succeeds(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(),
        json={"key": "alpha", "display_name": "Alpha"},
    )
    assert response.status_code == 201


def test_operator_routes_are_not_remote_routes(tailscale_client) -> None:
    client, _ = tailscale_client
    claim_id = str(uuid.uuid4())
    for method, path in (
        ("GET", f"/api/operator/youtube/claims/{claim_id}"),
        ("POST", "/api/operator/youtube/claims"),
        ("POST", f"/api/operator/youtube/claims/{claim_id}/retry"),
    ):
        if method == "GET":
            response = client.get(path, headers=_serve_headers())
        else:
            response = client.post(path, headers=_mutation_headers(), json={})
        assert response.status_code == 404
        assert _error_code(response) == "NOT_FOUND"


def test_operator_routes_remain_available_on_local_channel(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.post("/api/operator/youtube/claims", json={})
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "YOUTUBE_OPERATOR_NOT_CONFIGURED"


def test_route_policies_match_the_application_route_inventory(
    tailscale_client,
) -> None:
    client, _ = tailscale_client
    found: list[tuple[str, list[str]]] = []

    def walk(routes) -> None:
        for route in routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                found.append(
                    (
                        route.path,
                        [
                            method
                            for method in sorted(route.methods)
                            if method not in ("HEAD", "OPTIONS")
                        ],
                    )
                )
            elif hasattr(route, "original_router"):
                walk(route.original_router.routes)
            elif hasattr(route, "routes"):
                walk(route.routes)

    walk(client.app.routes)
    assert found

    def concrete(path: str) -> str:
        resolved = path
        while "{" in resolved:
            start = resolved.index("{")
            end = resolved.index("}", start)
            name = resolved[start + 1 : end]
            replacement = str(uuid.uuid4()) if name == "upload_id" else f"{name}-value"
            resolved = resolved[:start] + replacement + resolved[end + 1 :]
        return resolved

    for path, methods in found:
        for method in methods:
            matching = [
                policy
                for policy in ROUTE_POLICIES
                if policy.match(method, concrete(path)) is not None
            ]
            assert len(matching) == 1, (method, path)
    for policy in ROUTE_POLICIES:
        assert any(
            policy.match(method, concrete(path)) is not None
            for path, methods in found
            for method in methods
        ), (policy.method, policy.pattern.pattern)


def test_error_responses_are_sanitized(tailscale_client) -> None:
    client, settings = tailscale_client
    responses = [
        client.get("/api/media"),
        client.get("/api/media", headers=_serve_headers(STRANGER_LOGIN)),
        client.post(
            "/api/canonical-tags",
            headers=_mutation_headers(USER_LOGIN),
            json={"key": "alpha", "display_name": "Alpha"},
        ),
    ]
    for response in responses:
        assert response.headers["content-type"] == "application/json"
        payload = response.json()
        assert set(payload) == {"error"}
        assert set(payload["error"]) == {"code", "message"}
        body = response.text
        assert "Traceback" not in body
        assert str(settings.database_path) not in body
        assert str(tmp_path_sentinel(settings)) not in body


def tmp_path_sentinel(settings: FrameNestSettings) -> Path:
    return settings.database_path.parent


# --- CSRF, Origin, and CORS ----------------------------------------------


def test_same_origin_mutation_with_header_succeeds(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(),
        json={"key": "beta", "display_name": "Beta"},
    )
    assert response.status_code == 201


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example",
        "http://nuc-1.example.ts.net",
        "https://nuc-1.example.ts.net.",
        "https://nuc-1.example.ts.net:443",
        "https://nuc-1.example.ts.net/",
        "HTTPS://nuc-1.example.ts.net",
        "null",
    ],
)
def test_hostile_or_inexact_origin_is_rejected(
    tailscale_client, origin: str
) -> None:
    client, _ = tailscale_client
    headers = _mutation_headers()
    headers["Origin"] = origin
    response = client.post(
        "/api/canonical-tags",
        headers=headers,
        json={"key": "gamma", "display_name": "Gamma"},
    )
    assert response.status_code == 403
    assert _error_code(response) == "MUTATION_ORIGIN_FORBIDDEN"


def test_missing_origin_is_rejected_for_mutations(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _mutation_headers()
    del headers["Origin"]
    response = client.post(
        "/api/canonical-tags",
        headers=headers,
        json={"key": "delta", "display_name": "Delta"},
    )
    assert response.status_code == 403
    assert _error_code(response) == "MUTATION_ORIGIN_FORBIDDEN"


def test_duplicate_origin_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=[
            ("Tailscale-User-Login", ADMIN_LOGIN),
            ("Tailscale-User-Name", "Admin User"),
            ("X-Forwarded-Proto", "https"),
            ("X-Forwarded-Host", EXTERNAL_HOST),
            ("Origin", EXTERNAL_ORIGIN),
            ("Origin", EXTERNAL_ORIGIN),
            ("X-FrameNest-Request", "1"),
            ("Content-Type", "application/json"),
        ],
        content=b'{"key": "epsilon", "display_name": "Epsilon"}',
    )
    assert response.status_code == 400
    assert _error_code(response) == "INGRESS_HEADERS_CONFLICT"


def test_missing_mutation_header_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    headers = _mutation_headers()
    del headers["X-FrameNest-Request"]
    response = client.post(
        "/api/canonical-tags",
        headers=headers,
        json={"key": "zeta", "display_name": "Zeta"},
    )
    assert response.status_code == 403
    assert _error_code(response) == "MUTATION_HEADER_REQUIRED"


def test_cross_origin_form_style_mutation_is_rejected(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers={
            **_serve_headers(),
            "Origin": "https://evil.example",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        content=b"key=eta&display_name=Eta",
    )
    assert response.status_code == 403
    same_origin_form = client.post(
        "/api/canonical-tags",
        headers={
            **_serve_headers(),
            "Origin": EXTERNAL_ORIGIN,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        content=b"key=eta&display_name=Eta",
    )
    assert same_origin_form.status_code == 403
    assert _error_code(same_origin_form) == "MUTATION_HEADER_REQUIRED"


def test_responses_carry_no_cors_headers(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.get(
        "/api/media",
        headers={**_serve_headers(), "Origin": "https://evil.example"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_hostile_preflight_is_not_authorized(tailscale_client) -> None:
    client, _ = tailscale_client
    response = client.options(
        "/api/media",
        headers={
            **_serve_headers(),
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in (400, 401, 403, 405)
    assert "access-control-allow-origin" not in response.headers


def test_legitimate_upload_content_types_remain_functional(tailscale_client) -> None:
    client, _ = tailscale_client
    missing = str(uuid.uuid4())
    response = client.patch(
        f"/api/uploads/{missing}",
        headers={
            **_mutation_headers(),
            "Content-Type": "application/offset+octet-stream",
            "Upload-Offset": "0",
        },
        content=b"chunk",
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UPLOAD_CAPABILITY_NOT_CONFIGURED"
    delete = client.delete(f"/api/uploads/{missing}", headers=_mutation_headers())
    assert delete.status_code == 503
    assert delete.json()["error"]["code"] == "UPLOAD_CAPABILITY_NOT_CONFIGURED"


# --- Audit ---------------------------------------------------------------


def test_privileged_success_is_recorded_exactly(tailscale_client) -> None:
    client, settings = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(),
        json={"key": "theta", "display_name": "Theta"},
    )
    assert response.status_code == 201
    request_id = response.headers["x-request-id"]
    uuid.UUID(request_id)
    rows = _audit_rows(settings.database_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["request_id"] == request_id
    assert row["actor_login"] == ADMIN_LOGIN
    assert row["actor_key"] == ADMIN_LOGIN
    assert row["identity_provenance"] == "tailscale-serve"
    assert row["role"] == "admin"
    assert row["capability"] == "metadata.canonical.write"
    assert row["action"] == "canonical_tag.create"
    assert row["target_type"] == "canonical_tag"
    assert row["target_id"] is None
    assert row["outcome"] == "allowed"
    assert row["http_status"] == 201


def test_ordinary_user_denial_is_recorded(tailscale_client) -> None:
    client, settings = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(USER_LOGIN),
        json={"key": "iota", "display_name": "Iota"},
    )
    assert response.status_code == 403
    rows = _audit_rows(settings.database_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["request_id"] == response.headers["x-request-id"]
    assert row["actor_login"] == USER_LOGIN
    assert row["role"] == "user"
    assert row["capability"] == "metadata.canonical.write"
    assert row["action"] == "canonical_tag.create"
    assert row["outcome"] == "denied"
    assert row["http_status"] == 403


def test_unmapped_privileged_denial_is_recorded_once(tailscale_client) -> None:
    client, settings = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(STRANGER_LOGIN),
        json={"key": "kappa", "display_name": "Kappa"},
    )
    assert response.status_code == 403
    rows = _audit_rows(settings.database_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["actor_login"] == STRANGER_LOGIN
    assert row["role"] == "unmapped"
    assert row["outcome"] == "denied"
    assert row["http_status"] == 403


def test_audit_records_no_credentials_or_raw_headers(tailscale_client) -> None:
    client, settings = tailscale_client
    response = client.post(
        "/api/canonical-tags",
        headers={
            **_mutation_headers(),
            "Cookie": "session=SECRET-COOKIE-MARKER",
            "Authorization": "Bearer SECRET-TOKEN-MARKER",
        },
        json={"key": "lambda", "display_name": "Lambda"},
    )
    assert response.status_code == 201
    rows = _audit_rows(settings.database_path)
    assert len(rows) == 1
    recorded = " ".join(str(value) for value in tuple(rows[0]))
    assert "SECRET-COOKIE-MARKER" not in recorded
    assert "SECRET-TOKEN-MARKER" not in recorded


def test_audit_failure_blocks_the_privileged_action(tailscale_client) -> None:
    client, settings = tailscale_client
    connection = sqlite3.connect(settings.database_path)
    try:
        connection.execute("DROP TABLE security_audit_events")
        connection.commit()
    finally:
        connection.close()
    response = client.post(
        "/api/canonical-tags",
        headers=_mutation_headers(),
        json={"key": "mu", "display_name": "Mu"},
    )
    assert response.status_code == 500
    assert _error_code(response) == "AUDIT_UNAVAILABLE"
    assert response.headers["x-request-id"]
    tags = client.get("/api/canonical-tags", headers=_serve_headers())
    assert all(tag["key"] != "mu" for tag in tags.json()["tags"])


def test_correlation_id_is_present_on_remote_responses(tailscale_client) -> None:
    client, _ = tailscale_client
    ok = client.get("/api/media", headers=_serve_headers())
    uuid.UUID(ok.headers["x-request-id"])
    denied = client.get("/api/media", headers=_serve_headers(STRANGER_LOGIN))
    uuid.UUID(denied.headers["x-request-id"])
