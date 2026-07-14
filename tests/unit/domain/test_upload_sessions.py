"""Unit tests for pure-domain upload sessions."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from framenest.domain.uploads import (
    ALLOWED_UPLOAD_SESSION_TRANSITIONS,
    FrameNestUploadChecksumError,
    FrameNestUploadOffsetError,
    FrameNestUploadSessionError,
    FrameNestUploadSessionTransitionError,
    TERMINAL_UPLOAD_SESSION_STATES,
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
    ensure_upload_session_transition_allowed,
    is_terminal_upload_session_state,
    validate_sha256_checksum_hex,
    validate_upload_offset_advance,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_UPLOADS_MODULE = REPOSITORY_ROOT / "src" / "framenest" / "domain" / "uploads.py"


def _session(**overrides: object) -> UploadSession:
    values: dict[str, object] = {
        "id": UploadSessionId.new(),
        "state": UploadSessionState.CREATED,
        "storage_key": UploadStorageKey("upload-session-0001"),
        "display_filename": UploadDisplayFilename("example.mp4"),
        "declared_size_bytes": 100,
        "received_size_bytes": 0,
        "checksum_algorithm": None,
        "checksum_hex": None,
        "created_at_ms": 10,
        "updated_at_ms": 10,
        "expires_at_ms": 20,
        "failure_code": None,
        "version": 0,
    }
    values.update(overrides)
    return UploadSession(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (source, target)
        for source, targets in ALLOWED_UPLOAD_SESSION_TRANSITIONS.items()
        for target in targets
    ],
)
def test_every_allowed_transition_is_accepted(
    source: UploadSessionState,
    target: UploadSessionState,
) -> None:
    ensure_upload_session_transition_allowed(source, target)


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (UploadSessionState.CREATED, UploadSessionState.RECEIVED),
        (UploadSessionState.RECEIVING, UploadSessionState.PUBLISHED),
        (UploadSessionState.VALIDATING, UploadSessionState.CATALOGED),
        (UploadSessionState.PUBLISHED, UploadSessionState.FAILED),
    ],
)
def test_representative_forbidden_transitions_are_rejected(
    source: UploadSessionState,
    target: UploadSessionState,
) -> None:
    with pytest.raises(FrameNestUploadSessionTransitionError):
        ensure_upload_session_transition_allowed(source, target)


@pytest.mark.parametrize("terminal", sorted(TERMINAL_UPLOAD_SESSION_STATES, key=str))
def test_terminal_states_have_no_outgoing_transitions(terminal: UploadSessionState) -> None:
    assert is_terminal_upload_session_state(terminal)
    assert ALLOWED_UPLOAD_SESSION_TRANSITIONS[terminal] == frozenset()
    for target in UploadSessionState:
        with pytest.raises(FrameNestUploadSessionTransitionError):
            ensure_upload_session_transition_allowed(terminal, target)


def test_published_transitions_only_to_cataloged_not_failed() -> None:
    ensure_upload_session_transition_allowed(
        UploadSessionState.PUBLISHED,
        UploadSessionState.CATALOGED,
    )
    with pytest.raises(FrameNestUploadSessionTransitionError):
        ensure_upload_session_transition_allowed(
            UploadSessionState.PUBLISHED,
            UploadSessionState.FAILED,
        )


@pytest.mark.parametrize(
    ("declared", "received"),
    [(0, 0), (-1, 0), (100, -1), (100, 101), (True, 0), (100, True)],
)
def test_size_invariants_are_enforced(declared: Any, received: Any) -> None:
    with pytest.raises(FrameNestUploadSessionError):
        _session(declared_size_bytes=declared, received_size_bytes=received)


@pytest.mark.parametrize(
    ("current", "accepted", "declared", "expected"),
    [(0, 1, 10, 1), (5, 5, 10, 10)],
)
def test_valid_offset_advance_returns_next_offset(
    current: int,
    accepted: int,
    declared: int,
    expected: int,
) -> None:
    assert (
        validate_upload_offset_advance(
            current_offset=current,
            accepted_bytes=accepted,
            declared_size_bytes=declared,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("current", "accepted", "declared"),
    [(-1, 1, 10), (0, 0, 10), (0, -1, 10), (9, 2, 10)],
)
def test_invalid_offset_advance_is_rejected(
    current: int,
    accepted: int,
    declared: int,
) -> None:
    with pytest.raises((FrameNestUploadOffsetError, FrameNestUploadSessionError)):
        validate_upload_offset_advance(
            current_offset=current,
            accepted_bytes=accepted,
            declared_size_bytes=declared,
        )


def test_checksum_validation_accepts_only_lowercase_sha256_hex() -> None:
    digest = "a" * 64

    assert validate_sha256_checksum_hex(digest) == digest
    _session(checksum_algorithm="sha256", checksum_hex=digest)

    for invalid in ("A" * 64, "g" * 64, "a" * 63, None, 1):
        with pytest.raises(FrameNestUploadChecksumError):
            validate_sha256_checksum_hex(invalid)
        with pytest.raises(FrameNestUploadChecksumError):
            _session(checksum_algorithm="sha256", checksum_hex=invalid)


def test_checksum_pair_is_absent_before_known() -> None:
    session = _session()

    assert session.checksum_algorithm is None
    assert session.checksum_hex is None

    with pytest.raises(FrameNestUploadChecksumError):
        _session(checksum_algorithm="sha256", checksum_hex=None)
    with pytest.raises(FrameNestUploadChecksumError):
        _session(checksum_algorithm=None, checksum_hex="a" * 64)


def test_storage_key_is_opaque_and_display_filename_is_not_a_storage_path() -> None:
    session = _session(
        storage_key=UploadStorageKey("serverownedkey001"),
        display_filename=UploadDisplayFilename("Family Clip.mp4"),
    )

    assert session.storage_key.value == "serverownedkey001"
    assert session.display_filename.value == "Family Clip.mp4"

    for rejected_key in ("/absolute/file.mp4", "clips/file.mp4", "C:\\media\\file.mp4"):
        with pytest.raises(FrameNestUploadSessionError):
            UploadStorageKey(rejected_key)
    for rejected_name in ("/absolute/file.mp4", "clips/file.mp4", "C:\\media\\file.mp4"):
        with pytest.raises(FrameNestUploadSessionError):
            UploadDisplayFilename(rejected_name)


def test_expiration_must_be_later_than_creation() -> None:
    with pytest.raises(FrameNestUploadSessionError):
        _session(created_at_ms=10, expires_at_ms=10)


def test_upload_domain_module_imports_no_infrastructure_or_framework() -> None:
    tree = ast.parse(DOMAIN_UPLOADS_MODULE.read_text(encoding="utf-8"))
    forbidden_roots = {
        "alembic",
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "starlette",
        "uvicorn",
        "framenest.infrastructure",
        "framenest.application",
        "framenest.adapters",
        "framenest.configuration",
    }
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            module = node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
        else:
            continue
        root = module.split(".")[0]
        if root in forbidden_roots or any(module.startswith(prefix) for prefix in forbidden_roots):
            violations.append(module)
    assert violations == []
