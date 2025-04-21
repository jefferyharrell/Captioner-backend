import os
from abc import ABC, abstractmethod
from pathlib import Path

import requests


class PhotoStorage(ABC):
    """
    Interface for photo storage backends.
    """

    @abstractmethod
    def list_photos(self) -> list[str]:
        """
        Return a list of photo identifiers (e.g., filenames or IDs).
        """
        error_message = "list_photos not implemented"
        raise NotImplementedError(error_message)

    @abstractmethod
    def get_photo(self, identifier: str) -> bytes:
        """
        Retrieve the raw bytes of the photo specified by identifier.
        """
        error_message = "get_photo not implemented"
        raise NotImplementedError(error_message)

    @abstractmethod
    def get_caption(self, object_key: str) -> str | None:
        """
        Retrieve the caption for the specified photo.
        """
        error_message = "get_caption not implemented"
        raise NotImplementedError(error_message)

    @abstractmethod
    def set_caption(self, object_key: str, caption: str) -> None:
        """
        Set or update the caption for the specified photo.
        """
        error_message = "set_caption not implemented"
        raise NotImplementedError(error_message)

    @abstractmethod
    def delete_caption(self, object_key: str) -> None:
        """
        Delete the caption for the specified photo.
        """
        error_message = "delete_caption not implemented"
        raise NotImplementedError(error_message)


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

    def get_caption(self, object_key: str) -> str | None:
        """
        Filesystem storage does not implement captions (MVP: Dropbox only).
        """
        error_message = "get_caption not implemented for FileSystemStorage"
        raise NotImplementedError(error_message)

    def set_caption(self, object_key: str, caption: str) -> None:
        """
        Filesystem storage does not implement captions (MVP: Dropbox only).
        """
        error_message = "set_caption not implemented for FileSystemStorage"
        raise NotImplementedError(error_message)

    def delete_caption(self, object_key: str) -> None:
        """
        Filesystem storage does not implement captions (MVP: Dropbox only).
        """
        error_message = "delete_caption not implemented for FileSystemStorage"
        raise NotImplementedError(error_message)


class DropboxStorageError(Exception):
    """Custom exception for DropboxStorage errors."""


class DropboxStorage(PhotoStorage):
    """
    Photo storage using Dropbox HTTP API.
    Implements caption CRUD using Dropbox file properties API.
    """

    _DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
    _DROPBOX_LIST_FOLDER_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
    _DROPBOX_DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"
    _DROPBOX_PROPERTIES_GET_URL = "https://api.dropboxapi.com/2/file_properties/properties/get"
    _DROPBOX_PROPERTIES_OVERWRITE_URL = "https://api.dropboxapi.com/2/file_properties/properties/overwrite"
    _DROPBOX_PROPERTIES_REMOVE_URL = "https://api.dropboxapi.com/2/file_properties/properties/remove"
    _TEMPLATE_NAME = "CaptionerPhotoTags"
    _FIELD_NAME = "caption"
    _SUCCESS_CODE = 200
    _NOT_FOUND_CODE = 409
    _TIMEOUT = 10  # seconds

    def get_caption(self, object_key: str) -> str | None:
        """
        Retrieve the caption for the specified photo from Dropbox file properties.
        Returns the caption string if present, or None if not set.
        """
        if not self.token:
            if not all([self.app_key, self.app_secret, self.refresh_token]):
                error_message = "Dropbox OAuth credentials are not set"
                raise DropboxStorageError(error_message)
            self._refresh_token()
        url = self._DROPBOX_PROPERTIES_GET_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "path": f"/{object_key}",
            "property_templates": [self._TEMPLATE_NAME],
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=self._TIMEOUT)
        except requests.RequestException as exc:
            error_message = f"Dropbox API request failed: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            # If the properties are missing, treat as no caption
            if resp.status_code == self._NOT_FOUND_CODE:
                return None
            error_message = f"Dropbox API error: {resp.status_code} {resp.text}"
            raise DropboxStorageError(error_message)
        result = resp.json()
        for prop in result.get("property_groups", []):
            if (
                prop.get("template_id") == self._TEMPLATE_NAME
                or prop.get("template_name") == self._TEMPLATE_NAME
            ):
                for field in prop.get("fields", []):
                    if field.get("name") == self._FIELD_NAME:
                        return field.get("value")
        return None

    def set_caption(self, object_key: str, caption: str) -> None:
        """
        Set or update the caption for the specified photo in Dropbox file properties.
        """
        if not self.token:
            if not all([self.app_key, self.app_secret, self.refresh_token]):
                error_message = "Dropbox OAuth credentials are not set"
                raise DropboxStorageError(error_message)
            self._refresh_token()
        url = self._DROPBOX_PROPERTIES_OVERWRITE_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "path": f"/{object_key}",
            "property_groups": [
                {
                    "template_id": self._TEMPLATE_NAME,
                    "fields": [
                        {"name": self._FIELD_NAME, "value": caption}
                    ],
                }
            ],
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=self._TIMEOUT)
        except requests.RequestException as exc:
            error_message = f"Dropbox API request failed: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            error_message = f"Dropbox API error: {resp.status_code} {resp.text}"
            raise DropboxStorageError(error_message)

    def delete_caption(self, object_key: str) -> None:
        """
        Delete the caption for the specified photo from Dropbox file properties.
        """
        if not self.token:
            if not all([self.app_key, self.app_secret, self.refresh_token]):
                error_message = "Dropbox OAuth credentials are not set"
                raise DropboxStorageError(error_message)
            self._refresh_token()
        url = self._DROPBOX_PROPERTIES_REMOVE_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "path": f"/{object_key}",
            "property_template_id": self._TEMPLATE_NAME,
            "property_field_names": [self._FIELD_NAME],
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=self._TIMEOUT)
        except requests.RequestException as exc:
            error_message = f"Dropbox API request failed: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            # If the field is already missing, treat as success
            if resp.status_code == self._NOT_FOUND_CODE:
                return
            error_message = f"Dropbox API error: {resp.status_code} {resp.text}"
            raise DropboxStorageError(error_message)

    def __init__(self, base_path: str = "") -> None:
        """
        Args:
            base_path: The Dropbox folder to search from. If not provided, uses
                DROPBOX_ROOT_PATH env var if set, else root ('').
                Can be specified with or without a leading '/'.
        """
        # static DROPBOX_TOKEN support removed; token always via OAuth refresh
        self.token: str | None = None
        self.app_key = os.getenv("DROPBOX_APP_KEY")
        self.app_secret = os.getenv("DROPBOX_APP_SECRET")
        self.refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        root_env = os.getenv("DROPBOX_ROOT_PATH", "")
        if not base_path:
            base_path = root_env
        # Normalize base_path to start with '/' if non-empty
        if base_path and not base_path.startswith("/"):
            base_path = "/" + base_path
        self.base_path = base_path

    def _refresh_token(self) -> None:
        try:
            resp = requests.post(
                "https://api.dropbox.com/oauth2/token",
                headers=None,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.app_key,
                    "client_secret": self.app_secret,
                },
                timeout=self._TIMEOUT,
            )
        except requests.RequestException as exc:
            error_message = f"Failed to obtain Dropbox access token: {exc}"
            raise DropboxStorageError(error_message) from exc
        if resp.status_code != self._SUCCESS_CODE:
            error_message = (
                f"Failed to obtain Dropbox access token: {resp.status_code} "
                f"{resp.text}"
            )
            raise DropboxStorageError(error_message)
        token_json = resp.json()
        self.token = token_json.get("access_token")
        if not self.token:
            error_message = "Failed to obtain Dropbox access token"
            raise DropboxStorageError(error_message)

    def list_photos(self) -> list[str]:
        """
        Return a list of all JPEG and PNG photo paths (relative to root) in Dropbox,
        recursively, starting from self.base_path.
        """
        import re

        import requests

        # acquire access token via refresh token
        if not self.token:
            if not all([self.app_key, self.app_secret, self.refresh_token]):
                error_message = "Dropbox OAuth credentials are not set"
                raise DropboxStorageError(error_message)
            self._refresh_token()
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
        images = [
            entry["path_display"].lstrip("/")
            for entry in result.get("entries", [])
            if (
                entry.get(".tag") == "file"
                and image_pattern.search(entry.get("path_display", ""))
            )
        ]
        while result.get("has_more"):
            cursor = result["cursor"]
            url = self._DROPBOX_LIST_FOLDER_CONTINUE_URL
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            data = {"cursor": cursor}
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
            images.extend(
                [
                    entry["path_display"].lstrip("/")
                    for entry in result.get("entries", [])
                    if (
                        entry.get(".tag") == "file"
                        and image_pattern.search(entry.get("path_display", ""))
                    )
                ]
            )
        return images

    def get_photo(self, identifier: str) -> bytes:
        """Download photo bytes from Dropbox folder '/photos'."""
        import requests

        # acquire access token via refresh token
        if not self.token:
            if not all([self.app_key, self.app_secret, self.refresh_token]):
                error_message = "Dropbox OAuth credentials are not set"
                raise DropboxStorageError(error_message)
            self._refresh_token()
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
    S3 backend is post-MVP and not implemented.
    """

    def __init__(self) -> None:
        # Configuration (e.g., AWS credentials) via env variables
        self.bucket = os.getenv("S3_BUCKET")

    def list_photos(self) -> list[str]:
        error_message = "S3Storage.list_photos not implemented"
        raise NotImplementedError(error_message)

    def get_photo(self, identifier: str) -> bytes:
        error_message = "S3Storage.get_photo not implemented"
        raise NotImplementedError(error_message)

    def get_caption(self, object_key: str) -> str | None:
        """
        S3 backend is post-MVP and does not implement captions.
        """
        error_message = "get_caption not implemented for S3Storage"
        raise NotImplementedError(error_message)

    def set_caption(self, object_key: str, caption: str) -> None:
        """
        S3 backend is post-MVP and does not implement captions.
        """
        error_message = "set_caption not implemented for S3Storage"
        raise NotImplementedError(error_message)

    def delete_caption(self, object_key: str) -> None:
        """
        S3 backend is post-MVP and does not implement captions.
        """
        error_message = "delete_caption not implemented for S3Storage"
        raise NotImplementedError(error_message)


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
