from collections.abc import Mapping
from unittest.mock import patch

import pytest
import requests

from app.storage import PhotoStorage, get_storage_backend
from app.storage_dropbox import DropboxStorage, DropboxStorageError

OAUTH_TOKEN_URL = "https://api.dropbox.com/oauth2/token"  # noqa: S105

@pytest.fixture(autouse=True)
def dropbox_oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DROPBOX_APP_KEY", "dummy-app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "dummy-app-secret")
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "dummy-refresh-token")

def test_storage_interface() -> None:
    # DropboxStorage must implement the PhotoStorage interface
    storage: PhotoStorage = DropboxStorage()
    assert hasattr(storage, "list_photos")
    assert hasattr(storage, "get_photo")
    assert callable(storage.list_photos)
    assert callable(storage.get_photo)




def test_default_storage_is_dropbox(monkeypatch: pytest.MonkeyPatch) -> None:
    # Default backend without override should be Dropbox
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    storage = get_storage_backend()
    assert isinstance(storage, DropboxStorage)


def test_dropbox_storage_list_photos() -> None:
    # Mock Dropbox API response for listing files
    files_response = {
        "entries": [
            {
                ".tag": "file",
                "name": "photo1.jpg",
                "path_display": "/photos/photo1.jpg",
            },
            {
                ".tag": "file",
                "name": "photo2.png",
                "path_display": "/photos/photo2.png",
            },
            {
                ".tag": "file",
                "name": "nested1.JPG",
                "path_display": "/photos/2024/nested1.JPG",
            },
            {
                ".tag": "file",
                "name": "nested2.jpeg",
                "path_display": "/photos/2024/events/nested2.jpeg",
            },
            {
                ".tag": "file",
                "name": "not_photo.txt",
                "path_display": "/docs/not_photo.txt",
            },
            {
                ".tag": "folder",
                "name": "2024",
                "path_display": "/photos/2024",
            },
        ],
        "has_more": False,
    }

    def mock_post(
        _url: str,
        _headers: dict[str, str] | None = None,
        _json: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> object:
        _ = _kwargs
        if _url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> Mapping[str, str]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        class MockResponse:
            def __init__(self) -> None:
                self.status_code = 200
            def json(self) -> Mapping[str, object]:
                return files_response
        assert _url.endswith("/files/list_folder")
        return MockResponse()

    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        photos = storage.list_photos()
        # Only JPEGs and PNGs, with full relative paths
        assert set(photos) == {
            "photos/photo1.jpg",
            "photos/photo2.png",
            "photos/2024/nested1.JPG",
            "photos/2024/events/nested2.jpeg",
        }

def test_dropbox_storage_get_photo() -> None:
    # Mock Dropbox API response for downloading a file
    photo_bytes = b"fake image data"

    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.content = photo_bytes

    def mock_post(
        _url: str,
        _headers: dict[str, str] | None = None,
        _data: object | None = None,
        **_kwargs: object,
    ) -> object:
        _ = _kwargs
        if _url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> Mapping[str, str]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        assert _url.endswith("/files/download")
        return MockResponse()

    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        data = storage.get_photo("photo1.jpg")
        assert data == photo_bytes

def test_dropbox_storage_pagination_api_error() -> None:
    # Simulate error on pagination (list_folder/continue)
    page1 = {
        "entries": [
            {".tag": "file", "name": "photo1.jpg", "path_display": "/photos/photo1.jpg"}
        ],
        "has_more": True,
        "cursor": "abc123",
    }
    def mock_post(
        url: str,
        _headers: dict[str, str] | None = None,
        _json: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> object:
        if url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> dict[str, object]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        if url.endswith("/files/list_folder"):
            class MockRespList:
                status_code = 200
                def json(self) -> Mapping[str, object]:
                    return page1
            return MockRespList()
        if url.endswith("/files/list_folder/continue"):
            class MockRespContinue:
                status_code = 401
                text = "Unauthorized"
                def json(self) -> Mapping[str, object]:
                    return {}
            return MockRespContinue()
        msg = "Unexpected URL"
        raise AssertionError(msg)
    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        with pytest.raises(DropboxStorageError, match="Dropbox API error: 401"):
            storage.list_photos()

def test_photostorage_abstract_methods() -> None:
    # Subclass implements but calls super, which raises NotImplementedError
    class Dummy(PhotoStorage):
        def list_photos(self) -> list[str]:
            msg = "list_photos not implemented"
            raise NotImplementedError(msg)
        def get_photo(self, identifier: str) -> bytes:
            msg = "get_photo not implemented"
            raise NotImplementedError(msg)
    dummy = Dummy()
    with pytest.raises(NotImplementedError):
        dummy.list_photos()
    with pytest.raises(NotImplementedError):
        dummy.get_photo("x")

def test_dropbox_storage_list_photos_error() -> None:
    # Simulate Dropbox API error
    def mock_post(
        _url: str,
        _headers: dict[str, str] | None = None,
        _json: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> object:
        _ = _kwargs
        if _url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> dict[str, object]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        class MockResponse:
            def __init__(self) -> None:
                self.status_code = 401
                self.text = "Unauthorized"
            def json(self) -> Mapping[str, object]:
                return {"error": "Unauthorized"}
        return MockResponse()

    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        with pytest.raises(DropboxStorageError, match="Dropbox API error"):
            storage.list_photos()

def test_dropbox_storage_get_photo_not_found() -> None:
    # Simulate Dropbox API file not found
    def mock_post(
        _url: str,
        _headers: dict[str, str] | None = None,
        _data: object | None = None,
        **_kwargs: object,
    ) -> object:
        _ = _kwargs
        if _url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> Mapping[str, str]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        class MockResponse:
            def __init__(self) -> None:
                self.status_code = 409
                self.text = "File not found"
        return MockResponse()

    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        with pytest.raises(DropboxStorageError, match="Dropbox API error"):
            storage.get_photo("missing.jpg")

def test_dropbox_storage_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    # remove OAuth credentials to simulate missing config
    monkeypatch.delenv("DROPBOX_APP_KEY", raising=False)
    monkeypatch.delenv("DROPBOX_APP_SECRET", raising=False)
    monkeypatch.delenv("DROPBOX_REFRESH_TOKEN", raising=False)
    storage = DropboxStorage()
    with pytest.raises(DropboxStorageError, match="Dropbox OAuth credentials are not set"):  # noqa: E501
        storage.list_photos()
    with pytest.raises(DropboxStorageError, match="Dropbox OAuth credentials are not set"):  # noqa: E501
        storage.get_photo("anything.jpg")

def test_dropbox_storage_list_photos_request_exception() -> None:
    def mock_post(*args: object, **_kwargs: object) -> object:
        url, *_ = args
        if url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> Mapping[str, str]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        msg = "Simulated connection error"
        raise requests.RequestException(msg)
    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        with pytest.raises(DropboxStorageError, match="Dropbox API request failed"):
            storage.list_photos()

def test_dropbox_storage_get_photo_request_exception() -> None:
    def mock_post(*args: object, **_kwargs: object) -> object:
        url, *_ = args
        if url == OAUTH_TOKEN_URL:
            class MockAuth:
                def __init__(self) -> None:
                    self.status_code = 200
                def json(self) -> Mapping[str, str]:
                    return {"access_token": "dummy-token"}
            return MockAuth()
        msg = "Simulated connection error"
        raise requests.RequestException(msg)
    with patch("requests.post", mock_post):
        storage = DropboxStorage()
        with pytest.raises(DropboxStorageError, match="Dropbox API request failed"):
            storage.get_photo("anything.jpg")










def test_blank_override_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Override to empty string should default to DropboxStorage
    monkeypatch.setenv("STORAGE_BACKEND", "")
    storage = get_storage_backend()
    assert isinstance(storage, DropboxStorage)
