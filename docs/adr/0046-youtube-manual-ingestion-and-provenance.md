# ADR-0046: YouTube Manual Ingestion and Provenance

## Status

`Accepted`

## Decision Date

2026-07-23

## Context

FrameNest needs one explicit owner-operated path for cookie-free public
YouTube videos without creating another publication or catalog lifecycle.
Editable `media_metadata.acquisition_source` is useful for filtering, but it
cannot be the sole record of immutable upstream identity, downloader evidence,
retry lineage, and final catalog linkage.

The existing upload path already owns quarantine, media validation, exact-byte
identity, publication, and catalog creation. Downloader output therefore must
become a normal exact-size upload only after it is complete and stable.

## Decision

Add one source-specific durable `youtube_acquisition_claims` model. It records
the canonical YouTube identity, bounded upstream snapshot, confirmation,
downloader and selected-format evidence, retry and source-reuse lineage,
staging cleanup, upload linkage, and final logical-media/location linkage.
`youtube_manual_claim` remains the coarse editable catalog source; the claim is
the immutable provenance record.

A thin loopback-only operator CLI submits one supported public URL to the
authoritative server. The server independently canonicalizes the URL, owns one
acquisition subprocess at a time, downloads into a private claim directory,
and hands the stable artifact to `UploadTransportService`. It never writes
downloader output directly to quarantine or publication storage.

The subprocess boundary uses the release-local Python and pinned `yt-dlp`
module without a shell, user configuration, cookies, browser profiles, proxy
inheritance, or arbitrary environment state. Only supported single,
non-live, visual YouTube videos are accepted. Tests use a deterministic fake
subprocess and never contact YouTube.

Active source identity is transactionally unique. A cataloged source identity
is reused without another provider request. Exact-byte duplicates converge
through the existing upload byte identity; a YouTube claim preserves its
provenance while reusing the existing logical medium and physical location.
Automatic post-catalog AI analysis is suppressed for this source.

## Consequences

- Schema revision `0019` adds durable provenance with restrictive foreign
  keys, optimistic versioning, and downgrade refusal while claims exist.
- Claim-owned staging survives process restart and is cleaned by exact opaque
  ownership only.
- Generic manual upload duplicate choices remain unchanged; automatic YouTube
  duplicates never create a second logical medium.
- Cookies, authenticated media, playlists, scheduled or batch ingestion,
  refresh, browser UI, deployment, and live YouTube acceptance remain outside
  this decision.

## Related

- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [ADR-0040](0040-canonical-upload-byte-identity-foundation.md)
- [ADR-0043](0043-upload-to-catalog-transaction.md)
- [ADR-0045](0045-content-classification-and-movie-identification.md)
