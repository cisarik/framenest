"""Contract tests for resumable quarantine upload API."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.adapters.api.upload_api import _parse_content_length, _parse_upload_offset
from framenest.configuration import FrameNestSettings
from framenest.domain import Device, DeviceId, Library, LibraryId, LibraryPathFlavor, LibraryRoot
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


def _settings(tmp_path: Path, *, quarantine: bool = True, reserve: int = 0) -> FrameNestSettings:
    quarantine_root = tmp_path / "quarantine"
    if quarantine:
        quarantine_root.mkdir(parents=True, exist_ok=True)
    return FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        upload_quarantine_root=quarantine_root if quarantine else None,
        upload_max_total_bytes=16,
        upload_max_patch_bytes=8,
        upload_session_ttl_seconds=60,
        upload_min_free_space_reserve_bytes=reserve,
        _env_file=None,
    )


def _migrated_client(settings: FrameNestSettings) -> TestClient:
    upgrade_database_to_head(settings)
    return TestClient(create_app(settings=settings))


def _create(client: TestClient, *, size: int = 5, origin: str | None = None):
    headers = {} if origin is None else {"origin": origin}
    return client.post(
        "/api/uploads",
        json={"display_filename": "example.gif", "declared_size_bytes": size},
        headers=headers,
    )


def _patch(client: TestClient, upload_id: str, offset: int, payload: bytes):
    return client.patch(
        f"/api/uploads/{upload_id}",
        content=payload,
        headers={
            "content-type": "application/offset+octet-stream",
            "upload-offset": str(offset),
        },
    )


def _patch_with_content_length(
    client: TestClient,
    upload_id: str,
    *,
    content_length: str,
    payload: bytes = b"a",
):
    return client.patch(
        f"/api/uploads/{upload_id}",
        content=payload,
        headers={
            "content-type": "application/offset+octet-stream",
            "upload-offset": "0",
            "content-length": content_length,
        },
    )


async def _asgi_patch(
    app: Any,
    upload_id: str,
    headers: list[tuple[bytes, bytes]],
    body: bytes = b"a",
) -> tuple[int, dict[str, object]]:
    messages: list[dict[str, object]] = []
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    path = f"/api/uploads/{upload_id}"
    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "PATCH",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )
    status = next(
        int(message["status"])
        for message in messages
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, json.loads(response_body)


def _raw_patch(
    app: Any,
    upload_id: str,
    headers: list[tuple[bytes, bytes]],
    body: bytes = b"a",
) -> tuple[int, dict[str, object]]:
    return asyncio.run(_asgi_patch(app, upload_id, headers, body))


def _raw_patch_headers(
    *,
    content_type_headers: list[tuple[bytes, bytes]],
    content_length_headers: list[tuple[bytes, bytes]] | None = None,
    upload_offset_headers: list[tuple[bytes, bytes]] | None = None,
) -> list[tuple[bytes, bytes]]:
    return (
        [(b"host", b"testserver")]
        + content_type_headers
        + (content_length_headers or [(b"content-length", b"1")])
        + (upload_offset_headers or [(b"upload-offset", b"0")])
    )


def _raw_request(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "PATCH",
            "path": "/api/uploads/example",
            "headers": headers,
        },
        receive=lambda: None,
    )


def _part_file(settings: FrameNestSettings) -> Path:
    files = list(settings.upload_quarantine_root.glob("*.part"))  # type: ignore[union-attr]
    assert len(files) == 1
    return files[0]


def test_unconfigured_upload_capability_fails_closed(tmp_path: Path) -> None:
    settings = _settings(tmp_path, quarantine=False)
    client = _migrated_client(settings)

    response = _create(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UPLOAD_CAPABILITY_NOT_CONFIGURED"
    assert str(tmp_path) not in response.text


def test_create_and_status_return_sanitized_snapshot_without_storage_details(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)

    response = _create(client)
    payload = response.json()
    status = client.get(f"/api/uploads/{payload['id']}")

    assert response.status_code == 201
    assert status.status_code == 200
    assert payload["state"] == "created"
    assert payload["received_size_bytes"] == 0
    assert "storage_key" not in payload
    assert ".part" not in response.text + status.text
    assert str(settings.upload_quarantine_root) not in response.text + status.text


def test_create_rejects_invalid_metadata_size_limit_free_space_and_cross_origin(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)

    invalid_name = client.post(
        "/api/uploads",
        json={"display_filename": "../../example.gif", "declared_size_bytes": 1},
    )
    too_large = _create(client, size=17)
    cross_origin = _create(client, origin="http://evil.example")

    reserve_settings = _settings(tmp_path / "reserve", reserve=10**18)
    reserve_client = _migrated_client(reserve_settings)
    no_space = _create(reserve_client, size=1)

    assert invalid_name.status_code in {400, 422}
    assert too_large.status_code == 413
    assert cross_origin.status_code == 403
    assert no_space.status_code == 507
    assert str(tmp_path) not in invalid_name.text + too_large.text + no_space.text


def test_patch_multiple_chunks_resume_after_app_reconstruction_and_complete(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)
    created = _create(client).json()

    first = _patch(client, created["id"], 0, b"ab")
    assert first.status_code == 200
    assert first.json()["state"] == "receiving"
    assert first.json()["received_size_bytes"] == 2

    resumed_client = TestClient(create_app(settings=settings))
    status = resumed_client.get(f"/api/uploads/{created['id']}")
    second = _patch(resumed_client, created["id"], status.json()["received_size_bytes"], b"cde")
    complete = resumed_client.post(f"/api/uploads/{created['id']}/complete")

    assert status.json()["received_size_bytes"] == 2
    assert second.status_code == 200
    assert second.json()["received_size_bytes"] == 5
    assert complete.status_code == 200
    assert complete.json()["state"] == "received"
    assert _part_file(settings).read_bytes() == b"abcde"
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM logical_media").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM media_metadata").fetchone() == (0,)


def test_patch_rejects_header_errors_size_limits_wrong_state_and_offset_conflict(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)
    upload_id = _create(client).json()["id"]

    wrong_content_type = client.patch(
        f"/api/uploads/{upload_id}",
        content=b"a",
        headers={"content-type": "application/octet-stream", "upload-offset": "0"},
    )
    missing_offset = client.patch(
        f"/api/uploads/{upload_id}",
        content=b"a",
        headers={"content-type": "application/offset+octet-stream"},
    )
    chunk_too_large = _patch(client, upload_id, 0, b"abcdefghi")
    first = _patch(client, upload_id, 0, b"ab")
    conflict = _patch(client, upload_id, 0, b"c")

    assert wrong_content_type.status_code == 400
    assert missing_offset.status_code == 400
    assert chunk_too_large.status_code == 413
    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["error"]["current_offset"] == 2


def test_patch_content_length_accepts_ascii_digits_and_leading_zero(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)

    plain_upload_id = _create(client, size=1).json()["id"]
    plain = _patch_with_content_length(client, plain_upload_id, content_length="1")
    leading_zero_upload_id = _create(client, size=1).json()["id"]
    leading_zero = _patch_with_content_length(
        client,
        leading_zero_upload_id,
        content_length="01",
    )

    assert plain.status_code == 200
    assert plain.json()["received_size_bytes"] == 1
    assert leading_zero.status_code == 200
    assert leading_zero.json()["received_size_bytes"] == 1


def test_patch_content_length_rejects_signed_whitespace_mixed_and_zero_values(
    tmp_path: Path,
) -> None:
    for value in ("+1", "-1", " 1", "1 ", "1x", "0", ""):
        settings = _settings(tmp_path / value.encode("utf-8").hex())
        client = _migrated_client(settings)
        upload_id = _create(client, size=1).json()["id"]

        response = _patch_with_content_length(client, upload_id, content_length=value)

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_UPLOAD_CONTENT_LENGTH"


def test_patch_content_length_rejects_non_ascii_decimal_text() -> None:
    request = _raw_request([(b"content-length", "١".encode("utf-8"))])

    response = _parse_content_length(request)

    assert not isinstance(response, int)
    assert response.status_code == 400


def test_patch_raw_content_type_single_valid_header_is_accepted_and_advances_offset(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    upgrade_database_to_head(settings)
    app = create_app(settings=settings)
    upload_id = _create(TestClient(app), size=2).json()["id"]

    status, payload = _raw_patch(
        app,
        upload_id,
        _raw_patch_headers(
            content_type_headers=[(b"content-type", b"application/offset+octet-stream")]
        ),
    )

    assert status == 200
    assert payload["received_size_bytes"] == 1
    assert _part_file(settings).read_bytes() == b"a"


def test_patch_raw_content_type_rejects_ambiguous_or_invalid_values(
    tmp_path: Path,
) -> None:
    cases = (
        [
            (b"content-type", b"application/offset+octet-stream"),
            (b"content-type", b"application/offset+octet-stream"),
        ],
        [
            (b"content-type", b"application/offset+octet-stream"),
            (b"content-type", b"application/octet-stream"),
        ],
        [
            (b"content-type", b"application/octet-stream"),
            (b"content-type", b"application/offset+octet-stream"),
        ],
        [
            (b"Content-Type", b"application/offset+octet-stream"),
            (b"content-type", b"application/offset+octet-stream"),
        ],
        [(b"content-type", b"application/offset+octet-stream, application/octet-stream")],
        [
            (
                b"content-type",
                b"application/offset+octet-stream,application/offset+octet-stream",
            )
        ],
        [],
        [(b"content-type", b"application/octet-stream")],
        [(b"content-type", b"")],
        [(b"content-type", b"application/offset+octet-stream\xff")],
    )

    for index, content_type_headers in enumerate(cases):
        settings = _settings(tmp_path / str(index))
        upgrade_database_to_head(settings)
        app = create_app(settings=settings)
        upload_id = _create(TestClient(app), size=1).json()["id"]

        status, payload = _raw_patch(
            app,
            upload_id,
            _raw_patch_headers(content_type_headers=content_type_headers),
        )

        assert status == 400
        assert payload == {
            "error": {
                "code": "INVALID_UPLOAD_CONTENT_TYPE",
                "message": "Invalid upload content type.",
            }
        }


def test_patch_raw_content_length_and_upload_offset_singleton_contract_remains(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    upgrade_database_to_head(settings)
    app = create_app(settings=settings)
    client = TestClient(app)

    duplicate_content_length_id = _create(client, size=1).json()["id"]
    duplicate_content_length = _raw_patch(
        app,
        duplicate_content_length_id,
        _raw_patch_headers(
            content_type_headers=[(b"content-type", b"application/offset+octet-stream")],
            content_length_headers=[
                (b"content-length", b"1"),
                (b"content-length", b"1"),
            ],
        ),
    )
    duplicate_upload_offset_id = _create(client, size=1).json()["id"]
    duplicate_upload_offset = _raw_patch(
        app,
        duplicate_upload_offset_id,
        _raw_patch_headers(
            content_type_headers=[(b"content-type", b"application/offset+octet-stream")],
            upload_offset_headers=[
                (b"upload-offset", b"0"),
                (b"upload-offset", b"0"),
            ],
        ),
    )

    assert duplicate_content_length[0] == 400
    assert duplicate_content_length[1]["error"]["code"] == "INVALID_UPLOAD_CONTENT_LENGTH"
    assert duplicate_upload_offset[0] == 400
    assert duplicate_upload_offset[1]["error"]["code"] == "INVALID_UPLOAD_OFFSET"


def test_patch_content_length_raw_singleton_accepts_digits_and_leading_zero() -> None:
    plain = _parse_content_length(_raw_request([(b"Content-Length", b"1")]))
    leading_zero = _parse_content_length(_raw_request([(b"content-length", b"001")]))

    assert plain == 1
    assert leading_zero == 1


def test_patch_content_length_raw_duplicates_and_combined_values_are_rejected() -> None:
    cases = (
        [(b"content-length", b"1"), (b"content-length", b"+1")],
        [(b"content-length", b"+1"), (b"content-length", b"1")],
        [(b"Content-Length", b"1"), (b"content-length", b"1")],
        [(b"content-length", b"1,1")],
        [(b"content-length", b"1, 1")],
        [(b"content-length", b"1,+1")],
    )

    for headers in cases:
        response = _parse_content_length(_raw_request(headers))

        assert not isinstance(response, int)
        assert response.status_code == 400
        assert response.body == (
            b'{"error":{"code":"INVALID_UPLOAD_CONTENT_LENGTH",'
            b'"message":"Missing or invalid upload content length."}}'
        )


def test_patch_content_length_raw_rejects_signed_whitespace_mixed_zero_and_missing() -> None:
    cases = (
        [(b"content-length", b"+1")],
        [(b"content-length", b"-1")],
        [(b"content-length", b" 1")],
        [(b"content-length", b"1 ")],
        [(b"content-length", b"1x")],
        [(b"content-length", "١".encode("utf-8"))],
        [(b"content-length", b"0")],
        [],
    )

    for headers in cases:
        response = _parse_content_length(_raw_request(headers))

        assert not isinstance(response, int)
        assert response.status_code == 400


def test_patch_upload_offset_raw_duplicates_are_rejected() -> None:
    valid = _parse_upload_offset(_raw_request([(b"Upload-Offset", b"0")]))
    duplicate_same = _parse_upload_offset(
        _raw_request([(b"upload-offset", b"0"), (b"upload-offset", b"0")])
    )
    duplicate_mixed = _parse_upload_offset(
        _raw_request([(b"upload-offset", b"0"), (b"upload-offset", b"1")])
    )
    duplicate_malformed = _parse_upload_offset(
        _raw_request([(b"upload-offset", b"0"), (b"upload-offset", b"+0")])
    )

    assert valid == 0
    for response in (duplicate_same, duplicate_mixed, duplicate_malformed):
        assert not isinstance(response, int)
        assert response.status_code == 400


def test_file_ahead_is_truncated_and_file_behind_fails_closed(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)
    upload_id = _create(client).json()["id"]
    assert _patch(client, upload_id, 0, b"ab").status_code == 200
    part = _part_file(settings)
    part.write_bytes(b"abCRASH")

    resumed = _patch(client, upload_id, 2, b"c")
    assert resumed.status_code == 200
    assert part.read_bytes() == b"abc"

    part.write_bytes(b"a")
    failed = client.post(f"/api/uploads/{upload_id}/complete")
    status = client.get(f"/api/uploads/{upload_id}")
    assert failed.status_code == 409
    assert failed.json()["error"]["code"] == "QUARANTINE_STATE_INCONSISTENT"
    assert status.json()["state"] == "failed"


def test_cancel_persists_cancelled_removes_file_and_is_idempotent(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    client = _migrated_client(settings)
    upload_id = _create(client).json()["id"]
    assert _patch(client, upload_id, 0, b"abcde").status_code == 200

    cancelled = client.delete(f"/api/uploads/{upload_id}")
    repeated = client.delete(f"/api/uploads/{upload_id}")
    later_write = _patch(client, upload_id, 5, b"x")

    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert repeated.status_code == 200
    assert later_write.status_code == 409
    assert list(settings.upload_quarantine_root.glob("*.part")) == []  # type: ignore[union-attr]


def test_quarantine_root_overlapping_registered_library_rejects_create(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    upgrade_database_to_head(settings)
    library_root = settings.upload_quarantine_root.parent  # type: ignore[union-attr]
    engine = create_sqlite_engine(settings.database_path)
    try:
        device = Device(id=DeviceId.new(), display_name="Device")
        SqliteDeviceRepository(engine).add(device)
        SqliteLibraryRepository(engine).add(
            Library(
                id=LibraryId.new(),
                device_id=device.id,
                display_name="Library",
                root=LibraryRoot(flavor=LibraryPathFlavor.POSIX, path=str(library_root)),
            )
        )
    finally:
        dispose_engine(engine)
    client = TestClient(create_app(settings=settings))

    response = _create(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UPLOAD_CAPABILITY_NOT_CONFIGURED"
    assert str(library_root) not in response.text
