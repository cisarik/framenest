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
from framenest.domain.media_metadata import (
    CanonicalTag,
    CanonicalTagDisplayName,
    CanonicalTagKey,
    FrameNestMediaMetadataError,
    MediaDescription,
    MediaDisplayTitle,
    MediaMetadata,
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
    "FrameNestMediaMetadataError",
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
    "CanonicalTag",
    "CanonicalTagDisplayName",
    "CanonicalTagKey",
    "MediaDescription",
    "MediaDisplayTitle",
    "MediaMetadata",
    "SeriesId",
    "StorageVolumeId",
]
