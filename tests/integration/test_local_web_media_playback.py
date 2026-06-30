"""Integration proof for the identity-only local media playback endpoint."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings
from framenest.domain import Device, DeviceId, Library, LibraryId, LibraryPathFlavor, LibraryRoot
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x01" * 100
GIF_BYTES = b"GIF89a" + b"\x02" * 50


def _native_flavor() -> LibraryPathFlavor:
    if os.name == "nt":
        return LibraryPathFlavor.WINDOWS
    return LibraryPathFlavor.POSIX


def _register_library(database_path: Path, library_root: Path) -> LibraryId:
    engine = create_sqlite_engine(database_path)
    library_id = LibraryId.new()
    try:
        device = Device(id=DeviceId.new(), display_name="Playback Test Device")
        SqliteDeviceRepository(engine).add(device)
        library = Library(
            id=library_id,
            device_id=device.id,
            display_name="Playback Test Library",
            root=LibraryRoot(flavor=_native_flavor(), path=os.path.normpath(str(library_root))),
        )
        SqliteLibraryRepository(engine).add(library)
        return library_id
    finally:
        dispose_engine(engine)


def test_local_web_playback_endpoint_returns_gif_and_mp4_content_identity_only(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "playback.sqlite3"
    library_root = tmp_path / "registered-library"
    library_root.mkdir()
    (library_root / "entropy.mp4").write_bytes(MP4_BYTES)
    (library_root / "reaction.gif").write_bytes(GIF_BYTES)
    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    library_id = _register_library(database_path, library_root)

    with TestClient(create_app(settings=settings)) as client:
        imported_entropy = client.post(
            f"/api/libraries/{library_id}/media-imports",
            json={"relative_path": "entropy.mp4"},
        )
        imported_reaction = client.post(
            f"/api/libraries/{library_id}/media-imports",
            json={"relative_path": "reaction.gif"},
        )
        assert imported_entropy.status_code == 200
        assert imported_reaction.status_code == 200
        entropy_media_id = imported_entropy.json()["media"]["id"]
        reaction_media_id = imported_reaction.json()["media"]["id"]

        catalog = client.get("/api/media")
        assert catalog.status_code == 200
        catalog_payload = catalog.json()
        entropy_item = next(item for item in catalog_payload["items"] if item["media_id"] == entropy_media_id)
        reaction_item = next(item for item in catalog_payload["items"] if item["media_id"] == reaction_media_id)
        entropy_location = entropy_item["locations"][0]
        reaction_location = reaction_item["locations"][0]
        assert entropy_location["availability"] == "available"
        assert reaction_location["availability"] == "available"
        assert "location_id" in entropy_location
        assert "location_id" in reaction_location

        entropy_url = f"/api/media/{entropy_media_id}/locations/{entropy_location['location_id']}/content"
        reaction_url = f"/api/media/{reaction_media_id}/locations/{reaction_location['location_id']}/content"
        entropy_response = client.get(entropy_url)
        reaction_response = client.get(reaction_url)

        assert entropy_response.status_code == 200
        assert entropy_response.content == MP4_BYTES
        assert entropy_response.headers["content-type"] == "video/mp4"
        assert reaction_response.status_code == 200
        assert reaction_response.content == GIF_BYTES
        assert reaction_response.headers["content-type"] == "image/gif"

        assert str(library_root) not in entropy_response.text
        assert str(library_root) not in reaction_response.text
        assert "relative_path" not in entropy_url


def test_local_web_playback_rejects_offline_location(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "playback-offline.sqlite3"
    library_root = tmp_path / "registered-library"
    library_root.mkdir()
    (library_root / "offline.mp4").write_bytes(MP4_BYTES)
    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    library_id = _register_library(database_path, library_root)

    with TestClient(create_app(settings=settings)) as client:
        imported = client.post(
            f"/api/libraries/{library_id}/media-imports",
            json={"relative_path": "offline.mp4"},
        )
        assert imported.status_code == 200
        media_id = imported.json()["media"]["id"]

        engine = create_sqlite_engine(database_path)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("UPDATE physical_media_locations SET availability = 'offline' WHERE media_id = :media_id"),
                    {"media_id": media_id},
                )
        finally:
            dispose_engine(engine)

        catalog = client.get("/api/media")
        assert catalog.status_code == 200
        item = next(i for i in catalog.json()["items"] if i["media_id"] == media_id)
        location = item["locations"][0]
        assert location["availability"] == "offline"

        response = client.get(f"/api/media/{media_id}/locations/{location['location_id']}/content")
        assert response.status_code == 409
