"""API contract for capability-gated single-item content publication."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from framenest.adapters.api.content_publication_api import (
    ContentPublicationApiDependencies,
    create_content_publication_api_router,
)
from framenest.adapters.api.tailscale_ingress import (
    SCOPE_AUDIT_EVENT_ID,
    SCOPE_IDENTITY,
)
from framenest.application.ports.content_publication_repository import (
    AdminMediaItem,
    AdminMediaPage,
    ContentPublicationMediaNotFoundError,
    PublishContentResult,
)
from framenest.application.ports.media_catalog_repository import (
    CatalogMediaLocation,
    CatalogMediaTag,
)
from framenest.domain.content_publication import (
    ContentPublication,
    ContentPublicationOrigin,
    derive_content_publication_readiness,
)
from framenest.domain.identity_access import (
    CAPABILITIES_BY_ROLE,
    IdentityContext,
    ROLE_ADMIN,
    ROLE_USER,
)

MEDIA_ID = "11111111-1111-4111-8111-111111111111"
LOCATION_ID = "22222222-2222-4222-8222-222222222222"
LIBRARY_ID = "33333333-3333-4333-8333-333333333333"


def _identity(role: str) -> IdentityContext:
    return IdentityContext(
        login=f"{role}@example.com",
        login_key=f"{role}@example.com",
        display_name=role.title(),
        role=role,
        capabilities=CAPABILITIES_BY_ROLE[role],
        provenance="tailscale-serve",
    )


@dataclass
class _FakeList:
    calls: list[dict[str, object]]

    def execute(self, **kwargs: object) -> AdminMediaPage:
        self.calls.append(kwargs)
        readiness = derive_content_publication_readiness(
            display_title="Manual title",
            description="Manual description",
            canonical_tag_count=1,
        )
        return AdminMediaPage(
            items=(
                AdminMediaItem(
                    media_id=MEDIA_ID,
                    media_kind="video",
                    created_at_ms=10,
                    updated_at_ms=11,
                    display_title="Manual title",
                    description="Manual description",
                    collection_key=None,
                    processed_at_ms=None,
                    content_category="general",
                    acquisition_source="unknown",
                    tags=(
                        CatalogMediaTag(
                            key="manual",
                            display_name="Manual",
                            position=0,
                        ),
                    ),
                    locations=(
                        CatalogMediaLocation(
                            location_id=LOCATION_ID,
                            library_id=LIBRARY_ID,
                            relative_path="safe/item.mp4",
                            availability="available",
                            observed_size_bytes=10,
                            observed_mtime_ns=20,
                        ),
                    ),
                    publication=None,
                    readiness=readiness,
                    analysis_state="not_requested",
                ),
            ),
            total=1,
            limit=int(kwargs["limit"]),
            offset=int(kwargs["offset"]),
            q=kwargs["q"],  # type: ignore[arg-type]
            tag_keys=tuple(kwargs["tag_keys"]),  # type: ignore[arg-type]
            publication=kwargs["publication"],  # type: ignore[arg-type]
            readiness=kwargs["readiness"],  # type: ignore[arg-type]
            analysis=kwargs["analysis"],  # type: ignore[arg-type]
        )


@dataclass
class _FakePublish:
    result: PublishContentResult | Exception
    calls: list[str]

    def execute(self, media_id: str) -> PublishContentResult:
        self.calls.append(media_id)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _client(
    *,
    identity: IdentityContext | None,
    audit_proof: bool = False,
    publication_result: PublishContentResult | Exception | None = None,
) -> tuple[TestClient, _FakeList, _FakePublish]:
    readiness = derive_content_publication_readiness(
        display_title="Manual title",
        description="Manual description",
        canonical_tag_count=1,
    )
    result = publication_result or PublishContentResult(
        status="published",
        publication=ContentPublication(
            media_id=MEDIA_ID,
            published_at_ms=100,
            publication_origin=ContentPublicationOrigin.ADMIN_EXPLICIT,
        ),
        readiness=readiness,
    )
    list_service = _FakeList(calls=[])
    publish_service = _FakePublish(result=result, calls=[])
    app = FastAPI()

    @app.middleware("http")
    async def identity_scope(request: Request, call_next):
        if identity is not None:
            request.scope[SCOPE_IDENTITY] = identity
        if audit_proof:
            request.scope[SCOPE_AUDIT_EVENT_ID] = "audit-event"
        return await call_next(request)

    app.include_router(
        create_content_publication_api_router(
            ContentPublicationApiDependencies(
                list_admin_media=list_service,
                publish_content=publish_service,
                catalog_available=lambda: True,
            )
        )
    )
    return TestClient(app), list_service, publish_service


def test_admin_list_requires_verified_workflow_capability_and_defaults_unpublished() -> None:
    missing, _, _ = _client(identity=None)
    ordinary, _, _ = _client(identity=_identity(ROLE_USER))
    admin, service, _ = _client(identity=_identity(ROLE_ADMIN))

    assert missing.get("/api/admin/media").status_code == 401
    assert ordinary.get("/api/admin/media").status_code == 403
    response = admin.get("/api/admin/media")

    assert response.status_code == 200
    assert service.calls[0]["publication"] == "unpublished"
    assert response.json()["items"][0]["publication_ready"] is True
    assert response.json()["items"][0]["analysis_state"] == "not_requested"
    assert "relative_path" not in response.json()["items"][0]["locations"][0]
    assert response.json()["has_previous"] is False
    assert response.json()["has_next"] is False


def test_publication_requires_audit_before_mutation_and_is_idempotent() -> None:
    no_audit, _, blocked_service = _client(identity=_identity(ROLE_ADMIN))
    blocked = no_audit.put(
        f"/api/admin/media/{MEDIA_ID}/content-publication"
    )
    assert blocked.status_code == 500
    assert blocked.json()["error"]["code"] == "AUDIT_UNAVAILABLE"
    assert blocked_service.calls == []

    first, _, first_service = _client(
        identity=_identity(ROLE_ADMIN),
        audit_proof=True,
    )
    created = first.put(f"/api/admin/media/{MEDIA_ID}/content-publication")
    assert created.status_code == 201
    assert created.json()["status"] == "published"
    assert first_service.calls == [MEDIA_ID]

    repeated_result = PublishContentResult(
        status="already_published",
        publication=ContentPublication(
            media_id=MEDIA_ID,
            published_at_ms=100,
            publication_origin=ContentPublicationOrigin.ADMIN_EXPLICIT,
        ),
        readiness=derive_content_publication_readiness(
            display_title=None,
            description=None,
            canonical_tag_count=0,
        ),
    )
    repeated, _, _ = _client(
        identity=_identity(ROLE_ADMIN),
        audit_proof=True,
        publication_result=repeated_result,
    )
    repeat_response = repeated.put(
        f"/api/admin/media/{MEDIA_ID}/content-publication"
    )
    assert repeat_response.status_code == 200
    assert repeat_response.json()["status"] == "already_published"
    assert repeat_response.json()["publication_ready"] is False


def test_not_ready_unknown_and_failures_are_sanitized() -> None:
    not_ready_result = PublishContentResult(
        status="not_ready",
        publication=None,
        readiness=derive_content_publication_readiness(
            display_title=" ",
            description=None,
            canonical_tag_count=0,
        ),
    )
    not_ready, _, _ = _client(
        identity=_identity(ROLE_ADMIN),
        audit_proof=True,
        publication_result=not_ready_result,
    )
    conflict = not_ready.put(
        f"/api/admin/media/{MEDIA_ID}/content-publication"
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["missing_fields"] == [
        "display_title",
        "description",
        "tags",
    ]

    unknown, _, _ = _client(
        identity=_identity(ROLE_ADMIN),
        audit_proof=True,
        publication_result=ContentPublicationMediaNotFoundError("private"),
    )
    missing = unknown.put(
        f"/api/admin/media/{MEDIA_ID}/content-publication"
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "MEDIA_NOT_FOUND"
    assert "private" not in missing.text
