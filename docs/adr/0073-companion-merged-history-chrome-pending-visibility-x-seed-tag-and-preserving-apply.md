# ADR-0073: Companion Merged History Chrome, Pending Visibility, 𝕏 Seed Tag, and Preserving Apply

## Status

`Accepted`

## Decision Date

`2026-08-24`

## Context

ADR-0072 accepted a heading-free unread list above the hosted iframe plus a
separate title-bar history of every latest successful generic analysis. ADR-0068
accepted companion review Save of checkmarked fields with the sentence “Tags
replace, they do not union.” Live Cooperator revision replaced that two-list,
analyzed-only chrome and replacement Apply with one merged history, pending
visibility, a fixed first-use `x` / `𝕏` seed, and preserve-and-append Apply.
D1–D3 already shipped that contract. This ADR records it without changing
runtime code.

## Decision

1. `GET /api/companion/review-inbox` remains the existing mixed inbox. Each
   item includes `created_at_ms` and `analyzed`. `analysis_run_id` and
   `completed_at_ms` are null only when `analyzed` is false; pending `unopened`
   is always false. The opaque cursor is v2 `{v, at_ms, analyzed, id}`; legacy
   analyzed `{completed_at_ms, id}` cursors remain accepted; responses emit v2.
   `unopened_count` stays byte-compatible and is the only badge source,
   formatted `1` through `99` or `99+`. Pending rows never increment the badge.
   An ordinary-identity 403 hides history, collapses and disables the toggle,
   and clears the badge.
2. The side panel has one merged title-bar history: `#review-history-toggle`,
   `#review-history`, and `#review-history-list`. There is no `#review-inbox`.
   Analyzed rows use `review-history-button--analyzed` (accent green, dark
   text). Pending rows use `review-history-button--pending` (dark surface, light
   text). Clicking a row never removes it. A pending overlay shows `No
   successful analysis yet.` and does not send an opened mutation. Native
   chrome stays above the surviving hosted iframe (`#frame`) per ADR-0063 S1;
   Attach remains available.
3. `GET /api/canonical-tags?surface=x-companion-save` best-effort seeds the
   fixed pair `key="x"`, `display_name="𝕏"` (U+1D54F) before listing. A
   conflicting existing `x` definition or seed-only repository failure still
   returns the ordinary list. Bare GET without that surface does not seed. Save
   prepends the exact pair once when present and does not synthesize a missing
   pair. There is no YouTube analogue.
4. When Tags is selected, Apply preserves current canonical keys and appends
   submitted mapped AI keys that are not already present, then re-enumerates
   from 0. Submitted `tag_keys` remain administrator-selected mapped AI keys:
   at most five, distinct, and an ordered subsequence of that run’s eligible
   mapped keys. The combined vector may exceed five and must not exceed
   `MAX_MEDIA_TAGS` (32). Overflow is atomic HTTP 409
   `COMPANION_REVIEW_TAG_LIMIT_CONFLICT` with no truncate. Selecting Tags still
   requires at least one submitted AI key. Title/description-only Apply may
   send an empty `tag_keys` array. Migration `0032` adds table
   `companion_review_tag_sources` with no historical backfill. Detail and Apply
   responses expose `canonical.tag_sources` keyed by tag key and retain
   whole-field `field_sources.tags`.
5. Exactly four `companion_mutation` routes remain: X submit, X retry, review
   opened, and review apply. G2 readiness-triggered publication, movie
   exclusion, ingest Save as Title→Tags→Description→Save with no radios or
   Analyze, and the hosted iframe contract remain unchanged. NIM completion
   still does not publish.

## Superseded statements

ADR-0072 remains accepted. Only its decisions 1–4, insofar as they prescribe
separate unread and history lists, duplicate rows, analyzed-only history, and
marking every row opened, together with its “no JSON/schema change”
consequence, are succeeded by this merged-history, pending-visibility, and
inbox-payload contract.

ADR-0068 remains accepted. Only §1’s sentence “Tags replace, they do not
union.” is succeeded by preserve-and-append Apply. Checkmarked-field writes and
the zero-tag prohibition remain in force.

Matching present-tense two-list and replacement wording in
[docs/X_COMPANION.md](../X_COMPANION.md), [SPEC.md](../../SPEC.md),
[PRODUCT.md](../../PRODUCT.md), [ROADMAP.md](../../ROADMAP.md), and
[README.md](../../README.md) is likewise succeeded. No other companion trust,
publication, movie-exclusion, ingest-Save, or hosting statement is superseded.

Do not edit the bodies of accepted ADR-0068 or ADR-0072.

## Consequences

Administrators see pending and analyzed companion items in one newest-activity
history. Mixed timestamps may reorder a row when analysis completes. Full
history refresh cost still grows with eligible media. Best-effort `x` / `𝕏`
seeding never overwrites a conflicting catalog definition and never blocks
Save. Per-tag sources distinguish newly appended AI keys from retained manual
tags; pre-0032 tags have no backfill. Combined tag vectors may exceed the v4
five-tag suggestion cap and fail closed at 32.

The inbox route and four mutation routes are unchanged in number. Schema head
is revision `0032`. No notification permission, manifest change, or YouTube
seed is introduced.

## References

- [ADR-0063](0063-companion-side-panel-web-host.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
- [ADR-0068](0068-companion-review-save-and-readiness-triggered-publication.md)
- [ADR-0069](0069-five-tag-generic-media-suggestion-contract.md)
- [ADR-0070](0070-companion-exclusion-of-movie-workflows.md)
- [ADR-0071](0071-native-side-panel-review-inbox-chrome.md)
- [ADR-0072](0072-native-side-panel-unread-inbox-and-title-bar-history-chrome.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
