# ADR-0075: NUC as Development-Test Target and Routine Release Refresh

## Status

`Accepted`

Accepted by the Cooperator on 2026-08-26.

## Decision Date

2026-08-26

## Context

[ADR-0032](0032-ubuntu-nuc-deployment-foundation.md) accepted the Ubuntu NUC as
the "personal production server" target, and the runbook plus
[ADR-0060](0060-repeatable-immutable-nuc-release-update-contract.md) inherited
production-deployment framing: guarded state, per-step ceremony, and
consequence severity appropriate to owner-authoritative production data.

The operating reality has diverged from that framing:

- FrameNest is pre-alpha and is not in actual use by anyone yet; there are no
  real end users of the deployed instance.
- The VPS/public-net deployment direction is frozen (2026-08-25,
  [ADR-0074](0074-dual-audience-public-published-and-tailscale-workspace-boundary.md)
  Deployment-Freeze Annex); no production target other than the desk-side NUC
  exists or is planned for now.
- The NUC runs only FrameNest, sits on the owner's desk, and exists to test
  FrameNest. Its catalog and media state is disposable and reinitializable;
  losing it is acceptable.

The Cooperator therefore directed (2026-08-26) that the NUC be treated as a
FrameNest development-and-testing machine, and that keeping it current be a
routine, frequent operation — informally "push to NUC": after each advance of
public `main`, the NUC should move to that exact SHA, including schema jumps.

## Decision

1. **Role reframing.** The NUC is the FrameNest development-and-testing
   machine. It is not a guarded production server in the current stage.
   Dated production facts (for example the previously accepted release
   `aec2f009…`, schema `0028`) remain history. Loss of NUC state is accepted;
   recovery means reinitialization, not rescue.

2. **Mechanism unchanged.** Routine refreshes go exclusively through the sole
   entry point `deploy/ubuntu/framenest-release`
   (`status`, `check`, `deploy`, `rollback`; ADR-0060). Refreshes always
   target the exact public `main` SHA. Schema jumps use the documented
   `migration-required` continuation:
   - `deploy --yes` stops with exit 13 (`migration-required`) after fully
     preparing and publishing `/opt/framenest/releases/<SHA>`, before cutover;
     the running service is untouched.
   - The catalog backup/restore-readiness discipline stays enforced by the
     tooling (`check` requires `restore_readiness=ready`), because even test
     data deserves cheap insurance.
   - An explicit `framenest-db migrate` runs against the production catalog
     from the newly published release tree under the operator command
     execution contract; the helper itself never migrates
     (runbook section 5 intent).
   - Cutover completes through the `rollback` subcommand's documented path:
     atomic switch to the already-complete release under
     `/opt/framenest/releases/<SHA>`, single restart, bounded readiness
     polling, automatic restore-on-failure.
   - Known editorial debt: runbook section 5 shows
     `--chdir=/opt/framenest/current`, which predates the immutable-release
     flow; for schema jumps the operative form migrates from the newly
     published `/opt/framenest/releases/<SHA>` tree. A deferred editorial
     refactor will reconcile the prose (see Deferred work).

3. **Cadence and standing authority.** Refreshing the NUC after every advance
   of public `main` is normal operation, not an exceptional E3 event. Standing
   Cooperator authorization covers routine refresh runs executed directly by
   the owner or through an owner-maintained workstation wrapper that wraps
   only the four public subcommands plus the documented continuation above.
   Once the owner has interactively prepared SSH agent access, the Orchestrator
   may execute that wrapper on the owner's behalf; remote privileged phases
   still follow the Cooperator sudo-timestamp lifecycle (`sudo -v` outside the
   run, `sudo -K` afterwards). Non-routine host work — initial bootstrap,
   storage, firewall, SSH, Tailscale, credentials, unit changes — continues to
   require its own explicit bounded task.

4. **Unchanged boundaries.** This reframing lowers consequence severity for
   NUC operations; it does not weaken any service-level security boundary:
   - loopback-first service composition; no public listeners;
   - Tailscale-only remote access; no router port-forwarding; Funnel forbidden;
   - `/srv/media` remains read-only to the service;
   - ordinary clients never receive provider secrets;
   - companion `chrome-extension://` origin allowlist rules unchanged;
   - `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED` stays off in tracked files;
     live enablement remains an owner operational decision;
   - Cursor Worker execution boundaries (canonical `./.ap/ap exec` route, NUC
     worker gate, sudo lifecycle) unchanged.

## Relationship and supersession matrix

| ADR | Relation | Statements changed | Statements that remain |
|---|---|---|---|
| [0032](0032-ubuntu-nuc-deployment-foundation.md) | Narrow supersession | The "personal production server" role framing for current operations. | Deployment foundation facts, service contract paths, operator command execution contract. |
| [0060](0060-repeatable-immutable-nuc-release-update-contract.md) | Supplement with framing supersession | Only the production-ceremony interpretation of its use; the four public commands remain exactly the mechanism, including their gates. | The entire helper contract: source/public gates, immutability, same-schema boundary, checkpoint-before-cutover, privilege model, sanitized results. |
| [0074](0074-dual-audience-public-published-and-tailscale-workspace-boundary.md) | Unchanged | Nothing. | The VPS/TLS/public-net deployment freeze stands until explicitly lifted. |

## Consequences

- Living documents progressively shift wording from "production NUC" to the
  development-test framing; the owner acknowledged that many formulations
  across README, SERVER, SECURITY, and the runbook will need rework over time.
- Acceptance banners that cite stale production releases become historical
  context rather than active risk statements.
- Frequent refreshes are safe precisely because ADR-0060's gates stay in
  force: verified backups, hash-verified immutable trees, atomic cutover,
  readiness polling, and automatic rollback.
- No code change is authorized or required by this ADR.

## Deferred work

- Editorial refactor of repository documentation to the new framing
  (README status, SECURITY support status, SERVER NUC role, runbook prose).
- Possible later promotion of the owner workstation wrapper pattern into
  repository tooling as a separately authorized task.
- Runbook section 5 migration-path prose reconciliation noted above.

## References

- [ADR-0032](0032-ubuntu-nuc-deployment-foundation.md)
- [ADR-0052](0052-automated-catalog-backup-retention-and-restore-verification.md)
- [ADR-0060](0060-repeatable-immutable-nuc-release-update-contract.md)
- [ADR-0074](0074-dual-audience-public-published-and-tailscale-workspace-boundary.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
