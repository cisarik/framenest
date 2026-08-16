# ADR-0061: X Meme Browser Companion Origin Trust

## Status

`Accepted`

## Decision Date

`2026-08-16`

## Context

FrameNest already exposes requester-private X acquisition through
`POST /api/x/requests` and related read/retry routes. Those unsafe methods
accept the exact Tailscale Serve web origin plus `X-FrameNest-Request: 1`.
A Manifest V3 browser companion needs to submit the same X request mutations
and read a purpose-specific meme picker without becoming a public bridge,
generic proxy, or cookie/credential copier, and without changing Gallery or
Details UX.

The pinned `yt-dlp==2026.7.4` Twitter extractor still filters
`m['type'] != 'photo'`. Static X photographs therefore remain outside the
acquisition contract. Existing FrameNest JPEG/PNG catalog items remain
eligible for picker attachment independently of that gap.

## Decision

Adopt one unpacked Manifest V3 Chromium companion as the only browser
integration for X composer attach and explicit Save:

1. **Exact extension-origin allowlist.** Settings key
   `companion_extension_origins` holds at most four unique
   `chrome-extension://` + 32-character `[a-p]` origins and defaults to empty.
   Empty remains fail-closed. No CORS headers are added.
2. **Flagged mutations only.** `RoutePolicy.companion_mutation` is true solely
   for `POST /api/x/requests` and `POST /api/x/requests/{claim_id}/retry`.
   Those routes accept `Origin == external_origin` or an allowlisted companion
   origin. `X-FrameNest-Request: 1`, Tailscale identity, capability
   `x.request`, and audit continue to apply. Ordinary web mutations stay on
   the exact external origin.
3. **Purpose-specific picker.** `GET /api/x/companion/media` lists `meme`
   items whose kind is image, animated image, or video, that have at least one
   available `SUPPORTED_MEDIA_CONTENT` location, and that are published **or**
   the caller's own live cataloged X media. The caller comes only from verified
   ingress identity. `GET /api/media` remains published-only.
4. **Extension isolation.** The service worker is the only FrameNest network
   client. Content scripts send opaque ids and validated post URL strings.
   Messages use `v: "framenest.companion.v1"`. Unknown versions and types are
   dropped. Save polling is page-driven with `chrome.storage.local` recovery
   across service-worker suspension. The adapter contract contains no Post
   control and never submits.
5. **Inert default.** The companion does nothing until an operator lists the
   exact unpacked extension origin and the user grants the exact FrameNest
   tailnet origin. Rollback is emptying the allowlist.

Static X-photo Save remains deferred (`X_NO_SUPPORTED_MEDIA`) until a later
explicit pin decision. Live signed-in X evidence (SPIKE-X-01) is a separate
grant.

## Consequences

Operators must record the stable unpacked extension id derived from the
committed public `key` and keep the matching private key outside Git. The
companion is loadable unpacked in Brave/Chromium; it is not a Web Store
package and not a NUC deployable. Gallery/Details visual behavior is
unchanged.

## References

- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [ADR-0049](0049-durable-content-publication-boundary.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
