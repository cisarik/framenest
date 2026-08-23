# ADR-0066: Administrator-Owned X Automatic Generic Analysis

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0044 accepted optional automatic generic analysis after catalog, gated by
`FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED` (default false). X acquisition
later carved out that path: a linked X upload was never eligible, even when
the flag was on, so administrators could not wait for NVIDIA NIM after X Save.

The companion review inbox needs that enqueue for administrator-owned X catalog
events only. Ordinary X requesters, unmapped logins, missing claims, and YouTube
must remain denied. Enqueue is not apply. The flag stays default false; this
decision does not enable it.

## Decision

1. Keep `automatic_analysis_allowed_for_upload` in the X acquisition module. It
   answers only “may this X upload be analyzed if the scheduler is enabled?”
   It does not read the server flag.
2. No linked X asset: return true (not an X upload; the YouTube helper still
   runs next).
3. Linked X asset: load the claim by upload id. Deny when the claim is missing,
   `created_by_login_key` is null, the login is unmapped, the mapped role is
   not administrator, or repository/identity lookup fails. Fail closed without
   raising into the catalog transaction.
4. Linked X asset whose normalized login currently maps to administrator:
   return true. Eligibility is the identity map at catalog time, not the
   `x.request` capability. Demotion before catalog prevents enqueue. There is
   no retroactive backfill when the flag later turns on.
5. `ScheduleAutomaticMediaAnalysis.enabled` remains the final enqueue gate.
   Policy true with the flag false must not create a run.
6. Do not unify YouTube into this path. YouTube stays fail-closed.
7. An empty identity map denies every X-linked upload. Identity is resolved
   from the pre-built mapping at catalog time, never from HTTP request context.
8. This Worker implements the policy in code. Later slices own inbox routes,
   overlay, badge, and NUC enablement of the flag.

## Superseded statements

ADR-0044 remains accepted. Only the X-specific “never enqueue automatic
analysis” carve-out is succeeded by this decision.

## Consequences

Administrators can receive durable generic analysis after X catalog when the
existing flag is later enabled. Ordinary identities cannot. Catalog success
does not depend on analysis. Enabling the flag later incurs real NIM cost for
each new administrator X catalog event.

## Deferred

Inbox HTTP, Alembic 0031, review overlay, badge, alarms, G2 apply, NUC flag
enablement, and live provider calls remain later grants.

## References

- [ADR-0044](0044-durable-automatic-post-catalog-analysis.md)
- [ADR-0061](0061-x-meme-browser-companion.md)
- [ADR-0069](0069-five-tag-generic-media-suggestion-contract.md)
