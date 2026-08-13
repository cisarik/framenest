# ADR-0058: Independent Mullvad Egress and Operator Network Recovery

## Status

`Accepted`

## Decision Date

`2026-08-13`

## Context

FrameNest remote application ingress is already Tailscale-only: authenticated
tailnet HTTPS Serve to a permission-restricted Unix socket, with no public
listener and no Funnel
([ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)). That
ingress path is distinct from public-internet *egress*. Operator workstations
and the Ubuntu NUC still leave the tailnet through ordinary ISP NAT unless an
explicit Mullvad exit node is selected.

The owner operates two Linux members of one tailnet. Direct tailnet and
MagicDNS traffic between those members is overlay traffic and must remain
independent of public egress. The NUC is headless. Installed Tailscale clients
do not expose identical CLI surfaces. A standalone Mullvad daemon may exist on
a workstation without proving that a Mullvad tunnel is active.

This decision records the repository-native operator contract only. Host
mutation, account assignment, and live networking remain separately authorized.

## Decision

`ahw` and `framenest-nuc` select Mullvad exit nodes independently. Each device
uses `tailscale set` with one operator-supplied, verified hostname that ends
exactly in `.mullvad.ts.net`. FrameNest gains no public listener, inbound
exposure, router forwarding, or Funnel change.

### Accepted topology

- Direct tailnet and MagicDNS communication remains overlay traffic.
- Tailscale Serve ingress remains unchanged and tailnet-only.
- Each device chooses its own explicit Mullvad exit node.
- Persisted Tailscale preferences are the reboot-survival mechanism.
- `--exit-node-allow-lan-access=false` is the default on enable.
- Public verification sanitizes IP addresses, tailnet identity, account data,
  and node metadata.
- The privacy goal is Mullvad public egress, not anonymity. Tailscale remains
  identity-aware.

### Rejected topology

- Advertising `ahw` as an exit node.
- Exit-node chaining, including routing the NUC through `ahw`.
- `auto:any`, which may select a non-Mullvad exit node.
- Mandatory exit-node or MDM policy for this owner-operated Linux setup.
- Custom boot units or extra systemd services to reapply exit-node state.
- Firewall, NetworkManager, Wi-Fi, router, manual-route, forwarding, or sysctl
  changes as part of this contract.
- Competing standalone Mullvad routing alongside Tailscale Mullvad egress.
- Public inbound exposure or any change to Serve or Funnel.

### Operator controls

Repository scripts under `scripts/operator/network/` provide `status`,
`enable`, `disable`, `verify`, and `recover`. They never run `tailscale up`,
`tailscale down`, `tailscale login`, or `tailscale logout`; never advertise an
exit node; never configure a Tailscale operator identity; and never invoke
privilege escalation. Feature detection must handle the presence or absence of
`tailscale get` and must not assume identical CLI surfaces.

An explicit verified `*.mullvad.ts.net` node is required. Empty, whitespace,
option-like, non-DNS, and non-Mullvad values are rejected.

### Headless NUC rollback

Before an exit-node mutation on the headless NUC, a separately authorized
operator must arm an automatic transient rollback that clears only the selected
exit node if overlay or operator recovery would otherwise be lost. This ADR
does not install that timer, does not add a persistent boot unit, and does not
grant live NUC mutation. Repository scripts document the requirement and do
not invoke host timers themselves.

Host mutations remain separately authorized. Repository presence grants no
Tailscale account, Mullvad assignment, or host authority.

## Consequences

- Serve ingress and public egress are separately documented and separately
  authorized.
- Operators can recover a selected exit node without changing DNS, routes,
  firewall, or application ingress.
- Reboots should be accepted one device at a time after preferences persist.
- Diagnostic output that cannot establish Mullvad versus non-Mullvad egress
  must report `unknown` rather than guess.
- An active standalone Mullvad daemon without proof of a tunnel is not treated
  as connected; a positively detected competing tunnel blocks mutation.

## Alternatives considered

- Chained egress through `ahw`: rejected; couples the NUC to workstation
  availability and is unsupported exit-node chaining.
- `auto:any`: rejected; may select a non-Mullvad node.
- Advertising the workstation as an exit node: rejected; expands inbound
  routing surface and is not required for independent Mullvad selection.
- Mandatory exit-node policy: rejected for this owner-operated Linux pair.
- Custom boot services: rejected; Tailscale preferences already persist.

## References

- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [OPERATOR_NETWORK.md](../OPERATOR_NETWORK.md)
- [SERVER.md](../../SERVER.md)
- [SECURITY.md](../../SECURITY.md)
- [UBUNTU_NUC_DEPLOYMENT.md](../UBUNTU_NUC_DEPLOYMENT.md)
