"""Standard-library CLI for FrameNest catalog backup operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from framenest.infrastructure.persistence.catalog_backup import (
    BackupError,
    BackupResult,
    create_catalog_backup,
    restore_catalog_backup,
    verify_catalog_backup,
)

INVALID_INPUT_CODE = "FRAMENEST_BACKUP_INVALID_INPUT"
COMMAND_FAILED_CODE = "FRAMENEST_BACKUP_COMMAND_FAILED"


class _UsageError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _UsageError("Invalid backup command.")


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch catalog backup operations and return a process exit code."""
    operation = "unknown"
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        operation = args.operation
        if operation == "create":
            result = create_catalog_backup(Path(args.source), Path(args.output))
        elif operation == "verify":
            result = verify_catalog_backup(Path(args.bundle))
        elif operation == "restore":
            result = restore_catalog_backup(Path(args.bundle), Path(args.destination))
        else:
            raise _UsageError("Invalid backup command.")
        _write_success(operation, result)
        return 0
    except _UsageError:
        _write_error(
            operation=operation,
            error_code=INVALID_INPUT_CODE,
            message="Invalid backup command.",
        )
        return 2
    except (BackupError, Exception):
        _write_error(
            operation=operation,
            error_code=COMMAND_FAILED_CODE,
            message="Backup command failed.",
        )
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="framenest-backup", add_help=True)
    subcommands = parser.add_subparsers(dest="operation", required=True)

    create = subcommands.add_parser("create", help="Create a catalog backup bundle.")
    create.add_argument("--source", required=True, help="Existing catalog SQLite database.")
    create.add_argument("--output", required=True, help="New backup bundle directory.")

    verify = subcommands.add_parser("verify", help="Verify a catalog backup bundle.")
    verify.add_argument("--bundle", required=True, help="Backup bundle directory.")

    restore = subcommands.add_parser("restore", help="Restore a bundle to a new catalog path.")
    restore.add_argument("--bundle", required=True, help="Backup bundle directory.")
    restore.add_argument("--destination", required=True, help="Absent destination database path.")
    return parser


def _write_success(operation: str, result: BackupResult) -> None:
    payload = {
        "operation": operation,
        "state": result.state,
        "catalog": {
            "size_bytes": result.catalog_size_bytes,
            "sha256": result.catalog_sha256,
            "alembic_revision": result.alembic_revision,
        },
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stdout)


def _write_error(*, operation: str, error_code: str, message: str) -> None:
    payload = {
        "operation": operation,
        "state": "error",
        "error_code": error_code,
        "message": message,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
