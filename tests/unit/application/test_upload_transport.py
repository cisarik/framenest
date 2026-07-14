"""Unit tests for resumable upload transport application behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from pathlib import Path

import pytest

from framenest.application.upload_transport import (
    UPLOAD_FAILED_STORAGE_INCONSISTENT,
    UploadBodyLengthMismatchError,
    UploadCapabilityNotConfiguredError,
    UploadConcurrencyConflictError,
    UploadOffsetConflictTransportError,
    UploadQuarantineUnavailableError,
    UploadQuarantineStateInconsistentError,
    UploadSessionLockRegistry,
    UploadSessionExpiredError,
    UploadSessionStateConflictError,
    UploadTooLargeError,
    UploadTransportLimits,
    UploadTransportService,
)
from framenest.application.ports.quarantine_storage import (
    QuarantineStateInconsistentError,
    QuarantineWriteFailedError,
)
from framenest.application.ports.upload_sessions import (
    UploadOffsetConflictError,
    UploadSessionConcurrencyConflictError,
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
    quarantine_root.mkdir(parents=True, exist_ok=True)
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


def _service_with(
    tmp_path: Path,
    *,
    storage: object | None = None,
    repository: object | None = None,
    locks: UploadSessionLockRegistry | None = None,
) -> tuple[UploadTransportService, object, object]:
    database_path = tmp_path / "catalog.sqlite3"
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(database_path)
    inner_repository = SqliteUploadSessionRepository(engine)
    service = UploadTransportService(
        repository or inner_repository,
        storage or FilesystemQuarantineStorage(quarantine_root),
        _LibraryRepository(),
        UploadTransportLimits(
            max_total_bytes=100,
            max_patch_bytes=10,
            session_ttl_seconds=60,
            min_free_space_reserve_bytes=0,
        ),
        quarantine_root=quarantine_root,
        preview_cache_root=tmp_path / "preview-cache",
        now_ms=lambda: 1_000,
        locks=locks,
    )
    return service, repository or inner_repository, engine


class _FaultyWriter:
    def __init__(
        self,
        inner: object,
        storage: "_FaultyStorage",
    ) -> None:
        self._inner = inner
        self._storage = storage
        self.close_calls = 0

    def write(self, data: bytes) -> int:
        if self._storage.write_fails_after_accepting:
            self._inner.write(data)
            raise QuarantineWriteFailedError("synthetic write failure")
        return self._inner.write(data)

    def truncate_and_fsync(self, size: int) -> None:
        self._storage.rollback_attempted = True
        if self._storage.rollback_truncate_fails:
            raise QuarantineWriteFailedError("synthetic rollback truncate failure")
        self._inner.truncate_and_fsync(size)
        if self._storage.rollback_fsync_fails:
            raise QuarantineWriteFailedError("synthetic rollback fsync failure")

    def flush_and_fsync(self) -> None:
        if self._storage.flush_fails:
            raise QuarantineWriteFailedError("synthetic flush failure")
        self._inner.flush_and_fsync()

    def close(self) -> None:
        self.close_calls += 1
        if self._storage.close_fails:
            raise QuarantineWriteFailedError("synthetic close failure")
        self._inner.close()


class _FaultyStorage:
    def __init__(
        self,
        inner: FilesystemQuarantineStorage,
        *,
        write_fails_after_accepting: bool = False,
        flush_fails: bool = False,
        rollback_truncate_fails: bool = False,
        rollback_fsync_fails: bool = False,
        verification_size_delta: int | None = None,
        verification_size_fails: bool = False,
        close_fails: bool = False,
    ) -> None:
        self._inner = inner
        self.write_fails_after_accepting = write_fails_after_accepting
        self.flush_fails = flush_fails
        self.rollback_truncate_fails = rollback_truncate_fails
        self.rollback_fsync_fails = rollback_fsync_fails
        self.verification_size_delta = verification_size_delta
        self.verification_size_fails = verification_size_fails
        self.close_fails = close_fails
        self.rollback_attempted = False
        self.last_writer: _FaultyWriter | None = None

    @property
    def root_available(self) -> bool:
        return self._inner.root_available

    def available_bytes(self) -> int:
        return self._inner.available_bytes()

    def file_size(self, storage_key):
        if self.rollback_attempted and self.verification_size_fails:
            raise QuarantineStateInconsistentError("synthetic verification failure")
        size = self._inner.file_size(storage_key)
        if self.rollback_attempted and self.verification_size_delta is not None:
            return None if size is None else size + self.verification_size_delta
        return size

    def open_writer(self, storage_key, *, offset: int, create: bool):
        writer = _FaultyWriter(
            self._inner.open_writer(storage_key, offset=offset, create=create),
            self,
        )
        self.last_writer = writer
        return writer

    def truncate(self, storage_key, size: int) -> None:
        self._inner.truncate(storage_key, size)

    def remove(self, storage_key) -> None:
        self._inner.remove(storage_key)


class _AdvanceFailureRepository:
    def __init__(
        self,
        inner: SqliteUploadSessionRepository,
        exc: Exception,
        *,
        advance_first: bool = False,
    ) -> None:
        self._inner = inner
        self._exc = exc
        self._advance_first = advance_first

    def create(self, session):
        return self._inner.create(session)

    def get(self, session_id):
        return self._inner.get(session_id)

    def advance_received_offset(self, session_id, **kwargs):
        if self._advance_first:
            self._inner.advance_received_offset(session_id, **kwargs)
        raise self._exc

    def record_completed_checksum(self, session_id, **kwargs):
        return self._inner.record_completed_checksum(session_id, **kwargs)

    def transition_state(self, session_id, **kwargs):
        return self._inner.transition_state(session_id, **kwargs)


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


def test_excess_body_and_stream_disconnect_roll_back_and_remain_retryable(
    tmp_path: Path,
) -> None:
    async def disconnect_after_first_chunk() -> AsyncIterator[bytes]:
        yield b"a"
        raise RuntimeError("synthetic stream disconnect")

    service, _, engine = _service(tmp_path)
    try:
        excess_created = service.create_session(
            display_filename="excess.gif",
            declared_size_bytes=5,
        )
        excess_id = UploadSessionId.from_string(excess_created.id)
        with pytest.raises(UploadBodyLengthMismatchError):
            asyncio.run(
                service.receive_chunk(
                    excess_id,
                    upload_offset=0,
                    content_length=2,
                    body=_chunks(b"abc"),
                )
            )
        assert service.get_status(excess_id).received_size_bytes == 0

        disconnect_created = service.create_session(
            display_filename="disconnect.gif",
            declared_size_bytes=5,
        )
        disconnect_id = UploadSessionId.from_string(disconnect_created.id)
        with pytest.raises(UploadBodyLengthMismatchError):
            asyncio.run(
                service.receive_chunk(
                    disconnect_id,
                    upload_offset=0,
                    content_length=2,
                    body=disconnect_after_first_chunk(),
                )
            )
        retry = asyncio.run(
            service.receive_chunk(
                disconnect_id,
                upload_offset=0,
                content_length=2,
                body=_chunks(b"ab"),
            )
        )

        assert service.get_status(excess_id).received_size_bytes == 0
        assert retry.received_size_bytes == 2
        assert sorted(path.read_bytes() for path in (tmp_path / "quarantine").iterdir()) == [
            b"",
            b"ab",
        ]
    finally:
        dispose_engine(engine)


def test_write_flush_and_repository_failures_keep_original_error_after_verified_rollback(
    tmp_path: Path,
) -> None:
    write_root = tmp_path / "write"
    write_quarantine = write_root / "quarantine"
    write_quarantine.mkdir(parents=True)
    write_storage = _FaultyStorage(
        FilesystemQuarantineStorage(write_quarantine),
        write_fails_after_accepting=True,
    )
    write_service, _, write_engine = _service_with(write_root, storage=write_storage)
    try:
        created = write_service.create_session(
            display_filename="write.gif",
            declared_size_bytes=5,
        )
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadQuarantineUnavailableError):
            asyncio.run(
                write_service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=2,
                    body=_chunks(b"ab"),
                )
            )
        assert write_service.get_status(session_id).received_size_bytes == 0
        assert next(write_quarantine.iterdir()).read_bytes() == b""
    finally:
        dispose_engine(write_engine)

    flush_root = tmp_path / "flush"
    flush_quarantine = flush_root / "quarantine"
    flush_quarantine.mkdir(parents=True)
    flush_storage = _FaultyStorage(
        FilesystemQuarantineStorage(flush_quarantine),
        flush_fails=True,
    )
    flush_service, _, flush_engine = _service_with(flush_root, storage=flush_storage)
    try:
        created = flush_service.create_session(
            display_filename="flush.gif",
            declared_size_bytes=5,
        )
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadQuarantineUnavailableError):
            asyncio.run(
                flush_service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=2,
                    body=_chunks(b"ab"),
                )
            )
        assert flush_service.get_status(session_id).received_size_bytes == 0
        assert next(flush_quarantine.iterdir()).read_bytes() == b""
    finally:
        dispose_engine(flush_engine)

    repository_root = tmp_path / "repository"
    repository_db = repository_root / "catalog.sqlite3"
    repository_quarantine = repository_root / "quarantine"
    repository_quarantine.mkdir(parents=True)
    settings = FrameNestSettings(database_path=repository_db, _env_file=None)
    upgrade_database_to_head(settings)
    repository_engine = create_sqlite_engine(repository_db)
    inner_repository = SqliteUploadSessionRepository(repository_engine)
    repository = _AdvanceFailureRepository(
        inner_repository,
        UploadSessionConcurrencyConflictError("synthetic concurrency"),
    )
    repository_service = UploadTransportService(
        repository,
        FilesystemQuarantineStorage(repository_quarantine),
        _LibraryRepository(),
        UploadTransportLimits(100, 10, 60, 0),
        quarantine_root=repository_quarantine,
        preview_cache_root=repository_root / "preview-cache",
        now_ms=lambda: 1_000,
    )
    try:
        created = repository_service.create_session(
            display_filename="repository.gif",
            declared_size_bytes=5,
        )
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadConcurrencyConflictError):
            asyncio.run(
                repository_service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=2,
                    body=_chunks(b"ab"),
                )
            )
        assert repository_service.get_status(session_id).received_size_bytes == 0
        assert next(repository_quarantine.iterdir()).read_bytes() == b""
    finally:
        dispose_engine(repository_engine)


@pytest.mark.parametrize(
    ("storage_kwargs", "expected_bytes"),
    (
        ({"rollback_truncate_fails": True}, b"ab"),
        ({"rollback_fsync_fails": True}, b""),
        ({"verification_size_delta": 1}, b""),
        ({"verification_size_fails": True}, b""),
        ({"close_fails": True}, b""),
    ),
)
def test_unverified_rollback_fails_session_and_returns_inconsistency(
    tmp_path: Path,
    storage_kwargs: dict[str, object],
    expected_bytes: bytes,
) -> None:
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir()
    storage = _FaultyStorage(FilesystemQuarantineStorage(quarantine_root), **storage_kwargs)
    service, repository, engine = _service_with(tmp_path, storage=storage)
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadQuarantineStateInconsistentError):
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=3,
                    body=_chunks(b"ab"),
                )
            )

        stored = repository.get(session_id)
        assert stored is not None
        assert stored.state is UploadSessionState.FAILED
        assert stored.failure_code == UPLOAD_FAILED_STORAGE_INCONSISTENT
        assert stored.received_size_bytes == 0
        assert next(quarantine_root.iterdir()).read_bytes() == expected_bytes
        if storage_kwargs.get("close_fails"):
            assert storage.last_writer is not None
            assert storage.last_writer.close_calls == 1
        with pytest.raises(UploadSessionStateConflictError):
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=1,
                    body=_chunks(b"a"),
                )
            )
        with pytest.raises(UploadSessionStateConflictError):
            asyncio.run(service.complete(session_id))
    finally:
        dispose_engine(engine)


def test_unverified_rollback_still_returns_inconsistency_when_failed_state_cannot_persist(
    tmp_path: Path,
) -> None:
    class FailTransitionRepository:
        def __init__(self, inner: SqliteUploadSessionRepository) -> None:
            self._inner = inner

        def create(self, session):
            return self._inner.create(session)

        def get(self, session_id):
            return self._inner.get(session_id)

        def advance_received_offset(self, session_id, **kwargs):
            return self._inner.advance_received_offset(session_id, **kwargs)

        def record_completed_checksum(self, session_id, **kwargs):
            return self._inner.record_completed_checksum(session_id, **kwargs)

        def transition_state(self, session_id, **kwargs):
            if kwargs["target_state"] is UploadSessionState.FAILED:
                raise UploadSessionConcurrencyConflictError("synthetic stale state")
            return self._inner.transition_state(session_id, **kwargs)

    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir()
    storage = _FaultyStorage(
        FilesystemQuarantineStorage(quarantine_root),
        rollback_truncate_fails=True,
    )
    database_path = tmp_path / "catalog.sqlite3"
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    repository = FailTransitionRepository(SqliteUploadSessionRepository(engine))
    service = UploadTransportService(
        repository,
        storage,
        _LibraryRepository(),
        UploadTransportLimits(100, 10, 60, 0),
        quarantine_root=quarantine_root,
        preview_cache_root=tmp_path / "preview-cache",
        now_ms=lambda: 1_000,
    )
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadQuarantineStateInconsistentError):
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=3,
                    body=_chunks(b"ab"),
                )
            )
    finally:
        dispose_engine(engine)


def test_persisted_offset_advanced_during_repository_error_is_not_truncated(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir()
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    inner_repository = SqliteUploadSessionRepository(engine)
    repository = _AdvanceFailureRepository(
        inner_repository,
        UploadOffsetConflictError("synthetic acknowledged offset"),
        advance_first=True,
    )
    service = UploadTransportService(
        repository,
        FilesystemQuarantineStorage(quarantine_root),
        _LibraryRepository(),
        UploadTransportLimits(100, 10, 60, 0),
        quarantine_root=quarantine_root,
        preview_cache_root=tmp_path / "preview-cache",
        now_ms=lambda: 1_000,
    )
    try:
        created = service.create_session(display_filename="example.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        with pytest.raises(UploadOffsetConflictTransportError) as conflict:
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=2,
                    body=_chunks(b"ab"),
                )
            )

        assert conflict.value.current_offset == 2
        assert service.get_status(session_id).received_size_bytes == 2
        assert next(quarantine_root.iterdir()).read_bytes() == b"ab"
        with pytest.raises(UploadOffsetConflictTransportError) as retry_conflict:
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=0,
                    content_length=1,
                    body=_chunks(b"a"),
                )
            )
        assert retry_conflict.value.current_offset == 2
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


def test_lock_registry_releases_after_single_success_exception_and_terminal_operations(
    tmp_path: Path,
) -> None:
    locks = UploadSessionLockRegistry()
    service, _, engine = _service_with(tmp_path, locks=locks)
    try:
        created = service.create_session(display_filename="patch.gif", declared_size_bytes=3)
        session_id = UploadSessionId.from_string(created.id)
        asyncio.run(
            service.receive_chunk(
                session_id,
                upload_offset=0,
                content_length=1,
                body=_chunks(b"a"),
            )
        )
        assert locks.size() == 0

        with pytest.raises(UploadBodyLengthMismatchError):
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=1,
                    content_length=2,
                    body=_chunks(b"b"),
                )
            )
        assert locks.size() == 0

        asyncio.run(
            service.receive_chunk(
                session_id,
                upload_offset=1,
                content_length=2,
                body=_chunks(b"bc"),
            )
        )
        asyncio.run(service.complete(session_id))
        assert locks.size() == 0

        cancelled = service.create_session(display_filename="cancel.gif", declared_size_bytes=1)
        asyncio.run(service.cancel(UploadSessionId.from_string(cancelled.id)))
        assert locks.size() == 0
    finally:
        dispose_engine(engine)


def test_lock_registry_does_not_grow_after_many_sequential_mutations(
    tmp_path: Path,
) -> None:
    locks = UploadSessionLockRegistry()
    service, _, engine = _service_with(tmp_path, locks=locks)
    try:
        created = service.create_session(display_filename="patches.gif", declared_size_bytes=5)
        session_id = UploadSessionId.from_string(created.id)
        for offset in range(5):
            asyncio.run(
                service.receive_chunk(
                    session_id,
                    upload_offset=offset,
                    content_length=1,
                    body=_chunks(bytes([65 + offset])),
                )
            )
            assert locks.size() == 0

        for index in range(10):
            completed = service.create_session(
                display_filename=f"complete-{index}.gif",
                declared_size_bytes=1,
            )
            completed_id = UploadSessionId.from_string(completed.id)
            asyncio.run(
                service.receive_chunk(
                    completed_id,
                    upload_offset=0,
                    content_length=1,
                    body=_chunks(b"x"),
                )
            )
            asyncio.run(service.complete(completed_id))
            cancelled = service.create_session(
                display_filename=f"cancel-{index}.gif",
                declared_size_bytes=1,
            )
            asyncio.run(service.cancel(UploadSessionId.from_string(cancelled.id)))
            assert locks.size() == 0
    finally:
        dispose_engine(engine)


def test_lock_registry_serializes_waiters_and_cleans_up_cancelled_waiter() -> None:
    registry = UploadSessionLockRegistry()
    session_id = UploadSessionId.new()
    order: list[str] = []

    async def scenario() -> None:
        async with registry.lease(session_id):
            original_entry = registry._locks[session_id.to_string()]

            async def waiter() -> None:
                async with registry.lease(session_id):
                    order.append("waiter-entered")

            task = asyncio.create_task(waiter())
            await asyncio.sleep(0)
            assert registry.size() == 1
            assert registry._locks[session_id.to_string()] is original_entry
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert registry.size() == 1
        assert registry.size() == 0

    asyncio.run(scenario())
    assert order == []


def test_lock_registry_prevents_same_session_overlap_and_allows_unrelated_concurrency() -> None:
    registry = UploadSessionLockRegistry()
    session_id = UploadSessionId.new()
    other_session_id = UploadSessionId.new()
    inside = False
    overlap = False
    other_entered_while_first_held = False

    async def same_session_worker() -> None:
        nonlocal inside, overlap
        async with registry.lease(session_id):
            if inside:
                overlap = True
            inside = True
            await asyncio.sleep(0.01)
            inside = False

    async def other_session_worker() -> None:
        nonlocal other_entered_while_first_held
        async with registry.lease(other_session_id):
            other_entered_while_first_held = inside

    async def scenario() -> None:
        first = asyncio.create_task(same_session_worker())
        await asyncio.sleep(0)
        other = asyncio.create_task(other_session_worker())
        second = asyncio.create_task(same_session_worker())
        await asyncio.gather(first, second, other)

    asyncio.run(scenario())

    assert not overlap
    assert other_entered_while_first_held
    assert registry.size() == 0


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
