# FrameNest Worker Closeout Handoff

## Lifecycle Status

This handoff closes the concrete Worker session that completed the NVIDIA
provider deployment and validation block. No active Worker remains.

This file grants no future implementation, diagnostic, deployment, provider,
media, Git, or host authority. Only a new explicit ORCHESTRATOR prompt may
grant authority to a future Worker. Brainstorming, likely-next-work notes, and
state summaries in this file are context only, not task authority.

## Canonical Repository State

- Repository: `https://github.com/cisarik/framenest.git`
- Branch: `main`
- Current pre-closeout HEAD: `a1321338c54fd109ea2f4641fd618fa04338e282`
- Subject: `fix: align NVIDIA connection test request`
- Parent: `85aa09efde3fdaeeb5d3de9419ba3937750e0620`
- AP pin: `4c4213a81f9c8c7378778cdee7fcdf03db10088f`
- Migration head: `0007`

The final closeout commit containing this `NEXT_WORKER.md` file becomes the
new canonical `main` HEAD after successful push.

Relevant repository references:

- [README.md](README.md)
- [SERVER.md](SERVER.md)
- [SECURITY.md](SECURITY.md)
- [docs/UBUNTU_NUC_DEPLOYMENT.md](docs/UBUNTU_NUC_DEPLOYMENT.md)
- [docs/adr/0036-production-ai-credentials-via-systemd.md](docs/adr/0036-production-ai-credentials-via-systemd.md)

## Canonical Deployed NUC State

Accepted sanitized final state:

- Current application release:
  `a1321338c54fd109ea2f4641fd618fa04338e282`
- Previous retained release:
  `6873683f928e08b8724b82b2cb46386c691ae924`
- Service: enabled, active, healthy
- Health: exact accepted ok state
- Database: ready at revision `0007`
- Application listener: loopback-only on port `8000`
- Firewall: no public port-8000 rule
- Failed systemd units: zero at final validation
- AI provider: `nvidia-nim`
- AI model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- Credential: available to the running service through the accepted systemd
  credential boundary
- Latest persisted connection-test state: `success`
- Latest capability state: `available`
- No media has yet been uploaded or analyzed through the production workflow
- Vercel AI Gateway is not configured
- No provider fallback is implemented

No private IP addresses, SSH fingerprints, credential values, private media
names, raw journal text, or database contents are recorded here.

## Completed Logical Block

The NVIDIA provider deployment and validation block is complete and
rendered-accepted.

Accepted commit chain:

- `9782f9f71da5bdc973b6df947b3eee2f37155503` added production AI credential
  deployment support through repository-owned systemd credential source
  material and a bounded operator helper.
- `6873683f928e08b8724b82b2cb46386c691ae924` completed fully unconfigured AI
  status support so unconfigured and credential-missing states remain safe and
  actionable.
- `f37c0b9e6110785815f1c31318bf027f263dee95` completed production AI
  deployment rollback coverage for deployment-controlled credential, drop-in,
  and non-secret AI configuration state.
- `1b890b8aa88cafe7308a0f92d6a9cdc392967d42` hardened deployment readiness,
  recovery handling, and fail-closed behavior.
- `5997e7919157115716e54a8d0cc5f50762372b43` made exact tracked
  provider-specific AI credential drop-ins the sole source of authority and
  added systemd/capability acceptance gates.
- `85aa09efde3fdaeeb5d3de9419ba3937750e0620` added dynamic AI test-state
  refresh and completed the browser Status modal AI state display.
- `a1321338c54fd109ea2f4641fd618fa04338e282` corrected NVIDIA
  connection-test sampling and invalid-response classification.

Rendered/operator acceptance:

- The AI modal initially showed the configured provider and model.
- The historical failed test became visible dynamically.
- The corrected exact-once NVIDIA text connection test succeeded.
- The modal then displayed:
  - Configuration: Configured
  - Credential: Available to server
  - Last connection test: Successful
  - Tested at: present
- No media was sent during the connection test.
- NVIDIA reasoning was disabled.
- No retry occurred.

Therefore:

- Nemotron is not rejected as the primary candidate.
- NVIDIA NIM is currently the validated production provider.
- The old `provider_unreachable` state was replaced by `success`.
- No additional NVIDIA retry is pending.

## Incident History And Lessons

### Initial Deployment Readiness Failure

The first live credential deployment attempt encountered immediate readiness
timing problems and required recovery investigation. No credential compromise
was found.

### Malformed Systemd Drop-In

A helper bug installed literal escaped newline characters. The live drop-in was
repaired from the exact tracked template. Commit `5997e7919157115716e54a8d0cc5f50762372b43`
made tracked provider-specific templates the sole authority and added systemd
acceptance plus running-service capability validation.

### Historical Provider Unreachable Result

The first NVIDIA text connection test persisted `provider_unreachable`.

A separate unauthenticated diagnostic proved DNS, TCP, verified TLS, and the
NVIDIA HTTP path were reachable.

Commit `a1321338c54fd109ea2f4641fd618fa04338e282` then:

- aligned connection-test temperature with the accepted non-thinking profile;
- kept `top_k` at `1`;
- kept `max_tokens` at `8`;
- kept reasoning disabled;
- stopped mapping invalid transport responses to `provider_unreachable`.

The next single authorized corrected test succeeded.

## Current Product And Authority Boundaries

The following remain unimplemented and unauthorized:

- browser upload;
- resumable or chunked upload;
- large-file ingest;
- quarantine and atomic media publication;
- duplicate detection;
- derivative/frame generation for uploaded media;
- first real media analysis;
- automatic analysis;
- Vercel fallback;
- server model catalog;
- authentication;
- user/admin capability enforcement;
- admin UI;
- keyboard correction;
- responsive-layout correction.

Do not treat brainstorming or likely-next-work context as accepted
implementation.

## Likely Next Logical Block Context

Likely title: Upload, Safe Ingest, Large Files, And First Media Analysis.

This is context only. It grants no authority. A future ORCHESTRATOR should
begin with architecture and repository inspection before any implementation.

Current product intentions to preserve:

- the central FrameNest server stores authoritative media;
- remote clients upload to the server;
- large uploads over LAN or Tailscale must tolerate interruption;
- upload processing must stream to disk rather than buffering the whole file;
- resumable or chunked upload should be evaluated;
- incomplete uploads belong in quarantine or staging;
- type, size, path, and content validation occur before publication;
- duplicate detection and checksums are required;
- publication into managed storage must be atomic;
- upload and AI analysis are separate state machines;
- AI analysis remains an explicit user action;
- a deliberate `Upload & analyze` flow may combine those actions in UX without
  analyzing partial uploads;
- GIF/video analysis should use bounded server-generated derivatives or
  representative frames according to an explicit media policy;
- no provider should receive an entire large media file merely because the
  browser uploaded it;
- first real-media acceptance must use explicit COOPERATOR-provided media and
  separate provider-bearing authority;
- exact upload protocol, limits, storage paths, derivative policy, and job
  mechanism remain undecided.

Do not select or implement an upload protocol from this handoff.

## Language Protocol

- Michal and the ORCHESTRATOR communicate in Slovak.
- A WORKER communicating directly with Michal uses Slovak.
- ORCHESTRATOR-to-WORKER prompts and task authority are written in English.
- Formal WORKER-to-ORCHESTRATOR reports are written in English.
- Repository AP protocol documentation has not yet been updated for this rule;
  that remains a later separate task in `cisarik/ap`.

## Worker Context State

The closing Worker session had approximately 36 percent context usage at the
final provider-validation report. It was not context-exhausted. It is being
closed because the logical block is complete, not because of context failure.

No future work is assigned to this session.
