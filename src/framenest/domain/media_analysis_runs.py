"""Domain types for durable automatic media analysis runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from framenest.domain.identities import MediaId, MediaLocationId


class MediaAnalysisRunState(str, Enum):
    """Persisted lifecycle states for one automatic analysis run."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION = "automatic_post_catalog"
RESULT_SCHEMA_VERSION = "framenest-media-suggestion-result-v1"
DEFAULT_MAX_ANALYSIS_ATTEMPTS = 3
MAX_CONFIGURED_ANALYSIS_ATTEMPTS = 10

ACTIVE_ANALYSIS_RUN_STATES = frozenset(
    {
        MediaAnalysisRunState.PENDING,
        MediaAnalysisRunState.ANALYZING,
    }
)
TERMINAL_ANALYSIS_RUN_STATES = frozenset(
    {
        MediaAnalysisRunState.ANALYZED,
        MediaAnalysisRunState.FAILED,
    }
)


@dataclass(frozen=True, slots=True)
class MediaAnalysisRunId:
    """Opaque durable identity for one analysis run."""

    value: str

    def to_string(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MediaAnalysisRun:
    """One durable automatic analysis lifecycle record."""

    id: MediaAnalysisRunId
    media_id: MediaId
    media_location_id: MediaLocationId
    analysis_definition: str
    state: MediaAnalysisRunState
    attempt_count: int
    provider_id: str | None
    model_id: str | None
    prompt_version: str | None
    result_schema_version: str | None
    result_json: str | None
    error_code: str | None
    error_message: str | None
    created_at_ms: int
    started_at_ms: int | None
    completed_at_ms: int | None
    version: int
