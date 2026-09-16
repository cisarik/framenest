# ADR-0081: Declarative OpenAI-Compatible Provider Registry and Administrator Vision Probe

## Status

`Accepted`

Accepted by the Cooperator on 2026-09-16 as part of the approved plan and
implementation direction for this logical whole.

## Decision Date

2026-09-16

## Context

Server AI provider administration was a CLI-only operator boundary
([ADR-0020](0020-on-demand-ai-suggestion-review.md),
[ADR-0035](0035-authoritative-server-and-client-state-model.md)) with two
hardcoded providers, NVIDIA NIM and Vercel AI Gateway. Provider discovery and
administrator website Settings were deferred
([ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md),
[ADR-0044](0044-durable-automatic-post-catalog-analysis.md)), and
[ADR-0079](0079-administrator-automatic-analysis-runtime-setting.md) deferred
website Settings while shipping only the companion automatic-analysis checkbox.

The Cooperator's accepted target for this logical whole was: declare
OpenAI-compatible providers (first instance OpenCode Go), select a vision
model, ping it, run a color pong, and then use the existing Analyze path
through the administrator website surface, judged step by step.

Dated external facts, retrieved from public documentation on 2026-09-16 and
stated here as dated public documentation only (the live catalog is confirmed
later under a separate explicit provider-call grant): OpenCode Go documents a
chat-completions endpoint at `https://opencode.ai/zen/go/v1/chat/completions`,
a models catalog at `https://opencode.ai/zen/go/v1/models`, and a model
`deepseek-v4-flash-vision-exp` that is an `@ai-sdk/openai-compatible`
chat-completions model. The Go subscription is a monthly plan; OpenCode Zen is
a distinct endpoint family (`https://opencode.ai/zen/v1/...`) and is never
aliased to Go. Public Go documentation states that DeepSeek V4 Flash Vision
Exp is not used for training with 0-day retention (zero-data-retention
agreement through 2026-09-30), while Contributor-tier models may train on
prompts. Go is marketed for coding-agent traffic and documents abuse
monitoring; FrameNest image analysis is not coding-agent traffic, so the
implementation adds only a static `User-Agent: framenest/0.1` header and does
not fabricate coding-agent identity or session semantics, leaving the
subscription and terms decision to the Cooperator.

## Decision

1. **Non-secret schema-v2 declarative records.** Persist operator-declared
   OpenAI-compatible provider records inside the non-secret server AI
   configuration beside the existing selection and timestamps. A record is
   `provider_id`, `display_name`, `protocol`, `base_url`, `credential_env`,
   and a `models` map of model id to display name plus declared capabilities.
   Records are bounded (16 declared providers, 64 models each, 64 KiB file),
   unknown keys and unknown capabilities are rejected, provider ids are
   bounded `^[a-z0-9][a-z0-9._-]{0,63}$`, and `credential_env` is the
   environment-variable **name** only
   (`^[A-Z][A-Z0-9_]{0,63}$`, never a reserved transport header). Schema v1
   remains readable and is upgraded in memory with no provider invention;
   writers always write v2. The file never contains API keys, Authorization
   headers, cookies, provider responses, prompts, frame data, media paths, or
   database paths and never uses jsonc.

2. **One registry world.** Built-in providers are code-owned records of the
   same type as declared records; one definition type and one resolution path
   serve both. Built-in ids (`nvidia-nim`, `vercel-ai-gateway`) cannot be
   declared, edited, or deleted. Declared base URLs are exactly `https://`
   with a DNS host, no userinfo, port, query, fragment, or trailing slash, and
   no loopback/localhost/loopback-IP host; request URLs are
   `base_url + "/chat/completions"`. Loopback and local-gateway base URLs are
   deferred.

3. **Parameterized generic adapter.** A single OpenAI-compatible
   chat-completions adapter parameterized by base URL, provider id, and model
   id builds the suggestion body (bounded JPEG `image_url` data URLs,
   `response_format` for suggestions only), the text-only ping body, and the
   single-image vision-probe body. It performs one call in flight without
   automatic retries, uses a 120 s timeout with bounded request and response
   bodies, sends the static FrameNest user agent, and maps errors exactly:
   401/403 to credential/entitlement rejection, 429 to rate limiting, 404 to
   model unavailable, 5xx to provider unavailable, and other 4xx or bad JSON
   to invalid response. A provider HTTP 403 is never reported as invalid
   output. The Vercel adapter is a thin subclass over this implementation.

4. **Declared capability filtering.** Capabilities use the provider-neutral
   SPEC §22 names. The operator declares `vision_input` per model. Analyze and
   the vision probe refuse a selected model that does not declare
   `vision_input` with sanitized `409 AI_MODEL_CAPABILITY_MISSING`; browsing
   or listing models never calls a provider.

5. **Administrator website surface under `provider.operate`.** Six routes are
   mounted in the Tailscale workspace composition only: list providers,
   upsert a declared record, delete a declared record, set the active
   selection, ping, and pong. All require the `provider.operate` capability;
   mutations require the exact external `Origin` plus `X-FrameNest-Request: 1`
   and are audited before mutation with `ai_provider` targets. Built-in
   modification and active-provider deletion are refused. Responses and stored
   records expose only credential environment-variable names and availability
   booleans, never credential values. Ordinary identities receive sanitized
   403 responses and see no control; UI hiding remains convenience only and
   the server is the authorization mechanism.

6. **Ping and pong contract.** Ping is an explicit text-only provider request
   that reuses the safe last-test category and timestamp. Pong sends exactly
   one repository-owned committed synthetic fixture image (a tiny solid-red
   8x8 PNG loaded through the package resource boundary), requires explicit
   `confirm_cloud_upload: true`, judges the bounded completion against a fixed
   accepted color set with no fuzzy matching, and persists only the bounded
   observed token or `null`. Neither uses catalog media, persists a
   suggestion, logs or returns raw completion text, or runs without an
   explicit administrator action. Per-operation activity locks
   (`.test.lock` for ping, `.vision-probe.lock` for pong) keep one provider
   operation in flight.

7. **Credential names and dynamic resolution.** Declared providers resolve
   their credential by environment-variable name from the process environment
   first and then from exact-name systemd `CREDENTIALS_DIRECTORY` lookup.
   `OPENCODE_API_KEY` joins `NVIDIA_API_KEY` and `AI_GATEWAY_API_KEY` in the
   `.secrets/ai.env.fish` and systemd credential mechanisms, and its drop-in
   template is tracked under `deploy/systemd/`. Provider resolution re-reads
   the persisted configuration and environment per operation, so an added or
   activated provider takes effect without a service restart. Movie
   identification keeps its startup-resolved, NVIDIA-only wiring.

## Superseded statements

No prior ADR body is edited. This ADR narrowly succeeds the following
statements in later living documents:

- [ADR-0020](0020-on-demand-ai-suggestion-review.md) operator-boundary and
  Revisit triggers are fulfilled for non-secret provider administration; its
  browser credential and raw-response prohibitions remain in force.
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
  deferred provider-discovery contract is partially implemented through
  declared capabilities only; live catalog refresh remains deferred.
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
  "operator-only provider administration" phrasing is read as including the
  authenticated administrator website surface; it does not widen ordinary
  client access.
- [ADR-0036](0036-production-ai-credentials-via-systemd.md) credential
  mechanism is extended by a third identity, `OPENCODE_API_KEY`.
- [ADR-0044](0044-durable-automatic-post-catalog-analysis.md) deferred
  provider-management UI statement succeeds for this surface.
- [ADR-0079](0079-administrator-automatic-analysis-runtime-setting.md)
  "website Settings deferred" statement succeeds for the provider surface
  only; the companion automatic-analysis checkbox is unchanged.
- [ADR-0075](0075-nuc-development-test-target-and-routine-release-refresh.md)
  refresh framing is unchanged.

## Deferred

Model-catalog refresh from `GET {base_url}/models`, `/responses` and
`/messages` protocols, an OpenCode Zen record, loopback and local-gateway base
URLs, per-record `response_format` override, persisted probe history beyond
the last result, the inline media-detail model picker, persistent AI drafts
and multi-model draft comparison, and Cover Studio.

## Consequences

Operators can declare an OpenAI-compatible provider, select a declared model,
and verify connectivity and vision behavior from the authenticated
administrator surface without editing code or restarting the service.
Ordinary clients gain no provider administration, no credential access, and no
provider-call path. The color pong is deliberately strict: a model answer that
is not exactly one accepted color token is an honest `mismatch` carrying only
the bounded observed token, and the Cooperator owns the live provider/billing
decision. Non-secret configuration stays reviewable and backup-excluded, and
the schema-v2 writer cannot silently lose or invent the v1 active selection.

## References

- [ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
- [ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md)
- [ADR-0020](0020-on-demand-ai-suggestion-review.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
- [ADR-0036](0036-production-ai-credentials-via-systemd.md)
- [ADR-0044](0044-durable-automatic-post-catalog-analysis.md)
- [ADR-0060](0060-repeatable-immutable-nuc-release-update-contract.md)
- [ADR-0075](0075-nuc-development-test-target-and-routine-release-refresh.md)
- [ADR-0079](0079-administrator-automatic-analysis-runtime-setting.md)
- [SPEC.md](../../SPEC.md) §22
- [SECURITY.md](../../SECURITY.md)
- [SERVER.md](../../SERVER.md)
- [docs/UBUNTU_NUC_DEPLOYMENT.md](../../docs/UBUNTU_NUC_DEPLOYMENT.md)
