# ADR-0039: Lifecycle-Owned Upload Validation Orchestration

## Status

`Accepted`

## Decision Date

2026-07-14

## Context

ADR-0037 established durable upload sessions and quarantine transport. ADR-0038
established bounded internal media validation, but validation was not yet owned
by the FastAPI application lifecycle or triggered from durable upload
completion.

The `/complete` endpoint must preserve its public contract: it durably advances
a complete upload to `received` and returns that received snapshot. Hashing,
filesystem inspection, SQLite validation writes, and `ffprobe` execution can be
slow or blocking and must not run in the ASGI request path or block the event
loop.

## Decision

FrameNest owns upload-validation orchestration through one internal application
coordinator created by the FastAPI application lifecycle. A successful
`POST /api/uploads/{upload_id}/complete` persists `received`, returns the
existing received response, and then wakes the coordinator. The endpoint does
not wait for validation and does not expose a validation result. If coordinator
notification fails after durable completion, the received response is preserved
and the durable row remains recoverable.

The coordinator uses one bounded consumer by default. It discovers durable
validation candidates in bounded batches, coalesces duplicate wakeups, and runs
blocking validation work through an owned off-event-loop execution boundary.
It does not create one task per upload and does not use Starlette background
tasks as the durability mechanism.

Startup reconciliation discovers `received` and `validating` upload sessions
without delaying application readiness. `received` rows are claimed through the
existing guarded `received -> validating` transition. Startup-discovered
`validating` rows are treated as abandoned only inside the accepted
single-process model: a new process begins with no previous process-local owner,
so the same stable quarantine object can be revalidated and resolved to the
existing terminal validation outcomes.

## Boundary

This orchestration is explicitly limited to:

- one FrameNest server process;
- one Uvicorn worker;
- one upload-validation consumer;
- the loopback-first trust boundary.

It does not claim multi-process safety. There is no lease owner, heartbeat,
generation fencing, attempt counter, distributed lock, retry scheduler, or job
table.

## Failure And Recovery

`failed` remains terminal and is not discovered by startup reconciliation.
`rejected` remains terminal. `publish_pending` remains quarantined and
non-visible.

A process crash after `/complete` persists `received` but before notification is
repaired by startup discovery. A forced process termination during validation
may leave `validating`; startup recovery revalidates that stable quarantine
object without transitioning through `failed` or fabricating retry metadata.

Graceful shutdown stops claiming new uploads, wakes the runner, retains
ownership of the runner until it exits, and waits truthfully for an already
running bounded synchronous validation operation instead of pretending Python
can forcibly cancel an arbitrary running thread.

## Non-Visibility

Validation acceptance still stops at `publish_pending`. This decision creates:

- zero publication files;
- zero logical media;
- zero media locations;
- zero Gallery visibility;
- zero content-serving visibility;
- zero previews;
- zero AI analysis.

## Rejected Alternatives

### Durable Job Table

Rejected for this slice. Durable upload session state already represents work
availability for the current single-process coordinator.

### Periodic Polling

Rejected. Runtime wake notifications and startup reconciliation are sufficient
for this bounded slice.

### Automatic Retry Policy

Rejected. Failed validation remains terminal. Recovery of an abandoned
`validating` row after process loss is not the same as retrying a durable
`failed` result.

## Related Documents

- [ADR index](README.md)
- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [ADR-0038](0038-bounded-upload-media-validation.md)
- [SECURITY.md](../../SECURITY.md)
- [SPEC.md](../../SPEC.md)
