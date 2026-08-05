# ADR-0053: Ordinary-User Upload Submission and Administrator Review Boundary

## Status

`Accepted`

## Decision Date

2026-08-05

## Context

Michal decided that mapped ordinary Tailscale users may submit supported
direct uploads into the existing quarantine, validation, storage-publication,
and cataloging pipeline, while content remains unpublished until an
administrator explicitly publishes it. Ordinary users must not gain
administrator media workflow, metadata write, AI initiation, batch, import,
YouTube, removal, or content-publication authority. Exact-byte duplicate
matches must not disclose matching catalog or upload evidence to ordinary
submitters. Upload-session access across users must not rely on opaque UUID
secrecy alone. ADR-0048 historically assigned direct-upload routes to
administrator-only `upload.manage`. ADR-0041 remains historical authority for
administrator explicit duplicate keep/discard handling.

## Decision

1. **Capability split.** Introduce `upload.submit` for mapped ordinary users
   and administrators. Keep `upload.manage` administrator-only for duplicate
   cockpit and manage-override semantics. The seven direct-upload routes
   (`POST /api/uploads`, `GET /api/uploads/capability`,
   `GET /api/uploads/{upload_id}`, `PATCH /api/uploads/{upload_id}`,
   `POST /api/uploads/{upload_id}/complete`,
   `POST /api/uploads/{upload_id}/duplicate-resolution`,
   `DELETE /api/uploads/{upload_id}`) require `upload.submit`. No
   `/api/admin/*` widening.
2. **Tailscale identity trust boundary.** Creation stamps the verified
   normalized Tailscale `login_key` when present. Trusted loopback creation
   without Tailscale identity may remain single-tenant compatible with a
   `NULL` owner and explicit duplicate mode, without weakening the Tailscale
   multi-user path.
3. **Durable upload-session ownership.** Migration `0025` adds nullable
   `created_by_login_key`. Owner access and `upload.manage` override are
   required for Tailscale session routes. Foreign ordinary callers receive
   the same sanitized `404 UPLOAD_SESSION_NOT_FOUND` as a missing session.
   Legacy `NULL` owners are administrator-manage only. No media-level
   ownership and no personal-library semantics.
4. **Durable duplicate privacy mode.** Migration `0025` adds
   `duplicate_resolution_mode` with stable values `explicit` and
   `silent_keep_separate`. Creation sets `explicit` only when the creator is
   positively proven to have `upload.manage`; otherwise
   `silent_keep_separate`. Legacy rows migrate to `explicit`. Validation uses
   the persisted mode, not request-scoped identity. Unknown, missing, or
   invalid modes fail closed toward privacy-safe ordinary behavior.
5. **Ordinary duplicate non-disclosure.** For
   `silent_keep_separate`, a qualifying byte match atomically commits
   `keep_separate` with `publish_pending` in the same validation transaction.
   No externally observable `duplicate_pending` state, matching IDs, titles,
   owners, or publication/removal facts are disclosed. Administrator
   `explicit` sessions retain ADR-0041 `duplicate_pending` keep/discard.
6. **Content-unpublished default.** Ordinary cataloged submissions do not
   create content-publication rows. Ordinary Gallery, Details, metadata,
   preview, and content remain audience-denied until administrator
   publication. Completion feedback comes from the authorized upload session.
7. **Frontend boundary.** Upload visibility uses `upload.submit`. Ordinary
   completion states that submission awaits administrator review and is not
   public, without navigating to unpublished Details or triggering automatic
   analysis. Duplicate keep/discard UI requires `upload.manage`. Stale
   `404 UPLOAD_SESSION_NOT_FOUND` recovery clears only local recovery state,
   stops polling, shows a generic unavailable message, and never cancels a
   foreign server session.

## Explicit exclusions

Personal libraries, media ownership, generalized moderation, reviewer
assignment, notifications, ordinary publication/AI/metadata/batch/import/
YouTube/removal authority, anonymous upload, and public registration remain
out of scope.

## Consequences

- ADR-0048’s admin-only direct-upload capability assignment is superseded by
  this decision for capability assignment only; its ingress architecture
  remains authoritative.
- ADR-0041 remains authoritative for administrator explicit duplicate
  handling; this ADR records the ordinary-user privacy refinement.
- Schema head advances to migration `0025`.

## References

- [ADR-0041](0041-exact-upload-duplicate-decision.md)
- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [ADR-0049](0049-durable-content-publication-boundary.md)
- [SECURITY.md](../../SECURITY.md)
- [SPEC.md](../../SPEC.md)
