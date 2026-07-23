"""Execute durable movie-identification analysis runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Protocol

from framenest.application.media_analysis import (
    MediaAnalysisFailedError,
    MediaAnalysisUnavailableError,
    MediaRelativePath,
)
from framenest.application.media_analysis_lifecycle import (
    CatalogedAnalysisTarget,
    MediaAnalysisLifecycleError,
    RequestManualMediaAnalysis,
)
from framenest.application.media_content import supported_media_type
from framenest.application.media_suggestion import (
    FrameNestMediaSuggestionError,
    MediaSuggestionPreparationFailedError,
    MediaSuggestionPreparationUnavailableError,
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderModelUnavailableError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderTruncatedResponseError,
    MediaSuggestionProviderUnavailableError,
    source_extension,
)
from framenest.application.movie_identification import (
    MovieIdentificationRequest,
    MovieIdentificationSuggestion,
    serialize_movie_identification_result,
)
from framenest.application.ports.library_repository import LibraryRepository
from framenest.application.ports.media_analysis_runs import (
    FrameNestMediaAnalysisRunRepositoryError,
    MediaAnalysisRunRepository,
)
from framenest.application.ports.media_repository import MediaRepository
from framenest.application.ports.movie_identification import MovieIdentificationPreparer
from framenest.application.upload_transport import default_now_ms
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media import MediaKind, MediaLocationAvailability
from framenest.domain.media_analysis_runs import (
    MediaAnalysisRun,
    MediaAnalysisRunState,
    TERMINAL_ANALYSIS_RUN_STATES,
)
from framenest.domain.media_classification import (
    AnalysisProfile,
    CONTACT_SHEET_DERIVATIVE_STRATEGY,
    MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
    MOVIE_IDENTIFICATION_RESULT_SCHEMA_VERSION,
)


class MovieIdentificationProvider(Protocol):
    def identify_movie(
        self,
        request: MovieIdentificationRequest,
    ) -> MovieIdentificationSuggestion:
        """Submit exactly one movie-identification provider request."""


@dataclass(frozen=True, slots=True)
class ExecuteMovieIdentificationRun:
    """Claim and execute one durable movie-identification analysis run."""

    repository: MediaAnalysisRunRepository
    media_repository: MediaRepository
    library_repository: LibraryRepository
    preparer: MovieIdentificationPreparer
    provider: MovieIdentificationProvider
    now_ms: Callable[[], int] = default_now_ms
    in_transaction: Callable[[], bool] | None = None

    def execute(self, run: MediaAnalysisRun) -> MediaAnalysisRun:
        if run.analysis_definition != MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION:
            raise MediaAnalysisLifecycleError("unexpected analysis definition")
        if run.state in TERMINAL_ANALYSIS_RUN_STATES:
            return run
        if run.state is not MediaAnalysisRunState.PENDING:
            return run
        claimed = self.repository.claim_pending(
            run_id=run.id.to_string(),
            expected_version=run.version,
            started_at_ms=self.now_ms(),
            max_attempts=1,
        )
        if (self.in_transaction or (lambda: False))():
            raise MediaAnalysisLifecycleError(
                "provider execution must not run inside a database transaction"
            )
        try:
            suggestion = self._identify(claimed.media_id, claimed.media_location_id)
        except Exception as exc:
            return self._persist_failure(claimed, exc)
        try:
            return self.repository.record_analyzed(
                run_id=claimed.id.to_string(),
                expected_version=claimed.version,
                provider_id=suggestion.provider_id,
                model_id=suggestion.model_id,
                prompt_version=suggestion.prompt_version,
                result_schema_version=MOVIE_IDENTIFICATION_RESULT_SCHEMA_VERSION,
                result_json=json.dumps(
                    serialize_movie_identification_result(suggestion),
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                completed_at_ms=self.now_ms(),
                analysis_profile=AnalysisProfile.MOVIE_IDENTIFICATION.value,
                reasoning_enabled=True,
                derivative_strategy=CONTACT_SHEET_DERIVATIVE_STRATEGY,
                derivative_count=1,
                provider_submission_occurred=True,
            )
        except FrameNestMediaAnalysisRunRepositoryError as exc:
            raise MediaAnalysisLifecycleError(
                "movie identification persistence failed"
            ) from exc

    def _identify(
        self,
        media_id: MediaId,
        location_id: MediaLocationId,
    ) -> MovieIdentificationSuggestion:
        media = self.media_repository.get_media(media_id)
        if media is None:
            raise MediaSuggestionPreparationUnavailableError("media unavailable")
        if media.kind is not MediaKind.VIDEO:
            raise MediaSuggestionPreparationUnavailableError("media kind unsupported")
        location = self.media_repository.get_location(location_id)
        if location is None or location.media_id != media_id:
            raise MediaSuggestionPreparationUnavailableError("location unavailable")
        if location.availability != MediaLocationAvailability.AVAILABLE:
            raise MediaSuggestionPreparationUnavailableError("location unavailable")
        library = self.library_repository.get(location.library_id)
        if library is None:
            raise MediaSuggestionPreparationUnavailableError("library unavailable")
        relative = MediaRelativePath(location.relative_path.value)
        try:
            extension = source_extension(relative)
        except FrameNestMediaSuggestionError:
            raise MediaSuggestionPreparationUnavailableError(
                "media type unsupported"
            ) from None
        if supported_media_type(media.kind, extension) is None:
            raise MediaSuggestionPreparationUnavailableError("media type unsupported")

        try:
            prepared = self.preparer.prepare(library.root, relative)
        except MediaAnalysisUnavailableError:
            raise MediaSuggestionPreparationUnavailableError(
                "movie identification preparation unavailable"
            ) from None
        except MediaAnalysisFailedError:
            raise MediaSuggestionPreparationFailedError(
                "movie identification preparation failed"
            ) from None

        request = MovieIdentificationRequest(
            basename=prepared.basename,
            contact_sheet=prepared.contact_sheet,
            hints=prepared.hints,
        )
        assert not hasattr(request, "media_path")
        return self.provider.identify_movie(request)

    def _persist_failure(
        self,
        claimed: MediaAnalysisRun,
        exc: Exception,
    ) -> MediaAnalysisRun:
        error_code, error_message = _classify_movie_failure(exc)
        try:
            return self.repository.record_failed(
                run_id=claimed.id.to_string(),
                expected_version=claimed.version,
                error_code=error_code,
                error_message=error_message,
                provider_id=None,
                model_id=None,
                prompt_version=None,
                completed_at_ms=self.now_ms(),
                provider_submission_occurred=_provider_submission_occurred(error_code),
                analysis_profile=AnalysisProfile.MOVIE_IDENTIFICATION.value,
                reasoning_enabled=True,
                derivative_strategy=CONTACT_SHEET_DERIVATIVE_STRATEGY,
                derivative_count=1,
            )
        except FrameNestMediaAnalysisRunRepositoryError as persist_exc:
            raise MediaAnalysisLifecycleError(
                "movie identification failure persistence failed"
            ) from persist_exc


def request_movie_identification(
    repository: MediaAnalysisRunRepository,
    target: CatalogedAnalysisTarget,
    *,
    now_ms: Callable[[], int] = default_now_ms,
) -> MediaAnalysisRun:
    """Explicitly request one durable movie-identification run."""
    requester = RequestManualMediaAnalysis(
        repository,
        now_ms=now_ms,
        analysis_definition=MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
    )
    return requester.execute(target)


def _classify_movie_failure(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, MediaSuggestionPreparationUnavailableError):
        return "PREPARATION_UNAVAILABLE", "Movie identification preparation unavailable."
    if isinstance(exc, MediaSuggestionPreparationFailedError):
        return "PREPARATION_FAILED", "Movie identification preparation failed."
    if isinstance(exc, MediaSuggestionProviderAuthError):
        return "PROVIDER_AUTH", "Provider authentication failed."
    if isinstance(exc, MediaSuggestionProviderRateLimitedError):
        return "PROVIDER_RATE_LIMITED", "Provider rate limited the request."
    if isinstance(exc, MediaSuggestionProviderModelUnavailableError):
        return "PROVIDER_MODEL_UNAVAILABLE", "Provider model is unavailable."
    if isinstance(exc, MediaSuggestionProviderUnavailableError):
        return "PROVIDER_UNAVAILABLE", "Provider is unavailable."
    if isinstance(exc, MediaSuggestionProviderTruncatedResponseError):
        return "PROVIDER_RESPONSE_TRUNCATED", "Provider exhausted tokens before a final answer."
    if isinstance(exc, MediaSuggestionProviderInvalidResponseError):
        return "PROVIDER_INVALID_RESPONSE", "Provider returned an invalid response."
    if isinstance(exc, MediaSuggestionProviderFailedError):
        return "PROVIDER_FAILED", "Provider request failed."
    return "ANALYSIS_FAILED", "Movie identification failed."


_PROVIDER_SUBMISSION_ERROR_CODES = frozenset(
    {
        "PROVIDER_AUTH",
        "PROVIDER_RATE_LIMITED",
        "PROVIDER_MODEL_UNAVAILABLE",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_INVALID_RESPONSE",
        "PROVIDER_RESPONSE_TRUNCATED",
        "PROVIDER_FAILED",
    }
)


def _provider_submission_occurred(error_code: str) -> bool:
    """True only when failure classification implies the provider adapter was entered."""
    return error_code in _PROVIDER_SUBMISSION_ERROR_CODES
