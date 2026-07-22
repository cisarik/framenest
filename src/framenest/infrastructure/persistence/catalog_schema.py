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
    UniqueConstraint(
        "media_id",
        "analysis_definition",
        name="uq_media_analysis_runs_media_definition",
    ),
    Index(
        "ix_media_analysis_runs_unfinished",
        "state",
        "created_at_ms",
        "id",
    ),
)
