# ADR-0083: Modular Research Providers and Administrator-Curated Timeline

## Status

`Accepted`

Accepted by the Cooperator on 2026-09-26. This decision records architecture
only. It does not implement a provider, change schema, call a provider,
provision a credential, publish or deploy.

## Decision Date

2026-09-26

## Context

[ADR-0082](0082-kronika-one-product-and-private-records.md) accepted one
Kronika in this repository, with Search and Research restored into the capture
module, owner-only reading of private records, direct owner sharing, and
Timeline entry when a result is complete. The Cooperator later replaced those
four points. MEME and Movie stay. The chatgpt.com capture module stays in the
tree and is parked. The end goal remains the S10 public rename of this
repository to Kronika.

FrameNest already has a media-analysis provider registry
([ADR-0081](0081-declarative-openai-compatible-provider-registry-and-administrator-vision-probe.md)).
That registry is a Chat Completions-style media contract. Research needs its
own provider-neutral boundary. It must not replace media analysis or treat the
media protocol as the research contract.

## Decision

### Provider-neutral research boundary

Search and Research are application capabilities behind one provider-neutral
boundary in the existing domain, application and infrastructure split.

| Layer | Responsibility |
|---|---|
| Domain | Pure research request, result, lifecycle, capability, usage and typed-error values. Ownership and publication rules stay separate domain concerns. |
| Application ports | Research provider, request repository, budget ledger and atomic result completion. No HTTP, database, SDK or capture imports. |
| Application | One lifecycle coordinator: authorize, reserve budget, submit, poll, cancel, validate, save and reconcile cleanup. It must not automatically resubmit an interrupted research generation. |
| Infrastructure | Selected adapter, bounded HTTPS transport, non-secret configuration and document rendering. |
| API adapters | Research requests, personal history, common-record reads, administrator approval and operational controls. |
| Composition | Wire the coordinator into the existing server process. No second server, broker or deployment system. |

The boundary must admit the parked chatgpt.com capture module and a future
self-hosted provider as further adapters without rewriting records or the UI.
A capture adapter stays unavailable for new Search and Research work until it
proves those capabilities. Selection is server-controlled and snapshotted at
admission. An active request does not change provider or model because
configuration changed. Clients cannot supply endpoint, model or tool fields.
There is no automatic fallback to another provider.

### Execution location

The model and web-search loop runs natively at the selected provider.
FrameNest supervises admission, polling, cancellation, validation, local
persistence and remote cleanup. FrameNest does not execute that provider's
internal agent loop and does not fetch arbitrary result URLs.

Only the submitted question text and fixed non-secret instructions may leave
the host on this path. Private media, media derivatives, unrelated records,
account identities, browser state, local paths and application credentials
must never enter provider context. Research accepts no attachment.

Loading a page, viewing history, saving metadata or opening status must not
start generation. One explicit authenticated submission authorizes one bounded
native generation.

### Selected first provider and fixed configuration

The first provider is the OpenAI Responses API, provider id
`openai-responses`, fixed model `gpt-5.5-2026-04-23`, with native
provider-managed research and no automatic fallback. These values are
implementation defaults. This ADR does not apply them to a live account.

| Setting | Search | Research |
|---|---|---|
| Provider id | `openai-responses` | `openai-responses` |
| Model | `gpt-5.5-2026-04-23` | `gpt-5.5-2026-04-23` |
| Reasoning effort, server-side only | `low` | `high` |
| Tool allowlist | `web_search` only | `web_search` only |
| `max_tool_calls` | 3 | 20 |
| `max_output_tokens` | 4096 | 32768 |
| Execution | background | background |
| Application deadline | 180 seconds | 1800 seconds |
| Per-operation reservation | USD 0.50 | USD 5.00 |

Common settings:

```text
enabled = false
endpoint = https://api.openai.com/v1/responses
background = true
store = true
tool_choice = required
parallel_tool_calls = false
web_search.external_web_access = true

global_concurrency = 1
waiting_queue_capacity = 0
daily_budget_usd = 10
monthly_budget_usd = 30
budget_calendar = UTC

prompt_max_utf8_bytes = 16384
provider_response_max_bytes = 8388608
answer_max_utf8_bytes = 2097152
citation_count_max = 200

connect_timeout_seconds = 5
http_operation_timeout_seconds = 30
poll_interval_seconds = 5
automatic_generation_retries = 0
```

No conversation chaining, file search, MCP, code execution, browser tools,
local filesystem tools, location context or multi-agent feature is enabled.
The parked capture descriptor id is `chatgpt-page`. It is unavailable for new
Search and Research work.

Research has its own selected provider. It does not replace media-analysis
provider selection. Research configuration is an optional section; an absent
section means research is disabled. Existing media-configuration versions must
remain readable. A disabled or unconfigured research provider must not prevent
ordinary application startup.

### Budgets and accepted enforcement limits

Application thresholds are Search USD 0.50, Research USD 5, daily USD 10 and
monthly USD 30. Before any live use, a provider monthly hard limit of USD 30
is required. Delayed enforcement and possible overshoot of the application
thresholds were explicitly accepted. An application reservation is not an
absolute invoice cap. Listed provider prices must be revalidated before live
activation. A kill switch blocks new admission and requests cancellation of
active work. Missing usage is a visible accounting failure, not a silent
success.

### External retention

Local question and answer history is intentional, including complete Research
reports. Request remote storage for background work so recovery can retrieve
the same response. Delete that remote response after validated local
persistence, or after terminal cancellation or failure reconciliation.

Deletion of the response object is not a promise to erase provider security
logs or all processing state. Standard provider retention, including possible
security retention after deletion of the retrieved response, was accepted.
Zero Data Retention is not required. Background processing is not treated as
Zero Data Retention compatible.

### Question and answer history

Kronika stores each question and its answer, including the complete Research
report. Personal history is a separate view. It includes the caller's
unfinished and failed work as well as completed records. Ordinary household
members do not see another owner's private or unfinished records.

A completed question and answer is an immutable document in this version.
Another explicitly submitted question creates another history entry. The
application derives a display title from the question and does not purchase
another model call to name it.

### Administrator read-all and curated household publication

Private means visible to the owner and to authenticated application
administrators, and not to other ordinary household members. An authenticated
application administrator can read all product records, including private and
unfinished work. This deliberately replaces the ADR-0082 rule that
administrator status alone never permits reading another owner's private
content. The exact retained-history link is the partial-supersession section
of
[ADR-0082](0082-kronika-one-product-and-private-records.md).

Administrator access is application content only. It grants no access to
provider secrets, browser credentials, browser profiles or host
administration. Tailscale membership alone is neither household membership nor
administrator authority. A client-supplied user id is not owner authority.

Administrators approve completed question and answer records, and successfully
analyzed media, for the shared page. Owners do not publish directly to that
page. Approval rechecks the exact record version and validated completion.
Media approval also requires successful analysis and the existing persisted
metadata-review readiness. Approval records the decision, sets household
visibility, and sets the first timeline-entry time only on the first approval.
Withdrawal removes the shared card and keeps personal history. Reanalysis
keeps the previous approved projection and chronological position until the
administrator approves the new successful result. Failure preserves the
previous success. Successful generation never applies metadata automatically.
Approval of an administrator's own item uses the same explicit action.

The shared page is for verified household members only. Internet publication
remains disabled. The existing public composition stays off and must not
expose these records. Existing internet-publication actions are not the
household-sharing authority for Kronika records.

### Shared Timeline and Gallery

The main page is the Timeline. It contains only administrator-approved
records, including when the viewer is an administrator. Personal history is a
separate view. Gallery remains a working view, including authorized unanalyzed
media, and keeps the existing shell, CSS, controls and player. No new frontend
framework or design system is introduced.

Timeline order remains newest entry first, then stable id order, with a
default page size of 24 and a server maximum of 100. Filters combine Search,
Research and the existing media categories. GIF remains a technical format and
does not replace the Meme category.

### Safe rendering

Render the question as escaped text and the answer through a bounded Markdown
renderer and an HTML allowlist. Preserve the complete original answer
independently of its presentation. On a formatting or parser failure, display
the entire escaped answer. Prohibit scripts, event handlers, forms, frames,
SVG, media, external styles and image or resource loading. Serve the document
from the authorized render endpoint in a sandboxed frame, with a restrictive
content security policy, `no-store` and `no-referrer`. Never insert generated
HTML into the main application DOM. Show validated citations as visible,
user-activated links with safe schemes and `noopener noreferrer`. Never fetch
those targets automatically.

A successful result requires a terminal completed provider response, a
complete final answer, no refusal or incomplete marker, and evidence that web
search executed. A completed answer that no matching evidence was found may be
stored when search execution is proven. Do not fabricate citations. Validation
is not a claim of factual correctness.

### Credential and configuration boundary

Non-secret configuration stores a credential identifier only. No key-input
endpoint, frontend key, command-line key or secret-bearing diagnostic is
introduced. Production reads one dedicated project-scoped service credential
through the existing systemd credential boundary. The accepted identifier is
`KRONIKA_RESEARCH_OPENAI_API_KEY`. Development may use that named environment
variable only when an operator explicitly configures it. Provisioning, the
provider monthly limit and any live call remain separate later grants. This
decision does not create the credential.

### Active sequence

After this documentation slice the active order is S4-A, S6, S4-B, S7-P, S8,
S9, then S10, as recorded in [ROADMAP.md](../../ROADMAP.md). Parked, and not
gates for that order, are the remaining S3 host completion, capture-mode
Search and Research restoration, S5 ZIP activation, and S7-C capture
application integration. Each active row needs its own implementation grant.
Acceptance, publication, host operations, credential provisioning and live
calls stay separate.

## Relationship to Earlier Decisions

| Earlier decision | Relationship |
|---|---|
| ADR-0081 provider registry | Retained for media analysis. It does not define the research contract and is not an automatic research fallback. |
| ADR-0082 one product | Partially superseded on the four points named in that file. One repository, the parked capture constraints, Gallery, sanitized output, the empty-database transition, the single release helper and the S10 rename remain accepted. |
| ADR-0044 analysis lifecycle | Retained for media. Research must not inherit automatic resubmission of interrupted analysis. |
| ADR-0048 Tailscale identity | Retained trusted ingress and explicit mapping. Application-administrator content access is now an explicit product privilege and still grants no host or credential access. |
| ADR-0049 / ADR-0074 publication | Internet publication stays off for these records. Household Timeline entry is administrator approval, not those publication endpoints. |

## Consequences and Scope

Current normative product, specification, server, security, roadmap and
operator documents must follow this decision. Schema head stays `0033` until a
later authorized slice. Research stays disabled until that slice implements it
and a separate grant activates it. No AP pin, managed integration block or
upgrade-ledger change is part of this decision.

Personal photos and future local photo AI, old-database import, native share
apps, providers other than this selected provider and the parked capture
module, internet publication and production hardening remain outside the
active sequence.

## Revisit Conditions

A different provider, model, budget or retention posture, or a return to
owner-only private reading, direct owner publication or completion-triggered
Timeline entry, requires a new explicit Cooperator decision and a superseding
ADR. A failed provider, privacy or rendering gate stops the affected slice. It
does not authorize automatic fallback, weaker content controls or internet
publication.
