"""Withdrawal keeps the first Timeline timestamp and the approved snapshot."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from framenest.application.records import RecordService
from framenest.configuration import FrameNestSettings
from framenest.domain.identity_access import ROLE_ADMIN, ROLE_USER
from framenest.domain.records import CompletedDocument, DocumentId, RecordKind
from framenest.domain.research import CompletionEvidence
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.record_repository import SqliteRecordRepository
from tests.support.record_access import synthetic_identity


def test_withdrawal_keeps_timeline_position_and_snapshot(tmp_path: Path) -> None:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(settings.database_path)
    service = RecordService(SqliteRecordRepository(engine))
    alice = synthetic_identity("alice", role=ROLE_USER)
    admin = synthetic_identity("ada", role=ROLE_ADMIN)
    document = CompletedDocument(
        document_id=DocumentId.new(),
        operation_id="search-op-timeline",
        kind=RecordKind.SEARCH,
        question_text="Timeline question",
        answer_text="Timeline answer",
        citations=(),
        evidence=CompletionEvidence(
            provider_terminal=True,
            answer_complete=True,
            web_search_executed=True,
            refusal_marker=False,
            incomplete_marker=False,
        ),
        created_at_ms=5,
        completed_at_ms=6,
    )
    try:
        created = service.create_completed_document(alice, document)
        candidate = service.prepare_approval(admin, created.summary.record_id)
        approved = service.approve(admin, candidate, approved_at_ms=9)
        first_timeline = service.list_timeline(alice).items[0]
        assert first_timeline.timeline_entered_at_ms == 9
        withdrawn = service.withdraw(
            admin,
            record_id=created.summary.record_id,
            expected_version=approved.version,
        )
        assert withdrawn.changed is True
        history = service.list_own_history(alice)
        assert history.items[0].record_id == created.summary.record_id
        assert service.list_timeline(alice).items == ()
        detail = service.read_detail(alice, created.summary.record_id)
        assert detail.summary.timeline_entered_at_ms == 9
        again = service.withdraw(
            admin,
            record_id=created.summary.record_id,
            expected_version=withdrawn.version,
        )
        assert again.changed is False
    finally:
        dispose_engine(engine)


def test_household_keeps_approved_answer_until_reapproval(tmp_path: Path) -> None:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(settings.database_path)
    service = RecordService(SqliteRecordRepository(engine))
    alice = synthetic_identity("alice", role=ROLE_USER)
    household = synthetic_identity("bob", role=ROLE_USER)
    admin = synthetic_identity("ada", role=ROLE_ADMIN)
    document = CompletedDocument(
        document_id=DocumentId.new(),
        operation_id="search-op-stability",
        kind=RecordKind.SEARCH,
        question_text="Approved question",
        answer_text="Answer A",
        citations=(),
        evidence=CompletionEvidence(
            provider_terminal=True,
            answer_complete=True,
            web_search_executed=True,
            refusal_marker=False,
            incomplete_marker=False,
        ),
        created_at_ms=5,
        completed_at_ms=6,
    )
    try:
        created = service.create_completed_document(alice, document)
        candidate = service.prepare_approval(admin, created.summary.record_id)
        approved = service.approve(admin, candidate, approved_at_ms=9)
        connection = sqlite3.connect(settings.database_path)
        try:
            connection.execute(
                "UPDATE kronika_documents SET answer_text = ? WHERE operation_id = ?",
                ("Answer B", document.operation_id),
            )
            connection.execute(
                "UPDATE kronika_records SET version = version + 1 WHERE id = ?",
                (created.summary.record_id,),
            )
            connection.commit()
        finally:
            connection.close()
        frozen = service.read_detail(household, created.summary.record_id)
        assert frozen.document is not None
        assert frozen.document.answer_text == "Answer A"
        assert service.list_timeline(household).items[0].timeline_entered_at_ms == 9
        current = service.read_detail(alice, created.summary.record_id)
        assert current.document is not None
        assert current.document.answer_text == "Answer B"
        refreshed = service.prepare_approval(admin, created.summary.record_id)
        again = service.approve(admin, refreshed, approved_at_ms=11)
        assert again.changed is True
        assert again.version != approved.version
        updated = service.read_detail(household, created.summary.record_id)
        assert updated.document is not None
        assert updated.document.answer_text == "Answer B"
        assert updated.summary.timeline_entered_at_ms == 9
        assert service.list_timeline(household).items[0].timeline_entered_at_ms == 9
    finally:
        dispose_engine(engine)
