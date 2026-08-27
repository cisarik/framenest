# ADR-0078: Gallery Card AI Per-Field Review

## Status

`Accepted`

Accepted by the Cooperator on 2026-08-27.

## Decision Date

2026-08-27

## Context

[ADR-0077](0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md)
§10 parked Gallery card 🧠 as an administrator-only bulk
analyze-and-canonical-save path. That path confirmed cloud upload and then
issued last-write-wins `PUT /api/media/{id}/metadata`, replacing Current
canonical title, description, and tags without per-field review.

The existing Edit dialog already has per-field proposal strips, Load, dirty
discard, and canonical Save. Opening a second inline review surface on the
card would change the frozen Gallery grid and duplicate Save semantics.

Hosted companion Analyze stays hidden ([ADR-0077](0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md)
decision 7). A visible hosted-admin card 🧠 would otherwise reopen hosted
Analyze.

Schema head remains Alembic `0033`. Preview persist-join into
`media_analysis_runs` is unchanged.

## Decision

1. **Card 🧠 is Analyze-then-Edit, not analyze-and-save.** After explicit
   confirmation, the card POSTs the existing
   `/api/media/{id}/locations/{loc}/ai-suggestion-preview` with
   `confirm_cloud_upload: true`. It issues zero `PUT /api/media/{id}/metadata`
   and zero `POST /api/canonical-tags`. Canonical persist happens only when
   the administrator clicks Save in the existing Edit dialog.

2. **Existing Edit dialog.** Success opens the existing metadata workspace
   with the preview loaded as proposal strips. Current fields load from the
   canonical GET as usual and are not bulk-replaced. The leftover
   `{ aiSuggestion }` bulk-apply parameter on `handleOpenMetadataWorkspace`
   is removed; that path must not call
   `applyResolvedAiSuggestionToMetadataWorkspace`.

3. **Dismissal is not Save.** Canceling the confirmation performs no fetch.
   Dismissing Edit leaves canonical metadata unchanged. The persist-join from
   the preview POST may already exist in `media_analysis_runs`. If Edit is
   already open on another dirty item and discard is refused, the card
   returns to idle with a review-ready status and does not repeat analysis.

4. **Audience.** Card 🧠 remains `analysis.run` ∧ `metadata.canonical.write` ∧
   resolved ∧ available ∧ not movie, plus a supported available location, and
   is hidden when `companionWebHosted()`. It is available on all such
   administrator-visible supported non-movie items so the administrator can
   re-run analysis after changing AI provider or model, not only when
   canonical metadata is incomplete. Ordinary, unauthenticated, and hosted
   companion Gallery hide 🧠. Hosted Load chrome in Edit is unchanged.

5. **This is not publication.** Card 🧠 does not publish. The four
   `companion_mutation` routes stay unchanged. Schema head stays `0033`.

## Superseded statements

ADR-0077 remains accepted. Only §10 (Gallery 🧠 remains administrator-only
bulk analyze-and-canonical-save; parked as debt) is succeeded by this ADR.
Do not edit the body of accepted ADR-0077.

## Deferred

R4 Settings, Cover Studio, a persistent multi-model comparison board, movie
identification on the card, and persist-join redesign.

## Consequences

Administrators review AI title, description, and tags in the same Edit
chrome used by the pencil control. Card 🧠 stays available for
administrators on all supported non-movie items so they can re-run analysis
and experiment with models; completeness no longer hides the control.
Hosted companion cannot reach Analyze through the card shortcut.

## References

- [ADR-0020](0020-server-owned-ai-analysis-with-explicit-confirmation.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0062](0062-per-user-media-alias-overlay.md)
- [ADR-0077](0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md)
- [GALLERY.md](../../GALLERY.md)
