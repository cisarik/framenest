"""Unit tests for internal upload-validation use case."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from framenest.application.ports.upload_media_validation import (
    UploadMediaValidationEvidence,
    UploadMediaValidationRejectedError,
)
from framenest.application.upload_validation import (
    UPLOAD_VALIDATION_INTERNAL_ERROR,
    UPLOAD_VALIDATION_QUARANTINE_INCONSISTENT,
    UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE,
    UploadValidationQuarantineInconsistentError,
    UploadValidationUnavailableError,
    ValidateReceivedUpload,
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
)
from framenest.infrastructure.filesystem.quarantine_storage import FilesystemQuarantineStorage
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.upload_session_repository import (
    SqliteUploadSessionRepository,
)
from framenest.application.ports.upload_sessions import FrameNestUploadSessionRepositoryError


class _Validator:
    def __init__(
        self,
        evidence: UploadMediaValidationEvidence | None = None,
        rejection_code: str | None = None,
        on_validate=None,
    ) -> None:
        self._evidence = evidence or UploadMediaValidationEvidence(
            UploadValidatedMediaKind.VIDEO,
            UploadValidatedFormat.MP4,
        )
        self._rejection_code = rejection_code
        self._on_validate = on_validate
        self.calls = 0

    def validate(self, reader):
        self.calls += 1
        if self._on_validate is not None:
            self._on_validate(reader)
        if self._rejection_code is not None:
            raise UploadMediaValidationRejectedError(self._rejection_code)
        return self._evidence


def _setup(
    tmp_path: Path,
    *,
    payload: bytes = b"uploaded-bytes",
    state: UploadSessionState = UploadSessionState.RECEIVED,
    validator: _Validator | None = None,
):
    database_path = tmp_path / "catalog.sqlite3"
    quarantine_root = tmp_path / "quarantine"
    quarantine_root.mkdir()
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    engine = create_sqlite_engine(database_path)
    repository = SqliteUploadSessionRepository(engine)
    storage = FilesystemQuarantineStorage(quarantine_root)
    session = UploadSession(
        id=UploadSessionId.new(),
        state=state,
        storage_key=UploadStorageKey("validationupload0001"),
        display_filename=UploadDisplayFilename("client-name.mp4"),
        declared_size_bytes=len(payload),
        received_size_bytes=len(payload),
        checksum_algorithm=None,
        checksum_hex=None,
        created_at_ms=10,
        updated_at_ms=10,
        expires_at_ms=10_000,
        failure_code=None,
        version=0,
    )
    repository.create(session)
    path = quarantine_root / f"{session.storage_key.value}.part"
    path.write_bytes(payload)
    service = ValidateReceivedUpload(
        repository,
        storage,
        validator or _Validator(),
        now_ms=lambda: 20,
    )
    return service, repository, engine, session, path


def test_success_persists_checksum_validation_evidence_and_no_catalog_visibility(
    tmp_path: Path,
) -> None:
    service, repository, engine, session, _path = _setup(tmp_path)
    try:
        result = asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
        with sqlite3.connect(tmp_path / "catalog.sqlite3") as connection:
            logical_count = connection.execute("SELECT COUNT(*) FROM logical_media").fetchone()
            location_count = connection.execute(
                "SELECT COUNT(*) FROM physical_media_locations"
            ).fetchone()
    finally:
        dispose_engine(engine)

    assert result.state == UploadSessionState.PUBLISH_PENDING.value
    assert result.checksum_algorithm == "sha256"
    assert result.checksum_hex is not None and len(result.checksum_hex) == 64
    assert result.validated_media_kind == "video"
    assert result.validated_format == "mp4"
    assert stored is not None
    assert stored.state is UploadSessionState.PUBLISH_PENDING
    assert logical_count == (0,)
    assert location_count == (0,)


def test_permanent_policy_rejection_records_sanitized_code(tmp_path: Path) -> None:
    service, repository, engine, session, _path = _setup(
        tmp_path,
        validator=_Validator(rejection_code=UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE),
    )
    try:
        result = asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
    finally:
        dispose_engine(engine)

    assert result.state == UploadSessionState.REJECTED.value
    assert result.failure_code == UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE
    assert stored is not None
    assert stored.checksum_hex is None
    assert stored.validated_media_kind is None


def test_matching_publish_pending_result_is_idempotent_without_reprobe(tmp_path: Path) -> None:
    validator = _Validator()
    service, repository, engine, session, _path = _setup(tmp_path, validator=validator)
    try:
        first = asyncio.run(service.validate(session.id))
        second = asyncio.run(service.validate(session.id))
    finally:
        dispose_engine(engine)

    assert first == second
    assert validator.calls == 1


def test_path_replacement_after_open_does_not_split_hash_and_probe_object(
    tmp_path: Path,
) -> None:
    def replace_path(_reader) -> None:
        path.unlink()
        path.write_bytes(b"replacement!")

    service, repository, engine, session, path = _setup(
        tmp_path,
        payload=b"original!!!!",
        validator=_Validator(on_validate=replace_path),
    )
    try:
        result = asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
    finally:
        dispose_engine(engine)

    assert result.state == UploadSessionState.PUBLISH_PENDING.value
    assert stored is not None
    assert stored.checksum_hex == result.checksum_hex


def test_in_place_object_mutation_is_detected_before_success_persistence(
    tmp_path: Path,
) -> None:
    def mutate_open_object(reader) -> None:
        path.write_bytes(b"mutated-bytes")
        reader.seek_start()

    service, repository, engine, session, path = _setup(
        tmp_path,
        payload=b"original-bytes",
        validator=_Validator(on_validate=mutate_open_object),
    )
    try:
        with pytest.raises(UploadValidationQuarantineInconsistentError):
            asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
    finally:
        dispose_engine(engine)

    assert stored is not None
    assert stored.state is UploadSessionState.FAILED
    assert stored.failure_code == UPLOAD_VALIDATION_QUARANTINE_INCONSISTENT


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("raw-private-validator-detail /tmp/private"),
        OverflowError("raw overflow detail"),
        RuntimeError("raw arbitrary detail"),
    ],
)
def test_unexpected_validator_exception_records_sanitized_internal_failure(
    tmp_path: Path,
    exception: Exception,
) -> None:
    def raise_unexpected(_reader) -> None:
        raise exception

    service, repository, engine, session, _path = _setup(
        tmp_path,
        validator=_Validator(on_validate=raise_unexpected),
    )
    try:
        with pytest.raises(UploadValidationUnavailableError) as error:
            asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
    finally:
        dispose_engine(engine)

    assert str(error.value) == "upload validation unavailable"
    assert "raw" not in str(error.value)
    assert error.value.__cause__ is None
    assert stored is not None
    assert stored.state is UploadSessionState.FAILED
    assert stored.failure_code == UPLOAD_VALIDATION_INTERNAL_ERROR


def test_unexpected_validator_failure_recording_failure_stays_sanitized_and_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_unexpected(_reader) -> None:
        raise ValueError("raw-private-validator-detail")

    service, repository, engine, session, _path = _setup(
        tmp_path,
        validator=_Validator(on_validate=raise_unexpected),
    )

    def fail_transition(*_args: object, **_kwargs: object) -> object:
        raise FrameNestUploadSessionRepositoryError("raw repository detail")

    monkeypatch.setattr(repository, "transition_state", fail_transition)
    try:
        with pytest.raises(UploadValidationUnavailableError) as error:
            asyncio.run(service.validate(session.id))
        stored = repository.get(session.id)
    finally:
        dispose_engine(engine)

    assert str(error.value) == "upload validation unavailable"
    assert error.value.__cause__ is None
    assert stored is not None
    assert stored.state is UploadSessionState.VALIDATING
    assert stored.failure_code is None
