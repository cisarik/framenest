# ADR-0071: Native Side-Panel Review Inbox Chrome

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0063 made the side panel chrome plus an iframe of the hosted FrameNest
origin. The accepted inbox layout is S1: a native list under the FrameNest
wordmark above the still-mounted iframe. OS notifications are out of this
whole. Badge count does not require a `notifications` permission.

## Decision

1. Keep the hosted iframe and Attach contract. Do not replace the iframe with
   the inbox, and do not clone the in-page picker into the side panel.
2. Add collapsible native inbox chrome above the iframe. Empty or dismissed
   list must not unmount the iframe in a way that breaks hosted Attach.
3. Toolbar badge is the unopened successful in-scope inbox count. Failed runs
   do not increment the success badge.
4. Do not add `notifications` permission or OS notifications in this whole.
   MV3 badge polling may use `alarms` in a later slice; that is smaller trust
   expansion than notifications and is not implemented here.
5. Ingest Save overlay remains a separate frozen contract (title, tags,
   description, enabled Save). Review overlay is a sibling, later.
6. This ADR is an accepted contract. This Worker does not implement side-panel
   list, badge, or alarms.

## Superseded statements

ADR-0063 remains accepted. Only the iframe-only chrome statement is succeeded
for the native inbox list around the existing host.

## Consequences

Side-panel width/height and iframe survival for Attach become implementation
constraints for later UI slices.

## Deferred

Native list, badge, `alarms`, review overlay files, and ingest Save regression
gates.

## References

- [ADR-0063](0063-companion-side-panel-web-host.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
