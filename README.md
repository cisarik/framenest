# FrameNest

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media, designed around ownership, organization, and a premium visual gallery experience.

## Status

FrameNest is in an early foundation, pre-alpha stage.

There is no functional application, server, package, installer, or supported release yet. This repository currently establishes only the initial safety and documentation foundation.

## Product Vision

FrameNest is intended to help people acquire, organize, browse, and maintain personal video and animated-media libraries while keeping local ownership central.

The current approved product direction includes:

- A visually premium gallery as a flagship experience.
- Media acquisition through replaceable source adapters.
- Local-first catalog ownership, with portable sidecar metadata and local indexes.
- Privacy-aware AI assistance later, after core library behavior and safety boundaries are established.
- Multiple libraries, multiple devices, and one logical media item that may exist in multiple physical locations.
- An optional Intel NUC server aggregator for cross-device library coordination.

## Architectural Direction

The current conceptual direction is:

- A shared web-first UI that can later be hosted by a desktop shell.
- A Tauri desktop shell for local desktop operation.
- Python for domain, filesystem, downloader, metadata, server, and media-processing capabilities.
- PWA or browser access where appropriate.
- Local desktop catalogs plus an optional server aggregator.
- External VLC first for playback, with embedded libVLC considered later.
- Remote access through Tailscale-only networking rather than public internet exposure.

Exact frameworks, packaging choices, IPC design, API framework, data schema, deployment model, and production update mechanisms are still subject to documented architectural decisions. No final frontend framework has been selected.

## Security and Privacy Principles

FrameNest must keep secrets out of Git. Real environment files, API keys, tokens, cookies, private keys, and service credentials must not be committed.

Local desktop operation must not require a server. Remote features are expected to use Tailscale as the network boundary, and backend services must not be exposed publicly by default.

Security decisions should favor least privilege, explicit confirmation for destructive actions, and clear separation between local user data, generated runtime state, and version-controlled source files.

## Development Methodology

FrameNest development follows Analytic Programming and the Coordinator Protocol:

- Inspect before changing.
- Use the repository as the source of truth.
- Keep Worker tasks bounded and evidence-based.
- Make the smallest change that satisfies the authorized task.
- Verify behavior with tests or direct evidence before claiming success.
- Use public commit verification once commits are authorized.

## Development Targets

Initial development and testing targets Apple Silicon macOS.

Later server deployment targets a Fedora KDE environment on an Intel NUC. Broader cross-platform support remains an architectural requirement, but platform details will be refined through documented decisions.

## Documentation Map

The full documentation set will be added in later bounded cycles. Expected future documents include architecture decision records, development workflow guidance, security notes, local runtime layout, testing strategy, and deployment notes.

Current foundation files:

- [`.gitignore`](.gitignore) defines the first repository safety perimeter.
- [`.gitattributes`](.gitattributes) defines cross-platform text and binary handling.
- [`.editorconfig`](.editorconfig) defines baseline editor formatting.
- [`SECURITY.md`](SECURITY.md) defines the initial pre-alpha security policy.
- [`PRODUCT.md`](PRODUCT.md) defines the approved product vision, users, outcomes, experience principles, capabilities, and non-goals.
- [`SPEC.md`](SPEC.md) defines the initial normative product and system requirements.
- [`ROADMAP.md`](ROADMAP.md) defines the staged evidence-based development roadmap.
- [`AGENTS.md`](AGENTS.md) defines FrameNest-specific agent operating rules.
- [`AP.md`](AP.md) defines the general Analytic Programming protocol.
- [`AP_ORCHESTRATOR.md`](AP_ORCHESTRATOR.md) defines the Orchestrator operating handbook.
- [`AP_WORKER.md`](AP_WORKER.md) defines the Worker operating handbook.
- [`BOOT_WORKER.md`](BOOT_WORKER.md) defines the stable FrameNest Worker bootstrap.

## Non-Goals for the Current Stage

The current stage does not provide:

- A complete mobile application.
- Cloud backup.
- A transcoding cluster.
- Embedded libVLC.
- AI-generated covers.
- Public internet exposure.
- A complete application scaffold.

## License

A license has not yet been selected.

Although this repository may be publicly readable, it is not currently offered under an open-source license unless and until a license file is added.

## Contributing

Contribution guidelines are not finalized while the architecture and repository foundation are being established. Public issues and proposals should avoid sensitive information and should stay within the currently documented project scope.
