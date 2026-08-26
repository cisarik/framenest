# ADR-0077: Ordinary Alias Edit Affordance and Per-Field AI Suggestions

## Status

`Accepted`

## Decision Date

`2026-08-26`

## Context

ADR-0062 accepted a caller-private alias overlay and froze Gallery and Details
as canonical. Ordinary identities already hold `metadata.alias.write`, but the
website Edit affordance stayed behind `metadata.canonical.write`, so the overlay
had no in-app editor after X Save.

ADR-0023 accepted a manual-first Current form with bulk `Use this draft`
promotion. That bulk copy hid which fields changed and locked Analyze after the
first success. Companion review already persists generic runs; the website
editor still treated suggestions as a one-shot session replacement.

Gallery card 🧠 remains a separate admin bulk analyze-and-canonical-save path.
This ADR does not redesign that path.

## Decision

1. **Edit gate.** Details and Gallery Edit are shown when the actor is in a
   workspace audience and holds `metadata.canonical.write` **or**
   `metadata.alias.write`. Canonical-write wins when both are present.

2. **Save split.** Ordinary Save is `PUT /api/media/{id}/alias` with
   `display_title`, `description`, and `tag_keys` only. Empty content still
   means no overlay row (ADR-0062 `is_empty`). Administrator Save remains
   canonical metadata PUT. Authenticated Gallery and Details **display** the
   caller's overlay when a non-empty row exists for `(media_id, login_key)`;
   missing overlay fields keep canonical `media_metadata`. Anonymous, public,
   and no-`login_key` callers see canonical only. `GET /api/media/{id}/metadata`
   remains canonical.

3. **Ordinary load.** Edit opens with canonical metadata GET, then alias GET.
   A non-empty overlay becomes Current. An empty overlay or missing row keeps
   the canonical seed. Dirty state is versus that loaded seed.

4. **Suggestions chrome.** Heading is **AI suggestions**. Dropdown plus **Load**
   sit above Title. Load reveals per-field strips and does not call
   `applyResolvedAiSuggestionToMetadataWorkspace`. Dropdown change issues zero
   provider calls and hides strips until Load. Mapped suggested tags are
   buttons that append one key into Current. Unknown or ambiguous tags are not
   buttons. Nothing persists until Save.

5. **List source.** Website Edit reads
   `GET /api/media/{media_id}/ai-suggestions?limit=100` under
   `metadata.alias.write` for ordinary and administrator Load. Inbox detail
   `GET /api/companion/review-inbox/{media_id}` stays administrator
   `media.workflow.read`. The website reads only. There is no `POST …/apply`
   from this surface. Ordinary identities do not receive `analysis.run`,
   `metadata.canonical.write`, inbox list/detail, or Apply. Schema head remains
   `0033`.

6. **Analyze by AI.** Requires `analysis.run`, standalone (not hosted), not
   movie, not alias mode. Success becomes proposal strips and does not replace
   Current. `aiSuggestionApplied` must not hide or disable the next Analyze.
   Persist-join on preview POST is unchanged.

7. **Hosted companion Details.** Alias or canonical Edit remains shown per the
   Edit gate. Analyze stays hidden. Load, the dropdown, and strips remain shown
   for workspace actors with alias or canonical write.

8. **Ordinary form subset.** Hide content-category and acquisition for every
   actor in this Edit dialog; admin canonical Save still sends the existing
   values. Hide genres in alias mode. Tag search uses existing keys only; no
   `POST /api/canonical-tags`. Suggested filename is an informational note for
   ordinary and administrator Load, with copy allowed and no persist/rename.

9. **Movie Edit.** Hide generic suggestions chrome (detail GET 409). Identify
   movie stays administrator movie-only.

10. **Gallery 🧠.** Remains administrator-only bulk analyze-and-canonical-save.
    Parked as debt; not converted to per-field copy in this candidate.

11. **Four `companion_mutation` routes unchanged.** Alias PUT is not one of
    them.

## Superseded statements

ADR-0062 remains accepted. Only its frozen-surface statement is succeeded for
the **Edit affordance** and for authenticated Gallery/Details **display** of the
caller's overlay. Canonical metadata GET and administrator Manage remain
canonical.

ADR-0076 remains accepted. Only the statement that Edit remains
`metadata.canonical.write` is succeeded. Hosted hide of Analyze remains; hosted
hide of Load/dropdown/strips is succeeded.

ADR-0023 remains accepted. Only the website `Use this draft` bulk-promotion
surface is succeeded by per-field ✅ in the existing metadata dialog. The
manual-first Current form, confirmation-before-cloud, and no autosave
invariants remain.

Do not edit the bodies of accepted ADR-0062, ADR-0076, or ADR-0023.

## Deferred

Per-field Gallery 🧠, R4 Settings, Cover Studio, and a persistent multi-model
comparison board.

## Consequences

Ordinary workspace users can name media in FrameNest without canonical write.
Administrators keep canonical Save and Analyze. Website suggestion review lists
durable inbox runs and copies fields locally until Save. Companion Apply stays
on the extension review surface.

## References

- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0062](0062-per-user-media-alias-overlay.md)
- [ADR-0076](0076-companion-history-hosted-click-admin-analyzed-inbox-and-ordinary-own-history.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
