"""Production runtime checks for deployment supervisors."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import NoReturn

from framenest.configuration import load_settings
from framenest.infrastructure.persistence.errors import FrameNestPersistenceError
from framenest.infrastructure.persistence.migrations import inspect_database_migration_status
from framenest.server import run_server

COMMAND_ERROR_CODE = "FRAMENEST_PRODUCTION_COMMAND_FAILED"
DATABASE_NOT_READY_CODE = "FRAMENEST_DATABASE_NOT_READY"


class _UsageError(Exception):
    pass


class _DatabaseNotReadyError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _UsageError("Invalid production command.")


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch production runtime checks and return a process exit code."""
    operation = "unknown"
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        operation = args.operation
        settings = load_settings(env_file=None)
        if operation == "check-database-ready":
            status = inspect_database_migration_status(settings)
            if status.state != "at_head":
                raise _DatabaseNotReadyError()
            _write_success(operation, current_revision=status.current_revision)
        elif operation == "serve":
            run_server(settings=settings)
        else:
            raise _UsageError("Invalid production command.")
        return 0
    except _UsageError:
        _write_error(
            operation=operation,
            error_code=COMMAND_ERROR_CODE,
            message="Production command failed.",
        )
        return 2
    except KeyboardInterrupt:
        return 0
    except _DatabaseNotReadyError:
        _write_error(
            operation=operation,
            error_code=DATABASE_NOT_READY_CODE,
            message="Catalog database is not ready. Run framenest-db migrate first.",
        )
        return 4
    except (FrameNestPersistenceError, Exception):
        _write_error(
            operation=operation,
            error_code=COMMAND_ERROR_CODE,
            message="Production command failed.",
        )
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="framenest-production", add_help=True)
    subcommands = parser.add_subparsers(dest="operation", required=True)
    subcommands.add_parser(
        "check-database-ready",
        help="Verify the configured database is already migrated to head.",
    )
    subcommands.add_parser(
        "serve",
        help="Run the production FrameNest server in the foreground.",
    )
    return parser


def _write_success(operation: str, *, current_revision: str | None) -> None:
    payload = {
        "operation": operation,
        "state": "ready",
        "current_revision": current_revision,
    }
    print(json.dumps(payload, separators=(",", ":")), file=sys.stdout)


def _write_error(*, operation: str, error_code: str, message: str) -> None:
    payload = {
        "operation": operation,
        "state": "error",
        "error_code": error_code,
        "message": message,
    }
    print(json.dumps(payload, separators=(",", ":")), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
