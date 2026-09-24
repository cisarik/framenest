"""Durable one-flight capture lifecycle with fenced, single-use send permission."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import secrets
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from kronika_capture import config, errors, projects
from kronika_capture.bridge.journal import Journal, JournalUnavailable

ACTIVE_STATUSES = ("queued", "offered", "running", "needs_admin")
TERMINAL_STATUSES = ("done", "failed", "cancelled")
CLIENT_KINDS = ("headless",)
DEFAULT_CLIENT_KIND = "headless"
REMOVED_MODES = {"web_search": "E_WEB_SEARCH_UNAVAILABLE", "deep_research": "E_DEEP_RESEARCH_UNAVAILABLE"}
ADMIN_REASONS = {"E_LOGIN_REQUIRED", "E_CAPTCHA_REQUIRED", "E_CONSENT_REQUIRED",
                 "E_LIMIT_REACHED", "E_COMPOSER_NOT_FOUND", "E_NEEDS_ADMIN"}
PHASES = {"queued", "offered", "accepted", "project", "new_chat", "tab_ready",
          "composed", "sent", "observing", "cleanup", "project_warning", "cleanup_warning"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BridgeError(Exception):
    def __init__(self, code: str, step: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code, self.step, self.message, self.status = code, step, message, status


def failure(code, step="lifecycle", status=409):
    return BridgeError(code, step, errors.safe_message(code), status)


def identity(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except ValueError:
        return False


@dataclass
class Job:
    job_id: str
    request_id: str
    fingerprint: str
    kind: str = "ask"
    prompt: str = ""
    files: list = field(default_factory=list)
    new_chat: bool = True
    timeout_s: int = config.DEFAULT_ASK_TIMEOUT_S
    project: dict | None = None
    mode: str | None = None
    status: str = "queued"
    phase: str = "queued"
    created_at: str = ""
    updated_at: str = ""
    events: list = field(default_factory=list)
    result: dict | None = None
    result_id: str | None = None
    delivery_id: str | None = None
    delivery_digest: str | None = None
    cancel_requested: bool = False
    last_seq: int = 0
    started_mono: float = 0.0
    last_progress_mono: float = 0.0
    deadline_mono: float = 0.0
    cancel_mono: float = 0.0
    created_wall: float = 0.0
    terminal_wall: float | None = None
    runner_id: str | None = None
    offer_id: str | None = None
    epoch: str | None = None
    submission: str = "not_started"
    response_id: str | None = None
    intervention_id: str | None = None
    intervention_reason: str | None = None
    admin_started: float | None = None
    admin_started_wall: float | None = None
    admin_wait_s: float = 0.0

    def record(self):
        return asdict(self)

    def offer(self):
        return {key: copy.deepcopy(getattr(self, key)) for key in (
            "job_id", "request_id", "kind", "prompt", "files", "new_chat",
            "timeout_s", "project", "mode", "runner_id", "offer_id", "epoch"
        )}

    def metadata(self, now):
        wait = self.admin_wait_s + (max(0, now - self.admin_started) if self.admin_started is not None else 0)
        return {"job_id": self.job_id, "status": self.status, "phase": self.phase,
                "submission": self.submission, "intervention_id": self.intervention_id,
                "intervention_reason": self.intervention_reason, "admin_wait_s": wait,
                "cancel_requested": self.cancel_requested}

    def view(self, now=0):
        return {**self.metadata(now), "request_id": self.request_id, "kind": self.kind,
                "created_at": self.created_at, "updated_at": self.updated_at,
                "timeout_s": self.timeout_s, "result": copy.deepcopy(self.result),
                "result_id": self.result_id}


class JobManager:
    """Single owner of journal, service state and active slot; publish only committed copies."""

    def __init__(self, store, *, stall_after_s=None, cancel_grace_s=None,
                 connected_window_s=None, results=None, clock=time.monotonic,
                 wall_clock=time.time, journal=None):
        self.store = store
        self._clock, self._wall = clock, wall_clock
        self.stall_after_s = config.JOB_STALL_S if stall_after_s is None else stall_after_s
        self.cancel_grace_s = config.CANCEL_GRACE_S if cancel_grace_s is None else cancel_grace_s
        self.connected_window_s = config.EXTENSION_CONNECTED_WINDOW_S if connected_window_s is None else connected_window_s
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._last_hello = None
        self._last_hello_iso = None
        self._unavailable = False
        self._jobs = {}
        self._service = {}
        try:
            self.journal = journal or Journal(store.root)
            records, previous = self.journal.load()
            if (not isinstance(previous, dict) or len(records) > config.JOB_RETENTION_MAX_ITEMS
                or (previous and (not identity(previous.get("epoch"))
                    or previous.get("state") not in ("starting", "ready", "needs_admin", "browser_unavailable")))):
                raise ValueError()
            self._jobs = {r["job_id"]: Job(**r) for r in records}
            if len(self._jobs) != len(records) or len({j.request_id for j in self._jobs.values()}) != len(records):
                raise ValueError()
            for job in self._jobs.values():
                if (not identity(job.request_id) or job.status not in ACTIVE_STATUSES + TERMINAL_STATUSES
                    or job.submission not in ("not_started", "send_intent_persisted", "send_confirmed")
                    or not math.isfinite(job.created_wall)
                    or (job.terminal_wall is not None and not math.isfinite(job.terminal_wall))):
                    raise ValueError()
            blocked = previous.get("state") in ("needs_admin", "browser_unavailable")
            for job in self._jobs.values():
                if job.status in ("offered", "running", "needs_admin"):
                    if job.admin_started_wall is not None:
                        job.admin_wait_s += max(0, min(config.ADMIN_WAIT_MAX_S, self._wall() - job.admin_started_wall))
                        job.admin_started = None
                        job.admin_started_wall = None
                    self._terminal(job, "E_AMBIGUOUS_SEND", "recovery")
                    blocked = True
                elif job.status == "queued":
                    elapsed = self._wall() - job.created_wall
                    if job.admin_started_wall is not None:
                        job.admin_wait_s += max(0, self._wall() - job.admin_started_wall)
                        job.admin_started, job.admin_started_wall = self._clock(), self._wall()
                        blocked = True
                    active_elapsed = elapsed - job.admin_wait_s
                    if job.admin_wait_s >= config.ADMIN_WAIT_MAX_S:
                        self._terminal(job, "E_INTERVENTION_TIMEOUT", "recovery")
                    elif elapsed < 0 or active_elapsed >= job.timeout_s:
                        self._terminal(job, "E_RESPONSE_TIMEOUT", "recovery")
                    else:
                        job.deadline_mono = self._clock() + job.timeout_s - max(0, active_elapsed)
                        job.last_progress_mono = self._clock()
            self._service = {"epoch": str(uuid.uuid4()), "state": "needs_admin" if blocked else "starting",
                             "reason": "E_AMBIGUOUS_SEND" if blocked else None,
                             "runner_id": None, "browser_session": None, "adapter": None,
                             "intervention_id": str(uuid.uuid4()) if blocked else None,
                             "resume_id": None}
            self._prune_memory(self._jobs)
            self.journal.commit([j.record() for j in self._jobs.values()], self._service,
                                expected_epoch=previous.get("epoch"))
        except (JournalUnavailable, TypeError, ValueError, KeyError):
            if hasattr(self, "journal"):
                self.journal.close()
            raise failure("E_JOURNAL_UNAVAILABLE", "recovery", 503) from None

    def _commit(self, job=None, service=None, *, jobs=None):
        if self._unavailable:
            raise failure("E_JOURNAL_UNAVAILABLE", status=503)
        candidate = dict(self._jobs) if jobs is None else jobs
        if job is not None:
            candidate[job.job_id] = job
        state = dict(self._service) if service is None else service
        try:
            self.journal.commit([j.record() for j in candidate.values()], state,
                                expected_epoch=self._service["epoch"])
        except JournalUnavailable:
            self._unavailable = True
            raise failure("E_JOURNAL_UNAVAILABLE", status=503) from None
        self._jobs, self._service = candidate, state
        self._condition.notify_all()

    def _prune_memory(self, jobs):
        cutoff = self._wall() - config.JOB_RETENTION_MAX_AGE_S
        for key, job in list(jobs.items()):
            if job.status in TERMINAL_STATUSES and job.terminal_wall is not None and job.terminal_wall <= cutoff:
                del jobs[key]

    def _connected_locked(self, kind=DEFAULT_CLIENT_KIND):
        return kind == DEFAULT_CLIENT_KIND and self._last_hello is not None and 0 <= self._clock() - self._last_hello <= self.connected_window_s

    def connected(self, kind=DEFAULT_CLIENT_KIND):
        with self._lock:
            return self._connected_locked(kind)

    def job_executor(self):
        return DEFAULT_CLIENT_KIND

    def _block(self, state, reason, *, browser=False):
        state.update(state="browser_unavailable" if browser else "needs_admin", reason=reason,
                     intervention_id=state.get("intervention_id") or str(uuid.uuid4()), resume_id=None)

    def hello(self, payload):
        if payload.get("proto") != config.PROTO_VERSION:
            raise failure("E_PROTO_MISMATCH", "hello", 400)
        if payload.get("client", DEFAULT_CLIENT_KIND) != DEFAULT_CLIENT_KIND:
            raise failure("E_INTERNAL", "hello", 400)
        rid, bid = payload.get("runner_id"), payload.get("browser_session")
        if not identity(rid) or not identity(bid):
            raise failure("E_INTERNAL", "hello", 400)
        capabilities = payload.get("capabilities", [])
        if not isinstance(capabilities, list) or any(x not in ("durable_submission", "admin_resume") for x in capabilities) or len(capabilities) > 2:
            raise failure("E_INTERNAL", "hello", 400)
        ready = payload.get("readiness")
        if not isinstance(ready, dict) or ready.get("state") not in ("ready", "needs_admin", "browser_unavailable"):
            raise failure("E_INTERNAL", "hello", 400)
        with self._condition:
            state = dict(self._service)
            changed_runner = state["runner_id"] not in (None, rid)
            changed_browser = state["browser_session"] not in (None, bid)
            if changed_runner or changed_browser:
                if changed_runner and self._connected_locked():
                    raise failure("E_BUSY", "hello")
                for original in list(self._jobs.values()):
                    if original.status in ("offered", "running", "needs_admin"):
                        job = copy.deepcopy(original)
                        self._terminal(job, "E_AMBIGUOUS_SEND", "runner_lost")
                        self._block(state, "E_AMBIGUOUS_SEND")
                        self._commit(job, state)
            state.update(runner_id=rid, browser_session=bid,
                         adapter={"pack_version": config.PACK_VERSION})
            active = self._active()
            queued = copy.deepcopy(active) if active and active.status == "queued" else None
            if ready["state"] != "ready":
                reason = ready.get("reason")
                if not isinstance(reason, str) or reason not in ADMIN_REASONS | {"E_BROWSER_UNAVAILABLE", "E_AMBIGUOUS_SEND"}:
                    reason = "E_NEEDS_ADMIN"
                # Preserve the pending explicit resume until its check is acknowledged.
                resume_id = state["resume_id"]
                self._block(state, reason, browser=ready["state"] == "browser_unavailable")
                if payload.get("resume_id") != resume_id:
                    state["resume_id"] = resume_id
                if queued is not None:
                    if queued.admin_started is None:
                        queued.admin_started, queued.admin_started_wall = self._clock(), self._wall()
                        queued.intervention_id = str(uuid.uuid4())
                    queued.intervention_reason = reason
                    state["intervention_id"] = queued.intervention_id
            elif state["state"] == "starting" or (
                (active is None or active.status == "queued") and state["resume_id"] is not None
                and payload.get("resume_id") == state["resume_id"]
            ):
                if queued is not None and queued.admin_started is not None:
                    waited = max(0, self._clock() - queued.admin_started)
                    if queued.admin_wait_s + waited >= config.ADMIN_WAIT_MAX_S:
                        self._terminal(queued, "E_INTERVENTION_TIMEOUT", "intervention")
                    else:
                        queued.admin_wait_s += waited
                        queued.deadline_mono += waited
                        queued.admin_started = queued.admin_started_wall = None
                        queued.intervention_id = queued.intervention_reason = None
                if queued is None or queued.status == "queued":
                    state.update(state="ready", reason=None, intervention_id=None, resume_id=None)
            self._commit(queued, service=state)
            self._last_hello = self._clock()
            self._last_hello_iso = utc_now_iso()
            return {"ok": True, "proto": config.PROTO_VERSION, "bridge_version": config.BRIDGE_VERSION,
                    "server_time": utc_now_iso(), **self._control()}

    def _active(self):
        return next((j for j in self._jobs.values() if j.status in ACTIVE_STATUSES), None)

    def _control(self, job=None):
        return {"epoch": self._service["epoch"], "service_state": self._service["state"],
                "resume_id": self._service["resume_id"],
                "intervention_id": job.intervention_id if job else self._service["intervention_id"],
                "cancel_requested": bool(job and job.cancel_requested),
                "terminal": bool(job and job.status in TERMINAL_STATUSES)}

    def status(self):
        with self._lock:
            active = self._active()
            state = self._service["state"]
            if self._unavailable:
                state = "browser_unavailable"
            elif state == "ready" and not self._connected_locked():
                state = "browser_unavailable"
            return {"ok": True, "api_version": config.API_VERSION, "proto": config.PROTO_VERSION,
                    "client": {"kind": DEFAULT_CLIENT_KIND if self._last_hello is not None else None,
                               "connected": self._connected_locked(), "last_seen": self._last_hello_iso},
                    "job_executor": DEFAULT_CLIENT_KIND,
                    "jobs": {"active": int(active is not None), "total": len(self._jobs)},
                    "readiness": state,
                    "reason": "E_JOURNAL_UNAVAILABLE" if self._unavailable else self._service["reason"],
                    "capabilities": ["ask", "durable_submission", "admin_resume"],
                    "browser_session": self._service["browser_session"], "adapter": self._service["adapter"],
                    "intervention_id": (active.intervention_id if active else None) or self._service["intervention_id"],
                    "active_job": active.metadata(self._clock()) if active else None}

    def create_job(self, request):
        if not isinstance(request, dict):
            raise failure("E_INTERNAL", "admission", 400)
        kind, mode = request.get("kind", "ask"), request.get("mode")
        if kind != "ask":
            raise failure("E_INTERNAL", "kind", 400)
        if mode is not None:
            code = REMOVED_MODES.get(mode, "E_INTERNAL") if isinstance(mode, str) else "E_INTERNAL"
            raise BridgeError(code, "mode", "unsupported mode; nothing was queued", 400)
        prompt = request.get("prompt")
        files = request.get("files", [])
        if not isinstance(files, list) or any(not isinstance(x, str) for x in files):
            raise failure("E_INTERNAL", "files", 400)
        if files:
            raise BridgeError("E_UPLOAD_FAILED", "upload", config.UPLOAD_UNAVAILABLE, 400)
        timeout = request.get("timeout_s", config.DEFAULT_ASK_TIMEOUT_S)
        new_chat, project_name = request.get("new_chat", True), request.get("project")
        rid = request.get("request_id")
        if (not identity(rid) or not isinstance(prompt, str) or not prompt.strip()
            or type(timeout) is not int or not 1 <= timeout <= config.MAX_ASK_TIMEOUT_S
            or type(new_chat) is not bool
            or (project_name is not None and (not isinstance(project_name, str) or not project_name))):
            raise failure("E_INTERNAL", "admission", 400)
        immutable = {"prompt": prompt, "files": [], "timeout_s": timeout, "new_chat": new_chat,
                     "project": project_name, "kind": "ask", "mode": None}
        fingerprint = hashlib.sha256(json.dumps(immutable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self._condition:
            for original in self._jobs.values():
                if original.request_id == rid:
                    if original.fingerprint != fingerprint:
                        raise failure("E_IDEMPOTENCY_CONFLICT", "admission")
                    return copy.deepcopy(original)
            if self._unavailable:
                raise failure("E_JOURNAL_UNAVAILABLE", status=503)
            if self._active():
                raise failure("E_BUSY", "admission")
            if self._service["state"] == "needs_admin":
                raise failure("E_NEEDS_ADMIN", "admission", 503)
            if self._service["state"] != "ready" or not self._connected_locked():
                raise failure("E_BROWSER_UNAVAILABLE", "admission", 503)
            retained = dict(self._jobs)
            self._prune_memory(retained)
            if len(retained) >= config.JOB_RETENTION_MAX_ITEMS:
                raise failure("E_SERVICE_LIMIT", "admission", 429)
            project = projects.resolve(project_name, state_dir=self.store) if project_name else None
            if project_name and (not project or not project.get("url")):
                raise failure("E_PROJECT_NOT_CONFIGURED", "admission", 400)
            now = self._clock()
            job = Job(job_id=secrets.token_hex(8), request_id=rid, fingerprint=fingerprint,
                      prompt=prompt, timeout_s=timeout, new_chat=new_chat, project=project,
                      created_at=utc_now_iso(), created_wall=self._wall(), started_mono=now,
                      deadline_mono=now + timeout, last_progress_mono=now)
            self._event(job, "status", {"status": "queued"})
            self._commit(job, jobs=retained)
            return copy.deepcopy(job)

    def _runner(self, payload):
        if (payload.get("runner_id") != self._service["runner_id"]
            or payload.get("epoch") != self._service["epoch"] or not self._connected_locked()):
            raise failure("E_AMBIGUOUS_SEND", "identity")
        if self._unavailable:
            raise failure("E_JOURNAL_UNAVAILABLE", status=503)

    def next_offer(self, wait_s, kind=DEFAULT_CLIENT_KIND, *, runner_id=None, epoch=None):
        if kind not in CLIENT_KINDS:
            raise failure("E_INTERNAL", "next", 400)
        deadline = self._clock() + max(0, min(wait_s, config.NEXT_WAIT_MAX_S))
        with self._condition:
            while True:
                self._runner({"runner_id": runner_id, "epoch": epoch})
                if self._service["state"] == "ready":
                    for original in self._jobs.values():
                        if original.status == "queued" and original.admin_started is None:
                            job = copy.deepcopy(original)
                            job.status, job.phase = "offered", "offered"
                            job.runner_id, job.epoch = runner_id, epoch
                            job.offer_id = str(uuid.uuid4())
                            job.last_progress_mono = self._clock()
                            self._event(job, "status", {"status": "offered"})
                            self._commit(job)
                            return copy.deepcopy(job)
                remaining = deadline - self._clock()
                if remaining <= 0:
                    return None
                self._condition.wait(remaining)

    def _get(self, job_id):
        if job_id not in self._jobs:
            raise BridgeError("E_INTERNAL", "job", "job not found", 404)
        return self._jobs[job_id]

    def _fence(self, job, payload):
        self._runner(payload)
        if job.runner_id != payload.get("runner_id") or job.offer_id != payload.get("offer_id") or job.epoch != payload.get("epoch"):
            raise failure("E_AMBIGUOUS_SEND", "offer")

    def append_events(self, job_id, events, envelope=None):
        envelope = envelope or {}
        if not isinstance(events, list) or len(events) > 16:
            raise failure("E_INTERNAL", "events", 400)
        with self._condition:
            job = copy.deepcopy(self._get(job_id))
            self._fence(job, envelope)
            if job.status in TERMINAL_STATUSES:
                return {"ok": True, **self._control(job)}
            state = dict(self._service)
            for event in events:
                if not isinstance(event, dict) or not isinstance(event.get("data"), dict):
                    raise failure("E_INTERNAL", "events", 400)
                typ, data = event.get("type"), event["data"]
                if typ == "status" and data.get("status") == "accepted":
                    if job.status != "offered":
                        raise failure("E_AMBIGUOUS_SEND", "accept")
                    job.status, job.phase = "running", "accepted"
                elif typ == "send_intent":
                    if job.status != "running" or job.submission != "not_started" or job.cancel_requested or state["state"] != "ready":
                        raise failure("E_AMBIGUOUS_SEND", "send")
                    if self._clock() >= job.deadline_mono:
                        raise failure("E_RESPONSE_TIMEOUT", "send")
                    job.submission, job.phase = "send_intent_persisted", "sent"
                elif typ == "send_confirmed":
                    response = data.get("response_id")
                    if job.submission != "send_intent_persisted" or not identity(response):
                        raise failure("E_AMBIGUOUS_SEND", "send")
                    job.submission, job.response_id = "send_confirmed", response
                elif typ == "needs_admin":
                    if job.status != "running" or not isinstance(data.get("reason"), str) or data["reason"] not in ADMIN_REASONS:
                        raise failure("E_INTERNAL", "intervention", 400)
                    if job.submission == "send_intent_persisted":
                        raise failure("E_AMBIGUOUS_SEND", "intervention")
                    job.status = "needs_admin"
                    job.intervention_id = str(uuid.uuid4())
                    job.intervention_reason = data["reason"]
                    job.admin_started = self._clock()
                    job.admin_started_wall = self._wall()
                    self._block(state, data["reason"])
                    state["intervention_id"] = job.intervention_id
                elif typ == "resumed":
                    if (job.status != "needs_admin" or state["resume_id"] is None
                        or data.get("resume_id") != state["resume_id"]
                        or data.get("intervention_id") != job.intervention_id
                        or data.get("ready") is not True
                        or (job.submission == "send_confirmed" and data.get("response_id") != job.response_id)):
                        raise failure("E_AMBIGUOUS_SEND", "resume")
                    waited = max(0, self._clock() - job.admin_started)
                    if job.admin_wait_s + waited >= config.ADMIN_WAIT_MAX_S:
                        self._terminal(job, "E_INTERVENTION_TIMEOUT", "intervention")
                    else:
                        job.admin_wait_s += waited
                        job.deadline_mono += waited
                        job.admin_started = None
                        job.admin_started_wall = None
                        job.status = "running"
                        job.intervention_id = job.intervention_reason = None
                        state.update(state="ready", reason=None, intervention_id=None, resume_id=None)
                elif typ == "progress":
                    phase = data.get("phase")
                    if not isinstance(phase, str) or phase not in PHASES:
                        raise failure("E_INTERNAL", "progress", 400)
                    job.phase = phase
                elif typ != "heartbeat":
                    raise failure("E_INTERNAL", "events", 400)
                self._event(job, typ, {"phase": job.phase, "status": job.status})
            job.last_progress_mono = self._clock()
            self._commit(job, state)
            return {"ok": True, "submission": job.submission, **self._control(job)}

    def resume(self, payload):
        with self._condition:
            active = self._active()
            expected_job = active.job_id if active else None
            intervention = (active.intervention_id if active else None) or self._service["intervention_id"]
            if (self._service["state"] not in ("needs_admin", "browser_unavailable")
                or not intervention or payload.get("job_id") != expected_job
                or payload.get("intervention_id") != intervention):
                raise failure("E_IDEMPOTENCY_CONFLICT", "resume")
            state = dict(self._service)
            state["resume_id"] = state["resume_id"] or str(uuid.uuid4())
            self._commit(service=state)
            return {"ok": True, "status": "readiness_pending", "resume_id": state["resume_id"]}

    def resolve(self, job_id, result):
        with self._condition:
            job = copy.deepcopy(self._get(job_id))
            self._fence(job, result)
            delivery = result.get("delivery_id")
            if not identity(delivery):
                raise failure("E_INTERNAL", "result", 400)
            digest = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if job.status in TERMINAL_STATUSES:
                if job.delivery_id and (job.delivery_id != delivery or job.delivery_digest != digest):
                    raise failure("E_IDEMPOTENCY_CONFLICT", "result")
                return job.status
            status = result.get("status")
            if status not in TERMINAL_STATUSES:
                raise failure("E_INTERNAL", "result", 400)
            if status == "done":
                if job.submission != "send_confirmed":
                    raise failure("E_AMBIGUOUS_SEND", "result")
                answer = result.get("answer")
                if not isinstance(answer, str) or not answer.strip():
                    raise failure("E_RESPONSE_EMPTY", "result", 400)
                url = result.get("url")
                if url is not None and not isinstance(url, str):
                    raise failure("E_INTERNAL", "result", 400)
                job.result = {"answer": answer, "error_code": None, "url": url}
                job.result_id = job.job_id
                job.status, job.terminal_wall = "done", self._wall()
            else:
                code = "E_CANCELLED" if status == "cancelled" else result.get("error_code", "E_INTERNAL")
                self._terminal(job, code if code in errors.ERROR_CODES else "E_INTERNAL", "runner")
            job.delivery_id, job.delivery_digest = delivery, digest
            self._event(job, "status", {"status": job.status})
            state = dict(self._service)
            if result.get("activity_stopped") is not True or (job.result or {}).get("error_code") == "E_AMBIGUOUS_SEND":
                self._block(state, "E_AMBIGUOUS_SEND")
            self._commit(job, state)
            return job.status

    def cancel(self, job_id):
        with self._condition:
            job = copy.deepcopy(self._get(job_id))
            if job.status in TERMINAL_STATUSES:
                return job.status
            if job.status == "queued":
                self._terminal(job, "E_CANCELLED", "cancel")
            elif not job.cancel_requested:
                job.cancel_requested, job.cancel_mono = True, self._clock()
            self._commit(job)
            return job.status

    def get(self, job_id, since=0):
        with self._lock:
            job = self._get(job_id)
            return {"ok": True, "job": job.view(self._clock()),
                    "events": copy.deepcopy([e for e in job.events if e["seq"] > since])}

    def result_record(self, result_id):
        with self._lock:
            job = self._jobs.get(result_id)
            if job is None or job.status != "done":
                return None
            return {"result_id": result_id, "job_id": job.job_id, "text": job.result["answer"], "url": job.result["url"]}

    def watchdog(self):
        with self._condition:
            now = self._clock()
            for original in list(self._jobs.values()):
                if original.status in TERMINAL_STATUSES:
                    continue
                job = copy.deepcopy(original)
                code = None
                if job.cancel_requested and now - job.cancel_mono >= self.cancel_grace_s:
                    code = "E_CANCELLED"
                elif job.admin_started is not None:
                    if job.admin_wait_s + max(0, now - job.admin_started) >= config.ADMIN_WAIT_MAX_S:
                        code = "E_INTERVENTION_TIMEOUT"
                elif now >= job.deadline_mono:
                    code = "E_RESPONSE_TIMEOUT"
                elif job.status in ("offered", "running") and now - job.last_progress_mono > self.stall_after_s:
                    code = "E_AMBIGUOUS_SEND"
                if code:
                    state = dict(self._service)
                    if job.status != "queued":
                        self._block(state, code)
                    self._terminal(job, code, "watchdog")
                    self._commit(job, state)
            retained = dict(self._jobs)
            self._prune_memory(retained)
            if len(retained) != len(self._jobs):
                self._commit(jobs=retained)

    def _terminal(self, job, code, step):
        job.status = "cancelled" if code == "E_CANCELLED" else "failed"
        job.result = {"answer": None, "error_code": code, "step": step, "url": None}
        job.terminal_wall = self._wall()
        if job.admin_started is not None:
            job.admin_wait_s += max(0, self._clock() - job.admin_started)
            job.admin_started = None
            job.admin_started_wall = None
        self._event(job, "status", {"status": job.status, "error_code": code})

    def _event(self, job, typ, data):
        job.last_seq += 1
        job.updated_at = utc_now_iso()
        job.events.append({"seq": job.last_seq, "type": typ, "data": data})
        job.events = job.events[-config.JOB_EVENT_MAX_ITEMS:]
