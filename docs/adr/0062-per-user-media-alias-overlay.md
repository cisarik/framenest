# ADR-0062: Per-User Media Alias Overlay

## Status

`Accepted`

## Decision Date

`2026-08-17`

## Context

ADR-0061 accepted an unpacked Manifest V3 X companion that submits
`POST /api/x/requests` from an allowlisted extension origin. Hover-`+` Save
submitted only `{ url }` and wrote nothing caller-private. Canonical
`media_metadata` remains the Gallery and Details source of truth, including
imported X display titles derived from the tweet. Users still need to name a
save on X before catalog identity exists, without granting ordinary users
`metadata.canonical.write`, without CORS, and without expanding
`companion_mutation` beyond the two already-flagged X POST routes.

## Decision

Adopt a caller-private overlay distinct from canonical metadata:

1. **Overlay tables.** Migration `0029` adds `media_user_aliases` and
   `media_user_alias_tags` keyed by `(media_id, login_key)`, plus
   `x_claim_pending_aliases` and `x_claim_pending_alias_tags` keyed by
   `claim_id`. Empty content (no title, no description, no tags) means no row.
   Catalog removal deletes overlay tags then overlay rows for that `media_id`
   before the existing metadata graph.
2. **Pending on the claim.** The user names on X. Save submits
   `{ url, alias? }` on the existing `POST /api/x/requests`. Omitted `alias`
   preserves today's body. Present empty alias deletes pending content.
   After a CATALOGED `media_id`, upsert the overlay for
   `(media_id, claim.created_by_login_key)`. Reuse applies immediately to each
   successful asset. Canonical `_imported_display_title` and `media_metadata`
   are unchanged. `DUPLICATE_PENDING` still fails catalog handoff with no
   overlay.
3. **HTTP.** `GET /api/media/{media_id}/alias` uses `gallery.read`.
   `PUT /api/media/{media_id}/alias` uses ordinary capability
   `metadata.alias.write` and audit `metadata.alias.save`. Neither route is
   `companion_mutation`. Companion Origin PUT alias is
   `MUTATION_ORIGIN_FORBIDDEN`. Alias from X rides the already-flagged POST.
   Audience matches GET metadata, including the caller's own live cataloged X
   media; denial is `404 MEDIA_NOT_FOUND`. Unknown canonical tags are
   `422 ALIAS_TAG_NOT_FOUND`. `login_key` never appears in the body.
4. **Save popup.** Hover-`+` opens a closed-shadow iframe WAR
   `ui/save.html|css|js` with the same host matches as the picker. Title,
   Description, Tags (existing canonical keys), Save, and Cancel. The service
   worker remains the only FrameNest client. Cancel sends no request. Failed
   Save remains the plus glyph.
5. **Frozen surfaces.** Gallery and Details remain canonical. Attach
   positioning, picker WAR matches, and ADR-0061 origin trust stay frozen.
   Ordinary users still lack `metadata.canonical.write` and `analysis.run`.

## Consequences

Two callers can hold distinct overlays for one `media_id`. Gallery UX does not
read the overlay in this candidate. Operators Reload unpacked after the
extension WAR change. Independent INFOSEC R3 acceptance remains a later Worker.

## References

- [ADR-0061](0061-x-meme-browser-companion.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
