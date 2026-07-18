"""Public, composition, privacy, and negative-scope publication contracts."""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import insert

from framenest.adapters.api.application import create_app
from framenest.adapters.api.upload_api import (
    UploadApiDependencies,
    UploadCapabilityResponse,
    UploadDuplicateResolutionResponse,
    UploadSessionResponse,
    create_upload_api_router,
)
from framenest.application.upload_transport import UploadSessionSnapshot
from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.catalog_schema import devices, libraries
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

DESTINATION_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


class _PublicationCoordinator:
    def __init__(self) -> None:
        self.notifications = 0

    def notify(self) -> None:
        self.notifications += 1


class _DuplicateTransport:
    async def resolve_duplicate(self, *_args):
        return UploadSessionSnapshot(
            id="11111111-1111-4111-8111-111111111111",
            state="publish_pending",
            display_filename="private-client-name.mp4",
            declared_size_bytes=8,
            received_size_bytes=8,
            expires_at=100,
            failure_code=None,
        )


def _configured_settings(tmp_path: Path, *, publication_id: str | None):
    database_path = tmp_path / "database" / "catalog.sqlite3"
    quarantine = tmp_path / "quarantine"
    published = tmp_path / "published"
    quarantine.mkdir(parents=True)
    published.mkdir(parents=True)
    settings = FrameNestSettings(
        database_path=database_path,
        gallery_preview_cache_path=tmp_path / "cache" / "previews",
        upload_quarantine_root=quarantine,
        upload_publication_library_id=publication_id,
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    if publication_id is not None:
        engine = create_sqlite_engine(database_path)
        try:
            with engine.begin() as connection:
                connection.execute(
                    insert(devices).values(
                        id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                        display_name="Synthetic device",
                    )
                )
                connection.execute(
                    insert(libraries).values(
                        id=publication_id,
                        device_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                        display_name="Published originals",
                        path_flavor="posix",
                        root_path=str(published),
                    )
                )
        finally:
            dispose_engine(engine)
    return settings, quarantine, published


def test_public_api_adds_no_publish_route_or_internal_publication_fields() -> None:
    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert not any("publish" in path for path in paths)
    forbidden = {
        "publication_id",
        "storage_key",
        "quarantine_key",
        "relative_target",
        "target_path",
        "library_root",
        "checksum_hex",
        "byte_identity_id",
        "duplicate_disposition",
        "cleanup_state",
    }
    for response_model in (
        UploadSessionResponse,
        UploadDuplicateResolutionResponse,
        UploadCapabilityResponse,
    ):
        assert forbidden.isdisjoint(response_model.model_fields)


def test_duplicate_keep_notifies_publication_only_after_publish_pending_response() -> None:
    coordinator = _PublicationCoordinator()
    app = FastAPI()
    app.include_router(
        create_upload_api_router(
            UploadApiDependencies(
                transport=_DuplicateTransport(),
                publication_coordinator=coordinator,
            )
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/uploads/11111111-1111-4111-8111-111111111111/duplicate-resolution",
        json={"resolution": "keep_separate"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "11111111-1111-4111-8111-111111111111",
        "state": "publish_pending",
        "declared_size_bytes": 8,
        "received_size_bytes": 8,
        "expires_at": 100,
        "failure_code": None,
    }
    assert coordinator.notifications == 1


def test_missing_publication_configuration_starts_no_publisher_and_mutates_no_target(
    tmp_path: Path,
) -> None:
    settings, _, published = _configured_settings(tmp_path, publication_id=None)

    app = create_app(settings=settings)

    assert app.state.upload_publication is None
    assert app.state.upload_publication_coordinator is None
    assert list(published.iterdir()) == []


def test_valid_opaque_library_configuration_composes_lifecycle_owned_publisher(
    tmp_path: Path,
) -> None:
    settings, _, published = _configured_settings(
        tmp_path,
        publication_id=DESTINATION_ID,
    )

    app = create_app(settings=settings)

    assert app.state.upload_publication is not None
    assert app.state.upload_publication_coordinator is not None
    assert list(published.iterdir()) == []
    assert DESTINATION_ID not in repr(settings)


def test_invalid_explicit_destination_fails_closed_with_sanitized_diagnostic(
    tmp_path: Path,
) -> None:
    settings, _, _ = _configured_settings(
        tmp_path,
        publication_id="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    )
    engine = create_sqlite_engine(settings.database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                libraries.delete().where(
                    libraries.c.id == "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
                )
            )
    finally:
        dispose_engine(engine)

    with pytest.raises(ValueError) as error:
        create_app(settings=settings)

    assert str(error.value) == "Upload publication configuration is invalid."
    assert str(settings.database_path) not in str(error.value)
    assert str(settings.upload_quarantine_root) not in str(error.value)


def test_overlapping_publication_and_quarantine_roots_fail_closed(tmp_path: Path) -> None:
    database_path = tmp_path / "database" / "catalog.sqlite3"
    shared_root = tmp_path / "shared"
    shared_root.mkdir(parents=True)
    settings = FrameNestSettings(
        database_path=database_path,
        gallery_preview_cache_path=tmp_path / "cache" / "previews",
        upload_quarantine_root=shared_root,
        upload_publication_library_id=DESTINATION_ID,
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                insert(devices).values(
                    id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                    display_name="Synthetic device",
                )
            )
            connection.execute(
                insert(libraries).values(
                    id=DESTINATION_ID,
                    device_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                    display_name="Unsafe overlap",
                    path_flavor="posix",
                    root_path=str(shared_root),
                )
            )
    finally:
        dispose_engine(engine)

    with pytest.raises(ValueError, match="configuration is invalid"):
        create_app(settings=settings)


def test_publication_modules_contain_no_catalog_creation_provider_or_public_route_code() -> None:
    root = Path(__file__).resolve().parents[2]
    paths = (
        root / "src/framenest/domain/upload_publications.py",
        root / "src/framenest/application/upload_publication.py",
        root / "src/framenest/application/upload_publication_coordinator.py",
        root / "src/framenest/infrastructure/filesystem/published_media_storage.py",
        root / "src/framenest/infrastructure/persistence/upload_publication_repository.py",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = (
        "logical_media",
        "physical_media_locations",
        "media_metadata",
        "provider",
        "openai",
        "httpx",
        "requests",
        "@router",
    )

    assert all(fragment not in combined.lower() for fragment in forbidden)
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
