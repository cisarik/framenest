"""Unit tests for the SQLite upload-session repository."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import pytest
import sqlalchemy as sa

from framenest.application.ports.upload_sessions import (
    IncompleteUploadSessionError,
    InvalidUploadChecksumError,
    InvalidUploadSessionTransitionError,
    InvalidUploadValidationEvidenceError,
    UploadOffsetConflictError,
    UploadSessionAlreadyExistsError,
    UploadSessionConcurrencyConflictError,
    UploadSessionNotFoundError,
    UploadSizeLimitExceededError,
    UploadStorageKeyAlreadyExistsError,
)
from framenest.configuration import FrameNestSettings
from framenest.domain.uploads import (
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
    UploadValidatedFormat,
    UploadValidatedMediaKind,
    VALIDATED_UPLOAD_SESSION_STATES,
)
from framenest.infrastructure.persistence.engine import create_sqlite_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.upload_session_repository import (
    SqliteUploadSessionRepository,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
UPLOAD_REPOSITORY_MODULE = (
    REPOSITORY_ROOT
    / "src"
    / "framenest"
    / "infrastructure"
    / "persistence"
    / "upload_session_repository.py"
)


def _engine(tmp_path: Path) -> sa.Engine:
    database_path = tmp_path / "upload-sessions.sqlite3"
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    return create_sqlite_engine(database_path)


def _repository(tmp_path: Path) -> tuple[SqliteUploadSessionRepository, sa.Engine]:
    engine = _engine(tmp_path)
    return SqliteUploadSessionRepository(engine), engine


def _session(
    *,
    session_id: UploadSessionId | None = None,
    storage_key: str = "upload-session-0001",
    state: UploadSessionState = UploadSessionState.CREATED,
    received_size_bytes: int = 0,
    declared_size_bytes: int = 100,
    checksum_hex: str | None = None,
    version: int = 0,
    validated_media_kind: UploadValidatedMediaKind | None = None,
    validated_format: UploadValidatedFormat | None = None,
) -> UploadSession:
    if state in {
        UploadSessionState.RECEIVED,
        UploadSessionState.VALIDATING,
        UploadSessionState.DUPLICATE_PENDING,
        UploadSessionState.PUBLISH_PENDING,
        UploadSessionState.PUBLISHED,
        UploadSessionState.CATALOGED,
        UploadSessionState.REJECTED,
    } and received_size_bytes == 0:
        received_size_bytes = declared_size_bytes
    if state in VALIDATED_UPLOAD_SESSION_STATES:
        checksum_hex = checksum_hex or "a" * 64
        validated_media_kind = validated_media_kind or UploadValidatedMediaKind.VIDEO
        validated_format = validated_format or UploadValidatedFormat.MP4
    return UploadSession(
        id=session_id or UploadSessionId.new(),
        state=state,
        storage_key=UploadStorageKey(storage_key),
        display_filename=UploadDisplayFilename("example.mp4"),
        declared_size_bytes=declared_size_bytes,
        received_size_bytes=received_size_bytes,
        checksum_algorithm=None if checksum_hex is None else "sha256",
        checksum_hex=checksum_hex,
        created_at_ms=10,
        updated_at_ms=10,
        expires_at_ms=1000,
        failure_code=None,
        version=version,
        validated_media_kind=validated_media_kind,
        validated_format=validated_format,
    )


def test_create_and_get_round_trip(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session()
    try:
        repository.create(session)

        loaded = repository.get(session.id)
    finally:
        engine.dispose()

    assert loaded == session


def test_create_rejects_duplicate_session_id_and_storage_key(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session()
    try:
        repository.create(session)
        with pytest.raises(UploadSessionAlreadyExistsError):
            repository.create(_session(session_id=session.id, storage_key="upload-session-0002"))
        with pytest.raises(UploadStorageKeyAlreadyExistsError):
            repository.create(_session(storage_key=session.storage_key.value))
    finally:
        engine.dispose()


def test_advance_received_offset_is_exact_guarded_and_versioned(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING)
    try:
        repository.create(session)

        advanced = repository.advance_received_offset(
            session.id,
            expected_received_size_bytes=0,
            accepted_size_bytes=25,
            expected_version=0,
            updated_at_ms=20,
        )
    finally:
        engine.dispose()

    assert advanced.received_size_bytes == 25
    assert advanced.version == 1
    assert advanced.updated_at_ms == 20
    assert advanced.state == UploadSessionState.RECEIVING


def test_advance_received_offset_distinguishes_guard_failures(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    missing_id = UploadSessionId.new()
    wrong_state = _session(storage_key="upload-session-0002", state=UploadSessionState.CREATED)
    receiving = _session(
        storage_key="upload-session-0003",
        state=UploadSessionState.RECEIVING,
        received_size_bytes=10,
        declared_size_bytes=20,
        version=2,
    )
    try:
        repository.create(wrong_state)
        repository.create(receiving)

        with pytest.raises(UploadSessionNotFoundError):
            repository.advance_received_offset(
                missing_id,
                expected_received_size_bytes=0,
                accepted_size_bytes=1,
                expected_version=0,
                updated_at_ms=11,
            )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.advance_received_offset(
                wrong_state.id,
                expected_received_size_bytes=0,
                accepted_size_bytes=1,
                expected_version=0,
                updated_at_ms=11,
            )
        with pytest.raises(UploadOffsetConflictError):
            repository.advance_received_offset(
                receiving.id,
                expected_received_size_bytes=9,
                accepted_size_bytes=1,
                expected_version=2,
                updated_at_ms=11,
            )
        with pytest.raises(UploadSessionConcurrencyConflictError):
            repository.advance_received_offset(
                receiving.id,
                expected_received_size_bytes=10,
                accepted_size_bytes=1,
                expected_version=1,
                updated_at_ms=11,
            )
        with pytest.raises(UploadSizeLimitExceededError):
            repository.advance_received_offset(
                receiving.id,
                expected_received_size_bytes=10,
                accepted_size_bytes=11,
                expected_version=2,
                updated_at_ms=11,
            )
    finally:
        engine.dispose()


def test_failed_guarded_offset_update_rolls_back(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING, received_size_bytes=10, version=2)
    try:
        repository.create(session)
        with pytest.raises(UploadSessionConcurrencyConflictError):
            repository.advance_received_offset(
                session.id,
                expected_received_size_bytes=10,
                accepted_size_bytes=5,
                expected_version=99,
                updated_at_ms=30,
            )

        loaded = repository.get(session.id)
    finally:
        engine.dispose()

    assert loaded == session


def test_transition_state_persists_and_rejects_invalid_or_terminal_paths(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING, received_size_bytes=100)
    try:
        repository.create(session)
        received = repository.transition_state(
            session.id,
            expected_state=UploadSessionState.RECEIVING,
            target_state=UploadSessionState.RECEIVED,
            expected_version=0,
            updated_at_ms=20,
        )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.RECEIVED,
                target_state=UploadSessionState.PUBLISHED,
                expected_version=1,
                updated_at_ms=21,
            )
        cataloged = repository.transition_state(
            _create_at_state(
                repository,
                storage_key="upload-session-0004",
                state=UploadSessionState.PUBLISHED,
            ).id,
            expected_state=UploadSessionState.PUBLISHED,
            target_state=UploadSessionState.CATALOGED,
            expected_version=0,
            updated_at_ms=22,
        )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.transition_state(
                cataloged.id,
                expected_state=UploadSessionState.CATALOGED,
                target_state=UploadSessionState.FAILED,
                expected_version=1,
                updated_at_ms=23,
            )
    finally:
        engine.dispose()

    assert received.state == UploadSessionState.RECEIVED
    assert received.version == 1
    assert cataloged.state == UploadSessionState.CATALOGED


def test_transition_state_distinguishes_not_found_wrong_state_and_stale_version(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.CREATED)
    try:
        repository.create(session)
        with pytest.raises(UploadSessionNotFoundError):
            repository.transition_state(
                UploadSessionId.new(),
                expected_state=UploadSessionState.CREATED,
                target_state=UploadSessionState.RECEIVING,
                expected_version=0,
                updated_at_ms=20,
            )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.RECEIVING,
                target_state=UploadSessionState.RECEIVED,
                expected_version=0,
                updated_at_ms=20,
            )
        with pytest.raises(UploadSessionConcurrencyConflictError):
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.CREATED,
                target_state=UploadSessionState.RECEIVING,
                expected_version=99,
                updated_at_ms=20,
            )
    finally:
        engine.dispose()


def test_incomplete_receiving_to_received_fails_without_mutating_row(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING, received_size_bytes=25, version=2)
    try:
        repository.create(session)
        with pytest.raises(IncompleteUploadSessionError) as error:
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.RECEIVING,
                target_state=UploadSessionState.RECEIVED,
                expected_version=2,
                updated_at_ms=99,
            )

        loaded = repository.get(session.id)
    finally:
        engine.dispose()

    assert loaded == session
    assert str(error.value) == "incomplete upload session"


def test_complete_receiving_to_received_succeeds(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING, received_size_bytes=100)
    try:
        repository.create(session)
        received = repository.transition_state(
            session.id,
            expected_state=UploadSessionState.RECEIVING,
            target_state=UploadSessionState.RECEIVED,
            expected_version=0,
            updated_at_ms=20,
        )
    finally:
        engine.dispose()

    assert received.state == UploadSessionState.RECEIVED
    assert received.received_size_bytes == received.declared_size_bytes
    assert received.version == 1


def test_stale_version_takes_precedence_over_incomplete_upload(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVING, received_size_bytes=25, version=2)
    try:
        repository.create(session)
        with pytest.raises(UploadSessionConcurrencyConflictError):
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.RECEIVING,
                target_state=UploadSessionState.RECEIVED,
                expected_version=1,
                updated_at_ms=99,
            )
    finally:
        engine.dispose()


def test_wrong_state_takes_precedence_over_incomplete_upload(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.CANCELLED, received_size_bytes=25)
    try:
        repository.create(session)
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.transition_state(
                session.id,
                expected_state=UploadSessionState.RECEIVING,
                target_state=UploadSessionState.RECEIVED,
                expected_version=0,
                updated_at_ms=99,
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (UploadSessionState.RECEIVED, UploadSessionState.VALIDATING),
        (UploadSessionState.VALIDATING, UploadSessionState.DUPLICATE_PENDING),
        (UploadSessionState.VALIDATING, UploadSessionState.PUBLISH_PENDING),
        (UploadSessionState.VALIDATING, UploadSessionState.REJECTED),
        (UploadSessionState.DUPLICATE_PENDING, UploadSessionState.PUBLISH_PENDING),
        (UploadSessionState.PUBLISH_PENDING, UploadSessionState.PUBLISHED),
        (UploadSessionState.PUBLISHED, UploadSessionState.CATALOGED),
    ],
)
def test_later_complete_target_transitions_reject_incomplete_persisted_rows(
    tmp_path: Path,
    source: UploadSessionState,
    target: UploadSessionState,
) -> None:
    repository, engine = _repository(tmp_path)
    session_id = UploadSessionId.new()
    try:
        _insert_raw_upload_session(
            engine,
            session_id=session_id,
            storage_key=f"upload-session-{source.value.replace('_', '-')}",
            state=source,
            declared_size_bytes=100,
            received_size_bytes=25,
            version=0,
        )
        with pytest.raises(IncompleteUploadSessionError):
            repository.transition_state(
                session_id,
                expected_state=source,
                target_state=target,
                expected_version=0,
                updated_at_ms=99,
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (UploadSessionState.RECEIVED, UploadSessionState.VALIDATING),
        (UploadSessionState.VALIDATING, UploadSessionState.DUPLICATE_PENDING),
        (UploadSessionState.VALIDATING, UploadSessionState.PUBLISH_PENDING),
        (UploadSessionState.VALIDATING, UploadSessionState.REJECTED),
        (UploadSessionState.DUPLICATE_PENDING, UploadSessionState.PUBLISH_PENDING),
        (UploadSessionState.PUBLISH_PENDING, UploadSessionState.PUBLISHED),
        (UploadSessionState.PUBLISHED, UploadSessionState.CATALOGED),
    ],
)
def test_valid_complete_rows_continue_through_transition_graph(
    tmp_path: Path,
    source: UploadSessionState,
    target: UploadSessionState,
) -> None:
    repository, engine = _repository(tmp_path)
    evidence_kwargs: dict[str, object] = {}
    if target in VALIDATED_UPLOAD_SESSION_STATES:
        evidence_kwargs = {
            "checksum_hex": "a" * 64,
            "validated_media_kind": UploadValidatedMediaKind.VIDEO,
            "validated_format": UploadValidatedFormat.MP4,
        }
    session = _session(
        storage_key=f"upload-session-valid-{source.value.replace('_', '-')}",
        state=source,
        received_size_bytes=100,
        **evidence_kwargs,
    )
    try:
        repository.create(session)
        transitioned = repository.transition_state(
            session.id,
            expected_state=source,
            target_state=target,
            expected_version=0,
            updated_at_ms=20,
        )
    finally:
        engine.dispose()

    assert transitioned.state == target
    assert transitioned.received_size_bytes == transitioned.declared_size_bytes
    assert transitioned.version == 1


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (UploadSessionState.VALIDATING, UploadSessionState.DUPLICATE_PENDING),
        (UploadSessionState.VALIDATING, UploadSessionState.PUBLISH_PENDING),
    ],
)
def test_transition_state_rejects_advanced_targets_without_validation_evidence(
    tmp_path: Path,
    source: UploadSessionState,
    target: UploadSessionState,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(
        storage_key=f"upload-session-missing-evidence-{target.value.replace('_', '-')}",
        state=source,
        received_size_bytes=100,
    )
    try:
        repository.create(session)
        with pytest.raises(InvalidUploadValidationEvidenceError):
            repository.transition_state(
                session.id,
                expected_state=source,
                target_state=target,
                expected_version=0,
                updated_at_ms=20,
            )
    finally:
        engine.dispose()


def test_record_completed_checksum_is_guarded_and_idempotent_for_same_digest(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVED)
    digest = "a" * 64
    try:
        repository.create(session)
        recorded = repository.record_completed_checksum(
            session.id,
            expected_state=UploadSessionState.RECEIVED,
            expected_version=0,
            checksum_hex=digest,
            updated_at_ms=20,
        )
        repeated = repository.record_completed_checksum(
            session.id,
            expected_state=UploadSessionState.RECEIVED,
            expected_version=1,
            checksum_hex=digest,
            updated_at_ms=21,
        )
        with pytest.raises(InvalidUploadChecksumError):
            repository.record_completed_checksum(
                session.id,
                expected_state=UploadSessionState.RECEIVED,
                expected_version=1,
                checksum_hex="b" * 64,
                updated_at_ms=22,
            )
    finally:
        engine.dispose()

    assert recorded.checksum_algorithm == "sha256"
    assert recorded.checksum_hex == digest
    assert recorded.version == 1
    assert repeated == recorded


def test_record_completed_checksum_rejects_invalid_state_version_and_digest(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVED)
    try:
        repository.create(session)
        with pytest.raises(InvalidUploadChecksumError):
            repository.record_completed_checksum(
                session.id,
                expected_state=UploadSessionState.RECEIVED,
                expected_version=0,
                checksum_hex="A" * 64,
                updated_at_ms=20,
            )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.record_completed_checksum(
                session.id,
                expected_state=UploadSessionState.VALIDATING,
                expected_version=0,
                checksum_hex="a" * 64,
                updated_at_ms=20,
            )
        with pytest.raises(UploadSessionConcurrencyConflictError):
            repository.record_completed_checksum(
                session.id,
                expected_state=UploadSessionState.RECEIVED,
                expected_version=99,
                checksum_hex="a" * 64,
                updated_at_ms=20,
            )
    finally:
        engine.dispose()


def test_start_validation_transitions_received_to_validating(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.RECEIVED)
    try:
        repository.create(session)
        validating = repository.start_validation(
            session.id,
            expected_version=0,
            updated_at_ms=20,
        )
    finally:
        engine.dispose()

    assert validating.state is UploadSessionState.VALIDATING
    assert validating.version == 1


def test_complete_validation_success_commits_evidence_and_publish_state_atomically(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.VALIDATING)
    digest = "b" * 64
    try:
        repository.create(session)
        completed = repository.complete_validation_success(
            session.id,
            expected_version=0,
            checksum_hex=digest,
            validated_media_kind=UploadValidatedMediaKind.ANIMATED_IMAGE,
            validated_format=UploadValidatedFormat.GIF,
            updated_at_ms=20,
        )
        repeated = repository.complete_validation_success(
            session.id,
            expected_version=1,
            checksum_hex=digest,
            validated_media_kind=UploadValidatedMediaKind.ANIMATED_IMAGE,
            validated_format=UploadValidatedFormat.GIF,
            updated_at_ms=21,
        )
        with pytest.raises(InvalidUploadValidationEvidenceError):
            repository.complete_validation_success(
                session.id,
                expected_version=1,
                checksum_hex=digest,
                validated_media_kind=UploadValidatedMediaKind.VIDEO,
                validated_format=UploadValidatedFormat.MP4,
                updated_at_ms=22,
            )
    finally:
        engine.dispose()

    assert completed.state is UploadSessionState.PUBLISH_PENDING
    assert completed.checksum_algorithm == "sha256"
    assert completed.checksum_hex == digest
    assert completed.validated_media_kind is UploadValidatedMediaKind.ANIMATED_IMAGE
    assert completed.validated_format is UploadValidatedFormat.GIF
    assert repeated == completed


def test_reject_validation_commits_sanitized_code_and_rejected_state(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    session = _session(state=UploadSessionState.VALIDATING)
    try:
        repository.create(session)
        rejected = repository.reject_validation(
            session.id,
            expected_version=0,
            failure_code="UNSUPPORTED_MEDIA_TYPE",
            updated_at_ms=20,
        )
    finally:
        engine.dispose()

    assert rejected.state is UploadSessionState.REJECTED
    assert rejected.failure_code == "UNSUPPORTED_MEDIA_TYPE"
    assert rejected.checksum_hex is None
    assert rejected.validated_media_kind is None


def test_failure_code_is_sanitized_and_only_allowed_for_failure_states(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    failed = _session(storage_key="upload-session-0005", state=UploadSessionState.RECEIVING)
    invalid = _session(storage_key="upload-session-0006", state=UploadSessionState.CREATED)
    try:
        repository.create(failed)
        repository.create(invalid)
        stored = repository.transition_state(
            failed.id,
            expected_state=UploadSessionState.RECEIVING,
            target_state=UploadSessionState.FAILED,
            expected_version=0,
            updated_at_ms=20,
            failure_code="NETWORK_TIMEOUT",
        )
        with pytest.raises(InvalidUploadSessionTransitionError):
            repository.transition_state(
                invalid.id,
                expected_state=UploadSessionState.CREATED,
                target_state=UploadSessionState.RECEIVING,
                expected_version=0,
                updated_at_ms=20,
                failure_code="NOT_ALLOWED",
            )
    finally:
        engine.dispose()

    assert stored.failure_code == "NETWORK_TIMEOUT"


def test_no_absolute_path_can_be_persisted_in_upload_sessions(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with pytest.raises(Exception):
            repository.create(_session(storage_key="/absolute/file.mp4"))
        with pytest.raises(Exception):
            repository.create(
                _session(
                    storage_key="upload-session-0007",
                    state=UploadSessionState.CREATED,
                )
            )
            with engine.begin() as connection:
                connection.execute(
                    sa.text(
                        "UPDATE upload_sessions "
                        "SET display_filename = '/absolute/file.mp4' "
                        "WHERE storage_key = 'upload-session-0007'"
                    )
                )
    finally:
        engine.dispose()


def test_upload_session_repository_does_not_access_media_files_or_providers() -> None:
    tree = ast.parse(UPLOAD_REPOSITORY_MODULE.read_text(encoding="utf-8"))
    forbidden_imports = {"openai", "requests", "httpx", "PIL", "subprocess"}
    forbidden_calls = {"open", "read_bytes", "write_bytes", "rename", "replace", "unlink"}
    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    assert sorted(set(imports) & forbidden_imports) == []
    assert sorted(set(calls) & forbidden_calls) == []
    assert "logical_media" not in UPLOAD_REPOSITORY_MODULE.read_text(encoding="utf-8")
    assert "media_metadata" not in UPLOAD_REPOSITORY_MODULE.read_text(encoding="utf-8")


def _create_at_state(
    repository: SqliteUploadSessionRepository,
    *,
    storage_key: str,
    state: UploadSessionState,
) -> UploadSession:
    session = _session(storage_key=storage_key, state=state)
    repository.create(session)
    return session


def _insert_raw_upload_session(
    engine: sa.Engine,
    *,
    session_id: UploadSessionId,
    storage_key: str,
    state: UploadSessionState,
    declared_size_bytes: int,
    received_size_bytes: int,
    version: int,
) -> None:
    with engine.begin() as connection:
        connection.execute(sa.text("PRAGMA ignore_check_constraints=ON"))
        connection.execute(
            sa.text(
                """
                INSERT INTO upload_sessions (
                    id,
                    state,
                    storage_key,
                    display_filename,
                    declared_size_bytes,
                    received_size_bytes,
                    checksum_algorithm,
                    checksum_hex,
                    created_at_ms,
                    updated_at_ms,
                    expires_at_ms,
                    failure_code,
                    version
                ) VALUES (
                    :id,
                    :state,
                    :storage_key,
                    'example.mp4',
                    :declared_size_bytes,
                    :received_size_bytes,
                    NULL,
                    NULL,
                    10,
                    10,
                    1000,
                    NULL,
                    :version
                )
                """
            ),
            {
                "id": session_id.to_string(),
                "state": state.value,
                "storage_key": storage_key,
                "declared_size_bytes": declared_size_bytes,
                "received_size_bytes": received_size_bytes,
                "version": version,
            },
        )
        connection.execute(sa.text("PRAGMA ignore_check_constraints=OFF"))
