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


class DropboxStorageError(Exception):
    """Custom exception for DropboxStorage errors."""


class DropboxStorage(PhotoStorage):
    """
    Photo storage using Dropbox HTTP API.
    """

    _DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
    _DROPBOX_DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"
    _SUCCESS_CODE = 200
    _NOT_FOUND_CODE = 409
    _TIMEOUT = 10  # seconds

    def __init__(self, base_path: str = "") -> None:
        """
        Args:
            base_path: The Dropbox folder to search from (default: root "").
                      Can be specified with or without a leading '/'.
        """
        # Configuration (e.g., access token) via env variables
        self.token = os.getenv("DROPBOX_TOKEN")
        # Normalize base_path to start with '/' if non-empty
        if base_path and not base_path.startswith("/"):
            base_path = "/" + base_path
        self.base_path = base_path

    def list_photos(self) -> list[str]:
        """
        Return a list of all JPEG and PNG photo paths (relative to root) in Dropbox,
        recursively, starting from self.base_path.
        """
        import re

        import requests

        if not self.token:
            msg = "DROPBOX_TOKEN env var is not set"
            raise DropboxStorageError(msg)

        url = self._DROPBOX_LIST_FOLDER_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {"path": self.base_path, "recursive": True}
        try:
            resp = requests.post(
                url, headers=headers, json=data, timeout=self._TIMEOUT
            )
        except requests.RequestException as exc:
            error_message = f"Dropbox API request failed: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            error_message = f"Dropbox API error: {resp.status_code} {resp.text}"
            raise DropboxStorageError(error_message)
        result = resp.json()
        image_pattern = re.compile(r"\.(jpe?g|png)$", re.IGNORECASE)
        return [
            entry["path_display"].lstrip("/")
            for entry in result.get("entries", [])
            if (
                entry.get(".tag") == "file"
                and image_pattern.search(entry.get("path_display", ""))
            )
        ]

    def get_photo(self, identifier: str) -> bytes:
        """Download photo bytes from Dropbox folder '/photos'."""
        import requests
        if not self.token:
            msg = "DROPBOX_TOKEN env var is not set"
            raise DropboxStorageError(msg)
        url = self._DROPBOX_DOWNLOAD_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Dropbox-API-Arg": f'{{"path": "/photos/{identifier}"}}',
        }
        try:
            resp = requests.post(url, headers=headers, timeout=self._TIMEOUT)
        except requests.RequestException as exc:
            error_message = f"Dropbox API request failed: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            error_message = f"Dropbox API error: {resp.status_code} {resp.text}"
            raise DropboxStorageError(error_message)
        return resp.content


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
