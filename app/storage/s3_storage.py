import os

from .photo_storage import PhotoStorage


class S3Storage(PhotoStorage):
    """
    Photo storage using Amazon S3 HTTP API. (Stub; not implemented for MVP)
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
