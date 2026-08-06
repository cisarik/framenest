# ADR-0054: Requester-Private YouTube Acquisition and Promotion Boundary

## Status

`Accepted`

## Decision Date

2026-08-06

## Context

Mapped ordinary users need a bounded way to request YouTube downloads without
receiving administrator authority for metadata, AI, publication, or removal.
Private results must stay invisible to other ordinary users and to ordinary
Gallery listing until an administrator explicitly publishes them. Matching
protected private media must never disclose foreign existence through claim
reuse.

## Decision

1. **Claim-owned requester attribution.** Migration `0026` adds immutable
   nullable `created_by_login_key` on `youtube_acquisition_claims`. Ordinary
   requests stamp the normalized Tailscale login key. Legacy and administrator
   claims remain `NULL` and never authorize ordinary requester access.
2. **Audience extension, not personal ownership tables.**
   `ContentAudiencePolicy` remains the single server-authoritative media-read
   decision object. After workflow-read and published checks, a mapped identity
   may read unpublished media only when a live successful requester-owned claim
   still links that media. Gallery list queries remain published-only.
3. **Dedicated My YouTube downloads surface.** Ordinary navigation uses a
   capability-gated surface backed by `/api/youtube/requests*`. Completed
   authorized items open existing Details. Ordinary Gallery is not widened.
4. **Publication and removal reuse.** Administrators discover requester-owned
   claims through the existing YouTube claim cockpit (`requester_login_key`
   only; no display-name lookup). Metadata, tags, explicit AI, publication, and
   catalog removal remain administrator workflows. Publication widens access
   through the existing publication model. Removal retains original bytes per
   ADR-0051, ends requester media access, and leaves sanitized request history
   as `unavailable`.
5. **Protected duplicate privacy.** Ordinary requester acquisition never
   attaches to foreign private, unpublished, legacy-admin, or otherwise
   protected matching media. Published media may be attached because existence
   is already public. Matching bytes during handoff use
   `silent_keep_separate` and create a separate logical media record.
6. **No automatic AI.** Ordinary acquisition never invokes providers or AI.
   Explicit administrator AI controls remain unchanged.
7. **Queue and concurrency.** Ordinary quotas default to one active request
   per user, eight global ordinary active requests, six submits per hour, ten
   failed transitions in the previous rolling 24 hours, twenty private items,
   and 10 GiB private bytes. Global acquisition concurrency remains one through
   the existing coordinator.

## Explicit non-goals

X/Twitter acquisition, arbitrary URL fetching, personal folders/collections,
user sharing, ordinary metadata/AI/publication/removal authority, automatic AI
after download, and a durable cancelled state remain out of scope. Future X
support may reuse proven semantics but is not designed here.

## Consequences

Ordinary users gain a private YouTube request journey with sanitized phases and
quota-backed admission. Authorization stays centralized in
`ContentAudiencePolicy`. Independent same-source downloads are accepted for
this first version.
