# ADR-0036: Production AI Credentials via systemd Credentials

## Status

`Accepted`

## Decision Date

2026-07-11

## Context

FrameNest supports server-operated AI provider selection through non-secret
configuration. Development compatibility already allows `NVIDIA_API_KEY` and
`AI_GATEWAY_API_KEY` in the process environment, optionally bootstrapped from
the ignored local `.secrets/ai.env.fish` launcher file.

Production needed a repository-owned path that can later install exactly one
selected provider credential on the Ubuntu NUC without placing the secret in
Git, the non-secret environment file, command-line arguments, browser-visible
state, logs, or provider/model configuration JSON.

## Decision

FrameNest production AI credentials use provider-specific systemd credentials.

The base `framenest.service` remains credential-optional and continues to load
only `/etc/framenest/framenest.env` as non-secret environment configuration.
Optional provider-specific drop-in source material under `deploy/systemd/`
contains only `LoadCredential=` identity/path metadata:

- `NVIDIA_API_KEY:/etc/framenest/credentials/NVIDIA_API_KEY`
- `AI_GATEWAY_API_KEY:/etc/framenest/credentials/AI_GATEWAY_API_KEY`

The application credential resolver preserves existing process-environment
compatibility. If the required environment variable is absent, it reads only the
exact credential name for the selected provider from `CREDENTIALS_DIRECTORY`.
It rejects missing, empty, malformed, oversized, non-regular, symlinked,
non-UTF-8, NUL-containing, and multiline credential input as unavailable
without exposing credential content or source paths. The bounded credential
payload limit is 4096 bytes.

The repository-owned production operator entry point is the Fish script
`deploy/ubuntu/fn-production-env-deploy`. It delegates implementation to
repository support code in the same directory. The helper accepts an explicit
SSH target or non-secret environment default, explicit provider/model values,
and one private local credential source. It supports a non-mutating check mode,
uses SSH BatchMode-compatible command execution, uses only `sudo -n` remotely,
atomically acquires `/run/framenest-ai-credential-deploy`, and fails closed when
retained recovery material already exists. Check mode and deployment both
select only the provider-specific tracked drop-in template under
`deploy/systemd/`, validate its exact two-line `LoadCredential=` contract
locally, and never accept an operator-supplied template path.

After the complete remote backup marker exists, the helper may transmit the
credential over SSH stdin, install deployment-controlled files atomically, and
write non-secret provider/model configuration. The selected credential and the
selected drop-in template use separate stdin payloads. The remote drop-in
installation consumes the exact tracked template bytes, verifies deterministic
byte equivalence before and after atomic rename, and does not reconstruct line
breaks through shell escaping. Before restart, the helper verifies systemd
acceptance, daemon-reloads, confirms `framenest.service` remains enabled,
confirms systemd loaded the intended drop-in and credential identity, and only
then restarts `framenest.service`. After bounded readiness succeeds, it checks
only the same loopback, provider-free capability endpoint used by the web
status modal and requires the selected provider/model to be configured,
available, and not connection-tested. Deployment terminal service failure,
readiness timeout, systemd acceptance failure, byte-equivalence failure, and
capability mismatch all roll back deployment-controlled files. The rollback
contract restores the selected credential, systemd credential drop-in, and
non-secret AI configuration present/absent state, then daemon-reloads, restarts,
and uses the same bounded readiness contract on the restored service. Recovery
material is retained when rollback terminal failure, rollback readiness
timeout, rollback restore/restart failure, or cleanup failure occurs. This
repository slice does not install the Fish function into a user configuration
directory and does not execute a real NUC deployment.

Non-secret provider/model selection continues through the existing
`framenest-ai configure` boundary, extended only with explicit non-interactive
provider/model arguments.

## Consequences

- Production credentials remain outside the non-secret environment file and AI
  configuration JSON.
- An unconfigured service still starts and reports `not_configured`.
- A selected provider without a usable credential reports
  `credential_unavailable`.
- Development environment variables and the ignored local Fish secret file
  remain compatible.
- The helper and templates are repository source material only until a later
  task grants explicit real-host authority.

## Rejected Alternatives

- Store provider keys in `/etc/framenest/framenest.env`: rejected because the
  environment file is explicitly non-secret.
- Store provider keys in `/var/lib/framenest/ai/config.json`: rejected because
  the AI configuration boundary is non-secret provider/model state only.
- Put secrets in unit `Environment=` directives or command-line arguments:
  rejected because those surfaces are too easy to disclose through service
  inspection, logs, or process listings.
- Require TPM-backed encrypted systemd credentials now: rejected because this
  slice needs to work without assuming TPM availability.
