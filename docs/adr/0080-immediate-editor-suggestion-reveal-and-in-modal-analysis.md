# ADR-0080: Immediate Editor Suggestion Reveal and In-Modal Analysis

## Status

`Accepted`

Accepted by the Cooperator on 2026-08-29 as the editor-suggestion and in-modal
analysis successor for era 11 slice 1.

## Decision Date

2026-08-29

## Context

[ADR-0077](0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md)
required a **Load** control: Edit hid per-field strips until Load, and a
dropdown change hid them again. [ADR-0078](0078-gallery-card-ai-per-field-review.md)
required Gallery card 🧠 to POST analysis first and open Edit only after a
preview arrived. Rendered acceptance showed those seams as dead clicks on
already-present tags, no progress while the model ran, and failures that
landed on the card instead of the editor.

The Cooperator replaced both seams: Edit must open with the newest suggestion
already visible; Load is superseded; dropdown switches immediately; 🧠 opens
an empty loading Edit modal and resolves in place.

Schema head remains Alembic `0033`. Preview persist-join into
`media_analysis_runs` is unchanged. Companion unread-history semantics are
out of scope for this ADR.

## Decision

1. **Newest suggestion is visible on Edit open.** Website Edit reveals the
   newest durable generic suggestion immediately as per-field strips. There is
   no Load control. Dropdown selection switches the revealed suggestion with
   zero provider calls and without promoting fields into Current.

2. **Per-field copy remains the only promotion.** Suggested title, description,
   and mapped tags enter Current only through the existing ✅ / tag-click
   copies. A mapped tag already in Current is visibly selected
   (`aria-pressed`, already-added styling) and must not duplicate or dirty
   the workspace; after removal, the same suggestion re-adds exactly once.
   Unmapped tags stay inert in alias mode and remain
   `metadata.canonical.write`-gated in canonical mode. Suggested filename
   stays informational. Nothing persists until Save.

3. **Card 🧠 is Edit-then-analyze.** After explicit confirmation, the card
   opens the existing Edit dialog immediately, then POSTs
   `/api/media/{id}/locations/{loc}/ai-suggestion-preview` with
   `confirm_cloud_upload: true` from that workspace. It issues zero
   `PUT /api/media/{id}/metadata` and zero `POST /api/canonical-tags`. While
   the provider runs, Edit shows an accessible indeterminate progress state.
   Success merges the preview into the suggestion list and reveals it in
   place. Failure stays in the modal with sanitized copy and a manual retry
   that reconfirms cloud upload. There is no automatic retry.

4. **Edit Analyze shares that in-modal path.** Standalone Analyze by AI keeps
   `analysis.run`, not hosted, not movie, not alias mode. Retry after a
   classified provider failure reconfirms. Configuration, missing credential,
   authentication, and model-unavailable copy must not claim that retry will
   repair operator setup. Raw provider text stays unpublished.

5. **Audience and chrome.** Suggestion dropdown and strips remain shown for
   workspace actors with `metadata.alias.write` or `metadata.canonical.write`,
   including hosted companion Details. Hosted Analyze and card 🧠 stay hidden.
   Ordinary identities still do not receive `analysis.run`,
   `metadata.canonical.write`, inbox apply, or canonical tag creation.

6. **This is not publication.** Card 🧠 and Edit Analyze do not publish. The
   five `companion_mutation` routes stay unchanged. Schema head stays `0033`.

## Superseded statements

ADR-0077 remains accepted. Only the Load control, hide-on-dropdown-change, and
hosted “Load chrome” wording in decisions 4 and 7 are succeeded here. Do not
edit the body of accepted ADR-0077.

ADR-0078 remains accepted. Only the analyze-then-open order (decisions 1–2)
and the “Hosted Load chrome in Edit is unchanged” sentence in decision 4 are
succeeded here. Do not edit the body of accepted ADR-0078.

## Deferred

Companion unread-active history, ordinary contributor-scoped analyzed
notification, GIF pause/resume decoding, X terminal-outcome copy, provider
parser root-cause changes, Cover Studio, and a persistent multi-model
comparison board.

## Consequences

Administrators and ordinary workspace editors see the newest suggestion as
soon as Edit opens and can switch history without a confirm step. Gallery
brain no longer waits on the provider before the editor exists, so progress
and failure are visible in the same surface as Save. Per-field confirmation
before canonical or alias persist is unchanged.

## References

- [ADR-0020](0020-on-demand-ai-suggestion-review.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0077](0077-ordinary-alias-edit-affordance-and-per-field-ai-suggestions.md)
- [ADR-0078](0078-gallery-card-ai-per-field-review.md)
- [GALLERY.md](../../GALLERY.md)
- [AI_WORKSPACE.md](../../AI_WORKSPACE.md)
