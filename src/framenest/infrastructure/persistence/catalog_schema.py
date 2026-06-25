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

metadata = MetaData()

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
        "media_kind IN ('video', 'animated_image')",
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
    Column("created_at_ms", Integer(), nullable=False),
    Column("updated_at_ms", Integer(), nullable=False),
    CheckConstraint("length(media_id) = 36", name="ck_media_metadata_media_id_length"),
    CheckConstraint(
        "display_title IS NULL OR (length(display_title) >= 1 AND length(display_title) <= 240)",
        name="ck_media_metadata_title_length",
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
