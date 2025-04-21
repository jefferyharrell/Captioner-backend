from abc import ABC, abstractmethod


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
