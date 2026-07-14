"""SQLAlchemy Core upload-session table definition helper."""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    column,
    or_,
)

UPLOAD_SESSION_STATE_VALUES = (
    "created",
    "receiving",
    "received",
    "validating",
    "duplicate_pending",
    "publish_pending",
    "published",
    "cataloged",
    "rejected",
    "cancelled",
    "expired",
    "failed",
)

COMPLETE_UPLOAD_SESSION_STATE_VALUES = (
    "received",
    "validating",
    "duplicate_pending",
    "publish_pending",
    "published",
    "cataloged",
    "rejected",
)

VALIDATED_UPLOAD_SESSION_STATE_VALUES = (
    "duplicate_pending",
    "publish_pending",
    "published",
    "cataloged",
)


def define_upload_sessions_table(metadata: MetaData) -> Table:
    """Define the upload_sessions table on the supplied metadata object."""
    return Table(
        "upload_sessions",
        metadata,
        Column("id", Text(), primary_key=True, nullable=False),
        Column("state", Text(), nullable=False),
        Column("storage_key", Text(), nullable=False),
        Column("display_filename", Text(), nullable=False),
        Column("declared_size_bytes", Integer(), nullable=False),
        Column("received_size_bytes", Integer(), nullable=False),
        Column("checksum_algorithm", Text(), nullable=True),
        Column("checksum_hex", Text(), nullable=True),
        Column("validated_media_kind", Text(), nullable=True),
        Column("validated_format", Text(), nullable=True),
        Column("created_at_ms", Integer(), nullable=False),
        Column("updated_at_ms", Integer(), nullable=False),
        Column("expires_at_ms", Integer(), nullable=False),
        Column("failure_code", Text(), nullable=True),
        Column("version", Integer(), nullable=False),
        CheckConstraint("length(id) = 36", name="ck_upload_sessions_id_length"),
        CheckConstraint(
            "state IN ("
            + ", ".join(f"'{state}'" for state in UPLOAD_SESSION_STATE_VALUES)
            + ")",
            name="ck_upload_sessions_state",
        ),
        CheckConstraint(
            "length(storage_key) >= 16 AND length(storage_key) <= 128",
            name="ck_upload_sessions_storage_key_length",
        ),
        CheckConstraint(
            "storage_key = lower(storage_key) "
            "AND storage_key NOT GLOB '*[^a-z0-9._-]*' "
            "AND storage_key NOT GLOB '*/*' "
            "AND storage_key NOT GLOB '*\\*'",
            name="ck_upload_sessions_storage_key_opaque",
        ),
        CheckConstraint(
            "length(display_filename) >= 1 AND length(display_filename) <= 255",
            name="ck_upload_sessions_display_filename_length",
        ),
        CheckConstraint(
            "display_filename NOT GLOB '*/*' AND display_filename NOT GLOB '*\\*'",
            name="ck_upload_sessions_display_filename_not_path",
        ),
        CheckConstraint(
            "declared_size_bytes > 0",
            name="ck_upload_sessions_declared_size_positive",
        ),
        CheckConstraint(
            "received_size_bytes >= 0",
            name="ck_upload_sessions_received_size_non_negative",
        ),
        CheckConstraint(
            "received_size_bytes <= declared_size_bytes",
            name="ck_upload_sessions_received_size_not_over_declared",
        ),
        CheckConstraint(
            or_(column("state") != "created", column("received_size_bytes") == 0),
            name="ck_upload_sessions_created_received_size_zero",
        ),
        CheckConstraint(
            or_(
                ~column("state").in_(COMPLETE_UPLOAD_SESSION_STATE_VALUES),
                column("received_size_bytes") == column("declared_size_bytes"),
            ),
            name="ck_upload_sessions_complete_states_received_size_exact",
        ),
        CheckConstraint(
            "(checksum_algorithm IS NULL AND checksum_hex IS NULL) "
            "OR (checksum_algorithm = 'sha256' AND checksum_hex IS NOT NULL)",
            name="ck_upload_sessions_checksum_pair",
        ),
        CheckConstraint(
            "checksum_hex IS NULL OR ("
            "length(checksum_hex) = 64 "
            "AND checksum_hex = lower(checksum_hex) "
            "AND checksum_hex NOT GLOB '*[^0-9a-f]*')",
            name="ck_upload_sessions_checksum_hex",
        ),
        CheckConstraint(
            "(validated_media_kind IS NULL AND validated_format IS NULL) "
            "OR (validated_media_kind = 'animated_image' AND validated_format = 'gif') "
            "OR (validated_media_kind = 'video' AND validated_format = 'mp4')",
            name="ck_upload_sessions_validation_evidence_pair",
        ),
        CheckConstraint(
            or_(
                ~column("state").in_(VALIDATED_UPLOAD_SESSION_STATE_VALUES),
                (
                    (column("received_size_bytes") == column("declared_size_bytes"))
                    & (column("checksum_algorithm") == "sha256")
                    & column("checksum_hex").is_not(None)
                    & column("validated_media_kind").is_not(None)
                    & column("validated_format").is_not(None)
                ),
            ),
            name="ck_upload_sessions_validated_states_have_evidence",
        ),
        CheckConstraint(
            "created_at_ms >= 0",
            name="ck_upload_sessions_created_at_ms_non_negative",
        ),
        CheckConstraint(
            "updated_at_ms >= 0",
            name="ck_upload_sessions_updated_at_ms_non_negative",
        ),
        CheckConstraint(
            "updated_at_ms >= created_at_ms",
            name="ck_upload_sessions_updated_not_before_created",
        ),
        CheckConstraint(
            "expires_at_ms > created_at_ms",
            name="ck_upload_sessions_expires_after_created",
        ),
        CheckConstraint(
            "failure_code IS NULL OR ("
            "length(failure_code) >= 1 "
            "AND length(failure_code) <= 80 "
            "AND failure_code NOT GLOB '*[^A-Z0-9_]*')",
            name="ck_upload_sessions_failure_code_sanitized",
        ),
        CheckConstraint("version >= 0", name="ck_upload_sessions_version_non_negative"),
        UniqueConstraint("storage_key", name="uq_upload_sessions_storage_key"),
        Index("ix_upload_sessions_state", "state"),
        Index("ix_upload_sessions_expires_at_ms", "expires_at_ms"),
        Index("ix_upload_sessions_state_expires_at_ms", "state", "expires_at_ms"),
    )
