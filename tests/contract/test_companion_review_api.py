"""Contract tests for administrator companion review inbox GET routes."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from framenest.adapters.api.application import create_app
from framenest.application.companion_review import encode_companion_review_cursor
from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

EXTERNAL_ORIGIN = "https://nuc-1.example.ts.net"
EXTERNAL_HOST = "nuc-1.example.ts.net"
ADMIN_LOGIN = "admin@example.com"
USER_LOGIN = "owner@example.com"

DEVICE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LIBRARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
GENERIC = "11111111-1111-4111-8111-111111111111"
GENERIC_LOC = "21111111-1111-4111-8111-111111111111"
GENERIC_RUN = "31111111-1111-4111-8111-111111111111"
MOVIE = "22222222-2222-4222-8222-222222222222"
MOVIE_LOC = "42222222-2222-4222-8222-222222222222"
MOVIE_RUN = "52222222-2222-4222-8222-222222222222"
MISSING = "33333333-3333-4333-8333-333333333333"


def _serve_headers(login: str, name: str = "User") -> dict[str, str]:
    return {
        "Tailscale-User-Login": login,
        "Tailscale-User-Name": name,
        "X-Forwarded-Proto": "https",
        "X-Forwarded-Host": EXTERNAL_HOST,
    }


def _result_json(title: str) -> str:
    return json.dumps(
        {
            "collection": "memes",
            "confidence": 0.9,
            "description": "A description.",
            "evidence": ["visible subject"],
            "suggested_filename": "clip.gif",
            "tags": ["Cats"],
            "title": title,
            "uncertainties": [],
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _client(tmp_path: Path) -> TestClient:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3",
        gallery_preview_cache_path=tmp_path / "previews",
        ingress_mode="tailscale_uds",
        uds_path=tmp_path / "framenest.sock",
        external_origin=EXTERNAL_ORIGIN,
        identity_map={
            ADMIN_LOGIN: "admin",
            USER_LOGIN: "user",
        },
        _env_file=None,
    )
    upgrade_database_to_head(settings)
    _seed(settings.database_path)
    return TestClient(create_app(settings=settings))


def _seed(database_path: Path) -> None:
    engine = create_sqlite_engine(database_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO devices (id, display_name) VALUES (:id, 'Dev')"),
                {"id": DEVICE_ID},
            )
            connection.execute(
                text(
                    "INSERT INTO libraries "
                    "(id, device_id, display_name, path_flavor, root_path) "
                    "VALUES (:id, :device, 'Lib', 'posix', '/tmp/synthetic')"
                ),
                {"id": LIBRARY_ID, "device": DEVICE_ID},
            )
            connection.execute(
                text(
                    "INSERT INTO canonical_tags "
                    "(key, display_name, created_at_ms, updated_at_ms) "
                    "VALUES ('cats', 'Cats', 1, 1)"
                )
            )
            _insert_media(connection, GENERIC, GENERIC_LOC, "general", "Inbox title")
            _insert_media(connection, MOVIE, MOVIE_LOC, "movie", "Movie title")
            _insert_run(connection, GENERIC_RUN, GENERIC, GENERIC_LOC, "Inbox stored")
            _insert_run(connection, MOVIE_RUN, MOVIE, MOVIE_LOC, "Movie stored")
    finally:
        dispose_engine(engine)


def _insert_media(connection, media_id: str, location_id: str, category: str, title: str) -> None:
    connection.execute(
        text(
            "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
            "VALUES (:id, 'video', 10, 10)"
        ),
        {"id": media_id},
    )
    connection.execute(
        text(
            "INSERT INTO physical_media_locations ("
            "id, media_id, library_id, relative_path, availability, "
            "observed_size_bytes, observed_mtime_ns, created_at_ms, updated_at_ms"
            ") VALUES (:id, :media, :library, :path, 'available', 8, NULL, 10, 10)"
        ),
        {"id": location_id, "media": media_id, "library": LIBRARY_ID, "path": f"{media_id}.mp4"},
    )
    connection.execute(
        text(
            "INSERT INTO media_metadata ("
            "media_id, display_title, description, created_at_ms, updated_at_ms, "
            "content_category, acquisition_source"
            ") VALUES (:id, :title, 'Desc', 10, 10, :category, 'manual_upload')"
        ),
        {"id": media_id, "title": title, "category": category},
    )


def _insert_run(connection, run_id: str, media_id: str, location_id: str, title: str) -> None:
    connection.execute(
        text(
            "INSERT INTO media_analysis_runs ("
            "id, media_id, media_location_id, analysis_definition, state, attempt_count, "
            "provider_id, model_id, prompt_version, result_schema_version, result_json, "
            "error_code, error_message, analysis_profile, created_at_ms, started_at_ms, "
            "completed_at_ms, version"
            ") VALUES ("
            ":id, :media, :location, 'automatic_post_catalog', 'analyzed', 1, "
            "'nvidia-nim', 'test-model', 'framenest-media-suggestion-v4', "
            "'framenest-media-suggestion-result-v1', :result, "
            "NULL, NULL, 'generic_media', 20, 21, 22, 2)"
        ),
        {
            "id": run_id,
            "media": media_id,
            "location": location_id,
            "result": _result_json(title),
        },
    )


def test_admin_list_and_detail_are_no_store_and_ordinary_is_forbidden(
    tmp_path: Path,
) -> None:
    with _client(tmp_path) as client:
        admin = client.get(
            "/api/companion/review-inbox",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
        )
        assert admin.status_code == 200
        assert admin.headers.get("cache-control") == "no-store"
        payload = admin.json()
        assert payload["unopened_count"] == 1
        assert payload["items"][0]["media_id"] == GENERIC
        assert payload["items"][0]["unopened"] is True
        assert "collection" not in admin.text
        assert "suggested_filename" not in admin.text
        ordinary = client.get(
            "/api/companion/review-inbox",
            headers=_serve_headers(USER_LOGIN, "Owner"),
        )
        assert ordinary.status_code == 403
        assert "Inbox title" not in ordinary.text
        assert ordinary.json()["error"]["code"] == "CAPABILITY_DENIED"
        detail = client.get(
            f"/api/companion/review-inbox/{GENERIC}",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
        )
        assert detail.status_code == 200
        assert detail.headers.get("cache-control") == "no-store"
        body = detail.json()
        assert body["suggestions"][0]["title"] == "Inbox stored"
        assert body["canonical"]["field_sources"]["display_title"] is None
        assert "collection" not in body["suggestions"][0]


def test_bad_cursor_is_422_and_movie_detail_is_409(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        bad = client.get(
            "/api/companion/review-inbox",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
            params={"cursor": "%%%"},
        )
        assert bad.status_code == 422
        assert bad.headers.get("cache-control") == "no-store"
        movie = client.get(
            f"/api/companion/review-inbox/{MOVIE}",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
        )
        assert movie.status_code == 409
        assert "Movie stored" not in movie.text
        assert movie.json()["error"]["code"] == "COMPANION_REVIEW_MOVIE_EXCLUDED"
        missing = client.get(
            f"/api/companion/review-inbox/{MISSING}",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
        )
        assert missing.status_code == 404
        stale = encode_companion_review_cursor(
            completed_at_ms=1, analysis_run_id=GENERIC_RUN
        )
        valid_cursor = client.get(
            "/api/companion/review-inbox",
            headers=_serve_headers(ADMIN_LOGIN, "Admin"),
            params={"cursor": stale},
        )
        assert valid_cursor.status_code == 200
