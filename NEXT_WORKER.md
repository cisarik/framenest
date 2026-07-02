# FrameNest Worker Handoff

## 1. Identity And Authority

A future Worker must be a fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest WORKER role.

This Worker session closes with the enclosing closeout commit. After that
commit is verified and pushed, this concrete Worker instance must not be reused
and no active Worker remains.

Automatic context compaction occurred during the preceding implementation task.
Compaction did not reset the session lifecycle and did not create a fresh
Worker session.

NEXT_WORKER.md restores context only. It grants no task, Git, repository
mutation, runtime, browser, private-media, credential, provider-call, network,
deployment, or filesystem-mutation authority. Every future concrete task
requires a new authoritative ORCHESTRATOR prompt.

Expected enclosing closeout commit:

```text
subject: docs: prepare live gallery AI acceptance handoff
parent: ffa8545608eda826a1a5fed311614b168f117e34
changed path: NEXT_WORKER.md only
effect: closes this concrete Worker session
```

The enclosing commit SHA is intentionally not recorded here because the commit
does not exist until this file is committed.

## 2. Repository Truth

```text
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
pre-closeout HEAD: ffa8545608eda826a1a5fed311614b168f117e34
latest implementation subject: fix: refine gallery analysis workflow
persistent Gallery integration boundary: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
persistent preview backend boundary: 7289d8b509f851f8c87009c239012e658746662c
library workflow boundary: ba942f219932782b8f323768dbc9ed4667f6400f
migration head: 0007
highest accepted ADR: ADR-0030
cover semantics authority: ADR-0024
```

## 3. Current Accepted Gallery Behavior

Accepted COOPERATOR product direction:

- persistent JPEG previews are accepted for MVP;
- the static Gallery card has no permanent play glyph, badge, or overlay;
- the complete media surface remains the pointer and keyboard control for
  explicit inline playback;
- inline original GIF/MP4 playback is accepted;
- the media title opens the larger Details modal;
- Details continues to use original GIF/MP4 content;
- untagged supported GIF/MP4 cards show Analyze above Edit;
- tagged cards show meaningful persisted tags and omit the card-level Analyze
  shortcut;
- cards with no tags show no empty dot, blank metadata row, or placeholder;
- broad Gallery visual redesign remains frozen except concrete defects.

## 4. Analyze Workflow Semantics

Card-level Analyze is a needs-metadata shortcut. It is shown only when persisted
canonical tags are empty and is not durable AI provenance.

During a real request, card-level Analyze uses `Analyzing...`, `aria-busy`,
duplicate blocking, and an animated background tied to the in-flight request.
It uses the existing identity-only server suggestion endpoint and never calls a
provider directly from the browser.

Success opens the existing metadata editor with unsaved editable Title,
Description, Tags, and Suggested filename. Save remains explicit. AI analysis
alone performs no metadata save and no physical rename. Failure restores a
retryable state with a sanitized error. Unavailable AI opens the read-only
Status explanation without sending an analysis request.

Additional accepted decision:

- Analyze by AI must remain available inside the Edit modal even when the media
  already has persisted tags;
- an admin may have changed the active provider or model;
- the user may explicitly request a new draft from the currently active model;
- a new draft must not overwrite persisted metadata until Save;
- card-level Analyze visibility and modal re-analysis availability are
  separate concepts.

No AI analyzed badge or persistent AI provenance exists.

## 5. AI Status Truth

Commit `ffa8545608eda826a1a5fed311614b168f117e34` implemented sanitized AI
capability states:

- `not_configured`;
- `credential_unavailable`;
- `configured_unverified`;
- `available`;
- `authentication_failed`;
- `rate_limited_or_quota_exhausted`;
- `model_unavailable`;
- `provider_unreachable`;
- `provider_error`.

An unconfigured server no longer fabricates Vercel or another provider/model. A
real selected provider/model remains visible when its credential is
unavailable. The browser remains read-only and contains no provider
administration. Provider credentials remain server-side. Live provider
reachability is distinct from non-secret configuration.

## 6. Current Operator AI Configuration

Sanitized non-secret facts only:

- the COOPERATOR interactively selected NVIDIA NIM;
- selected model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
- the non-secret configuration was successfully written outside the repository;
- refer to that configuration only as `<SERVER_AI_CONFIG_PATH>`;
- the configuration stores provider/model selection but no credential;
- `NVIDIA_API_KEY` remains in the private server secret boundary;
- COOPERATOR-observed real media analysis with this model succeeded with
  reasoning disabled.

Do not inspect or reproduce configuration-file contents during closeout or from
this handoff.

## 7. Model Catalog Status

Current `./framenest ai configure` behavior:

- lists supported providers;
- proposes one provider default model;
- permits an explicitly entered validated custom model ID;
- remembers model selection per provider;
- does not yet present a curated VLM model picker.

This is expected current behavior, not a regression. A future bounded operator
task may add a code-owned curated model catalog. The catalog must include only
media-analysis-compatible image/JPEG models in the normal picker, and entries
should carry lifecycle such as recommended, experimental, deprecated, or
removed. Advanced custom model entry should remain possible.

Curated catalog work is lower priority than completing the accepted Gallery UX
and secure explicit download. Do not list unverified current external model
availability from this handoff.

## 8. Evidence

Worker-observed evidence for
`ffa8545608eda826a1a5fed311614b168f117e34`:

- focused tests: 229 passed;
- full suite: 1285 passed, 3 skipped;
- JavaScript syntax passed;
- Fish syntax passed;
- Python compile validation passed;
- `git diff --check` passed;
- public/local/origin equality was reported;
- final worktree/index was reported clean;
- no private media, browser automation, provider request, credential access,
  dependency installation, migration, or source-media mutation occurred.

COOPERATOR-observed evidence:

- persistent preview Gallery rendered real private GIF/MP4 media successfully
  before the correction in `ffa8545608eda826a1a5fed311614b168f117e34`;
- inline playback UX is accepted;
- media title opening Details is accepted;
- NVIDIA Nemotron real media analysis previously succeeded with reasoning
  disabled;
- NVIDIA NIM is now selected in non-secret operator configuration.

Still unproven after `ffa8545608eda826a1a5fed311614b168f117e34`:

- rendered absence of the permanent play overlay;
- rendered absence of the empty metadata dot;
- real card-level Analyze animation;
- real successful NVIDIA card analysis opening unsaved editor fields;
- Save transition from Analyze shortcut to displayed tags;
- modal Analyze by AI remaining available after tags are saved;
- truthful rendered NVIDIA Status after launcher secret loading;
- source integrity during final real AI acceptance.

## 9. Immediate Next Task

```text
Task:
Run live Gallery AI workflow acceptance

Task type:
Private-media, real-provider, and Safari acceptance without repository
modification initially

Expected implementation commit:
none
```

The next task must use a fresh Worker instance with Medium reasoning.

The future authoritative prompt should grant the minimum authority required to:

- use the private MEMEs library through `<PRIVATE_MEMES_ROOT>` in reports;
- use a disposable database and cache outside the repository and source root;
- allow the root launcher to load the existing private AI secret file without
  printing, reading, hashing, or reporting its contents;
- read the existing non-secret server AI selection;
- verify that NVIDIA NIM and the selected Nemotron model are active;
- start one loopback-only runtime;
- use one dedicated Safari acceptance document at the exact loopback origin;
- perform at most one real card-level AI media analysis request initially;
- upload only the already-authorized bounded derived JPEG frames and technical
  metadata through the existing server provider boundary;
- inspect the real Analyze animation and editor transition;
- save metadata only after separately observing the pre-save unsaved state;
- verify source-media integrity before and after;
- leave the runtime active only for COOPERATOR rendered acceptance when safe.

The future task must prohibit:

- secret content disclosure;
- provider-key logging;
- direct browser provider calls;
- unrelated Safari state;
- external origins other than the explicitly authorized NVIDIA provider call
  made by the server;
- source rename, move, delete, overwrite, transcode, or sidecar creation;
- implementing fixes;
- adding the curated model catalog;
- repository modification, commit, or push.

## 10. Required Next Acceptance Outcomes

The next task should prove:

1. static cards contain no permanent play overlay;
2. untagged cards contain no empty metadata dot;
3. one untagged supported card shows Analyze above Edit;
4. one tagged card shows persisted tags and no card-level Analyze;
5. the Edit modal retains Analyze by AI regardless of persisted tags;
6. Status shows the genuinely selected NVIDIA provider and model;
7. server credential availability is truthful without exposing a secret;
8. card Analyze enters a real animated `Analyzing...` state;
9. exactly one provider request occurs;
10. success opens the existing editor with unsaved editable suggestions;
11. no catalog save occurs before Save;
12. explicit Save persists metadata;
13. after refresh, tags appear and card-level Analyze disappears;
14. reopening Edit still exposes Analyze by AI;
15. no physical filename change occurs;
16. no source file, timestamp, size, or hash changes;
17. no server path, secret, prompt, raw provider payload, or data URL reaches
    the browser or report.

If this acceptance passes, the recommended next product slice is secure
explicit browser download. If a concrete Gallery or AI workflow defect is
observed, authorize only the smallest evidence-driven correction first. The
curated VLM model catalog remains a separate later operator slice.

## 11. Privacy

Do not include private media absolute paths in NEXT_WORKER.md. Use:

```text
<PRIVATE_MEMES_ROOT>
```

Do not include the absolute AI configuration path. Use:

```text
<SERVER_AI_CONFIG_PATH>
```

Do not include secret-file paths or credential values.

## 12. Immediate Non-Goals

Do not mix the next acceptance or correction into:

- curated model catalog;
- provider discovery;
- persistent AI provenance;
- AI analyzed badges;
- accepted covers;
- Cover Studio;
- browser download;
- Fedora deployment;
- Tailscale;
- authentication;
- synchronization;
- trusted client-local availability;
- Tauri.

## 13. Closure Summary

```text
pre-closeout HEAD: ffa8545608eda826a1a5fed311614b168f117e34
latest implementation boundary: ffa8545608eda826a1a5fed311614b168f117e34
migration head: 0007
automatic compaction occurred: yes
current Worker closes with enclosing commit: yes
active Worker afterward: none
active disposable runtime: none
immediate next task: live Gallery AI workflow acceptance
private-media authority granted by this handoff: no
provider-call authority granted by this handoff: no
Orchestrator session: remains active
```
