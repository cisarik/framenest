"""Integration proof for the manual metadata workspace API workflow."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings
from framenest.domain import Device, DeviceId, Library, LibraryId, LibraryPathFlavor, LibraryRoot
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


def _native_flavor() -> LibraryPathFlavor:
    if os.name == "nt":
        return LibraryPathFlavor.WINDOWS
    return LibraryPathFlavor.POSIX


def _snapshot_files(root: Path) -> dict[str, tuple[int, int, bytes]]:
    snapshot: dict[str, tuple[int, int, bytes]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            snapshot[path.relative_to(root).as_posix()] = (
                stat.st_size,
                stat.st_mtime_ns,
                path.read_bytes(),
            )
    return snapshot


def _register_library(database_path: Path, library_root: Path) -> LibraryId:
    engine = create_sqlite_engine(database_path)
    library_id = LibraryId.new()
    try:
        device = Device(id=DeviceId.new(), display_name="Workspace Test Device")
        SqliteDeviceRepository(engine).add(device)
        library = Library(
            id=library_id,
            device_id=device.id,
            display_name="Workspace Test Library",
            root=LibraryRoot(flavor=_native_flavor(), path=os.path.normpath(str(library_root))),
        )
        SqliteLibraryRepository(engine).add(library)
        return library_id
    finally:
        dispose_engine(engine)


def test_local_web_manual_metadata_workspace_api_roundtrip_and_file_safety(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    library_root = tmp_path / "registered-library"
    library_root.mkdir()
    (library_root / "entropy.mp4").write_bytes(b"synthetic-mp4-bytes")
    before = _snapshot_files(library_root)

    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    library_id = _register_library(database_path, library_root)

    with TestClient(create_app(settings=settings)) as client:
        imported = client.post(
            f"/api/libraries/{library_id}/media-imports",
            json={"relative_path": "entropy.mp4"},
        )
        assert imported.status_code == 200
        media_id = imported.json()["media"]["id"]

        sparse = client.get(f"/api/media/{media_id}/metadata")
        math = client.post("/api/canonical-tags", json={"key": "mathematics", "display_name": "Math"})
        compression = client.post(
            "/api/canonical-tags",
            json={"key": "compression", "display_name": "Compression"},
        )
        created = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": "Reinventing Entropy", "description": None, "tag_keys": ["mathematics", "compression"]},
        )
        read_back = client.get(f"/api/media/{media_id}/metadata")
        catalog = client.get("/api/media", params={"q": "entropy"})
        updated = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": "Entropy Revisited", "description": None, "tag_keys": ["compression", "mathematics"]},
        )
        updated_catalog = client.get("/api/media", params=[("tag", "compression"), ("tag", "mathematics")])
        cleared = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": None, "description": None, "tag_keys": []},
        )
        unchanged = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": None, "description": None, "tag_keys": []},
        )
        cleared_catalog = client.get("/api/media")

    assert sparse.status_code == 200
    assert sparse.json()["persisted"] is False
    assert sparse.json()["display_title"] is None
    assert sparse.json()["tags"] == []
    assert math.status_code == 201
    assert compression.status_code == 201

    assert created.status_code == 200
    assert created.json()["status"] == "created"
    assert read_back.json()["display_title"] == "Reinventing Entropy"
    assert read_back.json()["tags"] == [
        {"key": "mathematics", "display_name": "Math"},
        {"key": "compression", "display_name": "Compression"},
    ]
    assert catalog.status_code == 200
    assert catalog.json()["items"][0]["display_title"] == "Reinventing Entropy"
    assert catalog.json()["items"][0]["tags"] == [
        {"key": "mathematics", "display_name": "Math", "position": 0},
        {"key": "compression", "display_name": "Compression", "position": 1},
    ]

    assert updated.status_code == 200
    assert updated.json()["status"] == "updated"
    assert updated.json()["metadata"]["tags"] == [
        {"key": "compression", "display_name": "Compression"},
        {"key": "mathematics", "display_name": "Math"},
    ]
    assert updated_catalog.status_code == 200
    assert updated_catalog.json()["items"][0]["display_title"] == "Entropy Revisited"
    assert updated_catalog.json()["items"][0]["tags"] == [
        {"key": "compression", "display_name": "Compression", "position": 0},
        {"key": "mathematics", "display_name": "Math", "position": 1},
    ]

    assert cleared.status_code == 200
    assert cleared.json()["status"] == "updated"
    assert cleared.json()["metadata"]["display_title"] is None
    assert cleared.json()["metadata"]["tags"] == []
    assert unchanged.status_code == 200
    assert unchanged.json()["status"] == "unchanged"
    assert cleared_catalog.status_code == 200
    assert cleared_catalog.json()["items"][0]["display_title"] is None
    assert cleared_catalog.json()["items"][0]["tags"] == []

    for response in (
        imported,
        sparse,
        created,
        read_back,
        catalog,
        updated,
        updated_catalog,
        cleared,
        unchanged,
        cleared_catalog,
    ):
        assert str(library_root) not in response.text
        assert str(database_path) not in response.text

    assert _snapshot_files(library_root) == before
