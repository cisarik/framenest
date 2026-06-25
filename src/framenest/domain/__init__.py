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
from framenest.domain.media import (
    FrameNestMediaError,
    FrameNestMediaLocationError,
    FrameNestMediaRelativePathError,
    LogicalMedia,
    MediaKind,
    MediaLocation,
    MediaLocationAvailability,
    MediaRelativePath,
)

__all__ = [
    "Device",
    "DeviceId",
    "FrameNestDeviceError",
    "FrameNestIdentityError",
    "FrameNestLibraryError",
    "FrameNestLibraryRootError",
    "FrameNestMediaError",
    "FrameNestMediaLocationError",
    "FrameNestMediaRelativePathError",
    "Library",
    "LibraryId",
    "LibraryPathFlavor",
    "LibraryRoot",
    "LogicalMedia",
    "MediaId",
    "MediaKind",
    "MediaLocation",
    "MediaLocationAvailability",
    "MediaLocationId",
    "MediaRelativePath",
    "SeriesId",
    "StorageVolumeId",
]
