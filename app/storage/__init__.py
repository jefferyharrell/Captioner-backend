import os

from .dropbox_storage import DropboxStorage
from .filesystem_storage import FileSystemStorage
from .photo_storage import PhotoStorage
from .s3_storage import S3Storage


def get_storage_backend() -> PhotoStorage:
    """
    Factory for storage backend based on STORAGE_BACKEND env var.
    Defaults to DropboxStorage.

    Supported values (case-insensitive):
      - 'filesystem'
      - 'dropbox'
      - 's3'
    """
    backend = os.getenv("STORAGE_BACKEND", "dropbox").lower()
    if backend == "filesystem":
        return FileSystemStorage()
    if backend == "s3":
        return S3Storage()
    if backend in ("dropbox", ""):  # default
        return DropboxStorage()
    error_message = f"Unknown storage backend: {backend}"
    raise ValueError(error_message)
