import os
from abc import ABC, abstractmethod
from pathlib import Path


class PhotoStorage(ABC):
    """
    Interface for photo storage backends.
    """

    @abstractmethod
    def list_photos(self) -> list[str]:
        """
        Return a list of photo identifiers (e.g., filenames or IDs).
        """
        ...

    @abstractmethod
    def get_photo(self, identifier: str) -> bytes:
        """
        Retrieve the raw bytes of the photo specified by identifier.
        """
        ...


class FileSystemStorage(PhotoStorage):
    """
    Photo storage using the local filesystem.
    """

    def __init__(self, base_path: str = ".") -> None:
        self.base_path = Path(base_path)

    def list_photos(self) -> list[str]:
        try:
            return [p.name for p in self.base_path.iterdir() if p.is_file()]
        except FileNotFoundError:
            return []

    def get_photo(self, identifier: str) -> bytes:
        file_path = self.base_path / identifier
        return file_path.read_bytes()


class DropboxStorage(PhotoStorage):
    """
    Photo storage using Dropbox HTTP API.
    """

    def __init__(self) -> None:
        # Configuration (e.g., access token) should be via env variables
        self.token = os.getenv("DROPBOX_TOKEN")

    def list_photos(self) -> list[str]:
        msg = "DropboxStorage.list_photos not implemented"
        raise NotImplementedError(msg)

    def get_photo(self, identifier: str) -> bytes:
        msg = "DropboxStorage.get_photo not implemented"
        raise NotImplementedError(msg)


class S3Storage(PhotoStorage):
    """
    Photo storage using Amazon S3 HTTP API.
    """

    def __init__(self) -> None:
        # Configuration (e.g., AWS credentials) via env variables
        self.bucket = os.getenv("S3_BUCKET")

    def list_photos(self) -> list[str]:
        msg = "S3Storage.list_photos not implemented"
        raise NotImplementedError(msg)

    def get_photo(self, identifier: str) -> bytes:
        msg = "S3Storage.get_photo not implemented"
        raise NotImplementedError(msg)


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
    err_msg = f"Unknown storage backend: {backend}"
    raise ValueError(err_msg)
