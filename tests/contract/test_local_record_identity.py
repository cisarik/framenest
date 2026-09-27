"""Configured local owner is loopback-only and never manufactures an admin."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


def _settings(tmp_path: Path, login: str, role: str) -> FrameNestSettings:
    settings = FrameNestSettings(
        host="127.0.0.1",
        port=8000,
        database_path=tmp_path / "catalog.sqlite3",
        identity_map={login: role},
        local_owner_login=login,
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    return settings


def test_loopback_mutation_without_origin_is_forbidden(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path, "alice", "user"))
    client = TestClient(app, client=("127.0.0.1", 50000))
    response = client.post(
        "/api/uploads",
        json={"display_filename": "clip.gif", "declared_size_bytes": 8},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MUTATION_ORIGIN_FORBIDDEN"


def test_non_loopback_client_does_not_receive_local_owner(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path, "alice", "user"))
    client = TestClient(app, client=("192.0.2.10", 50000))
    response = client.get("/api/media")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_unmapped_local_owner_is_rejected() -> None:
    from pydantic import ValidationError

    try:
        FrameNestSettings(
            identity_map={"alice": "user"},
            local_owner_login="intruder",
            _env_file=None,
        )
    except ValidationError as exc:
        assert "local owner" in str(exc).lower()
    else:
        raise AssertionError("unmapped local owner was accepted")
