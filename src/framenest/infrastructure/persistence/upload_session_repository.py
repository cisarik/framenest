"""SQLAlchemy Core adapter for durable upload sessions."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from framenest.application.ports.upload_sessions import (
    FrameNestUploadSessionRepositoryError,
    IncompleteUploadSessionError,
    InvalidUploadChecksumError,
    InvalidUploadSessionTransitionError,
    UploadOffsetConflictError,
    UploadSessionAlreadyExistsError,
    UploadSessionConcurrencyConflictError,
    UploadSessionNotFoundError,
    UploadSizeLimitExceededError,
    UploadStorageKeyAlreadyExistsError,
)
from framenest.domain.uploads import (
    COMPLETE_UPLOAD_SESSION_STATES,
    FrameNestUploadChecksumError,
    FrameNestUploadOffsetError,
    FrameNestUploadSessionError,
    FrameNestUploadSessionTransitionError,
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
    ensure_upload_session_transition_allowed,
    validate_sha256_checksum_hex,
    validate_upload_failure_code,
    validate_upload_offset_advance,
)
from framenest.infrastructure.persistence.catalog_schema import upload_sessions
from framenest.infrastructure.persistence.engine import run_in_transaction

_REPOSITORY_FAILURE_MESSAGE = "Upload session operation failed."
_FAILURE_STATES = frozenset({UploadSessionState.FAILED, UploadSessionState.REJECTED})


class SqliteUploadSessionRepository:
    """Synchronous SQLite upload-session adapter."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, session: UploadSession) -> None:
        def operation(connection: Connection) -> None:
            if _row_by_id(connection, session.id) is not None:
                raise UploadSessionAlreadyExistsError("upload session already exists")
            if _row_by_storage_key(connection, session.storage_key.value) is not None:
                raise UploadStorageKeyAlreadyExistsError("upload storage key already exists")
            connection.execute(insert(upload_sessions).values(_values_from_session(session)))

        try:
            run_in_transaction(self._engine, operation)
        except (
            UploadSessionAlreadyExistsError,
            UploadStorageKeyAlreadyExistsError,
        ):
            raise
        except IntegrityError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc
        except SQLAlchemyError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def get(self, session_id: UploadSessionId) -> UploadSession | None:
        def operation(connection: Connection) -> UploadSession | None:
            row = _row_by_id(connection, session_id)
            if row is None:
                return None
            return _session_from_row(row)

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestUploadSessionRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def advance_received_offset(
        self,
        session_id: UploadSessionId,
        *,
        expected_received_size_bytes: int,
        accepted_size_bytes: int,
        expected_version: int,
        updated_at_ms: int,
    ) -> UploadSession:
        try:
            validate_upload_offset_advance(
                current_offset=expected_received_size_bytes,
                accepted_bytes=accepted_size_bytes,
                declared_size_bytes=max(expected_received_size_bytes + accepted_size_bytes, 1),
            )
            _validate_non_negative(expected_version)
            _validate_non_negative(updated_at_ms)
        except (FrameNestUploadOffsetError, FrameNestUploadSessionError) as exc:
            raise UploadOffsetConflictError("upload offset conflict") from exc

        def operation(connection: Connection) -> UploadSession:
            next_offset = expected_received_size_bytes + accepted_size_bytes
            result = connection.execute(
                update(upload_sessions)
                .where(
                    and_(
                        upload_sessions.c.id == session_id.to_string(),
                        upload_sessions.c.state == UploadSessionState.RECEIVING.value,
                        upload_sessions.c.received_size_bytes == expected_received_size_bytes,
                        upload_sessions.c.version == expected_version,
                        upload_sessions.c.declared_size_bytes >= next_offset,
                    )
                )
                .values(
                    received_size_bytes=next_offset,
                    updated_at_ms=updated_at_ms,
                    version=upload_sessions.c.version + 1,
                )
            )
            if result.rowcount == 1:
                return _require_session(connection, session_id)
            row = _row_by_id(connection, session_id)
            _raise_offset_guard_error(
                row,
                expected_received_size_bytes=expected_received_size_bytes,
                expected_version=expected_version,
                next_offset=next_offset,
            )

        try:
            return run_in_transaction(self._engine, operation)
        except (
            UploadSessionNotFoundError,
            InvalidUploadSessionTransitionError,
            UploadOffsetConflictError,
            UploadSizeLimitExceededError,
            UploadSessionConcurrencyConflictError,
        ):
            raise
        except SQLAlchemyError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def record_completed_checksum(
        self,
        session_id: UploadSessionId,
        *,
        expected_state: UploadSessionState,
        expected_version: int,
        checksum_hex: str,
        updated_at_ms: int,
    ) -> UploadSession:
        try:
            checksum = validate_sha256_checksum_hex(checksum_hex)
            _validate_non_negative(expected_version)
            _validate_non_negative(updated_at_ms)
        except FrameNestUploadChecksumError as exc:
            raise InvalidUploadChecksumError("invalid upload checksum") from exc
        except FrameNestUploadSessionError as exc:
            raise UploadSessionConcurrencyConflictError(
                "upload session concurrency conflict"
            ) from exc

        def operation(connection: Connection) -> UploadSession:
            result = connection.execute(
                update(upload_sessions)
                .where(
                    and_(
                        upload_sessions.c.id == session_id.to_string(),
                        upload_sessions.c.state == expected_state.value,
                        upload_sessions.c.version == expected_version,
                        upload_sessions.c.checksum_algorithm.is_(None),
                        upload_sessions.c.checksum_hex.is_(None),
                    )
                )
                .values(
                    checksum_algorithm="sha256",
                    checksum_hex=checksum,
                    updated_at_ms=updated_at_ms,
                    version=upload_sessions.c.version + 1,
                )
            )
            if result.rowcount == 1:
                return _require_session(connection, session_id)
            row = _row_by_id(connection, session_id)
            if row is None:
                raise UploadSessionNotFoundError("upload session not found")
            if str(row["state"]) != expected_state.value:
                raise InvalidUploadSessionTransitionError(
                    "invalid upload session transition"
                )
            if int(row["version"]) != expected_version:
                raise UploadSessionConcurrencyConflictError(
                    "upload session concurrency conflict"
                )
            if row["checksum_algorithm"] == "sha256" and row["checksum_hex"] == checksum:
                return _session_from_row(row)
            raise InvalidUploadChecksumError("invalid upload checksum")

        try:
            return run_in_transaction(self._engine, operation)
        except (
            UploadSessionNotFoundError,
            InvalidUploadSessionTransitionError,
            UploadSessionConcurrencyConflictError,
            InvalidUploadChecksumError,
        ):
            raise
        except SQLAlchemyError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def transition_state(
        self,
        session_id: UploadSessionId,
        *,
        expected_state: UploadSessionState,
        target_state: UploadSessionState,
        expected_version: int,
        updated_at_ms: int,
        failure_code: str | None = None,
    ) -> UploadSession:
        try:
            ensure_upload_session_transition_allowed(expected_state, target_state)
            _validate_non_negative(expected_version)
            _validate_non_negative(updated_at_ms)
            if failure_code is not None:
                validate_upload_failure_code(failure_code)
                if target_state not in _FAILURE_STATES:
                    raise FrameNestUploadSessionTransitionError(
                        "failure code is valid only for failure states"
                    )
        except FrameNestUploadSessionTransitionError as exc:
            raise InvalidUploadSessionTransitionError(
                "invalid upload session transition"
            ) from exc
        except FrameNestUploadSessionError as exc:
            raise UploadSessionConcurrencyConflictError(
                "upload session concurrency conflict"
            ) from exc

        def operation(connection: Connection) -> UploadSession:
            update_guards = [
                upload_sessions.c.id == session_id.to_string(),
                upload_sessions.c.state == expected_state.value,
                upload_sessions.c.version == expected_version,
            ]
            if _target_requires_complete_upload(target_state):
                update_guards.append(
                    upload_sessions.c.received_size_bytes
                    == upload_sessions.c.declared_size_bytes
                )
            result = connection.execute(
                update(upload_sessions)
                .where(and_(*update_guards))
                .values(
                    state=target_state.value,
                    updated_at_ms=updated_at_ms,
                    failure_code=failure_code,
                    version=upload_sessions.c.version + 1,
                )
            )
            if result.rowcount == 1:
                return _require_session(connection, session_id)
            row = _row_by_id(connection, session_id)
            if row is None:
                raise UploadSessionNotFoundError("upload session not found")
            if str(row["state"]) != expected_state.value:
                raise InvalidUploadSessionTransitionError(
                    "invalid upload session transition"
                )
            if int(row["version"]) != expected_version:
                raise UploadSessionConcurrencyConflictError(
                    "upload session concurrency conflict"
                )
            if _target_requires_complete_upload(target_state) and int(
                row["received_size_bytes"]
            ) != int(row["declared_size_bytes"]):
                raise IncompleteUploadSessionError("incomplete upload session")
            raise UploadSessionConcurrencyConflictError(
                "upload session concurrency conflict"
            )

        try:
            return run_in_transaction(self._engine, operation)
        except (
            UploadSessionNotFoundError,
            IncompleteUploadSessionError,
            InvalidUploadSessionTransitionError,
            UploadSessionConcurrencyConflictError,
        ):
            raise
        except SQLAlchemyError as exc:
            raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc


def _row_by_id(
    connection: Connection,
    session_id: UploadSessionId,
) -> Mapping[str, object] | None:
    return (
        connection.execute(
            select(upload_sessions).where(upload_sessions.c.id == session_id.to_string())
        )
        .mappings()
        .first()
    )


def _row_by_storage_key(
    connection: Connection,
    storage_key: str,
) -> Mapping[str, object] | None:
    return (
        connection.execute(
            select(upload_sessions).where(upload_sessions.c.storage_key == storage_key)
        )
        .mappings()
        .first()
    )


def _require_session(connection: Connection, session_id: UploadSessionId) -> UploadSession:
    row = _row_by_id(connection, session_id)
    if row is None:
        raise UploadSessionNotFoundError("upload session not found")
    return _session_from_row(row)


def _raise_offset_guard_error(
    row: Mapping[str, object] | None,
    *,
    expected_received_size_bytes: int,
    expected_version: int,
    next_offset: int,
) -> None:
    if row is None:
        raise UploadSessionNotFoundError("upload session not found")
    if str(row["state"]) != UploadSessionState.RECEIVING.value:
        raise InvalidUploadSessionTransitionError("invalid upload session transition")
    if int(row["received_size_bytes"]) != expected_received_size_bytes:
        raise UploadOffsetConflictError("upload offset conflict")
    if int(row["version"]) != expected_version:
        raise UploadSessionConcurrencyConflictError("upload session concurrency conflict")
    if next_offset > int(row["declared_size_bytes"]):
        raise UploadSizeLimitExceededError("upload size limit exceeded")
    raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE)


def _values_from_session(session: UploadSession) -> dict[str, object]:
    return {
        "id": session.id.to_string(),
        "state": session.state.value,
        "storage_key": session.storage_key.value,
        "display_filename": session.display_filename.value,
        "declared_size_bytes": session.declared_size_bytes,
        "received_size_bytes": session.received_size_bytes,
        "checksum_algorithm": session.checksum_algorithm,
        "checksum_hex": session.checksum_hex,
        "created_at_ms": session.created_at_ms,
        "updated_at_ms": session.updated_at_ms,
        "expires_at_ms": session.expires_at_ms,
        "failure_code": session.failure_code,
        "version": session.version,
    }


def _session_from_row(row: Mapping[str, object]) -> UploadSession:
    try:
        return UploadSession(
            id=UploadSessionId.from_string(str(row["id"])),
            state=UploadSessionState(str(row["state"])),
            storage_key=UploadStorageKey(str(row["storage_key"])),
            display_filename=UploadDisplayFilename(str(row["display_filename"])),
            declared_size_bytes=int(row["declared_size_bytes"]),
            received_size_bytes=int(row["received_size_bytes"]),
            checksum_algorithm=None
            if row["checksum_algorithm"] is None
            else str(row["checksum_algorithm"]),
            checksum_hex=None if row["checksum_hex"] is None else str(row["checksum_hex"]),
            created_at_ms=int(row["created_at_ms"]),
            updated_at_ms=int(row["updated_at_ms"]),
            expires_at_ms=int(row["expires_at_ms"]),
            failure_code=None if row["failure_code"] is None else str(row["failure_code"]),
            version=int(row["version"]),
        )
    except (FrameNestUploadSessionError, ValueError) as exc:
        raise FrameNestUploadSessionRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc


def _target_requires_complete_upload(target_state: UploadSessionState) -> bool:
    return target_state in COMPLETE_UPLOAD_SESSION_STATES


def _validate_non_negative(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FrameNestUploadSessionError("invalid concurrency guard")
