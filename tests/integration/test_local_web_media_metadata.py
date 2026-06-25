"""Integration proof for same-origin persistent media metadata API."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings
from framenest.domain import MediaId
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


def _insert_media(database_path: Path) -> MediaId:
    media_id = MediaId.from_string("12345678-1234-4234-9234-123456789abc")
    engine = create_sqlite_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
                    "VALUES (:id, 'video', 10, 10)"
                ),
                {"id": media_id.to_string()},
            )
    finally:
        dispose_engine(engine)
    return media_id


def test_local_web_persists_display_title_and_canonical_tags(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    media_id = _insert_media(database_path)

    with TestClient(create_app(settings=settings)) as client:
        math = client.post("/api/canonical-tags", json={"key": "mathematics", "display_name": "Math"})
        compression = client.post(
            "/api/canonical-tags",
            json={"key": "compression", "display_name": "Compression"},
        )
        unsaved = client.get(f"/api/media/{media_id}/metadata")
        created = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": "Reinventing Entropy", "tag_keys": ["mathematics", "compression"]},
        )
        unchanged = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": "Reinventing Entropy", "tag_keys": ["mathematics", "compression"]},
        )
        cleared = client.put(
            f"/api/media/{media_id}/metadata",
            json={"display_title": None, "tag_keys": []},
        )

    assert math.status_code == 201
    assert compression.status_code == 201
    assert unsaved.json()["persisted"] is False
    assert created.json()["status"] == "created"
    assert created.json()["metadata"]["display_title"] == "Reinventing Entropy"
    assert created.json()["metadata"]["tags"] == [
        {"key": "mathematics", "display_name": "Math"},
        {"key": "compression", "display_name": "Compression"},
    ]
    assert unchanged.json()["status"] == "unchanged"
    assert unchanged.json()["metadata"]["updated_at_ms"] == created.json()["metadata"]["updated_at_ms"]
    assert cleared.json()["status"] == "updated"
    assert cleared.json()["metadata"]["display_title"] is None
    assert cleared.json()["metadata"]["tags"] == []

    engine = create_sqlite_engine(database_path)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM canonical_tags")).scalar_one() == 2
            assert connection.execute(text("SELECT COUNT(*) FROM media_metadata")).scalar_one() == 1
            assert connection.execute(text("SELECT COUNT(*) FROM media_canonical_tags")).scalar_one() == 0
            assert connection.execute(text("SELECT COUNT(*) FROM physical_media_locations")).scalar_one() == 0
    finally:
        dispose_engine(engine)
