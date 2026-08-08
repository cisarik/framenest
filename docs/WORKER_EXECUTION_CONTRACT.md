# FrameNest Worker Execution Contract

## Status

This is the discoverable Worker execution and repository-authority contract for
FrameNest. It records how a fresh Worker must run Python, tests, and isolated
worktrees without reconstructing environments or claiming false exact-source
evidence.

Classification: living repository execution contract.

Consumers: Orchestrator, Worker, and local FrameNest developers.

Retention: remains while FrameNest uses Poetry, the canonical `.venv`, and AP
Worker execution.

## Relation To Other Authority

| Document | Role |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | Project rules, truth map, security and authority boundaries |
| [`.ap/AP.md`](../.ap/AP.md), [`.ap/AP_WORKER.md`](../.ap/AP_WORKER.md), [`.ap/AP_ORCHESTRATOR.md`](../.ap/AP_ORCHESTRATOR.md) | Pinned normative Analytic Programming protocol |
| [README.md](../README.md) | Repository overview and user-facing status |
| [DEVELOPMENT.md](../DEVELOPMENT.md) | Local browser-development launcher workflow |
| This document | Worker reliability: runtime, `.venv`, exact-source evidence, tests, and classification |

Do not duplicate the full AP protocol here. Task authority still comes only from
the current authoritative Orchestrator prompt. This contract does not grant
push, publication, deployment, provider contact, or production mutation.

## Runtime And Dependency Authority

- FrameNest requires **CPython 3.13.x** (`>=3.13,<3.14`).
- **Poetry** is the authoritative dependency, virtual-environment, and lockfile
  manager ([ADR-0002](adr/0002-python-environment-and-dependency-manager.md)).
- `pyproject.toml` plus the committed `poetry.lock` define dependency authority.
- **`uv` is not the project dependency manager.** Per
  [ADR-0006](adr/0006-macos-python-interpreter-provider.md), `uv` may acquire or
  locate a CPython 3.13 interpreter for Poetry (for example via
  `./framenest setup`). That limited role does not authorize `uv sync`,
  `uv lock`, or adopting an untracked `uv.lock`.
- An incidental or untracked `uv.lock` is **not** project authority. Do not
  adopt it. Do not delete it merely because it is present unless a separate
  hygiene task authorizes cleanup.

## Canonical `.venv`

The canonical project environment on this development host is:

```text
/home/agile/Projects/framenest/.venv
```

Workers must not casually:

- create a replacement `.venv`;
- delete `.venv`;
- reconstruct `.venv`;
- move `.venv`;
- symlink `.venv`;
- copy site-packages;
- run `poetry env use` merely to make an isolated worktree pass;
- perform an editable install merely to make an isolated worktree pass.

Treat those operations as environment reconstruction. They require explicit
Orchestrator authority and are outside ordinary implementation tasks. An
environment failure is an **environment defect**, not a candidate defect to
“fix” by rebuilding the environment.

## Isolated Worktrees And Exact-Source Evidence

When an isolated worktree needs Python execution against the **candidate**
checkout, use the canonical interpreter with an explicit candidate `PYTHONPATH`:

```text
/home/agile/Projects/framenest/.venv/bin/python
```

plus:

```text
PYTHONPATH=<exact-worktree>/src
```

Example patterns supported by this repository:

```text
cd <exact-worktree>
PYTHONPATH=<exact-worktree>/src \
  /home/agile/Projects/framenest/.venv/bin/python -m pytest <focused-tests>

PYTHONPATH=<exact-worktree>/src \
  /home/agile/Projects/framenest/.venv/bin/python -m framenest.adapters.cli.catalog --help
```

Equivalent `-m` entry points exist for other console modules declared in
`pyproject.toml` (`framenest.server`, `framenest.infrastructure.persistence.cli`,
`framenest.adapters.cli.backup`, and related adapters). Prefer
`python -m <module>` with `PYTHONPATH=<exact-worktree>/src` over bare console
scripts when proving candidate source.

### Why this matters

Exact-candidate evidence must import and execute **candidate** source.

The canonical `.venv` may resolve `framenest` through an installed or
parent/canonical checkout (for example a `.pth` pointing at the canonical
`src/`). A subprocess, console script, or Python invocation that silently
imports that revision does **not** prove the candidate.

This reasoning is not acceptable:

> The subprocess used parent/canonical source, but the changed feature is
> unrelated, so it is acceptable.

It is not acceptable exact-SHA evidence.

Before trusting a result, verify provenance, for example by printing
`framenest.__file__` under the same invocation and confirming it resolves under
`<exact-worktree>/src`.

Host shells that inject AppImage `LD_LIBRARY_PATH` (or similar) may break the
canonical interpreter. Clear only the interfering variables for the command, or
classify the failure as an environment defect. Do not rebuild `.venv` to work
around shell pollution.

## Failure Classification

Classify outcomes honestly:

| Class | Meaning | Worker response |
| --- | --- | --- |
| Candidate defect | Failure caused by the candidate change | Fix within scope, or stop if out of scope |
| Harness defect | Test/harness wrong relative to intended contract | Fix harness only with authority; do not hide candidate issues |
| Environment defect | Interpreter, `.venv`, host tools, or shell pollution | Report `ENVIRONMENT LIMITATION`; do not reconstruct `.venv` to force PASS |
| Acceptance limitation | Evidence requires owner/provider/production authority not granted | Report the limitation; do not improvise authority |
| Non-blocking observation | Useful note that does not block the gate | Record briefly; do not reopen closed wholes |

A mandatory non-zero gate or unresolved traceback prevents PASS / candidate
readiness for that gate. Do not convert an environment failure into a
candidate patch by rebuilding dependencies.

## Python Tests

Ordinary Python tests use pytest through the Poetry-managed environment:

```text
poetry run pytest
```

or, for exact-worktree provenance:

```text
PYTHONPATH=<exact-worktree>/src \
  /home/agile/Projects/framenest/.venv/bin/python -m pytest <selection>
```

`pyproject.toml` configures `testpaths = ["tests"]`. The logical whole
determines test breadth. Do not claim that every Worker must always run the
entire suite.

## JavaScript Tests

Tracked frontend contract suites live under `tests/*.test.js` and use Node’s
built-in `node:test` runner. There is no repository `package.json` test script
and no npm-managed JS test toolchain.

Authoritative ordinary invocation from the worktree root:

```text
node --test tests/<name>.test.js
```

or a bounded glob of non-browser suites, for example:

```text
node --test tests/*_frontend.test.js tests/*_cockpit.test.js tests/gallery_*.test.js
```

Do not install a new JS toolchain merely to document or run these suites.

## Repository Browser Evidence

Tracked browser evidence uses custom system-Chrome / DevTools Protocol tests,
not Playwright as repository acceptance authority.

Gated suites include:

- `tests/browser_cover_evidence.test.js`
- `tests/browser_catalog_removal_evidence.test.js`
- `tests/browser_movie_identification_evidence.test.js`

Invocation:

```text
FRAMENEST_RUN_BROWSER_EVIDENCE=1 node --test tests/browser_<name>_evidence.test.js
```

Discoverable prerequisites from those suites:

- `FRAMENEST_RUN_BROWSER_EVIDENCE=1` (otherwise the suite stays gated/skipped);
- system `google-chrome-stable`, or `FRAMENEST_CHROME_BIN` override;
- Node built-in WebSocket / CDP driving (no npm browser dependencies);
- ffmpeg where the suite generates synthetic media;
- a usable Python interpreter for spawning the FrameNest server helper.

Those suites create disposable temporary workdirs and remove them on cleanup.
They bind loopback only and must not save a browser profile into the
repository.

Untracked operator tooling such as `.playwright-mcp/` is **not** project
authority. External Playwright/MCP may remain a valid operator tool when
separately available; distinguish it from tracked repository browser evidence.

Browser evidence still requires exact-source provenance when used to accept a
candidate: the server process under test must import the candidate worktree, not
a silent parent/canonical install.

## Analytic Programming

FrameNest uses the pinned AP submodule at `.ap/`. Read:

- [AGENTS.md](../AGENTS.md) for project-specific rules and the managed AP block;
- [`.ap/AP.md`](../.ap/AP.md) for the protocol;
- [`.ap/AP_WORKER.md`](../.ap/AP_WORKER.md) for Worker boundaries;
- [`.ap/AP_ORCHESTRATOR.md`](../.ap/AP_ORCHESTRATOR.md) for Orchestrator boundaries.

Treat `.ap/` as read-only during ordinary work. Do not upgrade AP or change the
`.ap` gitlink without an explicit AP update task.

## Baseline-Bound AP Execution

FrameNest declares a root `ap.project.conf` (schema v1) that binds AP execution
to the canonical Poetry-owned interpreter and declares exactly three
operations:

| Operation | argv | Trailing argv |
| --- | --- | --- |
| `runtime-info` | `-c <provenance probe>` | forbidden |
| `test` | `-m pytest` | forbidden |
| `test-focus` | `-m pytest` | allowed only after `--` |

The declared runtime is **CPython 3.13** at `.venv/bin/python`, with
`sourceRoot = src` and `provenanceModule = framenest`. **Poetry remains the
owner** of dependency resolution, `poetry.lock`, and the `.venv` execution
environment; `ap.project.conf` binds to that environment, it does not replace
or manage it. Automatic repair through `uv`, `pip`, `poetry env use`, or
`.venv` reconstruction is prohibited; an unsuitable interpreter is an
environment defect to report, not a defect to repair.

Validation and execution:

```text
./.ap/ap project check --root /home/agile/Projects/framenest --candidate
./.ap/ap project check --root /home/agile/Projects/framenest --baseline <commit>
./.ap/ap exec --root /home/agile/Projects/framenest \
  --baseline <commit> --operation <id> [-- <trailing argv>]
```

`--baseline` must be an **exact Orchestrator-authorized or otherwise canonical
commit identity**. A Worker must not derive mutation authority merely from the
current `HEAD`. Candidate-mode validation is **readiness evidence only** and
authorizes nothing. A locally created commit is **not canonical** merely
because `ap project check` or `ap exec` accepts it. Technical readiness does
not grant mutation, publication, deployment, or production authority; Worker
authority remains separate from technical executability and comes only from
the current authoritative Orchestrator prompt.

The Cursor/AppImage host session is an **untrusted ambient execution
boundary**. `ap project` and `ap exec` re-exec themselves through a sanitized
bootstrap and then run the operation with `env -i`: the child environment is
exactly `PATH=/usr/bin:/bin`, `LC_ALL=C`, `LANG=C`, `PYTHONNOUSERSITE=1`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=<root>/src`, and the
`AP_PROJECT_ROOT` / `AP_BASELINE` / `AP_OPERATION` markers. Inherited
`APPIMAGE`, `APPDIR`, `LD_*`, `PYTHONHOME`, `VIRTUAL_ENV*`, `GIT_*`, and
`SSH_AUTH_SOCK` values do not reach the executed process; the tool reports
contaminated variable names/classes only, never values. `ap exec` is a direct
**execution envelope, not a sandbox**: it constrains the environment and argv
of declared operations, it does not isolate the process from the host.

Known limitations:

- Project identity is currently rooted in the **mutable
  `remote.origin.url`**; it is the present trust root for `projectId`
  verification, not a strong identity anchor.
- The dynamic loader acts on the initial shell interpreter **before** the
  tool's sanitized re-exec can run, so loader-level contamination classes
  cannot be filtered for that first stage (pre-re-exec loader limitation).

## Authority Boundaries

Implementation authority does **not** implicitly grant:

- push;
- publication;
- deployment;
- production mutation;
- provider contact;
- external X or YouTube acquisition.

Those require explicit phase-appropriate Orchestrator authority. Availability of
SSH, Tailscale, credentials, or mounted disks is capability context, not
authority ([AGENTS.md](../AGENTS.md)).

## Shell And GUI Safety

Unless specifically authorized, Workers must not launch from the Worker shell:

- Cursor;
- VS Code;
- `xdg-open`;
- GUI applications;
- AppImages.

Bounded browser automation used for repository acceptance evidence is distinct
from launching arbitrary GUI or IDE tooling.
