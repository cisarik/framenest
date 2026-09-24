"""Failure injection for durable admission, fencing, recovery and intervention."""

from __future__ import annotations

import json
import sqlite3
import uuid

import pytest

from kronika_capture.bridge.jobs import BridgeError, JobManager
from kronika_capture.bridge.journal import Journal, JournalUnavailable
from kronika_capture.bridge.store import Store


class Clock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


def uid():
    return str(uuid.uuid4())


def ready(manager, runner=None):
    return manager.hello({
        "proto": 1, "client": "headless", "runner_id": runner or uid(),
        "browser_session": uid(), "capabilities": ["durable_submission", "admin_resume"],
        "readiness": {"state": "ready"},
    })


def manager_at(tmp_path, **kwargs):
    manager = JobManager(Store(tmp_path), **kwargs)
    ready(manager)
    return manager


def request(prompt=" private prompt \n", **kwargs):
    return {"request_id": uid(), "prompt": prompt, **kwargs}


def offer(manager, job):
    accepted = manager.next_offer(0, runner_id=manager._service["runner_id"],
                                  epoch=manager._service["epoch"])
    assert accepted.job_id == job.job_id
    manager.append_events(job.job_id, [{"type": "status", "data": {"status": "accepted"}}],
                          accepted.offer())
    return accepted.offer()


def event(manager, job, fence, typ, **data):
    return manager.append_events(job.job_id, [{"type": typ, "data": data}], fence)


def result(fence, **kwargs):
    return {**fence, "delivery_id": uid(), "status": "done", "answer": "private answer",
            "url": "https://chatgpt.com/c/private-source", "activity_stopped": True, **kwargs}


def confirm(manager, job, fence):
    event(manager, job, fence, "send_intent")
    event(manager, job, fence, "send_confirmed", response_id=uid())


def test_request_id_required_canonical_defaults_whitespace_and_retry_priority(tmp_path):
    manager = manager_at(tmp_path)
    with pytest.raises(BridgeError) as error:
        manager.create_job({"prompt": "hello"})
    assert error.value.status == 400
    req = request()
    job = manager.create_job(req)
    assert manager.create_job({**req, "files": [], "new_chat": True, "kind": "ask",
                               "timeout_s": 600, "mode": None, "project": None}).job_id == job.job_id
    with pytest.raises(BridgeError) as error:
        manager.create_job({**req, "prompt": req["prompt"].strip()})
    assert error.value.code == "E_IDEMPOTENCY_CONFLICT"
    manager._service["state"] = "browser_unavailable"
    assert manager.create_job(req).job_id == job.job_id


@pytest.mark.parametrize("boundary", ["admission", "offer", "send_intent", "result"])
def test_failed_transaction_never_acknowledges_or_changes_memory(tmp_path, monkeypatch, boundary):
    manager = manager_at(tmp_path)
    req = request()
    job = fence = None
    if boundary != "admission":
        job = manager.create_job(req)
    if boundary in ("send_intent", "result"):
        fence = offer(manager, job)
    if boundary == "result":
        confirm(manager, job, fence)
    before = {key: value.record() for key, value in manager._jobs.items()}
    original = manager.journal.commit
    def fail(*args, **kwargs):
        raise JournalUnavailable()
    monkeypatch.setattr(manager.journal, "commit", fail)
    with pytest.raises(BridgeError) as error:
        if boundary == "admission":
            manager.create_job(req)
        elif boundary == "offer":
            manager.next_offer(0, runner_id=manager._service["runner_id"], epoch=manager._service["epoch"])
        elif boundary == "send_intent":
            event(manager, job, fence, "send_intent")
        else:
            manager.resolve(job.job_id, result(fence))
    assert error.value.code == "E_JOURNAL_UNAVAILABLE"
    assert error.value.status == 503
    assert {key: value.record() for key, value in manager._jobs.items()} == before
    monkeypatch.setattr(manager.journal, "commit", original)
    assert manager.status()["reason"] == "E_JOURNAL_UNAVAILABLE"
    with pytest.raises(BridgeError):
        manager.create_job(request("another"))


def test_commit_is_visible_to_another_reader_before_admission_returns(tmp_path, monkeypatch):
    manager = manager_at(tmp_path)
    original = manager.journal.commit
    observed = []
    def record(*args, **kwargs):
        original(*args, **kwargs)
        with sqlite3.connect(manager.journal.path) as reader:
            observed.extend(reader.execute("SELECT request_id FROM jobs").fetchall())
    monkeypatch.setattr(manager.journal, "commit", record)
    req = request()
    job = manager.create_job(req)
    assert (req["request_id"],) in observed
    assert job.request_id == req["request_id"]
    assert manager.journal.path.stat().st_mode & 0o777 == 0o600
    assert tmp_path.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("boundary", ["offered", "accepted", "send_intent", "send_confirmed"])
def test_recovery_invalidates_every_uncertain_offer_and_old_runner(tmp_path, boundary):
    manager = manager_at(tmp_path)
    req = request()
    job = manager.create_job(req)
    offered = manager.next_offer(0, runner_id=manager._service["runner_id"], epoch=manager._service["epoch"])
    fence = offered.offer()
    if boundary != "offered":
        event(manager, job, fence, "status", status="accepted")
    if boundary in ("send_intent", "send_confirmed"):
        event(manager, job, fence, "send_intent")
    if boundary == "send_confirmed":
        event(manager, job, fence, "send_confirmed", response_id=uid())
    recovered = JobManager(Store(tmp_path))
    assert recovered.get(job.job_id)["job"]["result"]["error_code"] == "E_AMBIGUOUS_SEND"
    assert recovered.create_job(req).job_id == job.job_id
    assert recovered.status()["readiness"] == "needs_admin"
    with pytest.raises(BridgeError):
        event(recovered, job, fence, "send_intent")
    # A surviving old manager also cannot overwrite the replacement's epoch.
    with pytest.raises(BridgeError) as error:
        manager.cancel(job.job_id)
    assert error.value.code == "E_JOURNAL_UNAVAILABLE"


def test_queued_restart_recovery_and_terminal_delivery_replay(tmp_path):
    manager = manager_at(tmp_path)
    req = request()
    job = manager.create_job(req)
    manager.journal.close()
    manager = manager_at(tmp_path)
    assert manager.get(job.job_id)["job"]["status"] == "queued"
    fence = offer(manager, job)
    confirm(manager, job, fence)
    delivery = result(fence)
    assert manager.resolve(job.job_id, delivery) == "done"
    assert manager.resolve(job.job_id, delivery) == "done"
    with pytest.raises(BridgeError) as error:
        manager.resolve(job.job_id, {**delivery, "answer": "different"})
    assert error.value.code == "E_IDEMPOTENCY_CONFLICT"
    manager.cancel(job.job_id)
    manager.journal.close()
    recovered = JobManager(Store(tmp_path))
    assert recovered.create_job(req).status == "done"
    assert recovered.result_record(job.job_id)["text"] == "private answer"


def test_recovery_failure_is_typed_and_no_new_journal_is_substituted(tmp_path, monkeypatch):
    journal = Journal(tmp_path)
    monkeypatch.setattr(journal, "load", lambda: (_ for _ in ()).throw(JournalUnavailable()))
    with pytest.raises(BridgeError) as error:
        JobManager(Store(tmp_path), journal=journal)
    assert error.value.code == "E_JOURNAL_UNAVAILABLE"
    assert journal.path.exists()


def test_corrupt_journal_is_not_replaced(tmp_path):
    path = tmp_path / "capture-journal.sqlite3"
    path.write_bytes(b"invalid synthetic database")
    with pytest.raises(BridgeError) as error:
        JobManager(Store(tmp_path))
    assert error.value.code == "E_JOURNAL_UNAVAILABLE"
    assert path.read_bytes() == b"invalid synthetic database"


def test_single_use_send_intent_and_cancel_cannot_grant_send(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    fence = offer(manager, job)
    event(manager, job, fence, "send_intent")
    with pytest.raises(BridgeError) as error:
        event(manager, job, fence, "send_intent")
    assert error.value.code == "E_AMBIGUOUS_SEND"
    manager.cancel(job.job_id)
    with pytest.raises(BridgeError):
        event(manager, job, fence, "send_intent")


def test_admin_resume_requires_identity_and_excludes_cumulative_wait(tmp_path):
    clock = Clock(0)
    manager = manager_at(tmp_path, clock=clock, connected_window_s=5000, stall_after_s=5000)
    job = manager.create_job(request(timeout_s=10))
    fence = offer(manager, job)
    clock.value = 2
    paused = event(manager, job, fence, "needs_admin", reason="E_LOGIN_REQUIRED")
    clock.value = 102
    manager.watchdog()
    view = manager.get(job.job_id)["job"]
    assert view["status"] == "needs_admin" and view["admin_wait_s"] == 100
    with pytest.raises(BridgeError):
        manager.resume({"job_id": job.job_id, "intervention_id": uid()})
    pending = manager.resume({"job_id": job.job_id, "intervention_id": paused["intervention_id"]})
    assert manager.status()["readiness"] == "needs_admin"
    with pytest.raises(BridgeError):
        event(manager, job, fence, "resumed", resume_id=pending["resume_id"],
              intervention_id=paused["intervention_id"], ready=False)
    event(manager, job, fence, "resumed", resume_id=pending["resume_id"],
          intervention_id=paused["intervention_id"], ready=True)
    clock.value = 109
    manager.watchdog()
    assert manager.get(job.job_id)["job"]["status"] == "running"
    event(manager, job, fence, "needs_admin", reason="E_CAPTCHA_REQUIRED")
    clock.value += 1700
    manager.watchdog()
    assert manager.get(job.job_id)["job"]["result"]["error_code"] == "E_INTERVENTION_TIMEOUT"
    assert manager.status()["readiness"] == "needs_admin"


def test_cancel_and_timeout_keep_service_blocked_until_stop_checked(tmp_path):
    clock = Clock(0)
    manager = manager_at(tmp_path, clock=clock)
    job = manager.create_job(request(timeout_s=5))
    offer(manager, job)
    clock.value = 5
    manager.watchdog()
    assert manager.get(job.job_id)["job"]["result"]["error_code"] == "E_RESPONSE_TIMEOUT"
    assert manager.status()["readiness"] == "needs_admin"


def test_idle_resume_requires_new_readiness_and_status_contains_only_metadata(tmp_path):
    manager = manager_at(tmp_path)
    rid = manager._service["runner_id"]
    manager.hello({"proto": 1, "runner_id": rid, "browser_session": uid(),
                   "readiness": {"state": "needs_admin", "reason": "E_LOGIN_REQUIRED"}})
    pending = manager.resume({"job_id": None, "intervention_id": manager.status()["intervention_id"]})
    manager.hello({"proto": 1, "runner_id": rid, "browser_session": uid(),
                   "readiness": {"state": "ready"}})
    assert manager.status()["readiness"] == "needs_admin"
    manager.hello({"proto": 1, "runner_id": rid, "browser_session": uid(),
                   "readiness": {"state": "ready"}, "resume_id": pending["resume_id"]})
    assert manager.status()["readiness"] == "ready"
    job = manager.create_job(request(prompt="SECRET PROMPT"))
    fence = offer(manager, job)
    confirm(manager, job, fence)
    manager.resolve(job.job_id, result(fence, answer="SECRET ANSWER"))
    public = json.dumps(manager.status())
    for private in ("SECRET", "private-source", "prompt", "answer", "title", "url"):
        assert private not in public


def test_24_hour_256_retention_no_unexpired_eviction(tmp_path):
    wall = Clock(1000)
    manager = manager_at(tmp_path, wall_clock=wall)
    requests = []
    for _ in range(256):
        req = request()
        requests.append(req)
        job = manager.create_job(req)
        manager.cancel(job.job_id)
    with pytest.raises(BridgeError) as error:
        manager.create_job(request())
    assert error.value.code == "E_SERVICE_LIMIT" and error.value.status == 429
    assert manager.create_job(requests[0]).status == "cancelled"
    wall.value -= 100
    manager.watchdog()
    assert manager.status()["jobs"]["total"] == 256
    wall.value = 1000 + 86400 - 1
    manager.watchdog()
    assert manager.status()["jobs"]["total"] == 256
    wall.value += 1
    manager.watchdog()
    assert manager.status()["jobs"]["total"] == 0
    assert manager.create_job(request()).status == "queued"


def test_events_are_bounded_metadata_and_arbitrary_dom_text_is_discarded(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    fence = offer(manager, job)
    for _ in range(80):
        event(manager, job, fence, "progress", phase="composed", text="PRIVATE DOM SNAPSHOT")
    record = manager._jobs[job.job_id]
    assert len(record.events) == 64
    assert "PRIVATE DOM SNAPSHOT" not in json.dumps(record.events)

@pytest.mark.parametrize("boundary", ["admission", "offer", "send_intent", "result"])
def test_commit_succeeded_but_acknowledgement_lost_recovers_without_reexecution(tmp_path, monkeypatch, boundary):
    manager = manager_at(tmp_path)
    req = request()
    job = fence = None
    if boundary != "admission":
        job = manager.create_job(req)
    if boundary in ("send_intent", "result"):
        fence = offer(manager, job)
    if boundary == "result":
        confirm(manager, job, fence)
    original = manager.journal.commit
    def lost_ack(*args, **kwargs):
        original(*args, **kwargs)
        raise JournalUnavailable()
    monkeypatch.setattr(manager.journal, "commit", lost_ack)
    with pytest.raises(BridgeError):
        if boundary == "admission":
            manager.create_job(req)
        elif boundary == "offer":
            manager.next_offer(0, runner_id=manager._service["runner_id"], epoch=manager._service["epoch"])
        elif boundary == "send_intent":
            event(manager, job, fence, "send_intent")
        else:
            manager.resolve(job.job_id, result(fence))
    manager.journal.close()
    recovered = JobManager(Store(tmp_path))
    replay = recovered.create_job(req)
    expected = {"admission": "queued", "offer": "failed", "send_intent": "failed", "result": "done"}
    assert replay.status == expected[boundary]
    if replay.status == "failed":
        assert replay.result["error_code"] == "E_AMBIGUOUS_SEND"


def test_recovery_commit_failure_is_not_acknowledged(tmp_path, monkeypatch):
    journal = Journal(tmp_path)
    monkeypatch.setattr(journal, "commit", lambda *args, **kwargs: (_ for _ in ()).throw(JournalUnavailable()))
    with pytest.raises(BridgeError) as error:
        JobManager(Store(tmp_path), journal=journal)
    assert error.value.code == "E_JOURNAL_UNAVAILABLE"
    journal.close()

def test_queued_job_can_resume_after_readiness_changes_before_offer(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    runner, browser = manager._service["runner_id"], manager._service["browser_session"]
    manager.hello({"proto": 1, "runner_id": runner, "browser_session": browser,
                   "readiness": {"state": "needs_admin", "reason": "E_LOGIN_REQUIRED"}})
    intervention = manager.status()["intervention_id"]
    assert intervention
    pending = manager.resume({"job_id": job.job_id, "intervention_id": intervention})
    manager.hello({"proto": 1, "runner_id": runner, "browser_session": browser,
                   "readiness": {"state": "ready"}, "resume_id": pending["resume_id"]})
    assert manager.status()["readiness"] == "ready"
    assert manager.get(job.job_id)["job"]["status"] == "queued"
    assert offer(manager, job)["job_id"] == job.job_id


def test_browser_identity_change_invalidates_inflight_offer(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    fence = offer(manager, job)
    ready(manager, manager._service["runner_id"])
    assert manager.get(job.job_id)["job"]["result"]["error_code"] == "E_AMBIGUOUS_SEND"
    assert manager.status()["readiness"] == "needs_admin"
    response = event(manager, job, fence, "heartbeat")
    assert response["terminal"] is True

def test_ambiguous_terminal_result_keeps_readiness_blocked_even_with_stop_claim(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    fence = offer(manager, job)
    event(manager, job, fence, "send_intent")
    manager.resolve(job.job_id, result(fence, status="failed", answer=None,
                                      error_code="E_AMBIGUOUS_SEND", activity_stopped=True))
    assert manager.status()["readiness"] == "needs_admin"
    with pytest.raises(BridgeError) as error:
        manager.create_job(request())
    assert error.value.code == "E_NEEDS_ADMIN"


def test_resume_at_admin_limit_counts_wait_once(tmp_path):
    clock = Clock(0)
    manager = manager_at(tmp_path, clock=clock, connected_window_s=5000)
    job = manager.create_job(request())
    fence = offer(manager, job)
    paused = event(manager, job, fence, "needs_admin", reason="E_LOGIN_REQUIRED")
    pending = manager.resume({"job_id": job.job_id, "intervention_id": paused["intervention_id"]})
    clock.value = 1800
    response = event(manager, job, fence, "resumed", ready=True,
                     resume_id=pending["resume_id"], intervention_id=paused["intervention_id"])
    assert response["terminal"] is True
    view = manager.get(job.job_id)["job"]
    assert view["result"]["error_code"] == "E_INTERVENTION_TIMEOUT"
    assert view["admin_wait_s"] == 1800

def test_confirmed_response_resume_requires_same_response_identity(tmp_path):
    manager = manager_at(tmp_path)
    job = manager.create_job(request())
    fence = offer(manager, job)
    event(manager, job, fence, "send_intent")
    response_id = uid()
    event(manager, job, fence, "send_confirmed", response_id=response_id)
    pause = event(manager, job, fence, "needs_admin", reason="E_CONSENT_REQUIRED")
    pending = manager.resume({"job_id": job.job_id, "intervention_id": pause["intervention_id"]})
    with pytest.raises(BridgeError) as error:
        event(manager, job, fence, "resumed", ready=True, resume_id=pending["resume_id"],
              intervention_id=pause["intervention_id"], response_id=uid())
    assert error.value.code == "E_AMBIGUOUS_SEND"
    event(manager, job, fence, "resumed", ready=True, resume_id=pending["resume_id"],
          intervention_id=pause["intervention_id"], response_id=response_id)
    with pytest.raises(BridgeError):
        event(manager, job, fence, "send_intent")
    assert manager.resolve(job.job_id, result(fence)) == "done"
