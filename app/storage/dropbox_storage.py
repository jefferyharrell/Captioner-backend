import os

import requests

from .photo_storage import PhotoStorage


class DropboxStorageError(Exception):
    """Custom exception for DropboxStorage errors."""

class DropboxStorage(PhotoStorage):
    """
    Photo storage using Dropbox HTTP API.
    """
    _DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
    _DROPBOX_LIST_FOLDER_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
    _DROPBOX_DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"
    _SUCCESS_CODE = 200
    _NOT_FOUND_CODE = 409
    _TIMEOUT = 10  # seconds

    def __init__(self, base_path: str = "") -> None:
        self.token: str | None = None
        self.app_key = os.getenv("DROPBOX_APP_KEY")
        self.app_secret = os.getenv("DROPBOX_APP_SECRET")
        self.refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        root_env = os.getenv("DROPBOX_ROOT_PATH", "")
        if not base_path:
            base_path = root_env
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
        import re
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
            resp = requests.post(url, headers=headers, json=data, timeout=self._TIMEOUT)
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
