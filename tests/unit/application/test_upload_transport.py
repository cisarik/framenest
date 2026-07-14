"""Unit tests for resumable upload transport application behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from pathlib import Path

import pytest

from framenest.application.upload_transport import (
    UploadBodyLengthMismatchError,
    UploadCapabilityNotConfiguredError,
    UploadOffsetConflictTransportError,
    UploadQuarantineStateInconsistentError,
    UploadSessionExpiredError,
    UploadSessionStateConflictError,
    UploadTooLargeError,
    UploadTransportLimits,
    UploadTransportService,
)
from framenest.domain import Library, LibraryId, LibraryPathFlavor, LibraryRoot
from framenest.domain.identities import DeviceId
from framenest.domain.uploads import UploadSessionId, UploadSessionState
from framenest.infrastructure.filesystem.quarantine_storage import FilesystemQuarantineStorage
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.upload_session_repository import SqliteUploadSessionRepository
from framenest.configuration import FrameNestSettings


class _LibraryRepository:
    def __init__(self, libraries: tuple[Library, ...] = ()) -> None:
        self._libraries = libraries

    def add(self, library: Library) -> None:
        raise AssertionError("not used")

    def get(self, library_id: LibraryId) -> Library | None:
        return next((library for library in self._libraries if library.id == library_id), None)

    def list_all(self) -> tuple[Library, ...]:
        return self._libraries


async def _chunks(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


def _service(
    tmp_path: Path,
    *,
    now_ms: int = 1_000,
    libraries: tuple[Library, ...] = (),
) -> tuple[UploadTransportService, FilesystemQuarantineStorage, object]:
    database_path = tmp_path / "catalog.sqlite3"
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir(parents=True)
    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(database_path)
    service = UploadTransportService(
        SqliteUploadSessionRepository(engine),
        FilesystemQuarantineStorage(quarantine_root),
        _LibraryRepository(libraries),
        UploadTransportLimits(
            max_total_bytes=100,
            max_patch_bytes=10,
            session_ttl_seconds=60,
            min_free_space_reserve_bytes=0,
        ),
        quarantine_root=quarantine_root,
        preview_cache_root=tmp_path / "preview-cache",
        now_ms=lambda: now_ms,
    )
    return service, FilesystemQuarantineStorage(quarantine_root), engine


def test_create_generates_ids_fixed_ttl_and_no_storage_public_fields(tmp_path: Path) -> None:
    service, _, engine = _service(tmp_path, now_ms=10_000)
    try:
        snapshot = service.create_session(
            display_filename="example.gif",
            declared_size_bytes=5,
        )
    finally:
        dispose_engine(engine)

    assert UploadSessionId.from_string(snapshot.id)
    assert snapshot.state == "created"
    assert snapshot.display_filename == "example.gif"
    assert snapshot.received_size_bytes == 0
    assert snapshot.expires_at == 70_000
    assert not hasattr(snapshot, "storage_key")


def test_create_rejects_unconfigured_oversize_and_overlapping_library_root(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    try:
        service = UploadTransportService(
            SqliteUploadSessionRepository(engine),
            None,
            _LibraryRepository(),
            UploadTransportLimits(5, 5, 60, 0),
            quarantine_root=None,
        )
        with pytest.raises(UploadCapabilityNotConfiguredError):
            service.create_session(display_filename="a.gif", declared_size_bytes=1)
    finally:
        dispose_engine(engine)

    service, _, engine = _service(tmp_path / "oversize")
    try:
        with pytest.raises(UploadTooLargeError):
            service.create_session(display_filename="a.gif", declared_size_bytes=101)
    finally:
        dispose_engine(engine)

    overlap_root = tmp_path / "overlap"
    database_path = overlap_root / "catalog.sqlite3"
    quarantine = overlap_root / "library" / "quarantine"
    quarantine.mkdir(parents=True)
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    library = Library(
        id=LibraryId.new(),
        device_id=DeviceId.new(),
        display_name="Library",
        root=LibraryRoot(flavor=LibraryPathFlavor.POSIX, path=str(quarantine.parent)),
    )
    service = UploadTransportService(
        SqliteUploadSessionRepository(engine),
        FilesystemQuarantineStorage(quarantine),
        _LibraryRepository((library,)),
        UploadTransportLimits(100, 10, 60, 0),
        quarantine_root=quarantine,
    )
    try:
        with pytest.raises(UploadCapabilityNotConfiguredError):
            service.create_session(display_filename="a.gif", declared_size_bytes=1)
    finally:
        dispose_engine(engine)


def test_patch_multiple_chunks_resume_complete_and_cancel_boundaries(tmp_path: Path) -> None:
    service, _, engine = _service(tmp_path)
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        first = asyncio.run(service.receive_chunk(
            session_id,
            upload_offset=0,
            content_length=2,
            body=_chunks(b"ab"),
        ))
        assert first.state == "receiving"
        assert first.received_size_bytes == 2

        with pytest.raises(UploadOffsetConflictTransportError) as conflict:
            asyncio.run(service.receive_chunk(
                session_id,
                upload_offset=0,
                content_length=1,
                body=_chunks(b"a"),
            ))
        assert conflict.value.current_offset == 2

        second = asyncio.run(service.receive_chunk(
            session_id,
            upload_offset=2,
            content_length=3,
            body=_chunks(b"c", b"de"),
        ))
        assert second.received_size_bytes == 5
        completed = asyncio.run(service.complete(session_id))
        assert completed.state == "received"
        repeated = asyncio.run(service.complete(session_id))
        assert repeated.state == "received"
        with pytest.raises(UploadSessionStateConflictError):
            asyncio.run(service.receive_chunk(
                session_id,
                upload_offset=5,
                content_length=1,
                body=_chunks(b"z"),
            ))
    finally:
        dispose_engine(engine)


def test_body_mismatch_rolls_file_back_to_authoritative_offset(tmp_path: Path) -> None:
    service, _, engine = _service(tmp_path)
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadBodyLengthMismatchError):
            asyncio.run(service.receive_chunk(
                session_id,
                upload_offset=0,
                content_length=3,
                body=_chunks(b"ab"),
            ))
        status = service.get_status(session_id)
        assert status.received_size_bytes == 0
        assert next((tmp_path / "quarantine").iterdir()).read_bytes() == b""
    finally:
        dispose_engine(engine)


def test_file_ahead_truncates_and_file_behind_fails_closed(tmp_path: Path) -> None:
    service, _, engine = _service(tmp_path)
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        asyncio.run(
            service.receive_chunk(session_id, upload_offset=0, content_length=2, body=_chunks(b"ab"))
        )
        staged = next((tmp_path / "quarantine").iterdir())
        staged.write_bytes(b"abCRASH")

        resumed = asyncio.run(service.receive_chunk(
            session_id,
            upload_offset=2,
            content_length=1,
            body=_chunks(b"c"),
        ))
        assert resumed.received_size_bytes == 3
        assert staged.read_bytes() == b"abc"

        staged.write_bytes(b"a")
        with pytest.raises(UploadQuarantineStateInconsistentError):
            asyncio.run(service.complete(session_id))
        assert service.get_status(session_id).state == UploadSessionState.FAILED.value
    finally:
        dispose_engine(engine)


def test_expired_mutation_transitions_and_rejects(tmp_path: Path) -> None:
    mutable_now = {"value": 1_000}
    database_path = tmp_path / "catalog.sqlite3"
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir()
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    service = UploadTransportService(
        SqliteUploadSessionRepository(engine),
        FilesystemQuarantineStorage(quarantine_root),
        _LibraryRepository(),
        UploadTransportLimits(100, 10, 1, 0),
        quarantine_root=quarantine_root,
        now_ms=lambda: mutable_now["value"],
    )
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        mutable_now["value"] = 3_000
        with pytest.raises(UploadSessionExpiredError):
            asyncio.run(
                service.receive_chunk(
                    UploadSessionId.from_string(created.id),
                    upload_offset=0,
                    content_length=1,
                    body=_chunks(b"a"),
                )
            )
        assert service.get_status(UploadSessionId.from_string(created.id)).state == "expired"
    finally:
        dispose_engine(engine)
