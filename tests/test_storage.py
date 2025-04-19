import pathlib

import pytest

from app.storage import (
    DropboxStorage,
    FileSystemStorage,
    PhotoStorage,
    S3Storage,
    get_storage_backend,
)


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


def test_dropbox_storage_not_implemented() -> None:
    # DropboxStorage methods are unimplemented
    storage = DropboxStorage()
    with pytest.raises(NotImplementedError, match="list_photos not implemented"):
        storage.list_photos()
    with pytest.raises(NotImplementedError, match="get_photo not implemented"):
        storage.get_photo("x")


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
