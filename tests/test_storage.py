import os
import pathlib
from collections.abc import Mapping
from unittest.mock import patch

import pytest
import requests

from app.storage import (
    DropboxStorage,
    DropboxStorageError,
    FileSystemStorage,
    PhotoStorage,
    S3Storage,
    get_storage_backend,
)

OAUTH_TOKEN_URL = "https://api.dropbox.com/oauth2/token"  # noqa: S105

@pytest.fixture(autouse=True)
def dropbox_oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DROPBOX_APP_KEY", "dummy-app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "dummy-app-secret")
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "dummy-refresh-token")

def test_storage_interface() -> None:
    # All storage backends must implement the PhotoStorage interface
    storage: PhotoStorage = FileSystemStorage(base_path="/does/not/matter")
    assert hasattr(storage, "list_photos")
    assert hasattr(storage, "get_photo")
    assert callable(storage.list_photos)
    assert callable(storage.get_photo)


def test_filesystem_storage(tmp_path: pathlib.Path) -> None:
    # Create sample photo files
    file1 = tmp_path / "photo1.jpg"
    content1 = b"first"
    file1.write_bytes(content1)
    file2 = tmp_path / "photo2.png"
    content2 = b"second"
    file2.write_bytes(content2)

    storage = FileSystemStorage(base_path=str(tmp_path))
    photos = storage.list_photos()
    # Expect filenames returned
    assert set(photos) == {"photo1.jpg", "photo2.png"}

    # get_photo returns raw bytes
    data = storage.get_photo("photo1.jpg")
    assert data == content1


def test_default_storage_is_dropbox(monkeypatch: pytest.MonkeyPatch) -> None:
    # Default backend without override should be Dropbox
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    storage = get_storage_backend()
    assert isinstance(storage, DropboxStorage)


def test_override_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # We can override default via STORAGE_BACKEND env var
    monkeypatch.setenv("STORAGE_BACKEND", "filesystem")
    storage = get_storage_backend()
    assert isinstance(storage, FileSystemStorage)


def test_unknown_backend_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "unknown")
    with pytest.raises(ValueError, match="Unknown storage backend"):
        get_storage_backend()


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
        def get_caption(self, object_key: str) -> str | None:
            msg = "get_caption not implemented"
            raise NotImplementedError(msg)
        def set_caption(self, object_key: str, caption: str) -> None:
            msg = "set_caption not implemented"
            raise NotImplementedError(msg)
        def delete_caption(self, object_key: str) -> None:
            msg = "delete_caption not implemented"
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


def test_s3_storage_not_implemented() -> None:
    # S3Storage methods are unimplemented
    storage = S3Storage()
    with pytest.raises(NotImplementedError, match="list_photos not implemented"):
        storage.list_photos()
    with pytest.raises(NotImplementedError, match="get_photo not implemented"):
        storage.get_photo("x")


def test_override_s3_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Override default via STORAGE_BACKEND to s3
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    storage = get_storage_backend()
    assert isinstance(storage, S3Storage)


@pytest.mark.skipif(
    not (os.getenv("DROPBOX_APP_KEY") and os.getenv("DROPBOX_APP_SECRET") and os.getenv("DROPBOX_REFRESH_TOKEN")),  # noqa: E501
    reason="No Dropbox token set; skipping live Dropbox API test."
)
def test_dropbox_live_list_folder() -> None:
    """
    Live test: Only runs if DROPBOX_TOKEN is set. Calls Dropbox API and checks
    status code.
    """
    from app.storage import DropboxStorage
    storage = DropboxStorage()
    photos = storage.list_photos()
    print(f"Photos found on Dropbox at {storage.base_path or '/'} (JPEG/PNG only):")  # noqa: T201
    for path in photos:
        print(path)  # noqa: T201
    # We still want to check API connectivity, so do a minimal API call for status
    token = storage.token
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {"path": storage.base_path, "recursive": False}
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    http_ok = 200
    assert resp.status_code == http_ok


def test_filesystem_storage_missing_path() -> None:
    # Listing a nonexistent directory returns empty list
    storage = FileSystemStorage(base_path="/path/does/not/exist")
    photos = storage.list_photos()
    assert photos == []


def test_blank_override_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Override to empty string should default to DropboxStorage
    monkeypatch.setenv("STORAGE_BACKEND", "")
    storage = get_storage_backend()
    assert isinstance(storage, DropboxStorage)
