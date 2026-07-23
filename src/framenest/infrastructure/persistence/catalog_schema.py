"""SQLAlchemy Core table definitions for FrameNest catalog schema."""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
    UniqueConstraint,
    text,
)

from framenest.infrastructure.persistence.upload_schema import define_upload_sessions_table

metadata = MetaData()

media_byte_identities = Table(
    "media_byte_identities",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column("checksum_algorithm", Text(), nullable=False),
    Column("size_bytes", Integer(), nullable=False),
    Column("checksum_hex", Text(), nullable=False),
    Column("created_at_ms", Integer(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_media_byte_identities_id_length"),
    CheckConstraint(
        "checksum_algorithm = 'sha256'",
        name="ck_media_byte_identities_algorithm_sha256",
    ),
    CheckConstraint("size_bytes > 0", name="ck_media_byte_identities_size_positive"),
    CheckConstraint(
        "length(checksum_hex) = 64 "
        "AND checksum_hex = lower(checksum_hex) "
        "AND checksum_hex NOT GLOB '*[^0-9a-f]*'",
        name="ck_media_byte_identities_checksum_hex",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_media_byte_identities_created_at_ms_non_negative",
    ),
    UniqueConstraint(
        "checksum_algorithm",
        "size_bytes",
        "checksum_hex",
        name="uq_media_byte_identities_tuple",
    ),
)

devices = Table(
    "devices",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column("display_name", Text(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_devices_id_length"),
    CheckConstraint(
        "length(display_name) >= 1 AND length(display_name) <= 120",
        name="ck_devices_display_name_length",
    ),
)

libraries = Table(
    "libraries",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column(
        "device_id",
        Text(),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("display_name", Text(), nullable=False),
    Column("path_flavor", Text(), nullable=False),
    Column("root_path", Text(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_libraries_id_length"),
    CheckConstraint("length(device_id) = 36", name="ck_libraries_device_id_length"),
    CheckConstraint(
        "length(display_name) >= 1 AND length(display_name) <= 120",
        name="ck_libraries_display_name_length",
    ),
    CheckConstraint(
        "path_flavor IN ('posix', 'windows')",
        name="ck_libraries_path_flavor",
    ),
    CheckConstraint(
        "length(root_path) >= 1 AND length(root_path) <= 4096",
        name="ck_libraries_root_path_length",
    ),
    UniqueConstraint(
        "device_id",
        "path_flavor",
        "root_path",
        name="uq_libraries_device_root",
    ),
)

logical_media = Table(
    "logical_media",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column("media_kind", Text(), nullable=False),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_logical_media_id_length"),
    CheckConstraint(
        "media_kind IN ('video', 'animated_image', 'image')",
        name="ck_logical_media_kind",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_logical_media_created_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= 0",
        name="ck_logical_media_updated_at_ms_non_negative",
    ),
)

physical_media_locations = Table(
    "physical_media_locations",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column(
        "media_id",
        Text(),
        ForeignKey("logical_media.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "library_id",
        Text(),
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("relative_path", Text(), nullable=False),
    Column("availability", Text(), nullable=False),
    Column("observed_size_bytes", Integer(), nullable=True),
    Column("observed_mtime_ns", Integer(), nullable=True),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_physical_media_locations_id_length"),
    CheckConstraint(
        "length(media_id) = 36",
        name="ck_physical_media_locations_media_id_length",
    ),
    CheckConstraint(
        "length(library_id) = 36",
        name="ck_physical_media_locations_library_id_length",
    ),
    CheckConstraint(
        "length(relative_path) >= 1 AND length(relative_path) <= 4096",
        name="ck_physical_media_locations_relative_path_length",
    ),
    CheckConstraint(
        "availability IN ('available', 'offline', 'missing', 'unverified', 'archived')",
        name="ck_physical_media_locations_availability",
    ),
    CheckConstraint(
        "observed_size_bytes IS NULL OR observed_size_bytes >= 0",
        name="ck_physical_media_locations_observed_size_non_negative",
    ),
    CheckConstraint(
        "observed_mtime_ns IS NULL OR observed_mtime_ns >= 0",
        name="ck_physical_media_locations_observed_mtime_non_negative",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_physical_media_locations_created_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= 0",
        name="ck_physical_media_locations_updated_at_ms_non_negative",
    ),
    UniqueConstraint(
        "library_id",
        "relative_path",
        name="uq_physical_media_locations_library_path",
    ),
    Index("ix_physical_media_locations_media_id", "media_id"),
)

canonical_tags = Table(
    "canonical_tags",
    metadata,
    Column("key", Text(), primary_key=True, nullable=False),
    Column("display_name", Text(), nullable=False),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    CheckConstraint(
        "length(key) >= 1 AND length(key) <= 64",
        name="ck_canonical_tags_key_length",
    ),
    CheckConstraint("key = lower(key)", name="ck_canonical_tags_key_lowercase"),
    CheckConstraint(
        "key GLOB '[a-z]*' "
        "AND key NOT GLOB '*[^a-z0-9-]*' "
        "AND key NOT LIKE '%--%' "
        "AND substr(key, length(key), 1) != '-'",
        name="ck_canonical_tags_key_slug",
    ),
    CheckConstraint(
        "length(display_name) >= 1 AND length(display_name) <= 80",
        name="ck_canonical_tags_display_name_length",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_canonical_tags_created_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= 0",
        name="ck_canonical_tags_updated_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= created_at_ms",
        name="ck_canonical_tags_updated_not_before_created",
    ),
)

media_metadata = Table(
    "media_metadata",
    metadata,
    Column(
        "media_id",
        Text(),
        ForeignKey("logical_media.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("display_title", Text(), nullable=True),
    Column("description", Text(), nullable=True),
    Column("content_category", Text(), nullable=False, server_default="general"),
    Column("acquisition_source", Text(), nullable=False, server_default="unknown"),
    Column("collection_key", Text(), nullable=True),
    Column("processed_at_ms", Integer(), nullable=True),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    CheckConstraint("length(media_id) = 36", name="ck_media_metadata_media_id_length"),
    CheckConstraint(
        "content_category IN ('general', 'meme', 'movie')",
        name="ck_media_metadata_content_category",
    ),
    CheckConstraint(
        "acquisition_source IN ("
        "'unknown', 'manual_upload', 'library_scan', 'youtube_manual_claim')",
        name="ck_media_metadata_acquisition_source",
    ),
    CheckConstraint(
        "collection_key IS NULL OR collection_key = 'processed'",
        name="ck_media_metadata_collection_key_valid",
    ),
    CheckConstraint(
        "(collection_key IS NULL AND processed_at_ms IS NULL) "
        "OR (collection_key = 'processed' AND processed_at_ms IS NOT NULL)",
        name="ck_media_metadata_collection_paired",
    ),
    CheckConstraint(
        "processed_at_ms IS NULL OR processed_at_ms >= 0",
        name="ck_media_metadata_processed_at_ms_non_negative",
    ),
    CheckConstraint(
        "display_title IS NULL OR (length(display_title) >= 1 AND length(display_title) <= 240)",
        name="ck_media_metadata_title_length",
    ),
    CheckConstraint(
        "description IS NULL OR (length(description) >= 1 AND length(description) <= 10000)",
        name="ck_media_metadata_description_length",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_media_metadata_created_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= 0",
        name="ck_media_metadata_updated_at_ms_non_negative",
    ),
    CheckConstraint(
        "updated_at_ms >= created_at_ms",
        name="ck_media_metadata_updated_not_before_created",
    ),
    Index(
        "ix_media_metadata_collection",
        "collection_key",
        "processed_at_ms",
        "media_id",
    ),
    Index("ix_media_metadata_content_category", "content_category", "media_id"),
    Index("ix_media_metadata_acquisition_source", "acquisition_source", "media_id"),
)

media_genres = Table(
    "media_genres",
    metadata,
    Column(
        "media_id",
        Text(),
        ForeignKey("media_metadata.media_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("genre_key", Text(), nullable=False),
    Column("position", Integer(), nullable=False),
    CheckConstraint("length(media_id) = 36", name="ck_media_genres_media_id_length"),
    CheckConstraint(
        "genre_key IN ("
        "'drama', 'comedy', 'sci-fi', 'thriller', 'horror', 'action', 'adventure', "
        "'documentary', 'animation', 'family', 'romance', 'crime', 'fantasy', 'mystery')",
        name="ck_media_genres_genre_key",
    ),
    CheckConstraint(
        "position >= 0 AND position < 8",
        name="ck_media_genres_position_range",
    ),
    PrimaryKeyConstraint("media_id", "genre_key", name="pk_media_genres"),
    UniqueConstraint("media_id", "position", name="uq_media_genres_media_position"),
    Index("ix_media_genres_genre_key", "genre_key"),
)

media_canonical_tags = Table(
    "media_canonical_tags",
    metadata,
    Column(
        "media_id",
        Text(),
        ForeignKey("media_metadata.media_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "tag_key",
        Text(),
        ForeignKey("canonical_tags.key", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("position", Integer(), nullable=False),
    CheckConstraint("length(media_id) = 36", name="ck_media_canonical_tags_media_id_length"),
    CheckConstraint(
        "length(tag_key) >= 1 AND length(tag_key) <= 64",
        name="ck_media_canonical_tags_tag_key_length",
    ),
    CheckConstraint(
        "position >= 0 AND position < 32",
        name="ck_media_canonical_tags_position_range",
    ),
    PrimaryKeyConstraint("media_id", "tag_key", name="pk_media_canonical_tags"),
    UniqueConstraint("media_id", "position", name="uq_media_canonical_tags_media_position"),
)

upload_sessions = define_upload_sessions_table(metadata)

upload_publications = Table(
    "upload_publications",
    metadata,
    Column(
        "upload_id",
        Text(),
        ForeignKey("upload_sessions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("publication_id", Text(), nullable=False),
    Column(
        "destination_id",
        Text(),
        ForeignKey("libraries.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("relative_target", Text(), nullable=False),
    Column(
        "byte_identity_id",
        Text(),
        ForeignKey("media_byte_identities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("expected_size_bytes", Integer(), nullable=False),
    Column("checksum_algorithm", Text(), nullable=False),
    Column("checksum_hex", Text(), nullable=False),
    Column("validated_media_kind", Text(), nullable=False),
    Column("validated_format", Text(), nullable=False),
    Column("state", Text(), nullable=False),
    Column("cleanup_state", Text(), nullable=False),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    Column("verified_at_ms", Integer(), nullable=True),
    Column("cleanup_completed_at_ms", Integer(), nullable=True),
    Column("version", Integer(), nullable=False),
    Column(
        "media_id",
        Text(),
        ForeignKey(
            "logical_media.id",
            ondelete="RESTRICT",
            name="fk_upload_publications_media_id",
        ),
        nullable=True,
    ),
    Column(
        "media_location_id",
        Text(),
        ForeignKey(
            "physical_media_locations.id",
            ondelete="RESTRICT",
            name="fk_upload_publications_media_location_id",
        ),
        nullable=True,
    ),
    CheckConstraint(
        "length(upload_id) = 36",
        name="ck_upload_publications_upload_id_length",
    ),
    CheckConstraint(
        "length(publication_id) = 36",
        name="ck_upload_publications_publication_id_length",
    ),
    CheckConstraint(
        "length(destination_id) = 36",
        name="ck_upload_publications_destination_id_length",
    ),
    CheckConstraint(
        "length(byte_identity_id) = 36",
        name="ck_upload_publications_byte_identity_id_length",
    ),
    CheckConstraint(
        "length(relative_target) = 36 "
        "AND relative_target = lower(relative_target) "
        "AND substr(relative_target, 1, 32) NOT GLOB '*[^0-9a-f]*' "
        "AND relative_target NOT GLOB '*/*' "
        "AND relative_target NOT GLOB '*\\*' "
        "AND substr(relative_target, 1, 32) = replace(publication_id, '-', '') "
        "AND ((validated_format = 'gif' AND substr(relative_target, 33) = '.gif') "
        "OR (validated_format = 'mp4' AND substr(relative_target, 33) = '.mp4') "
        "OR (validated_format = 'jpg' AND substr(relative_target, 33) = '.jpg') "
        "OR (validated_format = 'png' AND substr(relative_target, 33) = '.png'))",
        name="ck_upload_publications_relative_target_opaque",
    ),
    CheckConstraint(
        "expected_size_bytes > 0",
        name="ck_upload_publications_expected_size_positive",
    ),
    CheckConstraint(
        "checksum_algorithm = 'sha256'",
        name="ck_upload_publications_checksum_algorithm",
    ),
    CheckConstraint(
        "length(checksum_hex) = 64 "
        "AND checksum_hex = lower(checksum_hex) "
        "AND checksum_hex NOT GLOB '*[^0-9a-f]*'",
        name="ck_upload_publications_checksum_hex",
    ),
    CheckConstraint(
        "(validated_media_kind = 'animated_image' AND validated_format = 'gif') "
        "OR (validated_media_kind = 'video' AND validated_format = 'mp4') "
        "OR (validated_media_kind = 'image' AND validated_format = 'jpg') "
        "OR (validated_media_kind = 'image' AND validated_format = 'png')",
        name="ck_upload_publications_validation_evidence_pair",
    ),
    CheckConstraint(
        "state IN ('reserved', 'verified')",
        name="ck_upload_publications_state",
    ),
    CheckConstraint(
        "cleanup_state IN ('pending', 'complete')",
        name="ck_upload_publications_cleanup_state",
    ),
    CheckConstraint(
        "(state = 'reserved' AND cleanup_state = 'pending' "
        "AND verified_at_ms IS NULL AND cleanup_completed_at_ms IS NULL) "
        "OR (state = 'verified' AND verified_at_ms IS NOT NULL "
        "AND ((cleanup_state = 'pending' AND cleanup_completed_at_ms IS NULL) "
        "OR (cleanup_state = 'complete' AND cleanup_completed_at_ms IS NOT NULL)))",
        name="ck_upload_publications_progress",
    ),
    CheckConstraint(
        "created_at_ms >= 0 AND updated_at_ms >= created_at_ms",
        name="ck_upload_publications_timestamps",
    ),
    CheckConstraint(
        "verified_at_ms IS NULL OR verified_at_ms >= created_at_ms",
        name="ck_upload_publications_verified_at_ms",
    ),
    CheckConstraint(
        "cleanup_completed_at_ms IS NULL "
        "OR cleanup_completed_at_ms >= verified_at_ms",
        name="ck_upload_publications_cleanup_completed_at_ms",
    ),
    CheckConstraint(
        "version >= 0",
        name="ck_upload_publications_version_non_negative",
    ),
    CheckConstraint(
        "(media_id IS NULL AND media_location_id IS NULL) "
        "OR (media_id IS NOT NULL AND media_location_id IS NOT NULL)",
        name="ck_upload_publications_catalog_linkage",
    ),
    CheckConstraint(
        "media_id IS NULL OR length(media_id) = 36",
        name="ck_upload_publications_media_id_length",
    ),
    CheckConstraint(
        "media_location_id IS NULL OR length(media_location_id) = 36",
        name="ck_upload_publications_media_location_id_length",
    ),
    UniqueConstraint(
        "publication_id",
        name="uq_upload_publications_publication_id",
    ),
    UniqueConstraint(
        "destination_id",
        "relative_target",
        name="uq_upload_publications_destination_target",
    ),
    UniqueConstraint(
        "media_id",
        name="uq_upload_publications_media_id",
    ),
    UniqueConstraint(
        "media_location_id",
        name="uq_upload_publications_media_location_id",
    ),
    Index(
        "ix_upload_publications_state_cleanup",
        "state",
        "cleanup_state",
        "updated_at_ms",
        "upload_id",
    ),
    Index("ix_upload_publications_byte_identity_id", "byte_identity_id"),
)

youtube_acquisition_claims = Table(
    "youtube_acquisition_claims",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column("state", Text(), nullable=False),
    Column("acquisition_source", Text(), nullable=False),
    Column("submitted_url", Text(), nullable=False),
    Column("canonical_url", Text(), nullable=False),
    Column("youtube_video_id", Text(), nullable=False),
    Column("extractor_key", Text(), nullable=False),
    Column(
        "retry_of_claim_id",
        Text(),
        ForeignKey(
            "youtube_acquisition_claims.id",
            ondelete="RESTRICT",
            name="fk_youtube_claims_retry_of_claim_id",
        ),
        nullable=True,
    ),
    Column(
        "resolved_claim_id",
        Text(),
        ForeignKey(
            "youtube_acquisition_claims.id",
            ondelete="RESTRICT",
            name="fk_youtube_claims_resolved_claim_id",
        ),
        nullable=True,
    ),
    Column(
        "upload_id",
        Text(),
        ForeignKey(
            "upload_sessions.id",
            ondelete="RESTRICT",
            name="fk_youtube_claims_upload_id",
        ),
        nullable=True,
    ),
    Column(
        "media_id",
        Text(),
        ForeignKey(
            "logical_media.id",
            ondelete="RESTRICT",
            name="fk_youtube_claims_media_id",
        ),
        nullable=True,
    ),
    Column(
        "media_location_id",
        Text(),
        ForeignKey(
            "physical_media_locations.id",
            ondelete="RESTRICT",
            name="fk_youtube_claims_media_location_id",
        ),
        nullable=True,
    ),
    Column("confirmation_method", Text(), nullable=False),
    Column("confirmed_at_ms", Integer(), nullable=False),
    Column("upstream_title", Text(), nullable=True),
    Column("upstream_channel", Text(), nullable=True),
    Column("upstream_channel_id", Text(), nullable=True),
    Column("upstream_source_date", Text(), nullable=True),
    Column("downloader_name", Text(), nullable=True),
    Column("downloader_version", Text(), nullable=True),
    Column("extractor_version", Text(), nullable=True),
    Column("selected_video_format_id", Text(), nullable=True),
    Column("selected_audio_format_id", Text(), nullable=True),
    Column("remote_filename", Text(), nullable=True),
    Column("generated_filename", Text(), nullable=False),
    Column("staging_key", Text(), nullable=False),
    Column("downloaded_size_bytes", Integer(), nullable=True),
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    Column("downloaded_at_ms", Integer(), nullable=True),
    Column("completed_at_ms", Integer(), nullable=True),
    Column("failure_stage", Text(), nullable=True),
    Column("failure_code", Text(), nullable=True),
    Column("cleanup_state", Text(), nullable=False),
    Column("cleanup_completed_at_ms", Integer(), nullable=True),
    Column("version", Integer(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_youtube_claims_id_length"),
    CheckConstraint(
        "state IN ('claimed', 'inspecting', 'download_pending', 'downloading', "
        "'downloaded', 'handoff', 'handed_off', 'duplicate_resolved', "
        "'cataloged', 'failed')",
        name="ck_youtube_claims_state",
    ),
    CheckConstraint(
        "acquisition_source = 'youtube_manual_claim'",
        name="ck_youtube_claims_acquisition_source",
    ),
    CheckConstraint(
        "length(submitted_url) >= 1 AND length(submitted_url) <= 2048",
        name="ck_youtube_claims_submitted_url_length",
    ),
    CheckConstraint(
        "canonical_url = 'https://www.youtube.com/watch?v=' || youtube_video_id",
        name="ck_youtube_claims_canonical_identity",
    ),
    CheckConstraint(
        "length(youtube_video_id) = 11 "
        "AND youtube_video_id NOT GLOB '*[^A-Za-z0-9_-]*'",
        name="ck_youtube_claims_video_id",
    ),
    CheckConstraint(
        "extractor_key = 'Youtube'",
        name="ck_youtube_claims_extractor_key",
    ),
    CheckConstraint(
        "retry_of_claim_id IS NULL OR "
        "(length(retry_of_claim_id) = 36 AND retry_of_claim_id != id)",
        name="ck_youtube_claims_retry_lineage",
    ),
    CheckConstraint(
        "resolved_claim_id IS NULL OR "
        "(length(resolved_claim_id) = 36 AND resolved_claim_id != id)",
        name="ck_youtube_claims_resolution_lineage",
    ),
    CheckConstraint(
        "upload_id IS NULL OR length(upload_id) = 36",
        name="ck_youtube_claims_upload_id_length",
    ),
    CheckConstraint(
        "(media_id IS NULL AND media_location_id IS NULL) "
        "OR (length(media_id) = 36 AND length(media_location_id) = 36)",
        name="ck_youtube_claims_catalog_linkage_pair",
    ),
    CheckConstraint(
        "confirmation_method IN ('interactive', 'yes_flag')",
        name="ck_youtube_claims_confirmation_method",
    ),
    CheckConstraint(
        "confirmed_at_ms >= created_at_ms",
        name="ck_youtube_claims_confirmed_at",
    ),
    CheckConstraint(
        "upstream_title IS NULL OR "
        "(length(upstream_title) >= 1 AND length(upstream_title) <= 500)",
        name="ck_youtube_claims_upstream_title_length",
    ),
    CheckConstraint(
        "upstream_channel IS NULL OR "
        "(length(upstream_channel) >= 1 AND length(upstream_channel) <= 200)",
        name="ck_youtube_claims_upstream_channel_length",
    ),
    CheckConstraint(
        "upstream_channel_id IS NULL OR "
        "(length(upstream_channel_id) >= 1 AND length(upstream_channel_id) <= 128)",
        name="ck_youtube_claims_upstream_channel_id_length",
    ),
    CheckConstraint(
        "upstream_source_date IS NULL OR "
        "(length(upstream_source_date) = 10 "
        "AND upstream_source_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')",
        name="ck_youtube_claims_upstream_source_date",
    ),
    CheckConstraint(
        "downloader_name IS NULL OR "
        "(length(downloader_name) >= 1 AND length(downloader_name) <= 120)",
        name="ck_youtube_claims_downloader_name_length",
    ),
    CheckConstraint(
        "downloader_version IS NULL OR "
        "(length(downloader_version) >= 1 AND length(downloader_version) <= 120)",
        name="ck_youtube_claims_downloader_version_length",
    ),
    CheckConstraint(
        "extractor_version IS NULL OR "
        "(length(extractor_version) >= 1 AND length(extractor_version) <= 120)",
        name="ck_youtube_claims_extractor_version_length",
    ),
    CheckConstraint(
        "selected_video_format_id IS NULL OR "
        "(length(selected_video_format_id) >= 1 "
        "AND length(selected_video_format_id) <= 120)",
        name="ck_youtube_claims_video_format_id_length",
    ),
    CheckConstraint(
        "selected_audio_format_id IS NULL OR "
        "(length(selected_audio_format_id) >= 1 "
        "AND length(selected_audio_format_id) <= 120)",
        name="ck_youtube_claims_audio_format_id_length",
    ),
    CheckConstraint(
        "remote_filename IS NULL OR "
        "(length(remote_filename) >= 1 AND length(remote_filename) <= 500)",
        name="ck_youtube_claims_remote_filename_length",
    ),
    CheckConstraint(
        "generated_filename = 'youtube-' || youtube_video_id || '.mp4'",
        name="ck_youtube_claims_generated_filename",
    ),
    CheckConstraint(
        "length(staging_key) = 32 AND staging_key = lower(staging_key) "
        "AND staging_key NOT GLOB '*[^0-9a-f]*'",
        name="ck_youtube_claims_staging_key",
    ),
    CheckConstraint(
        "downloaded_size_bytes IS NULL OR downloaded_size_bytes > 0",
        name="ck_youtube_claims_downloaded_size",
    ),
    CheckConstraint(
        "created_at_ms >= 0 AND updated_at_ms >= created_at_ms",
        name="ck_youtube_claims_timestamps",
    ),
    CheckConstraint(
        "downloaded_at_ms IS NULL OR downloaded_at_ms >= created_at_ms",
        name="ck_youtube_claims_downloaded_at",
    ),
    CheckConstraint(
        "completed_at_ms IS NULL OR completed_at_ms >= created_at_ms",
        name="ck_youtube_claims_completed_at",
    ),
    CheckConstraint(
        "(failure_stage IS NULL AND failure_code IS NULL) OR ("
        "failure_stage IN ('configuration', 'inspection', 'download', 'staging', "
        "'handoff', 'downstream', 'cleanup', 'internal') "
        "AND length(failure_code) >= 1 AND length(failure_code) <= 80 "
        "AND failure_code NOT GLOB '*[^A-Z0-9_]*')",
        name="ck_youtube_claims_failure_pair",
    ),
    CheckConstraint(
        "cleanup_state IN ('pending', 'complete') "
        "AND ((cleanup_state = 'pending' AND cleanup_completed_at_ms IS NULL) "
        "OR (cleanup_state = 'complete' "
        "AND cleanup_completed_at_ms IS NOT NULL))",
        name="ck_youtube_claims_cleanup_pair",
    ),
    CheckConstraint(
        "version >= 0",
        name="ck_youtube_claims_version",
    ),
    CheckConstraint(
        "(state IN ('downloaded', 'handoff', 'handed_off', 'cataloged') "
        "AND downloaded_size_bytes IS NOT NULL AND downloaded_at_ms IS NOT NULL) "
        "OR state NOT IN ('downloaded', 'handoff', 'handed_off', 'cataloged')",
        name="ck_youtube_claims_download_payload",
    ),
    CheckConstraint(
        "(state IN ('handed_off', 'cataloged') AND upload_id IS NOT NULL) "
        "OR state NOT IN ('handed_off', 'cataloged')",
        name="ck_youtube_claims_handoff_linkage",
    ),
    CheckConstraint(
        "(state = 'cataloged' AND media_id IS NOT NULL "
        "AND completed_at_ms IS NOT NULL AND failure_code IS NULL) "
        "OR (state = 'duplicate_resolved' "
        "AND media_id IS NOT NULL AND completed_at_ms IS NOT NULL "
        "AND failure_code IS NULL) "
        "OR (state = 'failed' AND failure_code IS NOT NULL "
        "AND completed_at_ms IS NOT NULL) "
        "OR (state NOT IN ('cataloged', 'duplicate_resolved', 'failed') "
        "AND completed_at_ms IS NULL AND failure_code IS NULL)",
        name="ck_youtube_claims_terminal_payload",
    ),
    UniqueConstraint("staging_key", name="uq_youtube_claims_staging_key"),
    UniqueConstraint("upload_id", name="uq_youtube_claims_upload_id"),
    Index(
        "uq_youtube_claims_active_source_identity",
        "extractor_key",
        "youtube_video_id",
        unique=True,
        sqlite_where=text(
            "state IN ('claimed', 'inspecting', 'download_pending', 'downloading', "
            "'downloaded', 'handoff', 'handed_off')"
        ),
    ),
    Index(
        "ix_youtube_claims_source_identity",
        "extractor_key",
        "youtube_video_id",
        "created_at_ms",
    ),
    Index("ix_youtube_claims_state", "state", "updated_at_ms", "id"),
    Index("ix_youtube_claims_retry_of", "retry_of_claim_id"),
    Index("ix_youtube_claims_resolved_claim", "resolved_claim_id"),
    Index("ix_youtube_claims_media", "media_id", "media_location_id"),
)

media_analysis_runs = Table(
    "media_analysis_runs",
    metadata,
    Column("id", Text(), primary_key=True, nullable=False),
    Column(
        "media_id",
        Text(),
        ForeignKey(
            "logical_media.id",
            ondelete="RESTRICT",
            name="fk_media_analysis_runs_media_id",
        ),
        nullable=False,
    ),
    Column(
        "media_location_id",
        Text(),
        ForeignKey(
            "physical_media_locations.id",
            ondelete="RESTRICT",
            name="fk_media_analysis_runs_media_location_id",
        ),
        nullable=False,
    ),
    Column("analysis_definition", Text(), nullable=False),
    Column("state", Text(), nullable=False),
    Column("attempt_count", Integer(), nullable=False),
    Column("provider_id", Text(), nullable=True),
    Column("model_id", Text(), nullable=True),
    Column("prompt_version", Text(), nullable=True),
    Column("result_schema_version", Text(), nullable=True),
    Column("result_json", Text(), nullable=True),
    Column("error_code", Text(), nullable=True),
    Column("error_message", Text(), nullable=True),
    Column("analysis_profile", Text(), nullable=True),
    Column("reasoning_enabled", Integer(), nullable=True),
    Column("derivative_strategy", Text(), nullable=True),
    Column("derivative_count", Integer(), nullable=True),
    Column("provider_submission_occurred", Integer(), nullable=True),
    Column(
        "supersedes_run_id",
        Text(),
        ForeignKey(
            "media_analysis_runs.id",
            ondelete="RESTRICT",
            name="fk_media_analysis_runs_supersedes_run_id",
        ),
        nullable=True,
    ),
    Column("created_at_ms", Integer(), nullable=False),
    Column("started_at_ms", Integer(), nullable=True),
    Column("completed_at_ms", Integer(), nullable=True),
    Column("version", Integer(), nullable=False),
    CheckConstraint("length(id) = 36", name="ck_media_analysis_runs_id_length"),
    CheckConstraint(
        "length(media_id) = 36",
        name="ck_media_analysis_runs_media_id_length",
    ),
    CheckConstraint(
        "length(media_location_id) = 36",
        name="ck_media_analysis_runs_media_location_id_length",
    ),
    CheckConstraint(
        "length(analysis_definition) >= 1 AND length(analysis_definition) <= 64",
        name="ck_media_analysis_runs_definition_length",
    ),
    CheckConstraint(
        "state IN ('pending', 'analyzing', 'analyzed', 'failed')",
        name="ck_media_analysis_runs_state",
    ),
    CheckConstraint(
        "attempt_count >= 0 AND attempt_count <= 100",
        name="ck_media_analysis_runs_attempt_count",
    ),
    CheckConstraint(
        "analysis_profile IS NULL OR analysis_profile IN "
        "('generic_media', 'movie_identification')",
        name="ck_media_analysis_runs_analysis_profile",
    ),
    CheckConstraint(
        "reasoning_enabled IS NULL OR reasoning_enabled IN (0, 1)",
        name="ck_media_analysis_runs_reasoning_enabled",
    ),
    CheckConstraint(
        "provider_submission_occurred IS NULL OR provider_submission_occurred IN (0, 1)",
        name="ck_media_analysis_runs_provider_submission",
    ),
    CheckConstraint(
        "derivative_count IS NULL OR (derivative_count >= 0 AND derivative_count <= 16)",
        name="ck_media_analysis_runs_derivative_count",
    ),
    CheckConstraint(
        "supersedes_run_id IS NULL OR ("
        "length(supersedes_run_id) = 36 AND supersedes_run_id != id"
        ")",
        name="ck_media_analysis_runs_supersedes_run_id",
    ),
    CheckConstraint(
        "created_at_ms >= 0",
        name="ck_media_analysis_runs_created_at_ms_non_negative",
    ),
    CheckConstraint(
        "started_at_ms IS NULL OR started_at_ms >= 0",
        name="ck_media_analysis_runs_started_at_ms_non_negative",
    ),
    CheckConstraint(
        "completed_at_ms IS NULL OR completed_at_ms >= 0",
        name="ck_media_analysis_runs_completed_at_ms_non_negative",
    ),
    CheckConstraint(
        "version >= 1",
        name="ck_media_analysis_runs_version_positive",
    ),
    CheckConstraint(
        "("
        "state = 'pending' AND started_at_ms IS NULL AND completed_at_ms IS NULL "
        "AND result_json IS NULL AND result_schema_version IS NULL "
        "AND error_code IS NULL AND error_message IS NULL"
        ") OR ("
        "state = 'analyzing' AND started_at_ms IS NOT NULL AND completed_at_ms IS NULL "
        "AND result_json IS NULL AND result_schema_version IS NULL "
        "AND error_code IS NULL AND error_message IS NULL "
        "AND attempt_count >= 1"
        ") OR ("
        "state = 'analyzed' AND started_at_ms IS NOT NULL AND completed_at_ms IS NOT NULL "
        "AND result_json IS NOT NULL AND result_schema_version IS NOT NULL "
        "AND error_code IS NULL AND error_message IS NULL "
        "AND provider_id IS NOT NULL AND model_id IS NOT NULL "
        "AND prompt_version IS NOT NULL AND attempt_count >= 1"
        ") OR ("
        "state = 'failed' AND started_at_ms IS NOT NULL AND completed_at_ms IS NOT NULL "
        "AND result_json IS NULL AND result_schema_version IS NULL "
        "AND error_code IS NOT NULL AND error_message IS NOT NULL "
        "AND attempt_count >= 1"
        ")",
        name="ck_media_analysis_runs_state_payload",
    ),
    Index(
        "ix_media_analysis_runs_unfinished",
        "state",
        "created_at_ms",
        "id",
    ),
    Index(
        "uq_media_analysis_runs_active_media_definition",
        "media_id",
        "analysis_definition",
        unique=True,
        sqlite_where=text("state IN ('pending', 'analyzing')"),
    ),
)
