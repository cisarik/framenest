"""Bounded cancellation and deadline behavior for one ask."""

from __future__ import annotations

from kronika.bridge.jobs import JobManager
from kronika.bridge.store import Store


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _manager(tmp_path, clock: Clock) -> JobManager:
    manager = JobManager(
        Store(tmp_path),
        clock=clock,
        stall_after_s=30,
        cancel_grace_s=10,
        connected_window_s=1000,
    )
    manager.hello({"proto": 1, "client": "headless", "capabilities": []})
    return manager


def test_queued_cancel_is_terminal(tmp_path) -> None:
    clock = Clock()
    manager = _manager(tmp_path, clock)
    job = manager.create_job({"prompt": "hello"})
    assert manager.cancel(job.job_id) == "cancelled"
    assert manager.get(job.job_id)["job"]["result"]["error_code"] == "E_CANCELLED"


def test_running_cancel_waits_for_the_grace_then_stops(tmp_path) -> None:
    clock = Clock()
    manager = _manager(tmp_path, clock)
    job = manager.create_job({"prompt": "hello", "timeout_s": 100})
    offered = manager.next_offer(0)
    assert offered is not None
    manager.append_events(job.job_id, [{"type": "status", "data": {"status": "accepted"}}])
    assert manager.cancel(job.job_id) == "running"
    clock.now = 9.0
    manager.watchdog()
    assert manager.get(job.job_id)["job"]["status"] == "running"
    clock.now = 10.0
    manager.watchdog()
    viewed = manager.get(job.job_id)["job"]
    assert viewed["status"] == "cancelled"
    assert viewed["result"]["error_code"] == "E_CANCELLED"


def test_deadline_fails_the_job(tmp_path) -> None:
    clock = Clock()
    manager = _manager(tmp_path, clock)
    job = manager.create_job({"prompt": "hello", "timeout_s": 5})
    clock.now = 5.0
    manager.watchdog()
    viewed = manager.get(job.job_id)["job"]
    assert viewed["status"] == "failed"
    assert viewed["result"]["error_code"] == "E_RESPONSE_TIMEOUT"
