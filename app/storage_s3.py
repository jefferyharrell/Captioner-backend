import os

from app.storage import PhotoStorage


class S3Storage(PhotoStorage):
    """
    Photo storage using Amazon S3 HTTP API.
    """

    def __init__(self) -> None:
        # Configuration via env variables
        self.bucket = os.getenv("S3_BUCKET")

    def list_photos(self) -> list[str]:
        """
        List all photo keys in the S3 bucket.
        """
        error_message = "S3Storage.list_photos not implemented"
        raise NotImplementedError(error_message)

    def get_photo(self, identifier: str) -> bytes:
        """
        Retrieve photo bytes from S3 using the object key.
        """
        error_message = "S3Storage.get_photo not implemented"
        raise NotImplementedError(error_message)
