# FrameNest Architecture Decision Records

## Purpose

Architecture Decision Records (ADRs) document **accepted** architecture decisions for FrameNest. Each ADR explains the context, the decision, rationale, consequences, and how the decision may be revisited.

ADRs are normative for the decisions they record. They do not replace [SPEC.md](../../SPEC.md) product requirements, but they resolve architecture choices that implementation must follow.

## Relationship to evidence packages

Evidence packages such as [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md) collect primary-source research and provisional recommendations. Evidence packages are **not** accepted decisions. Only an ADR with status **Accepted** records project authority for an architecture choice.

## Permitted statuses

| Status | Meaning |
|---|---|
| **Proposed** | Drafted for review; not yet authoritative |
| **Accepted** | Explicitly approved and binding until superseded |
| **Superseded** | Replaced by a later ADR; retained for history |
| **Rejected** | Considered and not adopted; retained for history |

An accepted ADR may only be changed by a later ADR that supersedes it. Editing an accepted ADR in place without a superseding ADR is not permitted.

## Index

| ADR | Title | Status | Decision date | Link |
|---|---|---|---|---|
| 0001 | Supported Python Version | Accepted | 2026-06-23 | [0001-supported-python-version.md](0001-supported-python-version.md) |
