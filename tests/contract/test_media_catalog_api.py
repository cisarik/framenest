"""Contract tests for the searchable media catalog API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.adapters.api.media_catalog_api import MediaCatalogApiDependencies
from framenest.application.media_catalog import ListMediaCatalog
from framenest.application.ports.media_catalog_repository import (
    CatalogMediaItem,
    CatalogMediaLocation,
    CatalogMediaTag,
    FrameNestMediaCatalogRepositoryError,
    MediaCatalogPage,
    MediaCatalogQuery,
)
from framenest.configuration import FrameNestSettings
from framenest.domain.media_metadata import MediaCollectionKey

MEDIA_ID = "12345678-1234-4234-9234-123456789abc"
LOCATION_ID = "abcdefab-cdef-4abc-8def-abcdefabcdef"
LIBRARY_ID = "11111111-2222-4333-8444-555555555555"
PRIVATE_ROOT_MARKER = "private-root-marker"
UNDERLYING_EXCEPTION_TEXT = "sqlite failed beside private table"


@dataclass
class _FakeListMediaCatalog:
    error: Exception | None = None
    queries: list[dict[str, object]] | None = None

    def execute(
        self,
        *,
        q: str | None,
        tag_keys: list[str],
        limit: int,
        offset: int,
        collection_key: MediaCollectionKey | None = None,
        content_category: str | None = None,
        acquisition_source: str | None = None,
    ) -> MediaCatalogPage:
        if self.queries is None:
            self.queries = []
        self.queries.append(
            {
                "q": q,
                "tag_keys": tag_keys,
                "limit": limit,
                "offset": offset,
                "collection_key": collection_key,
                "content_category": content_category,
                "acquisition_source": acquisition_source,
            }
        )
        if self.error is not None:
            raise self.error
        return ListMediaCatalog(_FakeCatalogRepository()).execute(
            q=q,
            tag_keys=tag_keys,
            limit=limit,
            offset=offset,
            collection_key=collection_key,
            content_category=content_category,
            acquisition_source=acquisition_source,
        )


class _FakeCatalogRepository:
    def list_media(self, query: MediaCatalogQuery) -> MediaCatalogPage:
        return MediaCatalogPage(
            items=(
                CatalogMediaItem(
                    media_id=MEDIA_ID,
                    media_kind="video",
                    created_at_ms=10,
                    updated_at_ms=20,
                    display_title="Reinventing Entropy",
                    collection_key=None,
                    processed_at_ms=None,
                    tags=(CatalogMediaTag(key="mathematics", display_name="Math", position=0),),
                    locations=(
                        CatalogMediaLocation(
                            location_id=LOCATION_ID,
                            library_id=LIBRARY_ID,
                            relative_path="clips/reinventing-entropy.mp4",
                            availability="available",
                            observed_size_bytes=123,
                            observed_mtime_ns=456,
                        ),
                    ),
                ),
            ),
            total=1,
            limit=query.limit,
            offset=query.offset,
            q=query.q,
            tag_keys=query.tag_keys,
        )


def _client(
    *,
    catalog_available: bool = True,
    list_media: _FakeListMediaCatalog | None = None,
    database_path: Path | None = None,
) -> TestClient:
    settings = FrameNestSettings(
        database_path=database_path or Path("/tmp/framenest-media-catalog-api.sqlite3"),
        _env_file=None,
    )
    return TestClient(
        create_app(
            settings=settings,
            media_catalog_api_dependencies=MediaCatalogApiDependencies(
                list_media=list_media or _FakeListMediaCatalog(),
                catalog_available=lambda: catalog_available,
            ),
        )
    )


def test_successful_default_listing_exposes_complete_catalog_safe_fields() -> None:
    response = _client().get("/api/media")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "media_id": MEDIA_ID,
                "media_kind": "video",
                "created_at_ms": 10,
                "updated_at_ms": 20,
                "display_title": "Reinventing Entropy",
                "collection_key": None,
                "processed_at_ms": None,
                "tags": [{"key": "mathematics", "display_name": "Math", "position": 0}],
                "locations": [
                    {
                        "location_id": LOCATION_ID,
                        "library_id": LIBRARY_ID,
                        "relative_path": "clips/reinventing-entropy.mp4",
                        "availability": "available",
                        "observed_size_bytes": 123,
                        "observed_mtime_ns": 456,
                    }
                ],
                "content_category": "general",
                "acquisition_source": "unknown",
            }
        ],
        "total": 1,
        "limit": 24,
        "offset": 0,
        "q": None,
        "tag_keys": [],
        "content_category": None,
        "acquisition_source": None,
    }
    assert PRIVATE_ROOT_MARKER not in response.text


def test_repeated_tags_title_query_combined_filters_and_pagination_metadata() -> None:
    service = _FakeListMediaCatalog()
    response = _client(list_media=service).get(
        "/api/media",
        params=[
            ("q", " Entropy "),
            ("tag", "mathematics"),
            ("tag", "compression"),
            ("limit", "1"),
            ("offset", "2"),
        ],
    )

    assert response.status_code == 200
    assert response.json()["q"] == "Entropy"
    assert response.json()["limit"] == 1
    assert response.json()["offset"] == 2
    assert service.queries == [
        {
            "q": " Entropy ",
            "tag_keys": ["mathematics", "compression"],
            "limit": 1,
            "offset": 2,
            "collection_key": None,
            "content_category": None,
            "acquisition_source": None,
        }
    ]


def test_validation_failures_and_catalog_unavailable_response(tmp_path: Path) -> None:
    bad_limit = _client().get("/api/media?limit=0")
    bad_tag = _client().get("/api/media?tag=Bad")
    bad_query = _client().get("/api/media?q=bad%00query")
    database_path = tmp_path / "missing" / "catalog.sqlite3"
    unavailable = _client(catalog_available=False, database_path=database_path).get("/api/media")

    assert bad_limit.status_code == 422
    assert bad_tag.status_code == 422
    assert bad_query.status_code == 422
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "CATALOG_UNAVAILABLE"
    assert not database_path.exists()
    assert not database_path.parent.exists()


def test_repository_failures_are_sanitized() -> None:
    response = _client(
        list_media=_FakeListMediaCatalog(
            error=FrameNestMediaCatalogRepositoryError(UNDERLYING_EXCEPTION_TEXT)
        )
    ).get("/api/media")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "MEDIA_CATALOG_QUERY_FAILED"
    assert UNDERLYING_EXCEPTION_TEXT not in response.text
    assert PRIVATE_ROOT_MARKER not in response.text
