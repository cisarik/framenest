"""Pure-domain evidence for YouTube manual-acquisition policy."""

from __future__ import annotations

import pytest

from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.uploads import UploadSessionId
from framenest.domain.youtube_acquisition import (
    FrameNestYouTubeClaimError,
    FrameNestYouTubeTransitionError,
    FrameNestYouTubeUrlError,
    YouTubeAcquisitionClaim,
    YouTubeAcquisitionState,
    YouTubeConfirmationMethod,
    YouTubeFailureStage,
    canonicalize_youtube_url,
)

VIDEO_ID = "AbCdEf123_-"


@pytest.mark.parametrize(
    "submitted",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}&t=12",
        f"https://m.youtube.com/shorts/{VIDEO_ID}?si=synthetic",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}/?t=1",
    ],
)
def test_supported_url_variants_converge_on_one_identity(submitted: str) -> None:
    identity = canonicalize_youtube_url(submitted)

    assert identity.video_id == VIDEO_ID
    assert identity.canonical_url == (
        f"https://www.youtube.com/watch?v={VIDEO_ID}"
    )
    assert identity.extractor_key == "Youtube"


@pytest.mark.parametrize(
    "submitted",
    [
        f"http://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://user@www.youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com:444/watch?v={VIDEO_ID}",
        f"https://evil.example/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PL123",
        f"https://www.youtube.com/channel/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&v=Other123456",
        "https://youtu.be/not-an-id",
        f"https://www.youtube.com/watch?v={VIDEO_ID}#fragment",
    ],
)
def test_url_policy_rejects_non_single_public_video_targets(
    submitted: str,
) -> None:
    with pytest.raises(
        FrameNestYouTubeUrlError,
        match="Invalid public YouTube video URL",
    ):
        canonicalize_youtube_url(submitted)


def test_claim_lifecycle_carries_durable_provenance_to_catalog() -> None:
    claim = YouTubeAcquisitionClaim.new(
        submitted_url=f"https://youtu.be/{VIDEO_ID}",
        confirmation_method=YouTubeConfirmationMethod.YES_FLAG,
        now_ms=10,
    )
    inspecting = claim.advance(
        YouTubeAcquisitionState.INSPECTING,
        updated_at_ms=11,
    )
    pending = inspecting.advance(
        YouTubeAcquisitionState.DOWNLOAD_PENDING,
        updated_at_ms=12,
        upstream_title="Synthetic title",
        upstream_channel="Synthetic channel",
        upstream_channel_id="channel-id",
        upstream_source_date="2026-01-02",
        downloader_name="yt-dlp",
        downloader_version="2026.07.23",
        extractor_version="2026.07.23",
        selected_video_format_id="137",
        selected_audio_format_id="140",
        remote_filename="Synthetic remote.mp4",
    )
    downloading = pending.advance(
        YouTubeAcquisitionState.DOWNLOADING,
        updated_at_ms=13,
    )
    downloaded = downloading.advance(
        YouTubeAcquisitionState.DOWNLOADED,
        updated_at_ms=14,
        downloaded_size_bytes=123,
        downloaded_at_ms=14,
    )
    handoff = downloaded.advance(
        YouTubeAcquisitionState.HANDOFF,
        updated_at_ms=15,
    )
    handed_off = handoff.advance(
        YouTubeAcquisitionState.HANDED_OFF,
        updated_at_ms=16,
        upload_id=UploadSessionId.new(),
    )
    cataloged = handed_off.advance(
        YouTubeAcquisitionState.CATALOGED,
        updated_at_ms=17,
        completed_at_ms=17,
        media_id=MediaId.new(),
        media_location_id=MediaLocationId.new(),
    )

    assert cataloged.state is YouTubeAcquisitionState.CATALOGED
    assert cataloged.version == 7
    assert cataloged.youtube_video_id == VIDEO_ID
    assert cataloged.generated_filename == f"youtube-{VIDEO_ID}.mp4"
    assert cataloged.upstream_title == "Synthetic title"
    assert cataloged.failure_code is None


def test_cataloged_source_identity_can_be_reused_without_download() -> None:
    original = YouTubeAcquisitionClaim.new(
        submitted_url=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        confirmation_method=YouTubeConfirmationMethod.INTERACTIVE,
        now_ms=20,
    )
    reuse = YouTubeAcquisitionClaim.new(
        submitted_url=f"https://youtu.be/{VIDEO_ID}",
        confirmation_method=YouTubeConfirmationMethod.YES_FLAG,
        now_ms=30,
    ).advance(
        YouTubeAcquisitionState.DUPLICATE_RESOLVED,
        updated_at_ms=31,
        completed_at_ms=31,
        resolved_claim_id=original.id,
        media_id=MediaId.new(),
        media_location_id=MediaLocationId.new(),
    )

    assert reuse.downloaded_size_bytes is None
    assert reuse.upload_id is None
    assert reuse.resolved_claim_id == original.id


def test_failed_claim_requires_paired_sanitized_failure_evidence() -> None:
    claim = YouTubeAcquisitionClaim.new(
        submitted_url=f"https://youtu.be/{VIDEO_ID}",
        confirmation_method=YouTubeConfirmationMethod.YES_FLAG,
        now_ms=40,
    )

    failed = claim.advance(
        YouTubeAcquisitionState.FAILED,
        updated_at_ms=41,
        completed_at_ms=41,
        failure_stage=YouTubeFailureStage.INSPECTION,
        failure_code="UNSUPPORTED_MEDIA",
    )
    assert failed.failure_code == "UNSUPPORTED_MEDIA"

    with pytest.raises(FrameNestYouTubeClaimError):
        claim.advance(
            YouTubeAcquisitionState.FAILED,
            updated_at_ms=41,
            completed_at_ms=41,
            failure_stage=YouTubeFailureStage.INSPECTION,
            failure_code="raw error /private/path",
        )


def test_illegal_transition_is_rejected() -> None:
    claim = YouTubeAcquisitionClaim.new(
        submitted_url=f"https://youtu.be/{VIDEO_ID}",
        confirmation_method=YouTubeConfirmationMethod.YES_FLAG,
        now_ms=50,
    )

    with pytest.raises(FrameNestYouTubeTransitionError):
        claim.advance(
            YouTubeAcquisitionState.DOWNLOADING,
            updated_at_ms=51,
        )
