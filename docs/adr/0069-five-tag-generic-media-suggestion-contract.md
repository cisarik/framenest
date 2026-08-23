# ADR-0069: Five-Tag Generic Media Suggestion Contract

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0016’s live generic prompt asked for roughly 4–10 tags and the validator
allowed up to 12. Companion review will treat tags as the common apply. Quality
matters more than quantity for GIF, image, and video storage.

Movie identification keeps its own prompt and a maximum of 12 tags.

## Decision

1. Live generic `PROMPT_VERSION` is `framenest-media-suggestion-v4`.
2. `TAG_MIN_COUNT` remains 1. `TAG_MAX_COUNT` becomes 5. New provider output
   with 0 or 6+ tags is invalid.
3. The NVIDIA prompt instructs: return 1 to 5 concise English display tags that
   are most significant for storing this GIF, image, or video; quality over
   quantity; prefer 3 to 5 only when visual evidence supports it; omit weak,
   redundant, speculative, or filename-derived tags; never return more than
   five. Anti-injection and JSON-only rules remain.
4. Result schema stays `framenest-media-suggestion-result-v1`. Do not invent a
   parallel result schema.
5. Historical v3 JSON remains readable as stored text. A historical codec is a
   later slice. Website non-movie Analyze by AI uses the same live v4 contract.
6. Movie-identification prompt version and `MAX_TAG_COUNT = 12` are unchanged.
7. This Worker implements the live validator and prompt. It does not add
   companion review tables or a stored-result codec.

## Superseded statements

ADR-0016 remains accepted. Only the live generic prompt/tag-count contract is
succeeded by v4.

## Consequences

New generic runs carry at most five tags. Older durable rows may still hold
more; later review mapping must treat overflow as non-applicable history.

## Deferred

Historical v3 codec, inbox display of `legacy_limit` tags, and living-doc
SPEC/PRODUCT wording.

## References

- [ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
- [ADR-0045](0045-content-classification-and-movie-identification.md)
