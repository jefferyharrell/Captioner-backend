import http

import httpx
import pytest

# Mark all tests in this module as 'e2e'
pytestmark = pytest.mark.e2e


def test_api_docs_reachable(live_server_url: str) -> None:
    """Verify the API docs endpoint (/docs) is reachable and returns HTML."""
    client = httpx.Client(base_url=live_server_url)
    try:
        response = client.get("/docs")
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        assert response.status_code == http.HTTPStatus.OK
        # Check for some content indicating it's the Swagger UI
        assert "<title>FastAPI - Swagger UI</title>" in response.text
    finally:
        client.close()


def test_api_get_photos_empty(live_server_url: str) -> None:
    """Verify that GET /photos returns an empty list initially."""
    # Note: This assumes the container starts with an empty/no database.
    # If the Dockerfile initialized data, this test would need adjustment.
    client = httpx.Client(base_url=live_server_url)
    try:
        response = client.get("/photos")
        response.raise_for_status()
        assert response.status_code == http.HTTPStatus.OK
        assert response.json() == {"photo_ids": []}
    finally:
        client.close()
