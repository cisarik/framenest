"""Application-owned resumable upload transport into quarantine storage."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import time
import uuid

from framenest.application.ports.library_repository import LibraryRepository
from framenest.application.ports.quarantine_storage import (
    QuarantineStateInconsistentError,
    QuarantineStorage,
    QuarantineStorageInsufficientSpaceError,
    QuarantineStorageUnavailableError,
    QuarantineWriteFailedError,
)
from framenest.application.ports.upload_sessions import (
    FrameNestUploadSessionRepositoryError,
    IncompleteUploadSessionError,
    InvalidUploadSessionTransitionError,
    UploadOffsetConflictError,
    UploadSessionConcurrencyConflictError,
    UploadSessionNotFoundError,
    UploadSessionRepository,
    UploadSizeLimitExceededError,
)
from framenest.application.root_paths import roots_overlap
from framenest.domain import LibraryPathFlavor
from framenest.domain.uploads import (
    FrameNestUploadSessionError,
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
)

UPLOAD_FAILED_STORAGE_INCONSISTENT = "QUARANTINE_STATE_INCONSISTENT"


class UploadTransportError(RuntimeError):
    """Base sanitized upload transport error."""


class UploadCapabilityNotConfiguredError(UploadTransportError):
    """Raised when upload transport is disabled or unavailable."""


class UploadSessionNotFoundTransportError(UploadTransportError):
    """Raised when the requested upload session is absent."""


class UploadInvalidMetadataError(UploadTransportError):
    """Raised when create-session metadata is invalid."""


class UploadTooLargeError(UploadTransportError):
    """Raised when declared total upload size exceeds policy."""


class UploadChunkTooLargeError(UploadTransportError):
    """Raised when a PATCH chunk exceeds policy."""


class UploadInvalidOffsetError(UploadTransportError):
    """Raised when a supplied upload offset is malformed."""


class UploadOffsetConflictTransportError(UploadTransportError):
    """Raised when the supplied offset differs from the authoritative offset."""

    def __init__(self, current_offset: int) -> None:
        super().__init__("upload offset conflict")
        self.current_offset = current_offset


class UploadSessionStateConflictError(UploadTransportError):
    """Raised when the session state does not permit the requested mutation."""


class UploadSessionExpiredError(UploadTransportError):
    """Raised when a mutation observes an expired non-terminal session."""


class UploadInsufficientStorageError(UploadTransportError):
    """Raised when quarantine storage has insufficient free space."""


class UploadBodyLengthMismatchError(UploadTransportError):
    """Raised when streamed bytes do not match Content-Length."""


class UploadQuarantineUnavailableError(UploadTransportError):
    """Raised when quarantine storage cannot be used safely."""


class UploadQuarantineStateInconsistentError(UploadTransportError):
    """Raised when persisted and filesystem state cannot be reconciled."""


class UploadConcurrencyConflictError(UploadTransportError):
    """Raised when optimistic repository guards reject a mutation."""


@dataclass(frozen=True, slots=True)
class UploadTransportLimits:
    max_total_bytes: int
    max_patch_bytes: int
    session_ttl_seconds: int
    min_free_space_reserve_bytes: int


@dataclass(frozen=True, slots=True)
class UploadSessionSnapshot:
    id: str
    state: str
    display_filename: str
    declared_size_bytes: int
    received_size_bytes: int
    expires_at: int


def default_now_ms() -> int:
    """Return current wall-clock milliseconds for durable upload timestamps."""
    return int(time.time() * 1000)


class UploadSessionLockRegistry:
    """Bounded in-process per-session lock registry for one Uvicorn worker."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = Lock()

    def lock_for(self, session_id: UploadSessionId) -> asyncio.Lock:
        key = session_id.to_string()
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

    def discard(self, session_id: UploadSessionId) -> None:
        key = session_id.to_string()
        with self._guard:
            lock = self._locks.get(key)
            if lock is not None and not lock.locked():
                self._locks.pop(key, None)


class UploadTransportService:
    """Coordinate durable upload sessions with server-owned quarantine bytes."""

    def __init__(
        self,
        repository: UploadSessionRepository,
        storage: QuarantineStorage | None,
        library_repository: LibraryRepository,
        limits: UploadTransportLimits,
        *,
        quarantine_root: Path | None,
        preview_cache_root: Path | None = None,
        now_ms: Callable[[], int] = default_now_ms,
        locks: UploadSessionLockRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._library_repository = library_repository
        self._limits = limits
        self._quarantine_root = quarantine_root
        self._preview_cache_root = preview_cache_root
        self._now_ms = now_ms
        self._locks = locks or UploadSessionLockRegistry()

    def create_session(
        self,
        *,
        display_filename: object,
        declared_size_bytes: object,
    ) -> UploadSessionSnapshot:
        storage = self._require_storage()
        try:
            filename = UploadDisplayFilename(display_filename)
            if isinstance(declared_size_bytes, bool) or not isinstance(declared_size_bytes, int):
                raise FrameNestUploadSessionError("invalid upload size")
            if declared_size_bytes <= 0:
                raise FrameNestUploadSessionError("invalid upload size")
        except FrameNestUploadSessionError as exc:
            raise UploadInvalidMetadataError("invalid upload metadata") from exc
        if declared_size_bytes > self._limits.max_total_bytes:
            raise UploadTooLargeError("upload too large")
        self._ensure_root_separation()
        self._ensure_space(declared_size_bytes)
        now_ms = self._now_ms()
        session = UploadSession(
            id=UploadSessionId.new(),
            state=UploadSessionState.CREATED,
            storage_key=UploadStorageKey(uuid.uuid4().hex),
            display_filename=filename,
            declared_size_bytes=declared_size_bytes,
            received_size_bytes=0,
            checksum_algorithm=None,
            checksum_hex=None,
            created_at_ms=now_ms,
            updated_at_ms=now_ms,
            expires_at_ms=now_ms + self._limits.session_ttl_seconds * 1000,
            failure_code=None,
            version=0,
        )
        try:
            self._repository.create(session)
        except FrameNestUploadSessionRepositoryError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
        return _snapshot(session)

    def get_status(self, session_id: UploadSessionId) -> UploadSessionSnapshot:
        session = self._load(session_id)
        return _snapshot(session)

    async def receive_chunk(
        self,
        session_id: UploadSessionId,
        *,
        upload_offset: int,
        content_length: int,
        body: AsyncIterator[bytes],
    ) -> UploadSessionSnapshot:
        storage = self._require_storage()
        if upload_offset < 0:
            raise UploadInvalidOffsetError("invalid upload offset")
        if content_length <= 0:
            raise UploadBodyLengthMismatchError("upload body length mismatch")
        if content_length > self._limits.max_patch_bytes:
            raise UploadChunkTooLargeError("upload chunk too large")
        self._ensure_space(content_length)

        lock = self._locks.lock_for(session_id)
        async with lock:
            session = self._load(session_id)
            session = self._expire_if_needed(session)
            if session.received_size_bytes != upload_offset:
                raise UploadOffsetConflictTransportError(session.received_size_bytes)
            if session.state is UploadSessionState.CREATED:
                if upload_offset != 0:
                    raise UploadOffsetConflictTransportError(session.received_size_bytes)
                session = self._transition(
                    session,
                    UploadSessionState.RECEIVING,
                    failure_code=None,
                )
            if session.state is not UploadSessionState.RECEIVING:
                raise UploadSessionStateConflictError("upload session state conflict")
            if upload_offset + content_length > session.declared_size_bytes:
                raise UploadChunkTooLargeError("upload chunk too large")

            self._reconcile_file_before_write(storage, session)
            original_offset = session.received_size_bytes
            writer = storage.open_writer(
                session.storage_key,
                offset=original_offset,
                create=original_offset == 0 and storage.file_size(session.storage_key) is None,
            )
            actual = 0
            try:
                async for chunk in body:
                    if not chunk:
                        continue
                    actual += len(chunk)
                    if actual > content_length:
                        raise UploadBodyLengthMismatchError("upload body length mismatch")
                    written = writer.write(chunk)
                    if written != len(chunk):
                        raise UploadQuarantineUnavailableError("upload storage unavailable")
                if actual != content_length:
                    raise UploadBodyLengthMismatchError("upload body length mismatch")
                writer.flush_and_fsync()
                updated = self._repository.advance_received_offset(
                    session.id,
                    expected_received_size_bytes=original_offset,
                    accepted_size_bytes=actual,
                    expected_version=session.version,
                    updated_at_ms=self._now_ms(),
                )
            except (
                UploadBodyLengthMismatchError,
                UploadQuarantineUnavailableError,
                UploadChunkTooLargeError,
            ):
                _rollback_writer(writer, original_offset)
                raise
            except QuarantineWriteFailedError as exc:
                _rollback_writer(writer, original_offset)
                raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
            except UploadOffsetConflictError as exc:
                _rollback_writer(writer, original_offset)
                current = self._repository.get(session.id)
                raise UploadOffsetConflictTransportError(
                    current.received_size_bytes if current is not None else original_offset
                ) from exc
            except UploadSizeLimitExceededError as exc:
                _rollback_writer(writer, original_offset)
                raise UploadChunkTooLargeError("upload chunk too large") from exc
            except (
                UploadSessionConcurrencyConflictError,
                InvalidUploadSessionTransitionError,
                FrameNestUploadSessionRepositoryError,
            ) as exc:
                _rollback_writer(writer, original_offset)
                raise UploadConcurrencyConflictError("upload concurrency conflict") from exc
            except Exception as exc:
                _rollback_writer(writer, original_offset)
                raise UploadBodyLengthMismatchError("upload body length mismatch") from exc
            finally:
                writer.close()
            return _snapshot(updated)

    async def complete(self, session_id: UploadSessionId) -> UploadSessionSnapshot:
        storage = self._require_storage()
        lock = self._locks.lock_for(session_id)
        async with lock:
            session = self._load(session_id)
            session = self._expire_if_needed(session)
            if session.state is UploadSessionState.RECEIVED:
                self._ensure_complete_file(storage, session)
                return _snapshot(session)
            if session.state is not UploadSessionState.RECEIVING:
                raise UploadSessionStateConflictError("upload session state conflict")
            if session.received_size_bytes != session.declared_size_bytes:
                self._ensure_file_matches_received_size(storage, session)
                raise UploadSessionStateConflictError("upload session state conflict")
            self._ensure_complete_file(storage, session)
            updated = self._transition(session, UploadSessionState.RECEIVED, failure_code=None)
            self._locks.discard(session.id)
            return _snapshot(updated)

    async def cancel(self, session_id: UploadSessionId) -> UploadSessionSnapshot:
        storage = self._require_storage()
        lock = self._locks.lock_for(session_id)
        async with lock:
            session = self._load(session_id)
            if session.state is UploadSessionState.CANCELLED:
                self._remove_cancelled_file(storage, session)
                self._locks.discard(session.id)
                return _snapshot(session)
            if session.state in {
                UploadSessionState.EXPIRED,
                UploadSessionState.FAILED,
                UploadSessionState.CATALOGED,
                UploadSessionState.REJECTED,
            }:
                raise UploadSessionStateConflictError("upload session state conflict")
            cancelled = self._transition(session, UploadSessionState.CANCELLED, failure_code=None)
            self._remove_cancelled_file(storage, cancelled)
            self._locks.discard(cancelled.id)
            return _snapshot(cancelled)

    def _load(self, session_id: UploadSessionId) -> UploadSession:
        try:
            session = self._repository.get(session_id)
        except FrameNestUploadSessionRepositoryError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
        if session is None:
            raise UploadSessionNotFoundTransportError("upload session not found")
        return session

    def _require_storage(self) -> QuarantineStorage:
        storage = self._storage
        if storage is None or not storage.root_available:
            raise UploadCapabilityNotConfiguredError("upload capability not configured")
        return storage

    def _ensure_root_separation(self) -> None:
        if self._quarantine_root is None:
            raise UploadCapabilityNotConfiguredError("upload capability not configured")
        if self._preview_cache_root is not None and roots_overlap(
            self._quarantine_root,
            self._preview_cache_root,
        ):
            raise UploadCapabilityNotConfiguredError("upload capability not configured")
        for library in self._library_repository.list_all():
            if library.root.flavor is not LibraryPathFlavor.POSIX:
                continue
            if roots_overlap(self._quarantine_root, Path(library.root.path)):
                raise UploadCapabilityNotConfiguredError("upload capability not configured")

    def _ensure_space(self, requested_bytes: int) -> None:
        try:
            available = self._require_storage().available_bytes()
        except (
            QuarantineStorageUnavailableError,
            QuarantineStorageInsufficientSpaceError,
        ) as exc:
            raise UploadInsufficientStorageError("insufficient quarantine storage") from exc
        if requested_bytes + self._limits.min_free_space_reserve_bytes > available:
            raise UploadInsufficientStorageError("insufficient quarantine storage")

    def _expire_if_needed(self, session: UploadSession) -> UploadSession:
        if session.state in {
            UploadSessionState.CATALOGED,
            UploadSessionState.REJECTED,
            UploadSessionState.CANCELLED,
            UploadSessionState.EXPIRED,
            UploadSessionState.FAILED,
        }:
            return session
        if self._now_ms() <= session.expires_at_ms:
            return session
        try:
            expired = self._transition(session, UploadSessionState.EXPIRED, failure_code=None)
        except UploadTransportError:
            raise
        raise UploadSessionExpiredError(expired.state.value)

    def _transition(
        self,
        session: UploadSession,
        target: UploadSessionState,
        *,
        failure_code: str | None,
    ) -> UploadSession:
        try:
            return self._repository.transition_state(
                session.id,
                expected_state=session.state,
                target_state=target,
                expected_version=session.version,
                updated_at_ms=self._now_ms(),
                failure_code=failure_code,
            )
        except UploadSessionNotFoundError as exc:
            raise UploadSessionNotFoundTransportError("upload session not found") from exc
        except IncompleteUploadSessionError as exc:
            raise UploadQuarantineStateInconsistentError("quarantine state inconsistent") from exc
        except InvalidUploadSessionTransitionError as exc:
            raise UploadSessionStateConflictError("upload session state conflict") from exc
        except UploadSessionConcurrencyConflictError as exc:
            raise UploadConcurrencyConflictError("upload concurrency conflict") from exc
        except FrameNestUploadSessionRepositoryError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc

    def _reconcile_file_before_write(
        self,
        storage: QuarantineStorage,
        session: UploadSession,
    ) -> None:
        try:
            size = storage.file_size(session.storage_key)
        except QuarantineStateInconsistentError as exc:
            raise UploadQuarantineStateInconsistentError("quarantine state inconsistent") from exc
        except QuarantineStorageUnavailableError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
        if size is None:
            if session.received_size_bytes == 0:
                return
            self._fail_inconsistent_session(session)
        if size == session.received_size_bytes:
            return
        if size > session.received_size_bytes:
            try:
                storage.truncate(session.storage_key, session.received_size_bytes)
            except QuarantineWriteFailedError as exc:
                raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
            return
        self._fail_inconsistent_session(session)

    def _ensure_complete_file(
        self,
        storage: QuarantineStorage,
        session: UploadSession,
    ) -> None:
        try:
            size = storage.file_size(session.storage_key)
        except QuarantineStateInconsistentError as exc:
            self._fail_inconsistent_session(session)
            raise UploadQuarantineStateInconsistentError("quarantine state inconsistent") from exc
        if size != session.declared_size_bytes or size != session.received_size_bytes:
            if size is not None and size > session.received_size_bytes:
                storage.truncate(session.storage_key, session.received_size_bytes)
            self._fail_inconsistent_session(session)

    def _ensure_file_matches_received_size(
        self,
        storage: QuarantineStorage,
        session: UploadSession,
    ) -> None:
        try:
            size = storage.file_size(session.storage_key)
        except QuarantineStateInconsistentError as exc:
            self._fail_inconsistent_session(session)
            raise UploadQuarantineStateInconsistentError("quarantine state inconsistent") from exc
        except QuarantineStorageUnavailableError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc
        if size != session.received_size_bytes:
            if size is not None and size > session.received_size_bytes:
                storage.truncate(session.storage_key, session.received_size_bytes)
            self._fail_inconsistent_session(session)

    def _fail_inconsistent_session(self, session: UploadSession) -> None:
        try:
            self._transition(
                session,
                UploadSessionState.FAILED,
                failure_code=UPLOAD_FAILED_STORAGE_INCONSISTENT,
            )
        except UploadSessionStateConflictError:
            pass
        raise UploadQuarantineStateInconsistentError("quarantine state inconsistent")

    def _remove_cancelled_file(
        self,
        storage: QuarantineStorage,
        session: UploadSession,
    ) -> None:
        try:
            storage.remove(session.storage_key)
        except QuarantineWriteFailedError as exc:
            raise UploadQuarantineUnavailableError("upload storage unavailable") from exc


def _snapshot(session: UploadSession) -> UploadSessionSnapshot:
    return UploadSessionSnapshot(
        id=session.id.to_string(),
        state=session.state.value,
        display_filename=session.display_filename.value,
        declared_size_bytes=session.declared_size_bytes,
        received_size_bytes=session.received_size_bytes,
        expires_at=session.expires_at_ms,
    )


def _rollback_writer(writer: object, offset: int) -> None:
    try:
        writer.truncate_and_fsync(offset)
    except Exception:
        pass
