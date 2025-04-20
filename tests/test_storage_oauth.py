import pathlib

import pytest
import requests

from app.storage import DropboxStorage, DropboxStorageError

OAUTH_TOKEN_URL = "https://api.dropbox.com/oauth2/token"  # noqa: S105
DUMMY_ACCESS_TOKEN = "test-access-token-123"  # noqa: S105

@pytest.fixture
def dropbox_oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DROPBOX_APP_KEY", "dummy-app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "dummy-app-secret")
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "dummy-refresh-token")
    monkeypatch.delenv("DROPBOX_TOKEN", raising=False)  # Ensure legacy token is not set

def mock_oauth_token_success(
    _url: str, _headers: dict[str, str] | None, _data: dict[str, object] | None
) -> object:
    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 200
        def json(self) -> dict[str, object]:
            return {
                "access_token": DUMMY_ACCESS_TOKEN,
                "token_type": "bearer",
                "expires_in": 14400,
            }

    return MockResponse()

def mock_oauth_token_failure(
    _url: str, _headers: dict[str, str] | None, _data: dict[str, object] | None
) -> object:
    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 400
            self.text = "invalid_grant"

        def json(self) -> dict[str, object]:
            return {"error": "invalid_grant"}

    return MockResponse()

@pytest.mark.usefixtures("dropbox_oauth_env")
def test_dropbox_oauth_token_refresh_and_api_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test DropboxStorage obtains a new access token using OAuth 2.0 refresh flow and
    uses it for API calls.
    """
    # Patch requests.post to return a new access token on token endpoint, and a dummy
    # API response for Dropbox API. This ensures the backend uses the refreshed token
    # for Dropbox API calls.
    def mock_post(
        url: str,
        _headers: dict[str, str] | None = None,
        _json: dict[str, object] | None = None,
        data: dict[str, object] | None = None,
        _timeout: float | None = None,
        **_kwargs: object,
    ) -> object:
        if url == OAUTH_TOKEN_URL:
            return mock_oauth_token_success(url, None, data)
        class MockAPIResponse:
            def __init__(self) -> None:
                self.status_code = 200

            def json(self) -> dict[str, object]:
                return {"entries": [], "has_more": False}

            @property
            def content(self) -> bytes:
                return b"fake-bytes"

        return MockAPIResponse()

    monkeypatch.setattr(requests, "post", mock_post)
    storage = DropboxStorage()
    # Should not raise and should use new access token
    assert storage.list_photos() == []
    assert storage.get_photo("photo1.jpg") == b"fake-bytes"


@pytest.mark.usefixtures("dropbox_oauth_env")
def test_dropbox_oauth_token_refresh_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test DropboxStorage raises error if OAuth token refresh fails.
    """
    def mock_post(
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, object] | None = None,  # noqa: ARG001
        data: dict[str, object] | None = None,
        timeout: float | None = None,  # noqa: ARG001
        **_kwargs: object,
    ) -> object:
        if url == OAUTH_TOKEN_URL:
            return mock_oauth_token_failure(url, headers, data)
        msg = (
            "No Dropbox API call should be attempted if token refresh fails"
        )
        raise AssertionError(msg)

    monkeypatch.setattr(requests, "post", mock_post)
    with pytest.raises(
        DropboxStorageError, match="Failed to obtain Dropbox access token"
    ):
        DropboxStorage().list_photos()


def test_dropbox_oauth_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test DropboxStorage raises error if required OAuth env vars are missing.
    """
    monkeypatch.delenv("DROPBOX_APP_KEY", raising=False)
    monkeypatch.delenv("DROPBOX_APP_SECRET", raising=False)
    monkeypatch.delenv("DROPBOX_REFRESH_TOKEN", raising=False)
    with pytest.raises(
        DropboxStorageError, match="Dropbox OAuth credentials are not set"
    ):
        DropboxStorage().list_photos()


@pytest.mark.usefixtures("dropbox_oauth_env")
def test_dropbox_access_token_never_written_to_disk(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Ensure access token is never written to disk (simulate by checking for token in
    temp dir after API call).
    """
    def mock_post(
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, object] | None = None,  # noqa: ARG001
        data: dict[str, object] | None = None,
        timeout: float | None = None,  # noqa: ARG001
        **_kwargs: object,
    ) -> object:
        if url == OAUTH_TOKEN_URL:
            return mock_oauth_token_success(url, headers, data)
        class MockAPIResponse:
            def __init__(self) -> None:
                self.status_code = 200
            def json(self) -> dict[str, object]:
                return {"entries": [], "has_more": False}
            @property
            def content(self) -> bytes:
                return b"fake-bytes"
        return MockAPIResponse()

    monkeypatch.setattr(requests, "post", mock_post)
    storage = DropboxStorage()
    storage.list_photos()
    # Check that access token is not in any file in temp dir
    for file in tmp_path.iterdir():
        contents = file.read_bytes()
        assert DUMMY_ACCESS_TOKEN.encode() not in contents
