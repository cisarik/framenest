"""Application use cases for caller-private media alias overlays."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Protocol

from framenest.application.ports.media_user_alias_repository import (
    AliasTagNotFoundError,
    FrameNestMediaUserAliasRepositoryError,
    MediaUserAliasMediaNotFoundError,
    MediaUserAliasRepository,
)
from framenest.domain import MediaId
from framenest.domain.media_user_alias import (
    FrameNestMediaUserAliasError,
    MediaUserAlias,
    MediaUserAliasContent,
    parse_alias_content,
)
from framenest.domain.x_acquisition import XPostClaimId

MEDIA_USER_ALIAS_OPERATION_FAILED_MESSAGE = "Media user alias operation failed."


class ClockMs(Protocol):
    """Callable source of non-negative millisecond timestamps."""

    def __call__(self) -> int:
        """Return current timestamp in milliseconds."""


@dataclass(frozen=True, slots=True)
class MediaUserAliasView:
    """Caller-private overlay projection. Empty when no row exists."""

    display_title: str | None
    description: str | None
    tag_keys: tuple[str, ...]
    persisted: bool
    created_at_ms: int | None = None
    updated_at_ms: int | None = None


EMPTY_ALIAS_VIEW = MediaUserAliasView(
    display_title=None,
    description=None,
    tag_keys=(),
    persisted=False,
)


@dataclass(frozen=True, slots=True)
class TeamAliasEntry:
    """Administrator team-alias projection for one mapped login."""

    login_key: str
    display_title: str | None
    description: str | None
    tag_keys: tuple[str, ...]
    created_at_ms: int
    updated_at_ms: int


class GetMediaUserAlias:
    """Load the caller's overlay for one logical media item."""

    def __init__(self, repository: MediaUserAliasRepository) -> None:
        self._repository = repository

    def execute(self, media_id: str, login_key: str) -> MediaUserAliasView:
        alias = self._repository.get_alias(MediaId.from_string(media_id), login_key)
        return _view_from_alias(alias)


class ListTeamMediaAliases:
    """Read-only aggregation of every overlay for one media item."""

    def __init__(self, repository: MediaUserAliasRepository) -> None:
        self._repository = repository

    def execute(self, media_id: str) -> tuple[TeamAliasEntry, ...]:
        aliases = self._repository.list_aliases_for_media(MediaId.from_string(media_id))
        return tuple(_team_entry_from_alias(alias) for alias in aliases)


class SaveMediaUserAlias:
    """Replace or delete the caller's overlay for one logical media item."""

    def __init__(
        self,
        repository: MediaUserAliasRepository,
        *,
        clock_ms: ClockMs | None = None,
    ) -> None:
        self._repository = repository
        self._clock_ms = clock_ms if clock_ms is not None else _utc_now_ms

    def execute(
        self,
        media_id: str,
        login_key: str,
        display_title: str | None,
        description: str | None,
        tag_keys: list[str] | None,
    ) -> MediaUserAliasView:
        content = parse_alias_content(display_title, description, tag_keys)
        if not content.is_empty() and not self._repository.canonical_tag_keys_exist(
            content.tag_keys
        ):
            raise AliasTagNotFoundError()
        alias = self._repository.upsert_alias(
            MediaId.from_string(media_id),
            login_key,
            content,
            _call_clock_ms(self._clock_ms),
        )
        return _view_from_alias(alias)


def apply_alias_content_to_media(
    repository: MediaUserAliasRepository,
    *,
    media_id: MediaId,
    login_key: str,
    content: MediaUserAliasContent,
    now_ms: int,
) -> MediaUserAlias | None:
    """Upsert overlay from already-validated pending content."""
    if not content.is_empty() and not repository.canonical_tag_keys_exist(content.tag_keys):
        raise AliasTagNotFoundError()
    return repository.upsert_alias(media_id, login_key, content, now_ms)


def _team_entry_from_alias(alias: MediaUserAlias) -> TeamAliasEntry:
    return TeamAliasEntry(
        login_key=alias.login_key,
        display_title=None
        if alias.content.display_title is None
        else alias.content.display_title.value,
        description=None
        if alias.content.description is None
        else alias.content.description.value,
        tag_keys=tuple(key.value for key in alias.content.tag_keys),
        created_at_ms=alias.created_at_ms,
        updated_at_ms=alias.updated_at_ms,
    )


def _view_from_alias(alias: MediaUserAlias | None) -> MediaUserAliasView:
    if alias is None:
        return EMPTY_ALIAS_VIEW
    return MediaUserAliasView(
        display_title=None
        if alias.content.display_title is None
        else alias.content.display_title.value,
        description=None
        if alias.content.description is None
        else alias.content.description.value,
        tag_keys=tuple(key.value for key in alias.content.tag_keys),
        persisted=True,
        created_at_ms=alias.created_at_ms,
        updated_at_ms=alias.updated_at_ms,
    )


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


def _call_clock_ms(clock_ms: ClockMs) -> int:
    value = clock_ms()
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FrameNestMediaUserAliasRepositoryError(MEDIA_USER_ALIAS_OPERATION_FAILED_MESSAGE)
    return value


__all__ = [
    "EMPTY_ALIAS_VIEW",
    "AliasTagNotFoundError",
    "ClockMs",
    "FrameNestMediaUserAliasError",
    "FrameNestMediaUserAliasRepositoryError",
    "GetMediaUserAlias",
    "ListTeamMediaAliases",
    "MediaUserAliasMediaNotFoundError",
    "MediaUserAliasView",
    "SaveMediaUserAlias",
    "TeamAliasEntry",
    "apply_alias_content_to_media",
]
