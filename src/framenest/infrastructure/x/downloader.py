"""X-specific yt-dlp adapter with a bounded, normalized extractor contract.

The adapter never exposes raw yt-dlp structures. It inspects one validated X
post and downloads supported assets into claim-owned staging using only an
argument-vector subprocess with `--ignore-config`, a controlled environment, a
bounded working directory and strict timeout and process-group termination.

Mapping is aligned to the exact pinned extractor: ``yt-dlp==2026.7.4``
(``.venv/lib/python3.13/site-packages/yt_dlp/extractor/twitter.py``).

Verified upstream TwitterIE contract:

* ``id`` is the media id; ``display_id``/top-level ``id`` are the tweet id;
* ``channel_id`` is the stable numeric user id (``user_id_str``);
* ``uploader_id`` is the ``screen_name`` (handle);
* ``uploader`` is the display name;
* ``description`` is the tweet text; ``timestamp`` is the posted time;
* a single video returns one merged info dict with ``formats``/``duration``;
* multiple videos return a ``playlist_result`` with ``_type == 'playlist'``
  and an ordered ``entries`` list — the adapter preserves entry order and
  never passes ``--no-playlist`` (which would discard valid attached assets);
* photo media is filtered by the extractor (``m['type'] != 'photo'``), so the
  pinned extractor does not emit static still-image entries; photo-only posts
  surface the typed terminal failure ``X_NO_SUPPORTED_MEDIA``;
* an animated-GIF-like post is delivered as a short MP4 video entry and is
  treated as video unless a GIF marker is present.

First-release production capability: X native video and animated-GIF-as-video
only. Static X photo acquisition is deferred and NOT part of this adapter's
real contract, because the pinned extractor does not expose ordinary photo
entries through the selected contract. The normalized domain model retains the
``XMediaType.IMAGE`` type for internal/fake-fixture use, but a production
adapter result never normalizes to it.

The configured command never uses cookies, ``.netrc``, browser-cookie
extraction, arbitrary plugin/config discovery, or requester-supplied shell
interpolation. It is testable with a fake executable emitting local synthetic
JSON without any contact with X.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

from framenest.application.ports.x_extractor import (
    XAssetAcquisition,
    XExtractionError,
    XRequiresAuthenticationError,
    XStagingStorage,
)
from framenest.domain.x_acquisition import (
    MAX_ASSETS_PER_POST,
    MAX_VIDEO_DURATION_SECONDS,
    XMediaType,
    XNormalizedAssetDescriptor,
    XNormalizedInspection,
    accept_x_post_url,
)

DEFAULT_INSPECT_TIMEOUT_SECONDS = 60
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 600
DEFAULT_SOCKET_TIMEOUT_SECONDS = 30
MAX_STDOUT_BYTES = 4_194_304
TERMINATE_GRACE_SECONDS = 5

_SUPPORTED_MIME_BY_TYPE = {
    XMediaType.VIDEO: "video/mp4",
    XMediaType.ANIMATED_GIF: "video/mp4",
    XMediaType.IMAGE: "image/jpeg",
}


class YtDlpXExtractor:
    """Run yt-dlp under an argument-only, config-free, bounded subprocess."""

    def __init__(
        self,
        staging: XStagingStorage | None = None,
        *,
        executable: str = "yt-dlp",
        inspect_timeout_seconds: float = DEFAULT_INSPECT_TIMEOUT_SECONDS,
        download_timeout_seconds: float = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
        socket_timeout_seconds: float = DEFAULT_SOCKET_TIMEOUT_SECONDS,
        working_directory: Path | None = None,
        max_assets: int = MAX_ASSETS_PER_POST,
    ) -> None:
        self._staging = staging
        self._executable = executable
        self._inspect_timeout_seconds = inspect_timeout_seconds
        self._download_timeout_seconds = download_timeout_seconds
        self._socket_timeout_seconds = socket_timeout_seconds
        self._working_directory = working_directory
        self._max_assets = max_assets

    def attest_version(self) -> str | None:
        try:
            completed = subprocess.run(
                [self._executable, "--version"],
                capture_output=True,
                timeout=self._inspect_timeout_seconds,
                env=_subprocess_environment(),
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        first = completed.stdout.splitlines()[0] if completed.stdout else b""
        return first.decode("utf-8", "replace").strip()[:64] or None

    def inspect(
        self,
        *,
        post_id: str,
        submitted_url: str,
    ) -> XNormalizedInspection:
        identity = accept_x_post_url(submitted_url)
        if identity.post_id != post_id:
            raise XExtractionError("X_URL_INVALID_POST_ID", "Invalid X post identity.")
        argv = [
            self._executable,
            "--ignore-config",
            "--no-warnings",
            "--dump-single-json",
            "--skip-download",
            "--no-progress",
            "--socket-timeout",
            str(int(self._socket_timeout_seconds)),
            "--",
            submitted_url,
        ]
        completed = _run_bounded(argv, timeout=self._inspect_timeout_seconds)
        if completed.timed_out:
            raise XExtractionError("X_DOWNLOAD_TIMEOUT", "X extraction timed out.")
        if completed.returncode != 0:
            raise _extraction_from_exit(completed.returncode)
        try:
            raw = json.loads(completed.stdout)
        except (ValueError, TypeError) as exc:
            raise XExtractionError(
                "X_EXTRACTOR_MALFORMED", "X extractor returned malformed JSON."
            ) from exc
        return _normalize_inspection(raw, identity, self._max_assets)

    def download(
        self,
        *,
        post_id: str,
        ordinal: int,
        media_type: str,
        expected_mime: str,
        source_media_key: str | None,
        stage_key: str,
        staging: XStagingStorage,
    ) -> XAssetAcquisition:
        if self._staging is not None:
            staging = self._staging
        directory = staging.prepare(stage_key)
        argv = [
            self._executable,
            "--ignore-config",
            "--no-warnings",
            "--no-progress",
            "--no-overwrites",
            "--output",
            "artifact.mp4",
            "--socket-timeout",
            str(int(self._socket_timeout_seconds)),
        ]
        if source_media_key:
            argv += ["--", source_media_key]
        completed = _run_bounded(
            argv,
            timeout=self._download_timeout_seconds,
            cwd=_to_path(directory),
        )
        if completed.timed_out:
            raise XExtractionError("X_DOWNLOAD_TIMEOUT", "X download timed out.")
        if completed.returncode != 0:
            raise _extraction_from_exit(completed.returncode)
        artifact = _find_artifact(directory)
        if artifact is None:
            raise XExtractionError("X_STAGING_FAILED", "X produced no artifact.")
        size_bytes = os.path.getsize(artifact)
        if size_bytes <= 0:
            raise XExtractionError("X_MEDIA_TYPE_UNSUPPORTED", "X artifact is empty.")
        digest = hashlib.sha256()
        with open(artifact, "rb") as handle:
            while True:
                block = handle.read(1_048_576)
                if not block:
                    break
                digest.update(block)
        return XAssetAcquisition(size_bytes=size_bytes, sha256=digest.hexdigest())


def _normalize_inspection(
    raw: object,
    identity: object,
    max_assets: int,
) -> XNormalizedInspection:
    if not isinstance(raw, dict):
        raise XExtractionError("X_EXTRACTOR_MALFORMED", "X extractor is malformed.")
    if raw.get("availability") in {"needs_auth", "private", "members_only"} or raw.get(
        "is_live"
    ):
        code = "X_AUTHENTICATION_REQUIRED" if raw.get("availability") in {"needs_auth", "members_only"} else "X_POST_UNAVAILABLE"
        raise XExtractionError(code, "X post is not publicly available.")
    description = _clean_text(raw.get("description"))
    entries = raw.get("entries")
    if isinstance(entries, list) and entries:
        assets = _assets_from_entries(entries)
    else:
        assets = _assets_from_single(raw)
    if len(assets) > max_assets:
        raise XExtractionError("X_TOO_MANY_ASSETS", "X post exceeds asset limit.")
    if not assets:
        raise XExtractionError("X_NO_SUPPORTED_MEDIA", "X post has no media.")
    canonical_url = raw.get("webpage_url")
    canonical_url = _validated_canonical(canonical_url, identity)
    # Real TwitterIE contract: `channel_id` is the stable numeric user id,
    # `uploader_id` is the screen_name (handle), `uploader` is the display name.
    author_stable_id = _clean_text(raw.get("channel_id")) or _clean_text(
        raw.get("user_id")
    )
    author_handle = _clean_text(raw.get("uploader_id"))
    author_display_name = _clean_text(raw.get("uploader"))
    posted_at = raw.get("timestamp")
    posted_at_ms = None
    if isinstance(posted_at, (int, float)) and not isinstance(posted_at, bool):
        posted_at_ms = int(posted_at * 1000)
    return XNormalizedInspection(
        post_id=identity.post_id,
        canonical_url=canonical_url,
        post_text=description,
        posted_at_ms=posted_at_ms,
        author_stable_id=author_stable_id,
        author_handle=author_handle,
        author_display_name=author_display_name,
        assets=tuple(assets),
        extractor_version=_clean_text(raw.get("extractor_version")),
    )


def _assets_from_single(raw: dict) -> list[XNormalizedAssetDescriptor]:
    media_type = _media_type_from_raw(raw)
    if media_type is None:
        return []
    duration = raw.get("duration")
    duration_seconds = None
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        duration_seconds = int(duration)
        if duration_seconds > MAX_VIDEO_DURATION_SECONDS:
            raise XExtractionError(
                "X_DURATION_TOO_LONG", "X media exceeds duration limit."
            )
    width = raw.get("width")
    height = raw.get("height")
    source_media_key = _clean_text(raw.get("id"))
    return [
        XNormalizedAssetDescriptor(
            ordinal=0,
            media_type=media_type,
            expected_mime=_SUPPORTED_MIME_BY_TYPE[media_type],
            source_media_key=source_media_key,
            width=_bounded_dim(width),
            height=_bounded_dim(height),
            duration_seconds=duration_seconds,
        )
    ]


def _assets_from_entries(entries: list[object]) -> list[XNormalizedAssetDescriptor]:
    descriptors: list[XNormalizedAssetDescriptor] = []
    for offset, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        media_type = _media_type_from_raw(entry)
        if media_type is None:
            continue
        duration = entry.get("duration")
        duration_seconds = None
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            duration_seconds = int(duration)
            if duration_seconds > MAX_VIDEO_DURATION_SECONDS:
                raise XExtractionError(
                    "X_DURATION_TOO_LONG", "X media exceeds duration limit."
                )
        descriptors.append(
            XNormalizedAssetDescriptor(
                ordinal=len(descriptors),
                media_type=media_type,
                expected_mime=_SUPPORTED_MIME_BY_TYPE[media_type],
                source_media_key=_clean_text(entry.get("id")),
                width=_bounded_dim(entry.get("width")),
                height=_bounded_dim(entry.get("height")),
                duration_seconds=duration_seconds,
            )
        )
    return descriptors


def _media_type_from_raw(raw: dict) -> XMediaType | None:
    """Classify an entry emitted by the pinned yt-dlp Twitter extractor.

    The production adapter's real capability is video / animated-GIF-as-video
    only. The pinned TwitterIE filters ``type == 'photo'`` and never emits
    ordinary static photo entries through this contract. A remaining still-image
    marker (e.g. ``ext == 'png'``) is therefore not a supported production
    asset: it returns ``None`` so a photo-only post yields no supported assets
    and terminates through ``X_NO_SUPPORTED_MEDIA``.
    """
    ext = str(raw.get("ext") or "").lower()
    extname = str(raw.get("_filename") or "").lower()
    formats = raw.get("formats")
    has_formats = isinstance(formats, list) and len(formats) > 0
    duration = raw.get("duration")
    has_duration = isinstance(duration, (int, float)) and not isinstance(
        duration, bool
    )
    url = str(raw.get("url") or "")
    if ext == "gif" or extname.endswith(".gif"):
        return XMediaType.ANIMATED_GIF
    if has_formats or has_duration or re.search(r"\.(mp4|m4v|mov|webm|m3u8)(\?|$)", url):
        return XMediaType.VIDEO
    # Static photo markers are not a first-release production X capability.
    return None


def _is_visual(format: dict) -> bool:
    return (
        format.get("vcodec") not in {None, "none"}
        and format.get("resolution") not in {None, "audio only"}
    )



def _validated_canonical(value: object, identity: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        validated = accept_x_post_url(value)
        if validated.post_id == identity.post_id:
            return validated.canonical_url
    except Exception:
        return None
    return None


def _bounded_dim(value: object) -> int | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if value > 100_000 or value < 0:
        raise XExtractionError("X_DIMENSIONS_TOO_LARGE", "X dimensions are invalid.")
    return int(value)


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned[:500] if cleaned else None


def _extraction_from_exit(returncode: int) -> XExtractionError:
    if returncode == -9:
        return XExtractionError("X_DOWNLOAD_TIMEOUT", "X download killed.")
    if returncode in {1, 2}:
        return XExtractionError("X_EXTRACTOR_FAILED", "X extraction failed.")
    return XExtractionError("X_EXTRACTOR_FAILED", "X extraction failed.")


def _subprocess_environment() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "NO_COLOR": "1",
    }


class _BoundedCompleted:
    __slots__ = ("stdout", "stderr", "returncode", "timed_out")

    def __init__(self, stdout: bytes, stderr: bytes, returncode: int, timed_out: bool):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timed_out = timed_out


def _run_bounded(
    argv: list[str],
    *,
    timeout: float,
    cwd: Path | None = None,
) -> _BoundedCompleted:
    try:
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd is not None else None,
            env=_subprocess_environment(),
            start_new_session=True,
        )
    except OSError as exc:
        raise XExtractionError("X_EXTRACTOR_UNAVAILABLE", "X extractor is unavailable.") from exc
    timed_out = False
    try:
        _out, _err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_group(process)
        try:
            _out, _err = process.communicate(timeout=TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            _out, _err = process.communicate()
    if _out is not None and len(_out) > MAX_STDOUT_BYTES:
        raise XExtractionError("X_EXTRACTOR_FAILED", "X extractor output overflowed.")
    return _BoundedCompleted(
        stdout=_out or b"",
        stderr=_err or b"",
        returncode=process.returncode,
        timed_out=timed_out,
    )


def _terminate_process_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(process.pid), 15)
    except (ProcessLookupError, OSError):
        try:
            process.terminate()
        except OSError:
            pass


def _find_artifact(directory: Path) -> Path | None:
    candidates = sorted(
        path for path in (Path(directory).iterdir() if directory.is_dir() else [])
        if path.is_file() and re.search(r"\.(mp4|jpg|jpeg|png|webm|gif)$", path.name)
    )
    return candidates[0] if candidates else None


def _to_path(value: object) -> Path:
    return Path(value) if isinstance(value, (str, Path)) else Path(str(value))