# ADR-0070: Companion Exclusion of Movie Workflows

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0045 owns content classification and movie identification on the website.
The companion review inbox is a GIF/image/video administrator loop. Movie
identification, genres, and movie-category workflows must not leak into
companion chrome.

## Decision

1. Companion inbox, badge, and review overlay exclude movie-category media and
   movie-identification analysis runs.
2. The review overlay never writes genres, content category, acquisition
   source, collection, or suggested filename. The field set is title, tags, and
   description only.
3. Website movie identification, movie prompt version, and `MAX_TAG_COUNT = 12`
   remain unchanged. This Worker does not modify movie files.
4. A future movie application owns identification and genres. Parked W2
   taxonomy remains parked.

## Superseded statements

ADR-0045 remains accepted. This ADR supplements it for companion surfaces; it
does not rewrite website movie behavior.

## Consequences

Companion operators will not review movie-identification suggestions here.
Website Edit movie flows stay available.

## Deferred

Inbox query filters and apply-time movie race rejection.

## References

- [ADR-0045](0045-content-classification-and-movie-identification.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
