# ADR-0048: Tailscale Remote Access and Identity Foundation

## Status

`Accepted`

## Decision Date

2026-07-25

## Context

FrameNest began as a loopback-only application. The accepted remote-access
direction ([SERVER.md](../SERVER.md)) is Tailscale-only: no router port
forwarding, no public exposure, and no inference of administrator authority
from loopback, source IP, hostname, or Tailscale membership alone. The NUC
already runs a reboot-persistent `tailscaled` with an accepted MagicDNS
hostname and HTTPS capability, and Tailscale 1.98.9 supports HTTPS Serve
proxying to a Unix socket. The missing foundation was an application ingress
mode that turns that tailnet path into a trustworthy, auditable application
boundary without adding a reverse proxy, an application session system, or a
user administration UI.

## Decision

Adopt the following ingress architecture as the only remote application
path:

```text
authenticated tailnet browser
  -> Tailscale HTTPS Serve (root-owned tailscaled)
  -> permission-restricted Unix socket (/run/framenest/framenest.sock)
  -> FrameNest tailscale_uds ingress mode
```

1. **Trusted ingress is bound to provenance, not header names.** The
   application trusts `Tailscale-User-*` identity headers only when running
   in the `tailscale_uds` ingress mode, where the sole listener is a Unix
   socket inside the systemd-managed `RuntimeDirectory=framenest` (mode
   `0750`, service account only) created with `UMask=0077`. The root-owned
   `tailscaled` strips and reinjects those headers; a normal login user
   cannot open the socket, and no TCP listener remains. Uvicorn proxy-header
   processing stays disabled and arbitrary `X-Forwarded-*` values are never
   trusted.
2. **One middleware owns the boundary.** A pure ASGI middleware inspects raw
   headers, rejects duplicate or conflicting security-relevant values,
   requires `X-Forwarded-Proto: https` and the exact external forwarded host
   when Serve forwards them, resolves the exact Serve login through an
   explicit configuration identity map, and attaches an immutable identity
   context to the request scope. Missing identity yields a sanitized `401`;
   verified but unmapped or under-privileged identities yield a sanitized
   `403`. The loopback-only YouTube operator API stays unavailable remotely
   (sanitized `404`) and keeps working for a local operator through the same
   socket.
3. **Explicit mapping, no bootstrap.** Identity-to-role mapping is
   configuration-backed (`FRAMENEST_IDENTITY_MAP`), requires at least one
   exact admin login, and has no first-caller bootstrap, invitations, or
   user administration UI. `Tailscale-User-Login` is the authorization
   subject (deterministically normalized with casefold); `Tailscale-User-Name`
   is display-only and never alters privilege. The login is not treated as an
   immutable Tailscale internal user id. A schema-backed identity store
   remains a deferred migration if the configuration map outgrows its audit
   provenance or operational needs.
4. **Capabilities derive from real routes.** Every application route is
   classified by an explicit route policy (read capabilities for ordinary
   users; admin-only capabilities for metadata writes, uploads, analysis,
   library scan/import, and provider operation). The policy table is kept in
   one-to-one correspondence with the live route inventory by contract
   tests. Default posture is deny for privileged actions. The runtime
   fallback is fail-closed: a route without an explicit policy is denied
   with a sanitized `404` for every identity class, including admin. The
   web shell
   reflects effective capabilities, but hiding controls is never the
   authorization mechanism.
5. **Browser mutations require origin proof plus a custom header.** Unsafe
   methods require the exact external `Origin`
   (`https://<node>.<tailnet>.ts.net`) and the non-simple
   `X-FrameNest-Request: 1` header, which a cross-origin form or simple
   request cannot set. Duplicate, hostile, or missing origins are rejected.
   No CORS middleware is enabled; preflights fail closed.
6. **Privileged actions are audited before they execute.** Authorized
   privileged attempts are recorded in the durable `security_audit_events`
   table (migration `0020`) before the mutation may run; the final HTTP
   status is stamped best-effort at response start. If the attempt cannot be
   recorded, the action is refused with a sanitized `500`. Selected denials
   (unmapped or under-privileged privileged attempts) are recorded with the
   same shape. Audit rows carry actor login, normalized actor key, identity
   provenance, role, capability, action, target, correlation id, timestamp,
   and outcome — never cookies, authorization headers, provider secrets, or
   request bodies.
7. **Health stays narrowly local.** `GET /health` answers through the Unix
   socket for a local operator and in a deliberately sanitized form for
   mapped tailnet identities; no separate TCP health listener exists. The
   `framenest-production check-health` command speaks HTTP over the Unix
   socket in this mode and over loopback TCP otherwise.

Rollback removes only the FrameNest Serve handler, restores the previous
release and listener configuration, and restores the pre-migration database
backup when the rollback target predates migration `0020`.

## Consequences

- The application never binds a TCP socket in this mode; the legacy SSH
  tunnel to `127.0.0.1:8000` ceases to function by construction.
- Tailscale Funnel stays disabled; no tailnet-wide ACL, DNS, user, or tag
  mutation is part of this foundation, and stale nodes are left untouched.
- Display-name changes, tagged devices, and missing-user identities fail
  closed by design.
- The configuration identity map keeps secrets out of the repository; exact
  logins live only in the host environment file.
- A dedicated external security review of the trust boundary remains
  required before the boundary is considered certified.
