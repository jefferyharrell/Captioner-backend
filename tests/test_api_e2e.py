import http
from collections.abc import Generator

import httpx
import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def http_client(live_server_url: str) -> Generator[httpx.Client, None, None]:
    """Provides an httpx client configured for the live server."""
    client = httpx.Client(base_url=live_server_url)
    yield client
    client.close()


def test_api_docs_reachable(http_client: httpx.Client) -> None:
    """Verify the API docs endpoint (/docs) is reachable and returns HTML."""
    response = http_client.get("/docs")
    response.raise_for_status()
    assert response.status_code == http.HTTPStatus.OK
    assert "<title>FastAPI - Swagger UI</title>" in response.text


def test_api_get_photos_empty(http_client: httpx.Client) -> None:
    """Verify that GET /photos returns an empty list initially."""
    response = http_client.get("/photos")
    response.raise_for_status()
    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == {"photo_ids": []}


# --- New 404 Tests ---


def test_get_nonexistent_photo_returns_404(http_client: httpx.Client) -> None:
    """Verify GET /photos/{id} returns 404 for an ID that doesn't exist."""
    non_existent_id = 999999  # Use an integer ID
    response = http_client.get(f"/photos/{non_existent_id}")
    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert response.json().get("detail") == "Photo not found"


def test_patch_nonexistent_photo_returns_404(http_client: httpx.Client) -> None:
    """Verify PATCH /photos/{id}/metadata returns 404 for an ID that doesn't exist."""
    non_existent_id = 999999  # Use an integer ID
    response = http_client.patch(
        f"/photos/{non_existent_id}/metadata",
        json={"description": "New description"},  # Need valid body for PATCH
    )
    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert response.json().get("detail") == "Photo not found"
