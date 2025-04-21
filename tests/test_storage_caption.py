# ruff: noqa: UP035,UP006,UP007,ANN401,ARG005,I001
# pyright: reportUnknownArgumentType=false,reportUnknownLambdaType=false,reportMissingTypeArgument=false
from typing import Any, Optional
import pytest

from app.storage import DropboxStorage, DropboxStorageError

# Constants to avoid private member access lint errors
TEMPLATE_NAME = DropboxStorage._TEMPLATE_NAME  # noqa: SLF001
FIELD_NAME    = DropboxStorage._FIELD_NAME     # noqa: SLF001

DUMMY_TOKEN   = "dummy-token"               # noqa: S105
DUMMY_PATH    = "photos/test.jpg"
DUMMY_CAPTION = "A test caption!"

@pytest.fixture(autouse=True)
def dropbox_oauth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DROPBOX_APP_KEY", "dummy-app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "dummy-app-secret")
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "dummy-refresh-token")


def _mock_resp(
    status_code: int,
    text: str = "",
    json_body: Optional[dict[str, Any]] = None,
) -> object:
    class MockResp:
        def __init__(self) -> None:
            self.status_code = status_code
            self.text = text

        def json(self) -> dict[str, Any]:
            return json_body or {}

    return MockResp()

# --- get_caption ---

def test_get_caption_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return caption if present."""
    def mock_post(
        url: str,
        headers: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> object:
        return _mock_resp(
            200,
            json_body={
                "property_groups": [
                    {
                        "template_name": TEMPLATE_NAME,
                        "fields": [
                            {"name": FIELD_NAME, "value": DUMMY_CAPTION},
                        ],
                    }
                ]
            },
        )

    monkeypatch.setattr("requests.post", mock_post)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    assert storage.get_caption(DUMMY_PATH) == DUMMY_CAPTION


def test_get_caption_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None if property not found (409)."""
    def mock_post_notfound(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(409, text="not found")

    monkeypatch.setattr("requests.post", mock_post_notfound)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    assert storage.get_caption(DUMMY_PATH) is None


def test_get_caption_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise on non-409 error."""
    def mock_post_error(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(500, text="fail")

    monkeypatch.setattr("requests.post", mock_post_error)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    with pytest.raises(
        DropboxStorageError, match="Dropbox API error: 500"
    ):
        storage.get_caption(DUMMY_PATH)


def test_get_caption_request_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise on request exception."""
    def mock_post_exc(*_args: Any, **_kwargs: Any) -> object:
        raise Exception("boom")

    monkeypatch.setattr("requests.post", mock_post_exc)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    with pytest.raises(
        DropboxStorageError, match="Dropbox API request failed:"
    ):
        storage.get_caption(DUMMY_PATH)

# --- set_caption ---

def test_set_caption_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No exception if Dropbox returns 200."""
    def mock_post_set(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(200)

    monkeypatch.setattr("requests.post", mock_post_set)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    storage.set_caption(DUMMY_PATH, DUMMY_CAPTION)


def test_set_caption_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise on error."""
    def mock_post_seterr(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(500, text="oh no")

    monkeypatch.setattr("requests.post", mock_post_seterr)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    with pytest.raises(
        DropboxStorageError, match="Dropbox API error: 500"
    ):
        storage.set_caption(DUMMY_PATH, DUMMY_CAPTION)


def test_set_caption_request_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise on request exception."""
    def mock_post_setexc(*_args: Any, **_kwargs: Any) -> object:
        raise Exception("boom")

    monkeypatch.setattr("requests.post", mock_post_setexc)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    with pytest.raises(
        DropboxStorageError, match="Dropbox API request failed:"
    ):
        storage.set_caption(DUMMY_PATH, DUMMY_CAPTION)

# --- delete_caption ---

def test_delete_caption_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No exception if Dropbox returns 200."""
    def mock_post_del(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(200)

    monkeypatch.setattr("requests.post", mock_post_del)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    storage.delete_caption(DUMMY_PATH)


def test_delete_caption_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No exception if already deleted (409)."""
    def mock_post_delnf(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(409, text="already gone")

    monkeypatch.setattr("requests.post", mock_post_delnf)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    storage.delete_caption(DUMMY_PATH)


def test_delete_caption_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise on error."""
    def mock_post_delerr(*_args: Any, **_kwargs: Any) -> object:
        return _mock_resp(500, text="oh no")

    monkeypatch.setattr("requests.post", mock_post_delerr)
    storage = DropboxStorage()
    storage.token = DUMMY_TOKEN
    with pytest.raises(
        DropboxStorageError, match="Dropbox API error: 500"
    ):
        storage.delete_caption(DUMMY_PATH)
