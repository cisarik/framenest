# ADR-0074: Dual-Audience Public Published and Tailscale Workspace Boundary

## Status

`Accepted`

Accepted by the Cooperator on 2026-08-25 with clarifications recorded in the
external analytic trace (Meta `08_orchestrator_notes.md`, section 5). This
record is accepted architecture direction. It does not claim shipped runtime,
public bind, TLS, Funnel, or NUC changes.

## Decision Date

2026-08-25

## Context

FrameNest has one authoritative SQLite catalog and one server-owned media
store. Remote application access today is the Tailscale workspace path in
[ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md):
authenticated Serve to `/run/framenest/framenest.sock` and
`tailscale_uds`. Current ingress supports only `tcp` and `tailscale_uds`.
The TCP composition mounts the full route graph. Identity and route-policy
middleware that make Tailscale headers trustworthy exist only for
`tailscale_uds`. Binding that full application on a public listener would
expose a different trust boundary than the workspace.

[ADR-0049](0049-durable-content-publication-boundary.md) separates catalog
membership from durable content publication and keeps ordinary
`GET /api/media` published-only. [ADR-0068](0068-companion-review-save-and-readiness-triggered-publication.md)
then made companion review Save a second publication path when readiness
holds, with origin `companion_review`.
[ADR-0073](0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md)
preserved that G2 publication behavior while changing Apply tag merge.

Ordinary mapped users can submit uploads
([ADR-0053](0053-ordinary-user-upload-submission-and-administrator-review-boundary.md))
and request YouTube or X acquisition, but they cannot list unpublished
catalog rows on Gallery. Requester-private YouTube reads
([ADR-0054](0054-requester-private-youtube-acquisition-and-promotion-boundary.md))
are an audience extension, not ownership. Aliases
([ADR-0062](0062-per-user-media-alias-overlay.md)) are caller-private.
The companion side panel
([ADR-0063](0063-companion-side-panel-web-host.md)) iframes the stored
Tailscale origin. Companion surfaces exclude movie workflows
([ADR-0070](0070-companion-exclusion-of-movie-workflows.md)).

The product intent is two honest audiences on that same catalog: a paid
Tailscale workspace (identity-mapped team; Tailscale membership is not
administrator authority) and a free public origin that can search, view, and
later attach only published media.

## Decision

Use **one** authoritative catalog and media store with **two** separately
composed applications and listeners:

```text
Tailscale workspace
  -> authenticated Tailscale Serve
  -> /run/framenest/framenest.sock
  -> existing tailscale_uds application
  -> catalog/media read-write authority

Public HTTPS origin
  -> public TLS reverse proxy
  -> distinct public Unix socket
  -> new public_published_uds application
  -> same catalog/media, read-only
```

1. **Workspace writer, public reader.** The workspace process remains the
   only writer, migration owner, background-job owner, and provider-facing
   process. The public process opens SQLite through a read-only URI, reads
   media and derivatives without generating them, and fails startup rather
   than falling back to a writable catalog, a full-application mount, or
   `tailscale_uds` trust rules.
2. **Public composition is an allowlist, not a hide.** `public_published_uds`
   is assembled from the exact GET-only route allowlist below. It must not
   mount the full application and depend solely on middleware to hide
   privileged routes. Until a later operational whole binds it to public
   TLS, this composition stays local-only.
3. **Tailscale remains the workspace remote path.** ADR-0048’s Serve socket,
   identity-header trust, mutation proof, audit, fail-closed unsigned
   routes, and “Tailscale membership is not administrator authority” rules
   remain the workspace contract. Public callers never trust
   `Tailscale-User-*` headers and cannot widen access with them.
4. **No router port-forward.** Public reachability is a distinct origin and
   socket. Funnel to `/run/framenest/framenest.sock` stays forbidden.
   Funnel to the dedicated public socket is contingency only, through a
   later operational ADR, not this decision’s recommended path.

### Publication gate

Administrator `PUT /api/admin/media/{media_id}/content-publication`, guarded
by `media.content.publish`, becomes the **sole future** promotion and
unpublication path for every media type, including movies.

- Companion Apply continues applying reviewed metadata and must never
  publish. Preserve-and-append tag Apply from ADR-0073 remains in force for
  metadata writes.
- Historical `companion_review` publication rows and the enum value stay
  readable. No destructive rewrite, origin rewrite, or downgrade is
  performed.
- Readiness remains title + description + at least one canonical tag, as in
  ADR-0049. Metadata regression still does not silently unpublish.
- Unpublishing stops future public requests. It cannot revoke bytes already
  received by public clients.
- `GET /api/media` stays published-only on every audience.

This narrowly supersedes ADR-0068’s readiness-triggered publication and
ADR-0073’s preservation of that G2 publication behavior. It restores
ADR-0049’s explicit-route publication as the future write path without
editing ADR-0049 in place, and it fills ADR-0049’s deferred unpublish on
the same administrator PUT.

### Audience bootstrap

Add `GET /api/audience/me` to each UI composition:

```json
{
  "audience": "public_published | tailscale_workspace | trusted_loopback",
  "identity": {
    "login": "string",
    "display_name": "string",
    "role": "user | admin",
    "provenance": "string"
  },
  "capabilities": ["string"]
}
```

`identity` is `null` for public and trusted-loopback callers. Public callers
are not assigned a fake role or identity. Existing `GET /api/identity/me`
stays workspace-only.

The frontend bootstraps from this endpoint, treats missing or invalid
bootstrap state as having no capabilities, and removes the permissive
loopback capability fallback. Privileged controls start hidden and are
enabled only for the resolved audience. UI hiding remains never the
authorization mechanism.

### Public audience

Identity-absent public callers receive only:

- `gallery.read`
- `media.original.read`

Public routes are exactly these GET-only routes:

- `/`
- `/assets/app.js`
- `/assets/styles.css`
- `/api/audience/me`
- `/api/media`
- `/api/media/{media_id}`
- `/api/canonical-tags`, filtered to tags represented by published media
- `/api/media/{media_id}/metadata`
- `/api/media/{media_id}/locations/{location_id}/content`
- `/api/media/{media_id}/locations/{location_id}/gallery-preview`
- `/api/media/{media_id}/cover-thumbnail`

The public catalog projection includes only opaque media and location IDs
and user-facing published data: media kind, category/source, title,
description, ordered tags, public creator display fields, cover readiness,
and location availability. It excludes `library_id`, relative paths, file
timestamps and sizes, processing state, internal collection state, stable
provider IDs, aliases, and workflow metadata.

Public behavior:

- Catalog search and all direct reads recheck durable publication truth.
- Unknown and unpublished items return the same sanitized `404`.
- Every unlisted route or method returns sanitized `404`, including health,
  status, identity, libraries, uploads, downloads, AI, aliases, X/YouTube,
  companion review, operator, admin, OpenAPI, and docs.
- No CORS and no public mutation support.
- API and content responses initially use no shared caching so an
  unpublished item is not retained by a reverse-proxy cache.
- Published movies appear in search and Details and support Range playback.
  ADR-0070’s companion movie exclusion remains intact.
- The existing Attach bridge needs no new server mutation: it reads the
  content route using opaque media and location IDs. Until a later whole
  reconnects the companion to the public origin, the public website provides
  search, view, and the safe content seam but must not claim completed
  end-user Attach acceptance.

### Workspace audience

Add these capabilities to the identity-access table:

- `media.workspace.read` — ordinary and administrator roles.
- `analysis.propose` — ordinary and administrator roles.
- `metadata.alias.team.read` — administrator only.

Workspace behavior:

- Existing `upload.submit`, `youtube.request`, and `x.request` remain the
  ways ordinary users add media.
- `GET /api/workspace/media`, guarded by `media.workspace.read`, returns the
  caller’s upload, YouTube, and X-attributed media whether published or
  unpublished. This is contributor-scoped audience extension in the
  ADR-0054 sense: not an ownership column and not a personal library. A
  medium may have several contribution claims.
- Extend the shared content audience policy so a caller may read their own
  upload-attributed content. Existing YouTube and X requester-private
  extensions remain.
- Keep `GET /api/media` published-only.
- Enhance administrator `GET /api/admin/media` with contribution attribution
  and an optional normalized contributor filter. It continues returning all
  catalog media, including unattributed and unpublished items, under
  `media.workflow.read`.
- `POST /api/workspace/media/{media_id}/analysis-proposals`, guarded by
  `analysis.propose`, creates a durable administrator-visible proposal and
  audit event. It never calls a provider, starts analysis, or toggles
  automatic analysis.
- `GET /api/admin/analysis-proposals` under administrator workflow/analysis
  capabilities.
- `GET /api/admin/media/{media_id}/aliases` requires both
  `media.workflow.read` and `metadata.alias.team.read`, with audited access.
  Ordinary users retain only their own alias route. Public callers receive
  `404`.

Existing `metadata.canonical.write`, `analysis.run`, `media.workflow.read`,
and `media.content.publish` continue representing administrator authority.

## Relationship and supersession matrix

Do not edit the bodies of the ADRs named below. This accepted record is the
sole carrier of the new boundary.

| ADR | Relation | Statements this ADR changes | Statements that remain |
|---|---|---|---|
| [0048](0048-tailscale-remote-access-and-identity-foundation.md) | Narrow supersession | Only the inbound sentences that make Tailscale Serve the **only** remote application path and that treat **any** public exposure as out of bounds. A second origin exists for published-public reads. | Workspace remote path remains Serve → `/run/framenest/framenest.sock` → `tailscale_uds`. Identity headers are trusted only in that mode. No router port-forward. Funnel stays disabled against the workspace socket. Capability policy, mutation proof, audit, and fail-closed unsigned routes remain. Tailscale membership is not administrator authority. |
| [0068](0068-companion-review-save-and-readiness-triggered-publication.md) | Narrow supersession | Decision 2: same-transaction readiness-triggered publication with origin `companion_review` after companion Save. | Checkmarked-field metadata writes. `GET /api/media` published-only. NIM completion does not publish. Website administrator Publish remains and becomes the sole future publication write. |
| [0073](0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md) | Narrow supersession | Only the clause in decision 5 that G2 readiness-triggered publication remains unchanged. | Four `companion_mutation` routes. Movie exclusion. Ingest Save. Hosted iframe. Preserve-and-append Apply. NIM completion still does not publish. |
| [0049](0049-durable-content-publication-boundary.md) | Supplement | Unpublish on the administrator PUT fills deferred work. Dual-audience readers share the same publication table. Future writes use that PUT only. | `media_content_publications`, readiness (title, description, at least one canonical tag), published-only Gallery list, and the explicit administrator publication route remain. Metadata regression still does not silently unpublish. |
| [0053](0053-ordinary-user-upload-submission-and-administrator-review-boundary.md) | Supplement | Contributor-scoped unpublished workspace list and upload-attribution content reads. | No personal libraries. No media-level ownership. Ordinary Gallery remains published-only. `upload.submit` versus `upload.manage` remains. Ordinary cataloged submissions still do not create publication rows. |
| [0054](0054-requester-private-youtube-acquisition-and-promotion-boundary.md) | Supplement | The same audience-extension pattern is reused for upload-attributed unpublished reads and a workspace media list. | Requester-private YouTube claims, dedicated request surface, Gallery published-only, and `ContentAudiencePolicy` as the single media-read decision object remain. |
| [0062](0062-per-user-media-alias-overlay.md) | Supplement | Administrator team-alias read under `metadata.alias.team.read` with audit. Public alias routes return `404`. | Caller-private overlay keyed by `(media_id, login_key)`. Ordinary users retain only their own alias route. Gallery and Details stay canonical. |
| [0063](0063-companion-side-panel-web-host.md) | Supplement | Companion reconnect to the public origin is a later whole. Until then the public site must not claim completed Attach acceptance. | Current side panel iframes the stored Tailscale origin. Attach still uses opaque media and location IDs on the stored origin’s content route. |
| [0070](0070-companion-exclusion-of-movie-workflows.md) | Supplement | After administrator Publish, movies are in the public catalog, Details, and Range playback. | Companion inbox, badge, and review overlay continue to exclude movie workflows. |

## Public ingress ranking

1. **Distinct public HTTPS origin to the dedicated public ASGI socket —
   recommended.** One catalog; the public route graph is structurally
   incapable of reaching workspace APIs. TLS product, hostname, and host
   placement are deferred to a separately authorized operational preflight.
2. **Tailscale Funnel to the dedicated public socket — contingency only.**
   Consider only through a new operational ADR, never against
   `/run/framenest/framenest.sock`. Ranks lower because accepted deployment
   truth currently disables Funnel and it couples public availability to the
   NUC/Tailscale control plane.
3. **Static published export.** Strong isolation, but it introduces
   synchronization state and weakens live search, Range playback, movies,
   unpublication, and Attach.
4. **Later VPS.** Potential long-term host for the same public composition,
   but it requires a catalog/media projection or private tunnel and expands
   this work into cloud operations.

## Phased rollout

Acceptance of this ADR authorizes living-document updates as a follow-on;
it does not ship runtime. Ordered successor wholes:

1. Correct the sole publication gate and add focused compatibility tests.
   Companion Apply keeps metadata behavior and historical
   `companion_review` readability.
2. Implement local-only `public_published_uds`, read-only engine, audience
   bootstrap, redacted DTO, public frontend branch, exact route inventory,
   and published movie/Range support. Do not expose it externally.
3. Independent security acceptance, then a separately authorized public
   TLS/reverse-proxy deployment preflight. No NUC, DNS, Funnel, firewall, or
   router mutation before that authority.
4. Contributor-scoped workspace media, upload audience extension, and
   administrator contribution filtering.
5. Durable ordinary-user analysis proposals without enqueue or provider
   execution.
6. Audited administrator team-alias reads.
7. Reconnect the parked Brave companion to the public origin for published
   search, Attach, and view only; do not expose the administrator review
   inbox there.
8. Unpark the separate companion Brave acceptance backlog only on the
   Cooperator’s explicit request and against the origin and SHA matching
   that test.

## Rejected alternatives

- Two catalogs or a second media database.
- Optional identity on the workspace listener as a public mode.
- Public TCP binding of the current full application.
- Tailscale Funnel to the administrator/workspace socket.
- UI hiding as authorization.
- Treating companion Apply as a publication path.
- Ownership columns or personal libraries for the workspace “work gallery”.
- Enabling automatic analysis to feed public or workspace workflows.

## Assumptions and negative space

- Attribution records are contribution evidence, not ownership.
- Public publication is externally irreversible once bytes have been
  downloaded.
- Public hostname, TLS product, and deployment host are outside this
  ADR-only whole; the accepted boundary is a distinct origin and socket.
- In-git default for automatic media analysis stays off per
  [ADR-0066](0066-administrator-owned-x-automatic-generic-analysis.md).
  `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED` enablement for
  administrator-owned X events is a separate Cooperator operational
  decision on deployed environments, never enabled in tracked unit files by
  Workers, and is not part of this whole.
- This whole does not introduce registration, billing, payments, SaaS
  tenancy, personal libraries, a second database, anonymous upload, public
  aliases, public analysis, router forwarding of the admin API, companion
  chrome work, or an exploratory NUC Funnel change.

## Consequences

- An accepted contract exists for two audiences on one catalog before any
  public listener is bound.
- Future publication writes converge on the administrator PUT; companion
  history remains compatible with existing `companion_review` rows.
- Public callers are identity-absent and receive two read capabilities
  only. Workspace unpublished reads stay on a distinct list and on
  contributor-scoped content-audience extensions.
- Companion public-origin reconnect and Brave acceptance remain parked
  successor wholes.
- Living documents may record this ADR as accepted architecture direction.
  Runtime, public bind, TLS, Funnel, and NUC listener changes remain
  successor wholes.

## Deferred work

Everything in the phased-rollout list after acceptance, including socket
path for the public listener, TLS product, hostname, host placement, and
companion public-origin reconnect.

## References

- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [ADR-0049](0049-durable-content-publication-boundary.md)
- [ADR-0053](0053-ordinary-user-upload-submission-and-administrator-review-boundary.md)
- [ADR-0054](0054-requester-private-youtube-acquisition-and-promotion-boundary.md)
- [ADR-0062](0062-per-user-media-alias-overlay.md)
- [ADR-0063](0063-companion-side-panel-web-host.md)
- [ADR-0066](0066-administrator-owned-x-automatic-generic-analysis.md)
- [ADR-0068](0068-companion-review-save-and-readiness-triggered-publication.md)
- [ADR-0070](0070-companion-exclusion-of-movie-workflows.md)
- [ADR-0073](0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md)
