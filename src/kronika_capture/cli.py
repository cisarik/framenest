"""Operator entry for the stripped chatgpt-page ask kernel.

Supported commands are ``ask``, ``bridge run``, ``bridge status``, and
``login``. Removed commands are rejected by the parser.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

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

    login = sub.add_parser("login", help="launch the operator login wizard")
    login.add_argument(
        "--profile",
        default=None,
        help="owned Chromium profile directory (default: <state-dir>/chromium-profile)",
    )
    login.set_defaults(handler=_cmd_login)
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
    deadline = started + args.timeout
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


def _cmd_login(args: argparse.Namespace) -> int:
    state = _state_dir(args)
    profile = args.profile or str(state / "chromium-profile")
    script = paths.packaged_extension_path("headless", "probe.mjs")
    if not script.is_file():
        print("error: packaged login wizard is missing", file=sys.stderr)
        return EXIT_BRIDGE
    completed = subprocess.run(
        ["node", str(script), "login", "--profile", profile],
        check=False,
    )
    return completed.returncode


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
