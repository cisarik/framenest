"""Pure FrameNest domain primitives."""

from framenest.domain.devices import Device, FrameNestDeviceError
from framenest.domain.identities import (
    DeviceId,
    FrameNestIdentityError,
    LibraryId,
    MediaId,
    MediaLocationId,
    SeriesId,
    StorageVolumeId,
)
from framenest.domain.libraries import (
    FrameNestLibraryError,
    FrameNestLibraryRootError,
    Library,
    LibraryPathFlavor,
    LibraryRoot,
)

__all__ = [
    "Device",
    "DeviceId",
    "FrameNestDeviceError",
    "FrameNestIdentityError",
    "FrameNestLibraryError",
    "FrameNestLibraryRootError",
    "Library",
    "LibraryId",
    "LibraryPathFlavor",
    "LibraryRoot",
    "MediaId",
    "MediaLocationId",
    "SeriesId",
    "StorageVolumeId",
]
