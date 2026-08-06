# ADR-0055: YouTube Category, Creator Attribution, and Immutable Acquisition Provenance

## Status

`Accepted`

## Decision Date

2026-08-06

## Context

[ADR-0045](0045-content-classification-and-movie-identification.md) introduced
orthogonal content category and acquisition source, and Gallery used YouTube as
an acquisition-source filter. Owner-approved taxonomy work now requires:

- a semantic `youtube` content category;
- structured creator attribution distinct from semantic tags;
- immutable catalog `acquisition_source` provenance after creation;
- no historical backfill;
- forward-compatible `x_author` attribution without implementing X acquisition;
- preserved AI draft versus administrator Save boundaries.

This ADR records those decisions. It supersedes the Gallery YouTube-as-source
filter guidance and the editable-acquisition-source posture from ADR-0045 /
ADR-0046 for ordinary metadata Save, without reopening YouTube acquisition
lifecycle decisions in ADR-0046 or ADR-0054.

## Decision

### YouTube content category

Canonical stored category `youtube` (display label `YouTube`) is added.
Newly cataloged YouTube acquisitions initially receive:

- `content_category = youtube`
- `acquisition_source = youtube_manual_claim`

Administrators may later change the semantic category explicitly. Gallery
YouTube filtering uses `content_category = youtube` and must not substitute
acquisition source for semantic category. Acquisition source remains projected.

No historical backfill: existing rows stay unchanged until explicit admin edit
or a separately authorized backfill whole.

### Structured creator attribution

Creator attribution is canonical structured metadata, not an ordinary semantic
tag. Nullable fields:

- `creator_attribution_kind`
- `creator_stable_id`
- `creator_handle`
- `creator_display_name`

Allowed non-null kinds: `youtube_channel`, `x_author`. Absence is `NULL`; do
not store `"none"`.

Normalization:

- display name: trim, Unicode NFC, preserve capitalization, blank → NULL;
- stable ID: trim, preserve exact platform text, blank → NULL;
- handle: trim, strip leading `@`, lowercase, blank → NULL.

Filter identity prefers `kind + stable_id`, otherwise `kind + handle`. Display
name alone is not durable identity.

YouTube first-catalog handoff seeds `youtube_channel` from retained channel ID
and channel name when present; handle remains NULL unless authoritative data
exists. Duplicate/reuse paths must not overwrite existing metadata.

Creator attribution appears as the first attribution chip on relevant UI
surfaces and remains visually distinct from AI/human semantic tags, category,
and acquisition source. Chip activation filters by stable identity or handle
fallback.

### Immutable acquisition provenance

`acquisition_source` is canonical provenance. Ordinary metadata Save:

- omits → preserve stored value;
- identical value → accepted no-op;
- different value → clear validation/conflict rejection;
- must not silently replace provenance with `unknown`.

Acquisition/upload creation workflows may still set provenance. Claim
provenance remains unchanged. Metadata UI shows acquisition source as
read-only.

### AI draft and Save boundary

AI may propose currently supported draft fields (title, description, semantic
tags). AI must not automatically write acquisition source, creator
attribution, publication state, or canonical content category. Discarding or
rerunning analysis must not modify canonical creator or provenance fields.

### Future X contract (schema/docs only)

`x_author` is forward-compatible. Prefer stable author ID, handle fallback,
display name for presentation. Post identity belongs to a future claim.
Short video/GIF-like X media will normally default to Meme; ordinary static
images to General; administrator override remains possible. Acquisition source
remains separate from semantic category. This ADR does not authorize X
acquisition, cookies, downloaders, or network contact with X.

### Schema

Migration `0027` is additive: extend the content-category check for `youtube`,
add nullable creator columns with validation constraints and creator filter
indexes, and perform no data rewrite. Downgrade refuses when YouTube category
or non-null creator attribution exists; otherwise removes additive fields and
restores the previous category constraint.

## Consequences

- Gallery YouTube is a content-category filter.
- Creator chips and creator query parameters become part of the catalog
  contract under existing audience policy.
- Ordinary Save cannot mutate acquisition provenance.
- Acceptance remains zero-provider and fixture/fake-based for this whole.

## Related

- [ADR-0045](0045-content-classification-and-movie-identification.md)
- [ADR-0046](0046-youtube-manual-ingestion-and-provenance.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0054](0054-requester-private-youtube-acquisition-and-promotion-boundary.md)
