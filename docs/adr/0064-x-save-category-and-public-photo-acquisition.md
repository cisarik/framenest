# ADR-0064: X Save Category and Public Photo Acquisition

## Status

`Accepted`

## Decision Date

`2026-08-21`

## Context

ADR-0061 accepted the unpacked Manifest V3 X companion trust boundary and
deferred static X-photo Save (`X_NO_SUPPORTED_MEDIA`) until a later pin
decision. ADR-0062 accepted a caller-private alias overlay on the existing
`POST /api/x/requests` body without a category control. ADR-0063 accepted the
side-panel web host. ADR-0055 recorded `youtube` as a semantic content
category and treated source-derived X category as protected through ordinary
Save.

Users now need to choose canonical content category at X Save, acquire public
JPEG/PNG photographs with the same requester-private claim lifecycle as native
X video, and see honest overlay outcomes. Category must not be stuffed into
alias. Companion trust, picker audience, Gallery/Details, Analyze execution,
and the two-route `companion_mutation` set must stay frozen. Historical
accepted ADR-0061, ADR-0062, and ADR-0063 are not edited in place.

## Decision

Adopt one claim-wide Save category, public JPEG/PNG photo acquisition through
an isolated status bridge, and truthful Surface A outcomes:

1. **Four categories at Save.** The Save popup offers native radios General,
   Meme, Movie, and YouTube (`general|meme|movie|youtube`). `youtube` remains
   the ADR-0055 semantic category, not an acquisition-source proxy. Movie is
   valid with zero genres; no genre picker is added. Helper text: category
   describes the content and applies to every media item in the post; movie
   genres can be added later in FrameNest. Photo tiles default to General;
   video and X GIF-as-video default to Meme; unknown hosts default to General.
   Mixed posts use the clicked tile as the initial default; one final choice
   applies to every asset. Backend inspection never silently changes the
   visible selection.
2. **Claim persistence.** Migration `0030` adds nullable
   `requested_content_category` on `x_post_claims` with CHECK of `NULL` or the
   four values, no server default, and no backfill. The new UI always sends
   `content_category` on the existing POST. Old clients may omit it; `NULL`
   keeps media-kind catalog defaults. Same-requester conflicting category is
   HTTP `409` `X_REQUEST_CATEGORY_CONFLICT`. Invalid values are `422`
   `X_REQUEST_INVALID_CATEGORY`. Retry preserves the original claim category,
   including `NULL`. The new extension never retries by dropping category
   against an old backend.
3. **Correction versus provenance.** Administrators may correct canonical
   `content_category` through the existing capability-gated metadata Save.
   Acquisition source and X creator provenance remain immutable. Claim intent
   is not rewritten by that path.
4. **Public JPEG/PNG photos.** Isolated status-bridge inspect uses
   `sys.executable -I -m framenest.infrastructure.x.status_bridge` and the
   pinned yt-dlp `2026.07.04` `TwitterIE._extract_status` seam, with an empty
   cookie jar and no `.netrc`, browser cookies, CLI config, or plugins. Photo
   bytes are fetched over HTTPS to exact host `pbs.twimg.com` with no
   redirects, subprocess DNS, global-IP checks, TLS SNI plus `Host:
   pbs.twimg.com`, `Accept-Encoding: identity`, HTTP 200, JPEG/PNG magic, a
   30s timeout, and a 64 MiB cap. WebP is rejected without transcoding.
   Content scripts never fetch FrameNest or the CDN.
5. **Source continuity.** Inspect records `source_media_key`, display-only
   ordinal, and policy `selected_variant`
   (`x-photo-orig-jpeg-v1`, `x-photo-orig-png-v1`, `x-video-default-mp4-v1`,
   `x-animated-gif-mp4-v1`). `download()` requires `selected_variant`,
   reinspects, matches the key, and fails `X_SOURCE_MEDIA_CHANGED` on missing
   key, type change, or incompatible representation. Animated GIF remains the
   provider MP4 unless a literal GIF is identified and validated. X staging
   uses `artifact.bin`; YouTube staging default remains `artifact.mp4`.
6. **Honest terminals.** Overlay copy distinguishes busy, completed, already
   saved, partial (`S of N`), failed (plus glyph and danger border, never ×
   and never generic success), `catalog_removed`, and ambiguous transport.
   Every `+` on the same permalink mirrors the same state, keyed by post ID.
   Failed and `catalog_removed` never paint `Saved to FrameNest`.
7. **Frozen trust.** `companion_mutation` remains only `POST /api/x/requests`
   and `POST /api/x/requests/{claim_id}/retry`. No new companion HTTP route,
   CORS, `all_urls`, cookies, signed-in scraping, official X API, provider
   credential, dependency/pin change, picker-audience thaw, or side-panel
   chrome change is authorized. Independent INFOSEC R3, companion-origin
   mutation, NUC `x_acquisition_root`, publication, and deployment remain
   later grants.

This supersedes ADR-0061's static-photo deferral, the implicit fixed-category
Surface A behavior of ADR-0061/ADR-0062, and ADR-0055's future-X default where
an explicit Save choice now exists. Extension origin trust, alias overlay,
picker audience, Gallery/Details canonical metadata, and the side-panel web
host remain as those ADRs recorded them.

## Consequences

Schema head is `0030`. Operators must migrate `0029`→`0030` before starting a
backend that persists category, then reload the unpacked extension. An old
extension against the new backend may omit category. A new extension against
an old backend fails closed with an upgrade message. CDN host, redirect, or
format drift fails closed. The private `_extract_status` seam requires an
intentional maintenance gate on every future yt-dlp pin change.

## References

- [ADR-0055](0055-youtube-creator-taxonomy-and-immutable-provenance.md)
- [ADR-0061](0061-x-meme-browser-companion.md)
- [ADR-0062](0062-per-user-media-alias-overlay.md)
- [ADR-0063](0063-companion-side-panel-web-host.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
