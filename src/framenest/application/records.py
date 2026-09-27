"""Use cases for Kronika records. Owners come from the verified caller."""

from __future__ import annotations

from dataclasses import dataclass

from framenest.application.ports.records import (
    ApprovalCandidate,
    ApprovalResult,
    RecordDetail,
    RecordPage,
    RecordPageQuery,
    RecordRepository,
)
from framenest.domain.identity_access import IdentityContext
from framenest.domain.record_access import may_approve
from framenest.domain.records import (
    CompletedDocument,
    RecordConflictError,
    RecordId,
    RecordNotFoundError,
    RecordValueError,
    parse_owner_login_key,
)

DEFAULT_RECORD_PAGE_LIMIT = 24
MAX_RECORD_PAGE_LIMIT = 100


@dataclass(frozen=True, slots=True)
class RecordService:
    """Authorized record reads and administrator approval."""

    repository: RecordRepository

    def create_completed_document(
        self,
        identity: object,
        document: CompletedDocument,
        *,
        record_id: RecordId | None = None,
    ) -> RecordDetail:
        owner = _require_login(identity)
        return self.repository.create_completed_document(
            document,
            owner_login_key=owner,
            record_id=record_id or RecordId.new(),
        )

    def read_detail(self, identity: object, record_id: str) -> RecordDetail:
        caller = _require_identity(identity)
        return self.repository.read_detail(caller, record_id)

    def list_own_history(
        self,
        identity: object,
        *,
        limit: int = DEFAULT_RECORD_PAGE_LIMIT,
        offset: int = 0,
    ) -> RecordPage:
        caller = _require_identity(identity)
        return self.repository.list_own_history(caller, _page(limit, offset))

    def list_admin_inventory(
        self,
        identity: object,
        *,
        limit: int = DEFAULT_RECORD_PAGE_LIMIT,
        offset: int = 0,
    ) -> RecordPage:
        caller = _require_identity(identity)
        if not may_approve(caller):
            raise RecordNotFoundError()
        return self.repository.list_admin_inventory(caller, _page(limit, offset))

    def list_timeline(
        self,
        identity: object,
        *,
        limit: int = DEFAULT_RECORD_PAGE_LIMIT,
        offset: int = 0,
    ) -> RecordPage:
        caller = _require_identity(identity)
        return self.repository.list_timeline(caller, _page(limit, offset))

    def prepare_approval(self, identity: object, record_id: str) -> ApprovalCandidate:
        caller = _require_identity(identity)
        if not may_approve(caller):
            raise RecordNotFoundError()
        return self.repository.prepare_approval(caller, record_id)

    def approve(
        self,
        identity: object,
        candidate: ApprovalCandidate,
        *,
        approved_at_ms: int,
    ) -> ApprovalResult:
        caller = _require_identity(identity)
        if not may_approve(caller):
            raise RecordNotFoundError()
        if isinstance(approved_at_ms, bool) or not isinstance(approved_at_ms, int):
            raise RecordValueError()
        return self.repository.approve(
            caller,
            candidate,
            approved_at_ms=approved_at_ms,
        )

    def withdraw(
        self,
        identity: object,
        *,
        record_id: str,
        expected_version: int,
    ) -> ApprovalResult:
        caller = _require_identity(identity)
        if not may_approve(caller):
            raise RecordNotFoundError()
        if isinstance(expected_version, bool) or not isinstance(expected_version, int):
            raise RecordConflictError()
        return self.repository.withdraw(
            caller,
            record_id=record_id,
            expected_version=expected_version,
        )


def _require_identity(identity: object) -> IdentityContext:
    if not isinstance(identity, IdentityContext) or not identity.login_key:
        raise RecordNotFoundError()
    return identity


def _require_login(identity: object) -> str:
    caller = _require_identity(identity)
    return parse_owner_login_key(caller.login_key)


def _page(limit: int, offset: int) -> RecordPageQuery:
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or isinstance(offset, bool)
        or not isinstance(offset, int)
        or limit < 1
        or limit > MAX_RECORD_PAGE_LIMIT
        or offset < 0
    ):
        raise RecordValueError()
    return RecordPageQuery(limit=limit, offset=offset)
