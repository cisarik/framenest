# ADR-0029: Persistent Plain-Text Media Description

## Status

`Accepted`

## Decision Date

`2026-06-26`

## Decision Authority

The Cooperator explicitly decided: `The first persistent media description is plain text, not Markdown.`

## Context

FrameNest supports persistent display-title and canonical-tag metadata through
[ADR-0027](0027-persistent-display-title-and-canonical-tags.md) and a manual
browser `Current` workspace through Cycle 068. ADR-0023 describes description
as a future manual metadata field alongside display title, collection, canonical
tags, and suggested filename.

Before implementing description persistence, FrameNest must decide representation
semantics: whether the description uses plain text, Markdown, or another format.

### Key constraints

- Description is manual-first. AI is not required to create or edit it.
- Description is optional. Absent description is represented as `None`.
- This task does not create persistent AI drafts.
- Changing description must not rename, move, rewrite, or otherwise mutate media
  files.
- Description search is deferred.
- Catalog result-card display is deferred.
- Collection and suggested filename remain separate future fields.

## Decision

### Plain text

The first persistent media description in FrameNest is **plain text**.

Markdown syntax has no special meaning. HTML has no special meaning.

FrameNest must never:
- parse Markdown in description;
- render Markdown in description;
- parse HTML in description;
- trust embedded HTML in description;
- insert or render user-provided description as trusted HTML.

No Markdown, HTML-sanitizer, or rich-text dependency is introduced. The browser
reads and writes description through safe `textContent` or form-value APIs.

### Maximum length

A non-null description may contain at most 10,000 Unicode code points.

### Empty and whitespace-only values

At the user and application boundary:

- `None` means absent.
- An empty string means absent.
- A whitespace-only string means absent.

Empty or whitespace-only input is normalized to `None`. Empty strings are not
persisted in the database.

### Leading and trailing whitespace

For a non-empty description:
- Accepted content is preserved exactly.
- Leading whitespace is rejected.
- Trailing whitespace is rejected.
- A non-empty description is not silently trimmed and saved as a different value.

### Line breaks and control characters

Ordinary Unicode multiline text using line feed (`\n`) is allowed.

Invalid characters:
- carriage return `\r`;
- NUL (`\0`);
- tab (`\t`);
- C0 control characters other than line feed (`\n`);
- C1 control characters (U+0080–U+009F);
- any other character classified as Unicode `Cc` category except `\n`.

Ordinary internal spaces and accepted line feeds are preserved.

### Schema representation

The existing `media_metadata` table gains one nullable `description` column
in migration `0006`.

- Existing databases upgraded from `0005` preserve all existing logical media,
  display titles, and canonical tag data.
- Existing media metadata rows receive `NULL` description.
- Fresh schema creation includes the column.
- Clearing description stores SQL `NULL`.

### API contract

Description belongs to the existing complete metadata replacement model.

`GET /api/media/{media_id}/metadata` always contains an explicit `description`
member: either a string or `null`.

`PUT /api/media/{media_id}/metadata` requires an explicit `description` member:
either a string or `null`. The field is not optional at the JSON level; it must
be present as part of the complete replacement contract.

No separate description endpoint is created.

### Repository contract

`MediaMetadataSnapshot` gains a nullable `description` field.

`save_media_metadata` accepts an explicit `description` parameter.

No-op detection includes description equality. An unchanged title, description,
and tag order returns `unchanged` and preserves `updated_at_ms`.

### Browser contract

The manual `Current` metadata workspace adds an accessible plain-text description
textarea.

- Load persisted description.
- Load sparse metadata as an empty textarea.
- Expose the 10,000-character limit through `maxlength` and a truthful character
  count (e.g. `0 / 10000`).
- Allow multiple lines.
- Include description in semantic clean/dirty comparison.
- Discard restores the persisted description baseline.
- Switching or closing media protects unsaved description edits.
- `beforeunload` remains active only while the complete workspace is dirty.
- Successful Save updates the description baseline.
- Description is never rendered through `innerHTML`.

### Migration

Migration head becomes `0006`. Revision `0006` adds one nullable `description`
column to `media_metadata`. Upgrade does not modify existing data rows beyond
adding the column. Downgrade removes only the `description` column. The existing
title, tag, and media schema remain unchanged after downgrade.

### Deferred scope

The following remain deferred:
- description search;
- Catalog result-card display of description;
- collection field;
- suggested filename field;
- persistent AI drafts;
- Cover Studio;
- thumbnail generation;
- any filesystem mutation.

## Rationale

Plain text is the simplest safe representation. It avoids Markdown parsing,
HTML injection risk, rendering dependencies, and WYSIWYG editor complexity
before use cases for rich formatting are demonstrated. The manual-first and
AI-optional principles mean description editing must work fully without AI or
rich-text infrastructure.

## Consequences

### Positive

- Description storage and roundtrip work immediately with a simple text column.
- No new parsing, rendering, or sanitization dependency is introduced.
- The existing atomic metadata replacement contract extends naturally.
- Existing display-title and canonical-tag semantics remain unchanged.
- The browser textarea is accessible and straightforward.

### Costs and limitations

- Users cannot format description text (bold, italic, links, lists) without
  future Markdown or rich-text support.
- Plain-text line breaks are the only visual structure.
- Future Markdown or rich-text migration would require schema and UI changes.

## Revisit Triggers

Revisit this decision when:
- users request formatted description text;
- full-text search requires structured description content;
- a premium gallery detail view needs inline description rendering;
- persistent AI drafts need formatted description output.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, metadata domain
implementers, API implementers, browser workspace implementers, migration
implementers.

Inbound references: ADR index plus bounded product/specification documents.

Retention: until explicitly superseded.

Cleanup owner: only a future explicitly authorized task.

## Related Documents

- [ADR index](README.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0027](0027-persistent-display-title-and-canonical-tags.md)
- [ADR-0028](0028-catalog-read-model-and-search-semantics.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AI_WORKSPACE.md](../../AI_WORKSPACE.md)
