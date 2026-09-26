"""Application ports for provider-neutral research.

Protocols only. They import domain values and no HTTP, database, SDK, or
capture modules.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from framenest.domain.research import (
    BudgetHold,
    BudgetReconciliation,
    BudgetReservation,
    CleanupOutcome,
    ProviderDescriptor,
    ProviderHandle,
    ProviderObservation,
    ProviderRequest,
    ResearchRequestRecord,
    ResultCompletion,
    ResultCompletionReceipt,
)


@runtime_checkable
class ResearchProvider(Protocol):
    """One research adapter. Selection and limits arrive already snapshotted."""

    def describe(self) -> ProviderDescriptor:
        """Return the network-free provider descriptor."""

    def submit(self, request: ProviderRequest) -> ProviderObservation:
        """Submit one bounded generation. There is no client endpoint or model."""

    def poll(self, handle: ProviderHandle) -> ProviderObservation:
        """Read one already submitted remote operation."""

    def cancel(self, handle: ProviderHandle) -> ProviderObservation:
        """Request cancellation of one known remote operation."""

    def release_remote(self, handle: ProviderHandle) -> CleanupOutcome:
        """Delete one remote response after local reconciliation."""


@runtime_checkable
class ResearchRequestRepository(Protocol):
    """Durable request records. Owner identity is not part of this port."""

    def get(self, operation_id: str) -> ResearchRequestRecord | None:
        """Return one request, or none when it is absent."""

    def admit(self, record: ResearchRequestRecord) -> ResearchRequestRecord:
        """Persist one newly admitted request."""

    def save(self, record: ResearchRequestRecord) -> ResearchRequestRecord:
        """Persist a later lifecycle, cleanup, or accounting transition."""


@runtime_checkable
class ResearchBudgetLedger(Protocol):
    """Atomic budget reservation and later usage reconciliation."""

    def reserve(self, reservation: BudgetReservation) -> BudgetHold:
        """Reserve the full per-operation allowance or refuse admission."""

    def reconcile(self, reconciliation: BudgetReconciliation) -> BudgetHold:
        """Record reconciled usage, or an explicit unknown accounting state."""


@runtime_checkable
class ResearchResultCompletion(Protocol):
    """Atomic local save of one validated result."""

    def complete(self, completion: ResultCompletion) -> ResultCompletionReceipt:
        """Save the answer, citations, and request binding in one transaction."""
