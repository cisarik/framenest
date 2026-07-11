# FrameNest Development Launcher

## Status

This is the current browser-development workflow guide. It documents the local
launcher that runs the pre-alpha web application in an external browser.

Classification: development operator guide.

Consumers: Cooperator, Orchestrator, Worker, and local FrameNest developers.

Retention: remains while the browser-development launcher exists.

Inbound links: [README.md](README.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## First Run

From the repository root:

```text
git submodule update --init --recursive
./.ap/ap doctor
./framenest setup
./framenest start
```

The AP doctor validates the pinned canonical Analytic Programming submodule and
the managed block in [AGENTS.md](AGENTS.md). It does not replace product tests.

`setup` locates the uv-managed CPython `3.13.14`, installs it with `uv` if it is
missing, configures Poetry to use that interpreter with `.venv/`, and runs
`poetry install --no-interaction`. Re-run `./framenest setup` after committed
dependency or lockfile changes.

`start` automatically performs the same setup flow only when the expected
project environment or installed controller is missing.

## Commands

```text
./framenest setup              Prepare the Poetry environment.
./framenest start              Start, migrate, wait for health, and open a browser.
./framenest start --no-open    Start without opening a browser.
./framenest stop               Stop only the verified launcher-owned server.
./framenest restart            Verified stop, then start.
./framenest restart --no-open  Restart without opening a browser.
./framenest status             Show managed process, database, and log state.
./framenest open               Open the healthy managed server.
./framenest logs               Show recent server log lines.
./framenest logs --follow      Follow the development server log.
./framenest --help             Show wrapper help.
./framenest <command> --help   Show command help.
```

The launcher does not implement client start/stop commands. The current client
is an external browser tab, and FrameNest does not close browser processes.

## Runtime Locations

On ordinary macOS development hosts, launcher-owned data is outside the Git
worktree:

```text
~/Library/Application Support/FrameNest/development/catalog.sqlite3
~/Library/Application Support/FrameNest/development/runtime/
~/Library/Logs/FrameNest/development/server.log
```

The runtime state directory stores the managed process state and operation lock.
The log file contains the managed child process output used by `./framenest
logs`.

The launcher honors an existing absolute `FRAMENEST_DATABASE_PATH`. Tests and
manual disposable runs may also use:

```text
FRAMENEST_DEVELOPMENT_RUNTIME_DIR=/absolute/path/to/runtime
FRAMENEST_DEVELOPMENT_LOG_DIR=/absolute/path/to/log-directory
FRAMENEST_PORT=8123
```

Overrides must be absolute paths. They are launcher/runtime inputs only and are
not web API response data.

## Start And Migration

`./framenest start` enforces loopback host `127.0.0.1`, resolves the development
database, migrates it to the packaged Alembic head, starts a detached server
using the current Poetry environment's Python, writes managed state atomically,
waits for `GET /health` to return `{"status": "ok"}`, and opens the default
browser unless `--no-open` was supplied.

The raw server command remains a lower-level foreground boundary:

```text
poetry run framenest-server
```

That command does not migrate automatically, does not manage background state,
and is stopped directly from its terminal.

## Status And Exit Behavior

`status` reports one of:

```text
running
stopped
stale
unhealthy
conflict
```

Healthy running status exits with code `0`. Stopped or stale status exits with
code `3`, unhealthy with `4`, and conflict with `5`. Usage errors exit with
code `2`.

`conflict` means the launcher cannot safely prove ownership, or the selected
port is occupied by an unmanaged process. The launcher refuses to adopt,
replace, or kill that process.

## Logs

Use:

```text
./framenest logs
./framenest logs --follow
```

The command reads only the FrameNest development log. It does not classify
wrapper, Poetry, or shell diagnostics as FrameNest structured application
records, and it does not delete or rotate logs.

## Recovery

If status is `stale`, the recorded launcher-owned process no longer exists.
`start` and `stop` can clear stale launcher state safely.

If status is `conflict`, inspect the message and stop the unrelated process
through the tool that started it, or choose a different `FRAMENEST_PORT`. The
launcher does not use broad process search, `pkill`, `killall`, port-based
killing, or automatic force-kill recovery.

## Manual No-Browser Run

For disposable validation:

```text
FRAMENEST_DATABASE_PATH=/tmp/framenest-dev/catalog.sqlite3 \
FRAMENEST_DEVELOPMENT_RUNTIME_DIR=/tmp/framenest-dev/runtime \
FRAMENEST_DEVELOPMENT_LOG_DIR=/tmp/framenest-dev/logs \
FRAMENEST_PORT=8123 \
./framenest start --no-open
```

Use `./framenest stop` with the same environment values to stop that managed
server. To completely stop FrameNest browser-development mode, stop the managed
server and close any external browser tabs manually.
