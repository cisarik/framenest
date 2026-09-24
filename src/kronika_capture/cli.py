"""Operator entry for the stripped chatgpt-page ask kernel.

Supported commands are ``ask``, ``bridge run``, ``bridge status``, and
``login``. Removed commands are rejected by the parser.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path

from kronika_capture import __version__, paths
from kronika_capture.bridge.server import serve
from kronika_capture.client import (
    BridgeClient,
    BridgeError,
    BridgeNoToken,
    BridgeUnreachable,
)
from kronika_capture.config import (
    APP_NAME,
    CLIENT_POLL_INTERVAL_S,
    CLIENT_WAITING_NOTICE_S,
    DEFAULT_ASK_TIMEOUT_S,
    DEFAULT_BRIDGE_HOST,
    DEFAULT_BRIDGE_PORT,
    MAX_ASK_TIMEOUT_S,
    UPLOAD_UNAVAILABLE,
)
from kronika_capture.errors import (
    EXIT_BRIDGE,
    EXIT_CANCELLED,
    EXIT_OK,
    EXIT_TIMEOUT,
    EXIT_USAGE,
    exit_code_for_error,
)

TERMINAL_STATUSES = ("done", "failed", "cancelled")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=(
            "Local ask against a logged-in chatgpt.com page through a loopback bridge."
        ),
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    parser.add_argument(
        "--state-dir",
        default=None,
        help=(
            "explicit state directory; development default is the XDG "
            "framenest-chatgpt-page directory"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="send one prompt and print the answer text")
    ask.add_argument("prompt", nargs="?", help="prompt text; omit to read stdin")
    ask.add_argument(
        "-f",
        "--file",
        action="append",
        default=[],
        metavar="PATH",
        help="rejected; file upload is not available in this build",
    )
    ask.add_argument("--project", default=None, help="name of the one configured scratch project")
    ask.add_argument("--timeout", type=int, default=DEFAULT_ASK_TIMEOUT_S)
    ask.add_argument("--quiet", action="store_true")
    ask.set_defaults(handler=_cmd_ask)

    bridge = sub.add_parser("bridge", help="run or inspect the loopback bridge")
    bridge_sub = bridge.add_subparsers(dest="bridge_command", required=True)
    run = bridge_sub.add_parser("run", help="listen on 127.0.0.1")
    run.add_argument("--port", type=int, default=DEFAULT_BRIDGE_PORT)
    run.set_defaults(handler=_cmd_bridge_run)
    status = bridge_sub.add_parser("status", help="print bridge status JSON")
    status.set_defaults(handler=_cmd_bridge_status)
    resume = bridge_sub.add_parser("resume", help="request an explicit readiness check")
    resume.add_argument("--job-id", default=None)
    resume.add_argument("--intervention-id", required=True)
    resume.set_defaults(handler=_cmd_bridge_resume)

    login = sub.add_parser("login", help="launch the operator login wizard")
    login.add_argument(
        "--profile",
        default=None,
        help="owned Chromium profile directory (default: <state-dir>/chromium-profile)",
    )
    login.set_defaults(handler=_cmd_login)
    login.add_argument("--chrome-path", required=True, help="preflight-verified Chromium executable")

    runner = sub.add_parser("runner", help="launch the persistent browser runner")
    runner_sub = runner.add_subparsers(dest="runner_command", required=True)
    runner_run = runner_sub.add_parser("run", help="run until the service is stopped")
    runner_run.add_argument(
        "--chrome-path",
        default=None,
        help="explicit Chromium executable; defaults to KRONIKA_CHROMIUM_PATH",
    )
    runner_run.add_argument(
        "--profile",
        default=None,
        help="owned Chromium profile directory (default: <state-dir>/chromium-profile)",
    )
    runner_run.add_argument("--port", type=int, default=DEFAULT_BRIDGE_PORT)
    runner_run.add_argument(
        "--headed",
        action="store_true",
        help="show the browser on the configured display",
    )
    runner_run.set_defaults(handler=_cmd_runner_run)
    return parser


def _state_dir(args: argparse.Namespace):
    return paths.state_dir(args.state_dir)


def _read_prompt(args: argparse.Namespace) -> str | None:
    if args.prompt:
        return args.prompt
    if sys.stdin.isatty():
        return None
    text = sys.stdin.read()
    return text if text.strip() else None


def _cmd_ask(args: argparse.Namespace) -> int:
    if args.file:
        print(UPLOAD_UNAVAILABLE, file=sys.stderr)
        return EXIT_USAGE
    if not isinstance(args.timeout, int) or isinstance(args.timeout, bool):
        print("error: timeout must be an integer", file=sys.stderr)
        return EXIT_USAGE
    if not 1 <= args.timeout <= MAX_ASK_TIMEOUT_S:
        print(
            f"error: timeout must be in 1..{MAX_ASK_TIMEOUT_S}",
            file=sys.stderr,
        )
        return EXIT_USAGE
    prompt = _read_prompt(args)
    if not prompt:
        print("error: prompt is required", file=sys.stderr)
        return EXIT_USAGE
    client = BridgeClient(state_dir=_state_dir(args), timeout=args.timeout + 30)
    try:
        job_id = client.create_job(
            prompt,
            timeout_s=args.timeout,
            project=args.project,
            request_id=str(uuid.uuid4()),
        )
    except BridgeNoToken as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BRIDGE
    except BridgeUnreachable as exc:
        print(f"error: bridge unreachable: {exc}", file=sys.stderr)
        return EXIT_BRIDGE
    except BridgeError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return exit_code_for_error(exc.code)
    return _poll_ask(client, job_id, args)


def _poll_ask(client: BridgeClient, job_id: str, args: argparse.Namespace) -> int:
    started = time.monotonic()
    # The bridge owns active time; this outer bound includes the separate admin budget.
    deadline = started + args.timeout + 1800 + 30
    noticed = False
    while True:
        try:
            payload = client.get_job(job_id)
        except BridgeUnreachable:
            print("error: bridge unreachable while waiting", file=sys.stderr)
            return EXIT_BRIDGE
        except BridgeError as exc:
            print(f"error: {exc.message}", file=sys.stderr)
            return exit_code_for_error(exc.code)
        job = payload.get("job") if isinstance(payload, dict) else None
        if not isinstance(job, dict):
            print("error: bridge returned no job", file=sys.stderr)
            return EXIT_BRIDGE
        status = job.get("status")
        if status in TERMINAL_STATUSES:
            return _finish(job)
        if (
            not args.quiet
            and not noticed
            and status == "queued"
            and (time.monotonic() - started) >= CLIENT_WAITING_NOTICE_S
        ):
            print("[cli] waiting for the headless executor to pick up the job", file=sys.stderr)
            noticed = True
        if time.monotonic() >= deadline:
            try:
                client.cancel(job_id)
            except (BridgeError, BridgeUnreachable):
                pass
            print("error: timed out", file=sys.stderr)
            return EXIT_TIMEOUT
        time.sleep(min(CLIENT_POLL_INTERVAL_S, max(deadline - time.monotonic(), 0.0)))


def _finish(job: dict) -> int:
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    status = job.get("status")
    if status == "done":
        answer = result.get("answer")
        if isinstance(answer, str):
            sys.stdout.write(answer)
            if not answer.endswith("\n"):
                sys.stdout.write("\n")
            return EXIT_OK
        print("error: empty answer", file=sys.stderr)
        return exit_code_for_error("E_RESPONSE_EMPTY")
    if status == "cancelled":
        print("error: cancelled", file=sys.stderr)
        return EXIT_CANCELLED
    code = result.get("error_code") or "E_INTERNAL"
    print(f"error: {code}", file=sys.stderr)
    return exit_code_for_error(str(code))


def _cmd_bridge_run(args: argparse.Namespace) -> int:
    if args.port != DEFAULT_BRIDGE_PORT and not 1 <= args.port <= 65535:
        print("error: port is invalid", file=sys.stderr)
        return EXIT_USAGE
    return serve(
        host=DEFAULT_BRIDGE_HOST,
        port=args.port,
        state_dir=_state_dir(args),
    )


def _cmd_bridge_status(args: argparse.Namespace) -> int:
    client = BridgeClient(state_dir=_state_dir(args))
    try:
        payload = client.status()
    except BridgeNoToken as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_BRIDGE
    except BridgeUnreachable as exc:
        print(f"error: bridge unreachable: {exc}", file=sys.stderr)
        return EXIT_BRIDGE
    except BridgeError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return EXIT_BRIDGE
    print(json.dumps(payload, indent=2, sort_keys=True))
    return EXIT_OK


def configured_chromium(explicit: str | None) -> Path | None:
    """Resolve one absolute, executable Chromium path. Never search ``PATH``."""

    raw = (explicit or os.environ.get("KRONIKA_CHROMIUM_PATH") or "").strip()
    if not raw or "\x00" in raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        return None
    try:
        info = path.stat()
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode) or not os.access(path, os.X_OK):
        return None
    return path


def runner_token_directory(state: Path) -> Path:
    """Directory whose ``token`` file the existing runner already reads.

    Systemd names the credential ``token``, so the credentials directory is
    that parent. No token bytes are copied or placed on the command line.
    """

    credential = paths.systemd_bridge_token_path()
    if credential is None:
        return state
    return credential.parent


def build_runner_argv(args: argparse.Namespace) -> list[str] | None:
    """Build the node runner command. The token value is never an argument."""

    chrome = configured_chromium(args.chrome_path)
    if chrome is None:
        return None
    if not isinstance(args.port, int) or isinstance(args.port, bool):
        return None
    if args.port != DEFAULT_BRIDGE_PORT and not 1 <= args.port <= 65535:
        return None
    state = _state_dir(args)
    profile = args.profile or str(state / "chromium-profile")
    script = paths.packaged_extension_path("headless", "runner.mjs")
    if not script.is_file():
        return None
    argv = [
        "node",
        str(script),
        "run",
        "--state-dir",
        str(runner_token_directory(state)),
        "--profile",
        profile,
        "--port",
        str(args.port),
        "--chrome-path",
        str(chrome),
    ]
    if args.headed:
        argv.append("--headed")
    return argv


def _cmd_runner_run(args: argparse.Namespace) -> int:
    if not isinstance(args.port, int) or isinstance(args.port, bool) or not 1 <= args.port <= 65535:
        print("error: port is invalid", file=sys.stderr)
        return EXIT_USAGE
    if configured_chromium(args.chrome_path) is None:
        print("error: explicit Chromium executable is required", file=sys.stderr)
        return EXIT_USAGE
    command = build_runner_argv(args)
    if command is None:
        print("error: packaged runner is missing", file=sys.stderr)
        return EXIT_BRIDGE
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


def _cmd_login(args: argparse.Namespace) -> int:
    state = _state_dir(args)
    profile = args.profile or str(state / "chromium-profile")
    script = paths.packaged_extension_path("headless", "probe.mjs")
    if not script.is_file():
        print("error: packaged login wizard is missing", file=sys.stderr)
        return EXIT_BRIDGE
    completed = subprocess.run(
        ["node", str(script), "login", "--profile", profile, "--chrome-path", args.chrome_path],
        check=False,
    )
    return completed.returncode


def _cmd_bridge_resume(args: argparse.Namespace) -> int:
    try:
        result = BridgeClient(state_dir=_state_dir(args)).resume(args.job_id, args.intervention_id)
    except (BridgeError, BridgeNoToken, BridgeUnreachable):
        print("error: readiness check could not be requested", file=sys.stderr)
        return EXIT_BRIDGE
    print(json.dumps(result, sort_keys=True))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return EXIT_OK
        return int(code)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    return int(handler(args))
