# ADR-0051: Administrator Catalog Removal and Safe Catalog Retirement

## Status

`Accepted`

## Decision Date

2026-08-04

## Context

Administrators need a bounded way to remove one mistaken or unwanted logical
medium from the active catalog without introducing Trash, soft-delete query
fan-out, batch deletion, or physical original-byte purge. Catalog membership,
content publication, analysis history, and derived artifacts must leave the
active read model, while operator-managed and server-managed originals remain
on disk. YouTube and upload provenance must remain truthful after the active
catalog link disappears.

## Decision

FrameNest implements hard catalog removal for one `logical_media` identity
behind capability `media.catalog.remove`.

1. Preview is read-only and returns a deterministic `consequence_fingerprint`
   over removal-relevant state, always with `original_bytes_policy: retain_all`.
2. Mutation requires `acknowledge_consequences: true` and the exact preview
   fingerprint. Inside a SQLite `BEGIN IMMEDIATE` write transaction, FrameNest
   reloads state, verifies the fingerprint, inserts a durable catalog-removal
   receipt, transitions linked YouTube claims to `catalog_removed`, detaches
   upload-publication catalog linkage, deletes the removable active aggregate in
   explicit FK-safe order, and commits.
3. After commit, FrameNest attempts idempotent cleanup only for derived
   artifacts proven exclusive to the removed medium or its removed locations.
   Cleanup outcomes are mutable fields on the receipt; the historical receipt
   core remains durable. Retry is receipt-addressed.
4. Original media bytes are never unlinked by this whole. Physical purge remains
   a separate future decision.
5. Historical `CATALOGED` upload sessions qualify as live canonical duplicates
   only while upload-publication `media_id` still points at an active medium.

## Authorization and API

- `GET /api/admin/media/{media_id}/catalog-removal`
- `POST /api/admin/media/{media_id}/catalog-removal`
- `POST /api/admin/catalog-removal-receipts/{receipt_id}/cleanup-retry`

These routes require `media.catalog.remove`, fail closed for ordinary users, and
use the existing Tailscale route-policy audit and CSRF/same-origin mutation
proof conventions. Pre-mutation audit records authorization intent; the durable
receipt records completed catalog and cleanup outcomes.

## Consequences

- Active Gallery, Details, content, download, stream, cover, preview, and
  publication routes treat a removed medium like an unknown medium.
- Catalog removal is not Trash, Hide, soft delete, or physical purge.
- Migration `0024` adds YouTube `catalog_removed` constraints and the receipt
  table.
- Batch removal, tombstone filtering, Trash/Hide, and original-byte purge remain
  deferred.

## Alternatives considered

- Soft delete with `deleted_at` filters: rejected to avoid permanent query
  fan-out and ambiguous active-catalog truth.
- Physical purge in the same whole: rejected because original-byte ownership and
  recovery semantics require a separate bounded decision.
- Event-sourcing every catalog change: rejected as disproportionate.
