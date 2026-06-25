# ADR-0024: Cover Studio and AI Cover Candidates

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Cooperator accepted the manual Cover Studio and AI cover-candidate direction
through bounded task
`FRAMENEST-CYCLE-061-DOCUMENT-MANUAL-AI-AND-COVER-WORKSPACES`.

## Context

FrameNest should provide a premium, cover-first gallery. Current implementation
does not yet include persistent media records, cover persistence, thumbnail
derivatives, Cover Studio, imported image covers, or AI-generated covers.

[ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md) accepts
ephemeral JPEG derivatives for VLM transport and explicitly does not implement
gallery persistence or cover storage. Before persistent covers and thumbnails
are designed, FrameNest needs a clear cover-source and candidate lifecycle that
prioritizes manual human selection.

Related documents:

- [ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [COVER_PIPELINE.md](../../COVER_PIPELINE.md)
- [GALLERY.md](../../GALLERY.md)
- [SPEC.md](../../SPEC.md)

## Decision

### Manual Cover Studio first

The primary cover workflow is manual.

The future Cover Studio should allow the user to scrub a media timeline, display
the exact current timestamp, preview the selected frame, support fine keyboard
movement conceptually, and require an explicit `Set as cover` action.

When a source frame is accepted as the cover, FrameNest must retain an exact
durable cover timestamp and generate deterministic derivatives from the accepted
source frame.

This ADR does not specify final key bindings.

### Playback independence

Cover timestamp and playback start are separate.

The cover timestamp does not change normal playback start. Ordinary `Play`
starts at `00:00`. Seeking to the cover timestamp is a separate explicit action
if FrameNest later offers it.

### Cover candidate model

Possible cover candidates include:

- selected source frame;
- currently accepted cover;
- future imported image;
- future AI-generated image.

Only one candidate is active at a time. Creating or generating a candidate must
not activate it automatically. Activation requires explicit human acceptance.
FrameNest must preserve the prior accepted cover until another candidate is
explicitly accepted.

### AI cover generation

`Generate with AI` is a separate future workflow from metadata VLM analysis.

It must show only compatible image-generation or image-editing models. It may
optionally use the selected source frame when reference input is supported. Cloud
execution requires explicit cloud confirmation.

AI cover generation creates a new cover candidate. It must preserve manual
candidates, identify AI-generated output clearly, retain provider/model
provenance or supported authenticity metadata, require explicit review and
acceptance, and never automatically replace the current cover.

FrameNest must not select one permanent NVIDIA image-generation model as
product architecture.

### Deferred contracts

The following remain deferred:

- provider and model selection;
- capability contract details;
- reference-image policy;
- prompt construction;
- output dimensions;
- aspect ratio;
- content-safety handling;
- provenance format;
- output media format;
- derivative sizes;
- cache and retention lifecycle;
- timeout;
- cancellation;
- cost and trial disclosure;
- imported-image workflow;
- persistence schema.

## Rationale

Manual cover selection is deterministic, local-first, and understandable. It
keeps covers useful without internet access, without provider credentials, and
before AI workflows mature.

Separating candidate creation from activation prevents generated or imported
images from replacing user-approved covers unexpectedly. Preserving the exact
cover timestamp supports reproducible derivatives and future rebuilds.

Keeping AI cover generation separate from metadata VLM analysis avoids assuming
one model or prompt can serve every workflow.

## Consequences

### Positive

- Manual cover selection is the baseline workflow.
- Cover timestamp semantics are explicit before schema design.
- Normal playback is not affected by cover choice.
- AI-generated output remains optional, reviewable, and non-automatic.
- The accepted cover remains stable until the user explicitly accepts another
  candidate.

### Costs and limitations

- Future implementation must track candidate state separately from the accepted
  cover.
- Derivative generation, storage, retention, and cache invalidation remain to be
  designed.
- AI cover generation requires future capability filtering, provider selection,
  provenance, and safety policy.

## Current Implementation Boundary

No Cover Studio, cover persistence, cover candidate storage, imported cover
workflow, AI cover generation, or thumbnail cache is currently implemented.
This ADR records accepted architecture for future work only.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, gallery/cover
implementation tasks, catalog implementers, AI-provider implementers, and
security reviewers.

Retention: retained permanently; superseded only by a later accepted ADR.

Inbound links: ADR index, [COVER_PIPELINE.md](../../COVER_PIPELINE.md),
[GALLERY.md](../../GALLERY.md), [PRODUCT.md](../../PRODUCT.md),
[SPEC.md](../../SPEC.md), [ROADMAP.md](../../ROADMAP.md), and
[README.md](../../README.md).

Cleanup owner: future explicitly authorized Worker only through a superseding
ADR.

## Revisit Triggers

Revisit when authorizing persistent cover schema, thumbnail derivatives, imported
image covers, AI cover generation, provider/model selection, generated-image
provenance, content-safety policy, background generation jobs, cancellation, or
cache-retention lifecycle.

## Related Documents

- [ADR index](README.md)
- [ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [AI_WORKSPACE.md](../../AI_WORKSPACE.md)
- [COVER_PIPELINE.md](../../COVER_PIPELINE.md)
- [GALLERY.md](../../GALLERY.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
