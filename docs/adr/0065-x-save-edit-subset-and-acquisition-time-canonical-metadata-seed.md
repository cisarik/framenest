# ADR-0065: X Save Edit Subset and Acquisition-Time Canonical Metadata Seed

## Status

`Accepted`

## Decision Date

`2026-08-22`

## Context

The X Save overlay required category radios and stored Title, Description, and
tags only as a caller-private alias. Gallery and Details correctly read
canonical metadata, but the administrator therefore received no useful
acquisition-time description or tags. Ordinary users must not receive generic
canonical metadata authority, and public Gallery must continue to require
administrator publication.

## Decision

1. Surface A is an Edit-media subset containing Title, Description, existing
   canonical tag search, and one Save. It contains no category, source, genres,
   tag creation, or AI controls and performs no on-open focus.
2. Title is prefilled from a non-generic media accessible name, then a useful
   tweet sentence. Description uses the complete text available in the existing
   tweet-text DOM, bounded by the canonical 10,000-code-point contract.
3. The new extension omits `content_category`. Revision `0030` remains; old
   explicit clients remain compatible. A null request category selects the
   existing media-type default.
4. Existing Save alias fields also form the acquisition-time canonical seed.
   At first catalog creation only:
   - alias title wins, otherwise the existing server-derived claim title;
   - alias description becomes canonical description;
   - selected existing tag keys become ordered canonical tags.
5. Catalog media, location, metadata, tag assignments, collection state, and
   upload linkage are committed atomically. Retry, reuse, duplicate resolution,
   and later re-Save never overwrite canonical metadata.
6. The current eager caller-private alias behavior remains: non-empty Save
   content also writes the requester’s alias, even when initially identical to
   canonical seed; empty content means no alias. Alias rows remain isolated by
   login.
7. One Save form remains claim-wide for multi-asset posts. Per-tile canonical
   titles are deferred.
8. Acquisition-time seed is a specialized internal catalog classification
   rule, not `metadata.canonical.write`, not a new companion route, and not
   permission for ordinary callers to mutate arbitrary media.
9. Gallery and Details remain canonical readers. Seeded data may therefore
   appear there once audience and publication rules allow it. Newly cataloged
   media stays unpublished until the ADR-0049 administrator publication
   transition.
10. Missing canonical tags continue to make the item publication-incomplete.
    No synthetic tag is created.

## Superseded statements

- ADR-0062 is superseded only where it says companion Save values can never
  seed canonical metadata or later appear through canonical Gallery/Details.
  Its caller-private alias, audience, origin, and no-generic-canonical-write
  decisions remain.
- ADR-0064 §1 radio-based Save UI and §2 requirement that the new extension
  always submit a category are superseded.
- ADR-0045 and ADR-0055 enum, source, category, creator, and AI-persistence
  decisions are not reopened.
- ADR-0049, ADR-0061, ADR-0063, migrations `0029`/`0030`, and picker/Attach
  behavior remain authoritative.

## Consequences

Administrator review begins with useful canonical title, description, and
selected tags. A malicious or misleading X DOM string can enter unpublished
canonical metadata, so bounds, plain-text rendering, existing-tag validation,
first-create-only persistence, and administrator publication remain mandatory.
Redundant initial aliases are accepted to preserve a small and consistent
re-Save lifecycle.

## Deferred

W2 classification reconciliation, meme-as-tag, still/short/movie modeling,
duration threshold, backfill, Gallery-filter semantics, picker-audience
migration, YouTube `+`, shadow-DOM keyboard work, and NUC enablement remain
separate wholes.
