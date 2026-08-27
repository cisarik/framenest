# ADR-0079: Administrator Automatic Analysis Runtime Setting

## Status

`Accepted`

Accepted by the Cooperator on 2026-08-27.

## Decision Date

2026-08-27

## Context

Automatic post-catalog analysis remains default-off
([ADR-0044](0044-durable-automatic-post-catalog-analysis.md),
[ADR-0066](0066-administrator-owned-x-automatic-generic-analysis.md)). The git
and EnvironmentFile value `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED` is
process-start configuration. Administrators needed a companion Settings toggle
that takes effect without rewriting systemd files, without `sudo`, and without
an Alembic schema jump.

Website Edit and hosted companion Analyze stay unchanged. Desktop Settings
remains unshipped. Ordinary identities must not enable cloud frame upload.
YouTube stays excluded from automatic analysis.

Four `companion_mutation` routes already exist for X submit, X retry, review
opened, and review apply
([ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)).
The Settings dialog is `chrome-extension://…` origin, so a settings write from
the side panel needs a fifth flagged mutation.

## Decision

1. **JSON sidecar, not schema 0034.** Persist
   `{database_path.parent}/runtime-settings.json` (NUC:
   `/var/lib/framenest/runtime-settings.json`) with atomic tmp + `os.replace`
   and mode `0o600`. Body:
   `schema_version`, `automatic_media_analysis_enabled`, `updated_at_ms`.
   Tests may override the path with `FRAMENEST_RUNTIME_SETTINGS_PATH`.
   Do not add an Alembic revision, SQLite table, EnvironmentFile rewrite, or
   tracked git mutation. The git default remains `false`.

2. **Precedence for this one bool.** If the sidecar exists and the key is a
   valid bool, that value wins. Otherwise
   `FrameNestSettings.automatic_media_analysis_enabled` (env
   `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED`) applies. Missing or malformed
   JSON fails closed to that fallback. This is a narrow overlay on
   [ADR-0005](0005-configuration-strategy.md), not a general settings store.

3. **Dynamic without restart.** `ScheduleAutomaticMediaAnalysis.enabled` and
   `GET /api/ai/automatic-analysis-capability` read the overlay per call.
   Disabling stops queuing future catalog events; in-flight runs complete.
   Enabling applies to future events only. No historical backfill
   ([ADR-0066](0066-administrator-owned-x-automatic-generic-analysis.md) §4).
   YouTube remains excluded.

4. **Fifth `companion_mutation`.** `PUT /api/admin/settings/automatic-analysis`
   requires capability `provider.operate`, audit action
   `settings.automatic_analysis.put`, header `X-FrameNest-Request: 1`, and
   `companion_mutation=True`. Ordinary callers receive 403 `CAPABILITY_DENIED`.
   Enable body requires `confirm_cloud_upload: true` or the request is 422.
   Disable does not require confirm. GET capability stays unflagged and still
   requires `provider.operate`.

5. **Companion Settings only.** The side-panel Settings dialog shows an
   Administration section with checkbox **Automatic media analysis** only when
   the connected identity has `provider.operate`. Ordinary, disconnected, and
   hosted website Edit do not show it. Enabling opens an in-sheet confirm, not
   `window.confirm`. Desktop Settings stays unshipped.

6. **Not in catalog backup.** The sidecar is excluded from catalog backup the
   same way as `ai/config.json`. Loss returns to env/default.

## Superseded statements

No prior ADR body is edited. This ADR narrowly supplements ADR-0005, ADR-0044,
ADR-0066, ADR-0067, and ADR-0075 for this one runtime bool and the fifth
companion mutation. Named “exactly four `companion_mutation` routes”
statements in later living documents are succeeded here; the accepted ADR
bodies that recorded four routes remain historical.

## Deferred

Cover Studio, VPS, Funnel, YouTube automatic analysis, ordinary automatic
analysis, changing the git default to true, website Settings/Edit checkbox,
backup expansion, EnvironmentFile rewrite, and a new capability name.

## Consequences

Administrators can turn automatic analysis on or off from the companion
without a service restart or schema migration. Ordinary identities cannot.
In-flight analysis is not cancelled. Catalog restore does not restore this
sidecar.
