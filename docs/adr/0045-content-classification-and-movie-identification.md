# ADR-0045: Content Classification, Acquisition Source, and Movie Identification

## Status

`Accepted`

## Decision Date

2026-07-22

## Context

FrameNest already distinguishes technical media kinds (`video`,
`animated_image`, `image`). Operators also need independent first-class
concepts for content classification, acquisition source, movie genres, and a
bounded movie-identification analysis profile. Encoding Meme, Movie, and
YouTube as one enum would collapse orthogonal product dimensions and block
safe Gallery filters.

Generic media analysis must keep reasoning off. Movie identification needs
reasoning on with an explicit bounded budget, without uploading the original
movie or audio.

## Decision

### Technical media kind

`MediaKind` remains an intrinsic technical property. It is not user-editable
content classification and is unchanged by category or source edits.

### Content category

Canonical values:

- `general` (neutral default)
- `meme`
- `movie`

Content category is manually editable metadata. AI may suggest it; AI must not
silently persist it. Migration defaults every existing metadata row to
`general` without guessing.

### Acquisition source

Orthogonal to content category. Initial values:

- `unknown` (neutral default for historical rows)
- `manual_upload`
- `library_scan`
- `youtube_manual_claim` (owner-asserted classification)

This decision introduced only editable classification and did not add URL,
channel, or yt-dlp fields. [ADR-0046](0046-youtube-manual-ingestion-and-provenance.md)
later keeps this value while placing deterministic, immutable acquisition
evidence in a separate source-specific claim.

### Genres

Movie genres are first-class metadata separate from ordinary tags. A bounded
canonical list is stored in `media_genres`. Genres are allowed only when
content category is `movie`.

### Analysis profiles

- `generic_media` (`analysis_definition=automatic_post_catalog`): reasoning
  OFF (`enable_thinking=false`); existing representative-frame JPEG transport;
  no regression in provider-call count.
- `movie_identification` (`analysis_definition=movie_identification`):
  reasoning ON with `chat_template_kwargs.enable_thinking=true` and
  `reasoning_budget=2048`; exactly one provider submission per explicit run;
  no provider fallback; no retry after provider submission.

### Movie-identification derivative

Locally extract a bounded set of temporally diverse frames (about six
targets), reject near-black and duplicate frames, compose one bounded JPEG
contact sheet, and send only that single derivative. Temporary work is cleaned
deterministically. Absolute paths and audio never leave the local process.
Chain-of-thought is neither persisted nor displayed.

### Durable runs

Movie identification creates a separate durable run under
`movie_identification` and does not overwrite, delete, or reinterpret the
generic automatic-analysis run. Idempotent create-pending semantics prevent
accidental duplicate submissions for the same definition.

## Consequences

- Gallery filters Memes / Movies / YouTube query independent dimensions.
- Schema revision `0017` adds classification columns, `media_genres`, and
  analysis provenance fields.
- NVIDIA generic calls remain thinking-disabled; movie identification uses an
  explicit bounded reasoning budget.

## Related

- [ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md)
- [ADR-0044](0044-durable-automatic-post-catalog-analysis.md)
- [ADR-0046](0046-youtube-manual-ingestion-and-provenance.md)
