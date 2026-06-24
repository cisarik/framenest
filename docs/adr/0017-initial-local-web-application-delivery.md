# ADR-0017: Initial Local Web Application Delivery

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this first local web-application delivery foundation through bounded task `FRAMENEST-CYCLE-054-LOCAL-WEB-APPLICATION-FOUNDATION`.

## Context

FrameNest already has a FastAPI application factory, typed `GET /health`, loopback-first Uvicorn runtime, structured logging, SQLite persistence foundation, device and library registries, read-only scan preview, deterministic local media-analysis preparation, and a provider-neutral media suggestion preview.

The next useful product-visible step is not a complete gallery or desktop shell. It is a packaged local application surface that proves the existing loopback FastAPI process can serve an honest, installable, same-origin web shell without adding frontend tooling, cloud dependencies, CORS, provider exposure, or unimplemented product behavior.

Related documents:

- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0008](0008-asgi-runtime.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

The existing FastAPI process serves the initial local FrameNest web application.

The first UI uses packaged vanilla HTML, CSS, and JavaScript. No React, Vue, Svelte, Vite, npm, Node build system, CDN, external frontend package manager, or generated top-level frontend scaffold is introduced by this decision.

Application assets live inside the `framenest` Python package and must be available from an installed wheel. `GET /` serves the application entry document. A same-origin asset route serves the CSS and JavaScript resources. Unknown asset paths return ordinary `404` responses rather than the application document.

Browser code calls the existing same-origin `GET /health` endpoint and renders loading, healthy, and error states based only on that response. The health contract remains `{"status": "ok"}` and is not changed for the UI.

No CORS middleware is introduced for the loopback-only initial application. The server binding remains governed by the existing loopback-first runtime settings.

The shell must not use external fonts, scripts, stylesheets, analytics, telemetry, images, or runtime internet calls. It must not expose provider credentials, environment values, absolute media paths, the SQLite database path, secret references, or local machine-specific paths to browser code.

Provider calls and provider credentials remain server-side. This decision does not add AI endpoints, gallery APIs, library listing APIs, Settings endpoints, authentication, Tailscale integration, media persistence, downloads, playback, or storage-volume registration.

The initial shell must be visually premium, dark, responsive, accessible, and honest about pre-alpha status. It may identify future areas such as Gallery, Libraries, Downloads, and Settings only when clearly marked as future or unavailable. It must not pretend those workflows are implemented.

This decision does not determine the final desktop or Tauri packaging architecture. A later product need may supersede this decision with a compiled frontend toolchain, separate workspace, or desktop packaging approach after explicit evidence and approval.

## Rationale

Serving the first shell from the existing FastAPI process is the smallest coherent step from the current foundation to a visible local application. It proves package-resource delivery, same-origin health integration, and browser availability while preserving loopback-only safety and avoiding a premature frontend ecosystem.

Vanilla packaged assets are sufficient for this pre-alpha shell because there is no real gallery data, large interactive state model, routing tree, or component system yet. Avoiding Node tooling keeps the implementation aligned with the current Python package boundary and prevents an empty top-level web scaffold from becoming a false architecture decision.

Same-origin delivery avoids CORS complexity and keeps future browser-server contracts inside the existing local runtime boundary.

## Consequences

### Positive

- FrameNest has a locally runnable, packaged web shell at the default server URL.
- The browser can verify the real local application process through `/health`.
- Wheel installation includes the entry document and assets.
- The current loopback and secret boundaries remain intact.
- Future UI work has a concrete but deliberately small starting point.

### Negative / limitations

- Vanilla assets provide no component framework, build pipeline, bundling, or static analysis beyond ordinary tests.
- Browser behavior remains intentionally simple.
- The shell is not a real media gallery and contains no catalog-backed data.
- Future richer UI work may require a new ADR and migration to a compiled frontend toolchain.

## Security Boundaries

- No public bind address is introduced.
- No CORS middleware is introduced.
- No external runtime URL is called or embedded.
- No telemetry, analytics, remote fonts, or CDN assets are used.
- No provider credential or secret setting is sent to browser code.
- No absolute database path, media path, repository path, environment value, or machine-specific path is exposed.

## Rejected Scope

React, Vue, Svelte, Vite, Tailwind, npm, Node package files, Tauri, desktop packaging, authentication, CORS, gallery data, media catalog persistence, library browsing APIs, downloads, playback, Settings, AI endpoints, provider calls, telemetry, screenshots, and generated visual evidence are out of scope for this decision.

## Verification Expectations

Implementation must demonstrate:

- `GET /` returns an HTML FrameNest document with a semantic main region and honest pre-alpha indication;
- CSS and JavaScript assets are served from same-origin local routes;
- unknown asset paths return `404`;
- `/health` keeps its exact response contract;
- root and asset responses do not add wildcard CORS headers;
- JavaScript references same-origin `/health` and distinct loading, healthy, and error states;
- application assets contain no external runtime URLs;
- representative secret values, environment names, absolute database paths, and machine-specific paths are absent from application responses;
- resources are available through Python package resources;
- built wheel contents include `index.html`, `styles.css`, and `app.js`.

## Revisit Triggers

Revisit this decision when real gallery data, multi-view application routing, desktop shell integration, build-time asset processing, shared frontend components, offline caching, accessibility tooling, or product complexity justifies a compiled frontend toolchain or separate web workspace.

## Related Documents

- [ADR index](README.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0008](0008-asgi-runtime.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
