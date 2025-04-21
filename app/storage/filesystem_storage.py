from pathlib import Path

from .photo_storage import PhotoStorage


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
