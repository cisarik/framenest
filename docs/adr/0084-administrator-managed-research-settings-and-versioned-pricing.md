# ADR-0084: Administrator-Managed Research Settings and Versioned Pricing

## Status

`Accepted`

Accepted by the Cooperator on 2026-09-30. This decision records architecture
and the confirmed product choice of a bounded, administrator-selectable model
catalog. It does not publish, deploy, call a provider, provision a credential
or refresh the NUC.

## Decision Date

2026-09-30

## Context

[ADR-0083](0083-modular-research-providers-and-administrator-curated-timeline.md)
accepted the provider-neutral Search and Research boundary with a single fixed
model, `gpt-5.5-2026-04-23`, and fixed non-secret configuration. That fixed
model choice and the interpretation that every bounded administrator
adjustment required a further architecture decision are now superseded.

The Cooperator confirmed a bounded, server-controlled model catalog with four
exact identifiers, an unchanged default, and versioned pricing so a later price
change never reprices an already admitted request. The provider boundary,
default-disabled behavior, submission restrictions, privacy and publication
rules, capture parking and accepted limits are preserved.

## Decision

### Administrator-managed selection

Verified application administrators select the research model only through
server settings and the approved catalog. Search and Research submissions
cannot select a provider, model, endpoint or tools. Research stays disabled by
default, and the accepted monetary defaults are also upper bounds.

The immutable catalog lives in
`src/framenest/infrastructure/ai/research_models.py`. Exactly four exact
identifiers are selectable:

| Exact identifier | Purpose and pinning |
|---|---|
| `gpt-5.5-2026-04-23` | Default; dated snapshot |
| `gpt-5.6-sol` | Flagship alternative; undated identifier; promotional-price expiry guard |
| `gpt-5.6-terra` | Recommended balanced, lower-cost alternative; undated identifier |
| `gpt-5.6-luna` | Lowest-cost option; undated identifier; no claim of equivalent answer quality |

Aliases (`gpt-5.5`, `gpt-5.6`), arbitrary strings, `gpt-5.5-pro` and the
unselected `gpt-5.4` alternative are not admitted. Unknown or alias models fail
before configuration persistence, reservation or provider contact. There is no
network model discovery. Historical catalog entries remain available for
accounting even after they stop being selectable.

### Versioned pricing

Pricing is integer micro-USD per million tokens. Web search is
`10,000,000` micro-USD per thousand calls for every entry and tier. Short
pricing applies through `272,000` input tokens inclusive; above that boundary
long pricing applies to the entire request.

| Model | Short input | Short cached read | Short cache write | Short output |
|---|---:|---:|---:|---:|
| `gpt-5.5-2026-04-23` | 5,000,000 | 500,000 | 5,000,000 | 30,000,000 |
| `gpt-5.6-sol` | 4,000,000 | 400,000 | 5,000,000 | 20,000,000 |
| `gpt-5.6-terra` | 2,000,000 | 200,000 | 2,500,000 | 12,000,000 |
| `gpt-5.6-luna` | 200,000 | 20,000 | 250,000 | 1,200,000 |

| Model | Long input | Long cached read | Long cache write | Long output |
|---|---:|---:|---:|---:|
| `gpt-5.5-2026-04-23` | 10,000,000 | 1,000,000 | 10,000,000 | 45,000,000 |
| `gpt-5.6-sol` | 8,000,000 | 800,000 | 10,000,000 | 30,000,000 |
| `gpt-5.6-terra` | 4,000,000 | 400,000 | 5,000,000 | 18,000,000 |
| `gpt-5.6-luna` | 400,000 | 40,000 | 500,000 | 1,800,000 |

Usage distinguishes ordinary input, cached reads and cache writes. Cache-write
tokens are billed only at their write rate and are never charged again as
ordinary input. Reasoning tokens remain a subset of output tokens and are never
charged again. Cost is computed with integer arithmetic and per-component
ceiling rounding.

For `gpt-5.6-sol`, `valid_until` is `2026-11-22T00:00:00Z`. New admissions
whose deadline could cross that cutoff are refused until a separately reviewed
schedule update extends or replaces it. Expiry never rewrites admitted or
historical pricing, chooses another model or prevents disabling research.

### Immutable request pricing

Admission persists an immutable provider, model and profile identity. New
admissions use the profile `configuration_version = "s9r-20260930"`. The
immutable schedule is resolved from the persisted tuple
`(provider_id, model_id, configuration_version)`; the mapping is append-only and
a future price change adds a new profile version. Existing version `"3"`
requests on `gpt-5.5-2026-04-23` keep the original 2026-09-26 flat schedule, and
old checkpoints remain readable. Restart resolves pricing from the persisted
request identity, never from the currently selected model.

Configuration changes cannot reprice or regenerate an existing attempt.

### Runtime refresh and disabling

A persistent coordinator is built whenever the catalog engine exists, including
a disabled start. Construction performs no credential provisioning and no
provider contact. Admission and capabilities read a fresh validated
configuration; saving settings never replaces the coordinator. Disabling
prevents new admissions and new submission claims while preserving history,
polling, cancellation, cleanup and reservations. Re-enabling needs no restart.

### Idempotency and one generation attempt

Admission looks up `(owner, client_request_id)` before configuration,
enablement and credential checks. A version-2 fingerprint covers owner, kind,
prompt and consent only, so an identical replay returns the original attempt
even after model, budget or enablement changes; changed content conflicts. A
receipt distinguishes new admissions. An atomic `ADMITTED` to `SUBMITTING`
repository claim guarantees only one winner issues provider creation, and
restart recovery never resubmits an uncertain creation.

### Shared configuration concurrency

Research settings, media-provider HTTP mutations and CLI configuration writers
share one concurrency contract: a per-canonical-path process lock plus a stable
sibling OS advisory lock (`fcntl` on POSIX, `msvcrt` on Windows), with revision
snapshots computed as SHA-256 of the bounded raw bytes (absent = `"absent"`).
HTTP writers use one strong `If-Match` value and a stale revision returns `409`
without writing. Direct configuration writes without a revision are
creation-only. A research-only save preserves every supported normalized
non-research value, and a media-only save preserves the research subtree;
JSON formatting, key order and `updated_at_ms` are not preserved byte-for-byte.

### Accounting failures fail closed

Unknown accounting, a terminal request whose hold is still reserved, and a
recorded operation cost above its reservation block further generation pending
operator reconciliation. The full observed charge is preserved when it exceeds
the reservation and is never clamped. This implements the already accepted
accounting rules; the monetary thresholds remain admission and accounting
controls, not an absolute invoice guarantee.

## Consequences

- Administrators choose among four documented models without a new
  architecture decision for each bounded adjustment.
- A later price change is a new profile version, never a rewrite of an existing
  request's pricing.
- Unknown accounting is an explicit state rather than a fabricated zero.
- The GPT-5.6 identifiers are undated and their prices can change; Sol carries a
  reviewable cutoff. Reservations cannot guarantee an opaque native run's final
  invoice.
- Account-specific model access and the applicable billing tier remain later
  acceptance gates, not facts recorded here.

## Supersession

This ADR partially supersedes
[ADR-0083](0083-modular-research-providers-and-administrator-curated-timeline.md):
it supersedes only ADR-0083's fixed-model decision and the interpretation that
every bounded administrator adjustment requires another architecture decision.
It preserves the provider boundary, no automatic fallback, submission
restrictions, privacy and publication rules, capture parking, default-disabled
behavior and the accepted limits. ADR-0083's original fixed-model wording
remains as historical decision text.

## Revisit criteria

A different provider, a change to the selectable catalog beyond an accepted
amendment, a changed pricing basis, or an extension or replacement of the Sol
cutoff requires a later accepted decision.
