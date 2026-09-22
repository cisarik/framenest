"""One-flight ask lifecycle for the stripped loopback bridge."""

from __future__ import annotations

import logging
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from kronika import config, errors, projects

LOGGER = logging.getLogger("kronika.bridge.jobs")

ACTIVE_STATUSES = ("queued", "offered", "running")
TERMINAL_STATUSES = ("done", "failed", "cancelled")

CLIENT_KINDS = ("headless",)
DEFAULT_CLIENT_KIND = "headless"
REMOVED_MODES = {
    "search": "E_INTERNAL",
    "web_search": "E_WEB_SEARCH_UNAVAILABLE",
    "deep_research": "E_DEEP_RESEARCH_UNAVAILABLE",
    "verify": "E_INTERNAL",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BridgeError(Exception):
    """Typed bridge failure carrying an error code and HTTP status."""

    def __init__(self, code: str, step: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.step = step
        self.message = message
        self.status = status


@dataclass
class Job:
    job_id: str
    kind: str = "ask"
    prompt: str = ""
    files: list = field(default_factory=list)
    new_chat: bool = True
    timeout_s: int = config.DEFAULT_ASK_TIMEOUT_S
    project: dict | None = None
    mode: str | None = None
    status: str = "queued"
    created_at: str = ""
    updated_at: str = ""
    events: list = field(default_factory=list)
    result: dict | None = None
    result_id: str | None = None
    cancel_requested: bool = False
    last_seq: int = 0
    started_mono: float = 0.0
    last_progress_mono: float = 0.0
    deadline_mono: float = 0.0
    cancel_mono: float = 0.0

    def record(self) -> dict:
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "prompt": self.prompt,
            "files": list(self.files),
            "new_chat": self.new_chat,
            "timeout_s": self.timeout_s,
            "project": dict(self.project) if self.project else None,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": list(self.events),
            "result": self.result,
            "result_id": self.result_id,
            "cancel_requested": self.cancel_requested,
        }

    def offer(self) -> dict:
        offer = {
            "job_id": self.job_id,
            "kind": self.kind,
            "prompt": self.prompt,
            "files": list(self.files),
            "new_chat": self.new_chat,
            "timeout_s": self.timeout_s,
            "mode": self.mode,
        }
        if self.project:
            offer["project"] = {
                "name": self.project.get("name"),
                "url": self.project.get("url"),
            }
        return offer

    def view(self) -> dict:
        view = {
            "job_id": self.job_id,
            "kind": self.kind,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "timeout_s": self.timeout_s,
            "cancel_requested": self.cancel_requested,
            "result": self.result,
        }
        if self.result_id:
            view["result_id"] = self.result_id
        return view


class JobManager:
    """Single in-flight ask for one bridge instance."""

    def __init__(
        self,
        store,
        *,
        stall_after_s: float | None = None,
        cancel_grace_s: float | None = None,
        connected_window_s: float | None = None,
        results=None,
        clock=time.monotonic,
    ) -> None:
        self.store = store
        self.results = results
        self.bridge_version = config.BRIDGE_VERSION
        self.stall_after_s = config.JOB_STALL_S if stall_after_s is None else stall_after_s
        self.cancel_grace_s = (
            config.CANCEL_GRACE_S if cancel_grace_s is None else cancel_grace_s
        )
        self.connected_window_s = (
            config.EXTENSION_CONNECTED_WINDOW_S
            if connected_window_s is None
            else connected_window_s
        )
        self._clock = clock
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._jobs: dict[str, Job] = {}
        self._hellos: dict[str, tuple] = {}
        self._last_hello_kind: str | None = None

    def connected(self, kind: str = DEFAULT_CLIENT_KIND) -> bool:
        with self._lock:
            return self._connected_locked(kind)

    def _connected_locked(self, kind: str = DEFAULT_CLIENT_KIND) -> bool:
        entry = self._hellos.get(kind)
        if entry is None:
            return False
        return (self._clock() - entry[0]) <= self.connected_window_s

    def job_executor(self) -> str:
        return DEFAULT_CLIENT_KIND

    def hello(self, payload: dict) -> dict:
        proto = payload.get("proto")
        if proto != config.PROTO_VERSION:
            raise BridgeError(
                "E_PROTO_MISMATCH",
                "hello",
                f"unsupported proto {proto!r}; bridge speaks proto {config.PROTO_VERSION}",
                400,
            )
        kind = payload.get("client", DEFAULT_CLIENT_KIND)
        if kind not in CLIENT_KINDS:
            raise BridgeError(
                "E_INTERNAL",
                "hello",
                f"client must be one of {', '.join(CLIENT_KINDS)}",
                400,
            )
        capabilities = payload.get("capabilities")
        if capabilities is not None:
            if not isinstance(capabilities, list) or len(capabilities) > 16:
                raise BridgeError(
                    "E_INTERNAL",
                    "hello",
                    "capabilities must be a list of at most 16 strings",
                    400,
                )
            for capability in capabilities:
                if not isinstance(capability, str) or not capability or len(capability) > 64:
                    raise BridgeError(
                        "E_INTERNAL",
                        "hello",
                        "each capability must be a non-empty string",
                        400,
                    )
                if capability in ("conversation_open", "conversation_author", "deep_research", "web_search"):
                    raise BridgeError(
                        "E_INTERNAL",
                        "hello",
                        f"capability {capability!r} is not available in this build",
                        400,
                    )
        with self._condition:
            now = self._clock()
            self._hellos[kind] = (now, utc_now_iso())
            self._last_hello_kind = kind
            return {
                "ok": True,
                "proto": config.PROTO_VERSION,
                "bridge_version": self.bridge_version,
                "server_time": utc_now_iso(),
            }

    def status(self) -> dict:
        with self._lock:
            active = sum(1 for job in self._jobs.values() if job.status in ACTIVE_STATUSES)
            last = self._hellos.get(DEFAULT_CLIENT_KIND)
            return {
                "ok": True,
                "api_version": config.API_VERSION,
                "proto": config.PROTO_VERSION,
                "client": {
                    "kind": self._last_hello_kind,
                    "connected": self._connected_locked(DEFAULT_CLIENT_KIND),
                    "last_seen": last[1] if last else None,
                },
                "job_executor": self.job_executor(),
                "jobs": {"active": active, "total": len(self._jobs)},
            }

    def create_job(self, request: dict) -> Job:
        if not isinstance(request, dict):
            raise BridgeError("E_INTERNAL", "create_job", "job must be an object", 400)
        kind = request.get("kind", "ask")
        if kind != "ask":
            raise BridgeError(
                "E_INTERNAL",
                "kind",
                "only ask jobs are available in this build",
                400,
            )
        mode = request.get("mode", None)
        if mode is not None:
            code = REMOVED_MODES.get(mode, "E_INTERNAL")
            raise BridgeError(
                code,
                "mode",
                "unsupported mode; nothing was queued",
                400,
            )
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise BridgeError(
                "E_INTERNAL", "create_job", "prompt must be a non-empty string", 400
            )
        files = request.get("files") or []
        if not isinstance(files, list) or any(not isinstance(item, str) for item in files):
            raise BridgeError(
                "E_INTERNAL", "create_job", "files must be a list of file ids", 400
            )
        if files:
            raise BridgeError(
                "E_UPLOAD_FAILED",
                "upload",
                config.UPLOAD_UNAVAILABLE,
                400,
            )
        timeout_s = request.get("timeout_s", config.DEFAULT_ASK_TIMEOUT_S)
        if (
            not isinstance(timeout_s, int)
            or isinstance(timeout_s, bool)
            or not 1 <= timeout_s <= config.MAX_ASK_TIMEOUT_S
        ):
            raise BridgeError(
                "E_INTERNAL",
                "create_job",
                f"timeout_s must be an integer in 1..{config.MAX_ASK_TIMEOUT_S}",
                400,
            )
        new_chat = request.get("new_chat", True)
        if not isinstance(new_chat, bool):
            raise BridgeError("E_INTERNAL", "create_job", "new_chat must be boolean", 400)
        project = None
        project_name = request.get("project")
        if project_name is not None:
            if not isinstance(project_name, str) or not project_name:
                raise BridgeError(
                    "E_INTERNAL",
                    "create_job",
                    "project must be a non-empty string",
                    400,
                )
            project = projects.resolve(project_name, state_dir=self.store)
            if project is None or not project.get("url"):
                raise BridgeError(
                    "E_PROJECT_NOT_CONFIGURED",
                    "create_job",
                    f"project {project_name!r} is not configured on this bridge",
                    400,
                )
        with self._condition:
            if not self._connected_locked(DEFAULT_CLIENT_KIND):
                raise BridgeError(
                    "E_INTERNAL",
                    "create_job",
                    f"{DEFAULT_CLIENT_KIND} not connected",
                    503,
                )
            for job in self._jobs.values():
                if job.status in ACTIVE_STATUSES:
                    raise BridgeError(
                        "E_BUSY", "create_job", "a job is already in flight", 409
                    )
            now_mono = self._clock()
            now_iso = utc_now_iso()
            job = Job(
                job_id=secrets.token_hex(8),
                kind="ask",
                prompt=prompt,
                files=[],
                new_chat=new_chat,
                timeout_s=timeout_s,
                project=project,
                mode=None,
                created_at=now_iso,
                updated_at=now_iso,
                started_mono=now_mono,
                last_progress_mono=now_mono,
                deadline_mono=now_mono + timeout_s,
            )
            self._append_locked(job, "status", {"status": "queued"})
            self._jobs[job.job_id] = job
            self._condition.notify_all()
            return job

    def next_offer(self, wait_s: float, kind: str = DEFAULT_CLIENT_KIND):
        if kind not in CLIENT_KINDS:
            raise BridgeError(
                "E_INTERNAL",
                "next",
                f"client must be one of {', '.join(CLIENT_KINDS)}",
                400,
            )
        deadline = self._clock() + max(wait_s, 0.0)
        with self._condition:
            while True:
                for job in self._jobs.values():
                    if job.status == "queued" and job.kind == "ask" and job.mode is None:
                        job.status = "offered"
                        job.last_progress_mono = self._clock()
                        self._append_locked(job, "status", {"status": "offered"})
                        return job
                remaining = deadline - self._clock()
                if remaining <= 0:
                    return None
                self._condition.wait(remaining)

    def append_events(self, job_id: str, events: list) -> dict:
        with self._condition:
            job = self._get_locked(job_id)
            if job.status in TERMINAL_STATUSES:
                return {"ok": True, "cancel_requested": job.cancel_requested}
            for event in events:
                if not isinstance(event, dict):
                    raise BridgeError(
                        "E_INTERNAL", "events", "each event must be an object", 400
                    )
                event_type = event.get("type")
                if not isinstance(event_type, str) or not event_type:
                    raise BridgeError(
                        "E_INTERNAL", "events", "event type must be a string", 400
                    )
                data = event.get("data")
                if not isinstance(data, dict):
                    raise BridgeError(
                        "E_INTERNAL", "events", "event data must be an object", 400
                    )
                self._append_locked(job, event_type, data)
                job.last_progress_mono = self._clock()
                if data.get("status") == "accepted" and job.status == "offered":
                    job.status = "running"
                elif job.status == "offered" and event_type != "status":
                    job.status = "running"
            return {"ok": True, "cancel_requested": job.cancel_requested}

    def resolve(self, job_id: str, result: dict) -> str:
        with self._condition:
            job = self._get_locked(job_id)
            if job.status in TERMINAL_STATUSES:
                return job.status
            status = result.get("status")
            if not isinstance(status, str) or status not in TERMINAL_STATUSES:
                raise BridgeError("E_INTERNAL", "result", "status is required", 400)
            url = result.get("url")
            if url is not None and not isinstance(url, str):
                raise BridgeError("E_INTERNAL", "result", "url must be a string", 400)
            if status == "done":
                answer = result.get("answer")
                if not isinstance(answer, str) or not answer.strip():
                    raise BridgeError(
                        "E_RESPONSE_EMPTY",
                        "result",
                        "a done result requires a non-empty answer",
                        400,
                    )
                job.result = {"answer": answer, "error_code": None, "url": url}
                if self.results is not None:
                    job.result_id = self.results.put_text(job.job_id, answer, url)
            elif status == "cancelled":
                job.result = {"answer": None, "error_code": "E_CANCELLED", "url": url}
            else:
                code = result.get("error_code") or "E_INTERNAL"
                if code not in errors.ERROR_CODES:
                    code = "E_INTERNAL"
                step = result.get("step")
                job.result = {
                    "answer": None,
                    "error_code": code,
                    "step": step if isinstance(step, str) else None,
                    "url": url,
                }
            job.status = status
            self._append_locked(
                job,
                "status",
                {"status": status, "error_code": (job.result or {}).get("error_code")},
            )
            self._persist_locked(job)
            self._condition.notify_all()
            return job.status

    def cancel(self, job_id: str) -> str:
        with self._condition:
            job = self._get_locked(job_id)
            if job.status in TERMINAL_STATUSES:
                return job.status
            if job.status == "queued":
                job.status = "cancelled"
                job.result = {"answer": None, "error_code": "E_CANCELLED", "url": None}
                self._append_locked(
                    job, "status", {"status": "cancelled", "error_code": "E_CANCELLED"}
                )
                self._persist_locked(job)
                self._condition.notify_all()
                return job.status
            if not job.cancel_requested:
                job.cancel_requested = True
                job.cancel_mono = self._clock()
                self._append_locked(job, "status", {"status": "cancel_requested"})
            return job.status

    def get(self, job_id: str, since: int = 0) -> dict:
        with self._lock:
            job = self._get_locked(job_id)
            events = [event for event in job.events if event.get("seq", 0) > since]
            return {"ok": True, "job": job.view(), "events": events}

    def watchdog(self) -> None:
        with self._condition:
            now = self._clock()
            for job in list(self._jobs.values()):
                if job.status in TERMINAL_STATUSES:
                    continue
                if now >= job.deadline_mono:
                    self._fail_locked(job, "E_RESPONSE_TIMEOUT", "deadline")
                    continue
                if job.cancel_requested and (now - job.cancel_mono) >= self.cancel_grace_s:
                    job.status = "cancelled"
                    job.result = {"answer": None, "error_code": "E_CANCELLED", "url": None}
                    self._append_locked(
                        job,
                        "status",
                        {"status": "cancelled", "error_code": "E_CANCELLED"},
                    )
                    self._persist_locked(job)
                    continue
                if (
                    job.status in ("offered", "running")
                    and (now - job.last_progress_mono) > self.stall_after_s
                ):
                    self._fail_locked(job, "E_STALL", "watchdog")

    def _fail_locked(self, job: Job, code: str, step: str) -> None:
        if job.status in TERMINAL_STATUSES:
            return
        job.status = "failed"
        job.result = {"answer": None, "error_code": code, "step": step, "url": None}
        self._append_locked(job, "error", {"code": code, "step": step})
        self._persist_locked(job)
        self._condition.notify_all()

    def _get_locked(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise BridgeError("E_INTERNAL", "job", "job not found", 404)
        return job

    def _append_locked(self, job: Job, event_type: str, data: dict) -> None:
        seq = job.last_seq + 1
        job.events.append({"seq": seq, "type": event_type, "data": data})
        job.last_seq = seq
        job.updated_at = utc_now_iso()

    def _persist_locked(self, job: Job) -> None:
        try:
            self.store.save_job(job.job_id, job.record())
        except OSError:
            pass
