from typing import Never, NoReturn

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.dao import PhotoDAO
from app.database import Base
from app.deps import get_db
from app.main import app


def test_get_photos_returns_photo_ids() -> None:
    # Setup in-memory DB and override SessionLocal
    engine = create_engine(
        "sqlite:///file:memdb_get_photos_returns_photo_ids?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    # Override DB dependency
    app.dependency_overrides[get_db] = lambda: session
    # Seed two photos
    dao = PhotoDAO(session)
    photo1 = dao.create(object_key="foo.jpg", description=None)
    photo2 = dao.create(object_key="bar.png", description=None)
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [photo1.id, photo2.id]

def test_get_photos_empty() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_get_photos_empty?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == []

def test_get_photos_pagination() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_get_photos_pagination?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    # Seed 10 photos
    dao = PhotoDAO(session)
    for i in range(10):
        dao.create(object_key=f"img_{i}.jpg", description=None)
    client = TestClient(app)
    response = client.get("/photos?limit=5&offset=5")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [6, 7, 8, 9, 10]

def test_get_photos_storage_error() -> None:
    # Simulate DB connection error
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    # Override DB dependency to simulate error
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

# Tests for GET /photos/{id}
def test_get_photo_by_id_success() -> None:
    # Setup in-memory DB and override SessionLocal
    engine = create_engine(
        "sqlite:///file:memdb_get_photo_by_id_success?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    # Seed two photos
    dao = PhotoDAO(session)
    photo1 = dao.create(object_key="foo.jpg", description=None)
    photo2 = dao.create(object_key="bar.jpg", description="Bar")
    client = TestClient(app)
    # Happy path for first photo
    response = client.get(f"/photos/{photo1.id}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == photo1.id
    assert data["object_key"] == "foo.jpg"
    assert "description" in data
    assert data["description"] is None
    # Happy path for second photo (ensure line 68 is covered)
    response = client.get(f"/photos/{photo2.id}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == photo2.id
    assert data["object_key"] == "bar.jpg"
    assert data["description"] == "Bar"

def test_get_photo_by_id_not_found() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_get_photo_by_id_not_found?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Photo not found"

def test_get_photo_by_id_storage_error() -> None:
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

def test_get_photo_by_id_generic_exception(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Patch PhotoDAO.get to raise a generic exception
    class GenericError(Exception):
        pass
    engine = create_engine(
        "sqlite:///file:memdb_get_photo_by_id_generic_exception?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    dao = PhotoDAO(session)
    dao.create(object_key="foo.jpg", description=None)
    def raise_generic_error(_self: PhotoDAO, _photo_id: int) -> Never:
        msg = "something went wrong!"
        raise GenericError(msg)
    monkeypatch.setattr(PhotoDAO, "get", raise_generic_error)
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "something went wrong!" in data["detail"]

def test_patch_photo_description_success() -> None:
    # Use a shared in-memory SQLite DB
    db_url = (
        "sqlite:///file:memdb_patch_description?mode=memory&cache=shared&uri=true"
    )
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_maker()
    app.dependency_overrides[get_db] = lambda: session

    dao = PhotoDAO(session)
    photo = dao.create(object_key="foo.jpg", description=None)

    client = TestClient(app)
    response = client.patch(
        f"/photos/{photo.id}/metadata",
        json={"description": "A new description!"},
    )
    assert response.status_code == HTTP_200_OK

    data = response.json()
    assert data["id"] == photo.id
    assert data["object_key"] == "foo.jpg"
    assert data["description"] == "A new description!"

    # Confirm in DB
    updated = dao.get(photo.id)
    assert updated is not None
    assert updated.description == "A new description!"

    # Clean up
    app.dependency_overrides.clear()
    session.close()
    engine.dispose()

def test_patch_photo_description_not_found() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_patch_photo_description_not_found?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.patch("/photos/123/metadata",
                            json={"description": "Doesn't exist"})
    assert response.status_code == HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Photo not found"

def test_patch_photo_description_db_error() -> None:
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        msg = "db error"
        raise BoomError(msg)
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.patch("/photos/1/metadata",
                            json={"description": "irrelevant"})
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

def test_patch_photo_description_operational_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test patch_photo_caption handles OperationalError gracefully."""
    # Mock PhotoDAO.update_description to raise OperationalError
    from sqlalchemy.exc import OperationalError
    error_message = "mock db error"
    params_value = "params"
    orig_exception = BaseException("original db context")
    def mock_update_description(
        _self: object, _photo_id: int, _description: str
    ) -> Never:
        raise OperationalError(error_message, params_value, orig_exception)

    monkeypatch.setattr(PhotoDAO, "update_description", mock_update_description)

    response = client.patch("/photos/1/metadata",
                            json={"description": "new description"})
    # The implementation returns 404 when OperationalError occurs
    assert response.status_code == HTTP_404_NOT_FOUND
    # Just check that there's a detail message, exact content may vary
    assert "detail" in response.json()

def test_patch_photo_description_generic_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test patch_photo_caption handles generic Exception."""
    # Mock PhotoDAO.update_description to raise a generic Exception
    error_message = "mock generic error"

    class CustomGenericError(Exception):
        """Custom exception for testing."""

    def mock_update_description(_photo_id: int, _description: str) -> Never:
        raise CustomGenericError(error_message)

    monkeypatch.setattr(PhotoDAO, "update_description", mock_update_description)

    update_payload = {"description": "Trigger Generic Error"}
    response = client.patch("/photos/1/metadata", json=update_payload)

    # The route's own except Exception block should catch this
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Just verify there's a detail field in the response, content may vary
    assert "detail" in response.json()

SHUFFLE_TOTAL = 5
SHUFFLE_LIMIT = 3


def test_get_photos_shuffled_returns_all_when_limit_exceeds_count() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_photos_shuffled_all?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    app.dependency_overrides[get_db] = lambda: session
    dao = PhotoDAO(session)
    ids = [
        dao.create(object_key=f"img_{i}.jpg", description=None).id
        for i in range(SHUFFLE_TOTAL)
    ]
    client = TestClient(app)
    response = client.get("/photos/shuffled?limit=100")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert sorted(data["photo_ids"]) == sorted(ids)
    assert len(data["photo_ids"]) == SHUFFLE_TOTAL


def test_get_photos_shuffled_respects_limit() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_photos_shuffled_limit?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    app.dependency_overrides[get_db] = lambda: session
    dao = PhotoDAO(session)
    [
        dao.create(object_key=f"img_{i}.jpg", description=None)
        for i in range(10)
    ]
    client = TestClient(app)
    response = client.get(f"/photos/shuffled?limit={SHUFFLE_LIMIT}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert len(data["photo_ids"]) == SHUFFLE_LIMIT
    # All IDs must be unique
    assert len(set(data["photo_ids"])) == SHUFFLE_LIMIT


def test_get_photos_shuffled_is_randomized() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_photos_shuffled_random?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    app.dependency_overrides[get_db] = lambda: session
    dao = PhotoDAO(session)
    [
        dao.create(object_key=f"img_{i}.jpg", description=None)
        for i in range(SHUFFLE_TOTAL)
    ]
    client = TestClient(app)
    orderings: set[tuple[int, ...]] = set()
    for _ in range(5):
        response = client.get(f"/photos/shuffled?limit={SHUFFLE_TOTAL}")
        assert response.status_code == HTTP_200_OK
        orderings.add(tuple(response.json()["photo_ids"]))
    # At least two different orderings should be seen
    assert len(orderings) > 1


def test_get_photos_shuffled_empty_db() -> None:
    engine = create_engine(
        "sqlite:///file:memdb_photos_shuffled_empty?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.get("/photos/shuffled?limit=10")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == []


def test_get_photos_shuffled_storage_error() -> None:
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        msg = "db error"
        raise BoomError(msg)
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get(f"/photos/shuffled?limit={SHUFFLE_LIMIT}")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

# Tests for handle_db_errors decorator via routes
def test_get_photos_decorator_test_app_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test handle_db_errors catches test_app exception from DAO via route."""
    class CustomTestAppError(Exception):
        __module__ = "test_app_module"

    error_message = "DAO Test error from test_app module"

    def mock_list(_self: object, **kwargs: object) -> Never:  # noqa: ARG001
        raise CustomTestAppError(error_message)

    monkeypatch.setattr(PhotoDAO, "list", mock_list)

    response = client.get("/photos")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.json()

# Tests for GET /photos

def test_patch_photo_description_invalid_payload(client: TestClient) -> None:
    """Test updating with invalid payload returns 422."""
    # Payload missing the required 'description' field
    invalid_payload = {"wrong_field": "Some value"}
    response = client.patch("/photos/1/metadata", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Payload with incorrect type for 'description'
    invalid_payload_type = {"description": 12345}
    response = client.patch("/photos/1/metadata", json=invalid_payload_type)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_photos_shuffled_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test getting shuffled photo IDs successfully."""
    # Mock PhotoDAO.list to return pre-shuffled results
    mock_ids = [3, 1, 2]

    # Mock a Photo object
    class MockPhoto:
        def __init__(self, photo_id: int) -> None:
            self.id = photo_id

    # Create mock photos with the desired IDs
    mock_photos = [
        MockPhoto(photo_id)
        for photo_id in mock_ids
    ]

    def mock_list(
        _self: object, **kwargs: object  # noqa: ARG001
    ) -> list[MockPhoto]:
        return mock_photos

    monkeypatch.setattr(PhotoDAO, "list", mock_list)

    response = client.get("/photos/shuffled")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # Verify the structure and that we got the right number of IDs
    assert "photo_ids" in response_data
    assert len(response_data["photo_ids"]) == len(mock_ids)
    # Check that all expected IDs are in the response (order might be different)
    assert set(response_data["photo_ids"]) == set(mock_ids)


def test_get_photos_shuffled_db_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GET /photos/shuffled handles OperationalError returning empty list."""

    # Mock PhotoDAO.list to raise OperationalError
    error_message = "mock shuffle db error"
    # Provide BaseException instance
    orig_exception = BaseException("original shuffle error context")

    def mock_list_error(_self: object, **kwargs: object) -> Never:  # noqa: ARG001
        raise OperationalError(error_message, None, orig_exception)

    monkeypatch.setattr(PhotoDAO, "list", mock_list_error)

    response = client.get("/photos/shuffled")
    # Endpoint returns 200 with empty list on error
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"photo_ids": []}
