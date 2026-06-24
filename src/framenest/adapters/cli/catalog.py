"""Standard-library CLI for FrameNest catalog operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any, NoReturn

from framenest.adapters.cli.library_root import LibraryRootNotUsableError, prepare_library_root
from framenest.application.ports.device_repository import (
    DeviceAlreadyExistsError,
    DeviceRepository,
    FrameNestDeviceRepositoryError,
)
from framenest.application.ports.library_repository import (
    FrameNestLibraryRepositoryError,
    LibraryAlreadyExistsError,
    LibraryDeviceNotFoundError,
    LibraryRepository,
    LibraryRootAlreadyRegisteredError,
)
from framenest.configuration import FrameNestSettings, load_settings
from framenest.domain import (
    Device,
    DeviceId,
    FrameNestDeviceError,
    FrameNestIdentityError,
    FrameNestLibraryError,
    Library,
    LibraryId,
    LibraryRoot,
)
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.errors import FrameNestPersistenceError
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.migrations import inspect_database_migration_status

INVALID_INPUT_CODE = "FRAMENEST_CATALOG_INVALID_INPUT"
INVALID_INPUT_MESSAGE = "Invalid catalog command."
DEVICE_NOT_FOUND_CODE = "FRAMENEST_DEVICE_NOT_FOUND"
DEVICE_NOT_FOUND_MESSAGE = "Device not found."
LIBRARY_NOT_FOUND_CODE = "FRAMENEST_LIBRARY_NOT_FOUND"
LIBRARY_NOT_FOUND_MESSAGE = "Library not found."
LIBRARY_DEVICE_NOT_FOUND_CODE = "FRAMENEST_LIBRARY_DEVICE_NOT_FOUND"
LIBRARY_DEVICE_NOT_FOUND_MESSAGE = "Owning device not found."
ROOT_NOT_USABLE_CODE = "FRAMENEST_LIBRARY_ROOT_NOT_USABLE"
ROOT_NOT_USABLE_MESSAGE = "Library root is not usable."
ROOT_ALREADY_REGISTERED_CODE = "FRAMENEST_LIBRARY_ROOT_ALREADY_REGISTERED"
ROOT_ALREADY_REGISTERED_MESSAGE = "Library root is already registered."
NOT_READY_CODE = "FRAMENEST_CATALOG_NOT_READY"
NOT_READY_MESSAGE = "Catalog database is not ready. Run framenest-db migrate."
COMMAND_FAILED_CODE = "FRAMENEST_CATALOG_COMMAND_FAILED"
COMMAND_FAILED_MESSAGE = "Catalog command failed."


class _UsageError(Exception):
    pass


class _InvalidInputError(Exception):
    pass


class _DeviceNotFoundError(Exception):
    pass


class _LibraryNotFoundError(Exception):
    pass


class _LibraryDeviceNotFoundError(Exception):
    pass


class _RootNotUsableError(Exception):
    pass


class _RootAlreadyRegisteredError(Exception):
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
    except _RootNotUsableError:
        _write_error(
            operation=operation,
            error_code=ROOT_NOT_USABLE_CODE,
            message=ROOT_NOT_USABLE_MESSAGE,
        )
        return 2
    except _DeviceNotFoundError:
        _write_error(
            operation=operation,
            error_code=DEVICE_NOT_FOUND_CODE,
            message=DEVICE_NOT_FOUND_MESSAGE,
        )
        return 3
    except _LibraryNotFoundError:
        _write_error(
            operation=operation,
            error_code=LIBRARY_NOT_FOUND_CODE,
            message=LIBRARY_NOT_FOUND_MESSAGE,
        )
        return 3
    except _LibraryDeviceNotFoundError:
        _write_error(
            operation=operation,
            error_code=LIBRARY_DEVICE_NOT_FOUND_CODE,
            message=LIBRARY_DEVICE_NOT_FOUND_MESSAGE,
        )
        return 3
    except _RootAlreadyRegisteredError:
        _write_error(
            operation=operation,
            error_code=ROOT_ALREADY_REGISTERED_CODE,
            message=ROOT_ALREADY_REGISTERED_MESSAGE,
        )
        return 5
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
        FrameNestLibraryRepositoryError,
        DeviceAlreadyExistsError,
        LibraryAlreadyExistsError,
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
    device_commands = device.add_subparsers(dest="operation", required=True)
    device_register = device_commands.add_parser("register")
    device_register.add_argument("--display-name", required=True, dest="display_name")
    device_get = device_commands.add_parser("get")
    device_get.add_argument("--id", required=True, dest="device_id")
    device_commands.add_parser("list")

    library = resources.add_parser("library")
    library_commands = library.add_subparsers(dest="operation", required=True)
    library_register = library_commands.add_parser("register")
    library_register.add_argument("--device-id", required=True, dest="device_id")
    library_register.add_argument("--display-name", required=True, dest="display_name")
    library_register.add_argument("--root", required=True, dest="root_path")
    library_get = library_commands.add_parser("get")
    library_get.add_argument("--id", required=True, dest="library_id")
    library_commands.add_parser("list")

    return parser


def _operation_name(args: argparse.Namespace) -> str:
    resource = getattr(args, "resource", None)
    operation = getattr(args, "operation", None)
    if resource not in {"device", "library"} or operation is None:
        return "unknown"
    return f"{resource}.{operation}"


def _dispatch(args: argparse.Namespace, settings: FrameNestSettings) -> dict[str, Any]:
    if args.resource == "device":
        return _dispatch_device(args, settings)
    if args.resource == "library":
        return _dispatch_library(args, settings)
    raise _UsageError(INVALID_INPUT_MESSAGE)


def _dispatch_device(args: argparse.Namespace, settings: FrameNestSettings) -> dict[str, Any]:
    if args.operation == "register":
        _validate_device_register_input(args.display_name)
        return _with_device_repository(
            settings,
            lambda repository: _register_device(repository, args.display_name),
        )
    if args.operation == "get":
        device_id = _parse_device_id(args.device_id)
        return _with_device_repository(
            settings,
            lambda repository: _get_device(repository, device_id),
        )
    if args.operation == "list":
        return _with_device_repository(settings, _list_devices)
    raise _UsageError(INVALID_INPUT_MESSAGE)


def _dispatch_library(args: argparse.Namespace, settings: FrameNestSettings) -> dict[str, Any]:
    if args.operation == "register":
        device_id = _parse_device_id(args.device_id)
        _validate_library_register_input(args.display_name)
        root = _prepare_library_root(args.root_path)
        return _with_library_repository(
            settings,
            lambda repository: _register_library(
                repository,
                device_id=device_id,
                display_name=args.display_name,
                root=root,
            ),
        )
    if args.operation == "get":
        library_id = _parse_library_id(args.library_id)
        return _with_library_repository(
            settings,
            lambda repository: _get_library(repository, library_id),
        )
    if args.operation == "list":
        return _with_library_repository(settings, _list_libraries)
    raise _UsageError(INVALID_INPUT_MESSAGE)


def _parse_device_id(value: str) -> DeviceId:
    try:
        return DeviceId.from_string(value)
    except FrameNestIdentityError:
        raise _InvalidInputError() from None


def _parse_library_id(value: str) -> LibraryId:
    try:
        return LibraryId.from_string(value)
    except FrameNestIdentityError:
        raise _InvalidInputError() from None


def _validate_device_register_input(display_name: str) -> None:
    try:
        Device(id=DeviceId.new(), display_name=display_name)
    except FrameNestDeviceError:
        raise _InvalidInputError() from None


def _validate_library_register_input(display_name: str) -> None:
    try:
        Library(
            id=LibraryId.new(),
            device_id=DeviceId.new(),
            display_name=display_name,
            root=_valid_placeholder_root(),
        )
    except FrameNestLibraryError:
        raise _InvalidInputError() from None


def _valid_placeholder_root() -> LibraryRoot:
    from framenest.adapters.cli.library_root import native_library_path_flavor
    from framenest.domain import LibraryPathFlavor

    flavor = native_library_path_flavor()
    path = "C:\\" if flavor == LibraryPathFlavor.WINDOWS else "/"
    return LibraryRoot(flavor=flavor, path=path)


def _prepare_library_root(raw_path: str) -> LibraryRoot:
    try:
        return prepare_library_root(raw_path)
    except LibraryRootNotUsableError:
        raise _RootNotUsableError() from None


def _register_device(repository: DeviceRepository, display_name: str) -> dict[str, Any]:
    try:
        device = Device(id=DeviceId.new(), display_name=display_name)
    except FrameNestDeviceError:
        raise _InvalidInputError() from None
    repository.add(device)
    return {"device": _device_payload(device)}


def _get_device(repository: DeviceRepository, device_id: DeviceId) -> dict[str, Any]:
    device = repository.get(device_id)
    if device is None:
        raise _DeviceNotFoundError()
    return {"device": _device_payload(device)}


def _list_devices(repository: DeviceRepository) -> dict[str, Any]:
    devices = repository.list_all()
    return {"devices": [_device_payload(device) for device in devices]}


def _register_library(
    repository: LibraryRepository,
    *,
    device_id: DeviceId,
    display_name: str,
    root: LibraryRoot,
) -> dict[str, Any]:
    try:
        library = Library(
            id=LibraryId.new(),
            device_id=device_id,
            display_name=display_name,
            root=root,
        )
    except FrameNestLibraryError:
        raise _InvalidInputError() from None
    try:
        repository.add(library)
    except LibraryDeviceNotFoundError:
        raise _LibraryDeviceNotFoundError() from None
    except LibraryRootAlreadyRegisteredError:
        raise _RootAlreadyRegisteredError() from None
    return {"library": _library_payload(library)}


def _get_library(repository: LibraryRepository, library_id: LibraryId) -> dict[str, Any]:
    library = repository.get(library_id)
    if library is None:
        raise _LibraryNotFoundError()
    return {"library": _library_payload(library)}


def _list_libraries(repository: LibraryRepository) -> dict[str, Any]:
    libraries = repository.list_all()
    return {"libraries": [_library_payload(library) for library in libraries]}


def _device_payload(device: Device) -> dict[str, str]:
    return {"id": device.id.to_string(), "display_name": device.display_name}


def _library_payload(library: Library) -> dict[str, Any]:
    return {
        "id": library.id.to_string(),
        "device_id": library.device_id.to_string(),
        "display_name": library.display_name,
        "root": {
            "flavor": library.root.flavor.value,
            "path": library.root.path,
        },
    }


def _with_device_repository(
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


def _with_library_repository(
    settings: FrameNestSettings,
    callback: Callable[[LibraryRepository], dict[str, Any]],
) -> dict[str, Any]:
    status = inspect_database_migration_status(settings)
    if status.state != "at_head":
        raise _NotReadyError()
    engine = create_sqlite_engine(settings.database_path)
    try:
        repository = SqliteLibraryRepository(engine)
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
