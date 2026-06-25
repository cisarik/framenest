# ADR-0021: Tauri Desktop Shell

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Cooperator accepted the desktop direction through task
`FRAMENEST-CYCLE-061-DESKTOP-DISTRIBUTED-MEDIA-ARCHITECTURE-AND-WORKER-CLOSEOUT`.

## Context

FrameNest is a local-first media library whose flagship user experience is a
premium gallery. The repository currently has a Python/FastAPI loopback server,
packaged HTML/CSS/JavaScript web assets, local device and library registries,
read-only scan and media-analysis previews, and an explicit editable AI
suggestion review. It does not yet have a persistent media catalog, durable
gallery data, desktop shell, installer, native Settings view, or production
deployment.

The existing packaged browser UI is useful as a development and diagnostic
surface, but the normal end-user product must become a native desktop
application. Ordinary users should not need to manually open Chrome, Brave,
Firefox, Safari, or another external browser to use FrameNest.

Tauri v2 is a documented toolkit for building desktop applications from HTML,
CSS, and JavaScript rendered in a system WebView with native integration through
Rust and controlled APIs. Its official documentation covers the architecture and
WebView model, system tray, native menus, single-instance plugin, sidecars or
external binaries, and the capabilities/permissions security model.

## Decision

FrameNest accepts **Tauri v2** as the future desktop shell.

The Tauri shell will display the existing FrameNest HTML/CSS/JavaScript UI in a
native system WebView. The current packaged web UI remains reusable and should
evolve toward the desktop shell rather than being discarded merely because it is
currently served in browser mode.

The Python/FastAPI backend remains the application backend and domain/application
adapter host. Tauri is a native shell and native-capability boundary. It must
not duplicate FrameNest domain logic, catalog logic, provider logic, media
analysis policy, or persistence rules.

The future desktop lifecycle conceptually includes:

1. enforce a single application instance;
2. resolve application-owned runtime directories;
3. launch the packaged Python/FastAPI sidecar;
4. establish a bounded local bootstrap and health handshake;
5. open the main WebView only when the backend is ready;
6. supervise unexpected backend termination;
7. stop the backend cleanly during explicit application quit.

The supervised backend must remain loopback-only by default. An ephemeral port
and per-launch authorization or bootstrap mechanism are preferred directions,
but the exact IPC, port discovery, authentication, Python bundling, signing,
update, and installer choices remain deferred to later bounded decisions.

FrameNest desktop must use a single-instance lifecycle. A second launch should
focus or restore the existing application rather than creating an independent
backend and second catalog-facing UI.

The desktop shell must provide a system tray or macOS menu-bar presence. The
initial menu items are:

- `Gallery`;
- `Settings`;
- `Quit`.

`Gallery` restores or focuses the main gallery window. `Settings` opens the
future settings view when that view exists. `Quit` performs explicit application
shutdown and stops the supervised backend. Closing the main window normally
hides the window rather than treating close as application termination.

Browser mode remains a supported development and diagnostic mode. It should
continue to expose the loopback FastAPI application for tests, debugging, and
operator workflows, but it is not the normal end-user desktop experience.

Initial implementation and product validation are MacBook-first. Cross-platform
compatibility remains a product and architecture requirement, and platform
adapters must avoid macOS-only assumptions in domain logic, but simultaneous
Windows and Linux shell completion is not the immediate critical path.

The future Tauri shell may provide narrowly scoped native capabilities for:

- file selection;
- directory selection;
- save or export destinations;
- downloading to an approved destination;
- revealing a file in Finder, Explorer, or the equivalent file manager;
- opening media through VLC;
- clipboard operations;
- native notifications;
- single-instance handling;
- application lifecycle and tray/menu behavior.

The WebView must not receive unrestricted filesystem, shell, process, or
arbitrary-command access. Every native command must use explicit allowlisted
capabilities, permissions, and path scopes. Browser development mode may degrade
gracefully when a native-only capability is unavailable.

## Why Not Implement The Shell Now

The desktop shell is accepted direction, not the next implementation slice.

FrameNest still lacks durable gallery data, a persistent media catalog, logical
media and physical-location persistence, cover and thumbnail persistence, title
and tag search, and native Settings. Implementing Tauri before these foundations
would create packaging and lifecycle complexity around a UI that cannot yet
present the product's flagship gallery. The strongest next implementation
candidate remains the minimum persistent local media catalog on MacBook.

## Security Consequences

The Tauri shell increases native power and therefore increases security
obligation. The shell must be least-privilege by default.

The WebView may request only narrowly scoped commands. File and directory
selection must return approved paths through explicit user action. Shell/process
access must not become a generic command execution bridge. Provider secrets must
remain outside ordinary WebView state. Runtime bootstrap credentials must not be
persisted in browser storage or exposed to the UI as user-readable values.

The sidecar must bind only to loopback by default. Future remote access remains
Tailscale-only unless superseded by a later approved decision. Network identity
alone is not sufficient authorization.

## Deferred Decisions

This ADR does not decide:

- exact Tauri project layout;
- Rust module structure;
- JavaScript package manager or frontend build system;
- whether or when a compiled frontend toolchain is introduced;
- Python sidecar bundling or freezer;
- sidecar binary naming or resource placement;
- sidecar IPC beyond loopback HTTP;
- port discovery;
- bootstrap authorization mechanism;
- native secret-store implementation;
- code signing, notarization, installers, and update flow;
- tray icon assets;
- Settings UI structure;
- crash reporting;
- platform-specific menu conventions;
- Windows and Linux packaging details.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, maintainers, desktop
implementers, packaging implementers, and security reviewers.

Retention: retained permanently; superseded only by a later accepted ADR.

Inbound links: ADR index, [DESKTOP.md](../../DESKTOP.md),
[PRODUCT.md](../../PRODUCT.md), [SPEC.md](../../SPEC.md),
[ROADMAP.md](../../ROADMAP.md), and [README.md](../../README.md).

Cleanup owner: future explicitly authorized Worker only through a superseding
ADR.

## Official Tauri v2 References

- Architecture and WebView model:
  <https://v2.tauri.app/concept/architecture/>
- System tray:
  <https://v2.tauri.app/learn/system-tray/>
- Native menus:
  <https://v2.tauri.app/learn/window-menu/>
- Single-instance plugin:
  <https://v2.tauri.app/plugin/single-instance/>
- Sidecars and external binaries:
  <https://v2.tauri.app/develop/sidecar/>
- Capabilities:
  <https://v2.tauri.app/security/capabilities/>
- Permissions:
  <https://v2.tauri.app/security/permissions/>
- Configuration files:
  <https://v2.tauri.app/develop/configuration-files/>

## Related Documents

- [ADR index](README.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0017](0017-initial-local-web-application-delivery.md)
- [ADR-0022](0022-selective-media-placement-and-server-aggregation.md)
- [DESKTOP.md](../../DESKTOP.md)
- [SERVER.md](../../SERVER.md)
- [GALLERY.md](../../GALLERY.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
