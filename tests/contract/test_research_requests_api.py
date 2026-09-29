"""Research request API evidence: submission, history, cancel, refusals."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from framenest.adapters.api.research_api import (
    ResearchApiDependencies,
    create_research_api_router,
)
from framenest.application.research import ResearchCoordinator
from framenest.configuration import FrameNestSettings
from framenest.domain.research import (
    ProviderHandle,
    ProviderObservation,
    ProviderObservationKind,
    ResearchErrorCode,
)
from framenest.infrastructure.ai.research_configuration import (
    default_research_configuration,
)
from framenest.infrastructure.ai.research_registry import select_research_provider
from framenest.infrastructure.persistence.engine import (
    create_sqlite_engine,
    dispose_engine,
)
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.persistence.record_repository import (
    SqliteResearchResultCompletion,
)
from framenest.infrastructure.persistence.research_budget_repository import (
    SqliteResearchBudgetLedger,
)
from framenest.infrastructure.persistence.research_request_repository import (
    SqliteResearchRequestRepository,
)
from tests.support.record_access import install_synthetic_caller

HANDLE = ProviderHandle("api-handle-1")


class FakeProvider:
    def __init__(self) -> None:
        self.poll_kind = ProviderObservationKind.RUNNING
        self.cancelled = False

    def describe(self):
        raise AssertionError("not used")

    def submit(self, request):
        return ProviderObservation(
            kind=ProviderObservationKind.RUNNING,
            remote_handle=HANDLE,
        )

    def poll(self, handle):
        return ProviderObservation(kind=self.poll_kind, remote_handle=handle)

    def cancel(self, handle):
        self.cancelled = True
        return ProviderObservation(
            kind=ProviderObservationKind.CANCELLED,
            error_code=ResearchErrorCode.CANCELLED,
        )

    def release_remote(self, handle):
        from framenest.domain.research import CleanupOutcome, ResearchRemoteCleanupState

        return CleanupOutcome(state=ResearchRemoteCleanupState.DELETED)


@pytest.fixture()
def api(tmp_path: Path):
    settings = FrameNestSettings(
        database_path=tmp_path / "research-api.sqlite3",
        identity_map={"alice": "user", "bob": "user", "ada": "admin"},
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(settings.database_path)
    repository = SqliteResearchRequestRepository(engine)
    provider = FakeProvider()
    configuration = default_research_configuration(enabled=True)
    coordinator = ResearchCoordinator(
        provider=provider,
        requests=repository,
        ledger=SqliteResearchBudgetLedger(engine),
        completion=SqliteResearchResultCompletion(engine),
        select=lambda kind: select_research_provider(configuration, kind=kind),
    )

    def build_client(*, runtime=coordinator, caller: str | None = "alice") -> TestClient:
        app = FastAPI()
        app.include_router(
            create_research_api_router(
                ResearchApiDependencies(
                    requests=repository,
                    runtime=runtime,
                    configuration=configuration if runtime is not None else None,
                )
            )
        )
        if caller is not None:
            role = "admin" if caller == "ada" else "user"
            install_synthetic_caller(app, caller, role=role)
        return TestClient(app)

    try:
        yield {
            "engine": engine,
            "repository": repository,
            "provider": provider,
            "coordinator": coordinator,
            "configuration": configuration,
            "client": build_client(),
            "build_client": build_client,
        }
    finally:
        dispose_engine(engine)


def _submit(client: TestClient, *, client_request_id: str = "client-api-1", prompt: str = "Question?"):
    return client.post(
        "/api/research-requests",
        json={
            "kind": "search",
            "prompt": prompt,
            "client_request_id": client_request_id,
            "consent_version": "2026-09",
        },
    )


def test_capabilities_reports_selection_without_secrets(api) -> None:
    response = api["client"].get("/api/research/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["provider_id"] == "openai-responses"
    assert body["kinds"] == ["search", "research"]
    assert body["search"]["deadline_seconds"] == 180
    assert body["research"]["deadline_seconds"] == 1800
    assert "api_key" not in response.text.lower()
    disabled = api["build_client"](runtime=None).get("/api/research/capabilities")
    assert disabled.json()["enabled"] is False


def test_anonymous_is_refused(api) -> None:
    anonymous = api["build_client"](caller=None)
    assert anonymous.get("/api/research-requests").status_code == 401
    assert _submit(anonymous).status_code == 401


def test_submission_progress_and_owner_separation(api) -> None:
    created = _submit(api["client"])
    assert created.status_code == 202
    body = created.json()
    operation_id = body["operation_id"]
    assert body["state"] == "running"
    detail = api["client"].get(f"/api/research-requests/{operation_id}")
    assert detail.status_code == 200
    assert detail.json()["prompt"] == "Question?"
    bob = api["build_client"](caller="bob")
    assert bob.get(f"/api/research-requests/{operation_id}").status_code == 404
    assert bob.get("/api/research-requests").json()["total"] == 0
    admin = api["build_client"](caller="ada")
    assert admin.get(f"/api/research-requests/{operation_id}").status_code == 200
    assert admin.get("/api/admin/research-requests").json()["total"] == 1
    user_admin_list = api["client"].get("/api/admin/research-requests")
    assert user_admin_list.status_code == 403


def test_idempotent_replay_and_conflict(api) -> None:
    first = _submit(api["client"], client_request_id="client-api-2")
    replay = _submit(api["client"], client_request_id="client-api-2")
    assert first.json()["operation_id"] == replay.json()["operation_id"]
    conflict = _submit(
        api["client"],
        client_request_id="client-api-2",
        prompt="A different question?",
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "E_IDEMPOTENCY_CONFLICT"


def test_cancel_confirms_and_history_reflects_state(api) -> None:
    created = _submit(api["client"], client_request_id="client-api-3")
    operation_id = created.json()["operation_id"]
    cancelled = api["client"].post(f"/api/research-requests/{operation_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert api["provider"].cancelled is True
    history = api["client"].get("/api/research-requests").json()
    assert history["items"][0]["state"] == "cancelled"


def test_disabled_runtime_refuses_submission_but_serves_capabilities(api) -> None:
    client = api["build_client"](runtime=None)
    response = _submit(client, client_request_id="client-api-4")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "E_DISABLED"
