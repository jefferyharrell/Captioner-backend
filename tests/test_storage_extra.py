import pytest

from app.storage import (
    DropboxStorage,
    DropboxStorageError,
    FileSystemStorage,
    PhotoStorage,
    S3Storage,
    get_storage_backend,
)


# --- Abstract base class NotImplementedError branches ---
def test_photostorage_notimplemented() -> None:
    class Dummy(PhotoStorage):
        def list_photos(self):
            return super().list_photos()  # type: ignore[reportAbstractUsage]
        def get_photo(self, identifier: str) -> bytes:
            return super().get_photo(identifier)  # type: ignore[reportAbstractUsage]
        def get_caption(self, object_key: str) -> str | None:
            return super().get_caption(object_key)  # type: ignore[reportAbstractUsage]
        def set_caption(self, object_key: str, caption: str) -> None:
            return super().set_caption(object_key, caption)  # type: ignore[reportAbstractUsage]
        def delete_caption(self, object_key: str) -> None:
            return super().delete_caption(object_key)  # type: ignore[reportAbstractUsage]
    dummy = Dummy()
    with pytest.raises(NotImplementedError):
        dummy.list_photos()
    with pytest.raises(NotImplementedError):
        dummy.get_photo("foo")
    with pytest.raises(NotImplementedError):
        dummy.get_caption("foo")
    with pytest.raises(NotImplementedError):
        dummy.set_caption("foo", "bar")
    with pytest.raises(NotImplementedError):
        dummy.delete_caption("foo")

def test_filesystemstorage_caption_notimplemented(tmp_path: object) -> None:
    fs = FileSystemStorage(base_path=str(tmp_path))
    with pytest.raises(NotImplementedError):
        fs.get_caption("foo")
    with pytest.raises(NotImplementedError):
        fs.set_caption("foo", "bar")
    with pytest.raises(NotImplementedError):
        fs.delete_caption("foo")

def test_s3storage_notimplemented() -> None:
    s3 = S3Storage()
    with pytest.raises(NotImplementedError):
        s3.list_photos()
    with pytest.raises(NotImplementedError):
        s3.get_photo("foo")
    with pytest.raises(NotImplementedError):
        s3.get_caption("foo")
    with pytest.raises(NotImplementedError):
        s3.set_caption("foo", "bar")
    with pytest.raises(NotImplementedError):
        s3.delete_caption("foo")

# --- DropboxStorage: missing env vars, token refresh, and fallback logic ---
def test_dropboxstorage_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DROPBOX_APP_KEY", raising=False)
    monkeypatch.delenv("DROPBOX_APP_SECRET", raising=False)
    monkeypatch.delenv("DROPBOX_REFRESH_TOKEN", raising=False)
    storage = DropboxStorage()
    with pytest.raises(DropboxStorageError, match="Dropbox OAuth credentials are not set"):
        storage.get_caption("foo")
    with pytest.raises(DropboxStorageError, match="Dropbox OAuth credentials are not set"):
        storage.set_caption("foo", "bar")
    with pytest.raises(DropboxStorageError, match="Dropbox OAuth credentials are not set"):
        storage.delete_caption("foo")

def test_dropboxstorage_token_refresh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DROPBOX_APP_KEY", "dummy-app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "dummy-app-secret")
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "dummy-refresh-token")
    def mock_post(*a: object, **k: object) -> object:  # noqa: ARG001
        class Resp:
            status_code = 400
            text = "bad request"
        return Resp()
    monkeypatch.setattr("requests.post", mock_post)
    storage = DropboxStorage()
    storage.token = None
    with pytest.raises(DropboxStorageError, match="Failed to obtain Dropbox access token"):
        storage.get_caption("foo")

# --- get_storage_backend factory ---
def test_get_storage_backend_known(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "dropbox")
    assert isinstance(get_storage_backend(), DropboxStorage)
    monkeypatch.setenv("STORAGE_BACKEND", "filesystem")
    assert isinstance(get_storage_backend(), FileSystemStorage)
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    assert isinstance(get_storage_backend(), S3Storage)
    monkeypatch.setenv("STORAGE_BACKEND", "")
    assert isinstance(get_storage_backend(), DropboxStorage)

def test_get_storage_backend_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_BACKEND", "nonsense")
    with pytest.raises(ValueError, match="Unknown storage backend"):
        get_storage_backend()
