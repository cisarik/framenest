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
`deploy/ubuntu/fn-production-env-deploy.fish`. It delegates implementation to
repository support code in the same directory. The helper accepts an explicit
SSH target or non-secret environment default, explicit provider/model values,
and one private local credential source. It supports a non-mutating check mode,
uses SSH BatchMode-compatible command execution, uses only `sudo -n` remotely,
installs deployment-controlled files atomically, restarts and health-checks the
service, and rolls back deployment-controlled files on restart or health
failure after a complete remote backup marker exists. The rollback contract
restores the selected credential, systemd credential drop-in, and non-secret AI
configuration present/absent state, then daemon-reloads, restarts, and
health-checks the restored service. Recovery material is retained when rollback
or cleanup fails. This repository slice does not install the Fish function into
a user configuration directory and does not execute a real NUC deployment.

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
