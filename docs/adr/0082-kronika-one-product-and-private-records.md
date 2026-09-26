# ADR-0082: Kronika One Product and Private Records

## Status

`Accepted`; partially superseded by
[ADR-0083](0083-modular-research-providers-and-administrator-curated-timeline.md)

Accepted by the Cooperator on 2026-09-23. S0 records this decision only; it does
not implement, publish or deploy the later slices. Existing application code,
schema head `0033`, capture vendor packaging and service sources are unchanged
by that documentation slice. The historical reasoning below is retained. Where
this decision and ADR-0083 conflict, ADR-0083 is current for the four points
named in the next section.

## Partial supersession

[ADR-0083](0083-modular-research-providers-and-administrator-curated-timeline.md),
accepted on 2026-09-26, partially supersedes this decision. The superseded
points are only:

1. Capture-only Search and Research. This file treats missing Search and
   Research as a selective restore into the capture module and forbids
   fallback to an external LLM API. ADR-0083 delivers Search and Research
   through a provider-neutral application boundary. The chatgpt.com capture
   module remains parked and is not the current research provider.
2. Owner-only private reading. The sentence below, "Administrator status alone
   cannot read another owner's private records," and the ADR-0048 relationship
   note are retained as the 2026-09-23 reasoning. ADR-0083 replaces that rule:
   an authenticated application administrator can read all product records,
   including private and unfinished work. That access is application content
   only.
3. Direct owner sharing. This file lets the owner explicitly share a record
   with mapped household members. ADR-0083 replaces that with administrator
   approval of completed question and answer records and successfully analyzed
   media. Owners do not publish directly to the shared page.
4. Completion-triggered Timeline entry. This file enters Search and Research
   on the Timeline after a complete transactional save, and enters media after
   the first successful validated analysis. ADR-0083 keeps those completions
   in personal history and the administrator review inventory. The shared
   Timeline contains only administrator-approved records.

Unaffected decisions remain accepted. Those include one repository and
application, the parked capture-module constraints, Gallery as a working view,
sanitized output, the empty-database transition, the single release helper and
the S10 public rename. Do not read the retained paragraphs below as permission
to ignore ADR-0083 on the four points above.

## Decision Date

2026-09-23

## Context

FrameNest already supplies the application shell, Gallery/Details, catalog,
media handling, identity ingress and immutable NUC release workflow. Its
repository also contains a stripped capture kernel in `vendor/kronika-ask` and
application-owned JPEG frame preparation, deterministic ZIP and budget code.
The closed Kronika source contains the missing Search/Research capture
capabilities. Maintaining two products, libraries or account systems would
duplicate application authority rather than complete the intended product.

The existing publication-based Gallery and administrator workflows do not
provide the accepted private-by-default common-record model. Existing test
databases contain unwanted data; there is no preservation/import requirement
for those datasets. These facts require an explicit staged transition rather
than a claim that the desired behavior already exists.

## Decision

### One Repository, Application and Capture Module

The existing FrameNest repository becomes one Kronika. No new repository is
created. FrameNest retains ownership of the application, authoritative catalog,
media preparation, identity, sharing and deployment. Capture owns bounded
ChatGPT interaction and job/result state, not a family library or access policy.

Move `vendor/kronika-ask/src/kronika/**` to `src/kronika_capture/**`, update
imports/resources/packaging/tests, verify the result, then remove the executable
vendor copy so one implementation remains. The command is `kronika-capture`.
Selectively restore only missing Search/Research, required export/sanitization
helpers and relevant tests from the clean source commit
`66c40d43c577276b0ad304a494fbbb1ffb6fc933`, recording original commit, source
and destination in provenance. Do not port the source manager, local accounts,
family library or Git history. FrameNest JPEG preparation, deterministic ZIP
and budget calculations remain where they are.

The internal `framenest` package, migration history, compatible HTTP headers
and deployment identifiers remain during this stage. UI/product presentation
changes in S8 and public repository names in S10; no mass `framenest` rename.

### Common Catalog, Timeline and Privacy

Add common records in the existing database with stable ID, kind/content
reference, owner, `private` or `family` visibility, creation time, first
timeline-entry time and display name. Media retains its tables; Search and
Research documents use the same database and preserve complete text/Markdown.

Ownership exists at media catalog insertion. Only the first successful,
validated analysis enters a medium on Timeline. One medium has one card;
reanalysis updates it without changing its original entry time. A failed
analysis creates no new card and preserves an older successful result.
Search/Research enters only after complete result and job binding are saved
transactionally and idempotently. Pending/error work is not a family memory.
Successful analysis does not bypass metadata-suggestion approval.

Timeline becomes the main page, newest entry first with stable secondary ID
order, default 24 items and server cap 100. Filters combine Search/Research
with existing media categories; GIF remains a format, not the Meme category.
The existing shell, CSS, controls, Gallery and Details/player are retained;
Gallery remains a separate working view, including authorized unanalyzed media.
No new frontend framework or design system is introduced.

Every new record starts private. The server derives its owner from verified
Tailscale identity and explicit permission mapping; a local administrator must
use an explicitly configured owner. A client-supplied `user_id` is not owner
authority. The owner may explicitly share with mapped household members.
Administrator status alone cannot read another owner's private records.
Apply access policy to lists, counts, search, detail, jobs, previews, playback,
downloads and direct APIs, including existing administrator content paths.
New APIs join the existing permission table and mutation protection.

Family sharing is never content publication. Public composition stays off and
must not expose new records. Archived generated HTML is sanitized, with no
JavaScript or external resources, and is never trusted HTML in the main app.

### Persistent Capture and Bounded Inputs

Application and capture are separate processes communicating through the
existing bridge on `127.0.0.1`, with a per-install token, exact Host/Origin
checks and no wildcard CORS. The frontend never receives that token. Extend
the existing job manager rather than adding another browser queue. One active
job includes a paused job. Stable request IDs identify retries; identical
content returns the original job and conflicts are refused. Retain terminal
state/results for 24 hours, at most 256 records; refuse capacity overflow
instead of prematurely evicting idempotency.

Use one persistent headed Chromium on permanent Xvfb and one dedicated profile.
Do not launch per task, enable automatic stealth, inspect/select/report models
or reasoning settings, or fall back to an external LLM API. A web restart must
not close the browser. Bridge loss reconnects; a browser crash pauses service
without an automatic restart loop. Manual starts are at least five minutes
apart as an operational brake, not a guarantee against challenges.

Bounded login/challenge detection on the owned page enters `needs_admin`,
blocks new work and waits for the Cooperator's intervention through a temporary
loopback-only view over SSH. Explicit continuation checks readiness and resumes
only from a safely known point. A possibly sent prompt is never automatically
resent; ambiguity ends with a typed failure. The separate 30-minute admin wait
does not consume active-response time; expiry ends the job, not the browser.

Search/Research uses no attachment. Media accepts at most one ZIP, 32 MiB,
256 real JPEG frames, each at most 128 KiB with long side at most 480 px.
Only `ZIP_STORED` and sequential `frame-0001.jpg` names are accepted; reject
encryption, nested archives, non-JPEG files, paths, duplicates and gaps. Verify
actual JPEG data and dimensions before browser contact. Private staging uses
server IDs, directories `0700`, files `0600`, 15-minute unbound expiry and
terminal-job cleanup without following symlinks. Existing verified budgets may
lower limits; video still requires at least 12 frames. Synthetic evidence of
image understanding in the ZIP is required before real use. Upload acceptance
alone is insufficient; failure stops the path without bypass or model switching.

Never extract browser credentials, cookies, sessions, localStorage, profile
contents, unrelated tabs or history. Only the Cooperator handles real login and
opaque profile backup/restore, with the browser stopped for backup/restore.
Never replace a problematic profile automatically. Logs contain operational
metadata only, not prompts, answers, media, secret-bearing URLs or account data.

### Empty-Database and Deployment Transition

Do not import either old test database. A separately authorized operation must
identify exact database/WAL/SHM files and stop all writers before deleting only
those objects. Preserve source media, profiles, identity configuration, secrets,
other state and Git/Meta archives. Create the empty database through normal
schema/migrations without rewriting migration history. Rollback restores the
previous code with a compatible empty database, not deleted test data.

Extend `deploy/ubuntu/framenest-release`; do not add a second deployment system.
Capture uses a separate `kronika-capture` account and private state under
`/var/lib/kronika-capture`, with separate web/bridge/browser-runner supervision.
Normal web deployment does not restart Chromium; a capture runtime change gets
one planned restart. Installed tooling, service state and profile readiness are
unverified until a later authorized read-only host preflight. The NUC remains
the development/test machine; this is not production hardening.

Implement the locked S0-S10 sequence in [ROADMAP.md](../../ROADMAP.md), one row
per implementation grant. S1 is the first executable-code change. Focused
independent checks precede acceptance of browser lifecycle, upload and privacy;
integrated acceptance precedes joint deployment. Cooperator rendered acceptance
occurs on the exact accepted public-main commit refreshed onto NUC. Preserve
the existing baseline-bound AP Python route and `node --test` toolchain.

After transfer and acceptance, separately authorize S10: verify names/commits,
rename old `cisarik/kronika` to `kronika-capture-archive`, rename FrameNest to
`kronika`, update authorized remotes/deployment source references, verify refs
and release operation, then archive the old repository. Do not rewrite history
or publish non-public predecessor history. Local paths need not be renamed.

## Relationship to Earlier Decisions

Earlier ADR files and historical host observations remain unchanged. This
decision supersedes only the conflicting direction for new Kronika records:

| Earlier decision | Relationship |
|---|---|
| ADR-0035 server authority | Retained and extended to common media/text records; capture is not another catalog authority. |
| ADR-0044 analysis lifecycle | Retained review/lifecycle foundation; Timeline entry requires validated success and reanalysis must not duplicate it. |
| ADR-0048 Tailscale identity | Retained trusted ingress and explicit mapping; administrator capability is not a private-content read override. |
| ADR-0049 / ADR-0074 publication | Publication-based visibility and public-rollout direction do not apply to new records. Family sharing is separate; public composition stays off. |
| ADR-0053 upload review / ADR-0076 companion inbox | Existing implementations are baseline history; new private records require owner/family access on these paths too. |
| ADR-0060 / ADR-0075 release and NUC role | Retained single release route and development/test role; capture supervision is added later. |
| ADR-0081 provider registry | Existing HTTP-provider implementation remains documented; it does not define capture model/reasoning controls or authorize fallback. |

## Consequences and Scope

The principal later refactor is common-record ownership and access, not a broad
repository rename. Documentation must distinguish accepted target behavior
from the current implementation until each slice supplies evidence. No AP pin,
managed integration block or upgrade-ledger change is part of this decision.

Personal photos and future local photo AI, old-database import, native share
apps, new external LLM providers, public publication and production hardening
remain outside this stage. Longer-term desktop/media foundations are not new
S0-S10 scope. An ADR, roadmap or available host tool does not grant execution,
deletion, provider-call, publication or deployment authority.

## Revisit Conditions

Revisit only through a new explicit Cooperator decision and a superseding ADR.
A failed host, privacy or synthetic capture gate stops the affected slice; it
does not permit weaker privacy, silent resubmission, challenge bypass, a second
product or an unapproved fallback.
