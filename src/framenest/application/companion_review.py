"""Administrator companion review inbox read model and historical codec."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
import base64
import hashlib
import json
import re
from typing import TYPE_CHECKING

from framenest.application.media_suggestion import (
    DESCRIPTION_MAX_LENGTH,
    TAG_MAX_COUNT,
    TAG_MAX_LENGTH,
    TAG_MIN_COUNT,
    TITLE_MAX_LENGTH,
)
from framenest.application.upload_transport import default_now_ms
from framenest.domain.content_publication import (
    ContentPublication,
    ContentPublicationReadiness,
    derive_content_publication_readiness,
)
from framenest.domain.identities import FrameNestIdentityError, MediaId

if TYPE_CHECKING:
    from framenest.application.ports.companion_review_repository import (
        CompanionReviewRepository,
    )

DEFAULT_COMPANION_REVIEW_LIMIT = 25
MAX_COMPANION_REVIEW_LIMIT = 100
HISTORICAL_STORED_TAG_MAX_COUNT = 12
COMPANION_REVIEW_QUERY_INVALID_MESSAGE = "Invalid companion review query."
COMPANION_REVIEW_RESULT_INVALID_MESSAGE = "Stored analysis result is invalid."

_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
_CURSOR_B64_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_FIELD_DISPLAY_TITLE = "display_title"
_FIELD_DESCRIPTION = "description"
_FIELD_TAGS = "tags"
ALLOWED_APPLY_FIELDS = frozenset(
    {_FIELD_DISPLAY_TITLE, _FIELD_DESCRIPTION, _FIELD_TAGS}
)


class CompanionReviewQueryError(ValueError):
    """Raised when inbox query parameters cannot be accepted."""


class CompanionReviewCodecError(ValueError):
    """Raised when stored suggestion JSON cannot be decoded for review."""


class MappedTagStatus(StrEnum):
    """Deterministic mapping outcome for one stored suggested tag."""

    MAPPED = "mapped"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"
    DUPLICATE = "duplicate"
    LEGACY_LIMIT = "legacy_limit"


@dataclass(frozen=True, slots=True)
class StoredSuggestion:
    """Historical v1 suggestion fields used by companion review reads."""

    title: str
    description: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CanonicalTagView:
    """One canonical tag definition used for deterministic mapping."""

    key: str
    display_name: str


@dataclass(frozen=True, slots=True)
class MappedSuggestedTag:
    """One stored suggested tag after canonical lookup."""

    value: str
    status: MappedTagStatus
    key: str | None
    display_name: str | None


@dataclass(frozen=True, slots=True)
class CompanionReviewInboxItem:
    """One inbox row: latest successful generic run for one media item."""

    media_id: str
    title: str
    analysis_run_id: str
    completed_at_ms: int
    unopened: bool


@dataclass(frozen=True, slots=True)
class CompanionReviewInboxPage:
    """Cursor page of inbox rows plus actor-scoped unopened total."""

    items: tuple[CompanionReviewInboxItem, ...]
    unopened_count: int
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class CompanionReviewCanonicalTag:
    """Ordered canonical tag currently stored on the media item."""

    key: str
    display_name: str
    position: int


@dataclass(frozen=True, slots=True)
class CompanionReviewFieldSource:
    """Valid field-source receipt whose digest still matches canonical state."""

    analysis_run_id: str
    completed_at_ms: int
    provider_id: str
    model_id: str
    applied_at_ms: int


@dataclass(frozen=True, slots=True)
class CompanionReviewSuggestion:
    """One successful generic run decoded for administrator history."""

    analysis_run_id: str
    completed_at_ms: int
    provider_id: str
    model_id: str
    prompt_version: str
    title: str
    description: str
    tags: tuple[MappedSuggestedTag, ...]


@dataclass(frozen=True, slots=True)
class CompanionReviewDetail:
    """Per-media canonical state, receipts, and suggestion history page."""

    media_id: str
    display_title: str | None
    description: str | None
    tags: tuple[CompanionReviewCanonicalTag, ...]
    field_sources: dict[str, CompanionReviewFieldSource | None]
    publication: ContentPublication | None
    readiness: ContentPublicationReadiness
    suggestions: tuple[CompanionReviewSuggestion, ...]
    next_cursor: str | None


def decode_stored_suggestion_result(result_json: str) -> StoredSuggestion:
    """Decode durable v1 suggestion JSON without the live v4 validator."""
    if not isinstance(result_json, str) or not result_json:
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    try:
        payload = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise CompanionReviewCodecError(
            COMPANION_REVIEW_RESULT_INVALID_MESSAGE
        ) from exc
    if not isinstance(payload, dict):
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    title = _validate_stored_text(
        payload.get("title"),
        minimum=1,
        maximum=TITLE_MAX_LENGTH,
    )
    description = _validate_stored_text(
        payload.get("description"),
        minimum=1,
        maximum=DESCRIPTION_MAX_LENGTH,
    )
    tags = _validate_stored_tags(payload.get("tags"))
    return StoredSuggestion(title=title, description=description, tags=tags)


def map_suggested_tags(
    suggested: tuple[str, ...],
    canonical: tuple[CanonicalTagView, ...],
) -> tuple[MappedSuggestedTag, ...]:
    """Map stored suggestion tags onto existing canonical tags only."""
    display_index: dict[str, list[CanonicalTagView]] = {}
    key_index: dict[str, list[CanonicalTagView]] = {}
    for tag in canonical:
        display_index.setdefault(tag.display_name.casefold(), []).append(tag)
        key_index.setdefault(tag.key.casefold(), []).append(tag)

    mapped_keys: set[str] = set()
    mapped_count = 0
    mapped: list[MappedSuggestedTag] = []
    for raw in suggested:
        trimmed = raw.strip()
        folded = trimmed.casefold()
        display_matches = display_index.get(folded, [])
        if len(display_matches) > 1:
            mapped.append(
                MappedSuggestedTag(
                    value=raw,
                    status=MappedTagStatus.AMBIGUOUS,
                    key=None,
                    display_name=None,
                )
            )
            continue
        chosen: CanonicalTagView | None
        if len(display_matches) == 1:
            chosen = display_matches[0]
        else:
            key_matches = key_index.get(folded, [])
            if len(key_matches) > 1:
                mapped.append(
                    MappedSuggestedTag(
                        value=raw,
                        status=MappedTagStatus.AMBIGUOUS,
                        key=None,
                        display_name=None,
                    )
                )
                continue
            if len(key_matches) != 1:
                mapped.append(
                    MappedSuggestedTag(
                        value=raw,
                        status=MappedTagStatus.UNKNOWN,
                        key=None,
                        display_name=None,
                    )
                )
                continue
            chosen = key_matches[0]
        if chosen.key in mapped_keys:
            mapped.append(
                MappedSuggestedTag(
                    value=raw,
                    status=MappedTagStatus.DUPLICATE,
                    key=chosen.key,
                    display_name=chosen.display_name,
                )
            )
            continue
        mapped_keys.add(chosen.key)
        if mapped_count >= TAG_MAX_COUNT:
            mapped.append(
                MappedSuggestedTag(
                    value=raw,
                    status=MappedTagStatus.LEGACY_LIMIT,
                    key=chosen.key,
                    display_name=chosen.display_name,
                )
            )
            continue
        mapped_count += 1
        mapped.append(
            MappedSuggestedTag(
                value=raw,
                status=MappedTagStatus.MAPPED,
                key=chosen.key,
                display_name=chosen.display_name,
            )
        )
    return tuple(mapped)


def canonical_field_digest(field_name: str, value: object) -> str:
    """Return SHA-256 hex of UTF-8 canonical JSON for one receipt field."""
    if field_name in {_FIELD_DISPLAY_TITLE, _FIELD_DESCRIPTION}:
        payload: object = value
    elif field_name == _FIELD_TAGS:
        payload = list(value)
    else:
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def encode_companion_review_cursor(*, completed_at_ms: int, analysis_run_id: str) -> str:
    """Encode the opaque keyset cursor as canonical base64url JSON."""
    payload = json.dumps(
        {"completed_at_ms": completed_at_ms, "id": analysis_run_id},
        separators=(",", ":"),
        sort_keys=True,
    )
    return (
        base64.urlsafe_b64encode(payload.encode("ascii"))
        .decode("ascii")
        .rstrip("=")
    )


def decode_companion_review_cursor(value: str | None) -> tuple[int, str] | None:
    """Parse the opaque keyset cursor or raise for malformed input."""
    if value is None:
        return None
    if not isinstance(value, str) or not value or not _CURSOR_B64_PATTERN.fullmatch(
        value
    ):
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(raw.decode("ascii"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CompanionReviewQueryError(
            COMPANION_REVIEW_QUERY_INVALID_MESSAGE
        ) from exc
    if not isinstance(payload, dict) or set(payload) != {"completed_at_ms", "id"}:
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    completed_at_ms = payload["completed_at_ms"]
    analysis_run_id = payload["id"]
    if (
        isinstance(completed_at_ms, bool)
        or not isinstance(completed_at_ms, int)
        or completed_at_ms < 0
    ):
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    if not isinstance(analysis_run_id, str):
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    try:
        MediaId.from_string(analysis_run_id)
    except FrameNestIdentityError as exc:
        raise CompanionReviewQueryError(
            COMPANION_REVIEW_QUERY_INVALID_MESSAGE
        ) from exc
    return completed_at_ms, analysis_run_id


def validate_companion_review_limit(value: int) -> int:
    """Accept a bounded inbox/history page size."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > MAX_COMPANION_REVIEW_LIMIT
    ):
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    return value


def inbox_title(*, canonical_display_title: str | None, stored: StoredSuggestion) -> str:
    """Prefer current non-blank canonical title, else the stored suggestion title."""
    if isinstance(canonical_display_title, str) and canonical_display_title.strip():
        return canonical_display_title
    return stored.title


@dataclass(frozen=True, slots=True)
class ListCompanionReviewInbox:
    """List the latest successful generic run per in-scope media item."""

    repository: CompanionReviewRepository

    def execute(
        self,
        *,
        actor_login_key: str,
        limit: int = DEFAULT_COMPANION_REVIEW_LIMIT,
        cursor: str | None = None,
    ) -> CompanionReviewInboxPage:
        if not isinstance(actor_login_key, str) or not actor_login_key:
            raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
        return self.repository.list_inbox(
            actor_login_key=actor_login_key,
            limit=validate_companion_review_limit(limit),
            cursor=decode_companion_review_cursor(cursor),
        )


@dataclass(frozen=True, slots=True)
class GetCompanionReviewDetail:
    """Load canonical state and paginated successful generic history."""

    repository: CompanionReviewRepository

    def execute(
        self,
        *,
        media_id: str,
        actor_login_key: str,
        limit: int = DEFAULT_COMPANION_REVIEW_LIMIT,
        cursor: str | None = None,
    ) -> CompanionReviewDetail:
        if not isinstance(actor_login_key, str) or not actor_login_key:
            raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
        try:
            parsed_media_id = MediaId.from_string(media_id)
        except FrameNestIdentityError as exc:
            from framenest.application.ports.companion_review_repository import (
                CompanionReviewMediaNotFoundError,
            )

            raise CompanionReviewMediaNotFoundError(
                "The requested media item was not found."
            ) from exc
        return self.repository.get_detail(
            media_id=parsed_media_id,
            actor_login_key=actor_login_key,
            limit=validate_companion_review_limit(limit),
            cursor=decode_companion_review_cursor(cursor),
        )


@dataclass(frozen=True, slots=True)
class CompanionReviewOpenedResult:
    """Post-state of one monotonic opened write."""

    media_id: str
    opened_run_id: str
    opened_at_ms: int
    unopened: bool


@dataclass(frozen=True, slots=True)
class CompanionReviewApplyCanonical:
    """Canonical values and matching receipts after one apply transaction."""

    display_title: str | None
    description: str | None
    tags: tuple[CompanionReviewCanonicalTag, ...]
    field_sources: dict[str, CompanionReviewFieldSource | None]


@dataclass(frozen=True, slots=True)
class CompanionReviewApplyPublication:
    """Publication outcome of one companion apply transaction."""

    status: str
    state: str
    origin: str | None
    published_at_ms: int | None
    ready: bool
    missing_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompanionReviewApplyResult:
    """Metadata, receipt, and publication outcome of one apply transaction."""

    metadata_status: str
    canonical: CompanionReviewApplyCanonical
    publication: CompanionReviewApplyPublication


def eligible_mapped_tag_keys(
    mapped: tuple[MappedSuggestedTag, ...],
) -> tuple[str, ...]:
    """Return mapped keys in suggestion order, excluding non-selectable statuses."""
    return tuple(
        tag.key
        for tag in mapped
        if tag.status is MappedTagStatus.MAPPED and tag.key is not None
    )


def is_ordered_subsequence(submitted: tuple[str, ...], eligible: tuple[str, ...]) -> bool:
    """Return True when submitted keys appear in order inside eligible keys."""
    index = 0
    for key in submitted:
        found = False
        while index < len(eligible):
            if eligible[index] == key:
                found = True
                index += 1
                break
            index += 1
        if not found:
            return False
    return True


def validate_companion_review_apply_request(
    *,
    fields: tuple[str, ...],
    tag_keys: tuple[str, ...],
) -> None:
    """Reject empty, duplicate, or inconsistent apply field/tag selections."""
    if not fields or len(set(fields)) != len(fields):
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    if not set(fields) <= ALLOWED_APPLY_FIELDS:
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    tags_selected = _FIELD_TAGS in fields
    if tags_selected:
        if (
            not tag_keys
            or len(tag_keys) > TAG_MAX_COUNT
            or len(set(tag_keys)) != len(tag_keys)
            or any(not isinstance(key, str) or not key for key in tag_keys)
        ):
            raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
        return
    if tag_keys:
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)


def _parse_media_id(value: str) -> MediaId:
    try:
        return MediaId.from_string(value)
    except FrameNestIdentityError as exc:
        from framenest.application.ports.companion_review_repository import (
            CompanionReviewMediaNotFoundError,
        )

        raise CompanionReviewMediaNotFoundError(
            "The requested media item was not found."
        ) from exc


def _parse_analysis_run_id(value: str) -> MediaId:
    try:
        return MediaId.from_string(value)
    except FrameNestIdentityError as exc:
        from framenest.application.ports.companion_review_repository import (
            CompanionReviewAnalysisRunNotFoundError,
        )

        raise CompanionReviewAnalysisRunNotFoundError(
            "The requested analysis run was not found."
        ) from exc


def _require_actor_login_key(actor_login_key: str) -> str:
    if not isinstance(actor_login_key, str) or not actor_login_key:
        raise CompanionReviewQueryError(COMPANION_REVIEW_QUERY_INVALID_MESSAGE)
    return actor_login_key


@dataclass(frozen=True, slots=True)
class MarkCompanionReviewOpened:
    """Mark one displayed successful generic run as opened for one actor."""

    repository: CompanionReviewRepository
    now_ms: Callable[[], int] = default_now_ms

    def execute(
        self,
        *,
        media_id: str,
        actor_login_key: str,
        analysis_run_id: str,
    ) -> CompanionReviewOpenedResult:
        return self.repository.mark_opened(
            media_id=_parse_media_id(media_id),
            actor_login_key=_require_actor_login_key(actor_login_key),
            analysis_run_id=_parse_analysis_run_id(analysis_run_id),
            now_ms=self.now_ms(),
        )


@dataclass(frozen=True, slots=True)
class ApplyCompanionReview:
    """Apply selected stored-run fields, upsert receipts, and publish when ready."""

    repository: CompanionReviewRepository
    now_ms: Callable[[], int] = default_now_ms

    def execute(
        self,
        *,
        media_id: str,
        actor_login_key: str,
        analysis_run_id: str,
        fields: tuple[str, ...],
        tag_keys: tuple[str, ...],
    ) -> CompanionReviewApplyResult:
        validate_companion_review_apply_request(fields=fields, tag_keys=tag_keys)
        return self.repository.apply_review(
            media_id=_parse_media_id(media_id),
            actor_login_key=_require_actor_login_key(actor_login_key),
            analysis_run_id=_parse_analysis_run_id(analysis_run_id),
            fields=fields,
            tag_keys=tag_keys,
            now_ms=self.now_ms(),
        )


def derive_review_readiness(
    *,
    display_title: str | None,
    description: str | None,
    tag_count: int,
) -> ContentPublicationReadiness:
    """Expose existing readiness derivation for review detail."""
    return derive_content_publication_readiness(
        display_title=display_title,
        description=description,
        canonical_tag_count=tag_count,
    )


def _validate_stored_text(value: object, *, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    if len(value) < minimum or len(value) > maximum:
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    if value.strip() != value:
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    if _CONTROL_CHAR_PATTERN.search(value):
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    return value


def _validate_stored_tags(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    if len(value) < TAG_MIN_COUNT or len(value) > HISTORICAL_STORED_TAG_MAX_COUNT:
        raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _validate_stored_text(
            item, minimum=1, maximum=TAG_MAX_LENGTH
        )
        folded = text.casefold()
        if folded in seen:
            raise CompanionReviewCodecError(COMPANION_REVIEW_RESULT_INVALID_MESSAGE)
        seen.add(folded)
        normalized.append(text)
    return tuple(normalized)
