"""Repository transactions for documents: rollback and invalid persisted JSON."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from framenest.configuration import FrameNestSettings
from framenest.domain.identity_access import ROLE_USER
from framenest.application.records import RecordService
from framenest.domain.identity_access import ROLE_ADMIN
from framenest.domain.records import (
    CompletedDocument,
    DocumentId,
    RecordConflictError,
    RecordId,
    RecordKind,
    RecordStorageIntegrityError,
)
from framenest.domain.research import CompletionEvidence
from framenest.infrastructure.persistence.engine import (
    create_sqlite_engine,
    dispose_engine,
    run_in_immediate_transaction,
)
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.record_repository import SqliteRecordRepository
from tests.support.record_access import synthetic_identity


def _engine(tmp_path: Path):
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    return create_sqlite_engine(settings.database_path)


def _document(operation_id: str) -> CompletedDocument:
    return CompletedDocument(
        document_id=DocumentId.new(),
        operation_id=operation_id,
        kind=RecordKind.SEARCH,
        question_text="Question",
        answer_text="Answer",
        citations=(),
        evidence=CompletionEvidence(
            provider_terminal=True,
            answer_complete=True,
            web_search_executed=True,
            refusal_marker=False,
            incomplete_marker=False,
        ),
        created_at_ms=1,
        completed_at_ms=2,
    )


def test_document_insert_rolls_back_with_the_caller_transaction(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    repository = SqliteRecordRepository(engine)
    document = _document("search-op-rollback")
    try:
        def operation(connection) -> None:
            connection.exec_driver_sql(
                "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
                "VALUES ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'video', 1, 1)"
            )
            repository.bind_media_record(
                connection,
                record_id=RecordId.new(),
                media_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                owner_login_key="alice",
                created_at_ms=1,
            )
            raise RuntimeError("injected failure")

        with pytest.raises(RuntimeError, match="injected failure"):
            run_in_immediate_transaction(engine, operation)
        connection = sqlite3.connect(tmp_path / "catalog.sqlite3")
        try:
            count = connection.execute("SELECT COUNT(*) FROM kronika_records").fetchone()[0]
        finally:
            connection.close()
        assert count == 0
        created = repository.create_completed_document(
            document,
            owner_login_key="alice",
            record_id=RecordId.new(),
        )
        assert created.document is not None
    finally:
        dispose_engine(engine)


def test_invalid_persisted_document_fails_closed(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    repository = SqliteRecordRepository(engine)
    document = _document("search-op-invalid")
    try:
        created = repository.create_completed_document(
            document,
            owner_login_key="alice",
            record_id=RecordId.new(),
        )
        connection = sqlite3.connect(tmp_path / "catalog.sqlite3")
        try:
            connection.execute(
                "UPDATE kronika_documents SET citations_json = ? WHERE operation_id = ?",
                ("not-json", document.operation_id),
            )
            connection.commit()
        finally:
            connection.close()
        with pytest.raises(RecordStorageIntegrityError):
            repository.read_detail(
                synthetic_identity("alice", role=ROLE_USER),
                created.summary.record_id,
            )
    finally:
        dispose_engine(engine)


def test_stale_version_and_digest_leave_no_partial_approval(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = RecordService(SqliteRecordRepository(engine))
    alice = synthetic_identity("alice", role=ROLE_USER)
    admin = synthetic_identity("ada", role=ROLE_ADMIN)
    try:
        created = service.create_completed_document(
            alice, _document("search-op-stale")
        )
        candidate = service.prepare_approval(admin, created.summary.record_id)
        connection = sqlite3.connect(tmp_path / "catalog.sqlite3")
        try:
            connection.execute(
                "UPDATE kronika_documents SET answer_text = ? WHERE operation_id = ?",
                ("Changed before approval", "search-op-stale"),
            )
            connection.commit()
        finally:
            connection.close()
        with pytest.raises(RecordConflictError):
            service.approve(admin, candidate, approved_at_ms=8)
        connection = sqlite3.connect(tmp_path / "catalog.sqlite3")
        try:
            stored = connection.execute(
                "SELECT approved_projection_json, version FROM kronika_records"
            ).fetchone()
        finally:
            connection.close()
        assert stored[0] is None
        fresh = service.prepare_approval(admin, created.summary.record_id)
        approved = service.approve(admin, fresh, approved_at_ms=9)
        with pytest.raises(RecordConflictError):
            service.withdraw(
                admin,
                record_id=created.summary.record_id,
                expected_version=approved.version - 1,
            )
        assert service.list_timeline(alice).items[0].timeline_entered_at_ms == 9
    finally:
        dispose_engine(engine)


def test_racing_approve_and_withdraw_keep_one_consistent_state(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = RecordService(SqliteRecordRepository(engine))
    alice = synthetic_identity("alice", role=ROLE_USER)
    admin = synthetic_identity("ada", role=ROLE_ADMIN)
    try:
        created = service.create_completed_document(
            alice, _document("search-op-race")
        )
        candidate = service.prepare_approval(admin, created.summary.record_id)
        approved = service.approve(admin, candidate, approved_at_ms=9)
        barrier = threading.Barrier(2)
        outcomes: list[str] = []

        def approve_again() -> None:
            barrier.wait()
            try:
                service.approve(admin, candidate, approved_at_ms=12)
                outcomes.append("approve")
            except RecordConflictError:
                outcomes.append("approve-conflict")

        def withdraw() -> None:
            barrier.wait()
            try:
                service.withdraw(
                    admin,
                    record_id=created.summary.record_id,
                    expected_version=approved.version,
                )
                outcomes.append("withdraw")
            except RecordConflictError:
                outcomes.append("withdraw-conflict")

        threads = (
            threading.Thread(target=approve_again),
            threading.Thread(target=withdraw),
        )
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sorted(outcomes) in (
            ["approve-conflict", "withdraw"],
            ["approve", "withdraw-conflict"],
        )
        detail = service.read_detail(alice, created.summary.record_id)
        timeline = service.list_timeline(alice).items
        connection = sqlite3.connect(tmp_path / "catalog.sqlite3")
        try:
            row = connection.execute(
                "SELECT version, approved_projection_json, timeline_entered_at_ms "
                "FROM kronika_records"
            ).fetchone()
        finally:
            connection.close()
        assert row[1] is not None
        assert row[2] == 9
        assert detail.summary.timeline_entered_at_ms == 9
        assert len(timeline) in (0, 1)
    finally:
        dispose_engine(engine)
