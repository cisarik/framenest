# ASGI Runtime Evidence

## 1. Document status

| Field | Value |
|---|---|
| Document type | Evidence package only — **not** an accepted architecture decision |
| Research date | 2026-06-24 |
| Repository start HEAD | `ee04aa649eb77d72e46166c00da38b09636bb465` |
| Implementation status | **Unauthorized.** No ASGI runtime is installed, wired, or selected by this document. |
| ADR status | No ADR created or modified by this task |
| **Classification** | Temporary committed decision evidence |
| **Authority** | Non-authoritative |
| **Intended consumer** | The future Accepted ADR selecting the FrameNest ASGI runtime |
| **Discoverability** | Linked from [docs/adr/README.md](adr/README.md) while the decision remains open |
| **Retention trigger** | Delete after material conclusions and relevant primary-source references are transferred into the Accepted ASGI runtime ADR |
| **Cleanup timing** | Deletion and inbound-link removal MUST occur in the same bounded ADR-acceptance task |
| **Cleanup owner** | An Orchestrator-authorized Worker |
| **Historical preservation** | Git history remains the archive |

This file collects primary-source research to support a future Cooperator decision and a separate bounded ADR task. Provisional analysis appears only in sections explicitly marked **Worker analysis**.

---

## 2. FrameNest constraints

The following constraints are drawn from accepted ADRs, product documents, and the current repository state verified at the research date.

### Verified repository and architecture context

- **FastAPI adapter exists.** `create_app()` in `src/framenest/adapters/api/application.py` returns a `FastAPI` instance, supports injected `FrameNestSettings`, and exposes `GET /health` returning `{"status": "ok"}`. The factory is testable in-process without a network listener.
- **CPython 3.13** is the accepted supported runtime ([ADR-0001](adr/0001-supported-python-version.md)).
- **Poetry** is the dependency and lockfile authority ([ADR-0002](adr/0002-python-environment-and-dependency-manager.md)).
- **FastAPI** is the accepted HTTP API adapter; domain and application layers must not import FastAPI ([ADR-0003](adr/0003-initial-server-api-framework.md)).
- **Configuration** uses centralized `load_settings()` with default host `127.0.0.1` ([ADR-0005](adr/0005-configuration-strategy.md), [ADR-0007](adr/0007-settings-library.md)).
- **Repository layout** places ASGI serving outside `domain/` and inside adapter/infrastructure boundaries ([ADR-0004](adr/0004-repository-layout.md)).

### Product and deployment constraints (from SPEC and ROADMAP)

- **Localhost-first:** initial server must be configurable for loopback-only binding and must not be publicly exposed by default ([SPEC.md](../SPEC.md)).
- **macOS Apple Silicon** is the initial development platform; **Fedora KDE on Intel NUC** is the later server target ([ROADMAP.md](../ROADMAP.md)).
- **Tailscale-only** remote direction; application backend should bind to loopback when exposed through Tailscale Serve ([SPEC.md](../SPEC.md)).
- **Small-team proportional complexity:** first server skeleton should remain minimal; ASGI runner remains an explicit non-decision in ADR-0003 and ADR-0004.
- **Application factory testability** must be preserved: contract tests already run without binding sockets.

### Hard evaluation constraints for this evidence package

- Compare only bounded candidates with primary-source support.
- Do not treat GitHub stars, blog benchmarks, or third-party comparisons as decision evidence.
- Do not install or run any ASGI server in this task.

---

## 3. Verified candidate facts

Retrieval date for all primary sources below: **2026-06-24**.

### 3.1 Uvicorn

**Primary sources consulted**

- PyPI metadata: https://pypi.org/project/uvicorn/ (JSON API version `0.49.0`, uploaded 2026-06-03)
- README: https://raw.githubusercontent.com/encode/uvicorn/master/README.md
- Settings reference: https://www.uvicorn.dev/settings/ (mirrors repository `docs/settings.md`)
- Deployment guide: https://raw.githubusercontent.com/encode/uvicorn/master/docs/deployment/index.md
- Server behavior: https://raw.githubusercontent.com/encode/uvicorn/master/docs/server-behavior.md
- Source configuration defaults: https://raw.githubusercontent.com/encode/uvicorn/master/uvicorn/config.py
- GitHub repository activity: https://api.github.com/repos/Kludex/uvicorn (`pushed_at` 2026-06-22)

**Verified facts**

| Topic | Fact |
|---|---|
| Project status | Active ASGI web server maintained under `Kludex/uvicorn`; PyPI classifiers include CPython 3.13 and 3.14 |
| Latest stable release | **0.49.0** (PyPI upload 2026-06-03) |
| Python requirement | `>=3.10` (PyPI classifiers list 3.10–3.14) |
| Package form | Pure-Python wheel `uvicorn-0.49.0-py3-none-any.whl`; optional `[standard]` extra adds Cython-based `uvloop`/`httptools`, `watchfiles`, and related packages (README) |
| ASGI support | ASGI server; supports HTTP/1.1 and WebSockets (README) |
| Lifespan | Configurable via `--lifespan` / `lifespan=` with options `auto`, `on`, `off`; default `auto` (settings docs; `uvicorn/config.py`) |
| Default bind host | **`127.0.0.1`** (settings docs; `host: str = "127.0.0.1"` in `uvicorn/config.py`) |
| Default port | `8000` (settings docs) |
| CLI startup | `uvicorn module:app` (README) |
| Application factory | `--factory` treats target as `() -> ASGI app` callable (settings docs) |
| Programmatic startup | `uvicorn.run(...)` with same options as CLI (deployment docs) |
| Reload | `--reload` for development; requires `watchfiles` for advanced include/exclude behavior; mutually exclusive with `--workers` (settings docs) |
| Worker model | Built-in `--workers` uses multiprocessing `spawn`; monitors and restarts child processes (deployment docs) |
| Graceful shutdown | Deployment docs describe signal-based child-process management for multi-worker mode; server-behavior docs document connection and timeout semantics |
| Logging | `--log-config`, `--log-level`, access log controls; JSON/YAML config supported with optional deps (settings docs) |
| Proxy / forwarded headers | `--proxy-headers` enabled by default; trusts connecting IPs in `forwarded-allow-ips` (default `127.0.0.1`, overridable; literal `*` trusts all) (settings docs; `uvicorn/config.py` loads `ProxyHeadersMiddleware`) |
| HTTP/2 | Not listed among Uvicorn’s native protocol implementations; HTTP options are `auto`, `h11`, `httptools` (settings docs) |
| FastAPI relationship | FastAPI manual lists Uvicorn as the default ASGI server and documents `pip install "uvicorn[standard]"` (https://fastapi.tiangolo.com/deployment/manually/#asgi-servers) |
| macOS / Linux practicality | Pure-Python base install; optional native wheels via `[standard]` extras (`uvloop`, `httptools`) where platform supports them (README) |

**Worker analysis**

- Uvicorn’s default loopback host aligns directly with FrameNest’s accepted configuration default without requiring a separate bind policy in the first runtime wiring task.
- Built-in proxy-header handling with a conservative default trusted list is materially relevant to a future Tailscale Serve reverse-proxy topology, provided `forwarded-allow-ips` is configured explicitly for the proxy path rather than left at defaults in production.

---

### 3.2 Hypercorn

**Primary sources consulted**

- PyPI metadata: https://pypi.org/project/hypercorn/ (JSON API version `0.18.0`, uploaded 2025-11-08)
- README: https://raw.githubusercontent.com/pgjones/hypercorn/main/README.rst
- Configuration reference: https://raw.githubusercontent.com/pgjones/hypercorn/main/docs/how_to_guides/configuring.rst
- API usage: https://raw.githubusercontent.com/pgjones/hypercorn/main/docs/how_to_guides/api_usage.rst
- Default bind in source: https://raw.githubusercontent.com/pgjones/hypercorn/main/src/hypercorn/config.py
- GitHub repository activity: https://api.github.com/repos/pgjones/hypercorn (`pushed_at` 2025-11-08)

**Verified facts**

| Topic | Fact |
|---|---|
| Project status | ASGI and WSGI server by pgjones; PyPI classifiers include CPython 3.13 and 3.14 |
| Latest stable release | **0.18.0** (PyPI upload 2025-11-08) |
| Python requirement | `>=3.10` (PyPI classifiers list 3.10–3.14) |
| Package form | Python package on PyPI; optional extras include `uvloop`, `trio`, and `h3` (README) |
| ASGI support | ASGI and WSGI; inspired by Gunicorn (README) |
| HTTP protocols | HTTP/1, HTTP/2, WebSockets; optional HTTP/3 draft via `hypercorn[h3]` and `--quic-bind` (README) |
| Lifespan | Configurable startup/shutdown timeouts default **60s** each (`startup_timeout`, `shutdown_timeout` in configuring docs) |
| Default bind | **`127.0.0.1:8000`** (`_bind = ["127.0.0.1:8000"]` in `hypercorn/config.py`; configuring docs show `bind` examples including `127.0.0.1:5000`) |
| CLI startup | `hypercorn module:app` (README) |
| Programmatic startup | `asyncio.run(serve(app, Config()))`; separate asyncio, trio, and uvloop paths (API usage docs) |
| Reload | `use_reloader` / `--reload` documented in configuring reference |
| Worker model | CLI supports `workers` (default 1) and `worker_class` (`asyncio`, `uvloop`, `trio`); programmatic `serve()` docs state worker-class and worker-count options **do not apply** when using `serve()` directly |
| Graceful shutdown | `serve()` accepts `shutdown_trigger`; docs include SIGTERM example and option to disable signal handling (API usage docs); `graceful_timeout` default **3s** for remaining requests after SIGTERM/Ctrl-C (configuring docs) |
| Logging | `logconfig`, `logconfig_dict`, `accesslog`, `errorlog`, `loglevel` options (configuring docs) |
| Proxy / forwarded headers | **No server-level proxy-header or forwarded-header configuration** found in Hypercorn configuring reference or `hypercorn/config.py` during this research |
| Event-loop options | asyncio, uvloop, trio worker types (README, configuring docs) |
| macOS / Linux practicality | Pure Python package; optional `uvloop`/`trio` extras; no Rust binary wheel requirement |

**Worker analysis**

- Hypercorn’s HTTP/2 and trio support are genuine differentiators, but FrameNest’s initial health-only API does not currently require HTTP/2.
- Absence of documented server-level forwarded-header handling means Tailscale Serve proxy semantics would likely require explicit application-layer middleware or external proxy configuration, increasing review surface compared with Uvicorn’s built-in option.

---

### 3.3 Granian

**Primary sources consulted**

- PyPI metadata: https://pypi.org/project/granian/ (JSON API version `2.7.7`, uploaded 2026-06-23)
- README: https://raw.githubusercontent.com/emmett-framework/granian/master/README.md
- GitHub repository activity: https://api.github.com/repos/emmett-framework/granian (`pushed_at` 2026-06-23)
- PyPI wheel inventory for `2.7.7` (cp313 platform wheels)

**Verified facts**

| Topic | Fact |
|---|---|
| Project status | Described as “Rust HTTP server for Python applications”; actively maintained per README “Project status” section |
| Latest stable release | **2.7.7** (PyPI upload 2026-06-23) |
| Python requirement | `>=3.10` (PyPI classifiers list 3.10–3.14 and free-threading beta for 3.13) |
| Package form | **Prebuilt platform wheels** including `cp313` wheels for `macosx_11_0_arm64`, `manylinux_2_17_x86_64`, `manylinux_2_28_aarch64`, and musllinux variants (PyPI `2.7.7` file list) |
| ASGI support | Supports ASGI/3, RSGI, and WSGI interfaces (README) |
| HTTP protocols | HTTP/1 and HTTP/2; HTTPS and mTLS; WebSockets (README) |
| Default bind host | **`127.0.0.1`** (`--host` default documented in README CLI help excerpt) |
| Default port | `8000` (README CLI help excerpt) |
| CLI startup | `granian --interface asgi module:app` (README) |
| Application factory | `--factory` / `GRANIAN_FACTORY` documented in README CLI help excerpt |
| Programmatic startup | `Granian(...).serve()` documented; embeddable `granian.server.embed.Server` marked **experimental** (README) |
| Reload | `--reload` requires `granian[reload]` extra (README) |
| Worker model | Multi-process workers with separate Rust runtime threads and Python blocking threads; architecture explicitly differs from Gunicorn/Uvicorn (README “Workers and threads”) |
| Logging | Uses Python standard-library `logging`; `_granian` and `granian.access` loggers; JSON log config supported (README) |
| Proxy / forwarded headers | **No built-in server option**; README states protocols do not define proxy forwarded-header strategy and provides `granian.utils.proxies` wrappers (`wrap_asgi_with_proxy_headers`) with `trusted_hosts` default **`127.0.0.1`** |
| Native/binary implications | Rust-based server distributed as platform-specific wheels; README positions project as alternative to “Gunicorn + uvicorn + http-tools” composition |
| macOS Apple Silicon | `cp313-cp313-macosx_11_0_arm64.whl` published for 2.7.7 |
| Fedora / Intel NUC practicality | `cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` published for 2.7.7 |
| FastAPI relationship | Listed as an ASGI server option in FastAPI manual alongside Uvicorn and Hypercorn (FastAPI deployment docs) |
| Maintenance statement | README states bug/security fixes are “usually provided for the latest minor version only” |

**Worker analysis**

- Granian’s wheel-based distribution is practical on current FrameNest targets but introduces **platform wheel availability** as an operational dependency that pure-Python Uvicorn does not share at base install.
- README explicitly warns against tuning workers/threads using guidance meant for Uvicorn/Gunicorn, implying additional operational learning cost for a small team.
- README performance claims link to repository benchmarks; those figures are **not** used as decision evidence in this package.

---

## 4. Comparison matrix

Legend: **Yes** / **No** / **Partial** / **Unknown** / factual value.

| Criterion | Uvicorn 0.49.0 | Hypercorn 0.18.0 | Granian 2.7.7 |
|---|---|---|---|
| Official project/package active | Yes (PyPI 2026-06-03; GitHub push 2026-06-22) | Yes (PyPI/GitHub push 2025-11-08) | Yes (PyPI 2026-06-23; GitHub push 2026-06-23) |
| Declared Python 3.13 support | Yes (PyPI classifiers) | Yes (PyPI classifiers) | Yes (PyPI classifiers; cp313 wheels) |
| macOS Apple Silicon practicality | Yes (pure-Python base; optional native extras) | Yes (pure Python; optional uvloop) | Yes (`macosx_11_0_arm64` cp313 wheel) |
| Fedora x86_64 practicality | Yes (pure-Python base) | Yes (pure Python) | Yes (`manylinux_2_17_x86_64` cp313 wheel) |
| ASGI support | Yes | Yes | Yes (ASGI/3) |
| ASGI lifespan support | Yes (`auto`/`on`/`off`) | Yes (startup/shutdown timeouts documented) | Partial (Granian lifecycle hooks; embed server experimental) |
| HTTP/1 for initial local API | Yes | Yes | Yes |
| HTTP/2 | No (not native in Uvicorn settings) | Yes | Yes |
| WebSockets | Yes | Yes | Yes |
| CLI startup | Yes | Yes | Yes |
| Programmatic startup | Yes (`uvicorn.run`, `Config`) | Yes (`serve(app, Config())`) | Yes (`Granian.serve()`; embed API experimental) |
| Application factory flag | Yes (`--factory`) | Unknown (not found in consulted Hypercorn docs) | Yes (`--factory`) |
| Development reload | Yes (`--reload`; watchfiles for advanced mode) | Yes (`--reload`) | Yes (`--reload`; requires `granian[reload]`) |
| Multi-worker process model | Yes (`--workers`, spawn-based) | Yes (CLI workers; not via programmatic `serve()`) | Yes (`--workers`; distinct architecture) |
| Graceful shutdown | Yes (documented signal/process behavior) | Yes (`shutdown_trigger`, `graceful_timeout`) | Partial (hooks/`stop()` documented; less systemd-oriented documentation) |
| Structured logging integration | Yes (logging config files/levels) | Yes (logging config/access/error logs) | Yes (stdlib `logging`, JSON config) |
| Server-level proxy/trusted forwarded headers | Yes (`proxy_headers`, `forwarded-allow-ips`) | No (not found in primary docs/source) | No (application wrappers in `granian.utils.proxies`) |
| Default bind host | `127.0.0.1` | `127.0.0.1:8000` | `127.0.0.1` |
| Safe loopback-only default | Yes | Yes | Yes |
| systemd suitability (later) | Partial (common pattern; not systemd-specific) | Partial (signal hooks documented) | Partial (PID file option; less common examples) |
| Base install dependency weight | Low (pure Python) | Low–Moderate (pure Python) | Moderate (Rust binary wheels) |
| Native/binary wheel implications | Optional via `[standard]` | Optional via extras | **Required** (platform wheels) |
| FastAPI documented first-class path | Yes (default server) | Yes (listed alternative) | Yes (listed alternative) |
| Existing `create_app()` compatibility | Yes (ASGI callable) | Yes | Yes (`--interface asgi`; factory supported) |
| Poetry direct runtime dependency | `uvicorn` (+ optional extras group choice) | `hypercorn` (+ optional extras) | `granian` (+ optional extras such as `reload`) |

---

## 5. Operational and security analysis

### Local development

| Topic | Uvicorn | Hypercorn | Granian |
|---|---|---|---|
| Loopback dev server | Defaults to `127.0.0.1`; matches FrameNest settings default | Defaults to `127.0.0.1:8000` | Defaults to `127.0.0.1` |
| Reload ergonomics | Mature `--reload`; watchfiles optional for finer control | `--reload` documented | `--reload` requires extra dependency |
| Debug complexity | Low; widely documented with FastAPI | Moderate; additional worker/event-loop choices | Moderate–High; Rust/Python hybrid tuning |

**Worker analysis:** For a single-developer localhost-first workflow, Uvicorn presents the lowest documentation and tooling friction with FastAPI.

### Future systemd execution

**Verified facts**

- None of the three candidates ship FrameNest-specific systemd units in this repository or in the consulted primary docs.
- Hypercorn documents SIGTERM-driven graceful shutdown via `shutdown_trigger`.
- Uvicorn documents multi-worker signal management for child processes.
- Granian documents `--pid-file` and lifecycle hooks.

**Worker analysis**

- All three can be wrapped by a future systemd service unit that executes a Poetry-managed CLI or module entrypoint.
- Uvicorn and Hypercorn have more published examples in the broader ASGI ecosystem for small single-service deployments; Granian is increasingly adopted but operational guidance is less uniform in primary FrameNest sources.

### Loopback binding

**Verified facts**

- All three candidates default to loopback-oriented bind values in primary documentation or source defaults.
- FrameNest settings already default host to `127.0.0.1`; runtime wiring must not substitute `0.0.0.0` silently ([ADR-0005](adr/0005-configuration-strategy.md), [SPEC.md](../SPEC.md)).

**Worker analysis**

- Runtime selection should require explicit mapping from `FrameNestSettings.host` to server bind arguments; the candidate choice does not remove that obligation.

### Proxy / trusted-header risks

**Verified facts**

- Uvicorn enables proxy headers by default but restricts trusted sources to `forwarded-allow-ips` (default `127.0.0.1`; `*` trusts all).
- Granian requires explicit `granian.utils.proxies` wrappers for forwarded-header semantics; `trusted_hosts="*"` disables the security check (README).
- Hypercorn lacks documented server-level forwarded-header handling in consulted sources.

**Worker analysis**

- For Tailscale Serve, trusting forwarded headers incorrectly is a security-sensitive failure mode. Uvicorn provides the most direct server-level knob; Granian and Hypercorn shift responsibility to explicit wrapper/middleware design and operations review.

### Shutdown behavior

**Verified facts**

- Hypercorn documents graceful shutdown triggers and `graceful_timeout` (default 3s).
- Uvicorn documents worker supervision and connection timeout behavior.
- Granian documents `on_shutdown` hooks and `stop()` for embed mode.

**Worker analysis**

- For a small localhost service, all three are sufficient if shutdown semantics are tested in the implementation task; Hypercorn’s explicit `shutdown_trigger` API is the most visibly documented programmatic pattern.

### Package and native-code risk

| Candidate | Risk profile |
|---|---|
| Uvicorn | Lowest base risk: pure-Python wheel. Optional `[standard]` introduces native components (`uvloop`, `httptools`) that may affect wheel availability on uncommon platforms. |
| Hypercorn | Low base risk: pure Python; optional extras add complexity but not mandatory native wheels. |
| Granian | Higher operational risk: mandatory platform wheels; future Python/platform combinations depend on Granian release cadence (“latest minor only” security-fix policy per README). |

---

## 6. Dependency impact

No dependencies were installed in this task. The following reflects expected Poetry impact for a future implementation task.

### Uvicorn

| Item | Expected impact |
|---|---|
| Direct Poetry dependency | `uvicorn` under runtime dependencies |
| Typical extras | `standard` optional extra for `uvloop`, `httptools`, `watchfiles`, etc. (README) |
| Transitive/native | Base install remains pure Python; extras may pull native wheels |
| FastAPI interaction | FastAPI already depends on Starlette; Uvicorn adds separate runtime package |

### Hypercorn

| Item | Expected impact |
|---|---|
| Direct Poetry dependency | `hypercorn` runtime |
| Typical extras | `uvloop`, `trio`, `h3` optional extras (README) |
| Transitive/native | Primarily Python libraries (`h11`, `h2`, `wsproto` per README); optional extras may add more |

### Granian

| Item | Expected impact |
|---|---|
| Direct Poetry dependency | `granian` runtime |
| Typical extras | `reload`, `dotenv`, `pname`, `uvloop`, etc. (README) |
| Transitive/native | Rust extension wheels per platform; `reload` extra adds file-watching dependency chain |

**Worker analysis**

- For Poetry lock hygiene, Uvicorn’s optional `[standard]` extra should be a deliberate ADR follow-on choice rather than an unreviewed default.
- Granian introduces the strongest wheel-platform coupling for macOS arm64 and Fedora x86_64 targets.

---

## 7. Provisional recommendation

> **This is Worker analysis, not project authority.**

| Item | Recommendation |
|---|---|
| Recommended candidate | **Uvicorn** |
| Strongest alternative | **Hypercorn** |
| Confidence | **Medium-high** |

### Rationale (concise)

1. **FastAPI alignment:** FastAPI documents Uvicorn as the default ASGI server and the ordinary manual-install path.
2. **Loopback defaults:** Uvicorn’s default host `127.0.0.1` matches accepted FrameNest configuration policy without introducing a conflicting default.
3. **Proxy-header surface:** Uvicorn provides built-in, configurable trusted proxy-header handling relevant to a future Tailscale Serve topology.
4. **Operational simplicity:** Pure-Python base install minimizes native-wheel risk for a small localhost-first service on macOS and later Fedora.
5. **Ecosystem proportionality:** Uvicorn is the most conventional choice for a single-service FastAPI deployment with systemd wrapping later.

### Conditions that would change the recommendation

| Condition | Likely shift |
|---|---|
| Accepted requirement for native HTTP/2 termination at the app server without an external proxy | Toward **Hypercorn** or **Granian** |
| Evidence that Uvicorn lifecycle/worker behavior is insufficient for planned background work | Toward **Hypercorn** (trio) or reconsider process architecture first |
| Measured wheel or platform support failures for Uvicorn optional extras on Fedora NUC | Re-evaluate base vs `[standard]` split, or consider **Hypercorn** |
| Verified throughput requirements with primary-source operational justification | Consider **Granian**, accepting wheel and tuning complexity |
| Security review finds Uvicorn proxy-header defaults inadequate even with explicit `forwarded-allow-ips` | Mandate application-layer proxy middleware regardless of server, weakening Uvicorn’s differentiator |

---

## 8. Explicit unresolved decision

**Decision for the COOPERATOR**

> Which ASGI runtime should FrameNest adopt for loopback-first local server execution: **Uvicorn**, **Hypercorn**, or **Granian**?

No runtime is accepted until:

1. the Cooperator explicitly selects a candidate;
2. a separate bounded ADR task records an **Accepted** decision with pinned Poetry versions and operational constraints; and
3. only then a test-first runtime implementation task is authorized.

This evidence package does **not** authorize installation, startup wiring, CLI commands, socket binding, or production deployment.

---

## 9. Proposed next steps

1. **COOPERATOR decision** on the ASGI runtime candidate using this evidence package.
2. **Separate bounded Accepted ADR task** recording the chosen runtime, expected Poetry dependency form (including whether optional extras such as `uvicorn[standard]` or `granian[reload]` are in scope), bind/proxy policy, and revisit triggers.
3. **Only after ADR acceptance:** bounded test-first runtime implementation wiring `create_app()` to the selected server with explicit loopback host from `FrameNestSettings`, still without public exposure, deployment files, or additional endpoints beyond authorized scope.

---

## Source index

| ID | URL | Used for |
|---|---|---|
| S1 | https://pypi.org/project/uvicorn/ | Uvicorn release metadata |
| S2 | https://www.uvicorn.dev/settings/ | Uvicorn configuration defaults and proxy headers |
| S3 | https://raw.githubusercontent.com/encode/uvicorn/master/README.md | Uvicorn capabilities and extras |
| S4 | https://raw.githubusercontent.com/encode/uvicorn/master/docs/deployment/index.md | Uvicorn workers and deployment patterns |
| S5 | https://raw.githubusercontent.com/encode/uvicorn/master/uvicorn/config.py | Uvicorn source defaults |
| S6 | https://pypi.org/project/hypercorn/ | Hypercorn release metadata |
| S7 | https://raw.githubusercontent.com/pgjones/hypercorn/main/README.rst | Hypercorn protocols and extras |
| S8 | https://raw.githubusercontent.com/pgjones/hypercorn/main/docs/how_to_guides/configuring.rst | Hypercorn configuration matrix |
| S9 | https://raw.githubusercontent.com/pgjones/hypercorn/main/docs/how_to_guides/api_usage.rst | Hypercorn programmatic serve and shutdown |
| S10 | https://raw.githubusercontent.com/pgjones/hypercorn/main/src/hypercorn/config.py | Hypercorn default bind |
| S11 | https://pypi.org/project/granian/ | Granian release metadata |
| S12 | https://raw.githubusercontent.com/emmett-framework/granian/master/README.md | Granian features, CLI, proxy wrappers, workers |
| S13 | https://fastapi.tiangolo.com/deployment/manually/#asgi-servers | FastAPI ASGI server guidance |
| S14 | https://api.github.com/repos/Kludex/uvicorn | Uvicorn maintenance signal |
| S15 | https://api.github.com/repos/pgjones/hypercorn | Hypercorn maintenance signal |
| S16 | https://api.github.com/repos/emmett-framework/granian | Granian maintenance signal |

All URLs above returned HTTP 200 on retrieval date 2026-06-24, except GitHub code search (not used after 401).
