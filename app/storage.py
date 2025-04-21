import os
from abc import ABC, abstractmethod


class StorageError(Exception):
    """Base exception for all storage backend errors."""


class PhotoStorage(ABC):
    """
    Interface for photo storage backends.
    """

    @abstractmethod
    def list_photos(self) -> list[str]:
        ...

    @abstractmethod
    def get_photo(self, identifier: str) -> bytes:
        ...


def get_storage_backend() -> PhotoStorage:
    backend = os.getenv("STORAGE_BACKEND", "dropbox").strip().lower()
    if backend in ("", "dropbox"):
        from app.storage_dropbox import DropboxStorage
        return DropboxStorage()
    msg = f"Unknown storage backend: {backend}"
    raise ValueError(msg)
