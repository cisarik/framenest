"""Standard-library CLI for FrameNest catalog operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any, NoReturn

from framenest.application.ports.device_repository import (
    DeviceAlreadyExistsError,
    DeviceRepository,
    FrameNestDeviceRepositoryError,
)
from framenest.configuration import FrameNestSettings, load_settings
from framenest.domain import Device, DeviceId, FrameNestDeviceError, FrameNestIdentityError
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.errors import FrameNestPersistenceError
from framenest.infrastructure.persistence.migrations import inspect_database_migration_status

INVALID_INPUT_CODE = "FRAMENEST_CATALOG_INVALID_INPUT"
INVALID_INPUT_MESSAGE = "Invalid catalog command."
NOT_FOUND_CODE = "FRAMENEST_DEVICE_NOT_FOUND"
NOT_FOUND_MESSAGE = "Device not found."
NOT_READY_CODE = "FRAMENEST_CATALOG_NOT_READY"
NOT_READY_MESSAGE = "Catalog database is not ready. Run framenest-db migrate."
COMMAND_FAILED_CODE = "FRAMENEST_CATALOG_COMMAND_FAILED"
COMMAND_FAILED_MESSAGE = "Catalog command failed."


class _UsageError(Exception):
    pass


class _InvalidInputError(Exception):
    pass


class _NotFoundError(Exception):
    pass


class _NotReadyError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _UsageError(INVALID_INPUT_MESSAGE)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch catalog operations and return a process exit code."""
    operation = "unknown"
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        settings = load_settings()
        operation = _operation_name(args)
        result = _dispatch(args, settings)
        _write_success(operation, result)
        return 0
    except _UsageError:
        _write_error(
            operation=operation,
            error_code=INVALID_INPUT_CODE,
            message=INVALID_INPUT_MESSAGE,
        )
        return 2
    except _InvalidInputError:
        _write_error(
            operation=operation,
            error_code=INVALID_INPUT_CODE,
            message=INVALID_INPUT_MESSAGE,
        )
        return 2
    except _NotFoundError:
        _write_error(
            operation=operation,
            error_code=NOT_FOUND_CODE,
            message=NOT_FOUND_MESSAGE,
        )
        return 3
    except _NotReadyError:
        _write_error(
            operation=operation,
            error_code=NOT_READY_CODE,
            message=NOT_READY_MESSAGE,
        )
        return 4
    except (
        FrameNestPersistenceError,
        FrameNestDeviceRepositoryError,
        DeviceAlreadyExistsError,
        Exception,
    ):
        _write_error(
            operation=operation,
            error_code=COMMAND_FAILED_CODE,
            message=COMMAND_FAILED_MESSAGE,
        )
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="framenest-catalog", add_help=True)
    resources = parser.add_subparsers(dest="resource", required=True)
    device = resources.add_parser("device")
    commands = device.add_subparsers(dest="operation", required=True)

    register = commands.add_parser("register")
    register.add_argument("--display-name", required=True, dest="display_name")

    get_command = commands.add_parser("get")
    get_command.add_argument("--id", required=True, dest="device_id")

    commands.add_parser("list")
    return parser


def _operation_name(args: argparse.Namespace) -> str:
    if getattr(args, "resource", None) != "device":
        return "unknown"
    operation = getattr(args, "operation", None)
    if operation is None:
        return "unknown"
    return f"device.{operation}"


def _dispatch(args: argparse.Namespace, settings: FrameNestSettings) -> dict[str, Any]:
    if args.resource != "device":
        raise _UsageError(INVALID_INPUT_MESSAGE)

    if args.operation == "register":
        _validate_register_input(args.display_name)
        return _with_repository(
            settings,
            lambda repository: _register(repository, args.display_name),
        )
    if args.operation == "get":
        device_id = _parse_device_id(args.device_id)
        return _with_repository(
            settings,
            lambda repository: _get(repository, device_id),
        )
    if args.operation == "list":
        return _with_repository(settings, _list)
    raise _UsageError(INVALID_INPUT_MESSAGE)


def _parse_device_id(value: str) -> DeviceId:
    try:
        return DeviceId.from_string(value)
    except FrameNestIdentityError:
        raise _InvalidInputError() from None


def _validate_register_input(display_name: str) -> None:
    try:
        Device(id=DeviceId.new(), display_name=display_name)
    except FrameNestDeviceError:
        raise _InvalidInputError() from None


def _register(repository: DeviceRepository, display_name: str) -> dict[str, Any]:
    try:
        device = Device(id=DeviceId.new(), display_name=display_name)
    except FrameNestDeviceError:
        raise _InvalidInputError() from None
    repository.add(device)
    return {"device": _device_payload(device)}


def _get(repository: DeviceRepository, device_id: DeviceId) -> dict[str, Any]:
    device = repository.get(device_id)
    if device is None:
        raise _NotFoundError()
    return {"device": _device_payload(device)}


def _list(repository: DeviceRepository) -> dict[str, Any]:
    devices = repository.list_all()
    return {"devices": [_device_payload(device) for device in devices]}


def _device_payload(device: Device) -> dict[str, str]:
    return {"id": device.id.to_string(), "display_name": device.display_name}


def _with_repository(
    settings: FrameNestSettings,
    callback: Callable[[DeviceRepository], dict[str, Any]],
) -> dict[str, Any]:
    status = inspect_database_migration_status(settings)
    if status.state != "at_head":
        raise _NotReadyError()
    engine = create_sqlite_engine(settings.database_path)
    try:
        repository = SqliteDeviceRepository(engine)
        return callback(repository)
    finally:
        dispose_engine(engine)


def _write_success(operation: str, result: dict[str, Any]) -> None:
    payload = {
        "operation": operation,
        "state": "ok",
        **result,
    }
    print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), file=sys.stdout)


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
